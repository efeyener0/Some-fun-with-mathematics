# Algebra Ecology

This note explores the real three-dimensional algebra

\[
h^2=q,\qquad q^2=q,\qquad hq=1,\qquad qh=-1
\]

beyond the supplied whitepaper.  The executable certificate is
[`algebra_ecology.py`](./algebra_ecology.py); it is deterministic, standard-library
only, and uses exact `Fraction` row reduction rather than floating-point rank tests.

## 1. The shape of the associator

Write the pure-plane coordinates of \(x,y,z\) as
\(u=(b,c),v=(e,f),w=(m,n)\).  Scalars never enter the associator, and direct
expansion gives

\[
\begin{aligned}
[x,y,z]_1 &=-\langle u,v\rangle m-\langle v,w\rangle b,\\
[x,y,z]_h &=\det(u,v)m-\det(v,w)b,\\
[x,y,z]_q &=(\det(u,v)+\langle u,v\rangle)n
            -(\det(v,w)+\langle v,w\rangle)c.
\end{aligned}
\]

The exact tensor map \(\Omega:A^{\otimes3}\to A\) has rank 3 and kernel
dimension 24.  Nineteen kernel dimensions are automatic: every basis tensor
containing a \(1\) is killed.  The restriction
\(\Omega:\langle h,q\rangle^{\otimes3}\to A\) still has rank 3, leaving a
five-dimensional genuinely pure kernel.  A checked basis of relations is:

\[
\begin{aligned}
\Omega(q,q,q)&=0,\\
\Omega(h,h,q)+\Omega(h,q,h)+\Omega(q,h,h)&=0,\\
\Omega(h,q,q)-\Omega(q,q,h)&=0,\\
\Omega(h,q,q)+\Omega(q,h,q)+\Omega(q,q,h)-\Omega(h,h,h)&=0,\\
2\Omega(h,h,q)+\Omega(h,q,h)+\Omega(q,h,q)&=0.
\end{aligned}
\]

The image is nevertheless all of \(A\).  Thus the associator is globally
surjective while possessing a large, structured history-blind subspace.

Exact slotwise nullspaces give

\[
N_\ell=N_m=N_r=\mathbb R1,
\qquad Z(A)=\mathbb R1.
\]

No non-scalar direction can be moved freely through even one associator slot.

## 2. The associative oasis

For \(x=a+bh+cq\),

\[
x^2=a^2+2ab\,h+(2ac+b^2+c^2)q
\]

and a stronger identity appears:

\[
[x,x,x]=-2b(b^2+c^2)\,1.
\]

Over \(\mathbb R\), third-power agreement therefore forces \(b=0\).  Conversely,

\[
C:=\operatorname{span}\{1,q\}
\]

is associative.  Hence the **power-associative elements are exactly \(C\)**.
With \(p=1-q\),

\[
p^2=p,\quad q^2=q,\quad pq=qp=0,
\]

so \(C\cong\mathbb R\times\mathbb R\) via
\(a+cq\mapsto(a,a+c)\).  This one plane simultaneously contains:

- all four idempotents \(0,1,q,1-q\);
- every real two-sided unit;
- the fixed locus of the anti-involution \(h\mapsto-h\).

The complete two-sided unit law is

\[
a+cq\text{ is invertible}\iff a(a+c)\ne0,
\qquad
(a+cq)^{-1}=\frac1a-\frac{c}{a(a+c)}q.
\]

For completeness, if \(y=d+eh+fq\) and \(xy=yx=1\), subtracting the two
products gives \(bf=ce\); their scalar and \(h\)-coordinates give \(ad=1\)
and \(ae+bd=0\).  When \(b\ne0\), substitution into the \(q\)-coordinate
forces \(b^2+c^2=0\), impossible over \(\mathbb R\).  When \(b=0\), it yields
exactly the inverse above.  Thus this classification does not assume that a
one-sided multiplication matrix is invertible.

There are no nonzero square-zero real elements.  This statement is deliberately
not inflated into an unqualified notion of “nilpotent”: outside \(C\), powers
require a chosen tree.

## 3. Chiral singular surfaces

For \(x=a+bh+cq\), exact determinants of multiplication are

\[
\det L_x=a^2(a+c)+b(b^2+c^2),
\qquad
\det R_x=a^2(a+c)-b(b^2+c^2).
\]

Thus the anti-involution exchanges the two cubic zero-divisor surfaces.  Their
real intersection is only

\[
\mathbb Rq\ \cup\ \mathbb R(1-q).
\]

Inside the associative oasis these are the familiar two axes of
\(\mathbb R\times\mathbb R\); outside it, singularity is handed.  A mirrored
pair of explicit witnesses is

\[
(1-h)(1+h+q)=0,
\qquad
(1-h+q)(1+h)=0.
\]

Even nonsingular left/right multiplication does not supply one common inverse:

\[
hq=1,\qquad(-q)h=1.
\]

So \(q\) is the right inverse of \(h\), while \(-q\) is its left inverse.

## 4. Rigidity and the zero-divisor surprise

Exact Leibniz constraints on a general \(3\times3\) linear map give

\[
\operatorname{Der}(A)=0.
\]

A unital automorphism fixes \(1\) and must send \(q\) to one of the two
nontrivial idempotents \(q,1-q\).  If \(q\mapsto q\), the relations
\(xq=1,qx=-1,x^2=q\) force \(x=h\).  If \(q\mapsto1-q\), already

\[
x(1-q)=(a-b)+bh-aq=1
\]

is inconsistent.  Therefore

\[
\operatorname{Aut}(A)=\{\mathrm{id}\}.
\]

Since the known anti-involution exists, triviality of the automorphism group
also makes it the unique anti-automorphism.

The exact associative envelopes generated separately by \(L_h,L_q\) and by
\(R_h,R_q\) both have dimension 9, hence equal \(M_3(\mathbb R)\).  Any left
ideal would be invariant under the first full matrix algebra, and any right
ideal under the second.  Consequently the algebra has no nonzero proper left
or right ideals.

This creates the sharpest ecological oddity here: **the algebra is one-sided
simple and still has abundant zero divisors**.  In an associative algebra an
annihilator is stabilized by reassociation; here the associator breaks exactly
that inference.

## 5. Repeated-\(h\) forest

The whitepaper distinguishes multilinear maps of different Catalan trees.  A
different experiment labels every leaf by the same \(h\) and asks what remains
observable after evaluation.

Every tree lands in the six-state set

\[
\{\pm1,\pm h,\pm q\}.
\]

At seven leaves all six values occur (the exact multiplicities are
\(2,2,44,44,20,20\), ordered as \(1,-1,h,-h,q,-q\)).  They occur at every
larger degree as well: left-extending a tree by \(h\) permutes the same six
states.  Thus a Catalan forest can retain distinct multilinear behavior while
collapsing to a finite six-state orbit on one generator.

The two extreme combs expose the chirality:

\[
\begin{aligned}
(((hh)h)\cdots h)&: h,q,-1,-h,-q,1 &&\text{(period 6)},\\
h(\cdots h(hh))&: h,q,1              &&\text{(period 3)}.
\end{aligned}
\]

The executable counts every full binary tree, checks each total against the
appropriate Catalan number, stores a first witness for every state, and proves
the post-degree-7 saturation by the six-state permutation.

## Validation boundary

**Exact computational certificates:** associator ranks/nullities and five pure
relations; all three nuclei; commutant/center; zero-dimensional derivation
space; both 9-dimensional operator envelopes; anti-involution identities;
Catalan distributions and comb periods.

**Algebraic consequences proved from those certificates and direct expansion
of the displayed real equations:** determinant formulae; classification of
power-associative elements, idempotents, two-sided units, and the common
singular locus; trivial automorphism group; unique anti-automorphism; and
absence of proper one-sided ideals.

**Finite supplementary check only:** the script also scans the integer cube
\([-2,2]^3\) for determinant and inverse consistency.  The classifications do
not rely on that finite scan; their proofs are the equations above.

**Not claimed:** novelty in the classification literature; any corresponding
classification over \(\mathbb C\) (positivity is used); injectivity of all
multilinear tree maps in arbitrary degree; or a physical interpretation of the
kernel.

Run:

```powershell
python .\experiments\algebra_ecology.py
python .\experiments\algebra_ecology.py --json --max-h-leaves 12
```
