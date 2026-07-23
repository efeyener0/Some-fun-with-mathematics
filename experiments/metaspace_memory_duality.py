"""Exact tomography/erasure duality in the 192-state signed metaspace.

Three root experiments read the three signed columns of a state.  Dually,
three rank-one suffixes retain exactly one of those columns and erase the
others.  This probe derives both views from the certified signed-code model
and checks their relation on every unordered state pair.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from itertools import combinations
from typing import Dict, FrozenSet, Iterable, List, Mapping, Sequence, Set, Tuple

import certified_signed_metaspace as signed


Pair = Tuple[int, int]
Word = Tuple[str, ...]

COLUMN_NAMES = ("1", "h", "q")
ROOT_PROBE_WORDS: Tuple[Word, ...] = ((), ("Lh",), ("Lq",))
EXPECTED_STATE_COUNT = 192
EXPECTED_PAIR_COUNT = 18_336
EXPECTED_SINGLE_COLUMN_KERNEL_SIZE = 2_976
EXPECTED_TWO_COLUMN_INTERSECTION_SIZE = 432
EXPECTED_SYNCHRONIZABLE_PAIR_COUNT = 7_632
EXPECTED_NONSYNCHRONIZABLE_PAIR_COUNT = 10_704


def pair_key(left: int, right: int) -> Pair:
    return (left, right) if left < right else (right, left)


def all_pairs(count: int) -> Iterable[Pair]:
    return combinations(range(count), 2)


def apply_word(code: signed.SignedCode, word: Sequence[str]) -> signed.SignedCode:
    symbol_to_code = dict(zip(signed.SYMBOLS, map(signed.encode_matrix, signed.GENERATOR_MATRICES)))
    result = code
    for symbol in word:
        result = signed.compose_codes(result, symbol_to_code[symbol])
    return result


def root_after(code: signed.SignedCode, word: Sequence[str]) -> int:
    return apply_word(code, word)[0]


def column_kernel(
    states: Sequence[signed.SignedCode], column: int
) -> FrozenSet[Pair]:
    return frozenset(
        (left, right)
        for left, right in all_pairs(len(states))
        if states[left][column] == states[right][column]
    )


def transformation_kernel(
    states: Sequence[signed.SignedCode], suffix: signed.SignedCode
) -> FrozenSet[Pair]:
    products = [signed.compose_codes(state, suffix) for state in states]
    return frozenset(
        (left, right)
        for left, right in all_pairs(len(states))
        if products[left] == products[right]
    )


def word_sort_key(word: Sequence[str]) -> Tuple[int, Tuple[int, ...]]:
    symbol_index = {symbol: index for index, symbol in enumerate(signed.SYMBOLS)}
    return len(word), tuple(symbol_index[symbol] for symbol in word)


def shortest_rank_one_erasers(
    automaton: signed.CompiledAutomaton,
) -> Tuple[int, int, int]:
    chosen: List[int] = []
    for axis in (1, 2, 3):
        candidates = [
            state_id
            for state_id, code in enumerate(automaton.states)
            if signed.code_rank(code) == 1
            and {abs(value) for value in code} == {axis}
        ]
        chosen.append(
            min(
                candidates,
                key=lambda state_id: word_sort_key(
                    automaton.canonical_words[state_id]
                ),
            )
        )
    return tuple(chosen)  # type: ignore[return-value]


def analyze_tomography(
    automaton: signed.CompiledAutomaton,
    column_kernels: Sequence[FrozenSet[Pair]],
) -> Dict[str, object]:
    signatures = [
        tuple(root_after(state, word) for word in ROOT_PROBE_WORDS)
        for state in automaton.states
    ]
    if signatures != list(automaton.states):
        raise AssertionError("root-probe signature is not the signed state code")
    if len(set(signatures)) != EXPECTED_STATE_COUNT:
        raise AssertionError("root tomography did not separate all states")

    probe_kernels: List[FrozenSet[Pair]] = []
    for word in ROOT_PROBE_WORDS:
        outputs = [root_after(state, word) for state in automaton.states]
        kernel = frozenset(
            pair
            for pair in all_pairs(len(automaton.states))
            if outputs[pair[0]] == outputs[pair[1]]
        )
        probe_kernels.append(kernel)
    if tuple(probe_kernels) != tuple(column_kernels):
        raise AssertionError("root-probe kernels differ from column kernels")

    return {
        "probe_words": [list(word) for word in ROOT_PROBE_WORDS],
        "probe_labels": ["epsilon", "Lh", "Lq"],
        "columns_read": list(COLUMN_NAMES),
        "signature_formula": "(root(M), root(M*Lh), root(M*Lq)) = signed_code(M)",
        "distinct_signatures": len(set(signatures)),
        "complete_state_tomography": True,
        "intersection_of_probe_kernels_on_distinct_pairs": len(
            set.intersection(*(set(kernel) for kernel in probe_kernels))
        ),
    }


def analyze_pair_lattice(
    states: Sequence[signed.SignedCode],
    kernels: Sequence[FrozenSet[Pair]],
) -> Dict[str, object]:
    kernel_sizes = [len(kernel) for kernel in kernels]
    if kernel_sizes != [EXPECTED_SINGLE_COLUMN_KERNEL_SIZE] * 3:
        raise AssertionError("single-column kernel profile changed")

    pairwise_intersections = {
        "{}&{}".format(COLUMN_NAMES[left], COLUMN_NAMES[right]): len(
            kernels[left] & kernels[right]
        )
        for left, right in combinations(range(3), 2)
    }
    if set(pairwise_intersections.values()) != {
        EXPECTED_TWO_COLUMN_INTERSECTION_SIZE
    }:
        raise AssertionError("two-column intersection profile changed")

    triple = kernels[0] & kernels[1] & kernels[2]
    union = kernels[0] | kernels[1] | kernels[2]
    if triple:
        raise AssertionError("distinct states unexpectedly share all three columns")
    if len(union) != EXPECTED_SYNCHRONIZABLE_PAIR_COUNT:
        raise AssertionError("column-kernel union profile changed")

    exact_subsets: Counter[Tuple[int, ...]] = Counter()
    for pair in all_pairs(len(states)):
        equal = tuple(
            column for column, kernel in enumerate(kernels) if pair in kernel
        )
        exact_subsets[equal] += 1

    subset_labels = {
        subset: "{" + ",".join(COLUMN_NAMES[column] for column in subset) + "}"
        if subset
        else "{}"
        for subset in exact_subsets
    }
    exact_profile = {
        subset_labels[subset]: count
        for subset, count in sorted(exact_subsets.items())
    }
    expected_profile = {
        "{}": 10_704,
        "{1}": 2_112,
        "{h}": 2_112,
        "{q}": 2_112,
        "{1,h}": 432,
        "{1,q}": 432,
        "{h,q}": 432,
    }
    if exact_profile != expected_profile:
        raise AssertionError("exact equal-column subset profile changed")

    inclusion_exclusion = (
        sum(kernel_sizes)
        - sum(pairwise_intersections.values())
        + len(triple)
    )
    if inclusion_exclusion != len(union):
        raise AssertionError("column-kernel inclusion-exclusion failed")

    return {
        "unordered_state_pairs": EXPECTED_PAIR_COUNT,
        "single_column_kernel_sizes": dict(zip(COLUMN_NAMES, kernel_sizes)),
        "two_column_intersection_sizes": pairwise_intersections,
        "three_column_intersection_size_on_distinct_pairs": len(triple),
        "union_size": len(union),
        "union_inclusion_exclusion": inclusion_exclusion,
        "complement_size": EXPECTED_PAIR_COUNT - len(union),
        "exact_equal_column_subset_profile": exact_profile,
        "interpretation": (
            "intersection = indistinguishable under every coordinate probe; "
            "union = mergeable by at least one coordinate eraser"
        ),
    }


def analyze_erasers(
    automaton: signed.CompiledAutomaton,
    column_kernels: Sequence[FrozenSet[Pair]],
) -> Dict[str, object]:
    state_ids = shortest_rank_one_erasers(automaton)
    reports: List[Dict[str, object]] = []
    total_pair_checks = 0
    for column, state_id in enumerate(state_ids):
        eraser = automaton.states[state_id]
        image = [signed.compose_codes(state, eraser) for state in automaton.states]
        fiber_profile = Counter(Counter(image).values())
        eraser_kernel = transformation_kernel(automaton.states, eraser)
        if eraser_kernel != column_kernels[column]:
            raise AssertionError("rank-one eraser kernel differs from column equality")
        if len(set(image)) != 6 or fiber_profile != Counter({32: 6}):
            raise AssertionError("rank-one eraser did not produce six uniform fibers")
        total_pair_checks += EXPECTED_PAIR_COUNT
        reports.append(
            {
                "retained_column": COLUMN_NAMES[column],
                "state_id": state_id,
                "signed_code": list(eraser),
                "shortest_word": list(automaton.canonical_words[state_id]),
                "shortest_depth": len(automaton.canonical_words[state_id]),
                "image_size": len(set(image)),
                "fiber_size_multiplicity": {
                    str(size): count for size, count in sorted(fiber_profile.items())
                },
                "kernel_equals_column_equality": True,
            }
        )
    return {
        "erasers": reports,
        "pair_kernel_checks": total_pair_checks,
        "minimum_retained_state_count": 6,
        "reset_word_exists": False,
        "reason": (
            "rank one is the minimum available matrix rank; its six signed outputs "
            "form a nonzero memory floor"
        ),
    }


def fiber_signature(values: Sequence[signed.SignedCode]) -> Dict[int, int]:
    return dict(sorted(Counter(Counter(values).values()).items()))


def analyze_left_right_information(
    states: Sequence[signed.SignedCode],
) -> Dict[str, object]:
    left_sizes: Dict[int, Set[int]] = {1: set(), 2: set(), 3: set()}
    right_sizes: Dict[int, Set[int]] = {1: set(), 2: set(), 3: set()}
    left_fibers: Dict[int, Set[Tuple[Tuple[int, int], ...]]] = {
        1: set(),
        2: set(),
        3: set(),
    }
    kernel_subset_profile: Counter[Tuple[int, ...]] = Counter()
    product_checks = 0
    for suffix in states:
        rank = signed.code_rank(suffix)
        left_products = [signed.compose_codes(state, suffix) for state in states]
        right_products = [signed.compose_codes(suffix, state) for state in states]
        retained_columns = tuple(sorted({abs(value) - 1 for value in suffix}))
        kernel_subset_profile[retained_columns] += 1
        projection_to_product: Dict[Tuple[int, ...], signed.SignedCode] = {}
        product_to_projection: Dict[signed.SignedCode, Tuple[int, ...]] = {}
        for state, result in zip(states, left_products):
            projection = tuple(state[column] for column in retained_columns)
            prior_result = projection_to_product.setdefault(projection, result)
            prior_projection = product_to_projection.setdefault(result, projection)
            if prior_result != result or prior_projection != projection:
                raise AssertionError("suffix kernel is not its retained-column kernel")
        left_sizes[rank].add(len(set(left_products)))
        right_sizes[rank].add(len(set(right_products)))
        left_fibers[rank].add(tuple(fiber_signature(left_products).items()))
        product_checks += 2 * len(states)

    expected_left = {1: {6}, 2: {36}, 3: {192}}
    expected_right = {1: {8}, 2: {64}, 3: {192}}
    if left_sizes != expected_left or right_sizes != expected_right:
        raise AssertionError("left/right information-size profile changed")

    expected_fibers = {
        1: {((32, 6),)},
        2: {((4, 12), (6, 24))},
        3: {((1, 192),)},
    }
    if left_fibers != expected_fibers:
        raise AssertionError("right-action fiber profile changed")

    expected_kernel_subsets = {
        (0,): 8,
        (1,): 8,
        (2,): 8,
        (0, 1): 48,
        (0, 2): 48,
        (1, 2): 48,
        (0, 1, 2): 24,
    }
    if dict(kernel_subset_profile) != expected_kernel_subsets:
        raise AssertionError("suffix-kernel Boolean lattice profile changed")

    return {
        "products_checked": product_checks,
        "by_matrix_rank": [
            {
                "rank": rank,
                "M_times_p_size": next(iter(left_sizes[rank])),
                "p_times_M_size": next(iter(right_sizes[rank])),
                "M_times_p_fiber_profile": {
                    str(size): count
                    for size, count in next(iter(left_fibers[rank]))
                },
                "singular_formula_M_times_p": (
                    "6^rank" if rank < 3 else "unit right translation of M"
                ),
                "singular_formula_p_times_M": (
                    "(2*rank)^3" if rank < 3 else "unit left translation of M"
                ),
            }
            for rank in (1, 2, 3)
        ],
        "rank_two_parity_scar": {
            "possible_retained_column_pairs": 36,
            "fiber_4_count": 12,
            "fiber_6_count": 24,
            "explanation": (
                "four singular third-column extensions always survive; the two unit "
                "extensions survive exactly when their absolute permutation is even"
            ),
        },
        "suffix_kernel_lattice": {
            "distinct_nonempty_column_subsets": len(kernel_subset_profile),
            "suffix_count_by_retained_columns": {
                "{" + ",".join(COLUMN_NAMES[column] for column in subset) + "}": count
                for subset, count in sorted(kernel_subset_profile.items())
            },
            "formula": "kernel(R_p) = intersection of K_i over i in image(abs(p))",
            "universal_empty_subset_kernel_present": False,
            "reset_absence_explanation": "rank zero / the empty retained-column subset is absent",
        },
    }


def cross_check_companions(report: Mapping[str, object]) -> Dict[str, object]:
    import metaspace_observability as observability
    import metaspace_synchronizer as synchronizer

    observed = observability.build_report(False)
    synchronized = synchronizer.build_report(False)
    root = observed["observation_quotients"]["root_signed_basis"]
    sync = synchronized["pair_synchronizability"]
    action = synchronized["right_action_synchronization"]
    pair_lattice = report["pair_lattice"]
    erasure = report["erasure"]
    assert isinstance(root, dict)
    assert isinstance(sync, dict)
    assert isinstance(action, dict)
    assert isinstance(pair_lattice, dict)
    assert isinstance(erasure, dict)
    checks = {
        "observability_horizon_profile": root["horizon_class_counts"] == [6, 192],
        "synchronizable_pair_union": sync["synchronizable_pair_count"]
        == pair_lattice["union_size"],
        "nonsynchronizable_pair_complement": sync["nonsynchronizable_pair_count"]
        == pair_lattice["complement_size"],
        "minimum_image_floor": action["minimum_image_size"]
        == erasure["minimum_retained_state_count"],
        "reset_absence": action["reset_word_exists"]
        == erasure["reset_word_exists"],
    }
    if not all(checks.values()):
        raise AssertionError("companion experiment integration check failed")
    return checks


def build_report(deep_check: bool) -> Dict[str, object]:
    automaton, certificate = signed.build_automaton(deep_check=False)
    if len(automaton.states) != EXPECTED_STATE_COUNT:
        raise AssertionError("state count changed")
    kernels = tuple(
        column_kernel(automaton.states, column) for column in range(3)
    )
    report: Dict[str, object] = {
        "status": "exact_tomography_erasure_duality_verified",
        "source_fingerprints": {
            "model_sha256": automaton.model_fingerprint,
            "state_sha256": automaton.state_fingerprint,
            "transition_table_sha256": automaton.table_fingerprint,
        },
        "source_certificate": certificate,
        "tomography": analyze_tomography(automaton, kernels),
        "pair_lattice": analyze_pair_lattice(automaton.states, kernels),
        "erasure": analyze_erasers(automaton, kernels),
        "left_right_information": analyze_left_right_information(automaton.states),
        "epistemic_scope": {
            "exact": (
                "All equalities are finite signed-code/matrix identities over the "
                "literal 192-state monoid."
            ),
            "duality_word": (
                "Duality means equality of exact equivalence kernels, not a Hilbert-space "
                "adjoint, thermodynamic law, or physical information principle."
            ),
        },
    }
    report["companion_cross_check"] = (
        cross_check_companions(report)
        if deep_check
        else {"performed": False, "available_via": "--deep-check"}
    )
    return report


def print_human(report: Mapping[str, object]) -> None:
    tomography = report["tomography"]
    lattice = report["pair_lattice"]
    erasure = report["erasure"]
    geometry = report["left_right_information"]
    assert isinstance(tomography, dict)
    assert isinstance(lattice, dict)
    assert isinstance(erasure, dict)
    assert isinstance(geometry, dict)
    print("Metaspace memory duality (exact)")
    print("tomography signatures:", tomography["distinct_signatures"])
    print(
        "column kernels / pair intersections:",
        lattice["single_column_kernel_sizes"],
        lattice["two_column_intersection_sizes"],
    )
    print(
        "mergeable / never mergeable pairs:",
        lattice["union_size"],
        "/",
        lattice["complement_size"],
    )
    for item in erasure["erasers"]:
        print(
            "eraser for {}: {} -> image {} with {}".format(
                item["retained_column"],
                " ".join(item["shortest_word"]),
                item["image_size"],
                item["fiber_size_multiplicity"],
            )
        )
    print("left/right information by rank:", geometry["by_matrix_rank"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--deep-check",
        action="store_true",
        help="cross-check the independent observability and synchronizer probes",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()
    report = build_report(args.deep_check)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)


if __name__ == "__main__":
    main()
