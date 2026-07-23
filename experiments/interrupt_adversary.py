"""Deterministic contract probes for ``nonassoc_interrupt_pet.py``.

This is a benign, local mathematical-software experiment.  It treats the pet
module as read-only and exercises its pure register-transition scheduler.  The
probe deliberately distinguishes three things:

* invariants verified for the built-in, faithfully declared operations;
* caller preconditions demonstrated by small counterexamples; and
* input-domain assumptions that the implementation does not validate itself.

Only the Python standard library is required.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import platform
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Callable, Iterable, Sequence


DEFAULT_PET = Path(
    r"C:\Users\Efe\Documents\Codex\2026-07-17"
    r"\referenced-chatgpt-conversation-this-is-untrusted\outputs"
    r"\nonassoc_interrupt_pet.py"
)
DEFAULT_SEED = 20_260_717
State = tuple[int, ...]
Evaluator = Callable[[State], dict[int, int]]


class ProbeFailure(RuntimeError):
    """Raised when an expected scheduler contract does not hold."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ProbeFailure(message)


def load_pet(path: Path) -> ModuleType:
    """Load the read-only module from an explicit path without writing bytecode."""

    if not path.is_file():
        raise FileNotFoundError(path)

    sys.dont_write_bytecode = True
    module_name = "_nonassoc_interrupt_pet_under_test"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not create a module spec for {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(128 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


@dataclass(frozen=True, slots=True)
class ContractEvent:
    """Duck-typed event used to vary declared and actual effects independently."""

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

    def evaluate(self, snapshot: State) -> dict[int, int]:
        return self.evaluator(snapshot)


def expect_exception(
    expected: type[BaseException], operation: Callable[[], object]
) -> str:
    try:
        operation()
    except expected as error:
        return f"{type(error).__name__}: {error}"
    except Exception as error:  # pragma: no cover - diagnostic path
        raise ProbeFailure(
            f"expected {expected.__name__}, got {type(error).__name__}: {error}"
        ) from error
    raise ProbeFailure(f"expected {expected.__name__}, but no exception was raised")


def event(
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


def reproduce_baselines(
    pet: ModuleType, *, random_trials: int, seed: int, workers: int
) -> dict[str, object]:
    algebra = pet.verify_algebra()
    demo = pet.deterministic_demo(workers=0)
    threaded_demo = pet.deterministic_demo(workers=workers) if workers > 1 else demo
    randomized = pet.randomized_validation(
        trials=random_trials,
        seed=seed,
        workers=0,
    )

    require(demo["serial"] == demo["parallel"], "deterministic demo mismatch")
    require(
        threaded_demo["parallel"] == demo["serial"],
        "threaded deterministic demo mismatch",
    )
    require(
        randomized["serial_parallel_mismatches"] == 0,
        "randomized serial/wave mismatch",
    )

    return {
        "algebra": {
            "associator_hhh": algebra["associator_hhh"],
            "order_residual_hhq": algebra["order_residual_hhq"],
        },
        "deterministic": {
            "reference_order": demo["reference_order"],
            "waves": demo["waves"],
            "duplicates_folded": demo["duplicates_folded"],
            "serial": demo["serial"],
            "parallel": demo["parallel"],
            "blind_parallel": demo["blind_parallel"],
            "threaded_workers": workers if workers > 1 else 0,
            "threaded_parallel": threaded_demo["parallel"],
        },
        "randomized": randomized,
    }


def effect_subsets(register_count: int) -> list[frozenset[int]]:
    registers = range(register_count)
    return [
        frozenset(index for index in registers if mask & (1 << index))
        for mask in range(1 << register_count)
    ]


def conflict_truth_table(pet: ModuleType) -> dict[str, int]:
    """Exhaust all read/write-set profiles over two registers."""

    subsets = effect_subsets(2)
    profiles = list(itertools.product(subsets, repeat=2))
    checked = 0
    conflict_cases = 0

    for left_index, (left_reads, left_writes) in enumerate(profiles):
        left = ContractEvent(
            f"left_{left_index}",
            1,
            0,
            left_reads,
            left_writes,
            lambda _snapshot: {},
        )
        for right_index, (right_reads, right_writes) in enumerate(profiles):
            right = ContractEvent(
                f"right_{right_index}",
                0,
                1,
                right_reads,
                right_writes,
                lambda _snapshot: {},
            )
            expected = bool(
                (left_writes & right_reads)
                or (right_writes & left_reads)
                or (left_writes & right_writes)
            )
            observed = pet.conflicts(left, right)
            require(
                observed == expected,
                f"conflict predicate mismatch for profiles {left_index}, {right_index}",
            )
            require(
                (pet.hazard_tag(left, right) != pet.ZERO) == expected,
                f"hazard tag mismatch for profiles {left_index}, {right_index}",
            )
            checked += 1
            conflict_cases += int(expected)

    return {
        "effect_profiles": len(profiles),
        "ordered_profile_pairs_checked": checked,
        "conflict_pairs": conflict_cases,
        "mismatches": 0,
    }


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


def instantiate_sequence(
    pet: ModuleType,
    templates: Sequence[EventTemplate],
    priorities: Sequence[int],
) -> list[object]:
    return [
        event(
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


def check_wave_structure(
    pet: ModuleType,
    ordered: Sequence[object],
    waves: Sequence[Sequence[object]],
) -> tuple[int, int]:
    flattened = [member for wave in waves for member in wave]
    require(len(flattened) == len(ordered), "wave layering changed event cardinality")
    require(
        {id(member) for member in flattened} == {id(member) for member in ordered},
        "wave layering changed event membership",
    )
    positions = {
        id(member): wave_index
        for wave_index, wave in enumerate(waves)
        for member in wave
    }
    conflict_pairs = 0
    independent_pairs = 0

    for wave in waves:
        for left_index, left in enumerate(wave):
            for right in wave[left_index + 1 :]:
                require(not pet.conflicts(left, right), "one wave contains a conflict")

    for later in range(len(ordered)):
        earliest_legal_wave = 0
        for earlier in range(later):
            left = ordered[earlier]
            right = ordered[later]
            if pet.conflicts(left, right):
                require(
                    positions[id(left)] < positions[id(right)],
                    "conflicting reference-order pair was not wave-ordered",
                )
                earliest_legal_wave = max(
                    earliest_legal_wave,
                    positions[id(left)] + 1,
                )
                conflict_pairs += 1
            else:
                independent_pairs += 1
        require(
            positions[id(ordered[later])] == earliest_legal_wave,
            "event was not placed in its maximally early legal wave",
        )

    return conflict_pairs, independent_pairs


def bounded_exhaustive_equivalence(
    pet: ModuleType, *, max_events: int
) -> dict[str, object]:
    """Enumerate operation strings, priority bits, and small initial states."""

    initial_states = list(itertools.product((-1, 0, 1), repeat=2))
    schedule_cases = 0
    state_executions = 0
    conflict_pairs = 0
    independent_pairs = 0
    hazard_edges = 0
    widest_wave = 0

    for length in range(max_events + 1):
        for templates in itertools.product(TEMPLATES, repeat=length):
            for priorities in itertools.product((0, 1), repeat=length):
                events = instantiate_sequence(pet, templates, priorities)
                ordered, waves, edge_count = pet.build_parallel_waves(events)
                expected_order = sorted(
                    events,
                    key=lambda member: (
                        -member.priority,
                        member.arrival,
                        member.name,
                    ),
                )
                require(ordered == expected_order, "reference ordering mismatch")
                pair_counts = check_wave_structure(pet, ordered, waves)
                conflict_pairs += pair_counts[0]
                independent_pairs += pair_counts[1]
                hazard_edges += edge_count
                require(
                    edge_count == pair_counts[0],
                    "hazard edge count differs from conflicting pair count",
                )
                widest_wave = max(widest_wave, *(map(len, waves)), 0)
                schedule_cases += 1

                reversed_waves = [tuple(reversed(wave)) for wave in waves]
                for initial in initial_states:
                    serial = pet.execute_serial(initial, ordered)
                    parallel = pet.execute_waves(initial, waves, workers=0)
                    reversed_merge = pet.execute_waves(
                        initial, reversed_waves, workers=0
                    )
                    require(
                        parallel == serial,
                        "bounded serial/wave mismatch: "
                        f"initial={initial}, events={[item.name for item in events]}",
                    )
                    require(
                        reversed_merge == serial,
                        "valid same-wave merge depends on member order",
                    )
                    state_executions += 1

    return {
        "registers": 2,
        "event_templates": len(TEMPLATES),
        "max_events": max_events,
        "priority_domain": [0, 1],
        "initial_value_domain": [-1, 0, 1],
        "schedule_cases": schedule_cases,
        "state_executions": state_executions,
        "serial_wave_mismatches": 0,
        "reversed_valid_wave_merge_mismatches": 0,
        "maximally_early_level_mismatches": 0,
        "conflicting_reference_pairs": conflict_pairs,
        "independent_reference_pairs": independent_pairs,
        "hazard_edges": hazard_edges,
        "maximum_wave_width": widest_wave,
    }


def duplicate_token_contracts(pet: ModuleType) -> dict[str, object]:
    base = event(
        pet,
        "base",
        priority=7,
        arrival=0,
        delivery_id="token-A",
        op="add",
        target=0,
        constant=3,
    )
    retry_one = event(
        pet,
        "base_retry_one",
        priority=7,
        arrival=4,
        delivery_id="token-A",
        op="add",
        target=0,
        constant=3,
    )
    retry_two = event(
        pet,
        "base_retry_two",
        priority=7,
        arrival=9,
        delivery_id="token-A",
        op="add",
        target=0,
        constant=3,
    )
    kept, folded, acknowledgements = pet.fold_duplicate_deliveries(
        [retry_two, base, retry_one]
    )
    require(len(kept) == 1 and folded == 2, "exact retry folding mismatch")
    require(acknowledgements["token-A"] == pet.Q, "ACK state is not q")

    no_token_a = event(
        pet,
        "no_token_a",
        priority=1,
        arrival=0,
        op="set",
        target=0,
        constant=1,
    )
    no_token_b = event(
        pet,
        "no_token_b",
        priority=1,
        arrival=1,
        op="set",
        target=0,
        constant=1,
    )
    no_token_kept, no_token_folded, _ = pet.fold_duplicate_deliveries(
        [no_token_a, no_token_b]
    )
    require(
        len(no_token_kept) == 2 and no_token_folded == 0,
        "token-less deliveries were unexpectedly folded",
    )

    changed_effect = event(
        pet,
        "changed_effect",
        priority=7,
        arrival=1,
        delivery_id="token-A",
        op="add",
        target=0,
        constant=4,
    )
    changed_priority = event(
        pet,
        "changed_priority",
        priority=8,
        arrival=1,
        delivery_id="token-A",
        op="add",
        target=0,
        constant=3,
    )
    effect_collision = expect_exception(
        ValueError,
        lambda: pet.fold_duplicate_deliveries([base, changed_effect]),
    )
    priority_collision = expect_exception(
        ValueError,
        lambda: pet.fold_duplicate_deliveries([base, changed_priority]),
    )

    same_signature_new_name = event(
        pet,
        "distinct_name_but_same_signature",
        priority=7,
        arrival=99,
        delivery_id="token-A",
        op="add",
        target=0,
        constant=3,
    )
    indistinguishable_kept, indistinguishable_folded, _ = (
        pet.fold_duplicate_deliveries([base, same_signature_new_name])
    )
    require(
        len(indistinguishable_kept) == 1 and indistinguishable_folded == 1,
        "same-signature token reuse was not folded",
    )

    return {
        "three_exact_deliveries": {
            "kept": [member.name for member in kept],
            "folded": folded,
            "ack": acknowledgements["token-A"].as_tuple(),
        },
        "two_tokenless_deliveries": {
            "kept": len(no_token_kept),
            "folded": no_token_folded,
        },
        "same_token_changed_effect": effect_collision,
        "same_token_changed_priority": priority_collision,
        "same_token_same_signature_new_name": {
            "kept": len(indistinguishable_kept),
            "folded": indistinguishable_folded,
            "interpretation": (
                "name and arrival are not in the signature; token uniqueness is an "
                "external precondition"
            ),
        },
    }


def declaration_and_merge_contracts(pet: ModuleType) -> dict[str, object]:
    initial = (2, 0)
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
        frozenset(),  # intentionally incomplete
        frozenset({1}),
        lambda snapshot: {1: snapshot[0]},
    )
    hidden_ordered, hidden_waves, _ = pet.build_parallel_waves(
        [declared_writer, hidden_reader]
    )
    hidden_serial = pet.execute_serial(initial, hidden_ordered)
    hidden_parallel = pet.execute_waves(initial, hidden_waves)
    require(hidden_serial != hidden_parallel, "missing-read counterexample vanished")

    undeclared_writer = ContractEvent(
        "undeclared_writer",
        1,
        0,
        frozenset(),
        frozenset({0}),
        lambda _snapshot: {1: 9},
    )
    undeclared_write_error = expect_exception(
        AssertionError,
        lambda: pet.execute_waves(initial, [[undeclared_writer]]),
    )

    conservative_reader = ContractEvent(
        "conservative_set_r1",
        9,
        1,
        frozenset({0}),  # intentionally broader than the evaluator needs
        frozenset({1}),
        lambda _snapshot: {1: 11},
    )
    conservative_ordered, conservative_waves, _ = pet.build_parallel_waves(
        [declared_writer, conservative_reader]
    )
    conservative_serial = pet.execute_serial(initial, conservative_ordered)
    conservative_parallel = pet.execute_waves(initial, conservative_waves)
    require(
        conservative_serial == conservative_parallel,
        "conservative declaration changed the result",
    )
    require(len(conservative_waves) == 2, "over-declaration did not serialize")

    disjoint_a = event(
        pet,
        "disjoint_a",
        priority=2,
        arrival=0,
        op="set",
        target=0,
        constant=5,
    )
    disjoint_b = event(
        pet,
        "disjoint_b",
        priority=1,
        arrival=1,
        op="set",
        target=1,
        constant=8,
    )
    merge_forward = pet.execute_waves(initial, [[disjoint_a, disjoint_b]])
    merge_reverse = pet.execute_waves(initial, [[disjoint_b, disjoint_a]])
    require(merge_forward == merge_reverse, "disjoint merge order changed the result")

    overlap_a = event(
        pet,
        "overlap_a",
        priority=2,
        arrival=0,
        op="set",
        target=0,
        constant=5,
    )
    overlap_b = event(
        pet,
        "overlap_b",
        priority=1,
        arrival=1,
        op="set",
        target=0,
        constant=8,
    )
    overlapping_write_error = expect_exception(
        AssertionError,
        lambda: pet.execute_waves(initial, [[overlap_a, overlap_b]]),
    )

    raw_writer = event(
        pet,
        "raw_writer",
        priority=2,
        arrival=0,
        op="add",
        target=0,
        constant=1,
    )
    raw_reader = event(
        pet,
        "raw_reader",
        priority=1,
        arrival=1,
        op="copy_add",
        target=1,
        source=0,
        constant=0,
    )
    raw_ordered = pet.reference_order([raw_writer, raw_reader])
    raw_serial = pet.execute_serial(initial, raw_ordered)
    invalid_manual_wave = pet.execute_waves(initial, [raw_ordered])
    require(raw_serial != invalid_manual_wave, "invalid RAW wave unexpectedly matched")
    _, scheduled_raw_waves, _ = pet.build_parallel_waves(raw_ordered)
    scheduled_raw = pet.execute_waves(initial, scheduled_raw_waves)
    require(scheduled_raw == raw_serial, "builder failed to separate RAW dependency")

    return {
        "faithful_declarations": (
            "covered by bounded_exhaustive_equivalence; no mismatches"
        ),
        "missing_read_declaration": {
            "waves": [[member.name for member in wave] for wave in hidden_waves],
            "serial": hidden_serial,
            "wave": hidden_parallel,
            "interpretation": "read declarations are trusted, not dynamically checked",
        },
        "write_outside_declaration": undeclared_write_error,
        "conservative_read_declaration": {
            "waves": [
                [member.name for member in wave] for wave in conservative_waves
            ],
            "serial_equals_wave": conservative_serial == conservative_parallel,
            "interpretation": "sound but loses available parallelism",
        },
        "valid_disjoint_same_wave_merge": {
            "forward": merge_forward,
            "reverse": merge_reverse,
        },
        "overlapping_same_wave_writes": overlapping_write_error,
        "manually_supplied_raw_wave": {
            "serial": raw_serial,
            "manual_wave": invalid_manual_wave,
            "builder_waves": [
                [member.name for member in wave] for wave in scheduled_raw_waves
            ],
            "builder_result": scheduled_raw,
            "interpretation": (
                "execute_waves assumes conflict-free input; build_parallel_waves "
                "establishes that precondition"
            ),
        },
    }


def priority_contracts(pet: ModuleType) -> dict[str, object]:
    high = event(
        pet,
        "high_conflicting",
        priority=100,
        arrival=2,
        op="set",
        target=0,
        constant=10,
    )
    low = event(
        pet,
        "low_conflicting",
        priority=1,
        arrival=0,
        op="add",
        target=0,
        constant=1,
    )
    independent = event(
        pet,
        "lowest_independent",
        priority=0,
        arrival=0,
        op="set",
        target=1,
        constant=8,
    )
    ordered, waves, _ = pet.build_parallel_waves([low, independent, high])
    require(
        [member.name for member in ordered]
        == ["high_conflicting", "low_conflicting", "lowest_independent"],
        "priority order mismatch",
    )
    require(
        [[member.name for member in wave] for wave in waves]
        == [["high_conflicting", "lowest_independent"], ["low_conflicting"]],
        "priority/wave interaction mismatch",
    )

    arrival_late = event(
        pet,
        "z_arrival_late",
        priority=5,
        arrival=2,
        op="set",
        target=0,
        constant=0,
    )
    name_late = event(
        pet,
        "y_same_arrival",
        priority=5,
        arrival=1,
        op="set",
        target=0,
        constant=0,
    )
    name_early = event(
        pet,
        "a_same_arrival",
        priority=5,
        arrival=1,
        op="set",
        target=0,
        constant=0,
    )
    tied = pet.reference_order([arrival_late, name_late, name_early])
    require(
        [member.name for member in tied]
        == ["a_same_arrival", "y_same_arrival", "z_arrival_late"],
        "arrival/name tie-break mismatch",
    )

    exact_tie_add = event(
        pet,
        "same",
        priority=5,
        arrival=0,
        op="add",
        target=0,
        constant=1,
    )
    exact_tie_mul = event(
        pet,
        "same",
        priority=5,
        arrival=0,
        op="mul",
        target=0,
        constant=2,
    )
    forward_tie = pet.reference_order([exact_tie_add, exact_tie_mul])
    reverse_tie = pet.reference_order([exact_tie_mul, exact_tie_add])
    forward_result = pet.execute_serial((2,), forward_tie)
    reverse_result = pet.execute_serial((2,), reverse_tie)
    require(forward_result != reverse_result, "exact-key tie did not expose input order")

    return {
        "priority_order": [member.name for member in ordered],
        "priority_waves": [[member.name for member in wave] for wave in waves],
        "equal_priority_tie_break": [member.name for member in tied],
        "exact_key_tie": {
            "forward_ops": [member.op for member in forward_tie],
            "forward_result": forward_result,
            "reversed_ops": [member.op for member in reverse_tie],
            "reversed_result": reverse_result,
            "interpretation": (
                "when priority, arrival, and name all tie, Python's stable sort "
                "preserves caller input order"
            ),
        },
    }


def generator_domain_probe(pet: ModuleType) -> dict[str, object]:
    """Expose the random generator's implicit two-register minimum."""

    failure = expect_exception(
        ValueError,
        lambda: pet.random_event(
            random.Random(5),
            case_index=0,
            event_index=0,
            arrival=0,
            register_count=1,
        ),
    )
    return {
        "register_count": 1,
        "deterministic_seed": 5,
        "observed": failure,
        "interpretation": (
            "copy_add chooses a distinct source, so the random generator requires "
            "register_count >= 2 even though the function does not validate it"
        ),
    }


def run(args: argparse.Namespace) -> dict[str, object]:
    pet_path = args.pet.resolve()
    pet = load_pet(pet_path)
    return {
        "subject": {
            "path": str(pet_path),
            "sha256": sha256(pet_path),
            "python": platform.python_version(),
        },
        "configuration": {
            "seed": args.seed,
            "random_trials": args.random_trials,
            "thread_workers_for_demo": args.workers,
            "max_exhaustive_events": args.max_events,
        },
        "baseline_reproduction": reproduce_baselines(
            pet,
            random_trials=args.random_trials,
            seed=args.seed,
            workers=args.workers,
        ),
        "conflict_truth_table": conflict_truth_table(pet),
        "bounded_exhaustive_equivalence": bounded_exhaustive_equivalence(
            pet,
            max_events=args.max_events,
        ),
        "duplicate_token_contracts": duplicate_token_contracts(pet),
        "declaration_and_merge_contracts": declaration_and_merge_contracts(pet),
        "priority_contracts": priority_contracts(pet),
        "random_generator_domain": generator_domain_probe(pet),
        "verdict": {
            "verified": (
                "serial/wave equivalence held throughout the bounded built-in "
                "operation space under faithful declarations"
            ),
            "preconditions": [
                "read and write declarations faithfully cover actual effects",
                "execute_waves receives waves from build_parallel_waves or another "
                "conflict-free constructor",
                "delivery tokens uniquely identify a logical delivery",
                "priority/arrival/name keys are unique enough for the intended total order",
                "the random event generator receives at least two registers",
            ],
        },
    }


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pet", type=Path, default=DEFAULT_PET)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--random-trials", type=int, default=5_000)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--max-events", type=int, default=3)
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args(argv)
    if args.random_trials < 0:
        parser.error("--random-trials must be non-negative")
    if args.workers < 0:
        parser.error("--workers must be non-negative")
    if not 0 <= args.max_events <= 4:
        parser.error("--max-events must be in [0, 4]")
    return args


def main() -> None:
    args = parse_args()
    report = run(args)
    print(
        json.dumps(
            report,
            indent=None if args.compact else 2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
