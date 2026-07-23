"""Exact finite-monoid probe for the chiral multiplication operators.

The matrices are the left/right actions of ``h`` and ``q`` in the basis
``(1, h, q)`` of the experimental algebra.  Enumeration is breadth-first from
the identity and extends words on the right.  Matrix entries remain Python
integers; span ranks use ``fractions.Fraction`` row reduction.

Default execution proves closure for the left, right, and combined monoids.
Smaller user-selected caps produce explicitly bounded reports and suppress
claims that require complete closure.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from hashlib import sha256
from itertools import product
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple


Matrix = Tuple[int, int, int, int, int, int, int, int, int]

HARD_STATE_CAP = 100_000
HARD_DEPTH_CAP = 64

I3: Matrix = (1, 0, 0, 0, 1, 0, 0, 0, 1)
ZERO3: Matrix = (0, 0, 0, 0, 0, 0, 0, 0, 0)

L_H: Matrix = (0, 0, 1, 1, 0, 0, 0, 1, 0)
R_H: Matrix = (0, 0, -1, 1, 0, 0, 0, 1, 0)
L_Q: Matrix = (0, -1, 0, 0, 0, 0, 1, 0, 1)
R_Q: Matrix = (0, 1, 0, 0, 0, 0, 1, 0, 1)

# Coordinate matrix of the anti-involution 1 -> 1, h -> -h, q -> q.
S: Matrix = (1, 0, 0, 0, -1, 0, 0, 0, 1)


def matrix_multiply(left: Matrix, right: Matrix) -> Matrix:
    return tuple(
        sum(left[3 * row + k] * right[3 * k + column] for k in range(3))
        for row in range(3)
        for column in range(3)
    )  # type: ignore[return-value]


def matrix_negate(matrix: Matrix) -> Matrix:
    return tuple(-value for value in matrix)  # type: ignore[return-value]


def determinant(matrix: Matrix) -> int:
    return (
        matrix[0] * (matrix[4] * matrix[8] - matrix[5] * matrix[7])
        - matrix[1] * (matrix[3] * matrix[8] - matrix[5] * matrix[6])
        + matrix[2] * (matrix[3] * matrix[7] - matrix[4] * matrix[6])
    )


def matrix_rank(matrix: Matrix) -> int:
    if determinant(matrix):
        return 3
    row_pairs = ((0, 1), (0, 2), (1, 2))
    column_pairs = ((0, 1), (0, 2), (1, 2))
    for row_a, row_b in row_pairs:
        for column_a, column_b in column_pairs:
            minor = (
                matrix[3 * row_a + column_a] * matrix[3 * row_b + column_b]
                - matrix[3 * row_a + column_b] * matrix[3 * row_b + column_a]
            )
            if minor:
                return 2
    return 1 if any(matrix) else 0


def inverse_unimodular(matrix: Matrix) -> Optional[Matrix]:
    det = determinant(matrix)
    if abs(det) != 1:
        return None
    adjugate = (
        matrix[4] * matrix[8] - matrix[5] * matrix[7],
        matrix[2] * matrix[7] - matrix[1] * matrix[8],
        matrix[1] * matrix[5] - matrix[2] * matrix[4],
        matrix[5] * matrix[6] - matrix[3] * matrix[8],
        matrix[0] * matrix[8] - matrix[2] * matrix[6],
        matrix[2] * matrix[3] - matrix[0] * matrix[5],
        matrix[3] * matrix[7] - matrix[4] * matrix[6],
        matrix[1] * matrix[6] - matrix[0] * matrix[7],
        matrix[0] * matrix[4] - matrix[1] * matrix[3],
    )
    return tuple(value // det for value in adjugate)  # type: ignore[return-value]


def matrix_order(matrix: Matrix, step_cap: int) -> Optional[int]:
    value = I3
    for exponent in range(1, step_cap + 1):
        value = matrix_multiply(value, matrix)
        if value == I3:
            return exponent
    return None


def rational_span_rank(rows: Iterable[Matrix]) -> int:
    matrix = [[Fraction(value) for value in row] for row in rows]
    pivot_row = 0
    for column in range(9):
        candidate = next(
            (row for row in range(pivot_row, len(matrix)) if matrix[row][column]),
            None,
        )
        if candidate is None:
            continue
        matrix[pivot_row], matrix[candidate] = matrix[candidate], matrix[pivot_row]
        pivot = matrix[pivot_row][column]
        matrix[pivot_row] = [value / pivot for value in matrix[pivot_row]]
        for row in range(len(matrix)):
            if row == pivot_row or not matrix[row][column]:
                continue
            factor = matrix[row][column]
            matrix[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(matrix[row], matrix[pivot_row])
            ]
        pivot_row += 1
        if pivot_row == 9:
            break
    return pivot_row


def matrix_digest(states: Iterable[Matrix]) -> str:
    payload = ";".join(
        ",".join(str(value) for value in matrix) for matrix in sorted(states)
    ).encode("ascii")
    return sha256(payload).hexdigest()


def matrix_rows(matrix: Matrix) -> List[List[int]]:
    return [list(matrix[0:3]), list(matrix[3:6]), list(matrix[6:9])]


def signed_basis_actions() -> Set[Matrix]:
    """All maps sending each basis vector to one signed basis vector."""

    actions: Set[Matrix] = set()
    for targets in product(range(3), repeat=3):
        for signs in product((-1, 1), repeat=3):
            entries = [0] * 9
            for column, (row, sign) in enumerate(zip(targets, signs)):
                entries[3 * row + column] = sign
            actions.add(tuple(entries))  # type: ignore[arg-type]
    assert len(actions) == (2 * 3) ** 3 == 216
    return actions


@dataclass
class Enumeration:
    name: str
    generators: Tuple[Matrix, ...]
    depths: Dict[Matrix, int]
    layers: List[int]
    status: str
    first_empty_depth: Optional[int]
    explored_transitions: int
    state_cap: int
    depth_cap: int

    @property
    def closed(self) -> bool:
        return self.status == "closed_exact"

    @property
    def states(self) -> Set[Matrix]:
        return set(self.depths)


def enumerate_monoid(
    name: str,
    generators: Sequence[Matrix],
    state_cap: int,
    depth_cap: int,
) -> Enumeration:
    """Breadth-first word enumeration with explicit state and depth bounds."""

    generator_tuple = tuple(generators)
    depths: Dict[Matrix, int] = {I3: 0}
    frontier = [I3]
    layers = [1]
    transitions = 0

    for depth in range(1, depth_cap + 1):
        new_frontier: List[Matrix] = []
        for state in frontier:
            for generator in generator_tuple:
                transitions += 1
                candidate = matrix_multiply(state, generator)
                if candidate in depths:
                    continue
                if len(depths) >= state_cap:
                    if new_frontier:
                        layers.append(len(new_frontier))
                    return Enumeration(
                        name,
                        generator_tuple,
                        depths,
                        layers,
                        "bounded_state_cap",
                        None,
                        transitions,
                        state_cap,
                        depth_cap,
                    )
                depths[candidate] = depth
                new_frontier.append(candidate)
        if not new_frontier:
            return Enumeration(
                name,
                generator_tuple,
                depths,
                layers,
                "closed_exact",
                depth,
                transitions,
                state_cap,
                depth_cap,
            )
        layers.append(len(new_frontier))
        frontier = new_frontier

    # A closure can happen exactly at the requested depth.  Test the final
    # frontier without admitting another layer before declaring truncation.
    has_unseen_extension = any(
        matrix_multiply(state, generator) not in depths
        for state in frontier
        for generator in generator_tuple
    )
    return Enumeration(
        name,
        generator_tuple,
        depths,
        layers,
        "bounded_depth_cap" if has_unseen_extension else "closed_exact",
        None if has_unseen_extension else depth_cap + 1,
        transitions,
        state_cap,
        depth_cap,
    )


def sorted_counter(values: Iterable[int]) -> Dict[int, int]:
    return dict(sorted(Counter(values).items()))


def analyze_enumeration(enumeration: Enumeration) -> Dict[str, object]:
    states = enumeration.states
    ranks = {state: matrix_rank(state) for state in states}
    determinants = {state: determinant(state) for state in states}
    idempotents = {state for state in states if matrix_multiply(state, state) == state}
    unimodular = {state for state in states if abs(determinants[state]) == 1}
    units = {
        state
        for state in unimodular
        if inverse_unimodular(state) in states
    }
    orders = {
        state: matrix_order(state, max(1, len(states)))
        for state in units
    }
    if enumeration.closed:
        assert all(order is not None for order in orders.values())

    pairwise_closed: Optional[bool] = None
    pairwise_products_checked = 0
    if enumeration.closed:
        pairwise_products_checked = len(states) * len(states)
        pairwise_closed = all(
            matrix_multiply(left, right) in states
            for left in states
            for right in states
        )
        assert pairwise_closed

    return {
        "status": enumeration.status,
        "state_count": len(states),
        "generator_count": len(enumeration.generators),
        "layers_by_minimal_word_depth": enumeration.layers,
        "max_minimal_word_depth": max(enumeration.depths.values()),
        "first_empty_depth": enumeration.first_empty_depth,
        "explored_generator_transitions": enumeration.explored_transitions,
        "state_cap": enumeration.state_cap,
        "depth_cap": enumeration.depth_cap,
        "entry_absolute_max": max(abs(value) for state in states for value in state),
        "matrix_rank_profile": sorted_counter(ranks.values()),
        "determinant_profile": sorted_counter(determinants.values()),
        "idempotent_count": len(idempotents),
        "idempotent_rank_profile": sorted_counter(ranks[state] for state in idempotents),
        "idempotent_depth_profile": sorted_counter(
            enumeration.depths[state] for state in idempotents
        ),
        "unimodular_state_count": len(unimodular),
        "verified_unit_count": len(units),
        "unit_profile_complete": enumeration.closed,
        "unit_order_profile": sorted_counter(
            order for order in orders.values() if order is not None
        ),
        "unit_depth_profile": sorted_counter(enumeration.depths[state] for state in units),
        "zero_matrix_present": ZERO3 in states,
        "pairwise_closure_verified": pairwise_closed,
        "pairwise_products_checked": pairwise_products_checked,
        "linear_span_rank_over_Q": rational_span_rank(states),
        "state_set_sha256": matrix_digest(states),
    }


EXPECTED: Mapping[str, Mapping[str, object]] = {
    "left": {
        "state_count": 99,
        "layers_by_minimal_word_depth": [1, 2, 4, 6, 9, 11, 13, 12, 12, 10, 9, 6, 3, 1],
        "max_minimal_word_depth": 13,
        "first_empty_depth": 14,
        "matrix_rank_profile": {1: 24, 2: 72, 3: 3},
        "determinant_profile": {0: 96, 1: 3},
        "idempotent_count": 19,
        "idempotent_rank_profile": {1: 12, 2: 6, 3: 1},
        "idempotent_depth_profile": {0: 1, 2: 1, 3: 2, 4: 3, 5: 3, 6: 4, 7: 1, 8: 1, 10: 3},
        "verified_unit_count": 3,
        "unit_order_profile": {1: 1, 3: 2},
        "unit_depth_profile": {0: 1, 1: 1, 2: 1},
        "linear_span_rank_over_Q": 9,
        "state_set_sha256": "77abdbfa2de1833e5989318e3535022fa70122ef852ea3d4fcb995a4a3776df2",
    },
    "right": {
        "state_count": 102,
        "layers_by_minimal_word_depth": [1, 2, 4, 7, 12, 15, 17, 15, 14, 9, 5, 1],
        "max_minimal_word_depth": 11,
        "first_empty_depth": 12,
        "matrix_rank_profile": {1: 24, 2: 72, 3: 6},
        "determinant_profile": {-1: 3, 0: 96, 1: 3},
        "idempotent_count": 19,
        "idempotent_rank_profile": {1: 12, 2: 6, 3: 1},
        "idempotent_depth_profile": {0: 1, 2: 1, 4: 2, 5: 4, 6: 4, 7: 3, 9: 3, 10: 1},
        "verified_unit_count": 6,
        "unit_order_profile": {1: 1, 2: 1, 3: 2, 6: 2},
        "unit_depth_profile": {0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1},
        "linear_span_rank_over_Q": 9,
        "state_set_sha256": "f5ad0d5edbb95b69ed3057e9cb7a766f0342f8e64fa45b217eee32a3a067114c",
    },
    "combined": {
        "state_count": 192,
        "layers_by_minimal_word_depth": [1, 4, 14, 32, 44, 37, 24, 20, 12, 4],
        "max_minimal_word_depth": 9,
        "first_empty_depth": 10,
        "matrix_rank_profile": {1: 24, 2: 144, 3: 24},
        "determinant_profile": {-1: 12, 0: 168, 1: 12},
        "idempotent_count": 25,
        "idempotent_rank_profile": {1: 12, 2: 12, 3: 1},
        "idempotent_depth_profile": {0: 1, 2: 4, 3: 3, 4: 5, 5: 6, 6: 5, 9: 1},
        "verified_unit_count": 24,
        "unit_order_profile": {1: 1, 2: 7, 3: 8, 6: 8},
        "unit_depth_profile": {0: 1, 1: 2, 2: 4, 3: 7, 4: 6, 5: 4},
        "linear_span_rank_over_Q": 9,
        "state_set_sha256": "c7c110dce5fc69818255a07552b35c0b50f163aa624a63e06ade0eaa1db1c9fc",
    },
}


def assert_expected_profile(name: str, profile: Mapping[str, object]) -> None:
    for key, expected in EXPECTED[name].items():
        actual = profile[key]
        assert actual == expected, "{} {}: {!r} != {!r}".format(
            name, key, actual, expected
        )
    assert profile["entry_absolute_max"] == 1
    assert profile["zero_matrix_present"] is False
    assert profile["pairwise_closure_verified"] is True
    assert profile["unimodular_state_count"] == profile["verified_unit_count"]


def closed_relations(
    left: Enumeration,
    right: Enumeration,
    combined: Enumeration,
) -> Tuple[Dict[str, object], Dict[str, object]]:
    assert left.closed and right.closed and combined.closed
    left_states = left.states
    right_states = right.states
    combined_states = combined.states

    assert matrix_multiply(S, S) == I3
    assert matrix_multiply(matrix_multiply(S, R_H), S) == matrix_negate(L_H)
    assert matrix_multiply(matrix_multiply(S, R_Q), S) == L_Q

    negative_left = {matrix_negate(state) for state in left_states}
    signed_left = left_states | negative_left
    left_singular = {state for state in left_states if determinant(state) == 0}
    assert left_states & negative_left == left_singular
    assert len(left_singular) == 96

    conjugated_right = {
        matrix_multiply(matrix_multiply(S, state), S) for state in right_states
    }
    assert conjugated_right == signed_left
    assert len(signed_left) == 102

    # The combined unit group is generated without either singular q-action.
    unit_enumeration = enumerate_monoid(
        "combined_units",
        (L_H, R_H),
        HARD_STATE_CAP,
        HARD_DEPTH_CAP,
    )
    assert unit_enumeration.closed
    generated_units = unit_enumeration.states
    combined_units = {
        state for state in combined_states if abs(determinant(state)) == 1
    }
    assert generated_units == combined_units
    assert len(combined_units) == 24

    diagonal_units = {
        state
        for state in combined_units
        if all(
            state[3 * row + column] == 0
            for row in range(3)
            for column in range(3)
            if row != column
        )
    }
    expected_diagonals = {
        (a, 0, 0, 0, b, 0, 0, 0, c)
        for a, b, c in product((-1, 1), repeat=3)
    }
    assert diagonal_units == expected_diagonals
    assert all(matrix_multiply(state, state) == I3 for state in diagonal_units)
    assert all(
        matrix_multiply(left_state, right_state)
        == matrix_multiply(right_state, left_state)
        for left_state in diagonal_units
        for right_state in diagonal_units
    )

    cyclic_three = {I3, L_H, matrix_multiply(L_H, L_H)}
    assert matrix_multiply(matrix_multiply(L_H, L_H), L_H) == I3
    coordinate_flip = (-1, 0, 0, 0, 1, 0, 0, 0, 1)
    coordinate_flip_orbit = set()
    orbit_value = coordinate_flip
    for _ in range(3):
        coordinate_flip_orbit.add(orbit_value)
        orbit_value = matrix_multiply(
            matrix_multiply(L_H, orbit_value), matrix_multiply(L_H, L_H)
        )
    assert coordinate_flip_orbit == {
        (-1, 0, 0, 0, 1, 0, 0, 0, 1),
        (1, 0, 0, 0, -1, 0, 0, 0, 1),
        (1, 0, 0, 0, 1, 0, 0, 0, -1),
    }
    unit_normal_forms = {
        matrix_multiply(diagonal, cyclic)
        for diagonal in diagonal_units
        for cyclic in cyclic_three
    }
    assert unit_normal_forms == combined_units
    assert diagonal_units & cyclic_three == {I3}
    cyclic_inverses = {}
    for cyclic in cyclic_three:
        inverse = inverse_unimodular(cyclic)
        assert inverse is not None
        cyclic_inverses[cyclic] = inverse
    assert all(
        matrix_multiply(
            matrix_multiply(cyclic, diagonal),
            cyclic_inverses[cyclic],
        )
        in diagonal_units
        for cyclic in cyclic_three
        for diagonal in diagonal_units
    )

    assert matrix_multiply(matrix_multiply(L_H, R_H), L_H) == S
    assert matrix_multiply(L_Q, S) == R_Q

    left_times_units = {
        matrix_multiply(state, unit)
        for state in left_states
        for unit in combined_units
    }
    right_times_units = {
        matrix_multiply(state, unit)
        for state in right_states
        for unit in combined_units
    }
    assert left_times_units == combined_states
    assert right_times_units == combined_states

    left_right_intersection = left_states & right_states
    left_right_union = left_states | right_states
    mixed = combined_states - left_right_union
    assert len(left_right_intersection) == 49
    assert len(left_right_union) == 152
    assert len(mixed) == 40

    combined_singular = {
        state for state in combined_states if determinant(state) == 0
    }
    ambient_signed_actions = signed_basis_actions()
    ambient_singular = {
        state for state in ambient_signed_actions if determinant(state) == 0
    }
    ambient_units = ambient_signed_actions - ambient_singular
    assert len(ambient_singular) == 168
    assert len(ambient_units) == 48
    assert combined_states <= ambient_signed_actions
    assert combined_singular == ambient_singular
    assert len(ambient_units - combined_units) == 24
    singular_unit_action = {
        matrix_multiply(state, unit)
        for state in left_singular
        for unit in combined_units
    }
    assert singular_unit_action == combined_singular
    assert {matrix_negate(state) for state in combined_singular} == combined_singular

    relations = {
        "status": "exact_full_closure_relations_verified",
        "S": matrix_rows(S),
        "S_squared_is_identity": True,
        "S_Rh_S_equals_minus_Lh": True,
        "S_Rq_S_equals_Lq": True,
        "S_word": "L_h R_h L_h",
        "Rq_equals_Lq_S": True,
        "right_conjugate_equals_left_union_negative_left": True,
        "left_intersection_negative_left_count": len(left_states & negative_left),
        "left_singular_count": len(left_singular),
        "left_intersection_negative_left_is_exactly_left_singular": True,
        "left_right_intersection_count": len(left_right_intersection),
        "left_right_union_count": len(left_right_union),
        "combined_states_outside_left_right_union": len(mixed),
        "combined_equals_left_times_unit_group": True,
        "combined_equals_right_times_unit_group": True,
        "combined_singular_count": len(combined_singular),
        "ambient_signed_basis_action_count": len(ambient_signed_actions),
        "all_singular_signed_basis_actions_present": True,
        "ambient_signed_basis_unit_count": len(ambient_units),
        "signed_basis_units_outside_combined_count": len(
            ambient_units - combined_units
        ),
        "combined_singular_equals_left_singular_times_unit_group": True,
        "combined_singular_closed_under_global_sign": True,
    }
    unit_group = {
        "state_count": len(combined_units),
        "generated_by": ["L_h", "R_h"],
        "diagonal_sign_subgroup_count": len(diagonal_units),
        "cyclic_permutation_subgroup_count": len(cyclic_three),
        "unique_normal_form": "diag(e1,e2,e3) * L_h^k, ei in {+1,-1}, k in {0,1,2}",
        "normal_form_count": len(unit_normal_forms),
        "diagonal_subgroup_is_C2_cubed": True,
        "Lh_conjugation_preserves_diagonal_subgroup": True,
        "single_coordinate_flip_conjugacy_orbit_count": len(coordinate_flip_orbit),
        "semidirect_product": "C2^3 semidirect C3",
        "isomorphism": "C2 x A4",
        "isomorphism_basis": "C3 cyclically permutes the three diagonal sign coordinates; the all-minus sign is central",
    }
    return relations, unit_group


def bounded_relations() -> Tuple[Dict[str, object], Dict[str, object]]:
    reason = "withheld: one or more monoids did not close inside the selected bounds"
    return (
        {"status": reason},
        {"status": reason},
    )


def build_report(state_cap: int, depth_cap: int) -> Dict[str, object]:
    enumerations = {
        "left": enumerate_monoid("left", (L_H, L_Q), state_cap, depth_cap),
        "right": enumerate_monoid("right", (R_H, R_Q), state_cap, depth_cap),
        "combined": enumerate_monoid(
            "combined", (L_H, L_Q, R_H, R_Q), state_cap, depth_cap
        ),
    }
    profiles = {
        name: analyze_enumeration(enumeration)
        for name, enumeration in enumerations.items()
    }
    all_closed = all(enumeration.closed for enumeration in enumerations.values())
    expected_profiles_asserted = False
    if all_closed:
        for name, profile in profiles.items():
            assert_expected_profile(name, profile)
        expected_profiles_asserted = True
        relations, unit_group = closed_relations(
            enumerations["left"], enumerations["right"], enumerations["combined"]
        )
    else:
        relations, unit_group = bounded_relations()

    return {
        "method": {
            "word_extension": "breadth-first; append one generator on the right",
            "matrix_arithmetic": "exact Python integers",
            "span_rank_arithmetic": "fractions.Fraction",
            "hard_state_cap": HARD_STATE_CAP,
            "hard_depth_cap": HARD_DEPTH_CAP,
            "selected_state_cap": state_cap,
            "selected_depth_cap": depth_cap,
        },
        "generators": {
            "L_h": matrix_rows(L_H),
            "L_q": matrix_rows(L_Q),
            "R_h": matrix_rows(R_H),
            "R_q": matrix_rows(R_Q),
        },
        "monoids": profiles,
        "cross_relations": relations,
        "combined_unit_group": unit_group,
        "expected_profiles_asserted": expected_profiles_asserted,
        "epistemic_bounds": {
            "closed_claim": (
                "When status is closed_exact, every generator extension and every pairwise product was checked."
            ),
            "bounded_claim": (
                "When a cap is hit, counts are lower bounds on the generated monoid and cross-closure classifications are withheld."
            ),
            "scope": "Only the four literal 3x3 integer matrices in this file are classified.",
            "span_warning": (
                "Linear span rank 9 means the finite set spans M3 over Q/R; it does not mean the multiplicative monoid equals M3."
            ),
            "no_infinitude_inference": (
                "Failure to close under a smaller selected cap would not prove infinitude."
            ),
        },
    }


def print_human(report: Mapping[str, object]) -> None:
    monoids = report["monoids"]
    assert isinstance(monoids, dict)
    print("Chiral operator monoids (exact integer arithmetic)")
    for name in ("left", "right", "combined"):
        profile = monoids[name]
        assert isinstance(profile, dict)
        print(
            "{}: status={}, states={}, max-depth={}, ranks={}, idempotents={} {}, units={}, span-rank={}".format(
                name,
                profile["status"],
                profile["state_count"],
                profile["max_minimal_word_depth"],
                profile["matrix_rank_profile"],
                profile["idempotent_count"],
                profile["idempotent_rank_profile"],
                profile["verified_unit_count"],
                profile["linear_span_rank_over_Q"],
            )
        )
        print("  layers:", profile["layers_by_minimal_word_depth"])
        print("  determinants:", profile["determinant_profile"])
        print("  unit orders:", profile["unit_order_profile"])
        print("  pairwise closure:", profile["pairwise_closure_verified"])
    print("Expected 99/102/192 profiles asserted:", report["expected_profiles_asserted"])
    relations = report["cross_relations"]
    assert isinstance(relations, dict)
    print("Cross relations:", relations["status"])
    if relations["status"] == "exact_full_closure_relations_verified":
        print("  |L intersect R| =", relations["left_right_intersection_count"])
        print("  combined mixed states =", relations["combined_states_outside_left_right_union"])
        print("  R conjugates to L union (-L):", relations["right_conjugate_equals_left_union_negative_left"])
        unit_group = report["combined_unit_group"]
        assert isinstance(unit_group, dict)
        print("  combined unit group:", unit_group["semidirect_product"], "=", unit_group["isomorphism"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state-cap",
        type=int,
        default=HARD_STATE_CAP,
        help="enumeration state cap (1..100000; default: 100000)",
    )
    parser.add_argument(
        "--depth-cap",
        type=int,
        default=HARD_DEPTH_CAP,
        help="minimal-word depth cap (0..64; default: 64)",
    )
    parser.add_argument("--json", action="store_true", help="emit the full JSON certificate")
    args = parser.parse_args()
    if not 1 <= args.state_cap <= HARD_STATE_CAP:
        raise SystemExit("--state-cap must be between 1 and {}".format(HARD_STATE_CAP))
    if not 0 <= args.depth_cap <= HARD_DEPTH_CAP:
        raise SystemExit("--depth-cap must be between 0 and {}".format(HARD_DEPTH_CAP))
    report = build_report(args.state_cap, args.depth_cap)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)


if __name__ == "__main__":
    main()
