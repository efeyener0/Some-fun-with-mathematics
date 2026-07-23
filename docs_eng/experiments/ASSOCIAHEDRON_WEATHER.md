# Associahedron Weather

`associahedron_weather.py` places Bracket Garden's explicit Catalan trees into
the geometry of single rotations. Each vertex is a bracket history, and each
edge is exactly the local move

\[
((A B)C)\longleftrightarrow A(B C).
\]

The tool imports `bracket_garden.py` from the same directory. Both experiments
share `Leaf(index)`, `Branch(left,right)`, tree IDs, and the exact \(1,h,q\)
product. There are no external dependencies.

## Associahedron 1-skeleton

For \(n\) ordered leaves,

\[
V_n=C_{n-1}.
\]

For \(n\ge3\), every full binary tree has \(n-2\) internal rotation sites, so
the number of undirected edges is

\[
E_n=\frac{C_{n-1}(n-2)}{2}.
\]

The code generates only the orientation `((AB)C) -> (A(BC))` so that an edge
has a canonical delta sign. Adjacency remains undirected; the reverse rotation
is not counted as a second edge.

```powershell
python .\experiments\associahedron_weather.py topology --max-leaves 8
```

Exact ledger:

| Leaves | Vertices | Edges | Degree |
|---:|---:|---:|---:|
| 1 | 1 | 0 | 0 |
| 2 | 1 | 0 | 0 |
| 3 | 2 | 1 | 1 |
| 4 | 5 | 5 | 2 |
| 5 | 14 | 21 | 3 |
| 6 | 42 | 84 | 4 |
| 7 | 132 | 330 | 5 |
| 8 | 429 | 1,287 | 6 |

The generator checks these counts, regular degree, and graph connectivity
through eight leaves.

## Two residuals on an edge

Suppose the canonical source contains the rotation site `((A*B)*C)`. Its local
associator is

\[
\Delta_{\mathrm{local}}=((ab)c)-a(bc).
\]

After replacing that site inside the entire tree, the root phenotype delta is

\[
\Delta_{\mathrm{root}}
=\operatorname{eval}(T_{\mathrm{source}})
-\operatorname{eval}(T_{\mathrm{target}}).
\]

These are not the same object. They agree when the rotation is at the root.
Deeper in a context, the local residual passes through the linear context map
induced by the outer products. A nonzero local associator may vanish at the
root.

Weather classes:

- **ACTIVE:** `root_delta != 0`; adjacent vertices have different phenotypes.
- **DAMPED:** `local_associator != 0` but `root_delta == 0`; the context kills
  the local residual.
- **CALM:** the local associator is already zero, so the rotation is
  phenotype-silent.

The implementation asserts that a zero local associator can never change the
root.

## Forecasting one word

```powershell
python .\experiments\associahedron_weather.py forecast hhqqhq
python .\experiments\associahedron_weather.py forecast hhqqhq --edges damped --limit 0
```

A forecast includes:

- explicit `Tn:index` vertex IDs for every phenotype;
- exact vertex expressions and lossless shape codes;
- counts of active, damped, and calm edges;
- local associator and root delta for every `En:index` rotation;
- connected components of the subgraph induced by each phenotype.

`--edges` accepts `all`, `active`, `silent`, `damped`, or `calm`. `--limit 0`
prints every matching edge and vertex label.

To inspect one edge:

```powershell
python .\experiments\associahedron_weather.py rotation hhqqhq --edge 17
```

The report shows canonical source and target IDs, rotation path, both fully
parenthesized expressions, \([a,b,c]\), local associator, and root delta.

## Phenotype islands

For a phenotype \(p\), retain only vertices with phenotype \(p\) and the
rotation edges between them. The tool computes the connected components of
this induced subgraph exactly.

Two trees in the same component can be joined by phenotype-silent rotations.
Trees in different components have the same element-level result but cannot
reach one another on the associahedron without changing phenotype.

This is not multilinear-map equality. It is an observation about one selected
leaf word and its rotation graph.

## Deterministic expedition

```powershell
python .\experiments\associahedron_weather.py expedition --max-leaves 7
```

Running without a subcommand starts the same expedition. For every \(n\le7\),
all \(2^n\) positive `h/q` words are scanned exhaustively under three explicit
objectives:

1. **Storm champion:** maximize active-edge count.
2. **Damping champion:** maximize edges whose nonzero local associator vanishes
   at the root.
3. **Fracture champion:** maximize excess phenotype-component count beyond one
   component per phenotype.

Ties are resolved by secondary metrics and then lexical order `h < q`.
Nothing is randomized, and “interesting” is not presented as one universal
mathematical quantity.

Two named fronts are also reported:

- Bracket Garden's six-mask witness `hhqqhq`;
- the pure word `h^7 = hhhhhhh`.

## Tests

```powershell
python .\experiments\associahedron_weather.py test
python .\experiments\associahedron_weather.py test --deep
```

The default test validates topology, connectivity, regularity, the edge-state
partition, and the exact metrics of both named fronts. `--deep` rescans all
`h/q` words and reconstructs champions through \(n=7\).

## Epistemic boundary

- The Catalan vertex/edge formulas and rotation connectivity are known
  combinatorics; the script exactly reconstructs their \(n\le8\) instances.
- A word forecast is an exact calculation on its finite graph.
- Expedition results are exhaustive observations through \(n=7\), not
  all-degree theorems.
- `DAMPED` means that an algebraic context kills a residual. It is not a claim
  about physical energy dissipation or time dynamics.
- A phenotype component does not replace tree identity or multilinear-map
  identity.

To keep generation interactive and recoverable, weather is bounded at nine
leaves, topology validation at eight, and exhaustive word search at seven.
Exceeding a bound raises an explicit error rather than quotienting or sampling
trees.
