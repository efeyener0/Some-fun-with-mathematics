# Metaspace Observability

The 192-state combined chiral operator monoid can be read as a deterministic
Moore automaton:

\[
\mathcal A=(\mathcal C,\{L_h,L_q,R_h,R_q\},\delta,o),
\qquad
\delta(M,x)=M\,x.
\]

The transition is **right multiplication**.  A continuation word is appended
to the current operator history.  The companion
[`metaspace_observability.py`](./metaspace_observability.py) independently
reaches all 192 states from \(I\) with this convention and checks that its
minimal generation depths equal those from
[`chiral_operator_monoids.py`](./chiral_operator_monoids.py).

## Four observation alphabets

The experiment minimizes the same transition system under four Moore outputs:

1. `root_signed_basis`: \(o(M)=M1\), represented by
   \(\{\pm1,\pm h,\pm q\}\).
2. `root_plus_rank`: \((M1,\operatorname{rank}M)\).
3. `root_plus_rank_plus_det`:
   \((M1,\operatorname{rank}M,\det M)\).
4. `full_matrix_control`: the entire matrix, used as a reference ceiling.

Exact partition refinement gives:

| Observation | Horizon-0 classes | Refinement profile | Minimal quotient | Max shortest suffix depth |
|---|---:|---|---:|---:|
| Root signed basis | 6 | \(6\to192\) | 192 | 1 |
| Root + rank | 18 | \(18\to192\) | 192 | 1 |
| Root + rank + determinant | 24 | \(24\to192\) | 192 | 1 |
| Full matrix control | 192 | \(192\) | 192 | 0 |

Thus rank and determinant enrich the immediate reading, but do not reduce the
future horizon needed for complete state observability.  Every quotient is
ultimately discrete: no two distinct monoid matrices remain Moore-equivalent.

## Why one step is enough

Every current root value is a signed basis vector, and each of the six values
occurs in exactly 32 states.  Root observation alone therefore compresses
192 states to six immediate phenotypes.

However, right multiplication turns the generators into column probes:

\[
\begin{aligned}
o(M)&=M e_1=\operatorname{col}_1(M),\\
o(ML_h)=o(MR_h)&=M e_2=\operatorname{col}_2(M),\\
o(ML_q)=o(MR_q)&=M e_3=\operatorname{col}_3(M).
\end{aligned}
\]

Therefore

\[
\boxed{\bigl(o(M),o(ML_h),o(ML_q)\bigr)}
\]

is literally the three-column reconstruction of \(M\).  The executable checks
this equality for all 192 states.  Only `Lh` and `Lq` are needed as active
one-step probes; `Rh` and `Rq` duplicate them at the root-output level, though
they remain different full state transitions.

This explains the abrupt refinement profile.  It is not a numerical accident
or a lucky search result: the root channel becomes full matrix tomography after
two chosen one-letter experiments.

## Shortest distinguishing suffixes

There are

\[
\binom{192}{2}=18{,}336
\]

unordered state pairs.  Exact pair refinement assigns each distinguishable
pair its lexicographically first shortest continuation under alphabet order

\[
L_h<L_q<R_h<R_q.
\]

| Observation | Depth 0 (`epsilon`) | Depth 1 | Canonical depth-1 suffixes |
|---|---:|---:|---|
| Root signed basis | 15,360 | 2,976 | `Lh`: 2,544; `Lq`: 432 |
| Root + rank | 16,608 | 1,728 | `Lh`: 1,488; `Lq`: 240 |
| Root + rank + determinant | 16,632 | 1,704 | `Lh`: 1,476; `Lq`: 228 |
| Full matrix control | 18,336 | 0 | none |

No pair requires depth two.  No pair remains indistinguishable.  Pairs already
separated by the current output use the empty suffix; among equal-output pairs,
`Lh` is chosen whenever the second columns differ, otherwise `Lq` exposes the
third-column difference.

The JSON report includes a concrete matrix pair for every shortest suffix type,
with before/after observations.

## Refinement semantics

Horizon \(k\) equates two states precisely when every continuation word of
length at most \(k\) produces the same Moore output.  The refinement recurrence
is exact:

\[
P_{k+1}(s)=
\left(P_k(s),P_k(\delta(s,L_h)),P_k(\delta(s,L_q)),
P_k(\delta(s,R_h)),P_k(\delta(s,R_q))\right).
\]

The root-family partitions reach singleton blocks at horizon one and are
checked stable at horizon two.  Full-matrix control starts singleton and is
checked stable at horizon one.

With `--deep-check`, the program independently:

- enumerates all observation traces through the stability horizon;
- rechecks every shortest witness against every strictly shorter word;
- checks witness absence exactly against final-block equivalence;
- verifies imported BFS depths and the complete transition table digest.

## Epistemic boundary

These are exact Myhill–Nerode/Moore results for the literal 192 integer matrices,
the stated right-action alphabet, and the four exact outputs above.

They do **not** establish physical observability under noise, measurement cost,
hidden calibration, or partial access.  In particular, “observe \(M1\) exactly”
is a mathematical interface assumption.  Full-matrix control is deliberately
tautological and serves only as the upper reference.

The one-step result also depends on keeping the four generators as available
continuations.  It should not be silently generalized to a different action
side, a perturbed representation, or an alphabet lacking independent second-
and third-column probes.

Run:

```powershell
python .\experiments\metaspace_observability.py
python .\experiments\metaspace_observability.py --json
python .\experiments\metaspace_observability.py --deep-check --json
```
