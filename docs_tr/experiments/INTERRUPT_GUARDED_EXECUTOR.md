# Guarded executor: making the pet model's contracts executable

`interrupt_guarded_executor.py` wraps the read-only register-transition model
with runtime checks at the exact boundaries exposed by the adversarial probe.
It remains a benign local mathematical toy: no operating-system interrupt,
device, network, or external service participates.

## Outcome

The guarded layer converts the two earlier silent failure modes into explicit
rejections:

- a hidden register read is rejected before its wave can merge;
- a manually supplied RAW-conflicting wave is rejected before any evaluator in
  the supplied wave plan runs.

It also rejects writes outside declarations and conflicting events whose
`(priority, arrival, name)` keys are identical. The original documented demo and
a complete deterministic depth-three corpus remain serial-equivalent.

## Subject and run command

- Subject: `C:\Users\Efe\Documents\Codex\2026-07-17\referenced-chatgpt-conversation-this-is-untrusted\outputs\nonassoc_interrupt_pet.py`
- Subject SHA-256: `46A406DCDD402FAEB2BA67E4E904E81C00040322AB1D8C2B3B6FF8F5995FC098`
- Runtime used: CPython 3.12.13
- Guarded executor: `experiments/interrupt_guarded_executor.py`

Run from the workspace root:

```powershell
& 'C:\Users\Efe\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -B '.\experiments\interrupt_guarded_executor.py' --max-events 3
```

The command completed with exit code 0. `-B` prevents bytecode artifacts, and
the loader also disables bytecode writes before importing the read-only subject.

## Execution architecture

```text
delivery fold
  -> conflicting duplicate-key validation
  -> subject conflict-DAG builder
  -> whole-plan pairwise wave preflight
  -> TrackedState evaluation
  -> actual-read / actual-write validation
  -> disjoint update merge
```

The algebra and scheduler remain unchanged. The wrapper strengthens the
interfaces around them.

## The guards

### 1. `TrackedState` records actual reads

`TrackedState` implements `collections.abc.Sequence[int]`, so the existing
handlers continue to use `len(snapshot)` and `snapshot[index]`. Integer access
records the canonical non-negative register index. Negative indices are
normalized; slices record every value materialized by the slice; inherited
sequence iteration passes through indexed access.

The self-check observed:

```text
state            = (10, 20, 30)
observations     = state[1], state[-1], state[:1]
values           = 20, 30, (10,)
recorded reads   = {0, 1, 2}
```

An independent `tuple(TrackedState((40, 50)))` iteration returned `(40, 50)`
and recorded reads `{0, 1}`.

After an evaluator returns, its recorded reads must be a subset of
`event.reads`.

### 2. Returned writes are checked

Update mappings are validated before merge:

- register keys must be integers within state bounds;
- values must be integers, preserving the pet's `State = tuple[int, ...]` model;
- returned keys must be a subset of `event.writes`.

Conservative declarations remain legal. The guard enforces coverage, not exact
equality.

### 3. The entire wave plan is preflighted

Before evaluating any event, every supplied wave is checked for pairwise RAW,
WAR, or WAW conflict using the subject's declared-effect predicate. This is
stronger than checking only overlapping returned writes at merge time.

A two-wave test placed a harmless counting evaluator in wave 0 and conflicting
writes in wave 1. The executor rejected wave 1 while the wave-0 evaluation count
remained exactly zero. Thus the structural preflight covers the complete plan,
not merely the next wave.

### 4. Conflicting duplicate order keys are rejected

The subject sorts by:

```text
(-priority, arrival, name)
```

The guard groups events by the equivalent identity key
`(priority, arrival, name)`. If two events in one group conflict according to
the effect model, their relative order could matter and the guard raises
`AmbiguousOrderKeyError`.

Duplicate keys are permitted for declared-independent events because their
relative order is semantically irrelevant under faithful effects. This check is
intentionally conservative: declared conflict is treated as sufficient evidence
of potential order sensitivity; the guard does not try to prove that two
specific arithmetic functions happen to commute.

Duplicate delivery folding occurs before this order-key check. A genuine retry
with one trusted delivery token is therefore folded first; distinct remaining
events must have an unambiguous conflicting order.

## Exact rejection demonstrations

### Hidden read

The subject builder placed the deliberately under-declared writer and reader in
one wave because their declarations appeared independent. `TrackedState`
observed the hidden read and raised:

```text
EffectDeclarationError: event 'hidden_reader_to_r1' actually read [0] outside declared reads []
```

No update from that wave was merged.

### Undeclared write

An event declared writes `{0}` but returned an update for register 1:

```text
EffectDeclarationError: event 'undeclared_writer' actually wrote [1] outside declared writes [0]
```

### Manually supplied RAW wave

The earlier counterexample manually grouped a register-0 increment with a copy
from register 0 into register 1. Their returned writes are disjoint, but the copy
depends on the increment. The guarded executor now rejects this structure before
evaluation:

```text
WaveConflictError: wave 0 contains declared conflict between 'raw_writer' and 'raw_reader'
```

Passing the same events through `build_parallel_waves` produced two waves and
the correct guarded result `(3, 3)`.

### Complete-plan preflight

The later-wave WAW demonstration raised:

```text
WaveConflictError: wave 1 contains declared conflict between 'later_conflict_a' and 'later_conflict_b'
```

The first-wave evaluator count at rejection was `0`.

### Conflicting duplicate total-order key

Two events named `same`, both priority 5 and arrival 0, performed `add 1` and
`mul 2` on the same register. Without the guard, caller input order produced:

```text
add -> mul = (6,)
mul -> add = (5,)
```

The guarded order constructor rejected the pair:

```text
AmbiguousOrderKeyError: conflicting events 'same' and 'same' share total-order key (5, 0, 'same')
```

As a control, two same-key writes to different registers were accepted in both
caller orders and produced `(5, 8)` both times.

## Documented demo: preserved

The reconstructed source demo passed unchanged through token folding, guarded
ordering, subject wave construction, tracked serial execution, and tracked wave
execution:

```text
duplicates folded = 1
hazard edges       = 3

wave 0 = high_mul3_r0, network_r2, disk_r3
wave 1 = io_copy_r0_to_r1
wave 2 = timer_add5_r0

guarded serial = (35, 37, 11, 14, 7, 2)
guarded wave   = (35, 37, 11, 14, 7, 2)
```

No faithful built-in handler was rejected.

## Deterministic bounded corpus

The complete bounded domain was:

- two registers;
- eight templates covering `add`, `mul`, `set`, and cross-register `copy_add`;
- event sequence lengths zero through three;
- priority values `{0, 1}`;
- initial register values `{-1, 0, 1}`.

Exact results:

| Measurement | Result |
|---|---:|
| Schedule inputs | 4,369 |
| Concrete state/schedule executions | 39,321 |
| Guarded event evaluations | 230,688 |
| Hazard edges | 9,016 |
| Maximum wave width | 2 |
| Subject-serial vs guarded-serial mismatches | 0 |
| Guarded-serial vs guarded-wave mismatches | 0 |
| Guard rejections for faithful built-ins | 0 |

The subject serial executor was retained as a compatibility oracle. Every case
also ran through a separately guarded serial path, so equivalence establishes
both that the wrapper preserved valid handler semantics and that guarded wave
execution preserved the guarded reference order.

## Verified, observed, and inferred

### Verified by execution

- Ordinary integer, negative-index, slice, and sequence-mediated reads are
  recorded.
- Actual read and write excesses are rejected with explicit errors.
- All supplied waves pass pairwise conflict preflight before any evaluator runs.
- Conflicting duplicate total-order keys are rejected; independent duplicates
  remain allowed.
- The documented demo is unchanged.
- All 39,321 bounded executions are serial-equivalent.

### Observed design consequence

An incomplete read declaration no longer yields a silently stale committed
state. The builder may initially place the event too early because it can only
see declarations, but tracked evaluation detects the discrepancy before the
wave merge. An invalid manually assembled wave is rejected even earlier, during
whole-plan structural preflight.

### Inference, not a formal proof

For the pet's pure handler model, the guarded composition strengthens the earlier
conditional statement to:

```text
builder-produced or pairwise-validated waves
+ per-evaluation effect coverage
+ unambiguous conflicting reference keys
=> fail-closed execution within the observed bounded domain
```

The bounded corpus is exhaustive only inside its stated domain. It is not a
proof for arbitrary Python evaluators or unbounded schedules.

## Scope limits

- Read tracking covers accesses mediated through the supplied `Sequence` view.
  It is a software instrumentation contract, not language-level isolation from a
  deliberately introspective evaluator.
- Evaluators are assumed pure apart from their returned register update, matching
  the subject model. The wrapper does not attempt transactional rollback of
  arbitrary Python side effects.
- Declared effects still drive scheduling. Dynamic tracking verifies the executed
  path before merge; it does not predict all possible future paths.
- Duplicate-key rejection uses declared conflict as a conservative witness of
  possible order sensitivity; it is not an algebraic commutativity prover.
- No claim is made about real-time behavior, GPU performance, devices, or physical
  interrupt delivery.

## Workspace integrity

The subject remained read-only and retained its original SHA-256. This experiment
created only the guarded executor and this report; it did not modify the pet,
the earlier adversarial probe, or other workspace experiments.
