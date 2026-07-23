# Signed Metaspace Family

This experiment separates the genuinely three-dimensional features of the
192-state construction from a general signed-transformation geometry. \(M_n\)
is an abstract finite monoid family; only \(M_3\) is identified with the
literal chiral operator monoid.

## Definition

\[
a=(a_1,\ldots,a_n)\in\{\pm1,\ldots,\pm n\}^n,\qquad
a(e_j)=\operatorname{sgn}(a_j)e_{|a_j|}.
\]

The ambient monoid is

\[
\Sigma_n=C_2\wr T_n,\qquad |\Sigma_n|=(2n)^n.
\]

Let \(\chi_n\) be \(0\) for singular absolute maps, \(+1\) for even
permutations, and \(-1\) for odd permutations. Signed composition obeys

\[
(a\star b)_j=\operatorname{sgn}(b_j)a_{|b_j|},\qquad
\chi_n(a\star b)=\chi_n(a)\chi_n(b).
\]

For \(n\ge2\),

\[
\boxed{M_n=\chi_n^{-1}(\{0,+1\})},\qquad
U(M_n)=C_2^n\rtimes A_n.
\]

It contains every singular map and exactly the units with even unsigned
permutation. It is a maximal proper submonoid of the ambient monoid.

## Cardinality and ranks

For \(1\le r<n\),

\[
\boxed{|M_{n,r}|=2^n\binom nr r!\,S(n,r)},\qquad
\boxed{|M_{n,n}|=2^{n-1}n!},
\]

\[
\boxed{|M_n|=(2n)^n-2^{n-1}n!}.
\]

| \(n\) | Ambient | \(|M_n|\) | Excluded odd units | Minimum right-action image |
|---:|---:|---:|---:|---:|
| 2 | 16 | 12 | 4 | 4 |
| 3 | 216 | 192 | 24 | 6 |
| 4 | 4,096 | 3,904 | 192 | 8 |
| 5 | 100,000 | 98,080 | 1,920 | 10 |
| 6 | 2,985,984 | 2,962,944 | 23,040 | 12 |

Independent tuple enumeration makes the \(n=3\) row exactly equal to the
literal 192-state source oracle.

## General action formulas

For rank \(r<n\),

\[
\boxed{|M_np|=(2n)^r},\qquad
\boxed{|pM_n|=(2r)^n}.
\]

The rank-\(s\) layers are

\[
\boxed{|\{z\in M_np:\operatorname{rank}z=s\}|
=2^r(n)_sS(r,s)},
\]

\[
\boxed{|\{z\in pM_n:\operatorname{rank}z=s\}|
=2^n(r)_sS(n,s)}.
\]

If \(I(p)\) is the unsigned image-column set,

\[
\boxed{xp=yp\iff x_i=y_i\text{ for every }i\in I(p)}.
\]

Minimum right-action image is \(2n\), minimum left-translation image is
\(2^n\), and no \(M_n\) has a reset word.

## Parity scar in projection fibres

For \(r\) retained columns, a colliding partial absolute map has fibre

\[
F_{\mathrm{collision}}=(2n)^{n-r}.
\]

An injective partial map with at least two missing columns has

\[
F_{\mathrm{injective}}
=(2n)^{n-r}-2^{n-r-1}(n-r)!.
\]

With one missing column, fibre size is \(2n\) for an even unique completion
and \(2n-2\) for an odd one. At \(n=3,r=2\):

\[
24\cdot6+12\cdot4=192.
\]

At \(n=2\), root fibres are nonuniform: \(2\cdot4+2\cdot2=12\). For \(n\ge3\),

\[
\boxed{F_{\mathrm{root}}
=(2n)^{n-1}-2^{n-2}(n-1)!=\frac{|M_n|}{2n}}.
\]

## Verification and scope

```powershell
$py = 'C:\Users\Efe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py -B .\experiments\signed_metaspace_family.py --deep-check --max-n 8 --json
```

The implementation materializes \(n=2,3,4\), checks cardinalities, rank
layers, fibres, both action images and kernels, and bridges \(M_3\) to the
certified chiral states. Deep mode verifies character multiplicativity over
all ambient products for \(n=2,3\).

Closure, counting, action, fibre, and no-reset formulas are algebraically
proved; profiles through \(n=4\) and the \(n=3\) bridge are enumerated. No
source nonassociative algebra, generator set, physical metaspace, or inherited
rank-weather dynamics is claimed for \(n\ne3\).
