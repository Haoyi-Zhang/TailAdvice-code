"""Independent trace checks and an exhaustive integer-slot deadline oracle."""
from __future__ import annotations
from fractions import Fraction as Q
from functools import lru_cache
from model import Job, Schedule

if not __debug__:
    raise RuntimeError("verification requires Python without -O or -OO")


def service_at(schedule: Schedule, job_id: int, time: Q) -> Q:
    total = Q(0)
    for s in schedule.segments:
        if s.start >= time:
            break
        total += dict(s.rates).get(job_id, Q(0)) * (min(time, s.end) - s.start)
    return total


def validate_trace(jobs: tuple[Job, ...], schedule: Schedule, speed: Q = Q(1)) -> None:
    assert isinstance(speed, Q) and speed > 0, "invalid capacity"
    assert all(isinstance(c, Q) for c in schedule.completion), "inexact completion"
    assert len(schedule.completion) == len(jobs), "completion length"
    last_end = Q(0)
    for s in schedule.segments:
        assert isinstance(s.start, Q) and isinstance(s.end, Q), "inexact segment time"
        assert all(isinstance(v, Q) for _, v in s.rates), "inexact rate"
        assert s.start >= last_end and s.end > s.start, "overlapping/nonpositive segments"
        assert all(type(i) is int for i, _ in s.rates), "noninteger job identifier"
        ids = [i for i, _ in s.rates]
        assert len(ids) == len(set(ids)), "duplicate rate"
        assert sum(v for _, v in s.rates) <= speed, "capacity violation"
        for i, v in s.rates:
            assert 0 <= i < len(jobs) and v >= 0, "invalid rate"
            if v:
                assert jobs[i].release <= s.start, "service before release"
                assert schedule.completion[i] >= s.end, "service after completion"
        last_end = s.end
    for i, j in enumerate(jobs):
        c = schedule.completion[i]
        assert c >= j.release, "completion before release"
        assert service_at(schedule, i, c) == j.size, "incorrect delivered service"
        for s in schedule.segments:
            if s.end < c:
                assert service_at(schedule, i, s.end) < j.size, "late reported completion"
    # Busy gaps are not allowed in a work-conserving model.
    points = sorted({Q(0), *(j.release for j in jobs), *schedule.completion,
                     *(s.start for s in schedule.segments), *(s.end for s in schedule.segments)})
    for a, b in zip(points, points[1:]):
        mid = (a + b) / 2
        pending = any(j.release <= mid < schedule.completion[i] for i, j in enumerate(jobs))
        used = sum(sum(v for _, v in s.rates) for s in schedule.segments if s.start <= mid < s.end)
        assert used == (speed if pending else 0), "work conservation violation"


def validate_prefix_reservation(jobs: tuple[Job, ...], schedule: Schedule, guard: Q) -> None:
    for a in sorted({j.release for j in jobs}):
        prefix = [i for i, j in enumerate(jobs) if j.release <= a]
        end = max(schedule.completion[i] for i in prefix)
        initial = sum(service_at(schedule, i, a) for i in prefix)
        points = {a, end}
        points.update(s.end for s in schedule.segments if a < s.end < end)
        for t in points:
            used = sum(service_at(schedule, i, t) for i in prefix) - initial
            assert used >= guard * (t - a), "prefix reservation violated"


def validate_domination(jobs: tuple[Job, ...], fast: Schedule, slow: Schedule) -> None:
    points = ({s.start for s in fast.segments} | {s.end for s in fast.segments}
              | {s.start for s in slow.segments} | {s.end for s in slow.segments}
              | {j.release for j in jobs})
    for i in range(len(jobs)):
        assert fast.completion[i] <= slow.completion[i], "completion domination violated"
        for t in points:
            assert service_at(fast, i, t) >= service_at(slow, i, t), "service domination violated"


def slotted_max_flow_oracle(jobs: tuple[Job, ...]) -> tuple[int, int]:
    """Enumerate deadline-feasible unit-slot schedules, including deliberate idle.

    Returns the optimum in this finite slotted model and visited DP states.
    No queue-tail or general continuous-time theorem is checked by this oracle.
    """
    if not jobs:
        return 0, 1
    if any(j.release.denominator != 1 or j.size.denominator != 1 for j in jobs):
        raise ValueError("oracle accepts integer jobs only")
    release = tuple(int(j.release) for j in jobs)
    sizes = tuple(int(j.size) for j in jobs)
    visited = 0
    for deadline_offset in range(max(sizes), sum(sizes) + max(release) + 1):
        deadline = tuple(r + deadline_offset for r in release)

        @lru_cache(None)
        def feasible(t: int, rem: tuple[int, ...]) -> bool:
            nonlocal visited
            visited += 1
            if not any(rem):
                return True
            if any(v and t >= d for v, d in zip(rem, deadline)):
                return False
            choices = [i for i, v in enumerate(rem) if v and release[i] <= t]
            for i in choices:
                nxt = list(rem)
                nxt[i] -= 1
                if feasible(t + 1, tuple(nxt)):
                    return True
            return feasible(t + 1, rem)  # Explicitly retain idle as an oracle choice.

        if feasible(0, sizes):
            return deadline_offset, visited
    raise AssertionError("serial schedule should always be feasible")
