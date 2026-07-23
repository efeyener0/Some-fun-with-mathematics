"""Exact parity-cut signed transformation monoids in arbitrary dimension.

For n >= 2, define M_n inside the signed full transformation monoid
``C2 wreath T_n`` by keeping every singular signed transformation and only
those units whose underlying unsigned permutation is even.  The n=3 member
is exactly the 192-state combined chiral operator monoid.

This is an abstract semigroup continuation of the discovered finite control
structure.  It does not claim an n-dimensional extension of the source
non-associative algebra.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from itertools import product
from math import comb, factorial
from typing import Dict, Iterable, Iterator, List, Mapping, Sequence, Tuple


SignedCode = Tuple[int, ...]
HARD_MAX_N = 12
HARD_ENUMERATE_N = 4


def signed_axes(n: int) -> Tuple[int, ...]:
    return tuple(range(-n, 0)) + tuple(range(1, n + 1))


def validate_code(code: Sequence[int]) -> SignedCode:
    n = len(code)
    if n < 1 or any(value == 0 or abs(value) > n for value in code):
        raise ValueError("an n-code must contain n values from +/-{1,...,n}")
    return tuple(code)


def sign(value: int) -> int:
    if value == 0:
        raise ValueError("zero has no sign")
    return 1 if value > 0 else -1


def compose(left: Sequence[int], right: Sequence[int]) -> SignedCode:
    left_code = validate_code(left)
    right_code = validate_code(right)
    if len(left_code) != len(right_code):
        raise ValueError("signed transformations must have the same dimension")
    return tuple(
        sign(target) * left_code[abs(target) - 1] for target in right_code
    )


def code_rank(code: Sequence[int]) -> int:
    return len({abs(value) for value in validate_code(code)})


def permutation_parity(code: Sequence[int]) -> int:
    checked = validate_code(code)
    permutation = tuple(abs(value) for value in checked)
    if len(set(permutation)) != len(checked):
        raise ValueError("parity requires a signed permutation")
    inversions = sum(
        permutation[left] > permutation[right]
        for left in range(len(permutation))
        for right in range(left + 1, len(permutation))
    )
    return 1 if inversions % 2 == 0 else -1


def parity_character(code: Sequence[int]) -> int:
    checked = validate_code(code)
    if code_rank(checked) < len(checked):
        return 0
    return permutation_parity(checked)


def in_parity_cut_monoid(code: Sequence[int]) -> bool:
    return parity_character(code) != -1


def stirling_second(n: int, rank: int) -> int:
    if rank < 0 or rank > n:
        return 0
    table = [[0] * (rank + 1) for _ in range(n + 1)]
    table[0][0] = 1
    for size in range(1, n + 1):
        for blocks in range(1, min(size, rank) + 1):
            table[size][blocks] = (
                table[size - 1][blocks - 1]
                + blocks * table[size - 1][blocks]
            )
    return table[n][rank]


def rank_layer_count(n: int, rank: int) -> int:
    if not 1 <= rank <= n:
        return 0
    if n == 1:
        return 2 if rank == 1 else 0
    if rank == n:
        return (2 ** (n - 1)) * factorial(n)
    onto_unsigned = comb(n, rank) * factorial(rank) * stirling_second(n, rank)
    return (2**n) * onto_unsigned


def family_cardinality(n: int) -> int:
    if n == 1:
        return 2
    return (2 * n) ** n - (2 ** (n - 1)) * factorial(n)


def falling_factorial(n: int, rank: int) -> int:
    return factorial(n) // factorial(n - rank)


def ambient_cardinality(n: int) -> int:
    return (2 * n) ** n


def excluded_odd_unit_count(n: int) -> int:
    return ambient_cardinality(n) - family_cardinality(n)


def all_codes(n: int) -> Iterator[SignedCode]:
    yield from product(signed_axes(n), repeat=n)


def enumerate_family(n: int) -> Tuple[SignedCode, ...]:
    return tuple(code for code in all_codes(n) if in_parity_cut_monoid(code))


def projection_fiber_profile(n: int, retained_rank: int) -> Dict[int, int]:
    """Fiber-size -> output multiplicity for any fixed retained columns."""

    if not 1 <= retained_rank <= n:
        raise ValueError("retained rank must be between 1 and n")
    if retained_rank == n:
        return {1: family_cardinality(n)}

    remaining = n - retained_rank
    total_outputs = (2 * n) ** retained_rank
    injective_outputs = (
        (2**retained_rank)
        * factorial(n)
        // factorial(n - retained_rank)
    )
    colliding_outputs = total_outputs - injective_outputs
    ambient_fiber = (2 * n) ** remaining
    profile: Counter[int] = Counter()

    if remaining >= 2:
        excluded_per_injective_output = (
            (2 ** (remaining - 1)) * factorial(remaining)
        )
        profile[ambient_fiber] += colliding_outputs
        profile[ambient_fiber - excluded_per_injective_output] += injective_outputs
    else:
        # There is one unsigned completion.  Half of the injective partial
        # permutations complete evenly and half oddly; signs do not change parity.
        profile[ambient_fiber] += colliding_outputs + injective_outputs // 2
        profile[ambient_fiber - 2] += injective_outputs // 2

    result = dict(sorted(profile.items()))
    if sum(result.values()) != total_outputs:
        raise AssertionError("projection output multiplicities do not sum correctly")
    if sum(size * count for size, count in result.items()) != family_cardinality(n):
        raise AssertionError("projection fibers do not reconstruct the family")
    return result


def right_action_image_formula(n: int, rank: int) -> int:
    return family_cardinality(n) if rank == n else (2 * n) ** rank


def principal_right_ideal_formula(n: int, rank: int) -> int:
    return family_cardinality(n) if rank == n else (2 * rank) ** n


def right_action_image_rank_profile(n: int, rank: int) -> Dict[int, int]:
    if rank == n:
        return {layer: rank_layer_count(n, layer) for layer in range(1, n + 1)}
    return {
        layer: (2**rank)
        * falling_factorial(n, layer)
        * stirling_second(rank, layer)
        for layer in range(1, rank + 1)
    }


def principal_right_ideal_rank_profile(n: int, rank: int) -> Dict[int, int]:
    if rank == n:
        return {layer: rank_layer_count(n, layer) for layer in range(1, n + 1)}
    return {
        layer: (2**n)
        * falling_factorial(rank, layer)
        * stirling_second(n, layer)
        for layer in range(1, rank + 1)
    }


def family_row(n: int) -> Dict[str, object]:
    ranks = {rank: rank_layer_count(n, rank) for rank in range(1, n + 1)}
    if sum(ranks.values()) != family_cardinality(n):
        raise AssertionError("rank-layer formula does not sum to family cardinality")
    return {
        "n": n,
        "ambient_signed_transformation_count": ambient_cardinality(n),
        "parity_cut_monoid_count": family_cardinality(n),
        "excluded_odd_unit_count": excluded_odd_unit_count(n),
        "rank_layer_counts": ranks,
        "minimum_right_action_image_size": 2 * n,
        "minimum_principal_right_ideal_size": 2**n,
        "reset_word_possible_in_right_regular_action": False,
    }


def verify_enumerated_dimension(n: int) -> Dict[str, object]:
    states = enumerate_family(n)
    if len(states) != family_cardinality(n):
        raise AssertionError("enumerated family count differs from formula")
    rank_profile = Counter(code_rank(code) for code in states)
    expected_ranks = Counter(
        {rank: rank_layer_count(n, rank) for rank in range(1, n + 1)}
    )
    if rank_profile != expected_ranks:
        raise AssertionError("enumerated rank profile differs from formula")

    projection_checks: Dict[str, object] = {}
    product_checks = 0
    for rank in range(1, n + 1):
        observed_fibers = Counter(
            Counter(tuple(code[:rank]) for code in states).values()
        )
        expected_fibers = Counter(projection_fiber_profile(n, rank))
        if observed_fibers != expected_fibers:
            raise AssertionError("enumerated projection fibers differ from formula")

        witness = next(code for code in states if code_rank(code) == rank)
        left_image = {compose(state, witness) for state in states}
        right_image = {compose(witness, state) for state in states}
        if len(left_image) != right_action_image_formula(n, rank):
            raise AssertionError("M_n*p image formula failed")
        if len(right_image) != principal_right_ideal_formula(n, rank):
            raise AssertionError("p*M_n image formula failed")
        left_rank_profile = Counter(code_rank(code) for code in left_image)
        right_rank_profile = Counter(code_rank(code) for code in right_image)
        if left_rank_profile != Counter(right_action_image_rank_profile(n, rank)):
            raise AssertionError("M_n*p rank-layer formula failed")
        if right_rank_profile != Counter(principal_right_ideal_rank_profile(n, rank)):
            raise AssertionError("p*M_n rank-layer formula failed")

        retained_columns = tuple(sorted({abs(value) - 1 for value in witness}))
        projection_to_product: Dict[Tuple[int, ...], SignedCode] = {}
        product_to_projection: Dict[SignedCode, Tuple[int, ...]] = {}
        for state in states:
            projection = tuple(state[column] for column in retained_columns)
            result = compose(state, witness)
            if projection_to_product.setdefault(projection, result) != result:
                raise AssertionError("right-action kernel lost projection determinism")
            if product_to_projection.setdefault(result, projection) != projection:
                raise AssertionError("right-action product lost retained-column recovery")
            product_checks += 1

        projection_checks[str(rank)] = {
            "fiber_size_multiplicity": {
                str(size): count for size, count in sorted(observed_fibers.items())
            },
            "M_n_times_p_size": len(left_image),
            "p_times_M_n_size": len(right_image),
            "M_n_times_p_rank_profile": dict(sorted(left_rank_profile.items())),
            "p_times_M_n_rank_profile": dict(sorted(right_rank_profile.items())),
            "kernel_equals_retained_column_equality": True,
        }

    return {
        "state_count": len(states),
        "rank_profile": dict(sorted(rank_profile.items())),
        "projection_and_product_checks": projection_checks,
        "kernel_state_checks": product_checks,
    }


def verify_character_pairs(n: int) -> int:
    codes = tuple(all_codes(n))
    checks = 0
    for left in codes:
        for right in codes:
            if parity_character(compose(left, right)) != (
                parity_character(left) * parity_character(right)
            ):
                raise AssertionError("parity character is not multiplicative")
            checks += 1
    return checks


def verify_n3_bridge() -> Dict[str, object]:
    import certified_signed_metaspace as source

    source_automaton, evidence = source.build_automaton(deep_check=False)
    abstract_states = set(enumerate_family(3))
    if abstract_states != set(source_automaton.states):
        raise AssertionError("abstract M_3 differs from the chiral combined monoid")
    return {
        "state_set_equality": True,
        "state_count": len(abstract_states),
        "source_model_sha256": source_automaton.model_fingerprint,
        "source_state_sha256": source_automaton.state_fingerprint,
        "source_generator_transition_checks": evidence[
            "generator_transition_checks"
        ],
    }


def build_report(max_n: int, enumerate_through: int, deep_check: bool) -> Dict[str, object]:
    rows = [family_row(n) for n in range(2, max_n + 1)]
    expected_small = {
        2: (12, {1: 8, 2: 4}),
        3: (192, {1: 24, 2: 144, 3: 24}),
        4: (3904, {1: 64, 2: 1344, 3: 2304, 4: 192}),
        5: (98080, {1: 160, 2: 9600, 3: 48000, 4: 38400, 5: 1920}),
    }
    for row in rows:
        n = row["n"]
        if n in expected_small:
            count, ranks = expected_small[n]
            if row["parity_cut_monoid_count"] != count or row["rank_layer_counts"] != ranks:
                raise AssertionError("small-n expected profile changed")

    enumeration = {
        str(n): verify_enumerated_dimension(n)
        for n in range(2, min(enumerate_through, max_n) + 1)
    }
    character_checks = {
        str(n): verify_character_pairs(n)
        for n in range(2, min(3 if deep_check else 2, max_n) + 1)
    }
    return {
        "status": "exact_parity_cut_signed_transformation_family",
        "definition": {
            "ambient": "C2 wreath T_n; codes in +/-{1,...,n}^n",
            "character": "0 on singular maps; absolute permutation parity on units",
            "family": "M_n = character inverse image of {0,+1}",
            "cardinality_for_n_at_least_2": "(2n)^n - 2^(n-1) n!",
            "rank_r_below_n": "2^n * C(n,r) * r! * S(n,r)",
            "rank_n": "2^(n-1) n!",
            "unit_group": "C2^n semidirect A_n",
            "maximal_proper": (
                "Adding any excluded odd unit restores the full ambient unit group; "
                "the singular ideal is already complete."
            ),
        },
        "dimensions": rows,
        "enumeration_certificates": enumeration,
        "character_pair_checks": character_checks,
        "n3_chiral_bridge": verify_n3_bridge(),
        "general_action_formulas": {
            "for_rank_r_below_n": {
                "M_n_times_p": "(2n)^r",
                "p_times_M_n": "(2r)^n",
                "rank_s_in_M_n_times_p": "2^r * falling(n,s) * S(r,s)",
                "rank_s_in_p_times_M_n": "2^n * falling(r,s) * S(n,s)",
                "kernel_R_p": "equality on the r columns in image(abs(p))",
            },
            "for_rank_n": "left and right multiplication by a unit both permute M_n",
            "minimum_image": "2n at rank one",
            "minimum_principal_right_ideal": "2^n at rank one",
            "reset_absence": "rank zero / the universal kernel is absent",
        },
        "epistemic_scope": {
            "proved_abstract_family": (
                "The character, counts, fibers, kernels, and image formulas concern "
                "the explicitly defined signed transformation monoids."
            ),
            "bridge": "Only n=3 is identified with the literal chiral operator monoid.",
            "not_claimed": (
                "No n-dimensional non-associative multiplication algebra, physical "
                "metaspace, or generator presentation is inferred for n != 3."
            ),
        },
    }


def print_human(report: Mapping[str, object]) -> None:
    print("Parity-cut signed metaspace family")
    print("M_n = all singular signed maps + signed even-permutation units")
    for row in report["dimensions"]:
        print(
            "n={}: ambient={}, M_n={}, excluded={}, ranks={}, min-image={}".format(
                row["n"],
                row["ambient_signed_transformation_count"],
                row["parity_cut_monoid_count"],
                row["excluded_odd_unit_count"],
                row["rank_layer_counts"],
                row["minimum_right_action_image_size"],
            )
        )
    bridge = report["n3_chiral_bridge"]
    print("n=3 chiral state-set equality:", bridge["state_set_equality"])
    print("enumerated dimensions:", sorted(report["enumeration_certificates"]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-n",
        type=int,
        default=6,
        help="largest formula-only dimension (2..12; default: 6)",
    )
    parser.add_argument(
        "--enumerate-through",
        type=int,
        default=4,
        help="largest exhaustively materialized dimension (0..4; default: 4)",
    )
    parser.add_argument(
        "--deep-check",
        action="store_true",
        help="also check all 46,656 ambient n=3 character products",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not 2 <= args.max_n <= HARD_MAX_N:
        raise SystemExit("--max-n must be between 2 and {}".format(HARD_MAX_N))
    if not 0 <= args.enumerate_through <= HARD_ENUMERATE_N:
        raise SystemExit(
            "--enumerate-through must be between 0 and {}".format(
                HARD_ENUMERATE_N
            )
        )
    report = build_report(args.max_n, args.enumerate_through, args.deep_check)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)


if __name__ == "__main__":
    main()
