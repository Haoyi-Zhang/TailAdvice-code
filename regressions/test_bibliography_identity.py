"""Regression checks for exact historical source locators and UTC ledger dates."""
import csv
from datetime import date
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from check_bibliography import locator, parse_bib, verification_date


class BibliographyIdentityTests(unittest.TestCase):
    def test_ps_source_uses_the_matching_cwi_report(self):
        with (ROOT / 'literature-calibration.csv').open(newline='', encoding='utf-8') as handle:
            record = next(r for r in csv.DictReader(handle) if r['id'] == 'I05')
        expected = 'https://ir.cwi.nl/pub/4678/04678D.pdf'
        self.assertEqual(record['full_text'], expected)
        self.assertIn('PNA-R9802', record['version_inspected'])
        self.assertIn('1998', record['version_inspected'])
        with (ROOT / 'external_resources.csv').open(newline='', encoding='utf-8') as handle:
            resource = next(r for r in csv.DictReader(handle)
                            if r['name'].startswith('Full-paper calibration I05:'))
        self.assertEqual(resource['scholarly_or_official_url'], expected)
        self.assertIn('PNA-R9802', resource['acquisition_method'])

    def test_nudge_m_uses_exact_historical_record(self):
        entry = next(e for e in parse_bib(ROOT / 'proofs/references.bib')
                     if e['key'] == 'charlet2024')
        with (ROOT / 'bibliography-verification.csv').open(newline='', encoding='utf-8') as handle:
            record = next(r for r in csv.DictReader(handle) if r['key'] == 'charlet2024')
        self.assertEqual(locator(entry),
                         ('arxiv', '2403.06588v1', 'https://arxiv.org/abs/2403.06588v1'))
        self.assertEqual(record['persistent_id'], '2403.06588v1')
        self.assertEqual(record['stable_url'], locator(entry)[2])

    def test_new_real_date_and_old_dates_are_accepted(self):
        today = date(2026, 10, 14)
        self.assertEqual(verification_date('2026-10-14', today=today), today)
        self.assertEqual(verification_date('2026-09-16', today=today), date(2026, 9, 16))

    def test_predictions_citation_uses_the_read_author_survey(self):
        entry = next(e for e in parse_bib(ROOT / 'proofs/references.bib')
                     if e['key'] == 'mitzenmacher2022')
        self.assertEqual(entry['entry_type'], 'misc')
        self.assertEqual(entry['fields']['year'], '2020')
        self.assertEqual(locator(entry),
                         ('arxiv', '2006.09123v1', 'https://arxiv.org/abs/2006.09123v1'))
        self.assertNotIn('doi', entry['fields'])
        with (ROOT / 'bibliography-verification.csv').open(newline='', encoding='utf-8') as handle:
            record = next(r for r in csv.DictReader(handle)
                          if r['key'] == 'mitzenmacher2022')
        self.assertEqual(record['persistent_id'], locator(entry)[1])
        self.assertEqual(record['stable_url'], locator(entry)[2])
        self.assertEqual(record['year'], '2020')

    def test_future_and_malformed_dates_are_rejected(self):
        for value in ('2026-10-15', '2026-13-14', '', 'not-a-date'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                verification_date(value, today=date(2026, 10, 14))


if __name__ == '__main__':
    unittest.main()
