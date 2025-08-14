
"""
Simple CLI to validate a map f: P^1 -> cubic surface.
Usage example:

python cubic_inspect/cubic_cli.py \
  --surface "W0^3 + W1^3 + W2^3 + W3^3" \
  --F0 "s^5" --F1 "s*t^4" --F2 "t^5" --F3 "s^4*t" \
  --degree 15 --s_witness 3 --sage auto
"""

import argparse, json
import sys
from pathlib import Path

# Add parent directory to path to enable imports when run directly
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from cubic_inspect.validator import validate_map

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--surface", required=True, help="Cubic polynomial Q(W0..W3)")
    ap.add_argument("--F0", required=True)
    ap.add_argument("--F1", required=True)
    ap.add_argument("--F2", required=True)
    ap.add_argument("--F3", required=True)
    ap.add_argument("--degree", type=int, default=None)
    ap.add_argument("--s_witness", type=int, default=None, help="Optional vanishing-order witness s")
    ap.add_argument("--sage", choices=["auto","on","off"], default="auto", help="Use Sage for exact image degree")
    args = ap.parse_args()

    use_sage = None if args.sage == "auto" else (args.sage == "on")

    claims = {}
    if args.degree is not None:
        claims["degree"] = args.degree
    if args.s_witness is not None:
        claims["s_witness"] = args.s_witness

    res = validate_map(
        surface=args.surface,
        F={"F0": args.F0, "F1": args.F1, "F2": args.F2, "F3": args.F3},
        claims=claims,
        use_sage=use_sage,
        verbose=True
    )
    print(json.dumps(res.to_dict(), indent=2))

if __name__ == "__main__":
    main()
