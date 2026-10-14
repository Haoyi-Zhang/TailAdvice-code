"""A bounded report reading cannot be relabeled as a full-article reading."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_literature_calibration import reading_status_error


class LiteratureReadingScopeTests(unittest.TestCase):
    def report(self, **changes):
        row = {'id': 'I05', 'status': 'claim_scoped_report_read',
               'full_text': 'https://ir.cwi.nl/pub/4678/04678D.pdf',
               'version_inspected': '1998 CWI PNA-R9802 report'}
        return {**row, **changes}

    def test_matching_original_report_is_accepted(self):
        self.assertIsNone(reading_status_error(self.report()))

    def test_report_is_not_promoted_to_full_article(self):
        self.assertIsNotNone(reading_status_error(self.report(status='full_text_structural_read')))

    def test_unrelated_report_is_rejected(self):
        self.assertIsNotNone(reading_status_error(self.report(
            full_text='https://ir.cwi.nl/pub/4769/04769D.pdf')))

    def test_report_version_is_required(self):
        self.assertIsNotNone(reading_status_error(self.report(version_inspected='journal article')))

    def test_other_records_cannot_silently_change_depth(self):
        self.assertIsNone(reading_status_error({'id': 'S01', 'status': 'full_text_structural_read'}))
        for status in ('claim_scoped_report_read', 'passed', 'metadata_only', ''):
            with self.subTest(status=status):
                self.assertIsNotNone(reading_status_error({'id': 'S01', 'status': status}))


if __name__ == '__main__':
    unittest.main()
