# Bracket Tomography

## Question

For the `n`-leaf Catalan family, how few probe words from
`{1,h,q}^n` distinguish every ordered full binary tree?

The source of truth is `bracket_garden.py`'s exact multilinear signature.  A
probe portfolio is only a projection of that full signature; it never replaces
it.

## Pair claims

Let the Catalan trees be `T_0,...,T_(C-1)`.  Every unordered pair

```text
P_(i,j) := "T_i and T_j must receive different portfolio responses"
```

is a claim.  Its failure mode under probe `w` is exact phenotype equality:

```text
F_w(i,j) := evaluate(T_i,w) == evaluate(T_j,w)
```

Represent `F_w` as a bit mask over all `C choose 2` pairs.  A portfolio `W`
separates the garden exactly when

```text
intersection(F_w for w in W) == empty.
```

Thus tomography is a finite set-cover problem.  Words with identical failure
masks are behavior-equivalent; the implementation retains the
lexicographically first representative.  A probe with a strict superset of
another probe's failure mask is dominated and may be removed from exact search.

## Three logically different bounds

1. **Information lower bound.** Exact basis-word evaluations remain in the six
   signed basis values `±1, ±h, ±q`.  If the best one-probe outcome count is
   `m <= 6`, `k` probes encode at most `m^k` response tuples.  Therefore
   `k >= ceil(log_m(Catalan(n-1)))`.  This is a lower bound, not a construction.

2. **Greedy plus reverse-delete upper bound.** Repeatedly choose the probe that
   hits the largest number of currently unresolved pair claims; break ties by
   the word order `1 < h < q`.  Then attempt deletions in reverse selection
   order.  The resulting portfolio is validated against full signatures.  It
   is an upper bound only.

3. **Exact certificate.** Branch on a still-unresolved pair claim.  Every
   completion must choose one of its covering probes.  Equal next residuals are
   merged; residual supersets are dominated.  Memoization and the six-way code
   capacity bound prune branches.  Only a completed exhaustive decision search,
   or a matching information bound and witness, licenses `optimal=true`.
   A timeout is explicitly incomplete and never a proof.

Residual pair graphs are disjoint unions of cliques: two trees are adjacent
exactly when their response tuples are still equal.  With `r` probes left, a
class of size greater than `m^r` cannot be split into singletons.  This is the
dynamic capacity bound used by the exact solver.

## Computed spectrum

The following values were recomputed from the exact oracle in this workspace.

| leaves `n` | trees | pair claims | words | unique failure masks | information LB | greedy+RD | exact result |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | 2 | 1 | 27 | 2 | 1 | 1 | **1** |
| 4 | 5 | 10 | 81 | 12 | 2 | 2 | **2** |
| 5 | 14 | 91 | 243 | 70 | 2 | 3 | **3** |
| 6 | 42 | 861 | 729 | 320 | 3 | 5 | **4** |
| 7 | 132 | 8,646 | 2,187 | 1,240 | 3 | 6 | **`4 <= OPT <= 5`** |

Exact witnesses include:

```text
n=3: hhh
n=4: hhhh  h1hh
n=5: hhqqh  h1hhh  hhh1h
n=6: h1qqhh  hqqh1h  1hhhh1  hhq1qh
n=7: 1hhqq1h  hhh1hhq  1h1hhhh  hhqh1hh  hh1hqhh
```

The `n=7` five-probe row is a validated witness, not an optimality claim.  The
exact search exhausts the three-probe space, raising the certified lower bound
to four.  The four-probe infeasibility search was not completed, so the interval
must remain open.

The gap at `n=6` is the useful surprise: deterministic greedy needs five probes,
while exact search finds and certifies four.  This is precisely why construction
and optimality live in separate layers.

## Adaptive tomography

Static portfolios use the same probes on every tree.  An adaptive decision tree
may choose its next probe from the observed phenotype.  The exact minimax state
is simply the subset of Catalan trees still compatible with the path:

```text
D(S) = 0                                             when |S| <= 1
D(S) = 1 + min_w max_outcome D(S intersect block(w,outcome))
```

The implementation memoizes subset states, merges identical restricted
partitions, applies the same outcome-capacity bound, and exhausts every remaining
probe partition before declaring a depth impossible.  Full signatures again
validate the rendered decision tree.

| leaves `n` | static optimum/bounds | exact adaptive worst-case depth | effect |
|---:|---:|---:|---|
| 3 | 1 | **1** | equal |
| 4 | 2 | **2** | equal |
| 5 | 3 | **3** | equal |
| 6 | 4 | **3** | strictly one probe shallower |
| 7 | `4 <= OPT <= 5` | **4** | matches the static lower bound; strict gain remains undecidable until static `OPT` is known |

So adaptivity is genuinely useful at six leaves, but not uniformly useful.  At
five leaves, the information lower bound of two is unattainable even with
branch-specific second probes.  At seven leaves, the adaptive depth is exactly
four; this does not yet prove a strict advantage over the unresolved static
four-versus-five question.

## Commands

Default regression tests certify `n <= 6`:

```powershell
python experiments/bracket_tomography.py self-test
```

The deep profile additionally rebuilds all 132 seven-leaf signatures, validates
the five-probe witness, and exhausts the three-probe decision problem:

```powershell
python experiments/bracket_tomography.py self-test --deep
```

Survey the spectrum.  Exact optimization is enabled through six leaves by
default; `--deep` adds the `n=7,k=3` lower-bound certificate:

```powershell
python experiments/bracket_tomography.py atlas
python experiments/bracket_tomography.py atlas --deep --json
```

Audit one garden and optionally emit all pair claims:

```powershell
python experiments/bracket_tomography.py audit --leaves 6 --json
python experiments/bracket_tomography.py audit --leaves 5 --emit-claims --json
```

For `n=7`, `--exact` attempts the still-open four-probe decision.  A time limit
may be supplied; expiration leaves `complete=false`:

```powershell
python experiments/bracket_tomography.py audit --leaves 7 --exact --time-limit 120 --json
```

JSON reports include SHA-256 digests of the full signature table, pair-claim
matrix, and adaptive witness tree; every exact decision status and node count;
the greedy trace; the validated static portfolio; and the complete adaptive
decision tree.

## Runtime note

`bracket_garden.py` uses Python 3.10 type syntax.  The workspace's available
Android NDK Python is 3.9, so tomography contains a narrow compatibility loader
that removes only dataclass slots and the runtime type alias.  The algebra,
multiplication, tree generation, evaluation, and full-signature functions are
executed from the oracle source unchanged.  Reports identify whether the native
import or this type-only shim was used.
