#!/usr/bin/env python3
"""Bounded exact instances illustrating a separately proved limiting family."""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path
import resource
import sys
import time
from fractions import Fraction as Q
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/"src"))
from model import fcfs, long_job_stream, max_flow, simulate
from checker import validate_trace


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir",type=Path,default=ROOT/"results")
    args=p.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True)
    wall,cpu=time.perf_counter(),time.process_time()
    cases=((Q(1,4),8),(Q(1,4),16),(Q(1,2),4),(Q(1,2),8),(Q(1,2),16),(Q(1,2),32))
    rows=[];max_bits=0
    for delta,n in cases:
        js=long_job_stream(delta,n,1/delta+1)
        actual=simulate(js,delta)
        validate_trace(js,actual)
        opt=max_flow(js,fcfs(js))
        assert opt==1
        assert max_flow(js,actual)<=1/delta
        for t in actual.completion:
            max_bits=max(max_bits,t.numerator.bit_length(),t.denominator.bit_length())
        rows.append(dict(guard=str(delta),subdivisions=n,jobs=len(js),
                         optimal_max_flow=str(opt),root_response=str(actual.completion[0]),
                         root_response_approx=float(actual.completion[0]),
                         maximum_flow=str(max_flow(js,actual)),proved_supremum=str(1/delta)))
    with (args.output_dir/"tightness.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    report=dict(scope="six finite instances; the supremum is proved analytically, not inferred from this table",
                cases=len(rows),largest_job_count=max(r['jobs'] for r in rows),
                max_completion_fraction_bits=max_bits,workers=1,random_seed=None,
                wall_seconds=time.perf_counter()-wall,cpu_seconds=time.process_time()-cpu,
                peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,status="passed")
    (args.output_dir/"examples.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))

if __name__=='__main__': main()
