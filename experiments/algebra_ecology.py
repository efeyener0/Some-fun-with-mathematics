"""Exact ecology probe for the real algebra A = span{1, h, q}.

The product is

    h*h = q,  q*q = q,  h*q = 1,  q*h = -1.

This file deliberately uses only the Python standard library.  Every linear
algebra calculation is performed over ``fractions.Fraction``; claims that use
order/positivity are explicitly statements over the real numbers.

The probe is an independent, read-only descendant of the supplied research
inputs.  It does not import or modify them.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from fractions import Fraction
from itertools import product
from math import comb
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple


QNumber = Fraction
Vector = Tuple[QNumber, ...]
Matrix = Tuple[Vector, ...]


def frac(value: object) -> Fraction:
    if isinstance(value, Fraction):
        return value
    return Fraction(value)  # type: ignore[arg-type]


@dataclass(frozen=True)
class Element:
    """An exact element ``r*1 + h_coord*h + q_coord*q``."""

    r: Fraction = Fraction(0)
    h: Fraction = Fraction(0)
    q: Fraction = Fraction(0)

    def __post_init__(self) -> None:
        object.__setattr__(self, "r", frac(self.r))
        object.__setattr__(self, "h", frac(self.h))
        object.__setattr__(self, "q", frac(self.q))

    def __add__(self, other: "Element") -> "Element":
        return Element(self.r + other.r, self.h + other.h, self.q + other.q)

    def __sub__(self, other: "Element") -> "Element":
        return Element(self.r - other.r, self.h - other.h, self.q - other.q)

    def __neg__(self) -> "Element":
        return Element(-self.r, -self.h, -self.q)

    def __rmul__(self, scalar: object) -> "Element":
        value = frac(scalar)
        return Element(value * self.r, value * self.h, value * self.q)

    def __truediv__(self, scalar: object) -> "Element":
        value = frac(scalar)
        return Element(self.r / value, self.h / value, self.q / value)

    def __mul__(self, other: "Element") -> "Element":
        a, b, c = self.coordinates()
        d, e, f = other.coordinates()
        return Element(
            a * d + b * f - c * e,
            a * e + b * d,
            a * f + b * e + c * d + c * f,
        )

    def coordinates(self) -> Vector:
        return (self.r, self.h, self.q)


ZERO = Element()
ONE = Element(1)
H = Element(0, 1)
Q = Element(0, 0, 1)
P = ONE - Q
BASIS = (ONE, H, Q)
BASIS_NAMES = ("1", "h", "q")


def associator(x: Element, y: Element, z: Element) -> Element:
    return (x * y) * z - x * (y * z)


def commutator(x: Element, y: Element) -> Element:
    return x * y - y * x


def jordan(x: Element, y: Element) -> Element:
    return (x * y + y * x) / 2


def mirror(x: Element) -> Element:
    """The handedness-reversing anti-involution: h -> -h."""

    return Element(x.r, -x.h, x.q)


def determinant_2d(u: Tuple[Fraction, Fraction], v: Tuple[Fraction, Fraction]) -> Fraction:
    return u[0] * v[1] - u[1] * v[0]


def dot_2d(u: Tuple[Fraction, Fraction], v: Tuple[Fraction, Fraction]) -> Fraction:
    return u[0] * v[0] + u[1] * v[1]


def associator_plane_formula(x: Element, y: Element, z: Element) -> Element:
    """Closed form using only the pure-plane coordinates of x, y, z."""

    u = (x.h, x.q)
    v = (y.h, y.q)
    w = (z.h, z.q)
    uv_det = determinant_2d(u, v)
    vw_det = determinant_2d(v, w)
    uv_dot = dot_2d(u, v)
    vw_dot = dot_2d(v, w)
    return Element(
        -uv_dot * w[0] - vw_dot * u[0],
        uv_det * w[0] - vw_det * u[0],
        (uv_det + uv_dot) * w[1] - (vw_det + vw_dot) * u[1],
    )


def rref(rows: Sequence[Sequence[object]], ncols: int) -> Tuple[List[List[Fraction]], List[int]]:
    matrix = [[frac(value) for value in row] for row in rows]
    if any(len(row) != ncols for row in matrix):
        raise ValueError("ragged matrix")
    pivot_columns: List[int] = []
    pivot_row = 0
    for column in range(ncols):
        candidate = next(
            (row for row in range(pivot_row, len(matrix)) if matrix[row][column]),
            None,
        )
        if candidate is None:
            continue
        matrix[pivot_row], matrix[candidate] = matrix[candidate], matrix[pivot_row]
        scale = matrix[pivot_row][column]
        matrix[pivot_row] = [value / scale for value in matrix[pivot_row]]
        for row in range(len(matrix)):
            if row == pivot_row or not matrix[row][column]:
                continue
            factor = matrix[row][column]
            matrix[row] = [
                value - factor * pivot
                for value, pivot in zip(matrix[row], matrix[pivot_row])
            ]
        pivot_columns.append(column)
        pivot_row += 1
        if pivot_row == len(matrix):
            break
    return matrix, pivot_columns


def rank(rows: Sequence[Sequence[object]], ncols: int = None) -> int:
    if ncols is None:
        if not rows:
            return 0
        ncols = len(rows[0])
    return len(rref(rows, ncols)[1])


def nullspace(rows: Sequence[Sequence[object]], ncols: int) -> List[Vector]:
    reduced, pivots = rref(rows, ncols)
    free_columns = [column for column in range(ncols) if column not in pivots]
    vectors: List[Vector] = []
    for free in free_columns:
        vector = [Fraction(0) for _ in range(ncols)]
        vector[free] = Fraction(1)
        for row, pivot in enumerate(pivots):
            vector[pivot] = -reduced[row][free]
        vectors.append(tuple(vector))
    return vectors


def det3(matrix: Matrix) -> Fraction:
    a, b, c = matrix[0]
    d, e, f = matrix[1]
    g, h, i = matrix[2]
    return a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)


def matmul(left: Matrix, right: Matrix) -> Matrix:
    return tuple(
        tuple(
            sum((left[row][k] * right[k][column] for k in range(3)), Fraction(0))
            for column in range(3)
        )
        for row in range(3)
    )


I3: Matrix = (
    (Fraction(1), Fraction(0), Fraction(0)),
    (Fraction(0), Fraction(1), Fraction(0)),
    (Fraction(0), Fraction(0), Fraction(1)),
)


def operator_matrix(x: Element, side: str) -> Matrix:
    if side == "left":
        columns = [x * basis for basis in BASIS]
    elif side == "right":
        columns = [basis * x for basis in BASIS]
    else:
        raise ValueError("side must be 'left' or 'right'")
    return tuple(
        tuple(columns[column].coordinates()[row] for column in range(3))
        for row in range(3)
    )


def flatten_matrix(matrix: Matrix) -> Vector:
    return tuple(value for row in matrix for value in row)


def envelope_dimension(generators: Sequence[Matrix]) -> int:
    basis: List[Matrix] = []

    def add(candidate: Matrix) -> bool:
        old_rows = [flatten_matrix(matrix) for matrix in basis]
        if rank(old_rows + [flatten_matrix(candidate)], 9) > len(basis):
            basis.append(candidate)
            return True
        return False

    add(I3)
    for generator in generators:
        add(generator)
    changed = True
    while changed and len(basis) < 9:
        changed = False
        for matrix in list(basis):
            for generator in generators:
                changed = add(matmul(matrix, generator)) or changed
                changed = add(matmul(generator, matrix)) or changed
    return len(basis)


def solve3(matrix: Matrix, rhs: Vector) -> Vector:
    augmented = [list(matrix[row]) + [rhs[row]] for row in range(3)]
    reduced, pivots = rref(augmented, 4)
    if pivots[:3] != [0, 1, 2]:
        raise ValueError("matrix is singular")
    return tuple(reduced[row][3] for row in range(3))


def nucleus_constraints(slot: int) -> List[Vector]:
    rows: List[Vector] = []
    free_slots = [index for index in range(3) if index != slot]
    for first in BASIS:
        for second in BASIS:
            fixed = [ONE, ONE, ONE]
            fixed[free_slots[0]] = first
            fixed[free_slots[1]] = second
            for coordinate in range(3):
                coefficients = []
                for candidate in BASIS:
                    arguments = list(fixed)
                    arguments[slot] = candidate
                    coefficients.append(
                        associator(*arguments).coordinates()[coordinate]
                    )
                rows.append(tuple(coefficients))
    return rows


def commutant_constraints() -> List[Vector]:
    rows: List[Vector] = []
    for other in BASIS:
        for coordinate in range(3):
            rows.append(
                tuple(
                    commutator(candidate, other).coordinates()[coordinate]
                    for candidate in BASIS
                )
            )
    return rows


def derivation_constraints() -> List[Vector]:
    """Linear equations for D(xy)-D(x)y-xD(y)=0 on basis pairs."""

    elementary_maps = [
        (output_coordinate, input_coordinate)
        for input_coordinate in range(3)
        for output_coordinate in range(3)
    ]

    def apply_elementary(specification: Tuple[int, int], value: Element) -> Element:
        output_coordinate, input_coordinate = specification
        return value.coordinates()[input_coordinate] * BASIS[output_coordinate]

    rows: List[Vector] = []
    for x in BASIS:
        for y in BASIS:
            residuals = []
            for specification in elementary_maps:
                d_xy = apply_elementary(specification, x * y)
                d_x = apply_elementary(specification, x)
                d_y = apply_elementary(specification, y)
                residuals.append(d_xy - d_x * y - x * d_y)
            for coordinate in range(3):
                rows.append(
                    tuple(residual.coordinates()[coordinate] for residual in residuals)
                )
    return rows


def tensor_associator_report() -> Dict[str, object]:
    triples = list(product(BASIS, repeat=3))
    rows = [
        [associator(*triple).coordinates()[coordinate] for triple in triples]
        for coordinate in range(3)
    ]
    pure_triples = list(product((H, Q), repeat=3))
    pure_rows = [
        [associator(*triple).coordinates()[coordinate] for triple in pure_triples]
        for coordinate in range(3)
    ]

    relations: Mapping[str, Mapping[Tuple[Element, Element, Element], int]] = {
        "qqq": {(Q, Q, Q): 1},
        "cyclic_two_h": {(H, H, Q): 1, (H, Q, H): 1, (Q, H, H): 1},
        "outer_wing_symmetry": {(H, Q, Q): 1, (Q, Q, H): -1},
        "cyclic_one_h_equals_hhh": {
            (H, Q, Q): 1,
            (Q, H, Q): 1,
            (Q, Q, H): 1,
            (H, H, H): -1,
        },
        "bridge_relation": {(H, H, Q): 2, (H, Q, H): 1, (Q, H, Q): 1},
    }
    relation_vectors: List[Vector] = []
    for terms in relations.values():
        image = ZERO
        coefficients = []
        for triple in pure_triples:
            coefficient = terms.get(triple, 0)
            coefficients.append(Fraction(coefficient))
            image = image + coefficient * associator(*triple)
        assert image == ZERO
        relation_vectors.append(tuple(coefficients))
    assert rank(relation_vectors, 8) == 5

    full_rank = rank(rows, 27)
    pure_rank = rank(pure_rows, 8)
    assert full_rank == pure_rank == 3
    return {
        "image_rank": full_rank,
        "full_tensor_domain_dimension": 27,
        "full_kernel_dimension": 27 - full_rank,
        "unit_factor_kernel_dimension": 19,
        "pure_tensor_domain_dimension": 8,
        "pure_kernel_dimension": 8 - pure_rank,
        "pure_kernel_basis_relations": list(relations),
    }


def left_determinant_formula(x: Element) -> Fraction:
    a, b, c = x.coordinates()
    return a * a * (a + c) + b * (b * b + c * c)


def right_determinant_formula(x: Element) -> Fraction:
    a, b, c = x.coordinates()
    return a * a * (a + c) - b * (b * b + c * c)


def core_inverse(x: Element) -> Element:
    if x.h or not x.r or not x.r + x.q:
        raise ValueError("not a two-sided unit in the real associative core")
    return Element(1 / x.r, 0, -x.q / (x.r * (x.r + x.q)))


SIGNED_BASIS = (ONE, -ONE, H, -H, Q, -Q)
SIGNED_LABELS = {
    ONE: "1",
    -ONE: "-1",
    H: "h",
    -H: "-h",
    Q: "q",
    -Q: "-q",
}
LABEL_ORDER = ("1", "-1", "h", "-h", "q", "-q")


def catalan(index: int) -> int:
    return comb(2 * index, index) // (index + 1)


def h_tree_ecology(max_leaves: int) -> Dict[str, object]:
    assert {
        left * right for left, right in product(SIGNED_BASIS, repeat=2)
    }.issubset(set(SIGNED_BASIS))
    counts: List[Dict[Element, int]] = [{}, {H: 1}]
    witnesses: List[Dict[Element, str]] = [{}, {H: "h"}]
    first_witness: Dict[Element, Tuple[int, str]] = {H: (1, "h")}

    for leaves in range(2, max_leaves + 1):
        leaf_counts: Dict[Element, int] = {}
        leaf_witnesses: Dict[Element, str] = {}
        for left_leaves in range(1, leaves):
            right_leaves = leaves - left_leaves
            for left in sorted(counts[left_leaves], key=lambda item: item.coordinates()):
                for right in sorted(counts[right_leaves], key=lambda item: item.coordinates()):
                    value = left * right
                    multiplicity = (
                        counts[left_leaves][left] * counts[right_leaves][right]
                    )
                    leaf_counts[value] = leaf_counts.get(value, 0) + multiplicity
                    if value not in leaf_witnesses:
                        leaf_witnesses[value] = "({}{})".format(
                            witnesses[left_leaves][left], witnesses[right_leaves][right]
                        )
                    if value not in first_witness:
                        first_witness[value] = (leaves, leaf_witnesses[value])
        assert set(leaf_counts).issubset(set(SIGNED_BASIS))
        assert sum(leaf_counts.values()) == catalan(leaves - 1)
        counts.append(leaf_counts)
        witnesses.append(leaf_witnesses)

    assert set(counts[7]) == set(SIGNED_BASIS)
    assert {H * state for state in SIGNED_BASIS} == set(SIGNED_BASIS)

    distributions = []
    for leaves in range(1, max_leaves + 1):
        by_label = {SIGNED_LABELS[value]: amount for value, amount in counts[leaves].items()}
        distributions.append(
            {
                "leaves": leaves,
                "binary_trees": catalan(leaves - 1),
                "distinct_values": len(counts[leaves]),
                "counts": {
                    label: by_label[label] for label in LABEL_ORDER if label in by_label
                },
            }
        )

    left_comb = H
    right_comb = H
    left_cycle = []
    right_cycle = []
    for _ in range(6):
        left_cycle.append(SIGNED_LABELS[left_comb])
        right_cycle.append(SIGNED_LABELS[right_comb])
        left_comb = left_comb * H
        right_comb = H * right_comb
    assert left_comb == H
    assert right_cycle[:3] == right_cycle[3:]

    return {
        "all_six_values_from_leaves": 7,
        "saturation_for_all_larger_degrees": True,
        "saturation_certificate": "h * {+/-1,+/-h,+/-q} is the same six-state set",
        "first_witnesses": {
            SIGNED_LABELS[value]: {"leaves": data[0], "tree": data[1]}
            for value, data in sorted(
                first_witness.items(), key=lambda item: LABEL_ORDER.index(SIGNED_LABELS[item[0]])
            )
        },
        "left_comb_period_6": left_cycle,
        "right_comb_period_3_repeated": right_cycle,
        "distributions": distributions,
    }


def fraction_json(value: Fraction) -> object:
    if value.denominator == 1:
        return value.numerator
    return "{}/{}".format(value.numerator, value.denominator)


def element_json(value: Element) -> List[object]:
    return [fraction_json(coordinate) for coordinate in value.coordinates()]


def vector_elements(vectors: Iterable[Vector]) -> List[List[object]]:
    return [[fraction_json(value) for value in vector] for vector in vectors]


def run_probe(max_h_leaves: int) -> Dict[str, object]:
    # Defining table and closed associator formula.
    assert ONE * H == H * ONE == H
    assert ONE * Q == Q * ONE == Q
    assert H * H == Q and Q * Q == Q
    assert H * Q == ONE and Q * H == -ONE
    for x, y, z in product(BASIS, repeat=3):
        assert associator(x, y, z) == associator_plane_formula(x, y, z)

    tensor_report = tensor_associator_report()
    nuclei = [nullspace(nucleus_constraints(slot), 3) for slot in range(3)]
    commutant = nullspace(commutant_constraints(), 3)
    assert nuclei == [[ONE.coordinates()], [ONE.coordinates()], [ONE.coordinates()]]
    assert commutant == [ONE.coordinates()]

    derivations = nullspace(derivation_constraints(), 9)
    assert derivations == []

    # Baseline Lie-admissibility and a compact Jordan-admissibility counterexample.
    for x, y, z in product(BASIS, repeat=3):
        jacobi = (
            commutator(x, commutator(y, z))
            + commutator(y, commutator(z, x))
            + commutator(z, commutator(x, y))
        )
        assert jacobi == ZERO
    jordan_defect = jordan(jordan(jordan(H, H), H), H) - jordan(
        jordan(H, H), jordan(H, H)
    )
    assert jordan_defect == -Q

    # Anti-involution and the associative core C = span{1,q}.
    for x, y in product(BASIS, repeat=2):
        assert mirror(x * y) == mirror(y) * mirror(x)
    assert mirror(mirror(H)) == H
    assert P * P == P and P * Q == Q * P == ZERO

    # Idempotent and square-zero certificates over R.
    idempotents = (ZERO, ONE, Q, P)
    assert all(value * value == value for value in idempotents)
    for a, b, c in product(range(-2, 3), repeat=3):
        x = Element(a, b, c)
        expected_square = Element(a * a, 2 * a * b, 2 * a * c + b * b + c * c)
        assert x * x == expected_square
        assert associator(x, x, x) == Element(-2 * b * (b * b + c * c))

    # Exact determinant formulae, mirror exchange, and finite certificate grid.
    for a, b, c in product(range(-2, 3), repeat=3):
        x = Element(a, b, c)
        left_matrix = operator_matrix(x, "left")
        right_matrix = operator_matrix(x, "right")
        assert det3(left_matrix) == left_determinant_formula(x)
        assert det3(right_matrix) == right_determinant_formula(x)
        assert left_determinant_formula(mirror(x)) == right_determinant_formula(x)

        if det3(left_matrix) and det3(right_matrix):
            right_inverse = Element(*solve3(left_matrix, ONE.coordinates()))
            left_inverse = Element(*solve3(right_matrix, ONE.coordinates()))
            predicted_two_sided = not b and bool(a) and bool(a + c)
            assert (right_inverse == left_inverse) == predicted_two_sided
            if predicted_two_sided:
                assert right_inverse == core_inverse(x)

    assert (ONE - H) * (ONE + H + Q) == ZERO
    assert (ONE - H + Q) * (ONE + H) == ZERO
    assert H * Q == ONE and (-Q) * H == ONE

    # Exact envelope ranks imply one-sided simplicity.
    left_envelope = envelope_dimension(
        (operator_matrix(H, "left"), operator_matrix(Q, "left"))
    )
    right_envelope = envelope_dimension(
        (operator_matrix(H, "right"), operator_matrix(Q, "right"))
    )
    assert left_envelope == right_envelope == 9

    # Automorphism certificate.  A unital automorphism fixes 1 and sends q to
    # q or p (the two nontrivial idempotents).  If q -> q, x*q=1 forces x=h.
    # If q -> p, x*p=1 has coordinates (a-b,b,-a)=(1,0,0), inconsistent.
    assert H * Q == ONE and Q * H == -ONE and H * H == Q
    for x in BASIS:
        assert x * P == x - x * Q

    tree_report = h_tree_ecology(max_h_leaves)

    return {
        "algebra": {
            "field": "R (exact rational certificates; positivity steps stated separately)",
            "basis": list(BASIS_NAMES),
            "validation": "all exact assertions passed",
        },
        "associator": tensor_report,
        "nuclei_and_center": {
            "left_nucleus_basis": vector_elements(nuclei[0]),
            "middle_nucleus_basis": vector_elements(nuclei[1]),
            "right_nucleus_basis": vector_elements(nuclei[2]),
            "commutant_basis": vector_elements(commutant),
            "center_basis": [[1, 0, 0]],
        },
        "rigidity": {
            "derivation_space_dimension": len(derivations),
            "unital_automorphism_group": "trivial",
            "anti_automorphisms": [
                "unique mirror h -> -h (by composing with the trivial automorphism group)"
            ],
        },
        "associative_core": {
            "subspace": "C = span{1,q} = Fix(mirror) ~= R x R",
            "power_associative_elements_over_R": "exactly C",
            "idempotents": [element_json(value) for value in idempotents],
            "two_sided_units": "a+cq with a*(a+c) != 0",
            "two_sided_inverse": "(a+cq)^-1 = 1/a - c/(a*(a+c))*q",
            "nonzero_square_zero_elements_over_R": 0,
        },
        "singular_ecology": {
            "det_Lx": "a^2*(a+c) + b*(b^2+c^2)",
            "det_Rx": "a^2*(a+c) - b*(b^2+c^2)",
            "common_real_singular_locus": "R*q union R*(1-q)",
            "mirror_swaps_the_two_cubic_surfaces": True,
            "h_right_inverse": element_json(Q),
            "h_left_inverse": element_json(-Q),
            "mirrored_zero_product_pair": [
                "(1-h)*(1+h+q)=0",
                "(1-h+q)*(1+h)=0",
            ],
        },
        "one_sided_ideals": {
            "left_operator_envelope_dimension": left_envelope,
            "right_operator_envelope_dimension": right_envelope,
            "consequence": "no nonzero proper left or right ideals",
            "surprise": "one-sided-simple but still has zero divisors",
        },
        "h_tree_ecology": tree_report,
        "admissibility": {
            "commutator_lie_algebra": "3D Heisenberg ([h,q]=2*1)",
            "jordan_admissible": False,
            "jordan_identity_counterexample": element_json(jordan_defect),
        },
    }


def print_human(report: Mapping[str, object]) -> None:
    associator_report = report["associator"]
    nuclei_report = report["nuclei_and_center"]
    rigidity = report["rigidity"]
    core = report["associative_core"]
    singular = report["singular_ecology"]
    ideals = report["one_sided_ideals"]
    trees = report["h_tree_ecology"]
    assert isinstance(associator_report, dict)
    assert isinstance(nuclei_report, dict)
    assert isinstance(rigidity, dict)
    assert isinstance(core, dict)
    assert isinstance(singular, dict)
    assert isinstance(ideals, dict)
    assert isinstance(trees, dict)

    print("Exact algebra ecology: all assertions passed")
    print(
        "Associator: image rank {}, kernel {} = 19 unit-factor + 5 pure".format(
            associator_report["image_rank"], associator_report["full_kernel_dimension"]
        )
    )
    print("Left/middle/right nuclei and center: R*1")
    print(
        "Rigidity: derivation dimension {}; automorphism group {}".format(
            rigidity["derivation_space_dimension"], rigidity["unital_automorphism_group"]
        )
    )
    print("Associative core:", core["subspace"])
    print("Two-sided units:", core["two_sided_units"])
    print("det(L_x) =", singular["det_Lx"])
    print("det(R_x) =", singular["det_Rx"])
    print(
        "Operator envelopes: left={}, right={} -> {}".format(
            ideals["left_operator_envelope_dimension"],
            ideals["right_operator_envelope_dimension"],
            ideals["consequence"],
        )
    )
    print(
        "Repeated-h trees: all six signed basis values occur from n={} onward".format(
            trees["all_six_values_from_leaves"]
        )
    )
    print("Left comb:", " -> ".join(trees["left_comb_period_6"]))
    print("Right comb:", " -> ".join(trees["right_comb_period_3_repeated"][:3]))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-h-leaves",
        type=int,
        default=12,
        help="largest repeated-h tree degree to count (7..24; default: 12)",
    )
    parser.add_argument("--json", action="store_true", help="emit the full JSON certificate")
    args = parser.parse_args()
    if not 7 <= args.max_h_leaves <= 24:
        raise SystemExit("--max-h-leaves must be between 7 and 24")
    report = run_probe(args.max_h_leaves)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)


if __name__ == "__main__":
    main()
