"""Exact search-bound and minimality regressions for rational codebook roots."""
from fractions import Fraction as Q
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from advice import ceil_grid_root


class AdviceRootTests(unittest.TestCase):
    def test_nonpositive_upper_rejected(self):
        # Previously (-2)**2 bracketed the target while the search interval
        # was empty, so the helper returned zero for a strictly positive root.
        for upper in (Q(-2), Q(-1), Q(0)):
            for degree in (1, 2, 3, 4):
                with self.subTest(upper=upper, degree=degree):
                    with self.assertRaises(ValueError):
                        ceil_grid_root(Q(1), degree, 1, upper)

    def test_positive_unbracketed_root_rejected(self):
        for degree in range(1, 7):
            with self.subTest(degree=degree):
                with self.assertRaises(ValueError):
                    ceil_grid_root(Q(5) ** degree, degree, 3, Q(4))

    def test_exhaustive_minimal_grid_point(self):
        # 6 * 5 * 20 * 2 = 1,200 finite cases. The reference is a linear
        # search over the grid, independent of production binary search.
        for degree in range(1, 7):
            for denominator in range(1, 6):
                for numerator in range(1, 21):
                    for target_denominator in (1, 3):
                        target = Q(numerator, target_denominator)
                        upper = Q(20)
                        expected = next(Q(n, denominator)
                                        for n in range(20 * denominator + 1)
                                        if Q(n, denominator) ** degree >= target)
                        with self.subTest(degree=degree, denominator=denominator,
                                          target=target):
                            observed = ceil_grid_root(target, degree, denominator, upper)
                            self.assertEqual(observed, expected)
                            self.assertGreaterEqual(observed ** degree, target)
                            self.assertLess((observed - Q(1, denominator)) ** degree, target)


if __name__ == "__main__":
    unittest.main()
