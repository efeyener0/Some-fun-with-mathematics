# Shadow Root Seams

`shadow_root_seams.py` determines which products the strong root contract
forces in minimal six-dimensional extensions and which seam remains free.

\[
A=\operatorname{span}_{\mathbb R}\{1,h,q\},\quad
h^2=q,\ hq=1,\ qh=-1,\ q^2=q,
\]

\[
s^2=h,\qquad L_s^2=L_h,\qquad R_s^2=R_h.
\]

The sparse clock additionally chose \(sq=qs\); that is a symmetric seam, not a
consequence of the strong-root axioms.

## Canonical six-chain

Let \(t=sh=hs\) and \(u=qs\). The same five-dimensional obstruction proves
that \((1,s,h,t,q,u)\) is a canonical basis for every minimal six-dimensional
extension. In this basis

\[
R_s:1\to s\to h\to t\to q\to u\to-1
\]

is fixed.

## Left seam equation

Write

\[
a:=sq=\sum_{j=0}^{5}c_je_j,\qquad d:=su.
\]

Then \(L_s:(1,s,h,t,q,u)\mapsto(s,h,t,q,a,d)\), and the remaining root
condition is simply \(L_s(a)=1\).

If \(c_5\ne0\), \(a\) is free and

\[
d=\frac{1-c_0s-c_1h-c_2t-c_3q-c_4a}{c_5}.
\]

This open branch is six-parameter; the old clock is \(a=u,d=1\).

If \(c_5=0\), elimination gives \(c_4^6=1\), leaving only

\[
a_+=1-s+h-t+q,\qquad
a_-=-(1+s+h+t+q),
\]

with arbitrary \(d\). These are two exceptional six-dimensional branches.

## Completion dimensions

Eight further \(B\)-valued cells remain free:
\(qt,qu,tq,uq,tt,tu,ut,uu\).

| Table space | Root seam | Completion | Total |
|---|---:|---:|---:|
| Ungraded | 6 | \(8\cdot6=48\) | 54 |
| \(\mathbb Z_2\)-graded | 3 | \(8\cdot3=24\) | 27 |

These are dimensions in the chosen canonical basis, not dimensions of
isomorphism-class quotients.

## The fifth leaf reads the seam

Repeated-\(s\) trees agree through four leaves as \(s,h,t,q\). At five leaves,
the 14 Catalan trees split exactly:

\[
\boxed{\operatorname{Hist}_5=\{a:7,\ u:7\}}.
\]

Thus asymmetric seams shock at degree five. Only \(a=u\) collapses all 14
trees to \(u\), postponing the clock's first shock to degree six. For example,

\[
sq=s-t+2u,\qquad su=\tfrac12(1-h+q)
\]

gives `(s-t+2u):7, u:7`.

```powershell
python experiments/shadow_root_seams.py report --example clock --max-leaves 10
python experiments/shadow_root_seams.py test --deep
```

Default tests check the source table, strong-root identities, the degree-five
\(7+7\) law, equality of the clock table up to basis permutation, and its
degree-six \(19+4+19\) histogram. Deep mode tests 972 small integer open-branch
seams, 26 choices on the exceptional branches, and Catalan ledgers through 12
leaves.

The 54-parameter table family is not an isomorphism classification; distinct
parameters are not claimed non-isomorphic, full automorphism groups are not
computed, and this family is not the ordinary universal root adjunction.
