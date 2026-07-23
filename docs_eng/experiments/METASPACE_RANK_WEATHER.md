# Metaspace Rank Weather

This experiment tracks exactly how matrix rank changes while random generators
are appended on the right in the combined monoid.

```powershell
$py = 'C:\Users\Efe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py -B .\experiments\metaspace_rank_weather.py
& $py -B .\experiments\metaspace_rank_weather.py --horizon 16 --json
& $py -B .\experiments\metaspace_rank_weather.py --deep-check
```

At each step `Lh`, `Lq`, `Rh`, and `Rq` are selected independently with
probability \(1/4\). No claim is made for another distribution.

## Three ranks are not enough

Rank never increases under products. Rank-3 units stay at rank 3 or fall to
rank 2; rank-2 states stay at rank 2 or fall to rank 1; the rank-1 ideal is
absorbing. Yet rank alone is not Markovian: 96 of the 144 rank-2 states cannot
drop on the next step, while 48 can drop directly through either `q`
generator.

Exact Moore minimization with rank as output refines as

\[
3\longrightarrow4\longrightarrow5\longrightarrow5.
\]

The minimal weather machine therefore has five states.

## Exact five-state weather machine

Let \(H=\{L_h,R_h\}\) and \(Q=\{L_q,R_q\}\).

| Weather state | Elements | under \(H\) | under \(Q\) |
|---|---:|---|---|
| `rank3_unit_weather` | 24 | itself | `rank2_drop_gate` |
| `rank2_funnel` | 48 | `rank2_drop_gate` | `rank2_drop_gate` |
| `rank2_drop_gate` | 48 | `rank2_return` | `rank1_absorbing` |
| `rank2_return` | 48 | `rank2_funnel` | `rank2_drop_gate` |
| `rank1_absorbing` | 24 | itself | itself |

This is a deterministic Moore quotient preserving generator names, not merely
a uniform Markov lumping. The hidden rank-2 phase is a funnel, a gate where
`q` lowers rank, and a return loop.

## Time to reach rank 1

With \(P(H)=P(Q)=1/2\), exact rational linear systems give:

| Initial weather | \(\mathbb E[T]\) | \(\operatorname{Var}(T)\) |
|---|---:|---:|
| rank 1 | \(0\) | \(0\) |
| funnel | \(9/2\) | \(51/4\) |
| gate | \(7/2\) | \(51/4\) |
| return | \(5\) | \(13\) |
| identity's unit weather | \(11/2\) | \(59/4\) |

| \(n\) | \(P(T=n)\) | \(P(T\le n)\) |
|---:|---:|---:|
| 1 | \(0\) | \(0\) |
| 2 | \(1/4\) | \(1/4\) |
| 3 | \(1/8\) | \(3/8\) |
| 4 | \(1/8\) | \(1/2\) |
| 5 | \(1/8\) | \(5/8\) |
| 6 | \(5/64\) | \(45/64\) |
| 12 | \(37/2048\) | \(241/256\) |

`--horizon` only controls the printed finite table. Means and variances come
from the exact absorbing-chain solution, not truncation.

## Three absorbing islands with unequal rainfall

The rank-1 ideal contains three closed eight-state SCCs, labelled by range
axis:

\[
\mathcal I_1,\qquad\mathcal I_h,\qquad\mathcal I_q.
\]

Although equal in size, their eventual entry probabilities from identity are

\[
\boxed{P(\mathcal I_1)=\frac13,\qquad
P(\mathcal I_h)=\frac16,\qquad
P(\mathcal I_q)=\frac12}.
\]

These values come from an exact 21-block strong lumping and rational linear
system.

## Green geometry is transverse to weather phase

| Rank | SCC count | SCC size |
|---:|---:|---:|
| 3 | 1 | 24 |
| 2 | 3 | 48 |
| 1 | 3 | 8 |

The rank-2 weather phases are not the three Green-\(\mathcal R\) classes.
Instead they intersect in a complete \(3\times3\) grid:

| Green-\(\mathcal R\) image class | funnel | gate | return |
|---|---:|---:|---:|
| image \(\{1,h\}\) | 16 | 16 | 16 |
| image \(\{1,q\}\) | 16 | 16 | 16 |
| image \(\{h,q\}\) | 16 | 16 | 16 |

Green-\(\mathcal R\) asks which signed coordinate lines survive; weather asks
which phase of the rank-drop cycle the state occupies.

## Verification and boundary

The script recomputes Moore minimization, verifies symbol stability in every
block, solves exact first and second moments, builds the axis-labelled
21-block lumping, checks total probability \(1\), extracts all SCCs, and tests
the \(3\times3\times16\) transversality grid. Deep mode cross-checks the
Synchronizer's Green-\(\mathcal R\) and minimum-image results.

The result is exact only for the literal four generators, uniform \(1/4\)
choice, and finite 192-state automaton. It does not assert thermodynamic
equilibrium, physical entropy production, real-world randomness, non-uniform
policies, or stability under algebraic perturbation.
