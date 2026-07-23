"""Projection-seam experiments for the 1-h-q non-associative algebra.

The experiment separates three ideas that are easy to accidentally merge:

* payload safety is certified by explicit effects;
* operator composition preserves an ordered word, but ordinary matrix
  associativity erases its binary bracketing;
* a tree-indexed ledger of projection defects records where that bracketing
  crossed from operator metaspace back into the three-dimensional algebra.

Everything is exact integer arithmetic and uses only the Python standard
library.  The code is a research toy, not an interrupt implementation.
"""

from __future__ import annotations

import argparse
import itertools
import json
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable, TypeAlias


@dataclass(frozen=True, slots=True)
class Element:
    """Coordinates ``(r, h, q)`` for ``r*1 + h*h_basis + q*q_basis``."""

    r: int = 0
    h: int = 0
    q: int = 0

    def __add__(self, other: Element) -> Element:
        return Element(self.r + other.r, self.h + other.h, self.q + other.q)

    def __sub__(self, other: Element) -> Element:
        return Element(self.r - other.r, self.h - other.h, self.q - other.q)

    def __neg__(self) -> Element:
        return Element(-self.r, -self.h, -self.q)

    def __mul__(self, other: Element) -> Element:
        a, b, c = self.as_tuple()
        d, e, f = other.as_tuple()
        return Element(
            r=a * d + b * f - c * e,
            h=a * e + b * d,
            q=a * f + b * e + c * d + c * f,
        )

    def as_tuple(self) -> tuple[int, int, int]:
        return (self.r, self.h, self.q)


ZERO = Element()
ONE = Element(r=1)
H = Element(h=1)
Q = Element(q=1)
SYMBOLS = {"H": H, "Q": Q}
SIGNED_BASIS = (ONE, H, Q, -ONE, -H, -Q)

Matrix: TypeAlias = tuple[
    tuple[int, int, int],
    tuple[int, int, int],
    tuple[int, int, int],
]

IDENTITY: Matrix = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


def matrix_multiply(left: Matrix, right: Matrix) -> Matrix:
    return tuple(
        tuple(
            sum(left[row][k] * right[k][column] for k in range(3))
            for column in range(3)
        )
        for row in range(3)
    )  # type: ignore[return-value]


def matrix_subtract(left: Matrix, right: Matrix) -> Matrix:
    return tuple(
        tuple(left[row][column] - right[row][column] for column in range(3))
        for row in range(3)
    )  # type: ignore[return-value]


def matrix_vector(matrix: Matrix, vector: tuple[int, int, int]) -> tuple[int, int, int]:
    return tuple(
        sum(matrix[row][column] * vector[column] for column in range(3))
        for row in range(3)
    )  # type: ignore[return-value]


def flatten(matrix: Matrix) -> tuple[int, ...]:
    return tuple(value for row in matrix for value in row)


def determinant(matrix: Matrix) -> int:
    a, b, c = matrix[0]
    d, e, f = matrix[1]
    g, h, i = matrix[2]
    return a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)


def matrix_rank(matrix: Matrix) -> int:
    if determinant(matrix) != 0:
        return 3
    for rows in itertools.combinations(range(3), 2):
        for columns in itertools.combinations(range(3), 2):
            minor = (
                matrix[rows[0]][columns[0]] * matrix[rows[1]][columns[1]]
                - matrix[rows[0]][columns[1]] * matrix[rows[1]][columns[0]]
            )
            if minor != 0:
                return 2
    return 1 if any(flatten(matrix)) else 0


def is_signed_basis_action(matrix: Matrix) -> bool:
    """Each basis column is sent to exactly one signed basis vector."""

    for column in range(3):
        entries = [matrix[row][column] for row in range(3)]
        if sum(value != 0 for value in entries) != 1:
            return False
        if max(map(abs, entries)) != 1:
            return False
    return True


def left_operator(x: Element) -> Matrix:
    a, b, c = x.as_tuple()
    return ((a, -c, b), (b, a, 0), (c, b, a + c))


def project_operator(matrix: Matrix) -> Element:
    """Return ``M(1)``; ``P(M)`` itself would be ``L_{M(1)}``."""

    return Element(matrix[0][0], matrix[1][0], matrix[2][0])


def associator(x: Element, y: Element, z: Element) -> Element:
    return (x * y) * z - x * (y * z)


def projection_defect(x: Element, y: Element) -> Matrix:
    """Return ``L_x L_y - L_{xy}``, the negative associator as an operator."""

    return matrix_subtract(
        matrix_multiply(left_operator(x), left_operator(y)),
        left_operator(x * y),
    )


Tree: TypeAlias = type(None) | tuple["Tree", "Tree"]


@lru_cache(maxsize=None)
def full_binary_trees(leaves: int) -> tuple[Tree, ...]:
    if leaves < 1:
        raise ValueError("a tree needs at least one leaf")
    if leaves == 1:
        return (None,)

    result: list[Tree] = []
    for left_count in range(1, leaves):
        for left in full_binary_trees(left_count):
            for right in full_binary_trees(leaves - left_count):
                result.append((left, right))
    return tuple(result)


def catalan(index: int) -> int:
    value = 1
    for k in range(index):
        value = value * 2 * (2 * k + 1) // (k + 2)
    return value


@dataclass(frozen=True, slots=True)
class Seam:
    """One explicit projection boundary in a bracketed contraction."""

    start: int
    split: int
    end: int
    left: Element
    right: Element
    product: Element
    defect: Matrix

    @property
    def energy(self) -> int:
        return sum(value * value for value in flatten(self.defect))


@dataclass(frozen=True, slots=True)
class Evaluation:
    element: Element
    seams: tuple[Seam, ...]
    next_leaf: int


def evaluate_tree(tree: Tree, word: str, start: int = 0) -> Evaluation:
    if tree is None:
        return Evaluation(SYMBOLS[word[start]], (), start + 1)

    left_tree, right_tree = tree
    left = evaluate_tree(left_tree, word, start)
    right = evaluate_tree(right_tree, word, left.next_leaf)
    product = left.element * right.element
    seam = Seam(
        start=start,
        split=left.next_leaf,
        end=right.next_leaf,
        left=left.element,
        right=right.element,
        product=product,
        defect=projection_defect(left.element, right.element),
    )
    return Evaluation(
        product,
        left.seams + right.seams + (seam,),
        right.next_leaf,
    )


def render_tree(tree: Tree, word: str, start: int = 0) -> tuple[str, int]:
    if tree is None:
        return word[start].lower(), start + 1
    left_tree, right_tree = tree
    left, middle = render_tree(left_tree, word, start)
    right, end = render_tree(right_tree, word, middle)
    return f"({left}{right})", end


def raw_ledger_signature(seams: Iterable[Seam]) -> tuple[tuple[int, ...], ...]:
    """Projection defects in postorder, deliberately omitting tree location."""

    return tuple(flatten(seam.defect) for seam in seams)


def annotated_ledger_signature(
    seams: Iterable[Seam],
) -> tuple[tuple[int, int, int, tuple[int, ...]], ...]:
    """A lossless tree audit for a known word: topology plus local defect."""

    return tuple(
        (seam.start, seam.split, seam.end, flatten(seam.defect)) for seam in seams
    )


def late_operator(word: str) -> Matrix:
    """Compose the ordered operator word without intermediate projection."""

    result = IDENTITY
    for symbol in word:
        result = matrix_multiply(result, left_operator(SYMBOLS[symbol]))
    return result


def right_comb(leaves: int) -> Tree:
    if leaves == 1:
        return None
    return (None, right_comb(leaves - 1))


def validate_word(word: str) -> str:
    normalized = word.strip().upper()
    if not normalized or any(symbol not in SYMBOLS for symbol in normalized):
        raise ValueError("word must contain only H and Q")
    return normalized


def word_spectrum(word: str, include_trees: bool = True) -> dict[str, object]:
    word = validate_word(word)
    root_groups: dict[tuple[int, int, int], list[str]] = {}
    raw_ledgers: set[tuple[tuple[int, ...], ...]] = set()
    annotated_ledgers: set[
        tuple[tuple[int, int, int, tuple[int, ...]], ...]
    ] = set()
    energies: list[int] = []

    for tree in full_binary_trees(len(word)):
        evaluation = evaluate_tree(tree, word)
        rendered, end = render_tree(tree, word)
        assert evaluation.next_leaf == end == len(word)
        root_groups.setdefault(evaluation.element.as_tuple(), []).append(rendered)
        raw_ledgers.add(raw_ledger_signature(evaluation.seams))
        annotated_ledgers.add(annotated_ledger_signature(evaluation.seams))
        energies.append(sum(seam.energy for seam in evaluation.seams))

    late = late_operator(word)
    late_projection = project_operator(late)
    right_evaluation = evaluate_tree(right_comb(len(word)), word).element
    assert late_projection == right_evaluation

    groups = []
    for root, trees in sorted(root_groups.items()):
        group: dict[str, object] = {"root": list(root), "multiplicity": len(trees)}
        if include_trees:
            group["trees"] = trees
        groups.append(group)

    return {
        "word": word,
        "binary_trees": len(full_binary_trees(len(word))),
        "distinct_root_elements": len(root_groups),
        "distinct_raw_defect_ledgers": len(raw_ledgers),
        "distinct_annotated_ledgers": len(annotated_ledgers),
        "root_groups": groups,
        "late_projection": list(late_projection.as_tuple()),
        "late_projection_semantics": "fully right-nested evaluation",
        "late_operator": [list(row) for row in late],
        "minimum_seam_energy": min(energies, default=0),
        "maximum_seam_energy": max(energies, default=0),
    }


def landscape(max_length: int) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for length in range(3, max_length + 1):
        metrics: list[dict[str, object]] = []
        for symbols in itertools.product("HQ", repeat=length):
            word = "".join(symbols)
            spectrum = word_spectrum(word, include_trees=False)
            metrics.append(spectrum)

        max_roots = max(int(item["distinct_root_elements"]) for item in metrics)
        max_raw = max(int(item["distinct_raw_defect_ledgers"]) for item in metrics)
        tree_count = catalan(length - 1)
        root_blind = [
            str(item["word"])
            for item in metrics
            if int(item["distinct_root_elements"]) == 1
        ]
        fully_separating = [
            str(item["word"])
            for item in metrics
            if int(item["distinct_root_elements"]) == tree_count
        ]
        records.append(
            {
                "length": length,
                "words": len(metrics),
                "binary_trees_per_word": tree_count,
                "maximum_distinct_roots": max_roots,
                "words_with_maximum_roots": [
                    str(item["word"])
                    for item in metrics
                    if int(item["distinct_root_elements"]) == max_roots
                ][:8],
                "maximum_distinct_raw_ledgers": max_raw,
                "words_with_maximum_raw_ledgers": [
                    str(item["word"])
                    for item in metrics
                    if int(item["distinct_raw_defect_ledgers"]) == max_raw
                ][:8],
                "root_blind_word_count": len(root_blind),
                "root_blind_examples": root_blind[:8],
                "fully_root_separating_word_count": len(fully_separating),
                "fully_root_separating_examples": fully_separating[:8],
                "all_annotated_ledgers_preserve_tree": all(
                    int(item["distinct_annotated_ledgers"]) == tree_count
                    for item in metrics
                ),
            }
        )
    return records


def operator_landscape(max_length: int) -> list[dict[str, object]]:
    """Measure how strongly ordered H/Q words collapse in operator space."""

    records: list[dict[str, object]] = []
    for length in range(1, max_length + 1):
        operators: dict[tuple[int, ...], list[str]] = {}
        projections: set[tuple[int, int, int]] = set()
        for symbols in itertools.product("HQ", repeat=length):
            word = "".join(symbols)
            operator = late_operator(word)
            operators.setdefault(flatten(operator), []).append(word)
            projections.add(project_operator(operator).as_tuple())
        records.append(
            {
                "length": length,
                "words": 2**length,
                "distinct_operators": len(operators),
                "distinct_late_projections": len(projections),
                "largest_operator_collision": max(
                    len(words) for words in operators.values()
                ),
                "maximum_absolute_matrix_entry": max(
                    abs(value) for operator in operators for value in operator
                ),
            }
        )
    return records


def generated_operator_monoid(
    state_limit: int = 10_000, depth_limit: int = 64
) -> dict[str, object]:
    """Breadth-first closure of the monoid generated by ``L_h`` and ``L_q``."""

    generators = (("H", left_operator(H)), ("Q", left_operator(Q)))
    seen: dict[tuple[int, ...], tuple[Matrix, str]] = {
        flatten(IDENTITY): (IDENTITY, "")
    }
    frontier: list[tuple[Matrix, str]] = [(IDENTITY, "")]
    depth_counts = [1]

    for _depth in range(1, depth_limit + 1):
        next_frontier: list[tuple[Matrix, str]] = []
        for operator, word in frontier:
            for symbol, generator in generators:
                candidate = matrix_multiply(operator, generator)
                signature = flatten(candidate)
                if signature in seen:
                    continue
                witness = word + symbol
                seen[signature] = (candidate, witness)
                next_frontier.append((candidate, witness))
                if len(seen) >= state_limit:
                    return {
                        "closed": False,
                        "reason": "state limit reached",
                        "states_seen": len(seen),
                        "deepest_minimal_word": len(witness),
                        "new_states_by_depth": depth_counts + [len(next_frontier)],
                    }
        depth_counts.append(len(next_frontier))
        if not next_frontier:
            representatives = [word for _matrix, word in seen.values()]
            assert all(
                is_signed_basis_action(matrix) for matrix, _word in seen.values()
            )
            rank_distribution = {
                str(rank): sum(
                    matrix_rank(matrix) == rank for matrix, _word in seen.values()
                )
                for rank in range(4)
            }
            idempotent_witnesses = sorted(
                word
                for matrix, word in seen.values()
                if matrix_multiply(matrix, matrix) == matrix
            )
            zero = ((0, 0, 0), (0, 0, 0), (0, 0, 0))
            nilpotent_witnesses = sorted(
                word
                for matrix, word in seen.values()
                if matrix_multiply(matrix_multiply(matrix, matrix), matrix) == zero
            )
            return {
                "closed": True,
                "states_seen": len(seen),
                "deepest_minimal_word": max(map(len, representatives)),
                "new_states_by_depth": depth_counts,
                "maximum_absolute_matrix_entry": max(
                    abs(value) for signature in seen for value in signature
                ),
                "ambient_signed_transformation_bound": (2 * 3) ** 3,
                "longest_witnesses": sorted(
                    word
                    for word in representatives
                    if len(word) == max(map(len, representatives))
                ),
                "rank_distribution": rank_distribution,
                "invertible_states": sum(
                    determinant(matrix) != 0 for matrix, _word in seen.values()
                ),
                "idempotent_states": len(idempotent_witnesses),
                "idempotent_minimal_witnesses": idempotent_witnesses,
                "nilpotent_states": len(nilpotent_witnesses),
                "nilpotent_minimal_witnesses": nilpotent_witnesses,
            }
        frontier = next_frontier

    return {
        "closed": False,
        "reason": "depth limit reached",
        "states_seen": len(seen),
        "deepest_minimal_word": depth_limit,
        "new_states_by_depth": depth_counts,
    }


@dataclass(frozen=True, slots=True)
class Event:
    name: str
    op: str
    target: int
    constant: int
    tag: Element

    @property
    def reads(self) -> frozenset[int]:
        return frozenset() if self.op == "set" else frozenset({self.target})

    @property
    def writes(self) -> frozenset[int]:
        return frozenset({self.target})

    def apply(self, state: tuple[int, ...]) -> tuple[int, ...]:
        result = list(state)
        if self.op == "add":
            result[self.target] += self.constant
        elif self.op == "mul":
            result[self.target] *= self.constant
        elif self.op == "set":
            result[self.target] = self.constant
        else:
            raise ValueError(f"unknown operation: {self.op}")
        return tuple(result)


def events_conflict(left: Event, right: Event) -> bool:
    return bool(
        left.writes & (right.reads | right.writes)
        or right.writes & (left.reads | left.writes)
    )


def payload_outcomes(
    initial: tuple[int, ...], events: tuple[Event, ...]
) -> dict[tuple[int, ...], list[list[str]]]:
    outcomes: dict[tuple[int, ...], list[list[str]]] = {}
    for ordering in itertools.permutations(events):
        state = initial
        for event in ordering:
            state = event.apply(state)
        outcomes.setdefault(state, []).append([event.name for event in ordering])
    return outcomes


def effect_separation_demo() -> dict[str, object]:
    safe_events = (
        Event("add-r0", "add", 0, 1, H),
        Event("mul-r1", "mul", 1, 2, H),
        Event("set-r2", "set", 2, 9, H),
    )
    unsafe_events = (
        Event("set-r0", "set", 0, 2, Q),
        Event("mul-r0", "mul", 0, 3, Q),
        Event("add-r0", "add", 0, 1, Q),
    )

    def summarize(initial: tuple[int, ...], events: tuple[Event, ...]) -> dict[str, object]:
        conflicts = [
            [left.name, right.name]
            for index, left in enumerate(events)
            for right in events[index + 1 :]
            if events_conflict(left, right)
        ]
        outcomes = payload_outcomes(initial, events)
        word = "".join("H" if event.tag == H else "Q" for event in events)
        control = word_spectrum(word)
        return {
            "initial": list(initial),
            "events": [event.name for event in events],
            "control_word": word,
            "effect_conflicts": conflicts,
            "payload_final_state_count_across_all_orders": len(outcomes),
            "payload_outcomes": [
                {
                    "state": list(state),
                    "ordering_count": len(orderings),
                    "sample_order": orderings[0],
                }
                for state, orderings in sorted(outcomes.items())
            ],
            "control_root_count_across_bracketings": control[
                "distinct_root_elements"
            ],
            "control_root_groups": control["root_groups"],
        }

    return {
        "safe_but_algebraically_path_sensitive": summarize(
            (1, 2, 3), safe_events
        ),
        "unsafe_but_algebraically_root_silent": summarize((5,), unsafe_events),
        "interpretation": (
            "Effect overlap certifies payload safety; the algebra records path. "
            "Neither is a substitute for the other."
        ),
    }


def self_test() -> None:
    assert H * H == Q
    assert Q * Q == Q
    assert H * Q == ONE
    assert Q * H == -ONE
    assert associator(H, H, H) == Element(r=-2)
    assert all(left * right in SIGNED_BASIS for left in SIGNED_BASIS for right in SIGNED_BASIS)

    basis = (ONE, H, Q)
    for x in basis:
        for y in basis:
            assert project_operator(matrix_multiply(left_operator(x), left_operator(y))) == x * y
            defect = projection_defect(x, y)
            for z in basis:
                expected = x * (y * z) - (x * y) * z
                assert matrix_vector(defect, z.as_tuple()) == expected.as_tuple()

    for leaves in range(1, 8):
        assert len(full_binary_trees(leaves)) == catalan(leaves - 1)

    assert word_spectrum("HHH")["distinct_root_elements"] == 2
    qqq = word_spectrum("QQQ")
    assert qqq["distinct_root_elements"] == 1
    assert qqq["maximum_seam_energy"] > 0

    for length in range(1, 7):
        for symbols in itertools.product("HQ", repeat=length):
            word = "".join(symbols)
            assert project_operator(late_operator(word)) == evaluate_tree(
                right_comb(length), word
            ).element

    demos = effect_separation_demo()
    safe = demos["safe_but_algebraically_path_sensitive"]
    unsafe = demos["unsafe_but_algebraically_root_silent"]
    assert isinstance(safe, dict) and isinstance(unsafe, dict)
    assert safe["payload_final_state_count_across_all_orders"] == 1
    assert safe["control_root_count_across_bracketings"] == 2
    assert unsafe["payload_final_state_count_across_all_orders"] > 1
    assert unsafe["control_root_count_across_bracketings"] == 1

    monoid = generated_operator_monoid()
    assert monoid["closed"] is True
    assert monoid["states_seen"] == 99
    assert monoid["deepest_minimal_word"] == 13
    assert monoid["maximum_absolute_matrix_entry"] == 1
    assert monoid["ambient_signed_transformation_bound"] == 216
    assert monoid["rank_distribution"] == {"0": 0, "1": 24, "2": 72, "3": 3}
    assert monoid["invertible_states"] == 3
    assert monoid["idempotent_states"] == 19
    assert monoid["nilpotent_states"] == 0

    lq = left_operator(Q)
    lq_squared = matrix_multiply(lq, lq)
    assert lq_squared != lq
    assert matrix_multiply(lq_squared, lq_squared) == lq_squared
    assert matrix_multiply(lq_squared, lq) == lq_squared


def build_report(word: str, max_length: int) -> dict[str, object]:
    self_test()
    return {
        "experiment": "metaspace projection-seam seismograph",
        "arithmetic": "exact integers",
        "selected_word": word_spectrum(word),
        "landscape": landscape(max_length),
        "operator_landscape": operator_landscape(max_length),
        "generated_operator_monoid": generated_operator_monoid(),
        "effect_algebra_separation": effect_separation_demo(),
        "role_map": {
            "payload_state": "authoritative observable state",
            "effect_conflict_graph": "safety/serializability certificate",
            "root_algebra_element": "lossy path summary",
            "unprojected_operator_word": "ordered composition; bracket-blind",
            "projection_seam_defect": "local associator operator",
            "annotated_seam_ledger": "tree-indexed path audit",
        },
    }


def human_report(report: dict[str, object]) -> str:
    selected = report["selected_word"]
    landscape_rows = report["landscape"]
    separation = report["effect_algebra_separation"]
    operator_rows = report["operator_landscape"]
    monoid = report["generated_operator_monoid"]
    assert isinstance(selected, dict)
    assert isinstance(landscape_rows, list)
    assert isinstance(separation, dict)
    assert isinstance(operator_rows, list)
    assert isinstance(monoid, dict)

    lines = [
        "METASPACE PROJECTION-SEAM SEISMOGRAPH",
        f"word: {selected['word']}",
        f"binary trees: {selected['binary_trees']}",
        f"distinct root elements: {selected['distinct_root_elements']}",
        "raw defect ledgers: "
        f"{selected['distinct_raw_defect_ledgers']}",
        "tree-annotated ledgers: "
        f"{selected['distinct_annotated_ledgers']}",
        "late projection: "
        f"{selected['late_projection']} ({selected['late_projection_semantics']})",
        "",
        "LANDSCAPE",
    ]
    for row in landscape_rows:
        assert isinstance(row, dict)
        lines.append(
            "  n={length}: trees={binary_trees_per_word}, max roots={maximum_distinct_roots}, "
            "root-blind words={root_blind_word_count}, max raw ledgers={maximum_distinct_raw_ledgers}".format(
                **row
            )
        )

    lines.append("")
    lines.append("ORDERED OPERATOR WORDS")
    for row in operator_rows:
        assert isinstance(row, dict)
        lines.append(
            "  n={length}: words={words}, operators={distinct_operators}, "
            "late roots={distinct_late_projections}, largest collision={largest_operator_collision}, "
            "max |entry|={maximum_absolute_matrix_entry}".format(**row)
        )
    lines.append(
        "  closure: closed={closed}, states={states_seen}, deepest minimal word={deepest_minimal_word}".format(
            **monoid
        )
    )

    safe = separation["safe_but_algebraically_path_sensitive"]
    unsafe = separation["unsafe_but_algebraically_root_silent"]
    assert isinstance(safe, dict) and isinstance(unsafe, dict)
    lines.extend(
        [
            "",
            "EFFECT / ALGEBRA SEPARATION",
            "  safe-disjoint payload outcomes: "
            f"{safe['payload_final_state_count_across_all_orders']}",
            "  safe-disjoint control roots: "
            f"{safe['control_root_count_across_bracketings']}",
            "  conflicting payload outcomes: "
            f"{unsafe['payload_final_state_count_across_all_orders']}",
            "  conflicting control roots: "
            f"{unsafe['control_root_count_across_bracketings']}",
            "",
            str(separation["interpretation"]),
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--word", default="HHHHQ")
    parser.add_argument("--max-length", type=int, default=7)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    try:
        args.word = validate_word(args.word)
    except ValueError as error:
        parser.error(str(error))
    if not 3 <= args.max_length <= 8:
        parser.error("--max-length must be between 3 and 8")
    return args


def main() -> None:
    args = parse_args()
    report = build_report(args.word, args.max_length)
    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        print(human_report(report))


if __name__ == "__main__":
    main()
