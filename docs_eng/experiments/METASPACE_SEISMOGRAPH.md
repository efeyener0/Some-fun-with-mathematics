# Metaspace Projection-Seam Seismograph

This experiment sharpens the relation between operator metaspace and bracket
trees:

> Delayed projection preserves ordered operator composition, but ordinary
> matrix multiplication is associative and therefore cannot preserve the
> internal bracketing of a fixed word. Bracketing history must also record
> **where** projection occurs.

The architecture separates the operator word, projection schedule (binary
tree), local seam defects, and the effect graph that independently certifies
payload safety.

```powershell
<python> .\experiments\metaspace_seismograph.py
<python> .\experiments\metaspace_seismograph.py --word QQQ --max-length 7 --json
```

Only the standard library and exact integer arithmetic are used.

## The mathematical seam

\[
D(x,y)=L_xL_y-L_{xy},\qquad
D(x,y)z=x(yz)-(xy)z=-[x,y,z].
\]

At every internal tree node the ledger stores `(leaf interval, split point,
local projection defect)`. Defects alone may collide. Adding interval and
split preserves topology explicitly; injectivity comes from the metadata
contract, not an algebraic miracle.

## Observed landscape

| Experiment | Result |
|---|---:|
| Full binary trees of `HHHHQ` | 14 |
| Distinct root elements | 4 |
| Distinct raw defect ledgers | 8 |
| Tree-annotated ledgers | 14 |
| Trees per seven-leaf word | 132 |
| Maximum distinct roots at seven leaves | 6 |
| Maximum raw ledgers at seven leaves | 95 (`QHQQHHH`) |

The six-root ceiling is exact: the signed basis set
\(\{\pm1,\pm h,\pm q\}\) is closed under multiplication, so every bracketed
`H/Q` tree lands in one of these six elements. In exhaustive lengths three
through seven, \(Q^n\) was the only word whose bracketings all shared one root;
this is finite evidence, not an all-\(n\) proof.

`QQQ` is instructive: both trees have root \(q\) and identical raw defect
ledgers, yet seam energy is 4. Only explicit projection positions separate
them.

## Direction of delayed projection

\[
L_{x_1}L_{x_2}\cdots L_{x_n}(1)=x_1(x_2(\cdots x_n)),
\]

so final-only projection yields the right comb. Delaying projection preserves
operator action lost by early projection, but not alternative bracketings of
the same ordered word. The tree or an equivalent seam program must remain
authoritative.

### The operator word is not complete history either

Exact BFS finds only 99 matrices in
\(\langle I,L_h,L_q\rangle_{\mathrm{multiplicative}}\). All entries lie in
\(\{-1,0,1\}\); maximal minimal depth is 13, witnessed by
`HHQHHQHHQHQHH`. New states by depth are
`1,2,4,6,9,11,13,12,12,10,9,6,3,1,0`.

| Operator rank | States |
|---:|---:|
| 3 | 3 |
| 2 | 72 |
| 1 | 24 |
| 0 | 0 |

Only three states are invertible, 19 are idempotent, and none are nilpotent.
Element-level \(q^2=q\) does not imply \(L_q^2=L_q\):

\[
L_q^2\ne L_q,\qquad (L_q^2)^2=L_q^2,\qquad L_q^3=L_q^2.
\]

The ambient signed-basis action space has at most
\((2\cdot3)^3=216\) matrices. The 99-state multiplicative quotient can still
linearly span the nine-dimensional envelope \(M_3(\mathbb R)\); there is no
contradiction. It is richer than the six root states but does not injectively
store unbounded word history.

## Separation from effect semantics

A safe but algebraically path-sensitive example uses three handlers on
disjoint registers: all permutations give the same payload and the effect
graph has no conflicts, while `HHH` has two different bracket roots.

An unsafe but root-silent example uses `set`, `mul`, and `add` on one register:
six permutations produce five payloads and every event pair conflicts, while
every `QQQ` bracketing has root \(q\).

Thus a nonzero associator need not signal a payload hazard, and a zero
associator does not certify safe reordering.

| Concept | Primary role | Authoritative? |
|---|---|---:|
| Payload state | Observable result | Yes |
| Effect conflict graph | Safety/serializability certificate | Yes, within its model |
| Root algebra element | Lossy path summary | No |
| Operator word | Ordered composition | No |
| Projection defect | Local associator operator | No |
| Annotated seam ledger | Tree-indexed audit record | For the tree, given the word |

## Epistemic record

Finite counts, basis checks of \(D(x,y)z=-[x,y,z]\), right-comb equality, and
the two effect examples were executed. The seam ledger is a strong executable
contract for separating order history from projection history. Its minimality,
post-seven-leaf landscape, scheduler utility, compression ratio, GPU
performance, and physical interpretation remain unverified.
