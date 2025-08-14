
"""
cubic_inspect.validator
-----------------------

Core validators for a map f: P^1 -> P^3 lying on a cubic surface, with
helpers to check degree, on-surface substitution, primitivity (no common factor),
and—if SageMath is available—prove generic injectivity by computing the
degree of the Zariski-closure of the image curve via elimination.

Dependencies: sympy (always), optional sageall (if installed).
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Tuple, List, Optional, Any

import sympy as sp

# --------------------
# Parsing & utilities
# --------------------

def _poly_in(vars, expr: str) -> sp.Poly:
    """Parse `expr` into a SymPy polynomial in the given ordered `vars`."""
    local = {str(v): v for v in vars}
    try:
        e = sp.sympify(expr, locals=local)
    except Exception as ex:
        raise ValueError(f"Failed to parse polynomial '{expr}': {ex}") from ex
    P = sp.Poly(e, *vars, domain=sp.QQ)
    if not P.is_Poly:
        raise ValueError(f"Expression is not a polynomial in {vars}: {expr}")
    return P

def total_degree(poly: sp.Poly, vars) -> int:
    return max(sum(m) for m in poly.monoms()) if poly.total_degree() is None else poly.total_degree()

def gcd_many(polys: List[sp.Poly]) -> sp.Poly:
    g = polys[0]
    for h in polys[1:]:
        g = sp.gcd(g, h)
    # Make primitive (content 1)
    cont = sp.content(g.as_expr())
    if cont != 0:
        g = sp.Poly(g.as_expr() / cont, *g.gens, domain=sp.QQ)
    return g

# --------------------
# Validation result
# --------------------

@dataclass
class ValidationResult:
    ok: bool
    messages: List[str]
    on_surface: bool
    degree_map: Optional[int]
    image_degree: Optional[int]  # δ (requires Sage for proof)
    generically_injective: Optional[bool]  # True/False if proven, None if heuristic only
    gcd_is_one: bool
    heuristic_no_power_cover: bool
    nonfree_witness_s: Optional[int]  # if provided/verified
    extras: Dict[str, Any]

    def to_dict(self):
        d = asdict(self)
        return d

# --------------------
# Core validation
# --------------------

def validate_map(
    surface: str,
    F: Dict[str, str],
    claims: Optional[Dict[str, Any]] = None,
    use_sage: Optional[bool] = None,
    verbose: bool = True
) -> ValidationResult:
    """
    Validate a map f : P^1 -> P^3 given by 4 homogeneous polynomials F0..F3 in (s,t)
    against a cubic surface equation Q(W0..W3).

    Parameters
    ----------
    surface : str
        Polynomial Q(W0,W1,W2,W3) (homogeneous cubic) as a string.
    F : dict
        Keys 'F0','F1','F2','F3' with string polynomials in (s,t).
    claims : dict, optional
        May include: degree (int), nonfree (bool), generically_injective (bool), s_witness (int)
    use_sage : bool or None
        If True, attempt Sage-based exact image degree δ; if None, autodetect; if False, skip Sage.
    verbose : bool
        If True, include detailed messages.

    Returns
    -------
    ValidationResult
    """
    messages = []
    s, t = sp.symbols('s t')
    W0, W1, W2, W3 = sp.symbols('W0 W1 W2 W3')

    # Parse surface and Fs
    Q = _poly_in((W0, W1, W2, W3), surface)
    Fi = []
    for key in ['F0','F1','F2','F3']:
        if key not in F:
            raise ValueError(f"Missing key '{key}' in map F")
        Fi.append(_poly_in((s,t), F[key]))

    # Check homogeneity & common degree
    degs = [total_degree(P, (s,t)) for P in Fi]
    if len(set(degs)) != 1:
        messages.append(f"Coordinate degrees not equal: {degs}")
        D = None
    else:
        D = degs[0]
        messages.append(f"All coordinate degrees equal: D = {D}")

    # GCD primitivity
    g = gcd_many(Fi)
    gcd_one = (g.total_degree() == 0 and g.LC() == 1) or (g.as_expr() == 1)
    messages.append(f"gcd(F0..F3) == 1 ? {'YES' if gcd_one else 'NO'}")

    # On-surface check: Q(F)=0?
    Q_sub = Q.as_expr().subs({W0: Fi[0].as_expr(), W1: Fi[1].as_expr(),
                              W2: Fi[2].as_expr(), W3: Fi[3].as_expr()})
    Q_st = sp.Poly(sp.expand(Q_sub), s, t, domain=sp.QQ)
    on_surface = Q_st.is_zero
    messages.append(f"On-surface check Q(F)=0? {'PASS' if on_surface else 'FAIL'}")

    # Heuristic "no power cover" test: if all monomial exponents have gcd m>1, map factors through [s^m:t^m]
    def exponents(poly: sp.Poly):
        return poly.monoms()  # list of (a,b) with a+b=D
    all_exps = []
    for P in Fi:
        all_exps.extend(exponents(P))
    from math import gcd
    gexp = 0
    for (a,b) in all_exps:
        gexp = gcd(gexp, gcd(a,b))
    heuristic_no_power = (gexp == 1)
    messages.append(f"Heuristic power-cover test gcd(exp_s,exp_t) = {gexp} -> {'primitive' if heuristic_no_power else 'factors via power m='+str(gexp)}")

    # Attempt Sage-based exact image degree (δ) and generic injectivity proof
    image_degree = None
    generically_injective = None
    use_sage_flag = use_sage
    if use_sage_flag is None:
        # autodetect
        try:
            import sageall  # type: ignore
            use_sage_flag = True
        except Exception:
            use_sage_flag = False

    if use_sage_flag:
        try:
            image_degree = _image_degree_via_sage(surface, F)
            messages.append(f"Sage: degree(image curve) δ = {image_degree}")
            if D is not None and image_degree is not None:
                generically_injective = (image_degree == D)
                messages.append(f"Generic injectivity (δ == D)? {'YES' if generically_injective else 'NO'}")
        except Exception as ex:
            messages.append(f"Sage degree computation failed: {ex}")
            image_degree = None
            generically_injective = None

    # Non-free witness (optional): if user supplies s_witness (e.g. d-2), we report negative minimal summand
    nonfree_witness_s = None
    if claims and 's_witness' in claims:
        try:
            nonfree_witness_s = int(claims['s_witness'])
            if D is not None:
                a_min = 2 - nonfree_witness_s
                messages.append(f"Non-free witness: s={nonfree_witness_s} -> minimal summand O({a_min})")
        except Exception:
            messages.append("Provided s_witness not an int; ignoring.")

    # Overall ok: must be on_surface True, gcd_one True, and either (Sage proved δ==D) or (heuristic passes and no obvious power-cover)
    ok = on_surface and gcd_one
    if ok and D is not None:
        if generically_injective is True:
            ok = True
        elif generically_injective is False:
            ok = False
        else:
            # fall back on heuristic if no Sage
            ok = heuristic_no_power

    return ValidationResult(
        ok=ok,
        messages=messages,
        on_surface=on_surface,
        degree_map=D,
        image_degree=image_degree,
        generically_injective=generically_injective,
        gcd_is_one=gcd_one,
        heuristic_no_power_cover=heuristic_no_power,
        nonfree_witness_s=nonfree_witness_s,
        extras={"Q_zero_poly": str(Q_st.as_expr()) if on_surface else None}
    )

# --------------------
# Sage helper (optional)
# --------------------

def _image_degree_via_sage(surface: str, F: Dict[str, str]) -> int:
    """
    Compute the projective degree of the Zariski-closure of the image curve
    using Sage (Singular) elimination + Hilbert polynomial.
    """
    # delayed import
    from sageall import PolynomialRing, QQ, ideal

    # variables
    Sst = PolynomialRing(QQ, names=('s','t')); s,t = Sst.gens()
    Wring = PolynomialRing(QQ, names=('W0','W1','W2','W3')); W0,W1,W2,W3 = Wring.gens()
    R = PolynomialRing(QQ, names=('s','t','W0','W1','W2','W3'), order='lex')
    sR,tR,W0R,W1R,W2R,W3R = R.gens()

    # parse in Sage
    import sympy as sp
    # convert SymPy polys to strings then to Sage
    def to_sage_poly(expr: str, vars):
        # expr in Python string using s,t or W0..W3
        return R(str(sp.sympify(expr)), names=R.variable_names())

    F0 = to_sage_poly(F['F0'], (sR,tR))
    F1 = to_sage_poly(F['F1'], (sR,tR))
    F2 = to_sage_poly(F['F2'], (sR,tR))
    F3 = to_sage_poly(F['F3'], (sR,tR))

    # Ideal of graph
    I = ideal([W0R - F0, W1R - F1, W2R - F2, W3R - F3])

    # Eliminate parameters s,t
    Jgens = I.elimination_ideal([sR, tR]).gens()
    if not Jgens:
        raise RuntimeError("Elimination produced empty ideal; unexpected.")

    # Ideal in W0..W3 only
    RW = PolynomialRing(QQ, names=('W0','W1','W2','W3'))
    W0W,W1W,W2W,W3W = RW.gens()
    J = ideal([RW(str(g)) for g in Jgens])

    # Hilbert polynomial of projective coordinate ring (Sage computes on graded ring)
    P = J.hilbert_polynomial()
    # P(n) = δ n + (1-g) for curves in P^3
    # Extract δ as the coefficient of n^1
    # P is a polynomial in variable t (Sage uses 'x' usually), get coefficient of degree 1
    # Convert to string and parse quickly
    # Better: use .coefficients() with .degrees()
    degs = P.degrees()
    coeffs = P.coefficients()
    delta = 0
    for deg, c in zip(degs, coeffs):
        if deg == 1:
            delta = int(c)
    if delta == 0:
        # Fallback: try numeric estimate by evaluating P at 100 and 99
        delta = int(P(100) - P(99))
    return delta
