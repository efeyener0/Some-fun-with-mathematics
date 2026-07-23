# Metaspace Memory Duality

This experiment shows that the results of [Metaspace Observability](./METASPACE_OBSERVABILITY.md)
and [Metaspace Synchronizer](./METASPACE_SYNCHRONIZER.md) are two readings of
the same three equivalence kernels:

- **reading:** three root probes distinguish all 192 states;
- **erasure:** each of three rank-1 suffixes preserves one column and folds
  192 states into six outcomes.

“Duality” here means exact kernel equality, not a Hilbert-space adjoint,
thermodynamic law, or physical measurement claim.

```powershell
$py = 'C:\Users\Efe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py -B .\experiments\metaspace_memory_duality.py
& $py -B .\experiments\metaspace_memory_duality.py --deep-check --json
```

## The three columns of one state

In the [Certified Signed Metaspace](./CERTIFIED_SIGNED_METASPACE.md) normal
form, a state is \(a=(a_1,a_2,a_3)\). The root reads only the first column:

\[
o(M)=Me_1=a_1.
\]

Appending generators on the right changes the probe axis:

\[
o(ML_h)=Me_2=a_2,\qquad o(ML_q)=Me_3=a_3.
\]

Therefore

\[
\boxed{(o(M),o(ML_h),o(ML_q))=(a_1,a_2,a_3)},
\]

giving 192 distinct signatures for the 192 states.

## Three coordinate erasers

A rank-1 suffix \(p_k\) maps every basis vector to one coordinate line, so

\[
Mp_k=Np_k\iff Me_k=Ne_k.
\]

Its right-action kernel is exactly equality of column \(k\).

| Preserved column | Shortest suffix | Depth | Image | Fibres |
|---|---|---:|---:|---:|
| \(1\) | `Lh Lq Lq` | 3 | 6 | \(6\times32\) |
| \(h\) | `Lh Lh Lq Lq` | 4 | 6 | \(6\times32\) |
| \(q\) | `Lq Lq` | 2 | 6 | \(6\times32\) |

For retained coordinate set
\(I(p)=\{|p_1|,|p_2|,|p_3|\}\),

\[
\boxed{Mp=Np\iff M_i=N_i\text{ for every }i\in I(p)},\qquad
\boxed{\ker R_p=\bigcap_{i\in I(p)}E_i}.
\]

The seven reachable kernels are the nonempty subsets of the three-element
Boolean lattice. There is no empty retained set, hence no universal kernel and
no reset word.

## Kernel lattice

Each column-equality relation \(E_1,E_h,E_q\) consists of six 32-state classes:

\[
|E_k|=6\binom{32}{2}=2{,}976.
\]

\[
|E_1\cap E_h|=|E_1\cap E_q|=|E_h\cap E_q|=432,\qquad
|E_1\cap E_h\cap E_q|=0.
\]

Thus

\[
|E_1\cup E_h\cup E_q|=3(2{,}976)-3(432)=7{,}632.
\]

Of the \(18{,}336\) unordered pairs, the remaining \(10{,}704\) share no
coordinate column and can never synchronize. The same family therefore gives

\[
\boxed{E_1\cap E_h\cap E_q=\Delta}
\]

for complete tomography, while its union is the graph of pairs that some
rank-1 eraser can merge.

| Equal-column set | Pairs |
|---|---:|
| none | 10,704 |
| only \(1\) | 2,112 |
| only \(h\) | 2,112 |
| only \(q\) | 2,112 |
| \(1,h\) | 432 |
| \(1,q\) | 432 |
| \(h,q\) | 432 |

## Left and right information geometry

For a rank-\(r\) suffix \(p\), \(Mp=\{xp:x\in M\}\) measures retained source
columns, while \(pM=\{px:x\in M\}\) measures the freedom of three output
columns over the signed image alphabet.

| Rank | \(|Mp|\) | \(|pM|\) | \(M\to Mp\) fibre profile |
|---:|---:|---:|---|
| 1 | 6 | 8 | \(6\times32\) |
| 2 | 36 | 64 | \(12\times4+24\times6\) |
| 3 | 192 | 192 | \(192\times1\) |

For \(r\in\{1,2\}\),

\[
|Mp|=6^r,\qquad |pM|=(2r)^3.
\]

At rank 2, 12 of the 36 retained column-pairs have fibre size 4 and 24 have
size 6. This is the earlier fact that parity survives only on the unit layer,
reappearing as an information-fibre asymmetry.

## Verification

The script verifies all 192 tomography signatures, \(3\times18{,}336=55{,}008\)
eraser-kernel pair equalities, 73,728 left/right products over all suffixes,
and the rank/image/fibre profiles. Deep mode cross-checks the independent
observability and synchronizer reports.

**Exact scope:** the literal four generators, finite 192-state monoid, and
signed-code normal form. No claim is made about physical observability,
thermodynamic information loss, quantum duality, or automatic extension to
general matrix semigroups.
