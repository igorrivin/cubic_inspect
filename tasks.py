
"""
cubic_inspect.tasks
-------------------

A minimal Inspect task that asks the model to produce a map f: P^1 -> cubic surface
in **structured JSON** and is then scored by the cubic_surface_map scorer.
"""

from __future__ import annotations
from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.solver import system_message, generate, structured_output

# JSON schema to force the model to return the polynomials
SCHEMA = {
  "type": "object",
  "properties": {
    "map": {
      "type": "object",
      "properties": {
        "F0": {"type": "string"},
        "F1": {"type": "string"},
        "F2": {"type": "string"},
        "F3": {"type": "string"}
      },
      "required": ["F0","F1","F2","F3"]
    }
  },
  "required": ["map"]
}

SYSTEM = """You are a math tool that outputs a parameterized rational map f: P^1 -> P^3
lying on a given cubic surface. Return JSON only.
Polynomials use variables s,t (for P^1) and W0..W3 (for the cubic surface)."""

PROMPT = """Construct a generically injective non-free rational map f: P^1 -> X
to the cubic surface X specified below. Return **only** JSON with keys { "map": {F0,F1,F2,F3} }.

Surface:
{surface}

Target degree (if provided): {degree}

Constraints:
- F0..F3 must be homogeneous polynomials in s,t of the same total degree
- The image should lie on the surface (so Q(F)=0)
- Prefer maps produced via a rational cuspidal plane curve (but any valid map is acceptable)
"""

@task
def fermat_degree15_task():
    # default surface: Fermat cubic
    surface = "W0^3 + W1^3 + W2^3 + W3^3"
    return Task(
        dataset=[Sample(
            input=[
                system_message(SYSTEM),
                structured_output(SCHEMA),
                PROMPT.format(surface=surface, degree=15),
            ],
            target={"surface": surface, "claims": {"degree": 15, "nonfree": True, "s_witness": 3}},
        )],
        solver=[generate()],
        scorer=("cubic_inspect.scorer", "cubic_surface_map"),
    )
