#!/usr/bin/env python3
"""Compile the standalone mathematical argument; compilation is not proof checking."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import resource
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'proofs'/'argument.pdf')
    parser.add_argument('--report', type=Path, default=ROOT/'results'/'proof-build.json')
    args = parser.parse_args()
    latex = shutil.which('pdflatex')
    bibtex = next((shutil.which(x) for x in ('bibtex','bibtex.original','bibtex8')
                   if shutil.which(x)), None)
    if not latex or not bibtex:
        raise SystemExit('The proof PDF requires pdflatex and BibTeX; the source is readable without them.')
    started = time.perf_counter()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    records = []
    with tempfile.TemporaryDirectory(prefix='tail-proof-') as temp:
        work = Path(temp)
        for name in ('argument.tex', 'references.bib'):
            shutil.copy2(ROOT/'proofs'/name, work/name)
        for name in ('sections', 'figures'):
            shutil.copytree(ROOT/'proofs'/name, work/name)
        tex = [latex, '-no-shell-escape', '-interaction=nonstopmode',
               '-halt-on-error', '-file-line-error', 'argument.tex']
        env = os.environ.copy()
        env.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')
        for command in (tex, [bibtex, 'argument'], tex, tex, tex):
            t = time.perf_counter()
            result = subprocess.run(command, cwd=work, env=env, capture_output=True,
                                    text=True, timeout=45)
            records.append({'command': [Path(command[0]).name, *command[1:]],
                            'exit_code': result.returncode,
                            'wall_seconds': time.perf_counter()-t})
            if result.returncode:
                args.report.parent.mkdir(parents=True, exist_ok=True)
                args.report.write_text(json.dumps({'status':'failed','commands':records,
                    'stdout':result.stdout[-16000:],'stderr':result.stderr[-16000:]},indent=2)+'\n')
                raise SystemExit('Proof document compilation failed; inspect the requested report.')
        log = (work/'argument.log').read_text(errors='replace')
        issues = [line for line in log.splitlines()
                  if 'Overfull' in line or 'undefined' in line or 'multiply defined' in line or 'Label(s) may have changed' in line or 'Rerun to get cross-references' in line]
        pages = re.search(r'Output written on argument\.pdf \((\d+) pages?', log)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(work/'argument.pdf', args.output)
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    report = {'scope':'document compilation, not machine checking of mathematical proofs',
              'publisher_template_required':False, 'commands':records,
              'pages':int(pages.group(1)) if pages else None, 'layout_messages':issues,
              'wall_seconds':time.perf_counter()-started,
              'child_cpu_seconds':after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
              'peak_child_rss_bytes':after.ru_maxrss*1024,
              'status':'compiled' if not issues else 'compiled_with_messages'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if issues:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
