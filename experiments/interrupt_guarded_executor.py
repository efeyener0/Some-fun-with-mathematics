"""Guarded executor for the local non-associative register-transition pet.

The read-only subject trusts effect declarations and conflict-free input waves.
This standalone wrapper makes those boundaries executable:

* ``TrackedState`` records actual register reads performed through ``Sequence``;
* actual reads and returned writes must be subsets of declared effects;
* every supplied wave is structurally preflighted for pairwise conflicts; and
* conflicting events may not share the subject's complete ordering key.

The experiment is pure, local, deterministic, and standard-library only.  It
does not model an operating system, device, network, or physical interrupt.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import operator
import platform
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Callable, overload


DEFAULT_PET = Path(
    r"C:\Users\Efe\Documents\Codex\2026-07-17"
    r"\referenced-chatgpt-conversation-this-is-untrusted\outputs"
    r"\nonassoc_interrupt_pet.py"
)
State = tuple[int, ...]
Evaluator = Callable[[Sequence[int]], Mapping[int, int]]
OrderIdentity = tuple[int, int, str]


class GuardError(RuntimeError):
    """Base class for explicit guarded-executor contract failures."""


class EffectDeclarationError(GuardError):
    """An evaluator observed effects outside its declared effect sets."""


class WaveConflictError(GuardError):
    """A supplied wave contains a declared RAW, WAR, or WAW conflict."""


class AmbiguousOrderKeyError(GuardError):
    """Conflicting events share every field of the reference-order key."""


class DeclarationSchemaError(GuardError):
    """An effect declaration or returned update is outside the state schema."""


class GuardInvariantError(GuardError):
    """The experiment itself observed an unexpected result."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GuardInvariantError(message)


class TrackedState(Sequence[int]):
    """Read-only state view that records every indexed register observation.

    Integer indices are canonicalized, so ``state[-1]`` records the final
    non-negative register index.  Slices record every element materialized by
    the slice.  Iteration inherited from ``Sequence`` passes through indexed
    access and is therefore tracked as well.
    """

    __slots__ = ("_values", "_read_indices")

    def __init__(self, values: Sequence[int]) -> None:
        self._values = tuple(values)
        self._read_indices: set[int] = set()

    def __len__(self) -> int:
        return len(self._values)

    @overload
    def __getitem__(self, index: int) -> int:
        ...

    @overload
    def __getitem__(self, index: slice) -> tuple[int, ...]:
        ...

    def __getitem__(self, index: int | slice) -> int | tuple[int, ...]:
        if isinstance(index, slice):
            selected = range(len(self._values))[index]
            self._read_indices.update(selected)
            return self._values[index]

        normalized = operator.index(index)
        if normalized < 0:
            normalized += len(self._values)
        if not 0 <= normalized < len(self._values):
            raise IndexError(f"state index out of bounds: {index}")
        self._read_indices.add(normalized)
        return self._values[normalized]

    @property
    def actual_reads(self) -> frozenset[int]:
        return frozenset(self._read_indices)


@dataclass(frozen=True, slots=True)
class ContractEvent:
    """Duck-typed event used for declaration-counterexample demonstrations."""

    name: str
    priority: int
    arrival: int
    declared_reads: frozenset[int]
    declared_writes: frozenset[int]
    evaluator: Evaluator

    @property
    def reads(self) -> frozenset[int]:
        return self.declared_reads

    @property
    def writes(self) -> frozenset[int]:
        return self.declared_writes

    def evaluate(self, snapshot: Sequence[int]) -> dict[int, int]:
        return dict(self.evaluator(snapshot))


@dataclass(frozen=True, slots=True)
class GuardedEvaluation:
    updates: dict[int, int]
    actual_reads: frozenset[int]
    actual_writes: frozenset[int]


@dataclass(frozen=True, slots=True)
class GuardedScheduleResult:
    ordered: tuple[object, ...]
    waves: tuple[tuple[object, ...], ...]
    serial: State
    wave: State
    folded: int
    hazard_edges: int


@dataclass(frozen=True, slots=True)
class EventTemplate:
    label: str
    op: str
    target: int
    source: int | None
    constant: int


TEMPLATES = (
    EventTemplate("add_r0", "add", 0, None, 1),
    EventTemplate("mul_r0", "mul", 0, None, -1),
    EventTemplate("set_r0", "set", 0, None, 2),
    EventTemplate("copy_r1_to_r0", "copy_add", 0, 1, -1),
    EventTemplate("add_r1", "add", 1, None, -1),
    EventTemplate("mul_r1", "mul", 1, None, 2),
    EventTemplate("set_r1", "set", 1, None, -2),
    EventTemplate("copy_r0_to_r1", "copy_add", 1, 0, 1),
)


def load_pet(path: Path) -> ModuleType:
    if not path.is_file():
        raise FileNotFoundError(path)
    sys.dont_write_bytecode = True
    module_name = "_nonassoc_interrupt_pet_for_guarded_executor"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not create module spec for {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(128 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def interrupt_event(
    pet: ModuleType,
    name: str,
    *,
    priority: int,
    arrival: int,
    delivery_id: str | None = None,
    op: str,
    target: int,
    source: int | None = None,
    constant: int = 0,
) -> object:
    return pet.InterruptEvent(
        name=name,
        priority=priority,
        arrival=arrival,
        delivery_id=delivery_id,
        op=op,
        target=target,
        source=source,
        constant=constant,
    )


def event_name(event: object) -> str:
    return str(getattr(event, "name", type(event).__name__))


def _validated_register_set(
    event: object,
    attribute: str,
    register_count: int,
) -> frozenset[int]:
    try:
        effect_set = frozenset(getattr(event, attribute))
    except (AttributeError, TypeError) as error:
        raise DeclarationSchemaError(
            f"event {event_name(event)!r} has no valid {attribute} declaration"
        ) from error

    for register in effect_set:
        if type(register) is not int or not 0 <= register < register_count:
            raise DeclarationSchemaError(
                f"event {event_name(event)!r} declares invalid {attribute} "
                f"register {register!r} for state size {register_count}"
            )
    return effect_set


def declared_effects(
    event: object,
    register_count: int,
) -> tuple[frozenset[int], frozenset[int]]:
    return (
        _validated_register_set(event, "reads", register_count),
        _validated_register_set(event, "writes", register_count),
    )


def evaluate_guarded(event: object, snapshot: State) -> GuardedEvaluation:
    declared_reads, declared_writes = declared_effects(event, len(snapshot))
    tracked = TrackedState(snapshot)
    raw_updates = event.evaluate(tracked)
    if not isinstance(raw_updates, Mapping):
        raise DeclarationSchemaError(
            f"event {event_name(event)!r} returned a non-mapping update"
        )

    updates: dict[int, int] = {}
    for register, value in raw_updates.items():
        if type(register) is not int or not 0 <= register < len(snapshot):
            raise DeclarationSchemaError(
                f"event {event_name(event)!r} returned invalid register "
                f"{register!r} for state size {len(snapshot)}"
            )
        if type(value) is not int:
            raise DeclarationSchemaError(
                f"event {event_name(event)!r} returned non-integer value "
                f"{value!r} for register {register}"
            )
        updates[register] = value

    actual_reads = tracked.actual_reads
    actual_writes = frozenset(updates)
    excess_reads = actual_reads - declared_reads
    if excess_reads:
        raise EffectDeclarationError(
            f"event {event_name(event)!r} actually read {sorted(excess_reads)} "
            f"outside declared reads {sorted(declared_reads)}"
        )
    excess_writes = actual_writes - declared_writes
    if excess_writes:
        raise EffectDeclarationError(
            f"event {event_name(event)!r} actually wrote {sorted(excess_writes)} "
            f"outside declared writes {sorted(declared_writes)}"
        )

    return GuardedEvaluation(updates, actual_reads, actual_writes)


def apply_updates(state: State, updates: Mapping[int, int]) -> State:
    next_state = list(state)
    for register, value in updates.items():
        next_state[register] = value
    return tuple(next_state)


def validate_supplied_waves(
    pet: ModuleType,
    register_count: int,
    waves: Sequence[Sequence[object]],
) -> None:
    """Preflight every supplied wave before evaluating any member."""

    for wave_index, wave in enumerate(waves):
        for event in wave:
            declared_effects(event, register_count)
        for left_index, left in enumerate(wave):
            for right in wave[left_index + 1 :]:
                if pet.conflicts(left, right):
                    raise WaveConflictError(
                        f"wave {wave_index} contains declared conflict between "
                        f"{event_name(left)!r} and {event_name(right)!r}"
                    )


def execute_guarded_waves(
    pet: ModuleType,
    initial: State,
    waves: Sequence[Sequence[object]],
) -> State:
    validate_supplied_waves(pet, len(initial), waves)
    state = initial

    for wave in waves:
        snapshot = state
        evaluations = [evaluate_guarded(event, snapshot) for event in wave]
        written: set[int] = set()
        for event, evaluation in zip(wave, evaluations, strict=True):
            overlap = written & evaluation.actual_writes
            if overlap:
                raise WaveConflictError(
                    f"wave produced overlapping actual writes {sorted(overlap)} "
                    f"while merging event {event_name(event)!r}"
                )
            written.update(evaluation.actual_writes)
            state = apply_updates(state, evaluation.updates)
    return state


def execute_guarded_serial(
    initial: State,
    ordered: Sequence[object],
) -> State:
    state = initial
    for event in ordered:
        evaluation = evaluate_guarded(event, state)
        state = apply_updates(state, evaluation.updates)
    return state


def total_order_identity(event: object) -> OrderIdentity:
    priority = getattr(event, "priority", None)
    arrival = getattr(event, "arrival", None)
    name = getattr(event, "name", None)
    if type(priority) is not int or type(arrival) is not int or type(name) is not str:
        raise DeclarationSchemaError(
            f"event {event_name(event)!r} requires integer priority/arrival and "
            "a string name for total ordering"
        )
    return (priority, arrival, name)


def validate_total_order_keys(pet: ModuleType, events: Sequence[object]) -> None:
    groups: dict[OrderIdentity, list[object]] = {}
    for event in events:
        groups.setdefault(total_order_identity(event), []).append(event)

    for key, group in groups.items():
        for left_index, left in enumerate(group):
            for right in group[left_index + 1 :]:
                if pet.conflicts(left, right):
                    raise AmbiguousOrderKeyError(
                        f"conflicting events {event_name(left)!r} and "
                        f"{event_name(right)!r} share total-order key {key!r}"
                    )


def guarded_reference_order(
    pet: ModuleType,
    events: Iterable[object],
) -> list[object]:
    materialized = list(events)
    validate_total_order_keys(pet, materialized)
    return pet.reference_order(materialized)


def schedule_and_execute_guarded(
    pet: ModuleType,
    initial: State,
    events: Iterable[object],
    *,
    fold_duplicates: bool,
) -> GuardedScheduleResult:
    materialized = list(events)
    folded = 0
    if fold_duplicates:
        materialized, folded, _ack = pet.fold_duplicate_deliveries(materialized)

    ordered = guarded_reference_order(pet, materialized)
    rebuilt_order, waves, hazard_edges = pet.build_parallel_waves(ordered)
    require(rebuilt_order == ordered, "builder changed the guarded reference order")
    serial = execute_guarded_serial(initial, ordered)
    wave = execute_guarded_waves(pet, initial, waves)
    return GuardedScheduleResult(
        tuple(ordered),
        tuple(tuple(wave_members) for wave_members in waves),
        serial,
        wave,
        folded,
        hazard_edges,
    )


def expect_guard_error(
    expected: type[GuardError],
    operation: Callable[[], object],
) -> str:
    try:
        operation()
    except expected as error:
        return f"{type(error).__name__}: {error}"
    except Exception as error:  # pragma: no cover - diagnostic path
        raise GuardInvariantError(
            f"expected {expected.__name__}, got {type(error).__name__}: {error}"
        ) from error
    raise GuardInvariantError(f"expected {expected.__name__}, but none was raised")


def tracked_state_self_check() -> dict[str, object]:
    tracked = TrackedState((10, 20, 30))
    observations = [tracked[1], tracked[-1], tracked[:1]]
    require(
        tracked.actual_reads == frozenset({0, 1, 2}),
        "TrackedState failed integer/slice read accounting",
    )
    iterated = TrackedState((40, 50))
    iterated_values = tuple(iterated)
    require(
        iterated.actual_reads == frozenset({0, 1}),
        "TrackedState failed Sequence iteration read accounting",
    )
    return {
        "observations": observations,
        "actual_reads": sorted(tracked.actual_reads),
        "iterated_values": iterated_values,
        "iteration_actual_reads": sorted(iterated.actual_reads),
    }


def documented_demo(pet: ModuleType) -> dict[str, object]:
    initial: State = (10, 0, 4, 9, 7, 2)
    events = [
        interrupt_event(
            pet,
            "high_mul3_r0",
            priority=100,
            arrival=0,
            delivery_id="high-001",
            op="mul",
            target=0,
            constant=3,
        ),
        interrupt_event(
            pet,
            "network_r2",
            priority=90,
            arrival=1,
            delivery_id="net-014",
            op="add",
            target=2,
            constant=7,
        ),
        interrupt_event(
            pet,
            "disk_r3",
            priority=80,
            arrival=2,
            delivery_id="disk-008",
            op="add",
            target=3,
            constant=5,
        ),
        interrupt_event(
            pet,
            "io_copy_r0_to_r1",
            priority=70,
            arrival=3,
            delivery_id="io-103",
            op="copy_add",
            target=1,
            source=0,
            constant=7,
        ),
        interrupt_event(
            pet,
            "timer_add5_r0",
            priority=60,
            arrival=4,
            delivery_id="timer-055",
            op="add",
            target=0,
            constant=5,
        ),
        interrupt_event(
            pet,
            "network_r2_retry",
            priority=90,
            arrival=5,
            delivery_id="net-014",
            op="add",
            target=2,
            constant=7,
        ),
    ]
    result = schedule_and_execute_guarded(
        pet,
        initial,
        events,
        fold_duplicates=True,
    )
    expected: State = (35, 37, 11, 14, 7, 2)
    expected_waves = [
        ["high_mul3_r0", "network_r2", "disk_r3"],
        ["io_copy_r0_to_r1"],
        ["timer_add5_r0"],
    ]
    wave_names = [[event_name(member) for member in wave] for wave in result.waves]
    require(result.serial == expected, "guarded documented serial result mismatch")
    require(result.wave == expected, "guarded documented wave result mismatch")
    require(result.folded == 1, "guarded documented duplicate count mismatch")
    require(wave_names == expected_waves, "guarded documented wave layout mismatch")
    return {
        "initial": initial,
        "reference_order": [event_name(member) for member in result.ordered],
        "waves": wave_names,
        "duplicates_folded": result.folded,
        "hazard_edges": result.hazard_edges,
        "guarded_serial": result.serial,
        "guarded_wave": result.wave,
    }


def rejection_demonstrations(pet: ModuleType) -> dict[str, object]:
    initial: State = (2, 0)
    declared_writer = ContractEvent(
        "writer_r0",
        10,
        0,
        frozenset(),
        frozenset({0}),
        lambda _snapshot: {0: 7},
    )
    hidden_reader = ContractEvent(
        "hidden_reader_to_r1",
        9,
        1,
        frozenset(),
        frozenset({1}),
        lambda snapshot: {1: snapshot[0]},
    )
    _, hidden_waves, _ = pet.build_parallel_waves(
        [declared_writer, hidden_reader]
    )
    hidden_read_error = expect_guard_error(
        EffectDeclarationError,
        lambda: execute_guarded_waves(pet, initial, hidden_waves),
    )

    undeclared_writer = ContractEvent(
        "undeclared_writer",
        1,
        0,
        frozenset(),
        frozenset({0}),
        lambda _snapshot: {1: 9},
    )
    undeclared_write_error = expect_guard_error(
        EffectDeclarationError,
        lambda: execute_guarded_waves(pet, initial, [[undeclared_writer]]),
    )

    raw_writer = interrupt_event(
        pet,
        "raw_writer",
        priority=2,
        arrival=0,
        op="add",
        target=0,
        constant=1,
    )
    raw_reader = interrupt_event(
        pet,
        "raw_reader",
        priority=1,
        arrival=1,
        op="copy_add",
        target=1,
        source=0,
        constant=0,
    )
    manual_raw_error = expect_guard_error(
        WaveConflictError,
        lambda: execute_guarded_waves(pet, initial, [[raw_writer, raw_reader]]),
    )
    raw_result = schedule_and_execute_guarded(
        pet,
        initial,
        [raw_writer, raw_reader],
        fold_duplicates=False,
    )
    require(raw_result.serial == raw_result.wave == (3, 3), "guarded RAW schedule mismatch")

    evaluation_counter = {"count": 0}

    def counted_evaluator(_snapshot: Sequence[int]) -> Mapping[int, int]:
        evaluation_counter["count"] += 1
        return {0: 4}

    first_wave_probe = ContractEvent(
        "first_wave_probe",
        3,
        0,
        frozenset(),
        frozenset({0}),
        counted_evaluator,
    )
    later_conflict_a = ContractEvent(
        "later_conflict_a",
        2,
        1,
        frozenset(),
        frozenset({1}),
        lambda _snapshot: {1: 5},
    )
    later_conflict_b = ContractEvent(
        "later_conflict_b",
        1,
        2,
        frozenset(),
        frozenset({1}),
        lambda _snapshot: {1: 6},
    )
    whole_plan_preflight_error = expect_guard_error(
        WaveConflictError,
        lambda: execute_guarded_waves(
            pet,
            initial,
            [[first_wave_probe], [later_conflict_a, later_conflict_b]],
        ),
    )
    require(
        evaluation_counter["count"] == 0,
        "an evaluator ran before the complete wave plan passed preflight",
    )

    tied_add = interrupt_event(
        pet,
        "same",
        priority=5,
        arrival=0,
        op="add",
        target=0,
        constant=1,
    )
    tied_mul = interrupt_event(
        pet,
        "same",
        priority=5,
        arrival=0,
        op="mul",
        target=0,
        constant=2,
    )
    unguarded_forward = pet.execute_serial(
        (2,), pet.reference_order([tied_add, tied_mul])
    )
    unguarded_reverse = pet.execute_serial(
        (2,), pet.reference_order([tied_mul, tied_add])
    )
    require(
        unguarded_forward != unguarded_reverse,
        "ambiguous order demonstration is not semantically discriminating",
    )
    ambiguous_key_error = expect_guard_error(
        AmbiguousOrderKeyError,
        lambda: guarded_reference_order(pet, [tied_add, tied_mul]),
    )

    independent_a = interrupt_event(
        pet,
        "same_independent_key",
        priority=4,
        arrival=3,
        op="set",
        target=0,
        constant=5,
    )
    independent_b = interrupt_event(
        pet,
        "same_independent_key",
        priority=4,
        arrival=3,
        op="set",
        target=1,
        constant=8,
    )
    independent_forward = schedule_and_execute_guarded(
        pet,
        initial,
        [independent_a, independent_b],
        fold_duplicates=False,
    )
    independent_reverse = schedule_and_execute_guarded(
        pet,
        initial,
        [independent_b, independent_a],
        fold_duplicates=False,
    )
    require(
        independent_forward.wave == independent_reverse.wave == (5, 8),
        "independent duplicate-key events did not commute",
    )

    return {
        "hidden_read": {
            "builder_waves": [
                [event_name(member) for member in wave] for wave in hidden_waves
            ],
            "rejected": hidden_read_error,
        },
        "undeclared_write": {"rejected": undeclared_write_error},
        "manually_supplied_raw_wave": {
            "rejected": manual_raw_error,
            "builder_waves": [
                [event_name(member) for member in wave] for wave in raw_result.waves
            ],
            "guarded_builder_result": raw_result.wave,
        },
        "whole_plan_preflight": {
            "rejected": whole_plan_preflight_error,
            "first_wave_evaluations_before_rejection": evaluation_counter["count"],
        },
        "conflicting_duplicate_total_order_key": {
            "unguarded_forward": unguarded_forward,
            "unguarded_reverse": unguarded_reverse,
            "rejected": ambiguous_key_error,
        },
        "independent_duplicate_total_order_key": {
            "allowed": True,
            "forward": independent_forward.wave,
            "reverse": independent_reverse.wave,
        },
    }


def instantiate_sequence(
    pet: ModuleType,
    templates: Sequence[EventTemplate],
    priorities: Sequence[int],
) -> list[object]:
    return [
        interrupt_event(
            pet,
            f"e{index}_{template.label}",
            priority=priority,
            arrival=index,
            op=template.op,
            target=template.target,
            source=template.source,
            constant=template.constant,
        )
        for index, (template, priority) in enumerate(
            zip(templates, priorities, strict=True)
        )
    ]


def bounded_guarded_corpus(
    pet: ModuleType,
    *,
    max_events: int,
) -> dict[str, object]:
    initial_states = list(itertools.product((-1, 0, 1), repeat=2))
    schedule_cases = 0
    state_executions = 0
    guarded_evaluations = 0
    hazard_edges = 0
    maximum_wave_width = 0

    for length in range(max_events + 1):
        for templates in itertools.product(TEMPLATES, repeat=length):
            for priorities in itertools.product((0, 1), repeat=length):
                events = instantiate_sequence(pet, templates, priorities)
                ordered = guarded_reference_order(pet, events)
                rebuilt_order, waves, edge_count = pet.build_parallel_waves(ordered)
                require(rebuilt_order == ordered, "bounded builder changed reference order")
                validate_supplied_waves(pet, 2, waves)
                hazard_edges += edge_count
                maximum_wave_width = max(
                    maximum_wave_width,
                    *(len(wave) for wave in waves),
                    0,
                )
                schedule_cases += 1

                for initial in initial_states:
                    subject_serial = pet.execute_serial(initial, ordered)
                    guarded_serial = execute_guarded_serial(initial, ordered)
                    guarded_wave = execute_guarded_waves(pet, initial, waves)
                    require(
                        subject_serial == guarded_serial == guarded_wave,
                        "bounded guarded equivalence mismatch: "
                        f"initial={initial}, events={[event_name(item) for item in events]}",
                    )
                    state_executions += 1
                    guarded_evaluations += 2 * len(ordered)

    return {
        "registers": 2,
        "event_templates": len(TEMPLATES),
        "max_events": max_events,
        "priority_domain": [0, 1],
        "initial_value_domain": [-1, 0, 1],
        "schedule_cases": schedule_cases,
        "state_executions": state_executions,
        "guarded_event_evaluations": guarded_evaluations,
        "hazard_edges": hazard_edges,
        "maximum_wave_width": maximum_wave_width,
        "subject_serial_guarded_serial_mismatches": 0,
        "guarded_serial_wave_mismatches": 0,
        "guard_rejections_for_faithful_builtins": 0,
    }


def run(args: argparse.Namespace) -> dict[str, object]:
    subject_path = args.pet.resolve()
    pet = load_pet(subject_path)
    return {
        "subject": {
            "path": str(subject_path),
            "sha256": sha256(subject_path),
            "python": platform.python_version(),
        },
        "configuration": {"max_events": args.max_events},
        "tracked_state": tracked_state_self_check(),
        "documented_demo": documented_demo(pet),
        "guard_rejections": rejection_demonstrations(pet),
        "bounded_guarded_corpus": bounded_guarded_corpus(
            pet,
            max_events=args.max_events,
        ),
        "verdict": {
            "verified": [
                "actual Sequence index reads are checked against declared reads",
                "returned update keys are checked against declared writes",
                "all supplied waves are pairwise preflighted before evaluation",
                "conflicting duplicate total-order keys are rejected",
                "the documented demo remains serial/wave equivalent",
                "the deterministic bounded built-in corpus remains equivalent",
            ],
            "scope": (
                "pure local register transitions; ordinary Sequence-mediated reads; "
                "no external effects"
            ),
        },
    }


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pet", type=Path, default=DEFAULT_PET)
    parser.add_argument("--max-events", type=int, default=3)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args(argv)
    if not 0 <= args.max_events <= 4:
        parser.error("--max-events must be in [0, 4]")
    return args


def main() -> None:
    args = parse_args()
    print(
        json.dumps(
            run(args),
            indent=None if args.compact else 2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
