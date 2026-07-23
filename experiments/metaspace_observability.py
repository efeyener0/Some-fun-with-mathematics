"""Moore observability of the 192-state combined chiral operator monoid.

States are the exact integer matrices from ``chiral_operator_monoids``.  The
alphabet is ``(Lh, Lq, Rh, Rq)`` and the transition convention is explicitly

    delta(state, letter) = state * generator(letter).

For several observation maps, this program computes exact Moore partitions,
shortest distinguishing continuation words, and refinement horizons.  It uses
only deterministic standard-library algorithms and exact integer arithmetic.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations, product
from typing import Any, Callable, Dict, Hashable, Iterable, List, Mapping, Optional, Sequence, Tuple

import chiral_operator_monoids as monoids


State = monoids.Matrix
Observation = Hashable
Word = Tuple[int, ...]

ALPHABET: Tuple[Tuple[str, State], ...] = (
    ("Lh", monoids.L_H),
    ("Lq", monoids.L_Q),
    ("Rh", monoids.R_H),
    ("Rq", monoids.R_Q),
)
ALPHABET_NAMES = tuple(name for name, _ in ALPHABET)
EXPECTED_COMBINED_DIGEST = "c7c110dce5fc69818255a07552b35c0b50f163aa624a63e06ade0eaa1db1c9fc"
EXPECTED_TRANSITION_DIGEST = "3430a8beae95ef66b1ab60d8597d24e8678227c60cba3fefd9b747a7d362fc53"

SIGNED_ROOT_LABELS = {
    (1, 0, 0): "+1",
    (-1, 0, 0): "-1",
    (0, 1, 0): "+h",
    (0, -1, 0): "-h",
    (0, 0, 1): "+q",
    (0, 0, -1): "-q",
}


def root_vector(state: State) -> Tuple[int, int, int]:
    """Return ``state * 1``, the first matrix column."""

    return (state[0], state[3], state[6])


def root_label(state: State) -> str:
    return SIGNED_ROOT_LABELS[root_vector(state)]


def observe_root(state: State) -> Observation:
    return root_label(state)


def observe_root_rank(state: State) -> Observation:
    return (root_label(state), monoids.matrix_rank(state))


def observe_root_rank_det(state: State) -> Observation:
    return (
        root_label(state),
        monoids.matrix_rank(state),
        monoids.determinant(state),
    )


def observe_full_matrix(state: State) -> Observation:
    return state


OBSERVATION_MAPS: Tuple[Tuple[str, Callable[[State], Observation]], ...] = (
    ("root_signed_basis", observe_root),
    ("root_plus_rank", observe_root_rank),
    ("root_plus_rank_plus_det", observe_root_rank_det),
    ("full_matrix_control", observe_full_matrix),
)


@dataclass(frozen=True)
class Automaton:
    states: Tuple[State, ...]
    state_index: Mapping[State, int]
    transitions: Tuple[Tuple[int, ...], ...]
    generation_depths: Mapping[State, int]


@dataclass(frozen=True)
class PartitionResult:
    block_ids: Tuple[int, ...]
    partitions_by_horizon: Tuple[Tuple[int, ...], ...]
    class_counts: Tuple[int, ...]
    class_size_profiles: Tuple[Mapping[int, int], ...]
    minimal_complete_horizon: Optional[int]
    stability_check_horizon: int


@dataclass(frozen=True)
class WitnessResult:
    witnesses: Mapping[Tuple[int, int], Word]
    newly_distinguished_by_depth: Mapping[int, int]
    shortest_word_profile: Mapping[str, int]
    maximum_shortest_depth: Optional[int]
    indistinguishable_pair_count: int
    canonical_examples: Mapping[str, Mapping[str, object]]


def build_automaton() -> Automaton:
    enumeration = monoids.enumerate_monoid(
        "combined_observability",
        tuple(generator for _, generator in ALPHABET),
        monoids.HARD_STATE_CAP,
        monoids.HARD_DEPTH_CAP,
    )
    assert enumeration.closed
    assert len(enumeration.states) == 192
    assert monoids.matrix_digest(enumeration.states) == EXPECTED_COMBINED_DIGEST

    states = tuple(sorted(enumeration.states))
    state_index = {state: index for index, state in enumerate(states)}
    transitions = tuple(
        tuple(
            state_index[monoids.matrix_multiply(state, generator)]
            for _, generator in ALPHABET
        )
        for state in states
    )
    assert all(len(row) == len(ALPHABET) for row in transitions)
    assert all(0 <= target < len(states) for row in transitions for target in row)

    # Independent reachability pass through the transition table.  Equality of
    # minimal depths verifies that the imported enumeration and this Moore
    # automaton use the same right-extension convention.
    identity_index = state_index[monoids.I3]
    discovered = {identity_index: 0}
    frontier = [identity_index]
    while frontier:
        next_frontier: List[int] = []
        for source in frontier:
            for target in transitions[source]:
                if target not in discovered:
                    discovered[target] = discovered[source] + 1
                    next_frontier.append(target)
        frontier = next_frontier
    assert len(discovered) == 192
    assert {
        states[index]: depth for index, depth in discovered.items()
    } == enumeration.depths

    # Identity transitions make the multiplication side unambiguous.
    for letter_index, (_, generator) in enumerate(ALPHABET):
        assert states[transitions[identity_index][letter_index]] == generator

    return Automaton(
        states=states,
        state_index=state_index,
        transitions=transitions,
        generation_depths=enumeration.depths,
    )


def canonical_blocks(signatures: Sequence[Hashable]) -> Tuple[int, ...]:
    signature_to_block: Dict[Hashable, int] = {}
    block_ids = []
    for signature in signatures:
        if signature not in signature_to_block:
            signature_to_block[signature] = len(signature_to_block)
        block_ids.append(signature_to_block[signature])
    return tuple(block_ids)


def block_size_profile(block_ids: Sequence[int]) -> Mapping[int, int]:
    sizes = Counter(block_ids)
    return dict(sorted(Counter(sizes.values()).items()))


def refine_moore_partition(
    automaton: Automaton,
    observation: Callable[[State], Observation],
) -> PartitionResult:
    outputs = tuple(observation(state) for state in automaton.states)
    blocks = canonical_blocks(outputs)
    partitions = [blocks]
    class_counts = [len(set(blocks))]
    size_profiles = [block_size_profile(blocks)]
    horizon = 0

    while True:
        signatures = tuple(
            (
                blocks[state_index],
                tuple(blocks[target] for target in automaton.transitions[state_index]),
            )
            for state_index in range(len(automaton.states))
        )
        refined = canonical_blocks(signatures)
        horizon += 1
        if refined == blocks:
            stability_check_horizon = horizon
            break
        blocks = refined
        partitions.append(blocks)
        class_counts.append(len(set(blocks)))
        size_profiles.append(block_size_profile(blocks))

    complete_horizon = next(
        (
            index
            for index, count in enumerate(class_counts)
            if count == len(automaton.states)
        ),
        None,
    )
    return PartitionResult(
        block_ids=blocks,
        partitions_by_horizon=tuple(partitions),
        class_counts=tuple(class_counts),
        class_size_profiles=tuple(size_profiles),
        minimal_complete_horizon=complete_horizon,
        stability_check_horizon=stability_check_horizon,
    )


def canonical_pair(left: int, right: int) -> Tuple[int, int]:
    if left == right:
        raise ValueError("a state cannot distinguish itself")
    return (left, right) if left < right else (right, left)


def apply_word(automaton: Automaton, state_index: int, word: Word) -> int:
    current = state_index
    for letter in word:
        current = automaton.transitions[current][letter]
    return current


def word_label(word: Word) -> str:
    return "epsilon" if not word else " ".join(ALPHABET_NAMES[index] for index in word)


def json_value(value: Any) -> Any:
    if isinstance(value, tuple):
        return [json_value(item) for item in value]
    return value


def witness_example(
    automaton: Automaton,
    outputs: Sequence[Observation],
    pair: Tuple[int, int],
    word: Word,
) -> Mapping[str, object]:
    left, right = pair
    left_after = apply_word(automaton, left, word)
    right_after = apply_word(automaton, right, word)
    return {
        "state_a": "M{:03d}".format(left),
        "state_b": "M{:03d}".format(right),
        "matrix_a": monoids.matrix_rows(automaton.states[left]),
        "matrix_b": monoids.matrix_rows(automaton.states[right]),
        "suffix": list(ALPHABET_NAMES[index] for index in word),
        "depth": len(word),
        "observation_before": [json_value(outputs[left]), json_value(outputs[right])],
        "observation_after": [
            json_value(outputs[left_after]),
            json_value(outputs[right_after]),
        ],
    }


def shortest_distinguishing_suffixes(
    automaton: Automaton,
    observation: Callable[[State], Observation],
    final_blocks: Sequence[int],
) -> WitnessResult:
    outputs = tuple(observation(state) for state in automaton.states)
    all_pairs = tuple(combinations(range(len(automaton.states)), 2))
    witnesses: Dict[Tuple[int, int], Word] = {
        pair: () for pair in all_pairs if outputs[pair[0]] != outputs[pair[1]]
    }

    while True:
        previous = dict(witnesses)
        additions: Dict[Tuple[int, int], Word] = {}
        for pair in all_pairs:
            if pair in previous:
                continue
            left, right = pair
            candidates: List[Word] = []
            for letter in range(len(ALPHABET)):
                next_left = automaton.transitions[left][letter]
                next_right = automaton.transitions[right][letter]
                if next_left == next_right:
                    continue
                next_pair = canonical_pair(next_left, next_right)
                if next_pair in previous:
                    candidates.append((letter,) + previous[next_pair])
            if candidates:
                additions[pair] = min(candidates, key=lambda word: (len(word), word))
        if not additions:
            break
        witnesses.update(additions)

    indistinguishable = [pair for pair in all_pairs if pair not in witnesses]
    expected_indistinguishable = sum(
        size * (size - 1) // 2 for size in Counter(final_blocks).values()
    )
    assert len(indistinguishable) == expected_indistinguishable
    assert all(final_blocks[left] == final_blocks[right] for left, right in indistinguishable)
    assert all(
        outputs[apply_word(automaton, pair[0], word)]
        != outputs[apply_word(automaton, pair[1], word)]
        for pair, word in witnesses.items()
    )

    depth_profile = dict(sorted(Counter(len(word) for word in witnesses.values()).items()))
    word_profile = dict(
        sorted(Counter(word_label(word) for word in witnesses.values()).items())
    )
    examples: Dict[str, Mapping[str, object]] = {}
    for pair in all_pairs:
        if pair not in witnesses:
            continue
        label = word_label(witnesses[pair])
        if label not in examples:
            examples[label] = witness_example(
                automaton, outputs, pair, witnesses[pair]
            )

    return WitnessResult(
        witnesses=witnesses,
        newly_distinguished_by_depth=depth_profile,
        shortest_word_profile=word_profile,
        maximum_shortest_depth=max(depth_profile) if depth_profile else None,
        indistinguishable_pair_count=len(indistinguishable),
        canonical_examples=examples,
    )


EXPECTED = {
    "root_signed_basis": {
        "class_counts": (6, 192),
        "class_size_profiles": ({32: 6}, {1: 192}),
        "depth_profile": {0: 15360, 1: 2976},
        "word_profile": {"Lh": 2544, "Lq": 432, "epsilon": 15360},
        "max_depth": 1,
    },
    "root_plus_rank": {
        "class_counts": (18, 192),
        "class_size_profiles": ({4: 12, 24: 6}, {1: 192}),
        "depth_profile": {0: 16608, 1: 1728},
        "word_profile": {"Lh": 1488, "Lq": 240, "epsilon": 16608},
        "max_depth": 1,
    },
    "root_plus_rank_plus_det": {
        "class_counts": (24, 192),
        "class_size_profiles": ({2: 12, 4: 6, 24: 6}, {1: 192}),
        "depth_profile": {0: 16632, 1: 1704},
        "word_profile": {"Lh": 1476, "Lq": 228, "epsilon": 16632},
        "max_depth": 1,
    },
    "full_matrix_control": {
        "class_counts": (192,),
        "class_size_profiles": ({1: 192},),
        "depth_profile": {0: 18336},
        "word_profile": {"epsilon": 18336},
        "max_depth": 0,
    },
}


def verify_root_tomography(automaton: Automaton) -> Mapping[str, object]:
    root_counts = Counter(root_label(state) for state in automaton.states)
    assert root_counts == Counter({label: 32 for label in SIGNED_ROOT_LABELS.values()})

    for state_index, state in enumerate(automaton.states):
        root_now = root_vector(state)
        root_after_lh = root_vector(
            automaton.states[automaton.transitions[state_index][0]]
        )
        root_after_lq = root_vector(
            automaton.states[automaton.transitions[state_index][1]]
        )
        root_after_rh = root_vector(
            automaton.states[automaton.transitions[state_index][2]]
        )
        root_after_rq = root_vector(
            automaton.states[automaton.transitions[state_index][3]]
        )
        assert root_now == (state[0], state[3], state[6])
        assert root_after_lh == root_after_rh == (state[1], state[4], state[7])
        assert root_after_lq == root_after_rq == (state[2], state[5], state[8])
        reconstructed = (
            root_now[0],
            root_after_lh[0],
            root_after_lq[0],
            root_now[1],
            root_after_lh[1],
            root_after_lq[1],
            root_now[2],
            root_after_lh[2],
            root_after_lq[2],
        )
        assert reconstructed == state

    signatures = {
        (
            root_vector(state),
            root_vector(automaton.states[automaton.transitions[index][0]]),
            root_vector(automaton.states[automaton.transitions[index][1]]),
        )
        for index, state in enumerate(automaton.states)
    }
    assert len(signatures) == 192
    return {
        "root_value_profile": dict(sorted(root_counts.items())),
        "root_values_are_signed_basis": True,
        "root_now_reads_column": 1,
        "root_after_Lh_or_Rh_reads_column": 2,
        "root_after_Lq_or_Rq_reads_column": 3,
        "three_column_signature_count": len(signatures),
        "Lh_Rh_are_duplicate_one_step_root_probes": True,
        "Lq_Rq_are_duplicate_one_step_root_probes": True,
        "two_letter_probe_set_suffices": ["Lh", "Lq"],
    }


def words_through_horizon(horizon: int) -> List[Word]:
    words: List[Word] = []
    for length in range(horizon + 1):
        words.extend(tuple(word) for word in product(range(len(ALPHABET)), repeat=length))
    return words


def transition_digest(automaton: Automaton) -> str:
    payload = ";".join(
        ",".join(str(target) for target in row) for row in automaton.transitions
    ).encode("ascii")
    return sha256(payload).hexdigest()


def run_deep_checks(
    automaton: Automaton,
    analyses: Mapping[str, Mapping[str, object]],
) -> Mapping[str, object]:
    trace_profiles: Dict[str, List[int]] = {}
    witness_pairs_checked = 0
    shorter_words_checked = 0

    for name, observation in OBSERVATION_MAPS:
        result = analyses[name]
        partition = result["_partition"]
        witnesses = result["_witnesses"]
        assert isinstance(partition, PartitionResult)
        assert isinstance(witnesses, WitnessResult)
        outputs = tuple(observation(state) for state in automaton.states)

        trace_counts = []
        for horizon in range(partition.stability_check_horizon + 1):
            words = words_through_horizon(horizon)
            traces = {
                tuple(outputs[apply_word(automaton, state_index, word)] for word in words)
                for state_index in range(len(automaton.states))
            }
            trace_counts.append(len(traces))
        expected_trace_counts = list(partition.class_counts)
        expected_trace_counts.append(partition.class_counts[-1])
        assert trace_counts == expected_trace_counts
        trace_profiles[name] = trace_counts

        maximum_depth = witnesses.maximum_shortest_depth or 0
        shorter_words = {
            length: list(product(range(len(ALPHABET)), repeat=length))
            for length in range(maximum_depth)
        }
        for pair, word in witnesses.witnesses.items():
            witness_pairs_checked += 1
            assert outputs[apply_word(automaton, pair[0], word)] != outputs[
                apply_word(automaton, pair[1], word)
            ]
            for length in range(len(word)):
                for shorter in shorter_words[length]:
                    shorter_words_checked += 1
                    assert outputs[apply_word(automaton, pair[0], tuple(shorter))] == outputs[
                        apply_word(automaton, pair[1], tuple(shorter))
                    ]

        for left, right in combinations(range(len(automaton.states)), 2):
            pair = (left, right)
            equivalent = partition.block_ids[left] == partition.block_ids[right]
            assert equivalent == (pair not in witnesses.witnesses)

    digest = transition_digest(automaton)
    assert digest == EXPECTED_TRANSITION_DIGEST
    return {
        "performed": True,
        "independent_trace_class_counts": trace_profiles,
        "shortest_witness_pairs_rechecked": witness_pairs_checked,
        "strictly_shorter_words_rechecked": shorter_words_checked,
        "transition_table_sha256": digest,
        "generation_depths_match_imported_right_BFS": True,
        "pair_equivalence_matches_final_partitions": True,
    }


def public_analysis(
    partition: PartitionResult,
    witnesses: WitnessResult,
) -> Dict[str, object]:
    return {
        "immediate_observation_classes": partition.class_counts[0],
        "minimal_moore_quotient_states": partition.class_counts[-1],
        "horizon_class_counts": list(partition.class_counts),
        "horizon_new_class_counts": [
            partition.class_counts[0]
        ]
        + [
            partition.class_counts[index] - partition.class_counts[index - 1]
            for index in range(1, len(partition.class_counts))
        ],
        "class_size_profiles_by_horizon": [
            dict(profile) for profile in partition.class_size_profiles
        ],
        "minimal_complete_horizon": partition.minimal_complete_horizon,
        "stability_check_horizon": partition.stability_check_horizon,
        "distinguishable_pair_count": len(witnesses.witnesses),
        "indistinguishable_pair_count": witnesses.indistinguishable_pair_count,
        "newly_distinguished_pairs_by_depth": dict(
            witnesses.newly_distinguished_by_depth
        ),
        "shortest_distinguishing_suffix_profile": dict(
            witnesses.shortest_word_profile
        ),
        "maximum_shortest_distinguishing_depth": witnesses.maximum_shortest_depth,
        "canonical_shortest_suffix_examples": dict(witnesses.canonical_examples),
    }


def build_report(deep_check: bool) -> Dict[str, object]:
    automaton = build_automaton()
    tomography = verify_root_tomography(automaton)
    internal_analyses: Dict[str, Dict[str, object]] = {}
    public_analyses: Dict[str, Dict[str, object]] = {}

    for name, observation in OBSERVATION_MAPS:
        partition = refine_moore_partition(automaton, observation)
        witnesses = shortest_distinguishing_suffixes(
            automaton, observation, partition.block_ids
        )
        expected = EXPECTED[name]
        assert partition.class_counts == expected["class_counts"]
        assert partition.class_size_profiles == expected["class_size_profiles"]
        assert dict(witnesses.newly_distinguished_by_depth) == expected["depth_profile"]
        assert dict(witnesses.shortest_word_profile) == expected["word_profile"]
        assert witnesses.maximum_shortest_depth == expected["max_depth"]
        assert partition.class_counts[-1] == 192
        assert witnesses.indistinguishable_pair_count == 0

        internal_analyses[name] = {
            "_partition": partition,
            "_witnesses": witnesses,
        }
        public_analyses[name] = public_analysis(partition, witnesses)

    deep_report: Mapping[str, object]
    if deep_check:
        deep_report = run_deep_checks(automaton, internal_analyses)
    else:
        deep_report = {
            "performed": False,
            "available_via": "--deep-check",
        }

    return {
        "automaton": {
            "state_count": len(automaton.states),
            "alphabet": list(ALPHABET_NAMES),
            "transition_convention": "delta(M, x) = M * generator(x)",
            "transition_side": "right multiplication / append generator to the word",
            "identity_reaches_every_state": True,
            "maximum_generation_depth": max(automaton.generation_depths.values()),
            "combined_state_set_sha256": monoids.matrix_digest(automaton.states),
            "unordered_state_pair_count": len(automaton.states) * (len(automaton.states) - 1) // 2,
        },
        "root_tomography": tomography,
        "observation_quotients": public_analyses,
        "deep_check": deep_report,
        "verified_expected_profiles": True,
        "epistemic_bounds": {
            "scope": "The literal 192-state combined matrix monoid and the four stated Moore outputs only.",
            "suffix_meaning": "A continuation word appended through repeated right multiplication.",
            "minimality": "Exact finite Moore/Myhill-Nerode equivalence, not a statistical estimate.",
            "root_assumption": "The first column is observed exactly as one of six signed basis vectors.",
            "physical_limit": "No claim is made about noisy, partial, costly, or physically realizable measurement.",
            "control_limit": "Full-matrix control is an identity observation and is included only as a reference ceiling.",
        },
    }


def print_human(report: Mapping[str, object]) -> None:
    automaton = report["automaton"]
    analyses = report["observation_quotients"]
    assert isinstance(automaton, dict)
    assert isinstance(analyses, dict)
    print("Metaspace observability: exact Moore analysis")
    print("States:", automaton["state_count"])
    print("Alphabet:", automaton["alphabet"])
    print("Transition:", automaton["transition_convention"])
    for name, analysis in analyses.items():
        assert isinstance(analysis, dict)
        print(
            "{}: classes {}, quotient {}, horizon {}, max shortest depth {}".format(
                name,
                analysis["horizon_class_counts"],
                analysis["minimal_moore_quotient_states"],
                analysis["minimal_complete_horizon"],
                analysis["maximum_shortest_distinguishing_depth"],
            )
        )
        print("  suffix profile:", analysis["shortest_distinguishing_suffix_profile"])
    tomography = report["root_tomography"]
    assert isinstance(tomography, dict)
    print("Root tomography signatures:", tomography["three_column_signature_count"])
    deep = report["deep_check"]
    assert isinstance(deep, dict)
    print("Deep check performed:", deep["performed"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the full JSON certificate")
    parser.add_argument(
        "--deep-check",
        action="store_true",
        help="independently enumerate trace signatures and recheck pair-witness minimality",
    )
    args = parser.parse_args()
    report = build_report(args.deep_check)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)


if __name__ == "__main__":
    main()
