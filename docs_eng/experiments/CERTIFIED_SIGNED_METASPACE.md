# Certified Signed Metaspace

This experiment displays the 192-matrix combined operator monoid on a smaller
surface: every state is encoded exactly by three signed axis numbers. This is
not an approximation. It is a one-to-one, multiplication-preserving normal
form for the literal \(3\times3\) integer matrices.

```powershell
$py = 'C:\Users\Efe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

& $py -B .\experiments\certified_signed_metaspace.py
& $py -B .\experiments\certified_signed_metaspace.py --word 'Lh Lq Rh Rq Lh' --json
& $py -B .\experiments\certified_signed_metaspace.py --deep-check --json
```

## Exact three-coordinate normal form

With basis order \((1,h,q)=(e_1,e_2,e_3)\), every signed-basis action matrix
has a unique code

\[
a=(a_1,a_2,a_3)\in\{\pm1,\pm2,\pm3\}^3,\qquad
M(a)e_j=\operatorname{sgn}(a_j)e_{|a_j|}.
\]

The generators are

\[
L_h=(2,3,1),\quad L_q=(3,-1,3),\quad
R_h=(2,3,-1),\quad R_q=(3,1,3).
\]

Under the convention that a new generator is appended on the right,

\[
M(a)M(b)=M(a\star b),\qquad
(a\star b)_j=\operatorname{sgn}(b_j)a_{|b_j|}.
\]

This follows directly from column action. There are no floating-point values,
tolerances, or hash collisions.

## The 192 states inside 216

The ambient signed transformation monoid is

\[
\Sigma_3=\{\pm1,\pm2,\pm3\}^3,\qquad |\Sigma_3|=6^3=216,
\]

also readable as \(C_2\wr T_3\). Define

\[
\chi(a)=
\begin{cases}
0,& |a|\text{ is singular},\\
+1,& |a|\in A_3,\\
-1,& |a|\in S_3\setminus A_3.
\end{cases}
\]

Because absolute maps compose normally,
\(\chi(a\star b)=\chi(a)\chi(b)\), and the experimental monoid is exactly

\[
\boxed{\mathcal M=\chi^{-1}(\{0,+1\})}.
\]

Thus it contains every singular signed transformation and every unit whose
unsigned axis permutation is even. Only the 24 units with odd unsigned
permutation are excluded. “Even” does not mean determinant \(+1\): column
signs remain free. On the matrix surface,

\[
\chi(M)=\det(M)\prod_{j=1}^3s_j,
\]

where \(s_j\) is the sign of the unique nonzero entry in column \(j\).

| Layer | Absolute maps | Sign lifts | Total |
|---|---:|---:|---:|
| Rank 1 | \(3\) | \(2^3\) | 24 |
| Rank 2 | \(\binom32(2^3-2)=18\) | \(2^3\) | 144 |
| Even permutation units | \(|A_3|=3\) | \(2^3\) | 24 |
| **Combined** | 24 | 8 | **192** |

The 168 singular states form a two-sided ideal. Parity lives only on the unit
layer; singular composition absorbs it into \(0\).

## Generator rank and the redundant gate

Exact tuple BFS verifies

\[
\langle L_h,R_h,R_q\rangle=\mathcal M.
\]

Hence \(L_q\) is redundant for generating the combined monoid. Three
generators still reach all 192 states, with maximal minimal-word depth 9.
Three is also minimal: the unit group
\(C_2^3\rtimes A_3\cong C_2\times A_4\) needs at least two unit generators,
while entering the singular ideal needs a singular generator. Adding any one
of the 24 excluded odd units generates all 216 ambient states, so
\(\mathcal M\) is a maximal proper submonoid of \(C_2\wr T_3\).

## Exact oracle and fast lane

| Lane | Representation | Authority |
|---|---|---|
| Exact witness | Matrix with 9 integer entries | Authoritative source model |
| Certified compact | 3 signed axes and \(\star\) | Proven signed-action domain only |
| State table | 192 state IDs × 4 transitions | Derived accelerator |

The table is generated deterministically from the closed-form predicate, then
checked against exact matrix closure for state-set equality, all 768 generator
transitions, and canonical BFS depths. Model, state set, and transition table
have separate SHA-256 fingerprints. Matrices outside the signed-action domain,
such as \(2I\), fall back to exact integer matrices.

`--deep-check` compares all \(192^2=36{,}864\) compact products with the
matrix oracle, verifies all \(216^2=46{,}656\) character products, tests that
each excluded odd unit completes the ambient monoid, and confirms that
corrupted transitions and fingerprints are rejected.

## Certified fingerprints

```text
model       c42d225ccda025a81fc3941cff9a541d85f1011030885e8553a5b7f64a1c9a3e
states      82495596ee42be3ee8c946e5a64ebb93c2b2e9e43e24a074db7181800f02f971
transitions 8baeb58631b2c08f7c4e6bc88000258c01bec3d28fd1927ac87d21efeea530f7
```

A change closes as model/table drift requiring recertification; it is not
silently accepted.

## Epistemic boundary

**Algebraically exact:** signed-code composition equals matrix multiplication
on its declared domain; \(\chi\) is multiplicative; the singular set is an
ideal.

**Computationally certified:** equality between literal four-generator matrix
closure and the 192-state predicate, together with the transition, pair,
character, and maximal-extension checks.

**Not claimed:** physical speedup, noisy measurement, continuous extension, or
a physical interpretation. “Fast” means a smaller exact representation and
\(O(1)\) transition lookup.
