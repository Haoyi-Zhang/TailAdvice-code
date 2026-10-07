"""Exact grid-root checks against a bounded linear Fraction reference."""
from fractions import Fraction as Q
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from advice import ceil_grid_root, make_codebook


def root_cases():
    for degree in (1, 2, 3, 4, 8, 256):
        for denominator in (1, 2, 3, 8):
            for numerator in range(1, 8):
                power = Q(numerator, denominator) ** degree
                for factor in (Q(999, 1000), Q(1), Q(1001, 1000)):
                    yield power * factor, degree, denominator, Q(8)


def linear_root(target, degree, denominator, upper):
    n = 0
    while Q(n, denominator) ** degree < target:
        n += 1
    scaled = upper * denominator
    if n > -(-scaled.numerator // scaled.denominator):
        raise ValueError("upper bound does not bracket the root")
    return Q(n, denominator)


class IntegerRootTests(unittest.TestCase):
    def test_exact_powers_and_neighbors(self):
        count = 0
        for target, degree, denominator, upper in root_cases():
            actual = ceil_grid_root(target, degree, denominator, upper)
            self.assertEqual(actual, linear_root(target, degree, denominator, upper))
            self.assertGreaterEqual(actual ** degree, target)
            self.assertLess((actual - Q(1, denominator)) ** degree, target)
            count += 1
        self.assertEqual(count, 504)

    def test_ceil_upper_is_the_search_bracket(self):
        self.assertEqual(ceil_grid_root(Q(1), 2, 1, Q(1, 2)), Q(1))
        self.assertEqual(ceil_grid_root(Q(1, 9), 2, 3, Q(1, 3)), Q(1, 3))
        for degree in (1, 2, 4, 256):
            with self.assertRaisesRegex(ValueError, "does not bracket"):
                ceil_grid_root(Q(3) ** degree, degree, 2, Q(2))

    def test_invalid_parameters(self):
        bad = ((True, 1, 1, Q(1)), (1, 1, 1, Q(1)),
               (Q(1), True, 1, Q(1)), (Q(1), 1, True, Q(1)),
               (Q(1), 0, 1, Q(1)), (Q(1), 1, 0, Q(1)),
               (Q(0), 1, 1, Q(1)), (Q(-1), 1, 1, Q(1)),
               (Q(1), 1, 1, Q(0)), (Q(1), 1, 1, Q(-1)),
               (Q(1), 1, 1, 1.0), (Q(1), 1.0, 1, Q(1)),
               (Q(1), 1, Q(1), Q(1)))
        for args in bad:
            with self.assertRaisesRegex(ValueError, "invalid positive"):
                ceil_grid_root(*args)

    def test_all_admitted_message_lengths(self):
        for bits in range(9):
            book = make_codebook(bits)
            self.assertEqual(len(book.certificates), 1 << bits)
            self.assertEqual(book.boundaries[0], Q(2))
            self.assertEqual(book.boundaries[-1], Q(512))
            for j, (lo, hi, certificate) in enumerate(zip(book.boundaries, book.boundaries[1:], book.certificates)):
                target = Q(2) ** ((1 << bits) - j - 1) * Q(512) ** (j + 1)
                self.assertGreaterEqual(hi ** (1 << bits), target)
                if j + 1 < 1 << bits:
                    self.assertLess((hi - Q(1, 1024)) ** (1 << bits), target)
                for theta in (lo, (lo + hi) / 2, hi):
                    selected = book.certificates[book.select(theta)]
                    self.assertGreater(selected, theta)
                    self.assertLessEqual(selected / theta, book.inflation_bound)
                self.assertEqual(certificate, Q(9, 8) * hi)
                self.assertEqual(len(book.message(j)), bits)

    def test_coarse_grid_refusal(self):
        with self.assertRaisesRegex(ValueError, "grid is too coarse"):
            make_codebook(8, lower=Q(2), upper=Q(3), denominator=1)


if __name__ == "__main__":
    unittest.main()
