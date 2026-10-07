"""Finite rational load-advice codebooks, with exact integer comparisons."""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as Q


@dataclass(frozen=True)
class Codebook:
    bits: int
    boundaries: tuple[Q, ...]
    certificates: tuple[Q, ...]

    def select(self, theta: Q) -> int:
        if not isinstance(theta, Q):
            raise TypeError("theta must be Fraction")
        if not self.boundaries[0] <= theta <= self.boundaries[-1]:
            raise ValueError("theta outside the public envelope")
        for j, upper in enumerate(self.boundaries[1:]):
            if theta <= upper:
                return j
        raise AssertionError("last boundary failed to cover theta")

    def message(self, index: int) -> str:
        if type(index) is not int or not 0 <= index < len(self.certificates):
            raise ValueError("code index outside codebook")
        return format(index, f"0{self.bits}b") if self.bits else ""

    @property
    def inflation_bound(self) -> Q:
        return max(c / lo for c, lo in zip(self.certificates, self.boundaries))


def ceil_grid_root(target: Q, degree: int, denominator: int, upper: Q) -> Q:
    """Smallest n/D with (n/D)^degree >= target; no floating-point roots."""
    if (not isinstance(target, Q) or not isinstance(upper, Q)
            or type(degree) is not int or type(denominator) is not int
            or target <= 0 or upper <= 0 or degree < 1 or denominator < 1):
        raise ValueError("invalid positive root parameters")
    scaled_upper = upper * denominator
    hi = -(-scaled_upper.numerator // scaled_upper.denominator)
    threshold = target.numerator * denominator ** degree
    target_denominator = target.denominator
    if hi ** degree * target_denominator < threshold:
        raise ValueError("upper bound does not bracket the root")
    lo = 0
    while lo < hi:
        mid = (lo + hi) // 2
        if mid ** degree * target_denominator >= threshold:
            hi = mid
        else:
            lo = mid + 1
    return Q(lo, denominator)


def make_codebook(bits: int, lower: Q = Q(2), upper: Q = Q(512),
                  slack: Q = Q(1, 8), denominator: int = 1024) -> Codebook:
    """Build 2**bits public entries; bits counts message bits, not table size.

    An explicit construction cap avoids accidentally requesting an enormous
    table. Increasing it would require a new resource assessment.
    """
    if type(bits) is not int or not 0 <= bits <= 8:
        raise ValueError("construction is bounded to integer bits in [0,8]")
    if not all(isinstance(x, Q) for x in (lower, upper, slack)):
        raise TypeError("envelope and slack must be Fraction")
    if (type(denominator) is not int or not Q(1) < lower < upper
            or slack <= 0 or denominator < 1):
        raise ValueError("require 1 < lower < upper, positive slack and grid")
    m = 1 << bits
    bounds = [lower]
    for j in range(1, m):
        target = lower ** (m - j) * upper ** j
        bounds.append(ceil_grid_root(target, m, denominator, upper))
    bounds.append(upper)
    if any(a >= b for a, b in zip(bounds, bounds[1:])):
        raise ValueError("grid is too coarse: adjacent bin boundaries coincide")
    certificates = tuple((1 + slack) * b for b in bounds[1:])
    return Codebook(bits, tuple(bounds), certificates)


def eulerian_polynomial(order: int) -> tuple[int, ...]:
    """A_order(z) from the Eulerian-number recurrence (order >= 1)."""
    if type(order) is not int or not 1 <= order <= 32:
        raise ValueError("order must be an integer in [1,32]")
    row = [1]
    for n in range(2, order + 1):
        old, row = row, []
        for k in range(n):
            row.append((k + 1) * (old[k] if k < len(old) else 0)
                       + (n - k) * (old[k - 1] if k else 0))
    return tuple(row)


def permanent_count_moment(order: int, load: Q) -> Q:
    if type(order) is not int or not 1 <= order <= 31:
        raise ValueError("moment order must be an integer in [1,31]")
    if not isinstance(load, Q) or not Q(0) <= load < 1:
        raise ValueError("load must be a Fraction in [0,1)")
    coefficients = eulerian_polynomial(order + 1)
    return sum((Q(c) * load ** k for k, c in enumerate(coefficients)), Q(0)) / (1 - load) ** order
