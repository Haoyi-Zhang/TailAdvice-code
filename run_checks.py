#!/usr/bin/env python3
"""Run deterministic, exact finite checks; never fit an asymptotic tail."""
from __future__ import annotations
import argparse
import csv
import itertools
import json
from pathlib import Path
import resource
import sys
import time
from fractions import Fraction as Q

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from model import Job, Schedule, Segment, fcfs, long_job_stream, max_flow, simulate
from checker import (slotted_max_flow_oracle, validate_domination,
                     validate_prefix_reservation, validate_trace)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "checks.json")
    args = parser.parse_args()
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    max_n = 3 if args.pilot else 5
    types = tuple(Job(Q(r), Q(p)) for r in range(3) for p in (1, 2))
    guards = (Q(1, 2),) if args.pilot else (Q(1, 4), Q(1, 2), Q(3, 4))
    instances = policy_checks = oracle_states = max_bits = 0
    rows = []
    for n in range(1, max_n + 1):
        for js in itertools.combinations_with_replacement(types, n):
            instances += 1
            oracle, states = slotted_max_flow_oracle(js)
            oracle_states += states
            reference = fcfs(js)
            assert max_flow(js, reference) == oracle, "FCFS disagrees with independent slot oracle"
            validate_trace(js, reference)
            for guard in guards:
                actual = simulate(js, guard)
                slow = simulate(js, Q(0), speed=1 - guard)
                validate_trace(js, actual)
                validate_trace(js, slow, 1 - guard)
                validate_prefix_reservation(js, actual, guard)
                validate_domination(js, actual, slow)
                assert max_flow(js, actual) * guard <= oracle, "competitive bound violated"
                for t in actual.completion:
                    max_bits = max(max_bits, t.numerator.bit_length(), t.denominator.bit_length())
                policy_checks += 1
                rows.append({"case": f"case-{instances:04d}",
                             "jobs_release_size": ";".join(f"{j.release}:{j.size}" for j in js),
                             "guard": str(guard), "oracle_max_flow": oracle,
                             "oracle_states": states,
                             "fcfs_completion": ";".join(map(str, reference.completion)),
                             "guarded_completion": ";".join(map(str, actual.completion)),
                             "slow_ps_completion": ";".join(map(str, slow.completion)),
                             "guarded_max_flow": str(max_flow(js, actual)),
                             "checks": "passed"})
    guard = Q(1, 2)
    js = long_job_stream(guard, 8 if args.pilot else 16, Q(3))
    good = simulate(js, guard)
    bad = simulate(js, guard, protect="youngest")
    validate_trace(js, good)
    validate_trace(js, bad)
    opt = max_flow(js, fcfs(js))
    assert max_flow(js, good) <= opt / guard
    assert max_flow(js, bad) > opt / guard, "wrong-oldest negative control was not discriminating"
    try:
        validate_prefix_reservation(js, bad, guard)
    except AssertionError:
        rejected_wrong_guard = True
    else:
        raise AssertionError("checker failed to reject wrong reservation")
    # A malformed certificate must fail conservation.
    corrupt = Schedule(tuple(c + 1 for c in good.completion), good.segments)
    try:
        validate_trace(js, corrupt)
    except AssertionError:
        rejected_bad_completion = True
    else:
        raise AssertionError("checker accepted incorrect completion times")
    report = {
        "scope": "exact finite checks, not a general or mechanized asymptotic proof",
        "mode": "pilot" if args.pilot else "full",
        "integer_instance_count": instances,
        "policy_comparison_count": policy_checks,
        "integer_max_jobs": max_n,
        "integer_release_set": [0, 1, 2],
        "integer_size_set": [1, 2],
        "guard_values": [str(g) for g in guards],
        "oracle_visited_states": oracle_states,
        "max_completion_fraction_bits": max_bits,
        "negative_control": {
            "job_count": len(js), "optimal_max_flow": str(opt),
            "guard": str(guard), "correct_max_flow": str(max_flow(js, good)),
            "wrong_guard_max_flow": str(max_flow(js, bad)),
            "wrong_guard_rejected": rejected_wrong_guard,
            "incorrect_completion_rejected": rejected_bad_completion,
        },
        "random_seed": None,
        "workers": 1,
        "wall_seconds": time.perf_counter() - start_wall,
        "cpu_seconds": time.process_time() - start_cpu,
        "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024,
        "status": "passed",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.with_name(args.output.stem + "-cases.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
