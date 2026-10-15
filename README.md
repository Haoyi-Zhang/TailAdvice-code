# Distribution-robust tail scheduling

Standalone mathematical argument and exact finite evidence for *Finite Load Advice for Tail-Order and Maximum-Flow Guarantees*, by Haoyi Zhang and Huaijin Ran. No sibling paper directory or unpublished input is required.

The model is a unit-speed M/G/1 queue with independent positive iid sizes, load in (0,1), and a regularly varying service tail with index below -1. The finite-input objective is maximum response time against a clairvoyant unit-speed optimum. One environment-level message selects a fixed deterministic causal, prefix-consistent policy; it supplies neither a future trace nor per-job sizes.

The written argument separates a strict integrated-tail obstruction below `1/(1-rho)` from a guarded-sharing construction above it, together with finite load-advice bounds. Equality, optimal leading constants, broader arrival models, randomized expected guarantees, and deployment performance are not established. The complete assumptions, proofs, and bibliography are in `proofs/sections/` and `proofs/argument.tex`. This ordinary-article rendering is not the SIAM manuscript or a proof-assistant development.

## Environment

Use Python 3.10+ with the standard library. The combined reproducer and scientific CLI components use POSIX process/resource interfaces; run them on Linux/POSIX, not native Windows. CI uses Python 3.12 on Ubuntu 24.04. Library unit/root tests, source regressions, and the bibliography/source-calibration checkers can run on Windows; unavailable peak RSS is reported as null.

No scientific command requires network access, a solver, private data, GPU, model API, or dependency installation. TeX and plotting packages are optional and separate from the finite checks.

## Tests

From this directory, or the root of either flat public repository:

```sh
python -B -m unittest discover -s tests -v
python -B regressions/test_integer_roots.py -v
python -B regressions/test_bibliography_identity.py -v
python -B regressions/test_literature_reading_scope.py -v
python -B -O regressions/test_literature_reading_scope.py -v
```

The main suite has **14** methods: eleven scheduling/boundary tests and three rational-root regressions. The separate suites have five integer-root, five bibliography-identity/date, and five reading-scope methods. The optimized command applies only to the reading-scope regression: the finite reproducer refuses `-O`/`-OO` because its scientific checks use assertions.

Root regressions retain 1,200 exact grid cases and the separate 504 grid-power neighbors, message lengths 0–8, and input/bracketing/grid refusal boundaries. These finite arithmetic checks do not replace the stationary queueing proof or claim a measured construction-time gain.

## Isolated reproduction

On POSIX, use a fresh output-report path:

```sh
python -B reproduce.py --output results/local-reproduction.json
```

The runner copies required sources to a temporary directory, runs one child at a time with a 45-second wall timeout, and kills its process group on timeout. Its nine commands cover pilot/full enumeration, algebra/codebooks, examples, proof-interface diagnostics, source-calibration/bibliography consistency, separate simulator replay, and the 14-method main suite.

Success requires `status = passed_finite_reproduction`, all eight non-runtime JSON reports equal, all ten CSV files byte-equal, and exactly fourteen main test methods. A failure is nonzero and its raw command output is retained in the requested reproduction report. The default report path overwrites `results/reproduction.json`; use the explicit scratch path above to preserve historical records.

CI runs this workflow without TeX, followed by the separate regressions. It enforces a 240-second whole reproduction timeout, inherited 180-second per-process CPU limit and 1-GiB virtual-memory limit, and uploads raw outputs even on failure. Historical reports predate the current fourteen-method suite; their timing/RSS data remain historical, not current-host measurements.

Direct components overwrite their output files. Run them in a disposable copy with scratch destinations, for example:

```sh
python -B run_checks.py --pilot --output scratch/pilot.json
python -B run_checks.py --output scratch/checks.json
python -B check_analytics.py --output-dir scratch
python -B check_examples.py --output-dir scratch
python -B check_proof_obligations.py --output-dir scratch
python -B check_literature_calibration.py --output-dir scratch
python -B check_bibliography.py --output-dir scratch
python -B check_reference_simulator.py --output-dir scratch
```

## Inputs, results, and consumers

Finite instances are generated locally; no external scientific dataset is consumed.

- `src/model.py`: exact `Fraction` releases, sizes, rates, events and completions. Sizes determine completion events, while rate selection uses arrival order and the active set.
- `src/checker.py`: independently recomputed trace capacity, conservation, completion, active intervals, prefix reservation, and service domination.
- `src/advice.py`: exact rational advice/codebook and moment helpers.
- `run_checks.py`: 83-instance pilot and 461-instance integer multiset family, not arbitrary real inputs or every tie permutation. Three guards give 1,383 comparisons; the separate integer-slot oracle permits idle time.
- `check_reference_simulator.py`: separate breakpoint reconstruction, 2,856 exact completion-vector comparisons and three mutated-rule controls; it does not consume production segments.
- `results/checks-cases.csv`: generated inputs, oracle/comparison results and guarded completions. Other retained JSON/CSV files hold algebra, advice, tightness, proof-obligation, and source-consistency results.
- `proof-audit.md`: sixteen technical interface maps, finite diagnostics, and their analytic limits; the proof arguments remain in `proofs/sections/`.
- `claim_evidence_ledger.csv`: claim-to-proof/check/result links.
- `literature-calibration.csv`, `literature-calibration.md`: 12/5/5 source groups, version and reading-depth records, including the claim-scoped CWI report.
- `bibliography-verification.csv`, `proofs/references.bib`: 72 cited entries, persistent locators and metadata-verification scope.
- `external_resources.csv`: external-source identities, rights/access, and integration notes.

The source checkers validate recorded identities, reading scopes, dates, and citation closure offline; they do not reread scholarly full texts. The proof-interface checks and negative controls remain finite diagnostics, not asymptotic proofs or independent human review. The youngest-reservation control is feasible but violates the claimed factor and is rejected by the reservation checker; corrupted completions and wrong analytic controls are retained.

## Optional proof build and vector figure

With installed `pdflatex`, BibTeX, AMS, booktabs, TikZ/PGFPlots and hyperref:

```sh
python -B build_proofs.py --output scratch/argument.pdf --report scratch/proof-build.json
```

Alternatively, `reproduce.py --with-proof-pdf --output results/local-proof-reproduction.json` adds a temporary standalone build. Compilation checks typesetting, not mathematical correctness; it does not build or alter the SIAM manuscript.

For optional figure rendering, use a disposable standalone artifact copy with these declared versions:

```sh
python -m pip install "matplotlib==3.10.7" "fonttools==4.66.1"
python -B scripts/plot_figures.py
```

The script overwrites `figures/load-boundary.csv` and `.pdf`, copies the PDF to existing proof and sibling-paper figure directories, and preserves the existing Computer Modern glyph/Unicode mapping. Do not run it in a frozen manuscript checkout merely to execute finite checks.

## Interpretation and rights

Exact records cover bounded deterministic inputs; there are no stationary-tail simulations, fitted exponents, random samples, or representative deployment measurements. Interpreter/TeX versions are not pinned. Timings, PDF metadata, pagination and display-only floating approximations may vary; the reproducer flags CSV differences instead of silently accepting them.

The written proof is not mechanized or independently peer reviewed. The license covers original code and finite generated records; cited articles and publisher templates are not redistributed. Authorship and external dissemination responsibilities remain with the named authors.
