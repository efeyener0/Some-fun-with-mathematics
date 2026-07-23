# Metaspace Word Normalizer

`metaspace_word_normalizer.py` gives the 192-state signed metaspace monoid an
exact word calculus.  It does two related but distinct things:

1. a 192-state deterministic transducer maps every generator word to its
   shortlex-least representative;
2. 385 oriented equations form a finite terminating and confluent string
   rewriting presentation of the same literal monoid.

The distinction matters.  A lookup table that returns canonical words does
not automatically prove that contextual rewriting is confluent.  Here the
rewriting claim has its own proof obligations and an optional exhaustive
critical-overlap certificate.

There is no floating point, randomized corpus, or approximate lane.

## Alphabet and exact semantics

The presentation alphabet is deliberately three letters:

```text
Lh < Rh < Lq
```

The order above is part of the artifact.  “Shortlex” first minimizes word
length and then uses this declared symbol order.  It does not inherit Python's
string ordering.

For signed codes

\[
x=(x_1,x_2,x_3),\qquad x_i\in\{\pm1,\pm2,\pm3\},
\]

composition is exact:

\[
(x p)_j=\operatorname{sgn}(p_j)x_{|p_j|}.
\]

The implementation imports this law from
[`certified_signed_metaspace.py`](./certified_signed_metaspace.py), but compares
all derived states and generator transitions with the authoritative integer
matrix implementation in
[`chiral_operator_monoids.py`](./chiral_operator_monoids.py).

## Canonical language

Ordered breadth-first search from the identity gives one representative for
each of the 192 states.  Its exact depth profile is:

| Length | Canonical words |
|---:|---:|
| 0 | 1 |
| 1 | 3 |
| 2 | 9 |
| 3 | 23 |
| 4 | 38 |
| 5 | 44 |
| 6 | 34 |
| 7 | 24 |
| 8 | 12 |
| 9 | 4 |

Thus the directed Cayley diameter for this ordered three-generator alphabet
is exactly nine.  The canonical language is prefix-closed: every prefix of a
canonical word is itself the canonical representative of the state reached at
that prefix.

The underlying transition-table normalizer can retain only a state id while
consuming input. At end-of-input it emits the canonical word stored for that
state:

\[
N(w)=c_{\operatorname{eval}(w)}.
\]

Consequently:

\[
\operatorname{eval}(N(w))=\operatorname{eval}(w),
\qquad
N(N(w))=N(w),
\]

and

\[
N(u)=N(v)
\iff
\operatorname{eval}(u)=\operatorname{eval}(v).
\]

That table scan is linear in word length; final output has length at most nine.
The human/JSON report wrapper deliberately retains the expanded input and a
full transition trace, so that wrapper uses linear memory rather than the
abstract transducer's constant state. It also runs contextual-rewrite parity
as a diagnostic for inputs of at most 4096 symbols; larger finite inputs still
normalize through the authoritative table lane and are not rejected merely
because the diagnostic rewrite would be expensive. This is an exact
finite-state normalizer, not a heuristic abbreviation pass.

## The 385-rule presentation

Let \(c_s\) be the canonical word for state \(s\).  For every state and every
generator \(a\), form the transition equation

\[
c_s a = c_{sa}.
\]

When the two strings differ, orient it as

\[
c_s a \longrightarrow c_{sa}.
\]

There are \(192\cdot3=576\) transition equations.  Exactly 191 are the edges
of the canonical BFS tree and need no rule because their left side is already
canonical.  The remaining

\[
576-191=\boxed{385}
\]

are the rewriting rules.

Their length profiles are:

| LHS length | Rules |
|---:|---:|
| 3 | 4 |
| 4 | 31 |
| 5 | 70 |
| 6 | 98 |
| 7 | 78 |
| 8 | 60 |
| 9 | 32 |
| 10 | 12 |

| RHS length | Rules |
|---:|---:|
| 0 | 2 |
| 1 | 9 |
| 2 | 27 |
| 3 | 65 |
| 4 | 82 |
| 5 | 90 |
| 6 | 70 |
| 7 | 24 |
| 8 | 12 |
| 9 | 4 |

The four shortest rules are:

```text
Lh Lh Lh -> epsilon
Rh Lh Lq -> Lh Lh Lq
Rh Rh Lq -> Lh Rh Lq
Lq Lq Lq -> Lq Lq
```

The deterministic JSON report contains all 385 rules with state-transition
provenance.

## Why “terminating” and “confluent” are justified

This is not merely an empirical claim.

### Soundness

Every rule is one exact monoid transition, and both sides are compared as
literal \(3\times3\) integer matrices.

### Termination

The right side is the shortlex-least word in the semantic class of the left
side.  Since the left side is not canonical, every rule strictly decreases
shortlex.  Shortlex is well-founded and is preserved by adding the same left
and right contexts.  Infinite rewrite sequences are therefore impossible.

### Irreducible words

Every noncanonical word has a shortest noncanonical prefix.  Its previous
prefix is some canonical \(c_s\), so the first bad prefix has form \(c_s a\)
and is exactly the left side of a rule.  Hence every noncanonical word is
reducible.

Conversely, a canonical word cannot contain a redex in any context: replacing
that redex would produce a strictly smaller semantically equal whole word,
contradicting shortlex minimality.

Therefore the irreducibles are exactly the 192 canonical words.

### Confluence and presentation

Rules preserve exact semantics, and every semantic class has exactly one
irreducible.  Together with termination, this gives a unique normal form and
therefore confluence.

It also proves that

\[
M\cong
\left\langle L_h,R_h,L_q
\;\middle|\;
\ell=r\text{ for the 385 generated rules}
\right\rangle.
\]

Thus “finite complete rewriting system” and “finite presentation” are literal
claims here.  No claim is made that 385 is a minimal relation basis.

With `--deep-check`, the script independently enumerates every distinct
word through the maximum rule-left-side length and every distinct nontrivial
overlap or inclusion critical peak:

```text
88,573 words of length 0 through 10 normalized identically by both lanes
56,725 critical peaks
all joined
maximum deterministic branch-to-normal-form steps: 8
critical-peak SHA-256:
5e525e1e74ded91a1e082b916a86d5c98783c5e4fb4b426e0c472bb259e6af13
```

This is a second finite certificate of local confluence; the mathematical
unique-normal-form proof does not depend on running the optional deep pass.

## The Lq/Rq relation

`Rq` is not a presentation generator, but the CLI accepts it as an exact
boundary macro.  Put

\[
S=L_hR_hL_h=(1,-2,3).
\]

Exact signed-code multiplication gives:

\[
S^2=1,
\qquad
R_q=L_qS,
\qquad
L_q=R_qS,
\qquad
SR_qS=L_q,
\qquad
SL_q=L_q.
\]

In the chosen `Lh < Rh < Lq` canonical language, `Rq` has the shorter
representative:

```text
Rq = Lq Lh Lq
```

Both triples generate all 192 states and both have diameter nine, but their
shortlex depth distributions differ:

```text
Lh,Rh,Lq : 1,3,9,23,38,44,34,24,12,4
Lh,Rh,Rq : 1,3,9,21,36,42,36,28,12,4
```

So `Lq`/`Rq` are algebraically substitutable, but substitution is not an
isometry of the two ordered Cayley metrics.  This is a genuine chiral scar in
the canonical-word geometry rather than a closure defect.

## Validation boundary

Default execution checks:

- equality with the exact 192-state matrix closure;
- all 576 generator transitions;
- exact BFS depth equality;
- all 29,524 words through diameter nine in shortlex order;
- soundness and strict orientation of all 385 rules;
- irreducibility and prefix closure of all 192 canonical representatives;
- all 576 canonical boundary transitions;
- a 4098-symbol table-lane regression which bypasses the bounded contextual
  diagnostic and still normalizes exactly;
- both three-generator closures and the stated `Lq`/`Rq` identities;
- pinned model, transition, canonical-language, rewrite, and bundle hashes.

Deep execution additionally checks:

- the source signed oracle's full pair-composition certificate;
- contextual rewriting versus table normalization for all 88,573 words of
  length at most ten;
- all 56,725 distinct nontrivial critical peaks;
- deterministic transition-table and rewrite-rule corruption rejection.

The artifact is scoped only to the literal three matrices and their exact
192-state closure.  Unknown symbols are rejected.  `Rq` is expanded through
its matrix-certified canonical macro.  No Knuth–Bendix minimality,
production-performance, or physical claim is made.

## Run

```powershell
python .\experiments\metaspace_word_normalizer.py
python .\experiments\metaspace_word_normalizer.py --word "Lh Rh Lq Lq Rh"
python .\experiments\metaspace_word_normalizer.py --json
python .\experiments\metaspace_word_normalizer.py --deep-check --json
```
