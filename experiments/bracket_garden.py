#!/usr/bin/env python3
"""Bracket Garden: keep every non-associative history alive.

The garden grows every ordered full binary tree over a word in the real
algebra with basis (1, h, q) and multiplication

    h*h = q,  q*q = q,  h*q = 1,  q*h = -1.

A tree's value is called its phenotype for one chosen leaf word.  Tree
identity is never inferred from that value: Catalan identity, phenotype, and
multilinear-map identity are reported as three different layers.

The implementation is deliberately standard-library-only and uses exact
integer arithmetic.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations, product
from typing import Iterable, Sequence, TypeAlias


MAP_AUDIT_LIMIT = 7
EXPEDITION_LIMIT = 9
TREE_GENERATION_LIMIT = 11


@dataclass(frozen=True, slots=True)
class Element:
    """Coordinates ``(r,h,q)``; the field names are basis coefficients."""

    r: int = 0
    h: int = 0
    q: int = 0

    def __mul__(self, other: object) -> Element:
        if not isinstance(other, Element):
            return NotImplemented
        a, b, c = self.r, self.h, self.q
        d, e, f = other.r, other.h, other.q
        return Element(
            r=a * d + b * f - c * e,
            h=a * e + b * d,
            q=a * f + b * e + c * d + c * f,
        )

    def __neg__(self) -> Element:
        return Element(-self.r, -self.h, -self.q)

    def __str__(self) -> str:
        terms: list[tuple[int, str]] = [
            (self.r, ""),
            (self.h, "h"),
            (self.q, "q"),
        ]
        rendered: list[str] = []
        for coefficient, symbol in terms:
            if coefficient == 0:
                continue
            magnitude = abs(coefficient)
            body = str(magnitude) if not symbol else (
                symbol if magnitude == 1 else f"{magnitude}{symbol}"
            )
            if not rendered:
                rendered.append(f"-{body}" if coefficient < 0 else body)
            else:
                rendered.append(f"{'-' if coefficient < 0 else '+'} {body}")
        return " ".join(rendered) if rendered else "0"


ZERO = Element()
ONE = Element(r=1)
H = Element(h=1)
Q = Element(q=1)
SIGNED_BASIS = (ONE, -ONE, H, -H, Q, -Q)
BASIS = (ONE, H, Q)
BASIS_GLYPHS = {ONE: "1", H: "h", Q: "q"}


@dataclass(frozen=True, slots=True)
class Atom:
    glyph: str
    value: Element


@dataclass(frozen=True, slots=True)
class Leaf:
    """A leaf with a stable in-order position."""

    index: int


@dataclass(frozen=True, slots=True)
class Branch:
    """An ordered contraction; left and right are semantically retained."""

    left: Leaf | Branch
    right: Leaf | Branch


Tree: TypeAlias = Leaf | Branch


@dataclass(frozen=True, slots=True)
class Observation:
    tree_index: int
    tree: Tree
    phenotype: Element


@dataclass(frozen=True, slots=True)
class TraceStep:
    path: str
    expression: str
    left: Element
    right: Element
    result: Element


@dataclass(frozen=True, slots=True)
class WordSurvey:
    atoms: tuple[Atom, ...]
    trees: tuple[Tree, ...]
    groups: dict[Element, tuple[Observation, ...]]

    @property
    def phenotype_count(self) -> int:
        return len(self.groups)

    @property
    def largest_collision(self) -> int:
        return max(len(group) for group in self.groups.values())


def catalan(index: int) -> int:
    """Return the index-th Catalan number with exact integer arithmetic."""

    if index < 0:
        raise ValueError("Catalan index must be non-negative")
    value = 1
    for k in range(index):
        value = value * 2 * (2 * k + 1) // (k + 2)
    return value


@lru_cache(maxsize=None)
def _full_binary_trees(leaves: int, start: int) -> tuple[Tree, ...]:
    if leaves == 1:
        return (Leaf(start),)

    grown: list[Tree] = []
    for left_leaves in range(1, leaves):
        right_leaves = leaves - left_leaves
        for left in _full_binary_trees(left_leaves, start):
            for right in _full_binary_trees(right_leaves, start + left_leaves):
                grown.append(Branch(left, right))
    return tuple(grown)


def full_binary_trees(leaves: int) -> tuple[Tree, ...]:
    """Generate every ordered full binary tree, without quotienting shapes."""

    if leaves < 1:
        raise ValueError("a garden needs at least one leaf")
    if leaves > TREE_GENERATION_LIMIT:
        raise ValueError(
            f"explicit tree generation is bounded at {TREE_GENERATION_LIMIT} leaves "
            "to avoid an accidental Catalan explosion"
        )
    trees = _full_binary_trees(leaves, 0)
    expected = catalan(leaves - 1)
    if len(trees) != expected:
        raise AssertionError(f"tree generator made {len(trees)} trees, expected {expected}")
    return trees


@lru_cache(maxsize=None)
def arity(tree: Tree) -> int:
    if isinstance(tree, Leaf):
        return 1
    return arity(tree.left) + arity(tree.right)


def shape_code(tree: Tree) -> str:
    """A lossless structural code whose leaves retain their positions."""

    if isinstance(tree, Leaf):
        return f"{tree.index + 1}"
    return f"({shape_code(tree.left)}*{shape_code(tree.right)})"


def render_tree(tree: Tree, atoms: Sequence[Atom]) -> str:
    if isinstance(tree, Leaf):
        return atoms[tree.index].glyph
    return f"({render_tree(tree.left, atoms)}*{render_tree(tree.right, atoms)})"


def tree_id(leaves: int, index: int, total: int | None = None) -> str:
    total = catalan(leaves - 1) if total is None else total
    width = max(2, len(str(max(total - 1, 0))))
    return f"T{leaves}:{index:0{width}d}"


def evaluate(tree: Tree, values: Sequence[Element]) -> Element:
    if isinstance(tree, Leaf):
        return values[tree.index]
    return evaluate(tree.left, values) * evaluate(tree.right, values)


def trace_evaluation(tree: Tree, atoms: Sequence[Atom]) -> tuple[Element, tuple[TraceStep, ...]]:
    steps: list[TraceStep] = []

    def visit(node: Tree, path: str) -> Element:
        if isinstance(node, Leaf):
            return atoms[node.index].value
        left = visit(node.left, f"{path}.L")
        right = visit(node.right, f"{path}.R")
        result = left * right
        steps.append(
            TraceStep(
                path=path,
                expression=render_tree(node, atoms),
                left=left,
                right=right,
                result=result,
            )
        )
        return result

    result = visit(tree, "root")
    return result, tuple(steps)


def parse_word(source: str) -> tuple[Atom, ...]:
    """Parse an unbracketed word over signed 1/h/q atoms.

    Adjacent atoms or separators (space, comma, dot, or multiplication signs)
    are accepted.  Parentheses are intentionally not accepted: this program
    grows every bracketing itself.
    """

    atoms: list[Atom] = []
    separators = frozenset(" \t\r\n,.*\u00b7\u00d7")
    index = 0
    while index < len(source):
        if source[index] in separators:
            index += 1
            continue

        sign = 1
        if source[index] in "+-":
            sign = -1 if source[index] == "-" else 1
            index += 1
            if index >= len(source):
                raise ValueError("a trailing sign is not an atom")

        symbol = source[index]
        if symbol not in "1hq":
            raise ValueError(
                f"unexpected character {symbol!r}; use an unbracketed word over 1, h, q"
            )
        value = {"1": ONE, "h": H, "q": Q}[symbol]
        glyph = symbol if sign > 0 else f"-{symbol}"
        atoms.append(Atom(glyph, value if sign > 0 else -value))
        index += 1

    if not atoms:
        raise ValueError("the word is empty")
    return tuple(atoms)


def atoms_from_symbols(symbols: Iterable[str]) -> tuple[Atom, ...]:
    return tuple(Atom(symbol, {"h": H, "q": Q}[symbol]) for symbol in symbols)


def word_label(atoms: Sequence[Atom], compact: bool = False) -> str:
    if compact and all(atom.glyph in {"h", "q", "1"} for atom in atoms):
        return "".join(atom.glyph for atom in atoms)
    return " ".join(atom.glyph for atom in atoms)


def survey_word(atoms: tuple[Atom, ...]) -> WordSurvey:
    trees = full_binary_trees(len(atoms))
    values = tuple(atom.value for atom in atoms)
    mutable_groups: dict[Element, list[Observation]] = {}
    for index, tree in enumerate(trees):
        observation = Observation(index, tree, evaluate(tree, values))
        mutable_groups.setdefault(observation.phenotype, []).append(observation)
    groups = {key: tuple(value) for key, value in mutable_groups.items()}
    return WordSurvey(atoms, trees, groups)


@lru_cache(maxsize=None)
def basis_assignments(leaves: int) -> tuple[tuple[Element, ...], ...]:
    return tuple(product(BASIS, repeat=leaves))


@lru_cache(maxsize=None)
def multilinear_signature(tree: Tree) -> tuple[Element, ...]:
    """Exact map signature on the tensor-product basis.

    The product is multilinear, so agreement on all (1,h,q)^n basis tuples is
    equivalent to equality of the induced n-linear maps.
    """

    return tuple(evaluate(tree, assignment) for assignment in basis_assignments(arity(tree)))


def signature_groups(trees: Sequence[Tree]) -> dict[tuple[Element, ...], list[int]]:
    groups: dict[tuple[Element, ...], list[int]] = {}
    for index, tree in enumerate(trees):
        groups.setdefault(multilinear_signature(tree), []).append(index)
    return groups


def basis_word(assignment: Sequence[Element]) -> str:
    return "".join(BASIS_GLYPHS[value] for value in assignment)


def camouflage_witness(
    survey: WordSurvey,
) -> tuple[Observation, Observation, tuple[Element, ...], Element, Element] | None:
    """Find two phenotype-colliding trees that differ as multilinear maps."""

    assignments = basis_assignments(len(survey.atoms))
    for observations in survey.groups.values():
        if len(observations) < 2:
            continue
        for left, right in combinations(observations, 2):
            left_signature = multilinear_signature(left.tree)
            right_signature = multilinear_signature(right.tree)
            if left_signature == right_signature:
                continue
            for assignment, left_value, right_value in zip(
                assignments, left_signature, right_signature, strict=True
            ):
                if left_value != right_value:
                    return left, right, assignment, left_value, right_value
    return None


def format_histogram(groups: dict[Element, tuple[Observation, ...]]) -> str:
    fields = [
        f"{value}:{len(groups[value])}"
        for value in SIGNED_BASIS
        if value in groups
    ]
    extras = [
        f"{value}:{len(observations)}"
        for value, observations in groups.items()
        if value not in SIGNED_BASIS
    ]
    return "  ".join(fields + extras)


def print_survey(survey: WordSurvey, limit: int, audit_maps: bool) -> None:
    leaves = len(survey.atoms)
    total = len(survey.trees)
    if audit_maps and leaves > MAP_AUDIT_LIMIT:
        raise ValueError(
            f"exact map audit is bounded at {MAP_AUDIT_LIMIT} leaves; "
            "phenotype evaluation remains available above that bound"
        )
    collisions = sum(len(group) > 1 for group in survey.groups.values())
    print("BRACKET GARDEN / phenotype ledger")
    print(f"word       : {word_label(survey.atoms)}")
    print(f"leaves     : {leaves}")
    print(f"tree ledger: {total} retained IDs = Catalan({leaves - 1})")
    print(f"phenotypes : {survey.phenotype_count}")
    print(
        "split      : "
        + ("YES - one word has multiple bracket-sensitive results" if survey.phenotype_count > 1 else "no")
    )
    print(f"collisions : {collisions} phenotype bucket(s) contain distinct trees")

    for phenotype, observations in survey.groups.items():
        status = "COLLISION" if len(observations) > 1 else "singleton"
        print(f"\nphenotype {phenotype} <- {len(observations)} tree(s) [{status}]")
        visible = observations if limit == 0 else observations[:limit]
        for observation in visible:
            identity = tree_id(leaves, observation.tree_index, total)
            expression = render_tree(observation.tree, survey.atoms)
            print(f"  {identity}  shape={shape_code(observation.tree)}  {expression}")
        hidden = len(observations) - len(visible)
        if hidden:
            print(f"  ... {hidden} more retained tree ID(s); use --limit 0 to show all")

    if not audit_maps:
        return
    maps = signature_groups(survey.trees)
    map_collisions = [indices for indices in maps.values() if len(indices) > 1]
    print("\nMULTILINEAR MAP AUDIT")
    print(
        f"basis tests : {len(BASIS) ** leaves} per tree over (1,h,q)^{leaves}; "
        "exact by multilinearity"
    )
    print(f"map ledger  : {len(maps)} distinct maps / {total} trees")
    if map_collisions:
        print(f"map collapse: YES - {len(map_collisions)} signature collision(s)")
    else:
        print("map collapse: no; phenotype collisions are input-specific camouflage")

    witness = camouflage_witness(survey)
    if witness is not None:
        left, right, assignment, left_value, right_value = witness
        left_id = tree_id(leaves, left.tree_index, total)
        right_id = tree_id(leaves, right.tree_index, total)
        print("camouflage  :")
        print(
            f"  {left_id} and {right_id} both yield {left.phenotype} on "
            f"{word_label(survey.atoms, compact=True)}"
        )
        print(
            f"  but on {basis_word(assignment)} they split: "
            f"{left_id}->{left_value}, {right_id}->{right_value}"
        )


def best_binary_word(leaves: int) -> WordSurvey:
    """Find a deterministic, phenotype-rich h/q word.

    Primary score maximizes phenotype count; secondary score minimizes the
    largest collision bucket.  Product order h<q breaks remaining ties.
    """

    best: WordSurvey | None = None
    best_score: tuple[int, int] | None = None
    for symbols in product(("h", "q"), repeat=leaves):
        survey = survey_word(atoms_from_symbols(symbols))
        score = (survey.phenotype_count, -survey.largest_collision)
        if best_score is None or score > best_score:
            best = survey
            best_score = score
    if best is None:
        raise AssertionError("binary-word search produced no candidates")
    return best


def run_expedition(max_leaves: int) -> None:
    if not 1 <= max_leaves <= EXPEDITION_LIMIT:
        raise ValueError(f"--max-leaves must be between 1 and {EXPEDITION_LIMIT}")

    print("SIX-MASK EXPEDITION")
    print("Every h/q leaf product stays in {1,-1,h,-h,q,-q}; tree histories do not.")
    print("The search is exhaustive over every h/q word and every Catalan tree.\n")
    print(" n  trees  best word  phenotypes  largest collision  histogram")
    print("--  -----  ---------  ----------  -----------------  ---------")

    first_full_palette: WordSurvey | None = None
    final_survey: WordSurvey | None = None
    for leaves in range(1, max_leaves + 1):
        survey = best_binary_word(leaves)
        final_survey = survey
        if survey.phenotype_count == len(SIGNED_BASIS) and first_full_palette is None:
            first_full_palette = survey
        print(
            f"{leaves:>2}  {len(survey.trees):>5}  "
            f"{word_label(survey.atoms, compact=True):<9}  "
            f"{survey.phenotype_count:>10}  {survey.largest_collision:>17}  "
            f"{format_histogram(survey.groups)}"
        )

    print("\nEXPEDITION FINDINGS")
    if first_full_palette is None:
        print("full palette : not reached inside this bound")
    else:
        leaves = len(first_full_palette.atoms)
        print(
            f"full palette : first reached at n={leaves} by the balanced witness "
            f"{word_label(first_full_palette.atoms, compact=True)}"
        )
    if max_leaves >= 7:
        pure_h = survey_word(atoms_from_symbols("h" * 7))
        print(
            f"pure-h shock : hhhhhhh alone paints all {pure_h.phenotype_count} masks "
            f"across {len(pure_h.trees)} histories"
        )
    if final_survey is not None:
        print(
            f"identity gap : at n={max_leaves}, {len(final_survey.trees)} tree IDs "
            f"remain explicit behind only {final_survey.phenotype_count} phenotypes"
        )

    # A small exact audit exposes why a phenotype collision is not a tree-map identity.
    if max_leaves >= 4:
        camouflage = survey_word(atoms_from_symbols("hhhh"))
        witness = camouflage_witness(camouflage)
        if witness is None:
            raise AssertionError("expected hhhh camouflage witness was not found")
        left, right, assignment, left_value, right_value = witness
        total = len(camouflage.trees)
        left_id = tree_id(4, left.tree_index, total)
        right_id = tree_id(4, right.tree_index, total)
        print(
            f"camouflage   : {left_id} and {right_id} agree on hhhh ({left.phenotype}) "
            f"but {basis_word(assignment)} separates them ({left_value} vs {right_value})"
        )


def print_trace(atoms: tuple[Atom, ...], index: int) -> None:
    trees = full_binary_trees(len(atoms))
    if not 0 <= index < len(trees):
        raise ValueError(f"tree index must be between 0 and {len(trees) - 1}")
    tree = trees[index]
    identity = tree_id(len(atoms), index, len(trees))
    result, steps = trace_evaluation(tree, atoms)
    print("BRACKET GARDEN / contraction trace")
    print(f"tree       : {identity}")
    print(f"shape      : {shape_code(tree)}")
    print(f"expression : {render_tree(tree, atoms)}")
    for step_index, step in enumerate(steps, 1):
        print(
            f"{step_index:>2}. {step.path:<14} {step.expression:<28} "
            f"{step.left} * {step.right} -> {step.result}"
        )
    print(f"phenotype  : {result}")


def print_map_audit(leaves: int) -> None:
    if not 1 <= leaves <= MAP_AUDIT_LIMIT:
        raise ValueError(f"map audit leaves must be between 1 and {MAP_AUDIT_LIMIT}")
    trees = full_binary_trees(leaves)
    groups = signature_groups(trees)
    collisions = [indices for indices in groups.values() if len(indices) > 1]
    print("BRACKET GARDEN / exact multilinear-map audit")
    print(f"leaves      : {leaves}")
    print(f"trees       : {len(trees)}")
    print(f"basis tuples: {len(BASIS) ** leaves} per tree")
    print(f"distinct maps: {len(groups)}")
    if not collisions:
        print("verdict     : every Catalan tree has a distinct multilinear map")
        return
    print(f"verdict     : {len(collisions)} map-signature collision(s)")
    for collision in collisions:
        ids = ", ".join(tree_id(leaves, index, len(trees)) for index in collision)
        print(f"  {ids}")


def run_self_tests(deep: bool) -> None:
    # Multiplication table and the defining power split.
    assert ONE * H == H * ONE == H
    assert ONE * Q == Q * ONE == Q
    assert H * H == Q
    assert Q * Q == Q
    assert H * Q == ONE
    assert Q * H == -ONE
    hhh = survey_word(atoms_from_symbols("hhh"))
    assert set(hhh.groups) == {ONE, -ONE}
    assert all(len(group) == 1 for group in hhh.groups.values())

    # Catalan generation retains each shape exactly once.
    expected = (1, 1, 2, 5, 14, 42, 132)
    for leaves, count in enumerate(expected, 1):
        trees = full_binary_trees(leaves)
        assert len(trees) == count
        assert len({shape_code(tree) for tree in trees}) == count

    hhhh = survey_word(atoms_from_symbols("hhhh"))
    assert {value: len(group) for value, group in hhhh.groups.items()} == {
        H: 2,
        -H: 2,
        Q: 1,
    }

    # The exhaustive best-phenotype frontier is a compact regression oracle.
    frontier = tuple(best_binary_word(leaves).phenotype_count for leaves in range(1, 7))
    assert frontier == (1, 1, 2, 3, 5, 6)

    # Signed parser and trace agree with direct evaluation.
    signed = parse_word("-h, q, +1")
    assert tuple(atom.value for atom in signed) == (-H, Q, ONE)
    sample_tree = full_binary_trees(3)[1]
    traced, steps = trace_evaluation(sample_tree, signed)
    assert traced == evaluate(sample_tree, tuple(atom.value for atom in signed))
    assert len(steps) == 2

    # Basis signatures are exact n-linear map comparisons, not random probes.
    map_max = 7 if deep else 5
    for leaves in range(1, map_max + 1):
        trees = full_binary_trees(leaves)
        assert len(signature_groups(trees)) == len(trees)

    print("SELF-TEST PASS")
    print("algebra table       : exact")
    print("Catalan trees       : 1,1,2,5,14,42,132")
    print("phenotype frontier  : 1,1,2,3,5,6 for n=1..6")
    print(f"distinct tree maps  : verified exactly through n={map_max}")
    print("arithmetic          : integer / no tolerance")


def non_negative(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Grow and inspect every full binary bracketing in the 1,h,q algebra.",
        epilog="With no command, the deterministic six-mask expedition runs.",
    )
    subparsers = parser.add_subparsers(dest="command")

    plant = subparsers.add_parser("plant", help="group every bracketing of a word by phenotype")
    plant.add_argument("word", help="unbracketed word, e.g. hhhh or 'h q 1'")
    plant.add_argument(
        "--limit",
        type=non_negative,
        default=8,
        help="trees printed per phenotype; 0 prints every retained tree (default: 8)",
    )
    plant.add_argument(
        "--audit-maps",
        action="store_true",
        help=f"compare exact multilinear maps (bounded at {MAP_AUDIT_LIMIT} leaves)",
    )

    trace = subparsers.add_parser("trace", help="show each contraction inside one tree")
    trace.add_argument("word", help="unbracketed word")
    trace.add_argument("--tree", type=non_negative, default=0, help="zero-based Catalan tree index")

    expedition = subparsers.add_parser(
        "expedition", help="exhaustively hunt the six signed-basis phenotypes"
    )
    expedition.add_argument("--max-leaves", type=int, default=8)

    maps = subparsers.add_parser("maps", help="audit Catalan trees as exact multilinear maps")
    maps.add_argument("leaves", type=int)

    test = subparsers.add_parser("test", help="run embedded exact regression tests")
    test.add_argument(
        "--deep",
        action="store_true",
        help=f"verify all distinct tree maps through n={MAP_AUDIT_LIMIT}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "plant":
            print_survey(survey_word(parse_word(args.word)), args.limit, args.audit_maps)
        elif args.command == "trace":
            print_trace(parse_word(args.word), args.tree)
        elif args.command == "maps":
            print_map_audit(args.leaves)
        elif args.command == "test":
            run_self_tests(args.deep)
        else:
            max_leaves = args.max_leaves if args.command == "expedition" else 8
            run_expedition(max_leaves)
    except ValueError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
