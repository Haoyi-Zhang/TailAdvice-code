#!/usr/bin/env python3
"""Validate the retained 12/5/5 full-paper structural calibration without network access.

This checker validates record completeness and internal consistency. It does not
verify the scholarly claims, certify novelty, or independently review proofs.
"""
from __future__ import annotations
import argparse
import csv
from collections import Counter
from datetime import date
import json
from pathlib import Path
import re
import resource
import time

ROOT = Path(__file__).resolve().parent
FIELDS = (
    'group','id','full_citation','year','venue','official_record','full_text',
    'version_inspected','reading_scope','motivating_problem','general_principle',
    'main_result_boundary','proof_or_performance_architecture','practical_connection',
    'evaluation_breadth','artifact_strength','narrative_sequence','section_pattern',
    'bibliography_size_band','figure_table_roles','relation_to_current',
    'distinction_or_overlap','status','checked_on'
)
EXPECTED = {'same_venue':12, 'influential':5, 'adjacent':5}
EXPECTED_IDS = {
    *(f'S{i:02d}' for i in range(1,13)),
    *(f'I{i:02d}' for i in range(1,6)),
    *(f'A{i:02d}' for i in range(1,6)),
}
BANDS = {'compact (<=20)','medium (21–50)','large (>50)'}
STATUS = 'full_text_structural_read'


def main() -> None:
    if not __debug__:
        raise SystemExit('Verification cannot run under python -O or -OO.')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT/'results')
    args=parser.parse_args()
    started=time.perf_counter()
    before=resource.getrusage(resource.RUSAGE_SELF)
    csv_path=ROOT/'literature-calibration.csv'
    md_path=ROOT/'literature-calibration.md'
    with csv_path.open(newline='',encoding='utf-8') as f:
        reader=csv.DictReader(f)
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise SystemExit('Unexpected literature-calibration.csv header.')
        rows=list(reader)
    failures=[]
    if len(rows) != 22:
        failures.append(f'expected 22 rows, observed {len(rows)}')
    ids=[r['id'] for r in rows]
    if len(ids) != len(set(ids)):
        failures.append('duplicate identifiers')
    if set(ids) != EXPECTED_IDS:
        failures.append('identifier set differs from S01–S12, I01–I05, A01–A05')
    counts=Counter(r['group'] for r in rows)
    if dict(counts) != EXPECTED:
        failures.append(f'group counts differ: {dict(counts)}')
    years=[]
    checked_dates=[]
    for line,r in enumerate(rows,start=2):
        missing=[field for field in FIELDS if not r.get(field,'').strip()]
        if missing:
            failures.append(f'line {line} missing {missing}')
        if r.get('status') != STATUS:
            failures.append(f'line {line} has unexpected status')
        if r.get('bibliography_size_band') not in BANDS:
            failures.append(f'line {line} has unexpected bibliography band')
        for field in ('official_record','full_text'):
            if not re.fullmatch(r'https://[^\s]+',r.get(field,'')):
                failures.append(f'line {line} has malformed {field}')
        try:
            y=int(r['year'])
            if not 1900 <= y <= date.today().year:
                raise ValueError
            years.append(y)
        except ValueError:
            failures.append(f'line {line} has invalid year')
        try:
            d=date.fromisoformat(r['checked_on'])
            if d > date.today():
                failures.append(f'line {line} has future checked_on date')
            checked_dates.append(d.isoformat())
        except ValueError:
            failures.append(f'line {line} has invalid checked_on date')
        if len(r.get('main_result_boundary','')) < 45:
            failures.append(f'line {line} has an underspecified theorem boundary')
        if len(r.get('distinction_or_overlap','')) < 45:
            failures.append(f'line {line} has an underspecified project distinction')
    markdown=md_path.read_text(encoding='utf-8')
    missing_ids=[identifier for identifier in sorted(EXPECTED_IDS) if f'| {identifier} |' not in markdown]
    if missing_ids:
        failures.append(f'markdown omits identifiers: {missing_ids}')
    for phrase in ('**12** full-text structural reads','**5** full-text structural reads',
                   'not a proof of global novelty','does **not** certify worldwide originality'):
        if phrase not in markdown:
            failures.append(f'markdown omits required boundary phrase: {phrase}')
    group_rows=[]
    for group in ('same_venue','influential','adjacent'):
        subset=[r for r in rows if r['group']==group]
        group_rows.append({
            'group':group,
            'paper_count':len(subset),
            'earliest_year':min(int(r['year']) for r in subset),
            'latest_year':max(int(r['year']) for r in subset),
            'unique_venues':len({r['venue'] for r in subset}),
            'status':STATUS,
        })
    args.output_dir.mkdir(parents=True,exist_ok=True)
    summary_path=args.output_dir/'literature-calibration-summary.csv'
    with summary_path.open('w',newline='',encoding='utf-8') as f:
        fields=('group','paper_count','earliest_year','latest_year','unique_venues','status')
        writer=csv.DictWriter(f,fieldnames=fields,lineterminator='\n')
        writer.writeheader(); writer.writerows(group_rows)
        writer.writerow({'group':'total','paper_count':len(rows),'earliest_year':min(years),
                         'latest_year':max(years),'unique_venues':len({r['venue'] for r in rows}),
                         'status':'passed' if not failures else 'failed'})
    after=resource.getrusage(resource.RUSAGE_SELF)
    report={
        'scope':'internal consistency of a 12/5/5 full-paper structural calibration; not a novelty certificate or proof review',
        'source_records':len(rows),
        'group_counts':{k:counts.get(k,0) for k in ('same_venue','influential','adjacent')},
        'unique_identifiers':len(set(ids)),
        'unique_venues':len({r['venue'] for r in rows}),
        'year_range':[min(years),max(years)] if years else None,
        'checked_on_values':sorted(set(checked_dates)),
        'required_fields_per_record':len(FIELDS),
        'markdown_identifiers_present':len(EXPECTED_IDS)-len(missing_ids),
        'network_used':False,
        'scholarly_content_reverified_by_checker':False,
        'novelty_certified':False,
        'independent_review':False,
        'failures':failures,
        'status':'passed_literature_calibration' if not failures else 'failed',
        'wall_seconds':time.perf_counter()-started,
        'cpu_seconds':after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
        'peak_rss_bytes':after.ru_maxrss*1024,
    }
    report_path=args.output_dir/'literature-calibration.json'
    report_path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2,ensure_ascii=False))
    if failures:
        raise SystemExit(1)

if __name__=='__main__':
    main()
