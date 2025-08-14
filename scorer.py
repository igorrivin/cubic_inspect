
"""
cubic_inspect.scorer
--------------------

Inspect AI scorer that validates a parameterized rational map f: P^1 -> X (cubic surface)
returned by a model in JSON (structured output) form.

Expected model output JSON:
{
  "map": {
     "F0": "... polynomial in s,t ...",
     "F1": "...",
     "F2": "...",
     "F3": "..."
  }
}

The task `target` should be JSON containing:
{
  "surface": "... polynomial in W0,W1,W2,W3 ...",
  "claims": { "degree": 15, "nonfree": true, "s_witness": 3 }
}

You can pass `mode` ("auto" | "sage" | "sympy") via scorer args (-S mode=sage).
"""

from __future__ import annotations
import json
from typing import Any, Dict

from inspect_ai.scorer import Score, Target, accuracy, scorer, stderr
from inspect_ai.solver import TaskState

from .validator import validate_map

@scorer(metrics=[accuracy(), stderr()])
def cubic_surface_map(mode: str = "auto"):
    """
    Inspect scorer that checks:
      - Q(F) == 0 (on-surface)
      - all Fi have the same degree D
      - gcd(Fi) == 1 (primitive)
      - if Sage is available or mode=="sage", compute δ (degree of image) and assert δ == D

    Returns Score(value=1|0) with explanation + metadata including D, δ, and witness info.
    """
    use_sage = None
    if mode.lower() == "sage":
        use_sage = True
    elif mode.lower() == "sympy":
        use_sage = False
    else:
        use_sage = None

    async def score(state: TaskState, target: Target):
        # parse target (surface/claims) and model output (map)
        # target may already be a dict (if dataset supplies structured targets)
        target_obj : Dict[str, Any]
        if isinstance(target, dict):
            target_obj = target
        else:
            try:
                target_obj = json.loads(str(target))
            except Exception:
                return Score(value=0, explanation="Target is not valid JSON", answer=str(state.output.completion))

        surface = target_obj.get("surface")
        claims = target_obj.get("claims", {})

        # model output
        # structured output preferred, else JSON in text
        data = None
        if getattr(state.output, "structured", None) is not None:
            data = state.output.structured
        else:
            try:
                data = json.loads(state.output.completion)
            except Exception:
                return Score(value=0, explanation="Model output is not JSON; enable structured output.", answer=state.output.completion)

        F = data.get("map")
        if F is None:
            return Score(value=0, explanation="Model JSON is missing 'map' key.", answer=state.output.completion)

        try:
            result = validate_map(surface=surface, F=F, claims=claims, use_sage=use_sage, verbose=True)
        except Exception as ex:
            return Score(value=0, explanation=f"Validation error: {ex}", answer=state.output.completion)

        explanation = "\n".join(result.messages)
        meta = result.to_dict()
        # main pass/fail based on ok
        return Score(value=1 if result.ok else 0, explanation=explanation, answer=state.output.completion, metadata=meta)

    return score
