# Discovery Ledger — 17 July 2026

[Türkçe sürüm](../docs_tr/DISCOVERY_LEDGER_2026-07-17.md)

## 1. Snapshot

The experiments turned a playful nonassociative algebra into four connected
but distinct structures: exact bracket-tree geometry, associahedral transport,
finite operator metaspace, and a scheduler contract. The most important
architectural discovery is that payload causality, ordered operator state, and
bracketing/projection history must remain separate.

## 2. Source algebra

For \(A=\operatorname{span}\{1,h,q\}\), all three nuclei and the centre equal
\(\mathbb R1\). The associator map \(A^{\otimes3}\to A\) is surjective with
kernel dimension 24. Derivations vanish and the unital automorphism group is
trivial. The real power-associative locus is
\(\operatorname{span}\{1,q\}\cong\mathbb R\times\mathbb R\).

Left and right operator envelopes both linearly span \(M_3(\mathbb R)\), while
their multiplicative closures remain finite. One-sided inverses are chiral:
\(hq=1\) but \(qh=-1\).

## 3. Bracket trees and tomography

All Catalan trees through seven leaves are distinct as multilinear maps:
\(1,1,2,5,14,42,132\). A fixed generator word, however, can evaluate only to
the six signed basis elements. This separates map identity from one-input
phenotype identity.

Minimum static probe counts for \(n=3,4,5,6\) are \(1,2,3,4\); at \(n=7\),
\(4\le OPT\le5\). Adaptive worst-case depths for \(n=3,\ldots,7\) are
\(1,2,3,3,4\).

## 4. Associahedron transport

Single rotations form exact associahedron graphs. Every edge admits a
one-hole context matrix and factorization

\[
\Delta_e^{root}=C_e(r_e).
\]

`DAMPED` means \(r_e\ne0\) but \(r_e\in\ker C_e\). Root differences are a
gradient, while raw local-frame associator sums can be nonzero and close only
after adding context compensation. Square mixed curvature measures interaction
between commuting reassociations, not physical gauge curvature.

## 5. Finite metaspace

The left, right, and combined multiplicative operator monoids have 99, 102,
and 192 states. The combined monoid is

\[
\mathcal M=\chi^{-1}(\{0,+1\})\subset C_2\wr T_3,
\]

containing all 168 singular transformations and 24 units with even unsigned
permutation. Its generator rank is 3; adding any excluded odd unit produces
all 216 ambient states.

Three probes read the three signed columns and recover the state exactly.
Right-action images have sizes \(192,36,6\); no reset word exists. Of 18,336
state pairs, 7,632 synchronize and 10,704 never do. The three column kernels
simultaneously describe complete observation by intersection and possible
erasure by union.

Exact rank dynamics requires five weather states. Under uniform generator
choice, expected time from identity to rank 1 is \(11/2\), variance \(59/4\),
and the three absorbing islands receive probabilities \(1/3,1/6,1/2\).

## 6. Shadow roots

No \(s\in A\) satisfies \(s^2=h\). Requiring additionally
\(L_s^2=L_h\) and \(R_s^2=R_h\) forces real dimension at least six. An explicit
six-dimensional completion realizes the bound and yields

\[
\langle L_s,R_s\rangle\cong C_2^6\rtimes C_6
\]

of order 384.

The ordinary universal adjunction imposing only \(s^2=h\) is instead an
infinite-dimensional bracket-tree algebra. Its growth series is

\[
B(z)=\frac{1-\sqrt{(1-2z)(1-10z)}}2,
\]

and the 6D clock is a surjective, non-injective quotient.

In minimal 6D strong-root extensions, \(sh=hs\) is forced but \(sq=qs\) is
not. The general canonical table space is 54-dimensional, or 27-dimensional
with the natural parity grading. The symmetric clock slice has completion
dimensions 48 and 24. Repeated-\(s\) trees read the general seam at degree
five and the symmetric completion first at degree six.

## 7. Scheduler result

The algebra does not replace effect semantics. Disjoint payload operations can
be algebraically path-sensitive but safe; conflicting operations can be
root-silent but unsafe. The guarded executor therefore uses actual read
tracking, whole-wave preflight, and rejection of ambiguous ordering keys.

With the recorded seed, 5,000 trials produced zero serial/wave mismatch and
4,860 blind stale-snapshot mismatches. The bounded corpus covered 69,905
schedules and 629,145 executions without mismatch under the declared contract.

## 8. Evidence classes

**Algebraic/theorem level:** source-algebra invariants, strong-root dimension
lower bound, universal rewrite termination/confluence, signed-metaspace
counting and action formulas, and the no-reset consequence.

**Exact finite computation:** Catalan maps through seven leaves, face ledgers
through eight, finite monoid closures and Cayley checks, tomography portfolios,
weather chains, Green classes, and scheduler corpora.

**Finite evidence only:** champion words, higher-degree phenotype statistics,
coordinate-elementary deformation scans, and behaviour beyond tested leaf
bounds.

## 9. Open threads

- all-degree injectivity of Catalan tree maps;
- whether four static probes suffice at seven leaves;
- minimal projection-seam compression;
- full isomorphism and rank-jump classification of 6D strong-root tables;
- ideals and representations of the universal strong-root quotient;
- typed effect calculus and general serializability proof;
- real hardware performance and any physical interpretation.

## 10. Restart point

The clean next architecture is an add-on memory layer for a transformer-like
system:

1. retain ordinary attention for the local window;
2. compress older ordered control into a finite operator quotient;
3. retain explicit tree/seam metadata only where projection history matters;
4. keep effect and provenance records outside the algebraic compression;
5. certify retrieval by observability probes and reject lossy merges when the
   downstream query requires erased coordinates.

This is a research direction, not yet a demonstrated infinite-context model.
The experiments establish exact finite compression and explicit information
loss boundaries—the right substrate for testing such an add-on.
