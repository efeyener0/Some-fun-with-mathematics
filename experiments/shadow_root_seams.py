#!/usr/bin/env python3
"""Exact seam atlas for minimal six-dimensional strong shadow roots.

Let A=span(1,h,q) with h*h=q, h*q=1, q*h=-1, q*q=q.  In a
six-dimensional real unital extension with an element s satisfying

    s*s=h,  L_s^2=L_h,  R_s^2=R_h,

the five vectors (1,s,h,t=sh=hs,q) are independent.  Taking u=q*s as the
sixth basis vector fixes R_s as a negative six-cycle.  This module classifies
the remaining root seam a=s*q and d=s*u, constructs exact rational example
algebras, and measures their repeated-s Catalan ecology.

The classification concerns the root-operator skeleton.  The eight products
among q,t,u not already fixed by the skeleton remain arbitrary B-valued
completion cells; setting them to zero below merely selects sparse witnesses.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from fractions import Fraction
from math import comb
from typing import Iterable, Mapping, Sequence


DIMENSION = 6
BASIS_LABELS = ("1", "s", "h", "t", "q", "u")
ONE_INDEX, S_INDEX, H_INDEX, T_INDEX, Q_INDEX, U_INDEX = range(DIMENSION)
DEFAULT_MAX_LEAVES = 10
MAX_LEAVES = 18

Scalar = Fraction
Vector = tuple[Scalar, ...]
Matrix = tuple[tuple[Scalar, ...], ...]
Table = tuple[tuple[Vector, ...], ...]


def scalar(value: int | Fraction) -> Fraction:
    return value if isinstance(value, Fraction) else Fraction(value)


def vector(values: Iterable[int | Fraction]) -> Vector:
    result = tuple(scalar(value) for value in values)
    if len(result) != DIMENSION:
        raise ValueError(f"expected {DIMENSION} coordinates, got {len(result)}")
    return result


def basis_vector(index: int) -> Vector:
    return tuple(Fraction(int(position == index)) for position in range(DIMENSION))


BASIS = tuple(basis_vector(index) for index in range(DIMENSION))
ONE, S, H, T, Q, U = BASIS
ZERO = vector((0,) * DIMENSION)


def add(left: Sequence[Fraction], right: Sequence[Fraction]) -> Vector:
    return tuple(a + b for a, b in zip(left, right, strict=True))


def scale(coefficient: Fraction, value: Sequence[Fraction]) -> Vector:
    return tuple(coefficient * coordinate for coordinate in value)


def linear_combination(terms: Iterable[tuple[Fraction, Sequence[Fraction]]]) -> Vector:
    result = ZERO
    for coefficient, value in terms:
        result = add(result, scale(coefficient, value))
    return result


def matrix_from_columns(columns: Sequence[Sequence[Fraction]]) -> Matrix:
    if len(columns) != DIMENSION:
        raise ValueError("a root operator must have six columns")
    return tuple(
        tuple(scalar(columns[column][row]) for column in range(DIMENSION))
        for row in range(DIMENSION)
    )


def matrix_vector(matrix: Sequence[Sequence[Fraction]], value: Sequence[Fraction]) -> Vector:
    return tuple(
        sum((scalar(entry) * scalar(coordinate) for entry, coordinate in zip(row, value, strict=True)), Fraction())
        for row in matrix
    )


def matrix_multiply(left: Matrix, right: Matrix) -> Matrix:
    columns = tuple(tuple(right[row][column] for row in range(DIMENSION)) for column in range(DIMENSION))
    return matrix_from_columns(tuple(matrix_vector(left, column) for column in columns))


def generic_seam(a: Sequence[int | Fraction]) -> tuple[Vector, Vector]:
    """Return (a=s*q, d=s*u) on the open branch a_u != 0."""

    seam = vector(a)
    if seam[U_INDEX] == 0:
        raise ValueError("generic seam requires a nonzero u-coordinate")
    numerator = linear_combination(
        (
            (Fraction(1), ONE),
            (-seam[ONE_INDEX], S),
            (-seam[S_INDEX], H),
            (-seam[H_INDEX], T),
            (-seam[T_INDEX], Q),
            (-seam[Q_INDEX], seam),
        )
    )
    return seam, scale(Fraction(1, 1) / seam[U_INDEX], numerator)


def exceptional_seam(sign: int, d: Sequence[int | Fraction] = ZERO) -> tuple[Vector, Vector]:
    """Return one of the two real a_u=0 branches and arbitrary d=s*u."""

    if sign == 1:
        seam = vector((1, -1, 1, -1, 1, 0))
    elif sign == -1:
        seam = vector((-1, -1, -1, -1, -1, 0))
    else:
        raise ValueError("exceptional sign must be +1 or -1")
    return seam, vector(d)


def left_root_matrix(a: Vector, d: Vector) -> Matrix:
    return matrix_from_columns((S, H, T, Q, a, d))


def right_root_matrix() -> Matrix:
    return matrix_from_columns((S, H, T, Q, U, scale(Fraction(-1), ONE)))


RIGHT_ROOT = right_root_matrix()


def root_residual(a: Vector, d: Vector) -> Vector:
    """Return L_s(a)-1; a valid seam makes this vector zero."""

    return add(matrix_vector(left_root_matrix(a, d), a), scale(Fraction(-1), ONE))


def is_parity_preserving(a: Vector, d: Vector) -> bool:
    even = (ONE_INDEX, H_INDEX, Q_INDEX)
    odd = (S_INDEX, T_INDEX, U_INDEX)
    return all(a[index] == 0 for index in even) and all(d[index] == 0 for index in odd)


def build_sparse_table(a: Vector, d: Vector, tt: Vector = ZERO) -> Table:
    """Build the sparse completion selected by a valid root seam.

    The only optional completion cell exposed here is t*t, because it is the
    first free cell seen by repeated-s trees (at degree six).  All seven other
    free cells are zero.
    """

    if root_residual(a, d) != ZERO:
        raise ValueError("invalid seam: L_s(s*q) must equal 1")

    cells = [[ZERO for _ in range(DIMENSION)] for _ in range(DIMENSION)]
    for index in range(DIMENSION):
        cells[ONE_INDEX][index] = BASIS[index]
        cells[index][ONE_INDEX] = BASIS[index]

    # Source algebra A in chain coordinates (1,h,q)=(e0,e2,e4).
    cells[H_INDEX][H_INDEX] = Q
    cells[H_INDEX][Q_INDEX] = ONE
    cells[Q_INDEX][H_INDEX] = scale(Fraction(-1), ONE)
    cells[Q_INDEX][Q_INDEX] = Q

    left = left_root_matrix(a, d)
    right = RIGHT_ROOT
    left_squared = matrix_multiply(left, left)
    right_squared = matrix_multiply(right, right)

    for index in range(DIMENSION):
        left_column = tuple(left[row][index] for row in range(DIMENSION))
        right_column = tuple(right[row][index] for row in range(DIMENSION))
        h_left_column = tuple(left_squared[row][index] for row in range(DIMENSION))
        h_right_column = tuple(right_squared[row][index] for row in range(DIMENSION))
        cells[S_INDEX][index] = left_column
        cells[index][S_INDEX] = right_column
        cells[H_INDEX][index] = h_left_column
        cells[index][H_INDEX] = h_right_column

    cells[T_INDEX][T_INDEX] = vector(tt)
    return tuple(tuple(row) for row in cells)


def multiply(table: Table, left: Sequence[Fraction], right: Sequence[Fraction]) -> Vector:
    result = ZERO
    for left_index, left_coefficient in enumerate(left):
        if left_coefficient == 0:
            continue
        for right_index, right_coefficient in enumerate(right):
            if right_coefficient == 0:
                continue
            result = add(
                result,
                scale(left_coefficient * right_coefficient, table[left_index][right_index]),
            )
    return result


def operator_from_table(table: Table, left: bool, index: int) -> Matrix:
    columns = tuple(
        table[index][column] if left else table[column][index]
        for column in range(DIMENSION)
    )
    return matrix_from_columns(columns)


def catalan(index: int) -> int:
    return comb(2 * index, index) // (index + 1)


def repeated_s_ecology(table: Table, max_leaves: int) -> tuple[Counter[Vector], ...]:
    states: list[Counter[Vector]] = [Counter(), Counter({S: 1})]
    for leaves in range(2, max_leaves + 1):
        current: Counter[Vector] = Counter()
        for left_leaves in range(1, leaves):
            right_leaves = leaves - left_leaves
            for left_value, left_count in states[left_leaves].items():
                for right_value, right_count in states[right_leaves].items():
                    current[multiply(table, left_value, right_value)] += left_count * right_count
        states.append(current)
    return tuple(states)


def fraction_text(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def vector_text(value: Sequence[Fraction]) -> str:
    terms: list[str] = []
    for coefficient, label in zip(value, BASIS_LABELS, strict=True):
        if coefficient == 0:
            continue
        magnitude = abs(coefficient)
        body = label if magnitude == 1 else f"{fraction_text(magnitude)}*{label}"
        if not terms:
            terms.append(f"-{body}" if coefficient < 0 else body)
        else:
            terms.append(f"{'-' if coefficient < 0 else '+'}{body}")
    return "".join(terms) or "0"


def vector_json(value: Sequence[Fraction]) -> list[str]:
    return [fraction_text(scalar(coordinate)) for coordinate in value]


def ecology_report(ecology: Sequence[Counter[Vector]]) -> list[dict[str, object]]:
    report: list[dict[str, object]] = []
    for leaves in range(1, len(ecology)):
        histogram = ecology[leaves]
        report.append(
            {
                "leaves": leaves,
                "trees": sum(histogram.values()),
                "distinct_values": len(histogram),
                "histogram": [
                    {"value": vector_text(value), "count": count}
                    for value, count in sorted(histogram.items(), key=lambda item: vector_text(item[0]))
                ],
            }
        )
    return report


def examples() -> Mapping[str, tuple[Vector, Vector, Vector]]:
    clock_a, clock_d = generic_seam((0, 0, 0, 0, 0, 1))
    parity_a, parity_d = generic_seam((0, 1, 0, -1, 0, 2))
    generic_a, generic_d = generic_seam((1, -1, 2, 0, 1, 2))
    plus_a, plus_d = exceptional_seam(1)
    minus_a, minus_d = exceptional_seam(-1)
    return {
        "clock": (clock_a, clock_d, ZERO),
        "parity": (parity_a, parity_d, ZERO),
        "generic": (generic_a, generic_d, ZERO),
        "exceptional-plus": (plus_a, plus_d, ZERO),
        "exceptional-minus": (minus_a, minus_d, ZERO),
        "clock-tt-one": (clock_a, clock_d, ONE),
    }


def build_report(name: str, max_leaves: int) -> dict[str, object]:
    try:
        a, d, tt = examples()[name]
    except KeyError as error:
        raise ValueError(f"unknown example {name!r}") from error
    table = build_sparse_table(a, d, tt)
    ecology = repeated_s_ecology(table, max_leaves)
    payload: dict[str, object] = {
        "basis": list(BASIS_LABELS),
        "example": name,
        "seam": {
            "a_equals_u": a == U,
            "a_s_q": vector_json(a),
            "d_s_u": vector_json(d),
            "t_t": vector_json(tt),
            "parity_preserving": is_parity_preserving(a, d) and all(tt[index] == 0 for index in (S_INDEX, T_INDEX, U_INDEX)),
        },
        "classification": {
            "generic_branch": "a_u != 0: a is arbitrary and d is uniquely forced by L_s(a)=1",
            "exceptional_branch": "a_u = 0: exactly two real a vectors; d is arbitrary",
            "generic_root_skeleton_dimension": 6,
            "free_completion_cells": 8,
            "ungraded_completion_dimension": 48,
            "generic_total_parameter_dimension": 54,
            "parity_root_skeleton_dimension": 3,
            "parity_completion_dimension": 24,
            "parity_total_parameter_dimension": 27,
            "scope": "root skeleton plus completion family in the canonical basis u=q*s; not an isomorphism classification",
        },
        "ecology": ecology_report(ecology),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["fingerprint_sha256"] = hashlib.sha256(encoded).hexdigest()
    return payload


def assert_matrix_equal(left: Matrix, right: Matrix, message: str) -> None:
    if left != right:
        raise AssertionError(message)


def validate_table(a: Vector, d: Vector, tt: Vector = ZERO) -> None:
    table = build_sparse_table(a, d, tt)
    left_s = operator_from_table(table, True, S_INDEX)
    right_s = operator_from_table(table, False, S_INDEX)
    left_h = operator_from_table(table, True, H_INDEX)
    right_h = operator_from_table(table, False, H_INDEX)
    assert table[S_INDEX][S_INDEX] == H
    assert table[H_INDEX][H_INDEX] == Q
    assert table[H_INDEX][Q_INDEX] == ONE
    assert table[Q_INDEX][H_INDEX] == scale(Fraction(-1), ONE)
    assert table[Q_INDEX][Q_INDEX] == Q
    assert_matrix_equal(matrix_multiply(left_s, left_s), left_h, "L_s^2 != L_h")
    assert_matrix_equal(matrix_multiply(right_s, right_s), right_h, "R_s^2 != R_h")


def validate_clock_against_original() -> None:
    try:
        import shadow_root_clock as original
    except ImportError as error:  # pragma: no cover - only relevant outside this directory
        raise AssertionError("shadow_root_clock.py must be importable for cross-check") from error

    a, d, tt = examples()["clock"]
    table = build_sparse_table(a, d, tt)
    # Chain basis (1,s,h,t,q,u) corresponds to original indices (1,s,h,t,q,u).
    original_indices = (0, 3, 1, 4, 2, 5)
    inverse = {old: new for new, old in enumerate(original_indices)}
    for left_new, left_old in enumerate(original_indices):
        for right_new, right_old in enumerate(original_indices):
            code = original.PRODUCT_CODES[left_old][right_old]
            expected = ZERO
            if code:
                sign = Fraction(1 if code > 0 else -1)
                expected = scale(sign, BASIS[inverse[abs(code) - 1]])
            if table[left_new][right_new] != expected:
                raise AssertionError(
                    f"clock table mismatch at {BASIS_LABELS[left_new]}*{BASIS_LABELS[right_new]}"
                )


def validate_fifth_degree_seam_law(a: Vector, d: Vector) -> None:
    table = build_sparse_table(a, d)
    ecology = repeated_s_ecology(table, 5)
    expected: Counter[Vector] = Counter()
    expected[a] += 7
    expected[U] += 7
    if ecology[5] != expected:
        raise AssertionError(f"degree-five seam law failed: {ecology[5]!r} != {expected!r}")


def run_self_tests(deep: bool) -> None:
    for a, d, tt in examples().values():
        validate_table(a, d, tt)
        validate_fifth_degree_seam_law(a, d)

    validate_clock_against_original()

    clock_a, clock_d, _ = examples()["clock"]
    clock_ecology = repeated_s_ecology(build_sparse_table(clock_a, clock_d), 6)
    assert clock_ecology[5] == Counter({U: 14})
    assert sorted(clock_ecology[6].values()) == [4, 19, 19]

    plus_a, _ = exceptional_seam(1)
    minus_a, _ = exceptional_seam(-1)
    assert root_residual(plus_a, ZERO) == ZERO
    assert root_residual(minus_a, ZERO) == ZERO

    if deep:
        coefficients = (-1, 0, 1)
        for c0 in coefficients:
            for c1 in coefficients:
                for c2 in coefficients:
                    for c3 in coefficients:
                        for c4 in coefficients:
                            for c5 in (-2, -1, 1, 2):
                                a, d = generic_seam((c0, c1, c2, c3, c4, c5))
                                validate_table(a, d)

        trial_d = (ZERO,) + tuple(BASIS) + tuple(scale(Fraction(-1), item) for item in BASIS)
        for sign in (-1, 1):
            for d in trial_d:
                a, chosen_d = exceptional_seam(sign, d)
                validate_table(a, chosen_d)

        for name, (a, d, tt) in examples().items():
            ecology = repeated_s_ecology(build_sparse_table(a, d, tt), 12)
            for leaves in range(1, 13):
                if sum(ecology[leaves].values()) != catalan(leaves - 1):
                    raise AssertionError(f"Catalan ledger failed for {name} at n={leaves}")


def print_human(report: Mapping[str, object]) -> None:
    seam = report["seam"]
    assert isinstance(seam, Mapping)
    print("Shadow Root Seam Atlas")
    print(f"example: {report['example']}")
    print(f"basis: {', '.join(report['basis'])}")
    print(f"s*q: {vector_text(vector(Fraction(item) for item in seam['a_s_q']))}")
    print(f"s*u: {vector_text(vector(Fraction(item) for item in seam['d_s_u']))}")
    print(f"s*q == q*s: {seam['a_equals_u']}")
    print(f"parity preserving: {seam['parity_preserving']}")
    print("ecology:")
    for row in report["ecology"]:
        histogram = ", ".join(f"{item['value']}:{item['count']}" for item in row["histogram"])
        print(f"  n={row['leaves']:2d} C={row['trees']:6d} values={row['distinct_values']:3d}  {histogram}")
    print(f"fingerprint: {report['fingerprint_sha256']}")


def bounded_leaves(value: str) -> int:
    parsed = int(value)
    if not 1 <= parsed <= MAX_LEAVES:
        raise argparse.ArgumentTypeError(f"max leaves must be between 1 and {MAX_LEAVES}")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.set_defaults(example="clock", max_leaves=DEFAULT_MAX_LEAVES, json=False)
    subparsers = parser.add_subparsers(dest="command")

    report = subparsers.add_parser("report", help="analyze one exact seam example")
    report.add_argument("--example", choices=tuple(examples()), default="clock")
    report.add_argument("--max-leaves", type=bounded_leaves, default=DEFAULT_MAX_LEAVES)
    report.add_argument("--json", action="store_true")

    test = subparsers.add_parser("test", help="run exact structural checks")
    test.add_argument("--deep", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command or "report"
    if command == "test":
        run_self_tests(args.deep)
        print(f"shadow root seam tests passed ({'deep' if args.deep else 'default'})")
        return 0
    report = build_report(args.example, args.max_leaves)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
