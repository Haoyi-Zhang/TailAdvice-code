"""Exact finite-job models for guarded processor sharing.

All event times and service amounts use Fraction.  This module is a finite
model, not an implementation of a stationary queue or an asymptotic proof.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as Q
from typing import Iterable


@dataclass(frozen=True)
class Job:
    release: Q
    size: Q

    def __post_init__(self) -> None:
        if not isinstance(self.release, Q) or not isinstance(self.size, Q):
            raise TypeError("release and size must be fractions.Fraction")
        if self.release < 0 or self.size <= 0:
            raise ValueError("release must be nonnegative and size positive")


@dataclass(frozen=True)
class Segment:
    start: Q
    end: Q
    rates: tuple[tuple[int, Q], ...]


@dataclass(frozen=True)
class Schedule:
    completion: tuple[Q, ...]
    segments: tuple[Segment, ...]


def simulate(jobs: Iterable[Job], guard: Q, *, speed: Q = Q(1),
             protect: str = "oldest") -> Schedule:
    """Serve guard to the oldest job and share speed-guard equally.

    protect='youngest' is an intentionally incorrect negative control.
    guard=0 is ordinary processor sharing at the specified speed.
    The simulator sees sizes ONLY to detect the next completion; the rate
    rule itself uses releases, identifiers and the active set, not sizes.
    """
    js = tuple(jobs)
    if not isinstance(guard, Q) or not isinstance(speed, Q):
        raise TypeError("guard and speed must be Fraction")
    if speed <= 0 or not Q(0) <= guard <= speed:
        raise ValueError("require positive speed and 0 <= guard <= speed")
    if protect not in {"oldest", "youngest"}:
        raise ValueError("unknown protection order")
    n = len(js)
    if not n:
        return Schedule((), ())
    order = sorted(range(n), key=lambda i: (js[i].release, i))
    rem = [j.size for j in js]
    done: list[Q | None] = [None] * n
    active: set[int] = set()
    cursor = 0
    t = Q(0)
    segments: list[Segment] = []
    events = 0
    while any(c is None for c in done):
        while cursor < n and js[order[cursor]].release <= t:
            active.add(order[cursor])
            cursor += 1
        if not active:
            if cursor == n:
                raise AssertionError("unfinished job lost")
            t = js[order[cursor]].release
            continue
        selected = sorted(active, key=lambda i: (js[i].release, i))
        protected = selected[0] if protect == "oldest" else selected[-1]
        base = (speed - guard) / len(active)
        rates = {i: base + (guard if i == protected else 0) for i in active}
        until_finish = min(rem[i] / v for i, v in rates.items() if v > 0)
        dt = until_finish
        if cursor < n:
            dt = min(dt, js[order[cursor]].release - t)
        if dt <= 0:
            raise AssertionError("event advance must be positive")
        segments.append(Segment(t, t + dt, tuple(sorted(rates.items()))))
        for i, v in rates.items():
            rem[i] -= v * dt
            if rem[i] < 0:
                raise AssertionError("negative residual")
        t += dt
        finished = [i for i in active if rem[i] == 0]
        for i in finished:
            done[i] = t
            active.remove(i)
        events += 1
        if events > 2 * n:
            raise AssertionError("more event steps than arrivals plus completions")
    return Schedule(tuple(c for c in done if c is not None), tuple(segments))


def fcfs(jobs: Iterable[Job]) -> Schedule:
    js = tuple(jobs)
    c = [Q(0)] * len(js)
    seg = []
    t = Q(0)
    for i in sorted(range(len(js)), key=lambda i: (js[i].release, i)):
        t = max(t, js[i].release)
        seg.append(Segment(t, t + js[i].size, ((i, Q(1)),)))
        t += js[i].size
        c[i] = t
    return Schedule(tuple(c), tuple(seg))


def max_flow(jobs: Iterable[Job], schedule: Schedule) -> Q:
    js = tuple(jobs)
    if len(js) != len(schedule.completion):
        raise ValueError("completion vector has wrong length")
    return max((c - j.release for j, c in zip(js, schedule.completion)), default=Q(0))


def long_job_stream(guard: Q, subdivisions: int, horizon: Q) -> tuple[Job, ...]:
    """The deterministic tightness family: size 1 then jobs of size r*h."""
    if not Q(0) < guard < 1 or subdivisions < 1 or horizon <= 0:
        raise ValueError("invalid tightness-family parameters")
    h = Q(1, subdivisions)
    rate = 1 - guard / 2
    count = int(horizon / h)
    return (Job(Q(0), Q(1)),) + tuple(
        Job(k * h, rate * h) for k in range(1, count + 1))
