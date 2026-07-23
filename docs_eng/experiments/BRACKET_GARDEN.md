# Bracket Garden

`bracket_garden.py` treats the non-associative algebra on \(1,h,q\) not as a
mere result calculator, but as an **exploration toy that preserves genealogy**.

The core multiplication is

\[
h^2=q,\qquad q^2=q,\qquad hq=1,\qquad qh=-1.
\]

General coordinate multiplication is implemented with exact integer
arithmetic:

\[
(a+bh+cq)(d+eh+fq)
=(ad+bf-ce)+(ae+bd)h+(af+be+cd+cf)q.
\]

There are no external dependencies; Python 3.10+ is sufficient.

## Three identity layers kept separate

The tool deliberately separates three objects that are dangerous to conflate:

1. **Tree identity:** the Catalan tree itself, preserved by a stable ID such as
   `T6:00` and a lossless `shape` code containing leaf positions.
2. **Phenotype:** the algebra element produced by that tree on one chosen leaf
   word. Distinct trees may collide here.
3. **Multilinear-map identity:** the complete \(n\)-linear map induced by the
   tree, compared by an exact signature over every tensor-basis input in
   \((1,h,q)^n\).

Two trees with the same phenotype are therefore never merged. This is a
**phenotype collision**. When one leaf word produces several phenotypes, it is
a **split**. With `--audit-maps`, the tool also supplies a *camouflage witness*:
another basis word on which apparently colliding trees separate.

This preserves the whitepaper's central invariant: an element-level result
does not replace contraction-tree metadata.

## Usage

### Plant a word

```powershell
python .\experiments\bracket_garden.py plant hhhh
```

This generates all \(C_3=5\) full binary trees, evaluates them, and groups them
by phenotype. Every row contains the tree ID, lossless shape code, and fully
parenthesized expression.

To inspect exact multilinear-map separation as well:

```powershell
python .\experiments\bracket_garden.py plant hhhh --audit-maps
```

Display is limited to eight trees per phenotype by default; no computed tree
is discarded. Use `--limit 0` to print them all.

The word parser accepts `1`, `h`, `q`, and signed forms:

```powershell
python .\experiments\bracket_garden.py plant '-h, q, +1'
```

The input contains no parentheses: growing every parenthesization is the
garden's job.

### Trace one contraction tree

```powershell
python .\experiments\bracket_garden.py trace hhqq --tree 3
```

Tree indices are zero-based and match the `Tn:index` identifiers printed by
`plant`. The post-order trace shows every actual multiplication and performs
no implicit reassociation.

### Deterministic six-mask expedition

```powershell
python .\experiments\bracket_garden.py expedition --max-leaves 8
```

Running without a subcommand starts the same expedition.

For every \(n\), the expedition exhaustively scans all \(2^n\) `h/q` words and
all Catalan trees. It first maximizes phenotype count, then minimizes the
largest collision bucket, with ties broken by the lexical order `h < q`.
There is no randomness.

Because the basis table is closed, every tree whose leaves are only `h` and
`q` lands in one of six masks:

\[
\{1,-1,h,-h,q,-q\}.
\]

The number of trees nevertheless grows at Catalan rate. The expedition places
the saturation of the six-color phenotype space next to the continued growth
of tree-history space. Six possible outputs do **not** imply six trees; the
information loss between those spaces is precisely what the tool exposes.

### Audit complete multilinear maps

```powershell
python .\experiments\bracket_garden.py maps 7
```

For each tree, `maps` evaluates all \(3^n\) basis tuples exactly. Because tree
composition of a bilinear product is multilinear, this is a finite map-equality
test rather than randomized testing. The interactive limit is seven leaves,
matching the source whitepaper's validation boundary.

General `plant` and `trace` generation stops at eleven leaves to avoid an
accidental Catalan explosion. This is not an algebraic quotient: every tree
inside the bound is preserved, and exceeding the bound raises an explicit
error rather than silently sampling.

### Built-in tests

```powershell
python .\experiments\bracket_garden.py test
python .\experiments\bracket_garden.py test --deep
```

`--deep` compares the multilinear signatures of all Catalan trees from one
through seven leaves.

## Mathematical and epistemic boundary

- A phenotype collision is not equality of tree maps.
- Separation through seven leaves is an exact finite validation, not a proof
  for all degrees.
- The six-mask bound applies only to words whose leaves are signed basis
  elements. General \(a+bh+cq\) inputs are not restricted to six outputs.
- The tool does not turn non-associativity into an ordinary fold. Every product
  comes from an explicit `Branch(left, right)` node.
- Source files were read only to recover the algebra and verified boundary.
  This experiment is an independent, standard-library-only implementation.

## File boundary

The experiment consists only of:

- `experiments/bracket_garden.py`
- `experiments/BRACKET_GARDEN.md`

It performs no persistent storage, network access, global installation, or
mutation outside the workspace.
