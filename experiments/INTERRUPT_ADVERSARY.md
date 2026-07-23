# Interrupt scheduler contract probe

This report covers a benign local experiment on the pure register-transition
model in `nonassoc_interrupt_pet.py`. The subject file was treated as read-only.
No operating-system interrupt, device, network, or external service was used.

## Subject and reproducibility

- Subject: `C:\Users\Efe\Documents\Codex\2026-07-17\referenced-chatgpt-conversation-this-is-untrusted\outputs\nonassoc_interrupt_pet.py`
- SHA-256: `46A406DCDD402FAEB2BA67E4E904E81C00040322AB1D8C2B3B6FF8F5995FC098`
- Runtime actually used: CPython 3.12.13
- Seed: `20260717`
- Probe: `experiments/interrupt_adversary.py`

Run from the workspace root:

```powershell
& 'C:\Users\Efe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B '.\experiments\interrupt_adversary.py'
```

The probe imports the subject from its explicit path, disables bytecode writes,
and emits a deterministic JSON report. Its default bounded search is deliberately
small enough to inspect and repeat.

An additional depth-four exhaustive run was executed with:

```powershell
& 'C:\Users\Efe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B '.\experiments\interrupt_adversary.py' --random-trials 0 --workers 0 --max-events 4 --compact
```

## Concise result

Under the built-in operations and faithful effect declarations, serial and wave
execution agreed in every bounded and randomized case tested. The scheduler's
correctness is conditional, however: it trusts declared reads, trusts delivery-token
identity, and trusts callers not to pass arbitrary conflicting waves directly to
`execute_waves`.

| Probe | Cases | Result |
|---|---:|---|
| Source randomized validation | 5,000 trials | 0 serial/wave mismatches |
| Source stale-snapshot baseline | 5,000 trials | 4,860 mismatches (97.2%) |
| Exhaustive effect truth table | 256 ordered profile pairs | 0 predicate/tag mismatches |
| Bounded scheduler enumeration | 4,369 schedules | 0 structural failures |
| Concrete bounded executions | 39,321 states/schedules | 0 serial/wave mismatches |
| Reversed valid wave-member order | 39,321 executions | 0 merge-order mismatches |
| Extended depth-four enumeration | 69,905 schedules | 0 structural failures |
| Extended depth-four executions | 629,145 states/schedules | 0 serial/wave or merge-order mismatches |

## Verified facts

These statements were directly checked by executable assertions.

### 1. The documented baseline reproduces

The deterministic example produced:

```text
serial            = (35, 37, 11, 14, 7, 2)
scheduled parallel= (35, 37, 11, 14, 7, 2)
blind parallel    = (15, 17, 11, 14, 7, 2)
```

Its waves were:

```text
wave 0: high_mul3_r0, network_r2, disk_r3
wave 1: io_copy_r0_to_r1
wave 2: timer_add5_r0
```

The same scheduled result was obtained with four thread workers. The 5,000-trial
random run exactly reproduced the whitepaper values: 0 serial/wave mismatches,
4,860 blind mismatches, 15,534 folded retries, 115,805 hazard edges, and mean
idealized parallelism 2.4798273065823064.

### 2. The conflict predicate matches RAW/WAR/WAW overlap

For every combination of declared read and write subsets over two registers,
the probe compared `conflicts(left, right)` with an independently written set
predicate:

```text
(left.write ∩ right.read) != ∅
or (right.write ∩ left.read) != ∅
or (left.write ∩ right.write) != ∅
```

All 256 ordered profile pairs agreed. `hazard_tag` was nonzero for exactly the
same 192 conflict pairs and zero for the remaining 64.

### 3. Bounded serial/wave equivalence holds

The bounded space used:

- two registers;
- values `{-1, 0, 1}` for each initial register;
- `add`, `mul`, `set`, and `copy_add`, targeting both registers;
- priorities `{0, 1}`;
- every event sequence from length zero through three.

This is 4,369 distinct schedule inputs and 39,321 concrete executions. Every
conflicting reference-order pair appeared in a strictly later wave, all 9,016
conflicting pairs corresponded one-for-one with reported hazard edges, and all
events appeared exactly once in their maximally early legal wave. All serial and
scheduled states agreed. Reversing member order inside every valid wave did not
change any final state.

This bounded space includes repeated operation templates, same-target chains,
cross-register copies, equal priorities, mixed priorities, empty schedules, and
both convergent and independent dependency shapes.

A separate depth-four run expanded this to 69,905 schedule inputs and 629,145
concrete executions. It checked 291,640 conflicting reference pairs and 114,120
independent pairs. Serial/wave mismatches and reversed valid-wave merge mismatches
both remained zero. This deeper run used zero randomized trials so its evidence is
additive to, rather than a duplicate of, the 5,000-trial random baseline.

### 4. Duplicate-token behavior is internally consistent

- Three deliveries with one token and one signature kept the earliest
  reference-order event and folded two; the ACK state remained `q = (0, 0, 1)`.
- Two otherwise identical deliveries with `delivery_id=None` both remained.
- Reusing a token with a changed constant raised `ValueError`.
- Reusing a token with a changed priority also raised `ValueError`.

### 5. Priority ordering and legal parallel overlap behave as documented

A high-priority write and a lower-priority conflicting update were placed in
that order in separate waves. A still-lower-priority independent write shared
wave 0 with the high-priority event:

```text
reference: high_conflicting, low_conflicting, lowest_independent
wave 0:    high_conflicting, lowest_independent
wave 1:    low_conflicting
```

This preserves the serial result while allowing an independent low-priority
event to overlap. It does not claim completion-time priority or real-time
scheduling.

## Observed contract boundaries

These are concrete behaviors, not hypothetical concerns.

### A. Undeclared reads are not detectable

An event wrote register 0. A following event actually read register 0 into
register 1 but declared no reads. The builder placed both in one wave:

```text
initial = (2, 0)
serial  = (7, 7)
wave    = (7, 2)
```

This is the smallest useful counterexample to unconditional equivalence. It is
consistent with the source's stated model: read/write declarations are the
correctness oracle. The implementation checks returned write keys, but it has
no mechanism to observe which snapshot locations an evaluator read.

### B. Undeclared writes are checked at merge time

An evaluator declaring writes `{0}` but returning an update for register 1 was
rejected with:

```text
AssertionError: undeclared_writer wrote outside its declaration
```

The asymmetry matters: actual writes are visible in the returned dictionary;
actual reads are not.

### C. Conservative declarations remain correct but reduce parallelism

A constant write to register 1 falsely declared a read of register 0. It was
serialized after a register-0 writer even though the evaluators could safely
share a wave. Serial and wave results still agreed. Over-declaration therefore
costs parallelism; under-declaration can cost correctness.

### D. `execute_waves` assumes its waves are already conflict-free

When a register-0 increment and a register-0-to-register-1 copy were manually
placed in one wave, their returned write keys were disjoint, so `execute_waves`
did not reject the input:

```text
serial result       = (3, 3)
manual one-wave result = (3, 2)
```

`build_parallel_waves` correctly separated the same events and recovered
`(3, 3)`. Overlapping writes in a manually supplied wave were rejected, but a
RAW conflict with disjoint returned writes was not. Therefore “wave is
conflict-free” is a precondition of `execute_waves`, not a property that function
fully validates.

### E. A same-token/same-signature collision is indistinguishable from a retry

The duplicate signature contains priority, operation, target, source, and
constant. It does not contain name or arrival. A second event with the same token
and signature but a different name and arrival was folded.

That is coherent if the token uniquely denotes one logical delivery. The code
cannot establish that uniqueness; it is an external input contract. The phrase
“exact retry” should therefore be read as “same trusted token and checked
signature,” not as independently proven event identity.

### F. The total-order key has a final stable-input fallback

The explicit sort key is `(-priority, arrival, name)`. Arrival ties are broken by
name. If priority, arrival, and name all tie, Python's stable sort preserves the
caller's input order. Reversing two such conflicting inputs changed the result:

```text
add then mul: (2 + 1) * 2 = 6
mul then add: (2 * 2) + 1 = 5
```

Thus ordering is deterministic for a fixed input sequence, but the fields do not
form a unique total order over arbitrary events. A model requiring order to be
independent of input-container iteration needs a unique final key (for example,
a canonical event sequence number) or validation that the existing key is unique.

### G. The random generator has an implicit minimum register count

With deterministic seed 5, `random_event(..., register_count=1)` selected
`copy_add` and failed with `ValueError: empty range for randrange()`. The generator
requires at least two registers because it insists on a source distinct from the
target; that precondition is not validated at its API boundary. The normal
default of six registers is unaffected.

## Inferences, explicitly separated

The following conclusions are grounded in the code and observations but are not
formal proofs over arbitrary extensions.

1. **The built-in scheduler is structurally sound under faithful declarations.**
   The all-pairs conflict DAG orders every potentially noncommuting built-in
   transition, while same-wave events neither consume each other's writes nor
   overwrite the same register. The bounded result is strong evidence for the
   implementation; it is not a proof for user-defined evaluators.

2. **The algebraic residual is a control label, not the source of dependency
   discovery.** `build_parallel_waves` only distinguishes `ZERO` from the fixed
   nonzero `ORDER_RESIDUAL`; read/write overlap decides where the label appears.
   Replacing that residual with another consistently nonzero sentinel would not
   alter this scheduler's wave structure. This is an implementation-level
   inference, not a judgment about richer uses of the algebra elsewhere.

3. **The strongest accurate claim is conditional serializability.** The observed
   implication is:

   ```text
   faithful effects
   + fixed reference order
   + builder-produced conflict-free waves
   + trusted delivery identity
   => serial-equivalent wave execution for this transition model
   ```

4. **The randomized test is useful regression evidence, but the bounded search
   explains more.** The 5,000 random cases cover wider event lists; the bounded
   enumeration supplies complete coverage of its declared small domain and
   directly exercises ties, short chains, and every operation string within that
   domain.

## Focused hardening options

These are recommendations, not changes made to the subject.

1. Make `execute_waves` internal, or have it validate declared pairwise conflicts
   in every supplied wave. This closes the manual-wave API gap.
2. Add a canonical unique sequence field to the reference-order key, or reject
   duplicate `(priority, arrival, name)` keys when conflicting effects exist.
3. State token uniqueness as an explicit constructor/API precondition; signature
   comparison detects changed effects but cannot prove logical identity.
4. Validate `register_count >= 2` in `randomized_validation` and `random_event`,
   or define one-register `copy_add` generation semantics.
5. Keep the current documentation's narrow claim that effect declarations, not
   the associator alone, establish hazards. The executable evidence supports that
   formulation precisely.

## Validation status

- Both subject baseline commands completed successfully.
- The standalone probe completed successfully with exit code 0.
- The supplementary depth-four run completed successfully with exit code 0.
- All assertions described above ran under CPython 3.12.13.
- No source file was modified.
- No claim is made about arbitrary handlers, unbounded event counts, real-time
  behavior, GPU speed, or physical interrupt systems.
