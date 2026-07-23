#!/usr/bin/env python3
"""Exact probe portfolios for distinguishing non-associative bracket trees.

Each unordered tree pair is a claim.  A probe fails that claim exactly when
both trees have the same exact ``bracket_garden`` phenotype.  Selecting probes
is therefore a finite set-cover problem over pair claims.

The full multilinear signatures remain the authority: every reported
portfolio is revalidated as a projection of those signatures.  Greedy search
is only an upper bound.  Optimality is reported only after a counting bound
matches a witness or an exact branch-and-bound search completes.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import pathlib
import sys
import time
import types
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Sequence


def _load_oracle() -> tuple[Any, str]:
    """Load the sibling exact oracle, with a type-only Python 3.9 shim.

    ``bracket_garden`` targets Python 3.10 (``slots=`` and ``X | Y`` types).
    The Android NDK runtime available in this workspace is Python 3.9.  On that
    runtime only, this loader removes dataclass slots and replaces the runtime
    type alias.  Algebra, trees, multiplication, evaluation, and signatures
    are executed from the oracle source unchanged.
    """

    if sys.version_info >= (3, 10):
        import bracket_garden as oracle

        return oracle, "native-import"

    source_path = pathlib.Path(__file__).with_name("bracket_garden.py")
    source = source_path.read_text(encoding="utf-8")
    import_line = "from typing import Iterable, Sequence, TypeAlias"
    alias_line = "Tree: TypeAlias = Leaf | Branch"
    decorator = "@dataclass(frozen=True, slots=True)"
    if source.count(import_line) != 1 or source.count(alias_line) != 1:
        raise RuntimeError("bracket_garden compatibility anchors changed")
    if decorator not in source:
        raise RuntimeError("bracket_garden dataclass anchor changed")

    compatible = source.replace(
        import_line,
        "from typing import Iterable, Sequence\nTypeAlias = object",
    )
    compatible = compatible.replace(alias_line, "Tree: TypeAlias = object")
    compatible = compatible.replace(decorator, "@dataclass(frozen=True)")

    module_name = "_bracket_garden_exact_compat"
    oracle = types.ModuleType(module_name)
    oracle.__file__ = str(source_path)
    oracle.__package__ = ""
    sys.modules[module_name] = oracle
    exec(compile(compatible, str(source_path), "exec"), oracle.__dict__)
    return oracle, "python-3.9-type-shim"


ORACLE, ORACLE_RUNTIME = _load_oracle()


def popcount(value: int) -> int:
    """Return the number of set bits on both Python 3.9 and newer."""

    method = getattr(int, "bit_count", None)
    return method(value) if method is not None else bin(value).count("1")


def ceil_log(count: int, base: int) -> int:
    """Smallest k with base**k >= count, without floating-point rounding."""

    if count <= 1:
        return 0
    if base <= 1:
        raise ValueError("a non-trivial code alphabet needs at least two symbols")
    power = 1
    exponent = 0
    while power < count:
        power *= base
        exponent += 1
    return exponent


def pair_index(tree_count: int, left: int, right: int) -> int:
    """Index ``(left,right)`` in itertools.combinations(range(T), 2)."""

    if not 0 <= left < right < tree_count:
        raise ValueError("pair indices must satisfy 0 <= left < right < tree_count")
    return left * (2 * tree_count - left - 1) // 2 + right - left - 1


@dataclass(frozen=True)
class PairClaim:
    index: int
    left: int
    right: int


@dataclass(frozen=True)
class Probe:
    word: str
    assignment_index: int
    failure_mask: int
    outcome_count: int


@dataclass(frozen=True)
class GreedyTraceStep:
    word: str
    gain: int
    residual_claims: int


@dataclass
class SearchStats:
    nodes: int = 0
    memo_hits: int = 0
    capacity_prunes: int = 0
    terminal_checks: int = 0
    antichain_inputs: int = 0
    antichain_outputs: int = 0


@dataclass
class AdaptiveSearchStats:
    states: int = 0
    memo_hits: int = 0
    tests_considered: int = 0
    capacity_prunes: int = 0


@dataclass(frozen=True)
class DecisionCertificate:
    probes: int
    status: str
    witness: tuple[str, ...]
    stats: SearchStats
    complete: bool


@dataclass(frozen=True)
class ExactCertificate:
    kind: str
    complete: bool
    optimum: int | None
    certified_lower_bound: int
    decisions: tuple[DecisionCertificate, ...]


@dataclass(frozen=True)
class AdaptiveCertificate:
    complete: bool
    optimum_depth: int | None
    information_lower_bound: int
    validated_upper_bound: int
    root_probe: str | None
    decision_tree: dict[str, Any] | None
    decision_tree_digest: str | None
    stats: AdaptiveSearchStats


@dataclass(frozen=True)
class Problem:
    leaves: int
    trees: tuple[Any, ...]
    assignments: tuple[tuple[Any, ...], ...]
    signatures: tuple[tuple[Any, ...], ...]
    claims: tuple[PairClaim, ...]
    probes: tuple[Probe, ...]
    full_claim_mask: int
    full_signatures_distinct: bool
    signature_digest: str
    claim_matrix_digest: str
    signed_basis_closed: bool

    @property
    def tree_count(self) -> int:
        return len(self.trees)

    @property
    def claim_count(self) -> int:
        return len(self.claims)

    @property
    def max_probe_outcomes(self) -> int:
        return max((probe.outcome_count for probe in self.probes), default=1)

    @property
    def information_lower_bound(self) -> int:
        return ceil_log(self.tree_count, self.max_probe_outcomes)


# Exploratory witnesses are data, not axioms.  They are accepted only after a
# fresh full-signature projection proves that every claim is separated.
KNOWN_WITNESSES: dict[int, tuple[str, ...]] = {
    7: ("1hhqq1h", "hhh1hhq", "1h1hhhh", "hhqh1hh", "hh1hqhh"),
}


def _element_token(element: Any) -> str:
    return f"{element.r},{element.h},{element.q}"


def _signature_digest(signatures: Sequence[Sequence[Any]]) -> str:
    digest = hashlib.sha256()
    for tree_index, signature in enumerate(signatures):
        digest.update(f"T{tree_index}:".encode("ascii"))
        for element in signature:
            digest.update(_element_token(element).encode("ascii"))
            digest.update(b";")
        digest.update(b"\n")
    return digest.hexdigest()


def _claim_matrix_digest(probes: Sequence[Probe]) -> str:
    digest = hashlib.sha256()
    for probe in probes:
        digest.update(probe.word.encode("ascii"))
        digest.update(b":")
        digest.update(format(probe.failure_mask, "x").encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def build_problem(leaves: int) -> Problem:
    """Materialize every Catalan tree, full signature, probe, and pair claim."""

    if leaves < 1:
        raise ValueError("leaves must be positive")
    if leaves > ORACLE.MAP_AUDIT_LIMIT:
        raise ValueError(
            f"full-signature tomography is bounded at {ORACLE.MAP_AUDIT_LIMIT} leaves"
        )

    trees = ORACLE.full_binary_trees(leaves)
    assignments = ORACLE.basis_assignments(leaves)
    signatures = tuple(ORACLE.multilinear_signature(tree) for tree in trees)
    claims = tuple(
        PairClaim(index, left, right)
        for index, (left, right) in enumerate(
            itertools.combinations(range(len(trees)), 2)
        )
    )
    full_claim_mask = (1 << len(claims)) - 1
    signed_basis = frozenset(ORACLE.SIGNED_BASIS)
    signed_basis_closed = all(
        value in signed_basis for signature in signatures for value in signature
    )

    # Behavior-equivalent words are interchangeable for claim coverage.  Keep
    # the lexicographically first word as the deterministic representative.
    by_failure: dict[int, Probe] = {}
    tree_count = len(trees)
    for assignment_index, assignment in enumerate(assignments):
        groups: dict[Any, list[int]] = {}
        for tree_index, signature in enumerate(signatures):
            groups.setdefault(signature[assignment_index], []).append(tree_index)
        failure_mask = 0
        for group in groups.values():
            for left, right in itertools.combinations(group, 2):
                failure_mask |= 1 << pair_index(tree_count, left, right)
        word = ORACLE.basis_word(assignment)
        candidate = Probe(word, assignment_index, failure_mask, len(groups))
        previous = by_failure.get(failure_mask)
        if previous is None or word < previous.word:
            by_failure[failure_mask] = candidate

    probes = tuple(sorted(by_failure.values(), key=lambda probe: probe.word))
    return Problem(
        leaves=leaves,
        trees=trees,
        assignments=assignments,
        signatures=signatures,
        claims=claims,
        probes=probes,
        full_claim_mask=full_claim_mask,
        full_signatures_distinct=len(set(signatures)) == len(signatures),
        signature_digest=_signature_digest(signatures),
        claim_matrix_digest=_claim_matrix_digest(probes),
        signed_basis_closed=signed_basis_closed,
    )


def residual_claims(problem: Problem, portfolio: Sequence[Probe]) -> int:
    residual = problem.full_claim_mask
    for probe in portfolio:
        residual &= probe.failure_mask
    return residual


def validate_portfolio(problem: Problem, portfolio: Sequence[Probe]) -> bool:
    """Validate by projecting the authoritative full signatures."""

    if not problem.full_signatures_distinct:
        return False
    codes = {
        tuple(signature[probe.assignment_index] for probe in portfolio)
        for signature in problem.signatures
    }
    return len(codes) == problem.tree_count and residual_claims(problem, portfolio) == 0


def probes_by_word(problem: Problem, words: Iterable[str]) -> tuple[Probe, ...]:
    lookup = {probe.word: probe for probe in problem.probes}
    selected: list[Probe] = []
    for word in words:
        if word not in lookup:
            raise ValueError(f"probe {word!r} is absent from the behavior representatives")
        selected.append(lookup[word])
    return tuple(selected)


def greedy_portfolio(
    problem: Problem,
) -> tuple[tuple[Probe, ...], tuple[GreedyTraceStep, ...]]:
    """Deterministic maximum-gain greedy followed by reverse deletion."""

    if not problem.full_signatures_distinct:
        return (), ()
    residual = problem.full_claim_mask
    selected: list[Probe] = []
    trace: list[GreedyTraceStep] = []
    while residual:
        residual_count = popcount(residual)
        best = min(
            problem.probes,
            key=lambda probe: (
                -(residual_count - popcount(residual & probe.failure_mask)),
                probe.word,
            ),
        )
        next_residual = residual & best.failure_mask
        gain = residual_count - popcount(next_residual)
        if gain == 0:
            raise AssertionError("full signatures differ, but greedy cannot hit a claim")
        selected.append(best)
        residual = next_residual
        trace.append(GreedyTraceStep(best.word, gain, popcount(residual)))

    # Delete in reverse selection order; this is deterministic and cannot add
    # probes.  Preserve the original order of survivors.
    kept = selected[:]
    for index in range(len(kept) - 1, -1, -1):
        trial = kept[:index] + kept[index + 1 :]
        if residual_claims(problem, trial) == 0:
            kept = trial
    if not validate_portfolio(problem, kept):
        raise AssertionError("greedy portfolio failed full-signature validation")
    return tuple(kept), tuple(trace)


def nondominated_probes(probes: Sequence[Probe]) -> tuple[Probe, ...]:
    """Remove probes whose distinguished-claim set is a strict subset."""

    ordered = sorted(probes, key=lambda probe: (popcount(probe.failure_mask), probe.word))
    kept: list[Probe] = []
    for probe in ordered:
        # F_a subset F_b means a leaves no more failures and dominates b.
        if any(
            other.failure_mask != probe.failure_mask
            and (other.failure_mask & probe.failure_mask) == other.failure_mask
            for other in kept
        ):
            continue
        kept.append(probe)
    return tuple(sorted(kept, key=lambda probe: probe.word))


class ExactSolver:
    """Exact branch-and-bound over residual pair-claim masks."""

    def __init__(self, problem: Problem, time_limit: float | None = None) -> None:
        self.problem = problem
        self.probes = nondominated_probes(problem.probes)
        self.words = tuple(probe.word for probe in self.probes)
        self.failures = tuple(probe.failure_mask for probe in self.probes)
        self.candidate_count = len(self.probes)
        self.all_candidates = (1 << self.candidate_count) - 1
        self.coverers = [0] * problem.claim_count
        for candidate_index, failure in enumerate(self.failures):
            coverage = problem.full_claim_mask ^ failure
            while coverage:
                bit = coverage & -coverage
                self.coverers[bit.bit_length() - 1] |= 1 << candidate_index
                coverage -= bit
        self.coverer_counts = tuple(popcount(mask) for mask in self.coverers)
        self.incident_masks = [0] * problem.tree_count
        for claim in problem.claims:
            bit = 1 << claim.index
            self.incident_masks[claim.left] |= bit
            self.incident_masks[claim.right] |= bit
        self.deadline = None if time_limit is None else time.perf_counter() + time_limit

    def _expired(self) -> bool:
        return self.deadline is not None and time.perf_counter() >= self.deadline

    def decide(self, probe_budget: int) -> DecisionCertificate:
        stats = SearchStats()
        memo: set[tuple[int, int]] = set()
        timed_out = False

        def search(residual: int, remaining: int) -> tuple[str, ...] | None:
            nonlocal timed_out
            stats.nodes += 1
            if stats.nodes % 128 == 0 and self._expired():
                timed_out = True
                return None
            if residual == 0:
                return ()
            key = (residual, remaining)
            if key in memo:
                stats.memo_hits += 1
                return None
            if remaining == 0:
                memo.add(key)
                return None

            # Residual claims are equality classes under the already selected
            # response tuple, hence a disjoint union of cliques.  A future probe
            # can split a class into at most max_probe_outcomes subclasses.
            max_class = max(
                (popcount(residual & incident) + 1 for incident in self.incident_masks),
                default=1,
            )
            if max_class > self.problem.max_probe_outcomes**remaining:
                stats.capacity_prunes += 1
                memo.add(key)
                return None

            if remaining == 1:
                possible = self.all_candidates
                claims = residual
                while claims and possible:
                    bit = claims & -claims
                    possible &= self.coverers[bit.bit_length() - 1]
                    claims -= bit
                stats.terminal_checks += 1
                if possible:
                    candidate = (possible & -possible).bit_length() - 1
                    return (self.words[candidate],)
                memo.add(key)
                return None

            # Every completion must cover this residual claim.  The globally
            # rarest such claim gives the smallest complete branching family.
            claims = residual
            pivot = -1
            pivot_count = self.candidate_count + 1
            while claims:
                bit = claims & -claims
                claim_index = bit.bit_length() - 1
                count = self.coverer_counts[claim_index]
                if count < pivot_count:
                    pivot = claim_index
                    pivot_count = count
                claims -= bit
            if pivot < 0 or pivot_count == 0:
                memo.add(key)
                return None

            # Two probes producing the same next residual are interchangeable.
            # A next residual that strictly contains another is also dominated.
            branches: dict[int, int] = {}
            candidates = self.coverers[pivot]
            while candidates:
                bit = candidates & -candidates
                candidate = bit.bit_length() - 1
                next_residual = residual & self.failures[candidate]
                previous = branches.get(next_residual)
                if previous is None or self.words[candidate] < self.words[previous]:
                    branches[next_residual] = candidate
                candidates -= bit
            stats.antichain_inputs += len(branches)
            ordered = sorted(
                branches.items(),
                key=lambda item: (popcount(item[0]), self.words[item[1]]),
            )
            antichain: list[tuple[int, int]] = []
            for next_residual, candidate in ordered:
                if any(
                    (better & next_residual) == better
                    for better, _ in antichain
                ):
                    continue
                antichain.append((next_residual, candidate))
            stats.antichain_outputs += len(antichain)

            for next_residual, candidate in antichain:
                suffix = search(next_residual, remaining - 1)
                if suffix is not None:
                    return (self.words[candidate],) + suffix
                if timed_out:
                    return None
            memo.add(key)
            return None

        witness = search(self.problem.full_claim_mask, probe_budget)
        if timed_out:
            return DecisionCertificate(probe_budget, "timeout", (), stats, False)
        if witness is None:
            return DecisionCertificate(probe_budget, "infeasible", (), stats, True)
        portfolio = probes_by_word(self.problem, witness)
        if not validate_portfolio(self.problem, portfolio):
            raise AssertionError("exact-search witness failed authoritative validation")
        return DecisionCertificate(probe_budget, "feasible", witness, stats, True)


def exact_optimum(
    problem: Problem,
    upper_portfolio: Sequence[Probe],
    *,
    time_limit: float | None = None,
) -> ExactCertificate:
    """Prove an optimum or return the exact lower bound reached before timeout."""

    lower = problem.information_lower_bound
    upper = len(upper_portfolio)
    if lower == upper:
        return ExactCertificate("information-bound-match", True, upper, lower, ())
    solver = ExactSolver(problem, time_limit=time_limit)
    decisions: list[DecisionCertificate] = []
    certified_lower = lower
    for budget in range(lower, upper):
        decision = solver.decide(budget)
        decisions.append(decision)
        if decision.status == "timeout":
            return ExactCertificate(
                "exhaustive-branch-and-bound", False, None, certified_lower, tuple(decisions)
            )
        if decision.status == "feasible":
            return ExactCertificate(
                "exhaustive-branch-and-bound",
                True,
                budget,
                budget,
                tuple(decisions),
            )
        certified_lower = budget + 1
    return ExactCertificate(
        "exhaustive-branch-and-bound", True, upper, upper, tuple(decisions)
    )


def certify_lower_budget(
    problem: Problem,
    budget: int,
    *,
    time_limit: float | None = None,
) -> ExactCertificate:
    """Attempt only the budgets needed to certify OPT > budget."""

    lower = problem.information_lower_bound
    if budget < lower:
        return ExactCertificate("information-bound", True, None, lower, ())
    solver = ExactSolver(problem, time_limit=time_limit)
    decisions: list[DecisionCertificate] = []
    certified_lower = lower
    for current in range(lower, budget + 1):
        decision = solver.decide(current)
        decisions.append(decision)
        if decision.status == "timeout":
            return ExactCertificate(
                "exhaustive-branch-and-bound", False, None, certified_lower, tuple(decisions)
            )
        if decision.status == "feasible":
            return ExactCertificate(
                "exhaustive-branch-and-bound", True, current, current, tuple(decisions)
            )
        certified_lower = current + 1
    return ExactCertificate(
        "exhaustive-branch-and-bound", True, None, certified_lower, tuple(decisions)
    )


def adaptive_optimum(
    problem: Problem,
    *,
    validated_upper_bound: int,
    time_limit: float | None = None,
) -> AdaptiveCertificate:
    """Solve the exact minimax adaptive decision-tree problem.

    A state is the bit set of trees still compatible with observations.  Probe
    outcome labels are retained only when rendering the witness tree; search
    depends on the induced partition, so behavior-equivalent partitions are
    merged exactly.
    """

    stats = AdaptiveSearchStats()
    deadline = None if time_limit is None else time.perf_counter() + time_limit
    maximum_outcomes = problem.max_probe_outcomes
    tree_count = problem.tree_count
    lower = problem.information_lower_bound

    partitions: list[tuple[str, tuple[tuple[str, int], ...]]] = []
    for probe in problem.probes:
        groups: dict[Any, int] = {}
        for tree_index, signature in enumerate(problem.signatures):
            outcome = signature[probe.assignment_index]
            groups[outcome] = groups.get(outcome, 0) | (1 << tree_index)
        labelled = tuple(
            sorted(
                ((_element_token(outcome), mask) for outcome, mask in groups.items()),
                key=lambda item: item[0],
            )
        )
        partitions.append((probe.word, labelled))
    partitions.sort(key=lambda item: item[0])

    memo: dict[tuple[int, int], bool] = {}
    policy: dict[tuple[int, int], str] = {}
    timed_out = False

    def expired() -> bool:
        return deadline is not None and time.perf_counter() >= deadline

    def solve(state: int, remaining: int) -> bool:
        nonlocal timed_out
        stats.states += 1
        if stats.states % 128 == 0 and expired():
            timed_out = True
            return False
        size = popcount(state)
        if size <= 1:
            return True
        key = (state, remaining)
        known = memo.get(key)
        if known is not None:
            stats.memo_hits += 1
            return known
        if remaining == 0 or size > maximum_outcomes**remaining:
            stats.capacity_prunes += 1
            memo[key] = False
            return False

        # Favor balanced partitions for a quick witness, but enumerate every
        # distinct restricted partition before declaring failure.
        capacity = maximum_outcomes ** (remaining - 1)
        seen: set[tuple[int, ...]] = set()
        candidates: list[tuple[int, int, str, tuple[int, ...]]] = []
        for word, blocks in partitions:
            restricted = tuple(
                sorted(mask & state for _, mask in blocks if mask & state)
            )
            if restricted in seen:
                continue
            seen.add(restricted)
            if len(restricted) <= 1:
                continue
            sizes = tuple(popcount(group) for group in restricted)
            if max(sizes) > capacity:
                continue
            candidates.append((max(sizes), sum(size_ * size_ for size_ in sizes), word, restricted))
        candidates.sort()

        for _, __, word, groups in candidates:
            stats.tests_considered += 1
            if all(solve(group, remaining - 1) for group in groups):
                memo[key] = True
                policy[key] = word
                return True
            if timed_out:
                return False
        memo[key] = False
        return False

    root = (1 << tree_count) - 1
    optimum: int | None = None
    for depth in range(lower, validated_upper_bound + 1):
        if solve(root, depth):
            optimum = depth
            break
        if timed_out:
            break

    if timed_out or optimum is None:
        return AdaptiveCertificate(
            complete=False,
            optimum_depth=None,
            information_lower_bound=lower,
            validated_upper_bound=validated_upper_bound,
            root_probe=None,
            decision_tree=None,
            decision_tree_digest=None,
            stats=stats,
        )

    partition_lookup = {word: blocks for word, blocks in partitions}

    def render(state: int, remaining: int) -> dict[str, Any]:
        if popcount(state) == 1:
            tree_index = (state & -state).bit_length() - 1
            return {
                "tree": ORACLE.tree_id(problem.leaves, tree_index, problem.tree_count)
            }
        word = policy[(state, remaining)]
        branches: dict[str, Any] = {}
        for outcome, block in partition_lookup[word]:
            child = state & block
            if child:
                branches[outcome] = render(child, remaining - 1)
        return {"probe": word, "branches": branches}

    decision_tree = render(root, optimum)

    # Independently walk the rendered witness against the authoritative full
    # signature partitions.  This catches rendering or outcome-label drift,
    # not merely search-state errors.
    def validate_tree(node: dict[str, Any], state: int, depth: int) -> int:
        if "tree" in node:
            if popcount(state) != 1:
                raise AssertionError("adaptive witness terminated on a collision class")
            tree_index = (state & -state).bit_length() - 1
            expected = ORACLE.tree_id(problem.leaves, tree_index, problem.tree_count)
            if node["tree"] != expected:
                raise AssertionError("adaptive witness leaf identity drifted")
            return depth
        word = node.get("probe")
        branches = node.get("branches")
        if word not in partition_lookup or not isinstance(branches, dict):
            raise AssertionError("adaptive witness contains an invalid decision node")
        expected_children = {
            outcome: state & block
            for outcome, block in partition_lookup[word]
            if state & block
        }
        if set(branches) != set(expected_children):
            raise AssertionError("adaptive witness outcome labels drifted")
        return max(
            validate_tree(branches[outcome], child, depth + 1)
            for outcome, child in expected_children.items()
        )

    if validate_tree(decision_tree, root, 0) > optimum:
        raise AssertionError("adaptive witness exceeds its certified depth")
    encoded = json.dumps(decision_tree, sort_keys=True, separators=(",", ":")).encode("utf-8")
    root_probe = decision_tree.get("probe")
    return AdaptiveCertificate(
        complete=True,
        optimum_depth=optimum,
        information_lower_bound=lower,
        validated_upper_bound=optimum,
        root_probe=root_probe,
        decision_tree=decision_tree,
        decision_tree_digest=hashlib.sha256(encoded).hexdigest(),
        stats=stats,
    )


def best_validated_upper(problem: Problem) -> tuple[tuple[Probe, ...], str, tuple[GreedyTraceStep, ...]]:
    greedy, trace = greedy_portfolio(problem)
    best = greedy
    source = "greedy+reverse-delete"
    known = KNOWN_WITNESSES.get(problem.leaves)
    if known is not None:
        try:
            seeded = probes_by_word(problem, known)
        except ValueError:
            seeded = ()
        if seeded and len(seeded) < len(best) and validate_portfolio(problem, seeded):
            best = seeded
            source = "validated-exploratory-witness"
    return best, source, trace


def detailed_claims(problem: Problem, portfolio: Sequence[Probe]) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []
    for claim in problem.claims:
        witness: str | None = None
        left_signature = problem.signatures[claim.left]
        right_signature = problem.signatures[claim.right]
        for probe in portfolio:
            if left_signature[probe.assignment_index] != right_signature[probe.assignment_index]:
                witness = probe.word
                break
        details.append(
            {
                "claim_id": f"P{problem.leaves}:{claim.index:04d}",
                "left_tree": ORACLE.tree_id(problem.leaves, claim.left, problem.tree_count),
                "right_tree": ORACLE.tree_id(problem.leaves, claim.right, problem.tree_count),
                "failure_mode": "same response under every selected probe",
                "distinguishing_probe": witness,
                "satisfied": witness is not None,
            }
        )
    return details


def decision_to_dict(decision: DecisionCertificate) -> dict[str, Any]:
    return {
        "probes": decision.probes,
        "status": decision.status,
        "complete": decision.complete,
        "witness": list(decision.witness),
        "stats": asdict(decision.stats),
    }


def report_problem(
    problem: Problem,
    *,
    exact: bool,
    exact_lower_budget: int | None = None,
    time_limit: float | None = None,
    emit_claims: bool = False,
) -> dict[str, Any]:
    upper, upper_source, greedy_trace = best_validated_upper(problem)
    greedy, _ = greedy_portfolio(problem)
    if exact_lower_budget is not None:
        certificate = certify_lower_budget(
            problem, exact_lower_budget, time_limit=time_limit
        )
    elif exact:
        certificate = exact_optimum(problem, upper, time_limit=time_limit)
    else:
        certificate = ExactCertificate(
            "not-requested", False, None, problem.information_lower_bound, ()
        )

    portfolio = upper
    if certificate.optimum is not None:
        for decision in certificate.decisions:
            if decision.status == "feasible":
                candidate = probes_by_word(problem, decision.witness)
                if len(candidate) <= len(portfolio):
                    portfolio = candidate
    validated = validate_portfolio(problem, portfolio)
    if not validated and problem.tree_count > 1:
        raise AssertionError("reported portfolio is not a full-signature separator")

    adaptive = adaptive_optimum(
        problem,
        validated_upper_bound=len(portfolio),
        time_limit=time_limit,
    )

    payload: dict[str, Any] = {
        "leaves": problem.leaves,
        "trees": problem.tree_count,
        "pair_claims": problem.claim_count,
        "raw_probe_words": len(problem.assignments),
        "behavior_unique_probes": len(problem.probes),
        "exact_nondominated_probes": len(nondominated_probes(problem.probes)),
        "oracle": {
            "module": str(pathlib.Path(ORACLE.__file__).resolve()),
            "runtime": ORACLE_RUNTIME,
            "full_signatures_distinct": problem.full_signatures_distinct,
            "signed_basis_closed": problem.signed_basis_closed,
            "signature_sha256": problem.signature_digest,
            "claim_matrix_sha256": problem.claim_matrix_digest,
        },
        "bounds": {
            "six_symbol_information_lower": ceil_log(problem.tree_count, 6),
            "observed_outcome_information_lower": problem.information_lower_bound,
            "max_probe_outcomes": problem.max_probe_outcomes,
            "certified_lower": certificate.certified_lower_bound,
            "validated_upper": len(portfolio),
        },
        "greedy": {
            "portfolio": [probe.word for probe in greedy],
            "size": len(greedy),
            "trace": [asdict(step) for step in greedy_trace],
        },
        "best_portfolio": {
            "portfolio": [probe.word for probe in portfolio],
            "size": len(portfolio),
            "source": (
                "exact-branch-and-bound"
                if len(portfolio) < len(upper)
                else upper_source
            ),
            "full_signature_validated": validated,
            "residual_claims": popcount(residual_claims(problem, portfolio)),
        },
        "exact_certificate": {
            "kind": certificate.kind,
            "complete": certificate.complete,
            "optimal": certificate.complete and certificate.optimum is not None,
            "optimum": certificate.optimum,
            "decisions": [decision_to_dict(item) for item in certificate.decisions],
        },
        "adaptive_decision_tree": {
            "complete": adaptive.complete,
            "optimal": adaptive.complete and adaptive.optimum_depth is not None,
            "worst_case_depth": adaptive.optimum_depth,
            "information_lower_bound": adaptive.information_lower_bound,
            "validated_upper_bound": adaptive.validated_upper_bound,
            "root_probe": adaptive.root_probe,
            "tree_sha256": adaptive.decision_tree_digest,
            "stats": asdict(adaptive.stats),
            "decision_tree": adaptive.decision_tree,
        },
    }
    if emit_claims:
        payload["claims"] = detailed_claims(problem, portfolio)
    return payload


def _human_report(payload: dict[str, Any]) -> str:
    bounds = payload["bounds"]
    exact = payload["exact_certificate"]
    best = payload["best_portfolio"]
    adaptive = payload["adaptive_decision_tree"]
    lines = [
        (
            f"n={payload['leaves']}  trees={payload['trees']}  "
            f"claims={payload['pair_claims']}  words={payload['raw_probe_words']}  "
            f"unique={payload['behavior_unique_probes']}"
        ),
        (
            f"bounds: {bounds['certified_lower']} <= OPT <= "
            f"{bounds['validated_upper']}  max-outcomes={bounds['max_probe_outcomes']}"
        ),
        (
            f"greedy[{payload['greedy']['size']}]: "
            + " ".join(payload["greedy"]["portfolio"])
        ),
        f"best[{best['size']}]: " + " ".join(best["portfolio"]),
        (
            f"exact: kind={exact['kind']} complete={str(exact['complete']).lower()} "
            f"optimal={str(exact['optimal']).lower()} optimum={exact['optimum']}"
        ),
        (
            f"adaptive: depth={adaptive['worst_case_depth']} "
            f"complete={str(adaptive['complete']).lower()} root={adaptive['root_probe']}"
        ),
    ]
    for decision in exact["decisions"]:
        stats = decision["stats"]
        lines.append(
            f"  k={decision['probes']}: {decision['status']} "
            f"nodes={stats['nodes']} capacity-prunes={stats['capacity_prunes']}"
        )
    lines.append(
        f"oracle: full-signatures={payload['oracle']['full_signatures_distinct']} "
        f"residual-claims={best['residual_claims']} runtime={payload['oracle']['runtime']}"
    )
    return "\n".join(lines)


def _atlas_table(payloads: Sequence[dict[str, Any]]) -> str:
    headers = ("n", "trees", "claims", "unique", "info", "cert", "upper", "opt", "adaptive", "portfolio")
    rows = []
    for payload in payloads:
        exact = payload["exact_certificate"]
        rows.append(
            (
                str(payload["leaves"]),
                str(payload["trees"]),
                str(payload["pair_claims"]),
                str(payload["behavior_unique_probes"]),
                str(payload["bounds"]["observed_outcome_information_lower"]),
                str(payload["bounds"]["certified_lower"]),
                str(payload["bounds"]["validated_upper"]),
                str(exact["optimum"]) if exact["optimal"] else "?",
                str(payload["adaptive_decision_tree"]["worst_case_depth"]),
                " ".join(payload["best_portfolio"]["portfolio"]),
            )
        )
    widths = [max(len(headers[i]), *(len(row[i]) for row in rows)) for i in range(len(headers))]
    lines = ["  ".join(headers[i].ljust(widths[i]) for i in range(len(headers)))]
    lines.append("  ".join("-" * width for width in widths))
    for row in rows:
        lines.append("  ".join(row[i].ljust(widths[i]) for i in range(len(row))))
    return "\n".join(lines)


def run_self_tests(deep: bool) -> dict[str, Any]:
    expected = {
        3: {"trees": 2, "greedy": 1, "optimum": 1, "adaptive": 1},
        4: {"trees": 5, "greedy": 2, "optimum": 2, "adaptive": 2},
        5: {"trees": 14, "greedy": 3, "optimum": 3, "adaptive": 3},
        6: {"trees": 42, "greedy": 5, "optimum": 4, "adaptive": 3},
    }
    cases: list[dict[str, Any]] = []
    for leaves, wanted in expected.items():
        problem = build_problem(leaves)
        report = report_problem(problem, exact=True)
        assert problem.tree_count == wanted["trees"]
        assert report["greedy"]["size"] == wanted["greedy"]
        assert report["exact_certificate"]["complete"]
        assert report["exact_certificate"]["optimum"] == wanted["optimum"]
        assert report["adaptive_decision_tree"]["complete"]
        assert report["adaptive_decision_tree"]["worst_case_depth"] == wanted["adaptive"]
        assert report["best_portfolio"]["residual_claims"] == 0
        assert problem.signed_basis_closed
        cases.append(
            {
                "leaves": leaves,
                "status": "passed",
                "optimum": wanted["optimum"],
                "signature_sha256": problem.signature_digest,
            }
        )

    if deep:
        problem = build_problem(7)
        report = report_problem(problem, exact=False)
        assert report["greedy"]["size"] == 6
        assert report["best_portfolio"]["size"] == 5
        assert report["best_portfolio"]["residual_claims"] == 0
        assert report["adaptive_decision_tree"]["complete"]
        assert report["adaptive_decision_tree"]["worst_case_depth"] == 4
        lower = certify_lower_budget(problem, 3)
        assert lower.complete and lower.certified_lower_bound == 4
        assert lower.optimum is None
        cases.append(
            {
                "leaves": 7,
                "status": "passed",
                "certified_interval": [4, 5],
                "decision": decision_to_dict(lower.decisions[-1]),
                "signature_sha256": problem.signature_digest,
            }
        )

    return {
        "status": "passed",
        "profile": "deep" if deep else "default",
        "oracle_runtime": ORACLE_RUNTIME,
        "cases": cases,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit = subparsers.add_parser("audit", help="audit one leaf count")
    audit.add_argument("--leaves", type=int, required=True)
    exact_group = audit.add_mutually_exclusive_group()
    exact_group.add_argument("--exact", action="store_true", help="run exact optimization")
    exact_group.add_argument("--no-exact", action="store_true", help="keep bounds only")
    audit.add_argument("--time-limit", type=float, default=None)
    audit.add_argument("--emit-claims", action="store_true")
    audit.add_argument("--json", action="store_true")

    atlas = subparsers.add_parser("atlas", help="survey a range of leaf counts")
    atlas.add_argument("--min-leaves", type=int, default=3)
    atlas.add_argument("--max-leaves", type=int, default=7)
    atlas.add_argument("--exact-through", type=int, default=6)
    atlas.add_argument(
        "--deep",
        action="store_true",
        help="also certify that n=7 cannot be solved with three probes",
    )
    atlas.add_argument("--json", action="store_true")

    tests = subparsers.add_parser("self-test", help="run deterministic regression checks")
    tests.add_argument("--deep", action="store_true")
    tests.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "self-test":
        result = run_self_tests(args.deep)
        print(json.dumps(result, indent=2, sort_keys=True) if args.json else (
            f"self-test {result['profile']}: {result['status']} "
            f"({len(result['cases'])} cases, runtime={ORACLE_RUNTIME})"
        ))
        return 0

    if args.command == "audit":
        problem = build_problem(args.leaves)
        exact = args.exact or (not args.no_exact and args.leaves <= 6)
        payload = report_problem(
            problem,
            exact=exact,
            time_limit=args.time_limit,
            emit_claims=args.emit_claims,
        )
        print(json.dumps(payload, indent=2, sort_keys=True) if args.json else _human_report(payload))
        return 0

    if args.min_leaves < 1 or args.max_leaves < args.min_leaves:
        raise ValueError("atlas range must satisfy 1 <= min <= max")
    payloads: list[dict[str, Any]] = []
    for leaves in range(args.min_leaves, args.max_leaves + 1):
        problem = build_problem(leaves)
        if leaves <= args.exact_through:
            payload = report_problem(problem, exact=True)
        elif args.deep and leaves == 7:
            payload = report_problem(problem, exact=False, exact_lower_budget=3)
        else:
            payload = report_problem(problem, exact=False)
        payloads.append(payload)
    print(
        json.dumps(payloads, indent=2, sort_keys=True)
        if args.json
        else _atlas_table(payloads)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
