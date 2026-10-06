#!/usr/bin/env python3
"""Reproduce finite evidence in an isolated local copy, without network access.

Python checks use only the standard library on a POSIX system. Each child is
limited to 45 wall seconds, with one active command. The optional proof-PDF
step invokes installed TeX tools, not a theorem prover or publisher template.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
RUNTIME_KEYS = {'wall_seconds','cpu_seconds','peak_rss_bytes'}


def semantic_report(data: dict) -> dict:
    return {k:v for k,v in data.items() if k not in RUNTIME_KEYS}


def main() -> None:
    if not __debug__:
        raise SystemExit('Verification cannot run under python -O or -OO.')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-proof-pdf', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT/'results'/'reproduction.json')
    args = parser.parse_args()
    wall = time.perf_counter()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    records, compared = [], []
    summary = {'scope':'clean reproduction of finite evidence; not an asymptotic proof or originality review',
               'commands':records, 'compared_evidence':compared, 'workers':1,
               'network_used':False, 'random_seed':None, 'status':'running'}
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONOPTIMIZE='0',
               OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
    try:
        with tempfile.TemporaryDirectory(prefix='tail-reproduce-') as tmp:
            work = Path(tmp)
            for name in ('src','tests','proofs'):
                shutil.copytree(ROOT/name,work/name,
                                ignore=shutil.ignore_patterns('__pycache__','*.pyc','*.pdf'))
            for name in ('run_checks.py','check_analytics.py','check_examples.py','check_proof_obligations.py','check_literature_calibration.py','check_bibliography.py','check_reference_simulator.py','build_proofs.py'):
                shutil.copy2(ROOT/name,work/name)
            for name in ('literature-calibration.csv','literature-calibration.md','bibliography-verification.csv'):
                shutil.copy2(ROOT/name,work/name)
            (work/'observed').mkdir()
            commands = [
                ['run_checks.py','--pilot','--output','observed/pilot.json'],
                ['run_checks.py','--output','observed/checks.json'],
                ['check_analytics.py','--output-dir','observed'],
                ['check_examples.py','--output-dir','observed'],
                ['check_proof_obligations.py','--output-dir','observed'],
                ['check_literature_calibration.py','--output-dir','observed'],
                ['check_bibliography.py','--output-dir','observed'],
                ['check_reference_simulator.py','--output-dir','observed'],
                ['-m','unittest','discover','-s','tests','-v'],
            ]
            if args.with_proof_pdf:
                commands.append(['build_proofs.py','--output','observed/argument.pdf',
                                 '--report','observed/proof-build.json'])
            for command in commands:
                t = time.perf_counter()
                cpu = resource.getrusage(resource.RUSAGE_CHILDREN)
                process = subprocess.Popen([sys.executable,*command],cwd=work,env=env,
                    stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
                try:
                    stdout,stderr = process.communicate(timeout=45)
                    timed_out = False
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid,signal.SIGKILL)
                    stdout,stderr = process.communicate()
                    timed_out = True
                now = resource.getrusage(resource.RUSAGE_CHILDREN)
                record = {'command':['python',*command],
                    'executable_resolution':'the interpreter executing this runner',
                    'working_directory':'isolated copy of repository sources',
                    'exit_code':process.returncode,'timed_out':timed_out,
                    'wall_seconds':time.perf_counter()-t,
                    'cpu_seconds':now.ru_utime+now.ru_stime-cpu.ru_utime-cpu.ru_stime,
                    'stdout':stdout,'stderr':stderr}
                records.append(record)
                if timed_out or process.returncode:
                    raise RuntimeError('A reproduction command failed or timed out.')
                if command[:2] == ['-m','unittest']:
                    match = re.search(r'Ran (\d+) tests?', stderr)
                    if not match or int(match.group(1)) != 14:
                        raise RuntimeError('Boundary suite did not execute the expected fourteen tests.')
                    summary['boundary_test_count'] = int(match.group(1))
            for name in ('pilot.json','checks.json','analytics.json','examples.json','proof-obligations.json','literature-calibration.json','bibliography.json','reference-simulator.json'):
                expected = json.loads((ROOT/'results'/name).read_text())
                observed = json.loads((work/'observed'/name).read_text())
                if semantic_report(expected) != semantic_report(observed):
                    raise RuntimeError(f'Scientific fields disagree for {name}.')
                compared.append({'file':'results/'+name,'comparison':'all non-runtime fields equal'})
            for name in ('checks-cases.csv','advice.csv','codebook.csv','fluid_constants.csv','tightness.csv','proof-obligations.csv','deficit-parameters.csv','literature-calibration-summary.csv','bibliography-summary.csv','reference-simulator-summary.csv'):
                if (ROOT/'results'/name).read_bytes() != (work/'observed'/name).read_bytes():
                    raise RuntimeError(f'Deterministic exact records disagree for {name}.')
                compared.append({'file':'results/'+name,'comparison':'exact file bytes equal; no checksum used'})
            if args.with_proof_pdf:
                proof = json.loads((work/'observed'/'proof-build.json').read_text())
                if proof['status'] != 'compiled' or proof['layout_messages']:
                    raise RuntimeError('Standalone proof document has unresolved compilation messages.')
                summary['proof_document'] = {k:proof[k] for k in
                    ('scope','publisher_template_required','pages','layout_messages','status')}
            summary['status'] = 'passed_finite_reproduction'
    except Exception as exc:
        summary['status'] = 'failed'
        summary['error'] = str(exc)
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    summary.update(wall_seconds=time.perf_counter()-wall,
        child_cpu_seconds=after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
        peak_child_rss_bytes=after.ru_maxrss*1024)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k != 'commands'},indent=2))
    if summary['status'] == 'failed':
        raise SystemExit(1)

if __name__ == '__main__':
    main()
