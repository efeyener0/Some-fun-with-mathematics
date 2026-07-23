# Associahedron Holonomy

`associahedron_holonomy.py` reinterprets the rotation edges of Associahedron
Weather as a discrete connection. Vanishing root-phenotype circulation is only
the beginning: the experiment identifies the transported residual and the
information flattened only by root projection.

It uses exact algebra and trees from `bracket_garden.py` and the exact
single-rotation graph from `associahedron_weather.py`. There are no external
packages, randomness, or floating point; Python 3.10 or newer is required.

## Edge connection

For an edge \(((AB)C)\to A(BC)\), let

\[
r_e=[a,b,c]=(ab)c-a(bc).
\]

The tree outside the rotated subtree defines a one-hole linear context map
\(C_e:A\to A\), constructed as an exact \(3\times3\) integer matrix by placing
each basis element \(1,h,q\) in the hole. Every edge satisfies

\[
\boxed{\Delta_e^{root}=C_e(r_e)}.
\]

A `DAMPED` edge therefore means \(r_e\ne0\) but \(r_e\in\ker C_e\).
Full-rank contexts cannot extinguish a nonzero associator. “Connection” is
operational here: \(C_e\) transports a local residual to the common root
algebra. It need not be invertible.

## Three levels of flatness

### 1. Root 1-form

With vertex potential \(F(T)=\operatorname{eval}_T(w)\),

\[
\omega_e=F(source)-F(target)=\Delta_e^{root}
\]

is an exact gradient, hence \(\oint\omega=0\) on every cycle.

### 2. Raw local-frame holonomy

Naively identifying all local copies of \(A\) in the same \((1,h,q)\) frame
gives

\[
H_F^{raw}=\sum_{e\in\partial F}\operatorname{sign}(e)r_e.
\]

This need not vanish. With context correction \(k_e=(C_e-I)r_e\), every square
and pentagon closes exactly:

\[
\boxed{H_F^{raw}+\sum_{e\in\partial F}\operatorname{sign}(e)k_e=0}.
\]

The root connection is flat; the raw associator frame generally is not. Raw
holonomy depends on this canonical basis identification and is not claimed to
be intrinsic physical curvature.

### 3. Square mixed curvature

For canonical square vertices \(T_0,T_1,T_2,T_3\),

\[
K_\square=F(T_0)-F(T_1)+F(T_2)-F(T_3).
\]

This is a discrete mixed finite difference, not root circulation. The two
cross-effects agree exactly:

\[
\Delta_A^{after}-\Delta_A^{before}
=\Delta_B^{after}-\Delta_B^{before}
=-K_\square.
\]

Nonzero \(K_\square\) means that syntactically commuting reassociations do not
have additively independent phenotype effects.

## Pentagon coherence

For four macro-elements,

\[
[a,b,c]d+[a,bc,d]+a[b,c,d]=[ab,c,d]+[a,b,cd].
\]

The script checks this exact polynomial identity on all \(3^4=81\) basis
quadruples; multilinearity extends it to all of \(A^4\). Embedded paths have
equal root sums, although their bare local associator sums may differ. That
difference is raw holonomy and context correction is its negative.

## 2-cell ledger

```powershell
python .\experiments\associahedron_holonomy.py topology --max-leaves 8
```

| Leaves | Squares | Pentagons |
|---:|---:|---:|
| 3 | 0 | 0 |
| 4 | 0 | 1 |
| 5 | 3 | 6 |
| 6 | 28 | 28 |
| 7 | 180 | 120 |
| 8 | 990 | 495 |

\[
P_n=\binom{2n-4}{n-4},\qquad Q_n=\frac{n-4}{2}P_n.
\]

Square signatures are also checked to have form `A,B,A,B`, while pentagons
contain five distinct rotation forms.

## CLI and tests

```powershell
python .\experiments\associahedron_holonomy.py analyze hhqqhq
python .\experiments\associahedron_holonomy.py analyze hhhhhhh --face-limit 0
python .\experiments\associahedron_holonomy.py expedition
python .\experiments\associahedron_holonomy.py test
python .\experiments\associahedron_holonomy.py test --deep
```

The expedition exhausts all positive `h/q` words for \(n=4,\ldots,7\) and
ranks separate objectives: nonzero square raw holonomy, pentagon raw holonomy,
square mixed curvature, and damped edges. Deep tests regenerate the \(n=8\)
ledger and all connection/face assertions for 254 words through \(n=7\).

## Exact observations

For `hhqqhq`, context ranks are \(3:47,2:34,1:3\); 14 of 28 squares have
nonzero raw holonomy, 15 have nonzero mixed curvature, and 17 of 28 pentagons
have nonzero raw holonomy.

For pure \(h^7\), context ranks are \(3:258,2:68,1:4\); the corresponding
counts are 105 of 180 squares, 117 of 180 squares, and 90 of 120 pentagons.
These are finite exhaustive observations, not all-\(n\) theorems.

## Epistemic boundary

The gradient law, edge factorization, context-compensated closure, square
cross-effect equality, and pentagon associator identity are algebraic results.
Face ledgers through \(n=8\), named profiles, and the 254-word search through
\(n=7\) are finite exact computation. Raw local holonomy is frame-dependent;
mixed-curvature sign depends on cycle orientation, although zero versus
nonzero does not. No physical gauge field, energy interpretation, all-degree
generalization, or rank-only activity criterion is claimed.
