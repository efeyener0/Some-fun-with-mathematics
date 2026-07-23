# Shadow Root Deformations

`shadow_root_deformations.py` treats the six-dimensional shadow clock table as
one point in an exact affine family of bilinear completions.

## Scope

The basis \((1,h,q,s,t,u)\), source subalgebra \(A\), and literal \(L_s,R_s\)
clocks are fixed. In this gauge \(sq=qs=u\) belongs to the skeleton, although
the strong-root axioms alone do not force it. Consequently this is the
completion fibre of one clock skeleton, not the moduli space of every minimal
strong-root extension. See [Shadow Root Seams](./SHADOW_ROOT_SEAMS.md) for the
broader seam family.

## Dimensions 48 and 24

A bilinear product has \(6^3=216\) structure constants. Unit and source-table
constraints, literal root operators, and their square identities fix 28
ordered cells. Eight \(B\)-valued cells remain:

\[
qt,qu,tq,tt,tu,uq,ut,uu.
\]

Thus

\[
\operatorname{rank}C_{root}=168,\qquad
\dim\mathcal F_{clock}=216-168=48.
\]

Under the natural grading
\(B_{\bar0}=\operatorname{span}(1,h,q)\),
\(B_{\bar1}=\operatorname{span}(s,t,u)\), wrong-grade coordinates add 24
constraints:

\[
\operatorname{rank}C_{graded}=192,\qquad
\dim\mathcal F_{clock}^{\mathbb Z_2}=24.
\]

## Fibre-wide invariants and first variable degree

Every completion preserves the literal root equations, all four root/clock
matrices, their orders \(6,12,3,6\), determinant and nilpotent-defect data,
the 384-state group, both comb sequences, and the generation ladder.

Repeated \(s\) is forced to \(s,h,t,q,u\) through degree five. At degree six,

\[
\boxed{\mu_6=19\delta_{+1}+19\delta_{-1}+4\delta_{tt}}.
\]

The sparse origin has `t*t=0`, yielding `-1:19, 0:4, +1:19`; setting
`t*t=1` changes this to `-1:19, +1:23`. Isolated seam visibility begins at:

| Cell | First degree |
|---|---:|
| `t*t` | 6 |
| `q*t`, `t*q` | 7 |
| `t*u`, `u*t` | 8 |
| `q*u`, `u*q` | 9 |
| `u*u` | 10 |

## Completion-sensitive structure

At the sparse origin the three nuclei and centre have dimension 1, the
commutant has dimension 2, associator rank is 6, and derivations vanish.
Changing only `q*t=s` reduces the commutant dimension to 1 while preserving
all root/operator invariants. Maximum-rank minors show the other listed
properties persist on a nonempty Zariski-open neighbourhood, not necessarily
on the entire 48-dimensional family.

Deep tests scan all 48 positive coordinate-elementary completions: nuclei,
centre, associator rank, and derivations remain unchanged; commutant dimension
is 1 for 22 cases and 2 for 26. This is finite evidence, not a global theorem.

```powershell
python .\experiments\shadow_root_deformations.py report --json
python .\experiments\shadow_root_deformations.py test --deep
```

The affine dimensions, fibre-wide operator invariants, degree-six measure, and
isolated visibility ladder are proved within the fixed skeleton. A
classification of all minimal extensions, every rank-jump stratum,
universality/canonicity, and coverage of all real parameters are not claimed.
