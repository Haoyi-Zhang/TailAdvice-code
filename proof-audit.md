# Adversarial proof-interface audit

This document is an **author-side artifact-only audit** of the mathematical interfaces in *Finite Load Advice for Tail-Order and Maximum-Flow Guarantees*. It is deliberately more hostile than a prose summary: each item states a failure mode that would invalidate a claim, the repair or argument now present, the executable evidence that can expose a finite analogue, and the risk that remains outside execution. It is not independent review, a proof-assistant certificate, or permission to treat an unresolved boundary as proved.

## Audit protocol

The audit freezes the declared model before attacking the proof: deterministic causal and prefix-consistent policies; unit-speed preemptive single server; no per-job size advice; one message selecting a public policy for an environment; finite-input maximum response measured against a clairvoyant unit-speed optimum; and a stationary Poisson M/G/1 model with positive iid sizes, load in `(0,1)`, finite mean, and regularly varying tail index below `-1`. Attacks that silently change any of these quantifiers do not refute the theorem, but they must be recorded as generality boundaries.

`check_proof_obligations.py` checks exact finite consequences of the interfaces below. Its current retained output contains 16 obligation rows, 71 strict-deficit parameter cases, 71 equality-method boundary cases, 1,360 harmonic-path checks, 8,160 Jensen-path checks, 240 Pareto scaling identities, and discriminating wrong-law, wrong-denominator, and wrong-time-weighting controls. None of those counts turns a finite check into an asymptotic proof.

## P01. Offline maximum-response benchmark

**Attack.** The identity for the offline optimum could fail with simultaneous releases, deliberate idle time, or a job whose processing interval crosses several arrivals; an incorrect benchmark would contaminate every competitive ratio.

**Resolution.** Lemma `workload` proves that maximum response is at least the largest forward workload clearance time and that FCFS attains the bound. The proof is pathwise and permits arbitrary positive real sizes, arbitrary real release times, ties, and preemption. The finite oracle independently searches integer-slot schedules and deliberately includes idling.

**Executable evidence.** The oracle agrees with FCFS on 461 inputs while exploring 188,745 states. Boundary tests include empty/singleton inputs and coincident events.

**Residual risk.** The exhaustive oracle is discrete and bounded; arbitrary-real correctness still rests on the written workload/reflection argument.

## P02. Prefix consistency and horizon leakage

**Attack.** A finite-input policy could use the declared terminal horizon, future arrivals, or future sizes and therefore fail to define a queueing policy on an infinite sample path.

**Resolution.** Eligibility requires causal prefix consistency and empty-state reset. The guarded rule uses only current active jobs, their arrival order, and attained service; the simulator may know sizes solely to emit completion events, not to choose rates.

**Executable evidence.** Time translation, common rational scaling, malformed traces, and active-interval/service-conservation checks exercise the finite implementation. The emitted trace exposes each rate change.

**Residual risk.** Prefix consistency is a semantic property of the mathematical rule. The checker covers the implementation and selected transformations, not all possible programs implementing an equivalent rule.

## P03. Exact finite-input competitive factor

**Attack.** Reserving a fraction for the oldest job might prove only an upper bound, while the paper calls the factor exact; alternatively, the tight family may rely on an illegal limiting instance.

**Resolution.** Theorem `guard-competitive` bounds every job by the workload-optimal prefix clearance time divided by the reservation. Theorem `guard-tight` gives a finite family with positive sizes and releases whose root response converges to the reciprocal reservation while the offline maximum response remains one. “Exact” means the supremum over finite legal inputs, not attainment by one finite instance.

**Executable evidence.** Six rational members of the tight family are generated and checked; the largest has 97 jobs. Their values stay below the proved supremum, as required.

**Residual risk.** The convergence is a written two-limit argument. Six examples diagnose formulas but cannot prove the supremum.

## P04. Active-set inclusion in PS domination

**Attack.** The residual processor-sharing component may compare the tagged job with a slower PS queue while serving a different active set; a rate inequality using only queue lengths would then be invalid.

**Resolution.** Lemma `ps-domination` uses an attained-service coupling and the fact that completion in the guarded system can only remove competitors earlier. While a comparison job remains, the guarded residual component allocates at least its slow-PS share after matching jobs by identity; the oldest reservation adds service and is never subtracted.

**Executable evidence.** The rational trace checker recomputes attained service for every active job and verifies domination over PS at speed `1-delta` on all 1,383 guarded traces. A separate breakpoint implementation, which does not consume production segments, matches 2,856 exact completion vectors and rejects youngest-protection, extra-denominator, and omitted-reserve mutations.

**Residual risk.** The stationary infinite-horizon coupling and measurability of the identity matching remain written probability arguments.

## P05. Stationary residual law and count distribution

**Attack.** Treating the number in a PS queue as an ordinary birth-death chain ignores residual sizes; inserting a permanent customer can also introduce a missing size-bias factor.

**Resolution.** Lemma `ps-invariant` states the joint invariant measure on residual sizes, integrates the residual-coordinate balance equation, and obtains the ordinary geometric count and the `(n+1)`-biased permanent-customer count. The proof does not assume the count process alone is Markov.

**Executable evidence.** Exact arithmetic checks 256 ordinary balances, 256 permanent-customer balances, 260 geometric-convolution identities, and eight closed moments. Substituting one ordinary geometric law for the permanent system is rejected.

**Residual risk.** Identification and normalization of the full infinite-dimensional invariant measure are not mechanized. The paper therefore gives the residual-state argument rather than citing only a count formula.

## P06. Permanent-tag coupling

**Attack.** A permanent customer might reduce service to ordinary jobs and thus be unusable as an upper comparison for a finite tagged job; or the tagged job’s service could be compared after it has completed.

**Resolution.** The conditional PS proof couples the tagged job with an immortal competitor system only until the finite tag accumulates its required service. Keeping the tag present can only increase competition relative to its possible early departure, so the immortal system yields an upper bound on the completion time.

**Executable evidence.** Harmonic service-share paths are checked for 1,360 count/threshold combinations, including the tagged customer in the denominator. A deliberately wrong denominator is rejected.

**Residual risk.** Pathwise monotonicity in the continuous workload state is justified in prose and equations, not by a stochastic-order prover.

## P07. Cauchy/Jensen/Markov chain in the conditional tail bound

**Attack.** A moment inequality may reverse direction, condition on the wrong random count, or apply Jensen with an inadmissible exponent.

**Resolution.** Lemma `conditional-ps` proves the bound for every integer moment order `p>=1`; the regular-variation integration later chooses `p>alpha`. It bounds the reciprocal accumulated share and applies Cauchy--Schwarz, Jensen, and Markov at that declared convex exponent. The constants remain finite because the size-biased geometric count has all polynomial moments, not because the service law has a `p`th moment.

**Executable evidence.** 8,160 exact Jensen/moment comparisons and the first eight closed moment identities are checked.

**Residual risk.** The finite grid does not prove the inequality for every integer order or every sample path; those steps follow from the displayed pathwise inequalities and stationarity.

## P08. Regular variation, scaling, and atoms

**Attack.** Replacing `P(B>x/c)` by a constant multiple of `P(B>x)` can fail at atoms or without a genuine regularly varying tail; integrating a tail also needs finite mean and an index strictly greater than one.

**Resolution.** Lemma `rv-integrals` invokes regular variation only asymptotically and uses inequalities with fixed multiplicative slack rather than pointwise continuity. Karamata-type truncated-moment and integrated-tail relations are stated under index `alpha>1` and finite mean.

**Executable evidence.** Exact Pareto controls check 80 truncated moments, 80 integrated tails, and 240 fixed-scale ratios.

**Residual risk.** Pareto identities are a diagnostic subclass. The extension to arbitrary slowly varying factors is the written regular-variation theorem application.

## P09. Stationary common-empty coupling

**Attack.** Domination started from an empty state need not imply domination under a stationary initial distribution, especially if the coupled systems have different workloads.

**Resolution.** Both systems are constructed from a common bi-infinite input and coupled from common empty regeneration epochs. Stability of the slower PS comparison follows from `rho/(1-delta)<1`; stationary domination is obtained as the empty-start horizon recedes.

**Executable evidence.** Stability inequalities and finite coupled traces are checked, but no simulation is used as a stationary proof.

**Residual risk.** Existence of a common regenerative stationary construction is a classical queueing argument that has not been formalized here.

## P10. Growing-window uniform law of large numbers

**Attack.** A pointwise law of large numbers for bounded jobs may be insufficient when the proof chooses a window endpoint from the input and needs simultaneous control over many subwindows.

**Resolution.** Lemma `uniform-lln` applies the Poisson and marked iid strong laws, then upgrades each pointwise limit to a growing-window supremum by splitting at a finite random time `t_0`: the compact initial part is divided by the root scale, while the remainder is controlled by the limiting slope. The order of choices is fixed: strict factor gap, then `K`, then error parameters, then a sufficiently large root size.

**Executable evidence.** The deficit checker validates 71 complete rational parameter chains satisfying every strict inequality.

**Residual risk.** The probability convergence itself is analytic; the parameter checker guards algebra and quantifier order only.

## P11. Finite-prefix root deadline

**Attack.** The competitive certificate may be applied to an infinite queue trajectory, although it is defined only for finite inputs; future arrivals could also change the schedule before the root’s alleged deadline.

**Resolution.** Prefix consistency permits truncation at the finite time window used in the obstruction. The workload lemma bounds the optimum of that finite prefix, and the factor certificate forces the root to complete by the corresponding finite deadline. Later arrivals are excluded from the prefix and cannot retroactively change its rates.

**Executable evidence.** Prefix-reservation and horizon-independent trace checks cover finite analogues; the youngest-job mutation remains feasible but violates the required prefix property.

**Residual risk.** The transfer from stochastic sample path to its finite prefix is written measure-theoretic reasoning, not an executable universal check.

## P12. Truncation converts work to a job count

**Attack.** A large amount of bounded work does not by itself imply many delayed jobs if a few jobs can be near the truncation cap; the proof could lose the factor needed for `x P(B>x)`.

**Resolution.** The obstruction fixes `K`, so every counted ordinary job contributes at most `K` work. A positive residual workload deficit therefore yields at least deficit divided by `K` unfinished jobs. Arrival-window and root-size constants are chosen before taking the asymptotic limit.

**Executable evidence.** All 71 strict-deficit cases verify positive residual work and the resulting integral lower count.

**Residual risk.** The exact asymptotic event probability comes from regular variation and the uniform LLN, not from the finite arithmetic table.

## P13. Regenerative arrival ratio versus time ratio

**Attack.** Counting delayed jobs per busy cycle and dividing by cycle length would estimate a time average, not the Palm probability seen by arrivals. A missing expected-arrivals denominator changes the lower-bound constant.

**Resolution.** Lemma `cycle-reward` uses an arrival reward ratio: expected qualifying arrivals in a cycle divided by expected total arrivals in that cycle. Regenerative/Palm identification then yields the typical stationary-arrival probability; no time-integrated queue-length reward is substituted.

**Executable evidence.** Three exact regenerative examples distinguish arrival weighting from time weighting; the wrong denominator is rejected.

**Residual risk.** Integrability of cycle rewards and the Palm/regeneration theorem are conventional analytic inputs and remain unmechanized.

## P14. Strict threshold and equality nonclaim

**Attack.** Letting the strict factor gap tend to zero inside the proof may be presented as a theorem at `C=1/(1-rho)`, even though all positive deficit constants vanish.

**Resolution.** The converse is stated only for `C<theta`; the positive construction only for `C>theta`. The manuscript, figure, abstract, and conclusion all leave equality unresolved. The deficit parameter order explicitly requires a positive gap before choosing the truncation and uniform-LLN error constants.

**Executable evidence.** Seventy-one strict cases admit parameters; the same 71 equality substitutions are classified as an empty method interval, and the checker asserts that no equality extension is claimed.

**Residual risk.** Equality may be true, false, or policy-class dependent. The current method does not decide it.

## P15. Multiplicative covering endpoints and infimum

**Attack.** The product lower bound may mishandle open/closed interval endpoints, and geometric boundaries may use irrational guards that cannot be encoded by a finite message. Calling the optimum “attained” could be false.

**Resolution.** Proposition `covering` telescopes consecutive multiplicative coverage ratios. Proposition `geometric` gives the real-valued infimum. The rational theorem adds positive slack and approximates boundaries and guards with finite rationals; it claims approach to the infimum, not exact attainment in every finite encoding.

**Executable evidence.** Eight telescoping cases, eight finite-grid minimax checks, six rational-codebook coverage checks, and 93 selector decisions pass. The report explicitly records that continuous attainment is not claimed.

**Residual risk.** The checker samples finite grids for diagnosis; the universal lower bound and density of rationals are written proofs.

## P16. Speed augmentation comparator

**Attack.** Changing server speed can silently change both the stochastic load threshold and the adversarial benchmark, producing an apples-to-oranges corollary.

**Resolution.** Section 7 defines the faster online server and retains a unit-speed offline comparator explicitly. The obstruction threshold and positive guard are rescaled separately; no statement is folded into the unit-speed main theorem.

**Executable evidence.** Boundary tests include speed-augmented finite comparisons and reject invalid endpoint uses.

**Residual risk.** Other augmentation conventions or faster comparators require new statements and are not covered.

## Mutation coverage

The retained negative controls preserve enough surrounding structure to be discriminating:

- youngest-job reservation is feasible and work conserving but breaks the oldest-prefix invariant and exceeds the claimed factor on the control instance;
- a completion-time corruption preserves the policy’s nominal rates but fails service/active-interval accounting;
- an ordinary geometric count law is legitimate for ordinary PS but fails the permanent-customer balance equation;
- a missing tagged-customer denominator fails conditional-share identities;
- a time-weighted regenerative denominator fails an arrival-average identity;
- substituting equality into the strict deficit construction yields no admissible positive parameter interval rather than a fabricated pass;
- independent simulator mutations change the exact completion vector even though their surrounding event logic remains executable.

## Audit disposition

No P0 or internally repairable P1 remains in these sixteen interfaces: each has a written argument, an explicit quantifier boundary, and finite diagnostics where an exact diagnostic is meaningful. The retained external correctness hold is narrower and honest: a mathematically independent expert review or a full formalization could still find an error that author-side analysis and finite checks miss. The scientific equality boundary and excluded model extensions are nonclaims, not silently deferred proof steps.
