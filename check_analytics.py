#!/usr/bin/env python3
"""Exact finite identities and codebook checks, not asymptotic verification."""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path
import resource
import sys
import time
from fractions import Fraction as Q
if not __debug__:
    raise RuntimeError("verification requires Python without -O or -OO")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from advice import make_codebook, eulerian_polynomial, permanent_count_moment


def derivative_polynomials(max_order: int) -> list[tuple[int, ...]]:
    # Independently differentiate sum_{n>=0} (n+1)^m z^n.  This uses
    # polynomial coefficients, not the Eulerian recurrence used by advice.py.
    p = [1]
    out = [tuple(p)]
    for m in range(max_order):
        q = [0] * (len(p) + 1)
        for k, c in enumerate(p):
            q[k] += c
            q[k + 1] += m * c
            if k:
                q[k] += k * c
                q[k + 1] -= k * c
        while len(q) > 1 and q[-1] == 0:
            q.pop()
        p = q
        out.append(tuple(p))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    wall, cpu = time.perf_counter(), time.process_time()
    derivative = derivative_polynomials(9)
    moment_checks = balance_checks = selection_checks = 0
    loads = (Q(1,4), Q(1,2), Q(3,4), Q(9,10))
    for p in range(1, 9):
        coeff = eulerian_polynomial(p + 1)
        assert coeff == derivative[p + 1]
        assert sum(coeff) == math.factorial(p + 1)
        for a in loads:
            moment = permanent_count_moment(p, a)
            assert moment <= Q(math.factorial(p + 1)) / (1 - a) ** p
            moment_checks += 1
    for a in loads:
        for n in range(1, 65):
            pn = (n + 1) * (1 - a) ** 2 * a ** n
            prev = n * (1 - a) ** 2 * a ** (n - 1)
            assert pn * Q(n, n + 1) == a * prev
            balance_checks += 1
    # A plain geometric customer count is wrong in the permanent-customer model.
    a = Q(1,2)
    wrong_prev, wrong_pn = 1-a, (1-a)*a
    assert wrong_pn * Q(1,2) != a * wrong_prev
    assert permanent_count_moment(1, a) == (1+a)/(1-a)
    rows, entries, max_bits = [], [], 0
    for bits in range(5):
        cb = make_codebook(bits)
        m = len(cb.certificates)
        assert m == 2 ** bits
        assert len(set(cb.message(j) for j in range(m))) == m
        for j, (lo, hi, c) in enumerate(zip(cb.boundaries, cb.boundaries[1:], cb.certificates)):
            target = Q(2) ** (m-j-1) * Q(512) ** (j+1)
            assert hi ** m >= target
            if j+1 < m:
                assert (hi-Q(1,1024)) ** m < target
            for theta in (lo, (lo+hi)/2, hi):
                idx = cb.select(theta)
                selected = cb.certificates[idx]
                assert selected > theta
                assert selected/theta <= cb.inflation_bound
                assert 1-1/theta < 1-1/selected  # rho < residual PS capacity
                selection_checks += 1
            for v in (lo, hi, c):
                max_bits = max(max_bits, v.numerator.bit_length(), v.denominator.bit_length())
            entries.append(dict(bits=bits,index=j,message=cb.message(j),lower=str(lo),upper=str(hi),
                                certificate=str(c),guard=str(1/c)))
        # Covering lower bound checked without taking an inexact root.
        assert cb.inflation_bound ** m >= 256
        rows.append(dict(bits=bits,policies=m,infimum_approx=256 ** (1/m),
                         rational_inflation=str(cb.inflation_bound),
                         inflation_approx=float(cb.inflation_bound)))
    for invalid in (Q(1), Q(513)):
        try:
            make_codebook(1).select(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError("out-of-envelope selection accepted")
    # Check explicit fluid-lemma constants for Pareto(alpha=2, minimum=1).
    fluid_rows=[]
    for rho, c in ((Q(1,2),Q(1)),(Q(3,4),Q(2)),(Q(9,10),Q(3))):
        lam=rho/2
        k=16
        rho_k=rho*(1-Q(1,k))
        assert rho_k>1-1/c
        kappa=(c+1/(1-rho_k))/2
        delta=1-kappa*(1-rho_k)
        eps=min((kappa/c-1)/4,delta/4,delta/(16*k),Q(1,8))
        eta=min(kappa/2,delta/(8*k*(lam+1)))
        assert c*(1+2*eps)<kappa
        assert eps<=delta/4
        assert lam*eta+2*eps<=delta/(4*k)
        assert delta-eps-(lam*eta+2*eps)*k>=delta/2
        fluid_rows.append(dict(rho=str(rho),C=str(c),K=k,kappa=str(kappa),Delta=str(delta),
                               epsilon=str(eps),eta=str(eta)))
    for name, data in (("advice.csv",rows),("codebook.csv",entries),("fluid_constants.csv",fluid_rows)):
        with (args.output_dir/name).open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    report=dict(scope="finite algebra and encoding checks, not a stationary or asymptotic proof",
                polynomial_orders=list(range(1,9)),moment_checks=moment_checks,
                stationary_balance_checks=balance_checks,codebooks=5,codebook_entries=len(entries),
                selection_checks=selection_checks,max_codebook_fraction_bits=max_bits,
                fluid_parameter_cases=len(fluid_rows),wrong_geometric_count_rejected=True,
                out_of_envelope_requests_rejected=True,workers=1,random_seed=None,
                wall_seconds=time.perf_counter()-wall,cpu_seconds=time.process_time()-cpu,
                peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,status="passed")
    (args.output_dir/"analytics.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__": main()
