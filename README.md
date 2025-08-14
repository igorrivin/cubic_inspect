
# cubic_inspect

Inspect‑AI–friendly validators and scorers for rational maps \( f:\mathbb{P}^1 \to X \) with \( X \subset \mathbb{P}^3 \) a cubic surface.

## What it does

- **Checks**: same-degree coordinates, **on‑surface** \(Q(F)=0\), **primitivity** \( \gcd(F_i)=1 \)
- **Proves generic injectivity** if **Sage** is available by computing the **degree \(\delta\)** of the image curve and checking \(\delta = D\).
- **Heuristic** fallbacks (no Sage): detects trivial power-covers and reports confidence.

## Install

```bash
pip install sympy inspect-ai
# optional for exact degree / injectivity proof
# (ensure SageMath is installed in your environment)
```

## 1) Use directly from Python

```python
from cubic_inspect.validator import validate_map

surface = "W0^3 + W1^3 + W2^3 + W3^3"
F = {
  "F0": "s^5",
  "F1": "s*t^4",
  "F2": "t^5",
  "F3": "s^4*t"  # example only; must satisfy Q(F)=0 to pass
}
res = validate_map(surface, F, claims={"degree": 15, "s_witness": 3}, use_sage=None)
print(res.ok, res.messages, res.to_dict())
```

## 2) As an Inspect scorer

```bash
inspect eval cubic_inspect/tasks.py:fermat_degree15_task --model openai/gpt-4o
# or score an existing log
inspect score ./logs/....eval --scorer cubic_inspect/scorer.py@cubic_surface_map -S mode=sage
```

The scorer expects the **target** to contain the `surface` polynomial (string) and optional `claims`. The **model output** must be JSON:
```json
{"map":{"F0":"...","F1":"...","F2":"...","F3":"..."}} 
```

## 3) CLI (no Inspect needed)

Run directly from the cubic_inspect directory:
```bash
python cubic_cli.py \
  --surface "W0^3 + W1^3 + W2^3 + W3^3" \
  --F0 "s^5" --F1 "s*t^4" --F2 "t^5" --F3 "s^4*t" \
  --degree 15 --s_witness 3 --sage auto
```

Or run as a module from the parent directory:
```bash
python -m cubic_inspect \
  --surface "W0^3 + W1^3 + W2^3 + W3^3" \
  --F0 "s^5" --F1 "s*t^4" --F2 "t^5" --F3 "s^4*t" \
  --degree 15 --s_witness 3 --sage auto
```

**Outputs** a JSON report with pass/fail and diagnostics.

## Notes

- If Sage is available, we use elimination + Hilbert polynomial to compute the **image degree** \(\delta\). For curves in \(\mathbb{P}^3\), \(\delta\) is the coefficient of \(n\) in the Hilbert polynomial, so \(\delta=D\) certifies **generic injectivity**.
- Without Sage, we still do exact algebra for \(Q(F)=0\) and \(\gcd(F_i)=1\) (SymPy over \(\mathbb{Q}\)), and apply a **power-cover** heuristic.
- See Inspect docs on **Scorers**, **Tasks**, and **Structured Output** for how this integrates with evals. 
  - Scorers: https://inspect.aisi.org.uk/scorers.html
  - Tasks: https://inspect.aisi.org.uk/tasks.html
  - Structured output: https://inspect.aisi.org.uk/structured.html
