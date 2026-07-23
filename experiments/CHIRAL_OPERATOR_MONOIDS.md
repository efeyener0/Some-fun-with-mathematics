# Chiral Operator Monoids

This is an exact finite-state study of the four multiplication matrices

\[
L_h,L_q,R_h,R_q\in M_3(\mathbb Z)
\]

from the \((1,h,q)\) algebra.  The companion executable
[`chiral_operator_monoids.py`](./chiral_operator_monoids.py) is standalone and
standard-library only.  It uses integer matrix products, breadth-first minimal
word depths, and `Fraction` row reduction for linear-span ranks.

## Exact closures

All three default enumerations close far below the hard limits of 100,000
states and depth 64.

| Monoid | States | Maximum minimal depth | Rank 1 | Rank 2 | Rank 3 | Idempotents | Units |
|---|---:|---:|---:|---:|---:|---:|---:|
| \(\mathcal L=\langle L_h,L_q\rangle\) | 99 | 13 | 24 | 72 | 3 | 19 | 3 |
| \(\mathcal R=\langle R_h,R_q\rangle\) | 102 | 11 | 24 | 72 | 6 | 19 | 6 |
| \(\mathcal C=\langle L_h,L_q,R_h,R_q\rangle\) | 192 | 9 | 24 | 144 | 24 | 25 | 24 |

The nonempty BFS layers, beginning at the identity in depth zero, are:

\[
\begin{aligned}
\mathcal L &: 1,2,4,6,9,11,13,12,12,10,9,6,3,1,\\
\mathcal R &: 1,2,4,7,12,15,17,15,14,9,5,1,\\
\mathcal C &: 1,4,14,32,44,37,24,20,12,4.
\end{aligned}
\]

Every entry of every state remains in \(\{0,\pm1\}\), and none of the three
monoids contains the zero matrix.  After BFS closure, the executable checks
all \(99^2\), \(102^2\), and \(192^2\) pairwise products independently.

The idempotent rank profiles are

\[
\mathcal L,\mathcal R:(12,6,1),
\qquad
\mathcal C:(12,12,1)
\]

for ranks \((1,2,3)\).  The determinant profiles are

\[
\begin{array}{c|ccc}
 & -1 & 0 & +1\\ \hline
\mathcal L&0&96&3\\
\mathcal R&3&96&3\\
\mathcal C&12&168&12.
\end{array}
\]

Every observed unimodular matrix has its exact integer inverse inside the same
closed monoid, so these are genuine unit counts rather than determinant-only
proxies.  Their order distributions are

\[
\begin{aligned}
\mathcal L &: \{1:1,\ 3:2\},\\
\mathcal R &: \{1:1,\ 2:1,\ 3:2,\ 6:2\},\\
\mathcal C &: \{1:1,\ 2:7,\ 3:8,\ 6:8\}.
\end{aligned}
\]

## Why right has 102 states

Let

\[
S=\operatorname{diag}(1,-1,1).
\]

Exact multiplication gives

\[
S R_h S=-L_h,
\qquad
S R_q S=L_q.
\]

Therefore \(\mathcal R\) is conjugate to

\[
\langle-L_h,L_q\rangle=\mathcal L\cup(-\mathcal L).
\]

The 96 singular states of \(\mathcal L\) are already all paired under global
sign.  The only newly supplied states are the negative units

\[
-I,-L_h,-L_h^2,
\]

so the count grows from 99 to 102.  This also explains why the singular rank
and idempotent profiles of the left and right monoids agree while the right
unit group doubles from \(C_3\) to \(C_6\).

## Combined unit geometry

The combined units are exactly

\[
G=\langle L_h,R_h\rangle.
\]

There are 24.  The executable verifies the unique normal-form set

\[
G=
\left\{
\operatorname{diag}(\epsilon_1,\epsilon_2,\epsilon_3)L_h^k:
\epsilon_i\in\{\pm1\},\ k\in\{0,1,2\}
\right\}.
\]

The eight diagonal signs form \(C_2^3\); conjugation by \(L_h\) cyclically
permutes their coordinates.  Hence

\[
G\cong C_2^3\rtimes C_3\cong C_2\times A_4.
\]

The mirror itself is already a unit word,

\[
S=L_hR_hL_h,
\]

and

\[
R_q=L_qS.
\]

Thus the second singular generator becomes redundant once the full unit group
is present.  Exact set multiplication gives

\[
\boxed{\mathcal C=\mathcal L G=\mathcal R G.}
\]

The left and right monoids intersect in 49 states; their union contains 152.
The combined monoid therefore contains 40 genuinely mixed states outside that
union.

For the singular part, the stronger coverage identity also holds:

\[
\mathcal C_{\mathrm{sing}}=\mathcal L_{\mathrm{sing}}G.
\]

It has 168 states and is closed under global sign.

There are exactly \((2\cdot3)^3=216\) matrices that send each of the three
basis vectors to one signed basis vector.  Of these, 168 are singular and 48
are signed permutations.  Exact ambient-set construction verifies:

\[
\boxed{\mathcal C_{\mathrm{sing}}
=\{\text{all singular signed-basis actions}\}.}
\]

The combined monoid contains 24 of the 48 invertible signed permutations; the
other 24 are precisely the invertible ambient states excluded by its cyclic
rather than full symmetric permutation subgroup.

## Finite monoid, full linear envelope

Each of \(\mathcal L,\mathcal R,\mathcal C\) has exact rational linear-span rank
9.  Consequently each spans all of \(M_3(\mathbb R)\), even though each
multiplicative monoid is finite.

There is no contradiction.  Monoid closure permits multiplication only; a
linear envelope additionally permits arbitrary sums and real scalar
multiples.  Ninety-nine discrete matrices can therefore span a continuous
nine-dimensional matrix space without containing that space multiplicatively.

## Epistemic boundary

The closed profiles above are exact for the four literal matrices embedded in
the executable.  They are backed by:

- complete generator BFS;
- a second, full pairwise-closure pass;
- exact determinant/minor ranks and integer inverses;
- exact `Fraction` span ranks;
- fixed state-set SHA-256 fingerprints;
- asserted profiles and cross-set equalities.

The CLI accepts smaller bounds for controlled experiments.  If one is hit,
the script reports a lower bound, marks the status as bounded, and withholds
cross-closure classification.  Failure under a smaller bound is not evidence
of infinitude.

These results do not classify perturbed matrices, symbolic parameter families,
or arbitrary representations of the algebra.  In particular,
“span rank 9” must not be read as “the monoid is \(M_3(\mathbb R)\).”

Run:

```powershell
python .\experiments\chiral_operator_monoids.py
python .\experiments\chiral_operator_monoids.py --json
python .\experiments\chiral_operator_monoids.py --state-cap 100 --depth-cap 8
```
