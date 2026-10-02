#!/usr/bin/env python3
"""Exact finite audits of algebraic proof interfaces and deliberate nonclaims.

These checks exercise formulas used by the written proof.  They are neither a
proof assistant nor an independent review of the stochastic/asymptotic steps.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
from fractions import Fraction as Q
from pathlib import Path
import resource
import sys
import time

if not __debug__:
    raise RuntimeError("verification requires Python without -O or -OO")

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from advice import make_codebook, permanent_count_moment  # noqa: E402


def avg(values: list[Q]) -> Q:
    return sum(values, Q(0)) / len(values)


def stationary_checks() -> dict[str, int | bool]:
    loads = (Q(1, 5), Q(1, 3), Q(1, 2), Q(4, 5))
    ordinary_balance = permanent_balance = convolution = moment_formula = 0
    for a in loads:
        # The two displayed probability generating functions evaluate to one.
        assert (1 - a) / (1 - a) == 1
        assert (1 - a) ** 2 / (1 - a) ** 2 == 1
        for n in range(65):
            ordinary = (1 - a) * a**n
            if n:
                previous = (1 - a) * a ** (n - 1)
                assert ordinary == a * previous
                ordinary_balance += 1
            permanent = (n + 1) * (1 - a) ** 2 * a**n
            convolution_value = sum(
                ((1 - a) * a**k) * ((1 - a) * a ** (n - k))
                for k in range(n + 1)
            )
            assert permanent == convolution_value
            convolution += 1
            if n:
                previous_permanent = n * (1 - a) ** 2 * a ** (n - 1)
                assert permanent * Q(n, n + 1) == a * previous_permanent
                permanent_balance += 1
        assert permanent_count_moment(1, a) == (1 + a) / (1 - a)
        assert permanent_count_moment(2, a) == (1 + 4 * a + a * a) / (1 - a) ** 2
        moment_formula += 2

    # Deliberate mutation: a single geometric count is not the convolution law.
    a = Q(1, 2)
    n = 2
    wrong = (1 - a) * a**n
    correct = (n + 1) * (1 - a) ** 2 * a**n
    assert wrong != correct
    return {
        "ordinary_balance_checks": ordinary_balance,
        "permanent_balance_checks": permanent_balance,
        "geometric_convolution_checks": convolution,
        "closed_moment_checks": moment_formula,
        "wrong_single_geometric_rejected": True,
    }


def harmonic_and_jensen_checks() -> dict[str, int | bool]:
    harmonic = jensen = 0
    # Equal-duration step paths cover every count word through length five.
    for length in range(2, 6):
        for word in itertools.product(range(4), repeat=length):
            x = [Q(n + 1) for n in word]
            assert avg([1 / z for z in x]) * avg(x) >= 1
            harmonic += 1
            for p in range(1, 7):
                assert avg(x) ** p <= avg([z**p for z in x])
                jensen += 1

    # A plausible but wrong denominator mutation must not pass the same bound.
    x = [Q(1), Q(1), Q(1)]
    mutated_product = avg([1 / (z + 1) for z in x]) * avg(x)
    assert mutated_product < 1
    return {
        "harmonic_mean_path_checks": harmonic,
        "jensen_path_moment_checks": jensen,
        "wrong_denominator_rejected": True,
    }


def deficit_checks() -> tuple[dict[str, int | bool], list[dict[str, str]]]:
    strict_cases = equality_method_cases = 0
    rows: list[dict[str, str]] = []
    rhos = sorted({Q(n, d) for d in range(3, 16) for n in range(1, d)})
    for idx, rho in enumerate(rhos):
        theta = 1 / (1 - rho)
        c = (1 + theta) / 2
        assert 1 <= c < theta
        threshold = 1 - 1 / c
        rho_k = (threshold + rho) / 2
        assert threshold < rho_k < rho
        kappa = (c + 1 / (1 - rho_k)) / 2
        K = 2 + idx % 11
        lam = rho / 2
        delta = 1 - kappa * (1 - rho_k)
        eps = min((kappa / c - 1) / 4, delta / 4, delta / (16 * K), Q(1, 8))
        eta = min(kappa / 2, delta / (8 * K * (lam + 1)))
        assert delta > 0 and eps > 0 and eta > 0
        assert c * (1 + 2 * eps) < kappa
        assert eps <= delta / 4
        assert lam * eta + 2 * eps <= delta / (4 * K)
        assert delta - eps - (lam * eta + 2 * eps) * K >= delta / 2
        strict_cases += 1
        if idx < 12:
            rows.append({
                "rho": str(rho), "theta": str(theta), "C": str(c),
                "rho_K": str(rho_k), "K": str(K), "kappa": str(kappa),
                "Delta": str(delta), "epsilon": str(eps), "eta": str(eta),
            })

        # At equality, every finite truncation has rho_K<rho, so the interval
        # C < kappa < 1/(1-rho_K) used by the strict proof is empty.
        c_eq = theta
        rho_k_eq = (rho + max(Q(0), rho - Q(1, 5))) / 2
        assert rho_k_eq < rho
        assert 1 / (1 - rho_k_eq) < c_eq
        equality_method_cases += 1

    return ({
        "strict_deficit_parameter_cases": strict_cases,
        "equality_method_boundary_cases": equality_method_cases,
        "equality_extension_not_claimed": True,
    }, rows)


def pareto_checks() -> dict[str, int]:
    truncated = integrated = scaled = 0
    for alpha in (2, 3, 4, 5):
        for p in range(alpha + 1, alpha + 5):
            for y in (2, 3, 5, 11, 101):
                # Pareto tail y^{-alpha}, support [1,infinity).
                truncated_moment = Q(alpha, p - alpha) * (Q(y) ** (p - alpha) - 1)
                scale = Q(y) ** p * Q(1, y**alpha)
                ratio = truncated_moment / scale
                target = Q(alpha, p - alpha)
                assert 0 < ratio < target
                assert target - ratio == target / Q(y) ** (p - alpha)
                truncated += 1
                integrated_tail = Q(1, alpha - 1) * Q(1, y ** (alpha - 1))
                assert integrated_tail == Q(y) * Q(1, y**alpha) / (alpha - 1)
                integrated += 1
                for c in (Q(1, 2), Q(2), Q(7, 3)):
                    # Exact regular-variation scaling for this Pareto family.
                    assert (Q(y) ** alpha) / ((c * y) ** alpha) == c ** (-alpha)
                    scaled += 1
    return {
        "pareto_truncated_moment_checks": truncated,
        "pareto_integrated_tail_checks": integrated,
        "pareto_scaling_checks": scaled,
    }


def covering_checks() -> dict[str, int | bool]:
    telescoping = grid_optima = codebook = 0
    for m in range(1, 9):
        u, v = Q(2), Q(512)
        # Rational nongeometric partitions still telescope exactly.
        bounds = [u]
        for j in range(1, m):
            bounds.append(u + (v - u) * Q(j * j, m * m))
        bounds.append(v)
        product = Q(1)
        for lo, hi in zip(bounds, bounds[1:]):
            product *= hi / lo
        assert product == v / u
        telescoping += 1

        # Exact finite-grid analogue: enumerate all partitions of a small
        # ordered grid and verify the minimax consecutive ratio.
        grid = tuple(Q(k) for k in range(2, 9))
        mm = min(m, len(grid) - 1)
        best: Q | None = None
        for cuts in itertools.combinations(range(1, len(grid) - 1), mm - 1):
            indices = (0,) + cuts + (len(grid) - 1,)
            worst = max(grid[b] / grid[a] for a, b in zip(indices, indices[1:]))
            if best is None or worst < best:
                best = worst
        assert best is not None
        # Any cover's worst ratio obeys gamma^m >= v/u (with repeated/empty
        # bins allowed only making the finite-grid statement weaker).
        assert best**mm >= grid[-1] / grid[0]
        grid_optima += 1

    for bits in range(6):
        cb = make_codebook(bits)
        assert cb.inflation_bound ** len(cb.certificates) >= Q(512, 2)
        codebook += 1
    return {
        "telescoping_cover_checks": telescoping,
        "finite_grid_minimax_checks": grid_optima,
        "rational_codebook_cover_checks": codebook,
        "continuous_infimum_not_claimed_attained": True,
    }


def regenerative_ratio_checks() -> dict[str, int | bool]:
    checks = 0
    examples = [
        [(Q(1, 2), 2, 1), (Q(1, 2), 5, 2)],
        [(Q(1, 3), 1, 0), (Q(1, 3), 3, 2), (Q(1, 3), 8, 5)],
        [(Q(2, 5), 4, 1), (Q(3, 5), 7, 6)],
    ]
    for law in examples:
        ev = sum(prob * v for prob, v, _ in law)
        eq = sum(prob * q for prob, _, q in law)
        ratio = eq / ev
        assert 0 <= ratio <= 1
        # Replicating every cycle reward and count leaves the arrival ratio.
        ev2 = sum(prob * (3 * v) for prob, v, _ in law)
        eq2 = sum(prob * (3 * q) for prob, _, q in law)
        assert ratio == eq2 / ev2
        checks += 1
    # A time-weighted ratio is generally different and cannot replace the
    # arrival-count reward without a separate Little-law argument.
    law = [(Q(1, 2), 2, 1, 100), (Q(1, 2), 5, 2, 1)]
    arrival_ratio = sum(p * q for p, v, q, t in law) / sum(p * v for p, v, q, t in law)
    time_ratio = sum(p * q * t for p, v, q, t in law) / sum(p * v * t for p, v, q, t in law)
    assert arrival_ratio != time_ratio
    return {
        "regenerative_arrival_ratio_checks": checks,
        "wrong_time_weighting_rejected": True,
    }


def write_obligation_ledger(path: Path) -> int:
    rows = [
        ("P01", "workload benchmark and FCFS optimum", "written proof plus exhaustive finite oracle", "finite-checked", "general continuous-time proof remains prose"),
        ("P02", "arrival-prefix reservation", "written integral argument plus trace checker", "finite-checked", "measurable-time generalization remains prose"),
        ("P03", "exact guarded-sharing factor", "written limiting family plus exact examples", "finite-checked", "supremum argument remains prose"),
        ("P04", "slower-PS pathwise domination", "written event-interval induction plus per-job finite traces", "finite-checked", "stationary common-empty-time extension remains prose"),
        ("P05", "ordinary and permanent-customer invariant laws", "generator proof plus balance/convolution/moment identities", "algebra-checked", "invariant-measure identification is not mechanized"),
        ("P06", "immortal-tag coupling", "written monotone coupling", "written-only", "coupling construction is not mechanized"),
        ("P07", "conditional PS response bound", "Cauchy-Schwarz/Jensen/Markov proof plus exhaustive step-path inequalities", "algebra-checked", "probability implication remains written"),
        ("P08", "regular-variation integrals", "written dyadic domination plus exact Pareto family checks", "example-checked", "general slowly varying case relies on written proof"),
        ("P09", "guarded-sharing tail upper bound", "P04-P08 composition", "written-only", "asymptotic composition is not proof-assistant checked"),
        ("P10", "growing-interval LLN", "written strong-law scaling argument", "written-only", "probability convergence is not simulated or mechanized"),
        ("P11", "finite-prefix capacity deficit", "written accounting plus exact rational parameter sweep", "algebra-checked", "event-to-path transfer remains written"),
        ("P12", "regenerative cycle reward identity", "written renewal-reward argument plus finite ratio checks", "algebra-checked", "stationary regenerative theorem is external background"),
        ("P13", "integrated-tail obstruction", "P10-P12 composition", "written-only", "strict inequality only; equality intentionally open"),
        ("P14", "M-policy covering lower bound", "written interval argument plus telescoping/grid checks", "algebra-checked", "continuous infimum proof remains prose"),
        ("P15", "rational geometric codebook", "constructive proof plus exact codebooks", "finite-checked", "infimum is not claimed attained"),
        ("P16", "equality boundary", "method-boundary checks show strict proof cannot be closed by finite truncation", "not-claimed", "requires a new theorem, not a continuity argument"),
    ]
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(("obligation_id", "obligation", "evidence", "status", "remaining_boundary"))
        w.writerows(rows)
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    wall, cpu = time.perf_counter(), time.process_time()

    report: dict[str, object] = {
        "scope": "exact finite audits of proof interfaces; not a proof assistant or independent mathematical review",
        "stationary": stationary_checks(),
        "conditional_bound": harmonic_and_jensen_checks(),
        "regular_variation": pareto_checks(),
        "covering": covering_checks(),
        "regeneration": regenerative_ratio_checks(),
        "workers": 1,
        "random_seed": None,
    }
    deficit, rows = deficit_checks()
    report["capacity_deficit"] = deficit
    with (args.output_dir / "deficit-parameters.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    report["proof_obligation_rows"] = write_obligation_ledger(args.output_dir / "proof-obligations.csv")
    report.update(
        wall_seconds=time.perf_counter() - wall,
        cpu_seconds=time.process_time() - cpu,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        status="passed",
    )
    (args.output_dir / "proof-obligations.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
