#!/usr/bin/env python3
"""Exact deformation space of the fixed six-dimensional shadow-root clock.

This module does *not* classify every minimal strong-root extension.  It fixes
the particular left/right clock operators of ``shadow_root_clock.py`` on the
chosen basis ``(1,h,q,s,t,u)`` and asks how the remaining multiplication cells
may be completed bilinearly.

The answer is an affine 48-space over R: eight ordered cells are free and each
has six output coordinates.  Requiring the natural Z/2 shadow grading cuts it
to an affine 24-space.  The module separates invariants of the fixed operator
skeleton from invariants of one multiplication completion, supplies small
integer deformation witnesses, and records the first repeated-s degree at
which every free seam can become visible.

Only the standard library and the local exact clock module are used.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import dataclass
from typing import Mapping, Sequence, TypeAlias

import shadow_root_clock as clock


DIMENSION = clock.DIMENSION
LABELS = clock.BASIS_LABELS
ONE, H, Q, S, T, U = clock.BASIS
ZERO = clock.ZERO

Vector: TypeAlias = tuple[int, ...]
Table: TypeAlias = tuple[tuple[Vector, ...], ...]
Matrix: TypeAlias = tuple[tuple[int, ...], ...]
Cell: TypeAlias = tuple[int, int]

CORE = frozenset((0, 1, 2))
SHADOW = frozenset((3, 4, 5))
FREE_CELLS: tuple[Cell, ...] = (
    (2, 4),  # q*t
    (2, 5),  # q*u
    (4, 2),  # t*q
    (4, 4),  # t*t
    (4, 5),  # t*u
    (5, 2),  # u*q
    (5, 4),  # u*t
    (5, 5),  # u*u
)
EXPECTED_FIRST_SEAM_DEGREE: Mapping[Cell, int] = {
    (2, 4): 7,
    (2, 5): 9,
    (4, 2): 7,
    (4, 4): 6,
    (4, 5): 8,
    (5, 2): 9,
    (5, 4): 8,
    (5, 5): 10,
}


@dataclass(frozen=True, slots=True)
class Completion:
    name: str
    table: Table
    description: str


def add(*vectors: Sequence[int]) -> Vector:
    return tuple(sum(coordinates) for coordinates in zip(*vectors, strict=True))


def negate(vector: Sequence[int]) -> Vector:
    return tuple(-coordinate for coordinate in vector)


def subtract(left: Sequence[int], right: Sequence[int]) -> Vector:
    return add(left, negate(right))


def origin_table() -> Table:
    return tuple(
        tuple(clock.vector_from_code(clock.PRODUCT_CODES[left][right]) for right in range(DIMENSION))
        for left in range(DIMENSION)
    )


ORIGIN_TABLE = origin_table()


def mutable_copy(table: Table) -> list[list[Vector]]:
    return [[tuple(cell) for cell in row] for row in table]


def freeze(table: Sequence[Sequence[Sequence[int]]]) -> Table:
    if len(table) != DIMENSION or any(len(row) != DIMENSION for row in table):
        raise ValueError("multiplication table must be 6x6")
    frozen = tuple(tuple(tuple(cell) for cell in row) for row in table)
    if any(len(cell) != DIMENSION for row in frozen for cell in row):
        raise ValueError("every multiplication cell must be a six-vector")
    return frozen


def completion(
    name: str,
    replacements: Mapping[Cell, Sequence[int]],
    description: str,
) -> Completion:
    unknown = set(replacements).difference(FREE_CELLS)
    if unknown:
        raise ValueError(f"replacement outside the free seam: {sorted(unknown)}")
    table = mutable_copy(ORIGIN_TABLE)
    for (left, right), value in replacements.items():
        if len(value) != DIMENSION:
            raise ValueError("replacement vector has the wrong dimension")
        table[left][right] = tuple(value)
    result = Completion(name, freeze(table), description)
    validate_fixed_completion(result.table)
    return result


def multiply(table: Table, left: Sequence[int], right: Sequence[int]) -> Vector:
    if len(left) != DIMENSION or len(right) != DIMENSION:
        raise ValueError("multiplication requires two six-vectors")
    result = [0] * DIMENSION
    for left_index, left_coefficient in enumerate(left):
        if left_coefficient == 0:
            continue
        for right_index, right_coefficient in enumerate(right):
            if right_coefficient == 0:
                continue
            coefficient = left_coefficient * right_coefficient
            for output, structure_constant in enumerate(table[left_index][right_index]):
                result[output] += coefficient * structure_constant
    return tuple(result)


def matrix_from_columns(columns: Sequence[Sequence[int]]) -> Matrix:
    return tuple(
        tuple(columns[column][row] for column in range(DIMENSION))
        for row in range(DIMENSION)
    )


def left_matrix(table: Table, element: Sequence[int]) -> Matrix:
    return matrix_from_columns(tuple(multiply(table, element, basis) for basis in clock.BASIS))


def right_matrix(table: Table, element: Sequence[int]) -> Matrix:
    return matrix_from_columns(tuple(multiply(table, basis, element) for basis in clock.BASIS))


def matrix_column(matrix: Matrix, column: int) -> Vector:
    return tuple(matrix[row][column] for row in range(DIMENSION))


def fixed_cell_stages() -> tuple[dict[str, int], dict[Cell, Vector]]:
    """Reconstruct the fixed cells in dependency order, checking overlaps."""

    fixed: dict[Cell, Vector] = {}
    stage_counts: dict[str, int] = {}

    def install(cell: Cell, value: Sequence[int]) -> None:
        frozen = tuple(value)
        previous = fixed.get(cell)
        if previous is not None and previous != frozen:
            raise AssertionError(f"inconsistent fixed-cell equations at {cell}")
        fixed[cell] = frozen

    for left in range(DIMENSION):
        for right in range(DIMENSION):
            if left == 0 or right == 0 or (left in CORE and right in CORE):
                install((left, right), ORIGIN_TABLE[left][right])
    stage_counts["common_unit_and_A"] = len(fixed)

    for index in range(DIMENSION):
        install((3, index), ORIGIN_TABLE[3][index])
        install((index, 3), ORIGIN_TABLE[index][3])
    stage_counts["fixed_Ls_and_Rs"] = len(fixed)

    left_s = left_matrix(ORIGIN_TABLE, S)
    right_s = right_matrix(ORIGIN_TABLE, S)
    left_h = clock.matrix_power(left_s, 2)
    right_h = clock.matrix_power(right_s, 2)
    for index in range(DIMENSION):
        install((1, index), matrix_column(left_h, index))
        install((index, 1), matrix_column(right_h, index))
    stage_counts["root_squares"] = len(fixed)

    if any(ORIGIN_TABLE[left][right] != value for (left, right), value in fixed.items()):
        raise AssertionError("reconstructed root skeleton differs from the sparse witness")
    if set(FREE_CELLS) != {
        (left, right)
        for left in range(DIMENSION)
        for right in range(DIMENSION)
        if (left, right) not in fixed
    }:
        raise AssertionError("the fixed-cell complement is not the eight-cell seam")
    return stage_counts, fixed


STAGE_COUNTS, FIXED_CELLS = fixed_cell_stages()


def coordinate_index(left: int, right: int, output: int) -> int:
    return (left * DIMENSION + right) * DIMENSION + output


def parity_outputs(cell: Cell) -> frozenset[int]:
    left, right = cell
    left_odd = left in SHADOW
    right_odd = right in SHADOW
    return SHADOW if left_odd != right_odd else CORE


def constraint_rows(parity: bool) -> tuple[tuple[int, ...], ...]:
    """Selector rows for the affine skeleton, optionally with Z/2 grading."""

    variable_count = DIMENSION ** 3
    selected = {
        coordinate_index(left, right, output)
        for left, right in FIXED_CELLS
        for output in range(DIMENSION)
    }
    if parity:
        for cell in FREE_CELLS:
            forbidden = set(range(DIMENSION)).difference(parity_outputs(cell))
            selected.update(coordinate_index(*cell, output) for output in forbidden)
    return tuple(
        tuple(int(column == pivot) for column in range(variable_count))
        for pivot in sorted(selected)
    )


def deformation_dimensions() -> dict[str, object]:
    raw_rows = constraint_rows(False)
    parity_rows = constraint_rows(True)
    raw_rank = len(raw_rows)
    parity_rank = len(parity_rows)
    if len({row.index(1) for row in raw_rows}) != raw_rank:
        raise AssertionError("raw selector constraints are not independent")
    if len({row.index(1) for row in parity_rows}) != parity_rank:
        raise AssertionError("parity selector constraints are not independent")
    return {
        "structure_constants": DIMENSION ** 3,
        "fixed_cells": len(FIXED_CELLS),
        "free_ordered_cells": len(FREE_CELLS),
        "stage_cell_counts": dict(STAGE_COUNTS),
        "raw_constraint_rank": raw_rank,
        "raw_affine_dimension": DIMENSION ** 3 - raw_rank,
        "parity_constraint_rank": parity_rank,
        "parity_affine_dimension": DIMENSION ** 3 - parity_rank,
    }


def validate_fixed_completion(table: Table) -> None:
    for cell, expected in FIXED_CELLS.items():
        if table[cell[0]][cell[1]] != expected:
            raise AssertionError(f"completion changed fixed cell {cell}")
    left_s = left_matrix(table, S)
    right_s = right_matrix(table, S)
    if clock.matrix_power(left_s, 2) != left_matrix(table, H):
        raise AssertionError("L_s^2 != L_h")
    if clock.matrix_power(right_s, 2) != right_matrix(table, H):
        raise AssertionError("R_s^2 != R_h")
    if multiply(table, S, S) != H:
        raise AssertionError("s^2 != h")


def is_parity_preserving(table: Table) -> bool:
    for left in range(DIMENSION):
        for right in range(DIMENSION):
            allowed = parity_outputs((left, right))
            if any(
                coefficient and output not in allowed
                for output, coefficient in enumerate(table[left][right])
            ):
                return False
    return True


def associator(table: Table, left: Vector, middle: Vector, right: Vector) -> Vector:
    return subtract(
        multiply(table, multiply(table, left, middle), right),
        multiply(table, left, multiply(table, middle, right)),
    )


def nucleus_rows(table: Table, slot: int) -> tuple[tuple[int, ...], ...]:
    rows: list[tuple[int, ...]] = []
    for first in clock.BASIS:
        for second in clock.BASIS:
            columns: list[Vector] = []
            for candidate in clock.BASIS:
                arguments: list[Vector | None] = [None, None, None]
                arguments[slot] = candidate
                fixed = iter((first, second))
                for position in range(3):
                    if arguments[position] is None:
                        arguments[position] = next(fixed)
                if any(argument is None for argument in arguments):
                    raise AssertionError("nucleus argument assembly failed")
                left, middle, right = arguments
                assert left is not None and middle is not None and right is not None
                columns.append(associator(table, left, middle, right))
            for output in range(DIMENSION):
                rows.append(tuple(column[output] for column in columns))
    return tuple(rows)


def commutant_rows(table: Table) -> tuple[tuple[int, ...], ...]:
    rows: list[tuple[int, ...]] = []
    for fixed in clock.BASIS:
        columns = tuple(
            subtract(multiply(table, candidate, fixed), multiply(table, fixed, candidate))
            for candidate in clock.BASIS
        )
        for output in range(DIMENSION):
            rows.append(tuple(column[output] for column in columns))
    return tuple(rows)


def derivation_rows(table: Table) -> tuple[tuple[int, ...], ...]:
    rows: list[tuple[int, ...]] = []
    unknowns = DIMENSION * DIMENSION
    for left_index, left in enumerate(clock.BASIS):
        for right_index, right in enumerate(clock.BASIS):
            product_value = multiply(table, left, right)
            for output in range(DIMENSION):
                row = [0] * unknowns
                for input_index, coefficient in enumerate(product_value):
                    row[output * DIMENSION + input_index] += coefficient
                for image_index, image_basis in enumerate(clock.BASIS):
                    row[image_index * DIMENSION + left_index] -= multiply(
                        table, image_basis, right
                    )[output]
                    row[image_index * DIMENSION + right_index] -= multiply(
                        table, left, image_basis
                    )[output]
                rows.append(tuple(row))
    return tuple(rows)


def structural_metrics(table: Table) -> dict[str, object]:
    nuclei = tuple(nucleus_rows(table, slot) for slot in range(3))
    commutant = commutant_rows(table)
    center_rows = commutant + tuple(row for rows in nuclei for row in rows)
    associators = tuple(
        associator(table, left, middle, right)
        for left in clock.BASIS
        for middle in clock.BASIS
        for right in clock.BASIS
    )
    associator_matrix = tuple(
        tuple(value[output] for value in associators) for output in range(DIMENSION)
    )
    return {
        "nucleus_dimensions": [DIMENSION - clock.matrix_rank(rows) for rows in nuclei],
        "commutant_dimension": DIMENSION - clock.matrix_rank(commutant),
        "center_dimension": DIMENSION - clock.matrix_rank(center_rows),
        "associator_image_rank": clock.matrix_rank(associator_matrix),
        "derivation_dimension": DIMENSION * DIMENSION - clock.matrix_rank(derivation_rows(table)),
    }


def repeated_s_ecology(table: Table, max_leaves: int) -> tuple[Counter[Vector], ...]:
    if not 1 <= max_leaves <= 12:
        raise ValueError("deformation ecology is bounded at 12 leaves")
    counts: list[Counter[Vector]] = [Counter(), Counter({S: 1})]
    for leaves in range(2, max_leaves + 1):
        current: Counter[Vector] = Counter()
        for left_leaves in range(1, leaves):
            right_leaves = leaves - left_leaves
            for left, left_count in counts[left_leaves].items():
                for right, right_count in counts[right_leaves].items():
                    current[multiply(table, left, right)] += left_count * right_count
        if sum(current.values()) != clock.catalan(leaves - 1):
            raise AssertionError("deformed ecology lost a Catalan tree")
        counts.append(current)
    return tuple(counts)


def histogram(counter: Counter[Vector]) -> dict[str, int]:
    return {
        clock.vector_label(vector): counter[vector]
        for vector in sorted(counter)
    }


def first_ecology_difference(left: Table, right: Table, max_leaves: int) -> int | None:
    left_counts = repeated_s_ecology(left, max_leaves)
    right_counts = repeated_s_ecology(right, max_leaves)
    return next(
        (leaves for leaves in range(1, max_leaves + 1) if left_counts[leaves] != right_counts[leaves]),
        None,
    )


def comb_sequences(table: Table, length: int) -> dict[str, list[str]]:
    left = S
    right = S
    left_values = [clock.vector_label(left)]
    right_values = [clock.vector_label(right)]
    for _ in range(2, length + 1):
        left = multiply(table, left, S)
        right = multiply(table, S, right)
        left_values.append(clock.vector_label(left))
        right_values.append(clock.vector_label(right))
    return {"left": left_values, "right": right_values}


ORIGIN = Completion("origin", ORIGIN_TABLE, "the sparse zero-seam witness")
TT_ONE = completion(
    "tt_one",
    {(4, 4): ONE},
    "parity-preserving t*t=1; moves the first four balanced n=6 trees",
)
QT_S = completion(
    "qt_s",
    {(2, 4): S},
    "parity-preserving q*t=s; destroys the sparse extra commutant direction",
)
NAMED_COMPLETIONS: Mapping[str, Completion] = {
    witness.name: witness for witness in (ORIGIN, TT_ONE, QT_S)
}


def seam_witnesses() -> tuple[Completion, ...]:
    values: Mapping[Cell, Vector] = {
        (2, 4): S,
        (2, 5): S,
        (4, 2): S,
        (4, 4): ONE,
        (4, 5): ONE,
        (5, 2): S,
        (5, 4): ONE,
        (5, 5): ONE,
    }
    return tuple(
        completion(
            f"{LABELS[left]}{LABELS[right]}",
            {(left, right): values[(left, right)]},
            f"isolated parity seam {LABELS[left]}*{LABELS[right]}={clock.vector_label(values[(left, right)])}",
        )
        for left, right in FREE_CELLS
    )


def fixed_operator_report() -> dict[str, object]:
    left_s = left_matrix(ORIGIN_TABLE, S)
    right_s = right_matrix(ORIGIN_TABLE, S)
    left_h = left_matrix(ORIGIN_TABLE, H)
    right_h = right_matrix(ORIGIN_TABLE, H)
    group_words, depth_profile = clock.enumerate_clock_group()
    return {
        "orders": {
            "L_s": clock.action_order(clock.signed_action(left_s)),
            "R_s": clock.action_order(clock.signed_action(right_s)),
            "L_h": clock.action_order(clock.signed_action(left_h)),
            "R_h": clock.action_order(clock.signed_action(right_h)),
        },
        "determinants": {
            "L_s": clock.determinant(left_s),
            "R_s": clock.determinant(right_s),
            "L_h": clock.determinant(left_h),
            "R_h": clock.determinant(right_h),
        },
        "clock_group_order": len(group_words),
        "clock_group_depth_profile": list(depth_profile),
        "clock_group_maximum_depth": max(map(len, group_words.values())),
    }


def skew_tail_strong_root_witness() -> Table:
    """A six-dimensional strong root outside the fixed-clock affine fiber.

    It keeps L_s equal to the sparse clock but takes q*s=u+s and
    u*s=-1-h.  Thus strong roots and dimension six do not force s*q=q*s.
    """

    table = [[ZERO for _ in range(DIMENSION)] for _ in range(DIMENSION)]

    def install(cell: Cell, value: Sequence[int]) -> None:
        frozen = tuple(value)
        previous = table[cell[0]][cell[1]]
        if previous != ZERO and previous != frozen:
            raise AssertionError(f"skew-tail equations conflict at {cell}")
        table[cell[0]][cell[1]] = frozen

    for index, basis in enumerate(clock.BASIS):
        install((0, index), basis)
        install((index, 0), basis)
    for left in CORE:
        for right in CORE:
            install((left, right), ORIGIN_TABLE[left][right])

    left_images = (S, T, U, H, Q, ONE)
    right_images = (S, T, add(U, S), H, Q, negate(add(ONE, H)))
    for index in range(DIMENSION):
        install((3, index), left_images[index])
        install((index, 3), right_images[index])

    left_s = matrix_from_columns(left_images)
    right_s = matrix_from_columns(right_images)
    left_h = clock.matrix_power(left_s, 2)
    right_h = clock.matrix_power(right_s, 2)
    for index in range(DIMENSION):
        install((1, index), matrix_column(left_h, index))
        install((index, 1), matrix_column(right_h, index))

    result = freeze(table)
    if clock.matrix_power(left_matrix(result, S), 2) != left_matrix(result, H):
        raise AssertionError("skew-tail L_s root identity failed")
    if clock.matrix_power(right_matrix(result, S), 2) != right_matrix(result, H):
        raise AssertionError("skew-tail R_s root identity failed")
    if multiply(result, S, Q) == multiply(result, Q, S):
        raise AssertionError("skew-tail witness accidentally identified the two tails")
    return result


def completion_report(witness: Completion, max_leaves: int) -> dict[str, object]:
    origin_counts = repeated_s_ecology(ORIGIN_TABLE, max_leaves)
    witness_counts = repeated_s_ecology(witness.table, max_leaves)
    first = next(
        (leaves for leaves in range(1, max_leaves + 1) if origin_counts[leaves] != witness_counts[leaves]),
        None,
    )
    return {
        "name": witness.name,
        "description": witness.description,
        "parity_preserving": is_parity_preserving(witness.table),
        "structure": structural_metrics(witness.table),
        "first_repeated_s_difference_from_origin": first,
        "degree_6_histogram": histogram(witness_counts[6]) if max_leaves >= 6 else None,
        "comb_sequences": comb_sequences(witness.table, min(max_leaves, 12)),
    }


def elementary_scan() -> dict[str, object]:
    profiles: Counter[tuple[object, ...]] = Counter()
    parity_count = 0
    for cell in FREE_CELLS:
        for output, basis in enumerate(clock.BASIS):
            witness = completion(
                f"scan_{cell[0]}_{cell[1]}_{output}",
                {cell: basis},
                "elementary coordinate probe",
            )
            metrics = structural_metrics(witness.table)
            profile = (
                tuple(metrics["nucleus_dimensions"]),
                metrics["commutant_dimension"],
                metrics["center_dimension"],
                metrics["associator_image_rank"],
                metrics["derivation_dimension"],
            )
            profiles[profile] += 1
            if output in parity_outputs(cell):
                parity_count += 1
    return {
        "elementary_completions": len(FREE_CELLS) * DIMENSION,
        "parity_elementary_completions": parity_count,
        "profiles": [
            {
                "nuclei": list(profile[0]),
                "commutant": profile[1],
                "center": profile[2],
                "associator_rank": profile[3],
                "Der": profile[4],
                "count": count,
            }
            for profile, count in sorted(profiles.items(), key=lambda item: repr(item[0]))
        ],
        "scope": "finite coordinate probes, not a proof over the whole affine family",
    }


def build_report() -> dict[str, object]:
    dimensions = deformation_dimensions()
    operator = fixed_operator_report()
    seam = []
    for cell, witness in zip(FREE_CELLS, seam_witnesses(), strict=True):
        first = first_ecology_difference(ORIGIN_TABLE, witness.table, 10)
        seam.append(
            {
                "cell": f"{LABELS[cell[0]]}*{LABELS[cell[1]]}",
                "first_repeated_s_degree": first,
                "expected_degree": EXPECTED_FIRST_SEAM_DEGREE[cell],
            }
        )

    skew = skew_tail_strong_root_witness()
    return {
        "model": "fixed-shadow-clock affine completion family",
        "scope": {
            "fixed": "chosen basis, common-unit A, and the literal L_s/R_s clock of shadow_root_clock.py",
            "not_classified": "all six-dimensional strong-root extensions",
            "reason": "strong-root axioms force s*h=h*s=t but do not force s*q=q*s",
            "broader_canonical_family": {
                "companion": "shadow_root_seams.py / SHADOW_ROOT_SEAMS.md",
                "raw_table_dimension": 54,
                "parity_table_dimension": 27,
                "this_slice": "the symmetric a=s*q=u, d=s*u=1 clock seam; 48D raw / 24D parity",
            },
            "skew_tail_witness": {
                "s*q": clock.vector_label(multiply(skew, S, Q)),
                "q*s": clock.vector_label(multiply(skew, Q, S)),
                "root_identities_hold": True,
                "parity_preserving": is_parity_preserving(skew),
            },
        },
        "dimensions": dimensions,
        "free_cells": [f"{LABELS[left]}*{LABELS[right]}" for left, right in FREE_CELLS],
        "parity": {
            "even": ["1", "h", "q"],
            "odd": ["s", "t", "u"],
            "dimension": dimensions["parity_affine_dimension"],
        },
        "family_wide_operator_invariants": operator,
        "named_completions": [
            completion_report(witness, 10) for witness in NAMED_COMPLETIONS.values()
        ],
        "degree_6_law": "19[-1] + 19[+1] + 4[t*t]",
        "free_seam_visibility": seam,
        "rank_stratification": {
            "proved": (
                "origin has maximal nucleus/center/derivation/associator constraint ranks; "
                "therefore its nuclei=(1,1,1), center=1, associator-rank=6, and Der=0 "
                "persist on a nonempty Zariski-open neighborhood"
            ),
            "not_proved": "those ranks are constant on every point of the 48D or 24D family",
            "completion_sensitive_witness": "q*t=s changes commutant dimension from 2 to 1",
        },
    }


def print_report(report: Mapping[str, object]) -> None:
    dimensions = report["dimensions"]
    operators = report["family_wide_operator_invariants"]
    scope = report["scope"]
    assert isinstance(dimensions, dict) and isinstance(operators, dict) and isinstance(scope, dict)
    print("SHADOW ROOT DEFORMATION SPACE")
    print("scope        : fixed literal L_s/R_s skeleton; not all minimal roots")
    print(
        "cells/rank/dim: {}/{} / {}D raw; rank {} / {}D parity".format(
            dimensions["free_ordered_cells"],
            dimensions["raw_constraint_rank"],
            dimensions["raw_affine_dimension"],
            dimensions["parity_constraint_rank"],
            dimensions["parity_affine_dimension"],
        )
    )
    print("free seam    : " + ", ".join(report["free_cells"]))
    print(
        "fixed clock  : orders {}; group {} states".format(
            operators["orders"], operators["clock_group_order"]
        )
    )
    skew = scope["skew_tail_witness"]
    assert isinstance(skew, dict)
    print(f"scope witness: s*q={skew['s*q']}, q*s={skew['q*s']}; roots still exact")
    broader = scope["broader_canonical_family"]
    assert isinstance(broader, dict)
    print(
        "broader seam : {}D raw / {}D parity; this is the symmetric fixed-clock slice".format(
            broader["raw_table_dimension"], broader["parity_table_dimension"]
        )
    )

    print("\nNAMED COMPLETIONS")
    for witness in report["named_completions"]:
        assert isinstance(witness, dict)
        structure = witness["structure"]
        assert isinstance(structure, dict)
        print(
            "{:<7} parity={} nuclei={} Comm={} Der={} first-s={}".format(
                witness["name"],
                witness["parity_preserving"],
                structure["nucleus_dimensions"],
                structure["commutant_dimension"],
                structure["derivation_dimension"],
                witness["first_repeated_s_difference_from_origin"],
            )
        )
        if witness["degree_6_histogram"] is not None:
            print("         n=6 " + str(witness["degree_6_histogram"]))

    print("\nSEAM VISIBILITY")
    print("  " + ", ".join(
        f"{row['cell']}@n={row['first_repeated_s_degree']}"
        for row in report["free_seam_visibility"]
    ))
    print("degree-6 law: " + report["degree_6_law"])
    print("rank boundary: nuclei/Der are open-stratum stable here; global constancy not claimed")


def print_completion_report(report: Mapping[str, object]) -> None:
    structure = report["structure"]
    combs = report["comb_sequences"]
    assert isinstance(structure, dict) and isinstance(combs, dict)
    print("SHADOW ROOT COMPLETION / " + str(report["name"]))
    print("description : " + str(report["description"]))
    print("parity      : " + str(report["parity_preserving"]))
    print("structure   : " + str(structure))
    print("first delta : " + str(report["first_repeated_s_difference_from_origin"]))
    print("n=6         : " + str(report["degree_6_histogram"]))
    print("left comb   : " + " -> ".join(combs["left"]))
    print("right comb  : " + " -> ".join(combs["right"]))


def run_self_tests(deep: bool) -> None:
    dimensions = deformation_dimensions()
    assert STAGE_COUNTS == {
        "common_unit_and_A": 15,
        "fixed_Ls_and_Rs": 24,
        "root_squares": 28,
    }
    assert dimensions["raw_constraint_rank"] == 168
    assert dimensions["raw_affine_dimension"] == 48
    assert dimensions["parity_constraint_rank"] == 192
    assert dimensions["parity_affine_dimension"] == 24
    assert clock.matrix_rank(constraint_rows(False)) == 168
    assert clock.matrix_rank(constraint_rows(True)) == 192

    for witness in NAMED_COMPLETIONS.values():
        validate_fixed_completion(witness.table)
        assert left_matrix(witness.table, S) == left_matrix(ORIGIN_TABLE, S)
        assert right_matrix(witness.table, S) == right_matrix(ORIGIN_TABLE, S)
        assert left_matrix(witness.table, H) == left_matrix(ORIGIN_TABLE, H)
        assert right_matrix(witness.table, H) == right_matrix(ORIGIN_TABLE, H)
        assert is_parity_preserving(witness.table)

    operators = fixed_operator_report()
    assert operators["orders"] == {"L_s": 6, "R_s": 12, "L_h": 3, "R_h": 6}
    assert operators["clock_group_order"] == 384
    assert operators["clock_group_maximum_depth"] == 11

    origin_counts = repeated_s_ecology(ORIGIN_TABLE, 10)
    tt_counts = repeated_s_ecology(TT_ONE.table, 10)
    assert histogram(origin_counts[6]) == {"-1": 19, "0": 4, "1": 19}
    assert histogram(tt_counts[6]) == {"-1": 19, "1": 23}
    assert first_ecology_difference(ORIGIN_TABLE, TT_ONE.table, 10) == 6
    arbitrary_tt = (2, -1, 3, 4, -2, 1)
    arbitrary = completion(
        "arbitrary_tt",
        {(4, 4): arbitrary_tt},
        "exact degree-six measure-law probe",
    )
    expected_degree_6: Counter[Vector] = Counter()
    expected_degree_6[ONE] += 19
    expected_degree_6[negate(ONE)] += 19
    expected_degree_6[arbitrary_tt] += 4
    assert repeated_s_ecology(arbitrary.table, 6)[6] == expected_degree_6
    assert structural_metrics(ORIGIN_TABLE) == {
        "nucleus_dimensions": [1, 1, 1],
        "commutant_dimension": 2,
        "center_dimension": 1,
        "associator_image_rank": 6,
        "derivation_dimension": 0,
    }
    assert structural_metrics(QT_S.table) == {
        "nucleus_dimensions": [1, 1, 1],
        "commutant_dimension": 1,
        "center_dimension": 1,
        "associator_image_rank": 6,
        "derivation_dimension": 0,
    }

    origin_combs = comb_sequences(ORIGIN_TABLE, 12)
    for witness in seam_witnesses():
        assert comb_sequences(witness.table, 12) == origin_combs
    for cell, witness in zip(FREE_CELLS, seam_witnesses(), strict=True):
        assert first_ecology_difference(ORIGIN_TABLE, witness.table, 10) == EXPECTED_FIRST_SEAM_DEGREE[cell]

    skew = skew_tail_strong_root_witness()
    assert multiply(skew, S, Q) == U
    assert multiply(skew, Q, S) == add(U, S)
    assert is_parity_preserving(skew)

    dense = completion(
        "dense_ungraded",
        {
            cell: tuple((cell_index + 1) * (output + 1) for output in range(DIMENSION))
            for cell_index, cell in enumerate(FREE_CELLS)
        },
        "one point using every raw affine coordinate direction",
    )
    assert not is_parity_preserving(dense.table)
    assert left_matrix(dense.table, S) == left_matrix(ORIGIN_TABLE, S)
    assert right_matrix(dense.table, S) == right_matrix(ORIGIN_TABLE, S)

    scan: dict[str, object] | None = None
    if deep:
        scan = elementary_scan()
        assert scan["elementary_completions"] == 48
        assert scan["parity_elementary_completions"] == 24
        assert scan["profiles"] == [
            {
                "nuclei": [1, 1, 1],
                "commutant": 1,
                "center": 1,
                "associator_rank": 6,
                "Der": 0,
                "count": 22,
            },
            {
                "nuclei": [1, 1, 1],
                "commutant": 2,
                "center": 1,
                "associator_rank": 6,
                "Der": 0,
                "count": 26,
            },
        ]

    print("SELF-TEST PASS")
    print("affine dimensions      : 48 raw; 24 parity")
    print("fixed ordered cells    : 28 of 36")
    print("operator skeleton      : roots/orders/384-group invariant")
    print("degree-6 deformation   : 19[-1] + 19[+1] + 4[t*t]")
    print("commutant witness      : q*t=s moves dimension 2 -> 1")
    print("scope counterwitness   : s*q=u, q*s=u+s with both roots exact")
    print(f"elementary rank scan   : {scan['elementary_completions'] if scan else 'use --deep'}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Exact affine deformations of the fixed six-dimensional shadow clock.",
        epilog="With no command, print the deterministic deformation expedition.",
    )
    subparsers = parser.add_subparsers(dest="command")
    report = subparsers.add_parser("report", help="print the affine family ledger")
    report.add_argument("--json", action="store_true")

    analyze = subparsers.add_parser("analyze", help="inspect one named completion")
    analyze.add_argument("name", choices=tuple(NAMED_COMPLETIONS))
    analyze.add_argument("--max-leaves", type=int, default=10)
    analyze.add_argument("--json", action="store_true")

    test = subparsers.add_parser("test", help="run exact self-tests")
    test.add_argument("--deep", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "test":
            run_self_tests(args.deep)
        elif args.command == "analyze":
            if not 1 <= args.max_leaves <= 12:
                raise ValueError("--max-leaves must be between 1 and 12")
            report = completion_report(NAMED_COMPLETIONS[args.name], args.max_leaves)
            if args.json:
                print(json.dumps(report, indent=2, sort_keys=True))
            else:
                print_completion_report(report)
        else:
            report = build_report()
            if args.command == "report" and args.json:
                print(json.dumps(report, indent=2, sort_keys=True))
            else:
                print_report(report)
    except ValueError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
