#!/usr/bin/env python3
"""Universal nonassociative adjunction of a square root ``s*s = h``.

The source algebra A has basis (1,h,q) and multiplication

    h*h=q,  h*q=1,  q*h=-1,  q*q=q.

This module constructs the *presented* real unital nonassociative algebra U
obtained by adjoining one distinguished element s and imposing only s*s=h.
Its vector-space basis consists of irreducible bracket trees.  No
reassociation and no regular-operator square-root identities are imposed.

The seven tree rules are terminating and confluent.  The executable
certificate derives their first-order critical overlaps, checks both extreme
rewrite strategies on a bounded exhaustive tree corpus, verifies the exact
normal-form growth recurrence, and evaluates the resulting U onto the finite
six-dimensional ``shadow_root_clock`` quotient.

Only the Python standard library is used; certificate scalars are exact
``Fraction`` values.  The mathematical coefficient field of U is R.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from itertools import product
from math import comb
from typing import Dict, Iterable, Iterator, Mapping, MutableMapping, Sequence, TypeAlias

try:
    import shadow_root_clock as clock
except ModuleNotFoundError:  # Support import as experiments.universal_shadow_adjunction.
    from . import shadow_root_clock as clock  # type: ignore


SCHEMA_VERSION = 1
DEFAULT_GROWTH_LEAVES = 12
MAX_GROWTH_LEAVES = 50
DEFAULT_EXHAUSTIVE_LEAVES = 5
DEEP_EXHAUSTIVE_LEAVES = 6


class CertificateMismatch(RuntimeError):
    """Raised when an exact presentation certificate changes or fails."""


@dataclass(frozen=True, slots=True)
class Atom:
    label: str


@dataclass(frozen=True, slots=True)
class Variable:
    name: str


@dataclass(frozen=True, slots=True)
class Product:
    left: Expression
    right: Expression


Expression: TypeAlias = Atom | Variable | Product
Term: TypeAlias = Atom | Product
Path: TypeAlias = tuple[int, ...]
Polynomial: TypeAlias = dict[Term, Fraction]
ClockVector: TypeAlias = tuple[Fraction, ...]


ONE = Atom("1")
H = Atom("h")
Q = Atom("q")
S = Atom("s")
ATOMS: tuple[Atom, ...] = (ONE, H, Q, S)
SOURCE_BASIS: tuple[Atom, ...] = (ONE, H, Q)


@dataclass(frozen=True, slots=True)
class RewriteRule:
    name: str
    lhs: Expression
    coefficient: int
    rhs: Expression


X = Variable("x")
RULES: tuple[RewriteRule, ...] = (
    RewriteRule("unit-left", Product(ONE, X), 1, X),
    RewriteRule("unit-right", Product(X, ONE), 1, X),
    RewriteRule("hh-to-q", Product(H, H), 1, Q),
    RewriteRule("hq-to-one", Product(H, Q), 1, ONE),
    RewriteRule("qh-to-minus-one", Product(Q, H), -1, ONE),
    RewriteRule("qq-to-q", Product(Q, Q), 1, Q),
    RewriteRule("ss-to-h", Product(S, S), 1, H),
)


EXPECTED_PRESENTATION_SHA256 = "4b79988e7d0b47baf108fb17d9a5b72eac74239cb5b397452b0a9579d9971868"
EXPECTED_CRITICAL_ORDERED_OVERLAPS = 2
EXPECTED_CRITICAL_UNIQUE_OVERLAPS = 1
EXPECTED_GROWTH_PREFIX = (4, 4, 24, 160, 1152, 8768)


@dataclass(frozen=True, slots=True)
class RewriteStep:
    rule: str
    path: Path
    coefficient: int
    result: Expression


def expression_label(expression: Expression) -> str:
    if isinstance(expression, Atom):
        return expression.label
    if isinstance(expression, Variable):
        return f"${expression.name}"
    return f"({expression_label(expression.left)}*{expression_label(expression.right)})"


def signed_expression_label(coefficient: int, expression: Expression) -> str:
    if coefficient == 1:
        return expression_label(expression)
    if coefficient == -1:
        return "-" + expression_label(expression)
    return f"{coefficient}*{expression_label(expression)}"


def expression_record(expression: Expression) -> object:
    if isinstance(expression, Atom):
        return {"atom": expression.label}
    if isinstance(expression, Variable):
        return {"variable": expression.name}
    return {
        "product": [expression_record(expression.left), expression_record(expression.right)]
    }


def leaf_count(expression: Expression) -> int:
    if not isinstance(expression, Product):
        return 1
    return leaf_count(expression.left) + leaf_count(expression.right)


def variable_counts(expression: Expression) -> Dict[str, int]:
    counts: Dict[str, int] = {}

    def visit(current: Expression) -> None:
        if isinstance(current, Variable):
            counts[current.name] = counts.get(current.name, 0) + 1
        elif isinstance(current, Product):
            visit(current.left)
            visit(current.right)

    visit(expression)
    return counts


def match_pattern(
    pattern: Expression,
    subject: Expression,
    substitution: MutableMapping[Variable, Expression] | None = None,
) -> Mapping[Variable, Expression] | None:
    """One-way first-order match; subject variables remain opaque expressions."""

    if substitution is None:
        substitution = {}
    if isinstance(pattern, Variable):
        previous = substitution.get(pattern)
        if previous is None:
            substitution[pattern] = subject
            return substitution
        return substitution if previous == subject else None
    if isinstance(pattern, Atom):
        return substitution if pattern == subject else None
    if not isinstance(subject, Product):
        return None
    if match_pattern(pattern.left, subject.left, substitution) is None:
        return None
    return match_pattern(pattern.right, subject.right, substitution)


def substitute(
    expression: Expression, substitution: Mapping[Variable, Expression]
) -> Expression:
    if isinstance(expression, Variable):
        replacement = substitution.get(expression)
        if replacement is None or replacement == expression:
            return expression
        return substitute(replacement, substitution)
    if isinstance(expression, Atom):
        return expression
    return Product(
        substitute(expression.left, substitution),
        substitute(expression.right, substitution),
    )


def root_steps(
    expression: Expression, rules: Sequence[RewriteRule] = RULES
) -> tuple[RewriteStep, ...]:
    if not isinstance(expression, Product):
        return ()
    steps: list[RewriteStep] = []
    for rule in rules:
        matched = match_pattern(rule.lhs, expression)
        if matched is None:
            continue
        steps.append(
            RewriteStep(
                rule=rule.name,
                path=(),
                coefficient=rule.coefficient,
                result=substitute(rule.rhs, matched),
            )
        )
    return tuple(steps)


def one_step_rewrites(expression: Expression) -> Iterator[RewriteStep]:
    """Yield every named redex, including the two rules at ``1*1``."""

    yield from root_steps(expression)
    if not isinstance(expression, Product):
        return
    for step in one_step_rewrites(expression.left):
        yield RewriteStep(
            step.rule,
            (0,) + step.path,
            step.coefficient,
            Product(step.result, expression.right),
        )
    for step in one_step_rewrites(expression.right):
        yield RewriteStep(
            step.rule,
            (1,) + step.path,
            step.coefficient,
            Product(expression.left, step.result),
        )


@lru_cache(maxsize=None)
def normal_form(expression: Expression) -> tuple[int, Expression]:
    """Deterministic bottom-up normal form; coefficient is always +1 or -1."""

    if not isinstance(expression, Product):
        return 1, expression
    left_coefficient, left = normal_form(expression.left)
    right_coefficient, right = normal_form(expression.right)
    coefficient = left_coefficient * right_coefficient
    current: Expression = Product(left, right)
    while True:
        steps = root_steps(current)
        if not steps:
            return coefficient, current
        chosen = steps[0]
        coefficient *= chosen.coefficient
        current = chosen.result


def ground_normal_form(term: Term) -> tuple[int, Term]:
    coefficient, result = normal_form(term)
    if isinstance(result, Variable):
        raise CertificateMismatch("a ground term normalized to a variable")
    return coefficient, result


def is_irreducible(expression: Expression) -> bool:
    if root_steps(expression):
        return False
    if isinstance(expression, Product):
        return is_irreducible(expression.left) and is_irreducible(expression.right)
    return True


def strategy_normal_form(
    expression: Expression, *, reverse: bool
) -> tuple[int, Expression, int]:
    """Normalize by repeatedly choosing the first or last available redex."""

    coefficient = 1
    current = expression
    steps_taken = 0
    initial_leaves = leaf_count(expression)
    while True:
        choices = tuple(one_step_rewrites(current))
        if not choices:
            return coefficient, current, steps_taken
        chosen = choices[-1] if reverse else choices[0]
        coefficient *= chosen.coefficient
        current = chosen.result
        steps_taken += 1
        if steps_taken >= initial_leaves:
            raise CertificateMismatch("rewrite exceeded the strict leaf-decrease bound")


def rename_variables(expression: Expression, prefix: str) -> Expression:
    if isinstance(expression, Variable):
        return Variable(prefix + expression.name)
    if isinstance(expression, Atom):
        return expression
    return Product(
        rename_variables(expression.left, prefix),
        rename_variables(expression.right, prefix),
    )


def dereference(
    expression: Expression, substitution: Mapping[Variable, Expression]
) -> Expression:
    current = expression
    seen: set[Variable] = set()
    while isinstance(current, Variable) and current in substitution:
        if current in seen:
            raise CertificateMismatch("cyclic unification substitution")
        seen.add(current)
        current = substitution[current]
    return current


def occurs(
    variable: Variable,
    expression: Expression,
    substitution: Mapping[Variable, Expression],
) -> bool:
    expression = dereference(expression, substitution)
    if expression == variable:
        return True
    if isinstance(expression, Product):
        return occurs(variable, expression.left, substitution) or occurs(
            variable, expression.right, substitution
        )
    return False


def unify(
    left: Expression, right: Expression
) -> Mapping[Variable, Expression] | None:
    substitution: Dict[Variable, Expression] = {}

    def solve(first: Expression, second: Expression) -> bool:
        first = dereference(first, substitution)
        second = dereference(second, substitution)
        if first == second:
            return True
        if isinstance(first, Variable):
            if occurs(first, second, substitution):
                return False
            substitution[first] = second
            return True
        if isinstance(second, Variable):
            if occurs(second, first, substitution):
                return False
            substitution[second] = first
            return True
        if isinstance(first, Atom) or isinstance(second, Atom):
            return False
        return solve(first.left, second.left) and solve(first.right, second.right)

    if not solve(left, right):
        return None
    return substitution


def nonvariable_positions(expression: Expression, prefix: Path = ()) -> Iterator[Path]:
    if isinstance(expression, Variable):
        return
    yield prefix
    if isinstance(expression, Product):
        yield from nonvariable_positions(expression.left, prefix + (0,))
        yield from nonvariable_positions(expression.right, prefix + (1,))


def subexpression_at(expression: Expression, path: Path) -> Expression:
    current = expression
    for direction in path:
        if not isinstance(current, Product):
            raise CertificateMismatch("invalid expression path")
        current = current.left if direction == 0 else current.right
    return current


def replace_at(
    expression: Expression, path: Path, replacement: Expression
) -> Expression:
    if not path:
        return replacement
    if not isinstance(expression, Product):
        raise CertificateMismatch("invalid replacement path")
    head, tail = path[0], path[1:]
    if head == 0:
        return Product(replace_at(expression.left, tail, replacement), expression.right)
    return Product(expression.left, replace_at(expression.right, tail, replacement))


def critical_overlap_certificate() -> dict[str, object]:
    """Derive every ordered nonvariable overlap of the seven finite rules."""

    ordered: list[dict[str, object]] = []
    unique: Dict[tuple[object, ...], dict[str, object]] = {}
    proper_ordered = 0
    for outer_index, outer_source in enumerate(RULES):
        outer = RewriteRule(
            outer_source.name,
            rename_variables(outer_source.lhs, f"o{outer_index}_"),
            outer_source.coefficient,
            rename_variables(outer_source.rhs, f"o{outer_index}_"),
        )
        for inner_index, inner_source in enumerate(RULES):
            inner = RewriteRule(
                inner_source.name,
                rename_variables(inner_source.lhs, f"i{inner_index}_"),
                inner_source.coefficient,
                rename_variables(inner_source.rhs, f"i{inner_index}_"),
            )
            for path in nonvariable_positions(outer.lhs):
                if not path and outer_index == inner_index:
                    continue  # The identical root application is not a peak.
                substitution = unify(subexpression_at(outer.lhs, path), inner.lhs)
                if substitution is None:
                    continue
                peak = substitute(outer.lhs, substitution)
                outer_branch = substitute(outer.rhs, substitution)
                inner_branch = replace_at(
                    peak, path, substitute(inner.rhs, substitution)
                )
                outer_normal_coefficient, outer_normal = normal_form(outer_branch)
                inner_normal_coefficient, inner_normal = normal_form(inner_branch)
                outer_total = outer.coefficient * outer_normal_coefficient
                inner_total = inner.coefficient * inner_normal_coefficient
                joins = outer_total == inner_total and outer_normal == inner_normal
                record = {
                    "outer_rule": outer_source.name,
                    "inner_rule": inner_source.name,
                    "path": list(path),
                    "peak": expression_label(peak),
                    "outer_branch": signed_expression_label(
                        outer.coefficient, outer_branch
                    ),
                    "inner_branch": signed_expression_label(
                        inner.coefficient, inner_branch
                    ),
                    "common_normal_form": (
                        signed_expression_label(outer_total, outer_normal)
                        if joins
                        else None
                    ),
                    "joins": joins,
                }
                ordered.append(record)
                if path:
                    proper_ordered += 1
                branches = tuple(
                    sorted((record["outer_branch"], record["inner_branch"]))
                )
                key = (record["peak"], tuple(record["path"]), branches)
                unique.setdefault(key, record)
    if any(not record["joins"] for record in ordered):
        raise CertificateMismatch("a finite critical overlap does not join")
    if len(ordered) != EXPECTED_CRITICAL_ORDERED_OVERLAPS:
        raise CertificateMismatch("ordered critical-overlap count changed")
    if len(unique) != EXPECTED_CRITICAL_UNIQUE_OVERLAPS:
        raise CertificateMismatch("unique critical-overlap count changed")
    if proper_ordered != 0:
        raise CertificateMismatch("an unexpected proper nonvariable overlap appeared")
    return {
        "ordered_overlap_count": len(ordered),
        "unique_overlap_count": len(unique),
        "proper_nonvariable_overlap_count": proper_ordered,
        "all_join": True,
        "unique_overlaps": list(unique.values()),
        "variable_overlap_schema": (
            "Only a unit rule has a variable child. A reduction inside that child "
            "commutes with erasing the adjacent unit, with the same scalar factor."
        ),
        "disjoint_overlap_schema": (
            "Disjoint tree reductions commute; their central real scalar factors multiply."
        ),
    }


def catalan(index: int) -> int:
    if index < 0:
        raise ValueError("Catalan index must be non-negative")
    return comb(2 * index, index) // (index + 1)


def all_terms_by_size(max_leaves: int) -> tuple[tuple[Term, ...], ...]:
    rows: list[tuple[Term, ...]] = [(), ATOMS]
    for leaves in range(2, max_leaves + 1):
        current: list[Term] = []
        for left_leaves in range(1, leaves):
            right_leaves = leaves - left_leaves
            for left in rows[left_leaves]:
                for right in rows[right_leaves]:
                    current.append(Product(left, right))
        expected = 4**leaves * catalan(leaves - 1)
        if len(current) != expected:
            raise CertificateMismatch("raw bracket-tree enumeration lost a tree")
        rows.append(tuple(current))
    return tuple(rows)


def irreducibles_by_size(max_leaves: int) -> tuple[tuple[Term, ...], ...]:
    rows: list[tuple[Term, ...]] = [(), ATOMS]
    for leaves in range(2, max_leaves + 1):
        current: list[Term] = []
        for left_leaves in range(1, leaves):
            right_leaves = leaves - left_leaves
            for left in rows[left_leaves]:
                for right in rows[right_leaves]:
                    candidate = Product(left, right)
                    if not root_steps(candidate):
                        current.append(candidate)
        rows.append(tuple(current))
    return tuple(rows)


def growth_counts(max_leaves: int) -> tuple[int, ...]:
    """Normal-form basis counts by leaf size, including singleton unit."""

    if not 1 <= max_leaves <= MAX_GROWTH_LEAVES:
        raise ValueError(
            f"growth leaves must be between 1 and {MAX_GROWTH_LEAVES}"
        )
    nonunit = [0] * (max_leaves + 1)
    nonunit[1] = 3
    if max_leaves >= 2:
        nonunit[2] = 4
    for leaves in range(3, max_leaves + 1):
        nonunit[leaves] = sum(
            nonunit[left] * nonunit[leaves - left]
            for left in range(1, leaves)
        )
    full = nonunit[:]
    full[1] += 1  # The unit is the fourth singleton normal form.
    return tuple(full[1:])


def shadow_tail(s_count: int) -> Term:
    """Return (((h*s)*s)*...*s), an irreducible for every s_count >= 1."""

    if s_count < 1:
        raise ValueError("shadow-tail s-count must be positive")
    current: Term = H
    for _ in range(s_count):
        current = Product(current, S)
    return current


def clean_polynomial(polynomial: Mapping[Term, Fraction]) -> Polynomial:
    return {term: coefficient for term, coefficient in polynomial.items() if coefficient}


def polynomial_from_term(term: Term, coefficient: Fraction = Fraction(1)) -> Polynomial:
    sign, basis_term = ground_normal_form(term)
    return clean_polynomial({basis_term: coefficient * sign})


def add_polynomials(*polynomials: Mapping[Term, Fraction]) -> Polynomial:
    result: Dict[Term, Fraction] = {}
    for polynomial in polynomials:
        for term, coefficient in polynomial.items():
            result[term] = result.get(term, Fraction(0)) + coefficient
    return clean_polynomial(result)


def scale_polynomial(
    scalar: Fraction, polynomial: Mapping[Term, Fraction]
) -> Polynomial:
    return clean_polynomial(
        {term: scalar * coefficient for term, coefficient in polynomial.items()}
    )


def multiply_polynomials(
    left: Mapping[Term, Fraction], right: Mapping[Term, Fraction]
) -> Polynomial:
    result: Dict[Term, Fraction] = {}
    for left_term, left_coefficient in left.items():
        for right_term, right_coefficient in right.items():
            sign, basis_term = ground_normal_form(Product(left_term, right_term))
            result[basis_term] = result.get(basis_term, Fraction(0)) + (
                left_coefficient * right_coefficient * sign
            )
    return clean_polynomial(result)


def polynomial_label(polynomial: Mapping[Term, Fraction]) -> str:
    if not polynomial:
        return "0"
    pieces: list[str] = []
    for term in sorted(polynomial, key=expression_label):
        coefficient = polynomial[term]
        body = expression_label(term)
        if coefficient == 1:
            token = body
        elif coefficient == -1:
            token = "-" + body
        else:
            token = f"{coefficient}*{body}"
        if pieces and not token.startswith("-"):
            token = "+" + token
        pieces.append(token)
    return "".join(pieces)


ATOM_CLOCK_IMAGES: Mapping[Atom, tuple[int, ...]] = {
    ONE: clock.ONE,
    H: clock.H,
    Q: clock.Q,
    S: clock.S,
}


@lru_cache(maxsize=None)
def evaluate_clock_term(term: Term) -> tuple[int, ...]:
    if isinstance(term, Atom):
        return ATOM_CLOCK_IMAGES[term]
    return clock.multiply(evaluate_clock_term(term.left), evaluate_clock_term(term.right))


def evaluate_clock_polynomial(polynomial: Mapping[Term, Fraction]) -> ClockVector:
    result = [Fraction(0) for _ in range(clock.DIMENSION)]
    for term, coefficient in polynomial.items():
        image = evaluate_clock_term(term)
        for index, coordinate in enumerate(image):
            result[index] += coefficient * coordinate
    return tuple(result)


def scaled_clock_vector(coefficient: int, vector: Sequence[int]) -> tuple[int, ...]:
    return tuple(coefficient * coordinate for coordinate in vector)


def source_table_checks() -> dict[str, object]:
    expected: Mapping[tuple[Atom, Atom], tuple[int, Atom]] = {
        (ONE, ONE): (1, ONE),
        (ONE, H): (1, H),
        (ONE, Q): (1, Q),
        (H, ONE): (1, H),
        (Q, ONE): (1, Q),
        (H, H): (1, Q),
        (H, Q): (1, ONE),
        (Q, H): (-1, ONE),
        (Q, Q): (1, Q),
    }
    rows: list[dict[str, object]] = []
    for left in SOURCE_BASIS:
        for right in SOURCE_BASIS:
            actual = ground_normal_form(Product(left, right))
            wanted = expected[(left, right)]
            if actual != wanted:
                raise CertificateMismatch("the embedded A multiplication table changed")
            rows.append(
                {
                    "left": left.label,
                    "right": right.label,
                    "result": signed_expression_label(*actual),
                }
            )
    if ground_normal_form(Product(S, S)) != (1, H):
        raise CertificateMismatch("the adjoined square-root relation failed")
    return {
        "A_table_checks": len(rows),
        "A_table": rows,
        "s_squared": "h",
        "source_normal_forms": ["1", "h", "q"],
        "source_basis_remains_distinct": True,
    }


def rule_record(rule: RewriteRule) -> dict[str, object]:
    return {
        "name": rule.name,
        "lhs": expression_label(rule.lhs),
        "coefficient": rule.coefficient,
        "rhs": expression_label(rule.rhs),
        "leaf_drop": leaf_count(rule.lhs) - leaf_count(rule.rhs),
    }


def stable_digest(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def presentation_digest(rules: Sequence[RewriteRule] = RULES) -> str:
    return stable_digest(
        {
            "schema_version": SCHEMA_VERSION,
            "coefficient_field": "R",
            "signature": "one bilinear binary product, constants 1,h,q,s",
            "bracketing": "ordered full binary trees; no reassociation",
            "rules": [rule_record(rule) for rule in rules],
            "morphisms": "unital R-algebra homomorphisms fixing A and s",
        }
    )


def presentation_static_checks(enforce_baseline: bool = True) -> dict[str, object]:
    for rule in RULES:
        lhs_variables = variable_counts(rule.lhs)
        rhs_variables = variable_counts(rule.rhs)
        if any(count != 1 for count in lhs_variables.values()):
            raise CertificateMismatch("a rewrite left side is not left-linear")
        if not set(rhs_variables).issubset(lhs_variables):
            raise CertificateMismatch("a rewrite right side introduces a variable")
        if leaf_count(rule.lhs) <= leaf_count(rule.rhs):
            raise CertificateMismatch("a rewrite rule does not strictly decrease leaves")
        if rule.coefficient not in {-1, 1}:
            raise CertificateMismatch("a rule coefficient left the signed-monomial class")
    digest = presentation_digest()
    if enforce_baseline and digest != EXPECTED_PRESENTATION_SHA256:
        raise CertificateMismatch(
            "presentation fingerprint changed: expected "
            f"{EXPECTED_PRESENTATION_SHA256}, got {digest}"
        )
    return {
        "rule_count": len(RULES),
        "all_left_linear": True,
        "all_strictly_leaf_decreasing": True,
        "presentation_sha256": digest,
        "baseline_match": digest == EXPECTED_PRESENTATION_SHA256,
    }


def clock_quotient_certificate() -> dict[str, object]:
    preimages: tuple[tuple[str, Term], ...] = (
        ("1", ONE),
        ("h", H),
        ("q", Q),
        ("s", S),
        ("t", Product(H, S)),
        ("u", Product(Q, S)),
    )
    images: list[dict[str, object]] = []
    for index, (label, term) in enumerate(preimages):
        image = evaluate_clock_term(term)
        if image != clock.BASIS[index]:
            raise CertificateMismatch("the declared clock quotient preimages changed")
        images.append(
            {
                "clock_basis": label,
                "preimage_normal_form": expression_label(term),
                "image": list(image),
            }
        )

    hs = polynomial_from_term(Product(H, S))
    sh = polynomial_from_term(Product(S, H))
    kernel_witness = add_polynomials(hs, scale_polynomial(Fraction(-1), sh))
    if not kernel_witness:
        raise CertificateMismatch("the clock-kernel witness vanished in U")
    if evaluate_clock_polynomial(kernel_witness) != (Fraction(0),) * clock.DIMENSION:
        raise CertificateMismatch("the declared clock-kernel witness has nonzero image")

    left_operator_defect = add_polynomials(
        polynomial_from_term(Product(S, Product(S, Q))),
        scale_polynomial(Fraction(-1), polynomial_from_term(Product(H, Q))),
    )
    if not left_operator_defect:
        raise CertificateMismatch("the regular-operator defect vanished universally")
    if evaluate_clock_polynomial(left_operator_defect) != (Fraction(0),) * clock.DIMENSION:
        raise CertificateMismatch("the regular-operator defect did not vanish in clock")

    return {
        "target": "the explicit six-dimensional shadow_root_clock algebra",
        "surjective": True,
        "surjectivity_certificate": images,
        "kernel_witness": {
            "element_in_U": polynomial_label(kernel_witness),
            "nonzero_by_distinct_normal_forms": True,
            "clock_image": [0] * clock.DIMENSION,
            "meaning": "h*s and s*h are distinct in U but both map to t",
        },
        "extra_clock_relation_witness": {
            "element_in_U": polynomial_label(left_operator_defect),
            "nonzero_in_U": True,
            "clock_image": [0] * clock.DIMENSION,
            "meaning": "L_s^2(q)=L_h(q) holds in clock but is not imposed in U",
        },
        "finite_clock_is_the_universal_object": False,
    }


def clock_collapse_profile(max_leaves: int = DEEP_EXHAUSTIVE_LEAVES) -> dict[str, object]:
    """Measure how the infinite normal-form basis collapses in the 6D quotient."""

    rows = irreducibles_by_size(max_leaves)
    profile: list[dict[str, object]] = []
    first_collision: dict[str, object] | None = None
    first_zero: dict[str, object] | None = None
    zero = (0,) * clock.DIMENSION
    for leaves in range(1, max_leaves + 1):
        fibers: Dict[tuple[int, ...], list[Term]] = {}
        for term in rows[leaves]:
            fibers.setdefault(evaluate_clock_term(term), []).append(term)
        collision_fibers = [
            (image, terms) for image, terms in fibers.items() if len(terms) > 1
        ]
        if first_collision is None and collision_fibers:
            image, terms = min(
                collision_fibers,
                key=lambda item: tuple(expression_label(term) for term in item[1]),
            )
            first_collision = {
                "leaf_size": leaves,
                "normal_forms": [expression_label(terms[0]), expression_label(terms[1])],
                "common_clock_image": clock.vector_label(image),
            }
        if first_zero is None and zero in fibers:
            witness = min(fibers[zero], key=expression_label)
            first_zero = {
                "leaf_size": leaves,
                "normal_form": expression_label(witness),
                "clock_image": "0",
            }
        profile.append(
            {
                "leaf_size": leaves,
                "U_basis_count": len(rows[leaves]),
                "distinct_clock_images": len(fibers),
                "collision_fiber_count": len(collision_fibers),
                "maximum_fiber_size": max(map(len, fibers.values())),
                "zero_is_an_image": zero in fibers,
                "image_labels": sorted(clock.vector_label(image) for image in fibers),
            }
        )
    if first_collision is None or first_collision["leaf_size"] != 2:
        raise CertificateMismatch("the clock quotient's first basis collision changed")
    if first_zero is None or first_zero["leaf_size"] != 3:
        raise CertificateMismatch("the clock quotient's first zero normal form changed")
    return {
        "profile": profile,
        "first_same_degree_basis_collision": first_collision,
        "first_irreducible_with_zero_image": first_zero,
    }


def exhaustive_tree_certificate(max_leaves: int) -> dict[str, object]:
    rows = all_terms_by_size(max_leaves)
    irreducible_rows = irreducibles_by_size(max_leaves)
    recurrence = growth_counts(max_leaves)
    enumerated_counts = tuple(len(irreducible_rows[size]) for size in range(1, max_leaves + 1))
    if enumerated_counts != recurrence:
        raise CertificateMismatch("irreducible enumeration differs from the recurrence")

    raw_checks = 0
    branch_checks = 0
    maximum_steps = 0
    for size in range(1, max_leaves + 1):
        for term in rows[size]:
            coefficient, irreducible = ground_normal_form(term)
            if not is_irreducible(irreducible):
                raise CertificateMismatch("normalizer emitted a reducible term")
            first_coefficient, first_normal, first_steps = strategy_normal_form(
                term, reverse=False
            )
            last_coefficient, last_normal, last_steps = strategy_normal_form(
                term, reverse=True
            )
            if (first_coefficient, first_normal) != (coefficient, irreducible):
                raise CertificateMismatch("preorder strategy disagrees with bottom-up normal form")
            if (last_coefficient, last_normal) != (coefficient, irreducible):
                raise CertificateMismatch("reverse strategy disagrees with bottom-up normal form")
            maximum_steps = max(maximum_steps, first_steps, last_steps)
            for step in one_step_rewrites(term):
                branch_coefficient, branch_normal = normal_form(step.result)
                if (
                    step.coefficient * branch_coefficient,
                    branch_normal,
                ) != (coefficient, irreducible):
                    raise CertificateMismatch("a bounded local rewrite peak does not join")
                branch_checks += 1
            raw_image = evaluate_clock_term(term)
            normal_image = evaluate_clock_term(irreducible)
            if raw_image != scaled_clock_vector(coefficient, normal_image):
                raise CertificateMismatch("tree normalization is unsound in the clock quotient")
            raw_checks += 1
    return {
        "maximum_leaf_size": max_leaves,
        "raw_tree_count": raw_checks,
        "one_step_branch_join_checks": branch_checks,
        "first_last_bottom_up_strategy_agreement": True,
        "maximum_rewrite_steps_seen": maximum_steps,
        "clock_evaluation_parity_checks": raw_checks,
        "irreducible_counts": list(enumerated_counts),
        "recurrence_counts_match_enumeration": True,
    }


def polynomial_contract_checks() -> dict[str, object]:
    one = polynomial_from_term(ONE)
    h = polynomial_from_term(H)
    q = polynomial_from_term(Q)
    s = polynomial_from_term(S)
    contracts = (
        (multiply_polynomials(h, h), q, "h*h=q"),
        (multiply_polynomials(h, q), one, "h*q=1"),
        (multiply_polynomials(q, h), scale_polynomial(Fraction(-1), one), "q*h=-1"),
        (multiply_polynomials(q, q), q, "q*q=q"),
        (multiply_polynomials(s, s), h, "s*s=h"),
        (multiply_polynomials(one, s), s, "1*s=s"),
        (multiply_polynomials(s, one), s, "s*1=s"),
    )
    for actual, expected, name in contracts:
        if actual != expected:
            raise CertificateMismatch(f"polynomial contract failed: {name}")

    hs = multiply_polynomials(h, s)
    sh = multiply_polynomials(s, h)
    if hs == sh:
        raise CertificateMismatch("universal presentation accidentally imposed h*s=s*h")
    left_bracket = multiply_polynomials(hs, s)
    right_bracket = multiply_polynomials(h, multiply_polynomials(s, s))
    if left_bracket == right_bracket:
        raise CertificateMismatch("universal presentation accidentally reassociated a product")
    return {
        "exact_contract_checks": len(contracts),
        "h_times_s_distinct_from_s_times_h": True,
        "left_bracket": polynomial_label(left_bracket),
        "right_bracket": polynomial_label(right_bracket),
        "nonassociative_witness": True,
    }


def fault_injection_certificate() -> dict[str, bool]:
    corrupted = list(RULES)
    original = corrupted[-1]
    corrupted[-1] = RewriteRule(original.name, original.lhs, 1, Q)
    corrupted_digest = presentation_digest(corrupted)
    fingerprint_rejected = corrupted_digest != presentation_digest()
    corrupted_relation_rejected_by_clock = (
        evaluate_clock_term(Product(S, S)) != evaluate_clock_term(Q)
    )
    if not fingerprint_rejected or not corrupted_relation_rejected_by_clock:
        raise CertificateMismatch("deterministic rule corruption was not rejected")
    return {
        "ss_to_q_fingerprint_rejected": fingerprint_rejected,
        "ss_to_q_clock_semantics_rejected": corrupted_relation_rejected_by_clock,
    }


def build_report(
    growth_leaves: int = DEFAULT_GROWTH_LEAVES,
    *,
    deep: bool = False,
    enforce_baseline: bool = True,
) -> dict[str, object]:
    static = presentation_static_checks(enforce_baseline=enforce_baseline)
    source = source_table_checks()
    critical = critical_overlap_certificate()
    polynomial = polynomial_contract_checks()
    clock_quotient = clock_quotient_certificate()
    clock_collapse = clock_collapse_profile()
    exhaustive_leaves = (
        DEEP_EXHAUSTIVE_LEAVES if deep else DEFAULT_EXHAUSTIVE_LEAVES
    )
    exhaustive = exhaustive_tree_certificate(exhaustive_leaves)
    counts = growth_counts(growth_leaves)
    if tuple(counts[: len(EXPECTED_GROWTH_PREFIX)]) != EXPECTED_GROWTH_PREFIX[: len(counts)]:
        raise CertificateMismatch("normal-form growth prefix changed")

    tails: list[dict[str, object]] = []
    for s_count in range(1, min(growth_leaves, 10) + 1):
        term = shadow_tail(s_count)
        if not is_irreducible(term) or ground_normal_form(term) != (1, term):
            raise CertificateMismatch("the explicit infinite irreducible family reduced")
        tails.append(
            {
                "s_count": s_count,
                "leaf_size": leaf_count(term),
                "normal_form": expression_label(term),
            }
        )

    deep_evidence: dict[str, object]
    if deep:
        deep_evidence = {
            "performed": True,
            "exhaustive_tree_certificate": exhaustive,
            "fault_injection": fault_injection_certificate(),
        }
    else:
        deep_evidence = {
            "performed": False,
            "note": (
                "use --deep to extend the exhaustive corpus from five to six leaves "
                "and run deterministic corruption rejection"
            ),
        }

    return {
        "status": "exact_infinite_universal_square_root_adjunction",
        "presentation": {
            "notation": "U = R{1,h,q,s}_nonassoc / (unit, A-table, s*s-h)",
            "coefficient_field": "real numbers",
            "terms": "ordered full binary bracket trees over 1,h,q,s",
            "rules": [rule_record(rule) for rule in RULES],
            "no_reassociation_rule": True,
            "static_certificate": static,
        },
        "normal_forms": {
            "basis": (
                "all irreducible trees; 1 occurs only as the singleton, and no leaf-cherry "
                "is one of hh,hq,qh,qq,ss"
            ),
            "termination": "every rule strictly decreases total leaf count by one",
            "confluence": {
                "critical_overlaps": critical,
                "argument": (
                    "termination plus joinability of the only root peak, unit-variable "
                    "overlaps, and disjoint overlaps gives a unique normal form"
                ),
            },
            "growth": {
                "leaf_sizes": list(range(1, growth_leaves + 1)),
                "basis_counts": list(counts),
                "nonunit_recurrence": (
                    "b1=3, b2=4, and bn=sum_{i=1}^{n-1} bi*b(n-i) for n>=3"
                ),
                "generating_function": (
                    "B(z)=(1-sqrt(1-12z+20z^2))/2; U(z)=z+B(z)"
                ),
                "factorized_discriminant": "1-12z+20z^2=(1-2z)(1-10z)",
                "dominant_radius": "1/10",
                "coefficient_asymptotic": (
                    "b_n ~ 10^n/(sqrt(20*pi)*n^(3/2)); this is derived from B(z), "
                    "not an independent validation claim"
                ),
                "meaning": (
                    "B counts normal forms over h,q,s; the extra z is singleton 1"
                ),
            },
            "infinite_irreducible_family": {
                "formula": "w_n=(((h*s)*s)*...*s) with n copies of s, n>=1",
                "why_distinct": "w_n is irreducible and has leaf size n+1",
                "samples": tails,
            },
        },
        "source_embedding": {
            **source,
            "injective": True,
            "proof": (
                "1,h,q are three different irreducible basis trees, so no nonzero "
                "real linear combination of them vanishes in U"
            ),
            "common_unit": True,
        },
        "universal_property": {
            "objects": (
                "real unital nonassociative algebras B containing A with the same unit, "
                "together with b in B satisfying b*b=h"
            ),
            "morphisms": (
                "unital real-algebra homomorphisms that fix A pointwise and send the "
                "distinguished root to the distinguished root; morphisms need not be injective"
            ),
            "map": (
                "evaluate a tree recursively: 1,h,q use the A inclusion, s maps to b, "
                "and (x*y) maps to eval(x)*eval(y); then extend real-linearly"
            ),
            "well_defined": (
                "each of the seven rewrite rules is exactly a unit, A-table, or b*b=h "
                "identity in B, so equivalent expressions have the same value"
            ),
            "unique": (
                "every basis tree is built from A and s, hence any such homomorphism is "
                "forced recursively on every tree and therefore on every linear combination"
            ),
        },
        "clock_quotient": clock_quotient,
        "clock_collapse_profile": clock_collapse,
        "default_evidence": {
            "formal_static_checks": static,
            "source_and_root_checks": source,
            "critical_overlap_certificate": critical,
            "polynomial_contracts": polynomial,
            "bounded_exhaustive_certificate": exhaustive,
            "clock_quotient_certificate": clock_quotient,
            "clock_collapse_profile": clock_collapse,
        },
        "deep_evidence": deep_evidence,
        "scope": {
            "proved": (
                "U is an infinite-dimensional presented real unital nonassociative algebra, "
                "A embeds with the same unit, and U has the stated initial mapping property"
            ),
            "finite_clock_boundary": (
                "shadow_root_clock is a surjective six-dimensional quotient satisfying "
                "additional L_s and R_s identities; it is not U"
            ),
            "not_imposed": [
                "associativity or power-associativity",
                "L_s^2=L_h",
                "R_s^2=R_h",
                "commutation of s with h or q",
                "finite dimensionality",
            ],
            "runtime_boundary": (
                "Python checks rational/integer certificates and finite tree corpora; "
                "the all-real universal statement follows from the symbolic rewrite proof"
            ),
            "fingerprint_boundary": (
                "the SHA-256 value detects source drift; it is not the confluence proof"
            ),
        },
    }


def print_human(report: Mapping[str, object]) -> None:
    presentation = report["presentation"]
    normal_forms = report["normal_forms"]
    source = report["source_embedding"]
    quotient = report["clock_quotient"]
    default = report["default_evidence"]
    deep = report["deep_evidence"]
    assert isinstance(presentation, dict)
    assert isinstance(normal_forms, dict)
    assert isinstance(source, dict)
    assert isinstance(quotient, dict)
    assert isinstance(default, dict)
    assert isinstance(deep, dict)
    growth = normal_forms["growth"]
    exhaustive = default["bounded_exhaustive_certificate"]
    confluence = normal_forms["confluence"]
    assert isinstance(growth, dict)
    assert isinstance(exhaustive, dict)
    assert isinstance(confluence, dict)
    critical = confluence["critical_overlaps"]
    assert isinstance(critical, dict)

    print("Universal shadow adjunction")
    print("status:", report["status"])
    print("presentation:", presentation["notation"])
    print("rules / unique critical overlaps:", len(presentation["rules"]), "/", critical["unique_overlap_count"])
    print("critical overlaps join:", critical["all_join"])
    print("A injective / common unit:", source["injective"], "/", source["common_unit"])
    print("basis growth:", growth["basis_counts"])
    print(
        "exhaustive raw trees / one-step joins:",
        exhaustive["raw_tree_count"],
        "/",
        exhaustive["one_step_branch_join_checks"],
    )
    print("clock quotient surjective:", quotient["surjective"])
    print("clock kernel witness:", quotient["kernel_witness"]["element_in_U"])
    print("deep certificate:", "performed" if deep.get("performed") else "not requested")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        nargs="?",
        choices=("report", "test"),
        default="report",
        help="report is the default; test emits a compact success summary",
    )
    parser.add_argument(
        "--growth-leaves",
        type=int,
        default=DEFAULT_GROWTH_LEAVES,
        help=f"normal-form growth prefix length (1..{MAX_GROWTH_LEAVES})",
    )
    parser.add_argument(
        "--deep",
        action="store_true",
        help="check every raw tree through six leaves and inject a bad ss rule",
    )
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    args = parser.parse_args()
    try:
        report = build_report(args.growth_leaves, deep=args.deep)
    except (ValueError, CertificateMismatch) as error:
        raise SystemExit(str(error))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    elif args.command == "test":
        exhaustive = report["default_evidence"]["bounded_exhaustive_certificate"]
        print(
            "PASS universal shadow adjunction: "
            f"{exhaustive['raw_tree_count']} trees, "
            f"{exhaustive['one_step_branch_join_checks']} local branches, "
            f"deep={args.deep}"
        )
    else:
        print_human(report)


if __name__ == "__main__":
    main()
