# Metaspace Synchronizer

`metaspace_synchronizer.py` reads the 192-element combined monoid as a
four-letter deterministic automaton and exhaustively derives the state-
compression geometry of right-multiplication words. It uses no approximation,
randomness, external package, or floating point.

## Convention: right action, left ideal

Words append generators in order:

\[
p(g_1\ldots g_k)=(((Ig_1)g_2)\cdots)g_k,\qquad \delta(x,g)=xg.
\]

Thus

\[
\operatorname{Im}(R_p)=\{xp:x\in M\}=Mp
\]

is a principal **left** ideal and measures Green-\(\mathcal L\). Principal
right ideals and Green-\(\mathcal R\) are computed separately as \(pM\).

```powershell
python .\experiments\metaspace_synchronizer.py
python .\experiments\metaspace_synchronizer.py --deep-check --json
```

Deep mode checks all \(192^3=7{,}077{,}888\) associativity triples, replays
shortest words, and verifies closure of every distinct principal ideal.

## Exact image spectrum

The 192 induced right transformations are distinct because \(R_p(I)=p\).
Their only image sizes are

\[
\boxed{192,\ 36,\ 6}.
\]

| First depth | Word | Matrix rank | Image |
|---:|---|---:|---:|
| 0 | `epsilon` | 3 | 192 |
| 1 | `L_q` | 2 | 36 |
| 2 | `L_q L_q` | 1 | 6 |

| Rank | Products | \(|Mp|\) | \(|pM|\) |
|---:|---:|---:|---:|
| 3 | 24 | 192 | 192 |
| 2 | 144 | 36 | 64 |
| 1 | 24 | 6 | 8 |

Minimum image size is 6, so there is no reset word. Fibre profiles are
\(192\times1\), \(12\times4+24\times6\), and \(6\times32\) respectively.

## Pair synchronizability

Of \(\binom{192}{2}=18{,}336\) unordered pairs, 7,632 synchronize and 10,704
never merge.

| Shortest depth | Pairs |
|---:|---:|
| 1 | 432 |
| 2 | 2,976 |
| 3 | 2,112 |
| 4 | 2,112 |

The exact criterion is

\[
\boxed{x,y\text{ synchronize}\iff
x\text{ and }y\text{ agree in at least one basis column}.}
\]

| Equal columns | Pairs | Depth | Witness |
|---|---:|---:|---|
| `{1,q}` | 432 | 1 | `L_q` |
| `{1,h}` | 432 | 2 | `L_h L_q` |
| `{h,q}` | 432 | 2 | `L_q L_q` |
| `{q}` | 2,112 | 2 | `L_q L_q` |
| `{1}` | 2,112 | 3 | `L_h L_q L_q` |
| `{h}` | 2,112 | 4 | `L_h L_h L_q L_q` |

## Green geometry

The \(Mp\) family contains 11 principal left ideals: one of size 192, six of
size 36, and four of size 6. Green-\(\mathcal L\) has seven classes of size 24
and four of size 6. Its cover incidence matches tetrahedral vertex-edge
incidence as a computable analogy.

The \(pM\) family contains seven principal right ideals: one of size 192, three
of size 64, and three of size 8. Green-\(\mathcal R\) has a 24-state unit
class, three 48-state rank-2 classes, and three eight-state rank-1 classes.
Its cover incidence matches triangle vertex-edge incidence.

Principal two-sided ideals form

\[
24<168<192.
\]

The three Green-\(\mathcal J=\mathcal D\) classes are matrix ranks 1, 2, and 3.
There are 31 Green-\(\mathcal H\) classes: one of size 24, 18 of size 8, and
12 of size 2. Twenty-five contain an idempotent; six do not.

## Epistemic boundary

All products, transformations, unordered pairs, ideals, and Green profiles
were derived exactly from the finite Cayley table. The equal-column criterion
is both exhaustive and structurally explained by accessible rank-1 coordinate
lines. Rank/image relations and triangle/tetrahedron incidences are not
claimed as general matrix-semigroup theorems or physical ontology. The result
concerns only the four literal integer generators and their 192-state closure.
