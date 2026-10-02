#!/usr/bin/env python3
"""Differentially check the exact simulator against a separate reference path.

The reference implementation below does not consume emitted schedule segments
or call the production event routine.  It reconstructs rates and breakpoints
from the policy definition with independent state variables.  Agreement is a
finite implementation check, not a proof of the continuous-time theorems.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from fractions import Fraction as Q
import itertools
import json
from pathlib import Path
import resource
import sys
import time
from typing import Iterable

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from model import Job, simulate  # production implementation under test


@dataclass(frozen=True)
class RefJob:
    release: Q
    size: Q


def reference_completion(
    jobs: Iterable[RefJob],
    guard: Q,
    *,
    speed: Q = Q(1),
    protect: str = "oldest",
    mutation: str = "none",
) -> tuple[Q, ...]:
    """Independent breakpoint reconstruction of guarded sharing completions."""
    js = tuple(jobs)
    if speed <= 0 or guard < 0 or guard > speed:
        raise ValueError("invalid speed/guard")
    if protect not in {"oldest", "youngest"}:
        raise ValueError("invalid protection rule")
    if mutation not in {"none", "extra_divisor", "omit_guard"}:
        raise ValueError("invalid mutation")
    n = len(js)
    if n == 0:
        return ()
    remaining = [job.size for job in js]
    completion: list[Q | None] = [None] * n
    not_released = sorted(range(n), key=lambda index: (js[index].release, index))
    release_cursor = 0
    active: list[int] = []
    now = Q(0)
    event_budget = 3 * n + 3
    event_count = 0

    while any(value is None for value in completion):
        while release_cursor < n and js[not_released[release_cursor]].release <= now:
            active.append(not_released[release_cursor])
            release_cursor += 1
        if not active:
            if release_cursor >= n:
                raise AssertionError("reference path lost unfinished work")
            now = js[not_released[release_cursor]].release
            continue

        ordered = sorted(active, key=lambda index: (js[index].release, index))
        protected = ordered[0] if protect == "oldest" else ordered[-1]
        divisor = len(active) + (1 if mutation == "extra_divisor" else 0)
        common = (speed - guard) / divisor
        rate: dict[int, Q] = {}
        for index in active:
            protected_increment = guard if index == protected and mutation != "omit_guard" else Q(0)
            rate[index] = common + protected_increment
        finish_times = [now + remaining[index] / rate[index]
                        for index in active if rate[index] > 0]
        if not finish_times:
            raise AssertionError("reference mutation produced permanent zero service")
        next_event = min(finish_times)
        if release_cursor < n:
            next_event = min(next_event, js[not_released[release_cursor]].release)
        if next_event <= now:
            raise AssertionError("reference event did not advance")
        duration = next_event - now
        for index in tuple(active):
            remaining[index] -= rate[index] * duration
            if remaining[index] < 0:
                raise AssertionError("reference residual became negative")
        now = next_event
        completed_now = [index for index in active if remaining[index] == 0]
        for index in completed_now:
            completion[index] = now
            active.remove(index)
        event_count += 1
        if event_count > event_budget:
            raise AssertionError("reference path exceeded arrival/completion event budget")
    return tuple(value for value in completion if value is not None)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    start = time.perf_counter()
    before = resource.getrusage(resource.RUSAGE_SELF)

    atoms = tuple(RefJob(Q(r, 2), Q(p, 2)) for r in (0, 1, 2) for p in (1, 2, 3))
    configurations = ((Q(1), Q(1, 4)), (Q(1), Q(1, 2)),
                      (Q(1), Q(3, 4)), (Q(3, 2), Q(1, 2)))
    instance_count = comparison_count = max_numerator_bits = max_denominator_bits = 0
    grouped: dict[tuple[int, str, str], int] = {}
    for n in range(1, 5):
        for records in itertools.combinations_with_replacement(atoms, n):
            instance_count += 1
            production_jobs = tuple(Job(record.release, record.size) for record in records)
            for speed, guard in configurations:
                expected = reference_completion(records, guard, speed=speed)
                observed = simulate(production_jobs, guard, speed=speed).completion
                if observed != expected:
                    raise AssertionError(
                        f"differential mismatch for n={n}, speed={speed}, guard={guard}: "
                        f"{observed!r} != {expected!r}"
                    )
                for value in expected:
                    max_numerator_bits = max(max_numerator_bits, value.numerator.bit_length())
                    max_denominator_bits = max(max_denominator_bits, value.denominator.bit_length())
                grouped[(n, str(speed), str(guard))] = grouped.get((n, str(speed), str(guard)), 0) + 1
                comparison_count += 1

    witness = (RefJob(Q(0), Q(2)), RefJob(Q(0), Q(1)), RefJob(Q(1, 2), Q(1)))
    correct = reference_completion(witness, Q(1, 2))
    mutation_results = {}
    for name, kwargs in {
        "protect_youngest": {"protect": "youngest", "mutation": "none"},
        "extra_divisor": {"protect": "oldest", "mutation": "extra_divisor"},
        "omit_guard": {"protect": "oldest", "mutation": "omit_guard"},
    }.items():
        mutated = reference_completion(witness, Q(1, 2), **kwargs)
        rejected = mutated != correct
        if not rejected:
            raise AssertionError(f"negative control {name} was not discriminating")
        mutation_results[name] = {
            "correct_completion": [str(value) for value in correct],
            "mutated_completion": [str(value) for value in mutated],
            "rejected": rejected,
        }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "reference-simulator-summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["jobs", "speed", "guard", "exact_instances", "status"])
        for (n, speed, guard), count in sorted(grouped.items()):
            writer.writerow([n, speed, guard, count, "matched"])

    after = resource.getrusage(resource.RUSAGE_SELF)
    report = {
        "scope": "finite exact differential implementation check; not an asymptotic theorem proof",
        "reference_implementation": "independent breakpoint reconstruction; production segments are not consumed",
        "atom_release_values": ["0", "1/2", "1"],
        "atom_size_values": ["1/2", "1", "3/2"],
        "maximum_jobs": 4,
        "unordered_instance_count": instance_count,
        "configuration_count_per_instance": len(configurations),
        "exact_completion_vector_comparisons": comparison_count,
        "max_completion_numerator_bits": max_numerator_bits,
        "max_completion_denominator_bits": max_denominator_bits,
        "negative_controls": mutation_results,
        "random_seed": None,
        "workers": 1,
        "network_used": False,
        "status": "passed",
        "wall_seconds": time.perf_counter() - start,
        "cpu_seconds": after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime,
        "peak_rss_bytes": after.ru_maxrss * 1024,
    }
    (args.output_dir / "reference-simulator.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
