# Shadow Root Clock

`shadow_root_clock.py` adjoins a missing root \(s^2=h\) while requiring the
regular operators themselves to be roots:

\[
s^2=h,\qquad L_s^2=L_h,\qquad R_s^2=R_h.
\]

The smallest finite real dimension satisfying all three conditions is six.

```powershell
python experiments/shadow_root_clock.py
python experiments/shadow_root_clock.py report --max-leaves 12 --json
python experiments/shadow_root_clock.py test --deep
```

## Why dimensions four and five fail

In \(A=\operatorname{span}_{\mathbb R}\{1,h,q\}\),

\[
h^2=q,\quad q^2=q,\quad hq=1,\quad qh=-1.
\]

For \(s=a+bh+cq\), the equations for \(s^2=h\) require both \(a^2=0\) and
\(2ab=1\), impossible over \(\mathbb R\). Under the strong contract,
\(sh=hs=:x\), \(sx=xs=q\), and

\[
1\mapsto s\mapsto h\mapsto x\mapsto q.
\]

The five vectors are independent. If dimension were five, writing the last
column of \(U=R_s\) and imposing \(U^2q=-1\) eliminates to

\[
\boxed{a_4^6=-1},
\]

again impossible over \(\mathbb R\). Hence \(\dim_{\mathbb R}B\ge6\); this is
a linear-algebraic certificate, not a bounded coefficient search.

## A six-dimensional witness

In basis \((1,h,q\mid s,t,u)\):

| \(\cdot\) | 1 | h | q | s | t | u |
|---|---:|---:|---:|---:|---:|---:|
| **1** | 1 | h | q | s | t | u |
| **h** | h | q | 1 | t | u | s |
| **q** | q | -1 | q | u | 0 | 0 |
| **s** | s | t | u | h | q | 1 |
| **t** | t | u | 0 | q | 0 | 0 |
| **u** | u | -s | 0 | -1 | 0 | 0 |

This is a sparse completion witness, not a uniqueness classification.

\[
L_s:1\to s\to h\to t\to q\to u\to1,
\]

\[
R_s:1\to s\to h\to t\to q\to u\to-1.
\]

Therefore \(L_s^6=I\), \(R_s^6=-I\), \(R_s^{12}=I\), and the required square
identities hold. The shadow channel supplies a second orientation reversal,
so \(\det R_h=(-1)(-1)=+1=\det(R_s)^2\).

The chiral defects satisfy

\[
\operatorname{rank}(L_s-R_s)=1,\quad (L_s-R_s)^2=0,
\]

and the corresponding \(h\)-level defect has rank 2 and square zero.

## Rigidity and the 384-state clock group

\[
N_\ell(B)=N_m(B)=N_r(B)=\mathbb R1,\quad
\operatorname{Comm}(B)=\operatorname{span}\{1,t\},\quad Z(B)=\mathbb R1.
\]

The associator flattening has rank 6 and kernel dimension 210;
\(\operatorname{Der}(B)=0\). Among 3,840 unit-fixing signed-basis
permutations, only identity and simultaneous sign reversal of \(s,t,u\) are
automorphisms. This does not classify all real-linear automorphisms.

\[
\langle L_s,R_s\rangle\cong C_2^6\rtimes C_6\cong C_2\wr C_6,
\qquad |\langle L_s,R_s\rangle|=384.
\]

The maximum shortlex depth is 11; element-order counts are
\(1:1,2:71,3:32,4:56,6:160,12:64\).

## Repeated-\(s\) trees

All Catalan trees agree through five leaves, yielding
\(s,h,t,q,u\). At six leaves:

\[
42=19+4+19,\qquad \operatorname{Hist}_6=\{-1:19,0:4,+1:19\}.
\]

The two combs expose opposite clock seams. Thus the root looks
bracketing-blind through degree five and shocks at degree six.

## Proof boundary

The six-dimensional lower bound, explicit table, strong root equations,
operator periods, determinant ledger, defect ranks, algebraic invariants,
384-state group, and Catalan histograms for this table are exact. The sparse
table is not claimed unique, universal, power-associative, or a classification
of all minimal completions. The ordinary universal nonassociative adjunction
is a different, infinite-dimensional object.
