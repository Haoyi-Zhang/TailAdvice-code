# Full-paper structural calibration

This matrix records the completed **12 same-venue / 5 influential / 5 adjacent-venue** reading protocol used to calibrate the paper’s theorem presentation, comparison boundaries, and evidence story. It is an author-side structural reading record, not a citation-metric exercise, award claim, independent novelty opinion, or line-by-line validation of any paper’s proof. Publisher/article bytes are not redistributed. Stable records and lawful author/preprint copies are listed in the CSV.

## Scope and completion

- Same venue (`SIAM Journal on Computing`): **12** full-text structural reads.
- Influential/foundational scheduling and queueing: **5** full-text structural reads.
- Adjacent venues and recent directions: **5** full-text structural reads.
- Each read covered the problem framing, formal model, stated theorem boundary, proof spine, conclusion/limitations, references, and the role of figures/tables.
- Bibliography-size bands are descriptive (`compact <=20`, `medium 21–50`, `large >50`), not exact citation audits.
- “No direct match” below means no paper in this declared 22-paper calibration has the same full conjunction of quantifiers. It is not a proof of global novelty.

## Per-paper map

| ID | Group | Paper | Structural lesson | Boundary relative to this project |
|---|---|---|---|---|
| S01 | same_venue | Online Scheduling with General Cost Functions, | State one general objective and derive guarantees from a reusable potential/dual viewpoint rather than treating each norm separately. | Uses per-job revealed cost/size information and speed augmentation; no global environment advice or M/G/1 asymptotics. |
| S02 | same_venue | The Geometry of Scheduling, | Translate scheduling constraints into geometric covering, then use strengthened LPs and geometric rounding. | Our covering theorem is one-dimensional multiplicative load covering, not this offline geometric set cover. |
| S03 | same_venue | Flow Time Scheduling and Prefix Beck–Fiala, | Reduce scheduling to prefix discrepancy so progress transfers between fields. | Studies offline approximation across machines; our exact single-machine finite-input identity and queue tail are different quantifiers. |
| S04 | same_venue | Tight Bounds for Online Vector Scheduling, | Use potential functions and adversarial constructions to match upper and lower bounds. | Information and objective differ; useful only as a narrative/proof-architecture analogue. |
| S05 | same_venue | Fair Scheduling via Iterative Quasi-Uniform Sampling, | Iteratively round a fractional schedule while preserving local fairness/coverage properties. | Our fairness notion is absent; the overlap is only scheduling and a finite family of policies. |
| S06 | same_venue | Minimizing the Flow Time without Migration, | Combine dispatch rules with per-machine scheduling and adversarial charging. | Our policy is single-server and exact for maximum response; this paper optimizes aggregate flow without migration. |
| S07 | same_venue | Online Scheduling to Minimize Average Stretch, | Use size classes, batching, and resource augmentation to overcome clairvoyant/nonclairvoyant barriers. | Our benchmark is maximum response and our stochastic objective is a probability tail, not mean stretch. |
| S08 | same_venue | Extra Unit-Speed Machines Are Almost as Powerful as Speedy Machines for Flow Time Scheduling, | Simulate speed augmentation with extra machines through structured dispatch and coupling. | Our main result uses no extra speed; speed augmentation appears only as an explicitly labeled boundary consequence. |
| S09 | same_venue | Better Bounds for Online Scheduling, | Refine adversarial potentials and matching bad sequences around a crisp benchmark. | Only proof-writing structure overlaps; objective and information model differ. |
| S10 | same_venue | Scheduling Parallel Machines On-Line, | Design primal/rounding-inspired online rules and compare against offline load. | Our comparator is an exact single-server workload identity rather than a machine-assignment relaxation. |
| S11 | same_venue | Online Scheduling of Equal-Length Jobs: Randomization and Restarts Help, | Use randomized phases and restart rules to beat deterministic barriers. | Our retained policy class is deterministic; randomized expected factors are an explicit nonclaim. |
| S12 | same_venue | Scheduling to Minimize Total Weighted Completion Time via Time-Indexed Linear Programming Relaxations, | Exploit natural time-indexed LP relaxations and correlated rounding instead of heavier lift-and-project machinery. | Our paper intentionally retains one strict boundary rather than accumulating unrelated scheduling corollaries. |
| I01 | influential | Is Tail-Optimal Scheduling Possible? | Use distributional indistinguishability/robustness tension to prove an impossibility for weak tail competitiveness. | Our model changes the information structure and adds a separate finite-input certificate; finite advice does not “evade” this theorem without those explicit changes. |
| I02 | influential | Tail-Robust Scheduling via Limited Processor Sharing, | Cap the number of simultaneous jobs to interpolate among FCFS/PS-like tail behaviors. | Our oldest-job reservation plus residual PS is chosen to preserve an exact adversarial certificate; LPS tuning alone does not provide that certificate. |
| I03 | influential | Nonclairvoyant Scheduling to Minimize the Total Flow Time on Single and Parallel Machines, | Use multilevel feedback/round-robin style allocation and speed augmentation to offset missing size information. | Our exact same-speed maximum-response certificate comes from oldest-prefix reservation, not aggregate-flow competitiveness. |
| I04 | influential | Speed Is as Powerful as Clairvoyance, | Relate nonclairvoyant multilevel feedback policies to clairvoyant optimal schedules under augmentation. | We do not trade information for speed in the main theorem; our environment message selects a policy but gives no job size. |
| I05 | influential | Sojourn Time Asymptotics in the M/G/1 Processor Sharing Queue, | Represent conditional sojourn time and transfer regular variation through queueing transforms. | Our proof uses a permanent-customer comparison and only claims tail order; it must not silently inherit stronger constants or assumptions. |
| A01 | adjacent | Characterizing Policies with Optimal Response Time Tails under Heavy-Tailed Job Sizes, | Reduce tail optimality to structural properties of a policy’s rank function and worst future rank. | Our policy lies outside a mere distribution-optimality comparison because it must also satisfy every finite adversarial instance. |
| A02 | adjacent | Strongly Tail-Optimal Scheduling in the Light-Tailed M/G/1, | Identify policies and analytic conditions that control logarithmic asymptotics uniformly. | Our manuscript avoids “optimal” and claims only service-tail order in a regularly varying setting. |
| A03 | adjacent | SOAP: One Clean Analysis of All Age-Based Scheduling Policies, | Encode scheduling by a rank function and analyze tagged-job interference through worst future rank. | Our oldest-job guard is explained directly because importing SOAP would obscure the adversarial prefix invariant. |
| A04 | adjacent | SOAP Bubbles: Robust Scheduling under Adversarial Noise, | Transform ranks into noise-insensitive “bubbles” while retaining performance near accurate predictions. | Its advice is per job and noisy; ours is one exact environment message and no predicted sizes. |
| A05 | adjacent | Learning for Sustainable Online Scheduling with Competitive Fairness Guarantees, | Combine a learned policy with an online baseline through a provable consistency/robustness mechanism. | Related motivation only: its objective, data, and information timing differ from our stochastic-tail/adversarial maximum-flow conjunction. |

## Cross-paper pattern matrix

| Calibration set | Recurrent motivating move | Recurrent proof/evidence move | Figure/table role | Effect on the present manuscript |
|---|---|---|---|---|
| 12 SICOMP papers | Begin with a familiar scheduling objective, isolate the exact obstruction, then state one reusable mechanism. | Theorem ladders, reductions, potentials/charging, and explicit lower-bound families; empirical evidence is rarely central. | Sparse, claim-linked diagrams or parameter-summary tables; equations and lemmas remain decisive. | Keep nine coherent sections, put the strict theorem boundary before finite checks, and avoid presenting enumeration as asymptotic evidence. |
| 5 influential papers | Make the information or service-law assumption explicit before claiming robustness. | Queueing transforms/couplings for stochastic tails; adversarial charging and speed augmentation for nonclairvoyance. | Tail/rank plots explain regimes but do not replace proof. | Separate the M/G/1 tail statement from the finite-input maximum-response benchmark and expose every information change. |
| 5 adjacent papers | Clarify what “tail optimal,” “robust,” or “learning augmented” means for one objective and information channel. | Rank-policy characterizations, large-deviation/heavy-tail bounds, baseline wrappers, and application evaluation. | Policy diagrams and empirical curves matter only when the paper makes corresponding policy/application claims. | Use the modest term “tail order,” exclude per-job predictions, and retain a single analytic boundary plot rather than decorative architecture. |

## Collision and novelty conclusion

The closest stochastic papers analyze universal tail optimality, load-configured limited processor sharing, processor-sharing asymptotics, or rank-policy tail characterizations. The closest worst-case papers analyze aggregate flow, stretch, machine load, or resource augmentation. The advice/learning papers use realized-input tapes, per-job predictions, or learned baseline wrappers. Within this completed calibration, no paper states the same conjunction of: (i) one global environment message selecting from finitely many public policies; (ii) a deterministic, same-speed maximum-response certificate on every finite input; and (iii) stationary regularly-varying response tail of service-tail order in the correctly classified environment. This narrows the comparison target but does **not** certify worldwide originality or correctness.

## Reproducible validation

`check_literature_calibration.py` validates the 22 unique records, the exact 12/5/5 group counts, required nonempty fields, stable URL syntax, date/status fields, and the presence of every identifier in this narrative. It performs no network request and does not infer scholarly truth from metadata.
