# Mathematical argument

`argument.tex` includes all nine manuscript sections, complete strict-case derivations, five tables, and the analytic boundary diagram. These sources are contained in this repository and match the current manuscript's mathematical content. Only the document preamble and figure width differ from the SIAM review layout.

Run `python build_proofs.py` from the repository root to generate `proofs/argument.pdf`. Standard article, AMS, array, booktabs, TikZ/PGFPlots, and hyperref packages are used; no SIAM assets or network access are needed. A successful compile is typesetting evidence only. The proof is not mechanized or independently peer reviewed, and broader publication novelty is not certified. The ordinary article's page count is unrelated to the SIAM target.

The proof dependencies are: workload identity -> prefix reservation and exact factor; stationary residual law -> permanent-customer conditional tail -> regular-variation integration; finite-prefix workload bound + bounded marked work + forced root completion -> busy-cycle reward lower bound. The advice lower bound uses that universal obstruction, while the upper bound uses the same guarded policy's competitive and tail guarantees. Equality at the load boundary is excluded throughout.
