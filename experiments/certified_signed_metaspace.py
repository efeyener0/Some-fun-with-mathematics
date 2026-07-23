"""Certified signed-transformation fast path for the chiral operator monoid.

Every matrix in the 192-state combined monoid sends each basis vector to one
signed basis vector.  Such a matrix is encoded by three values in
``{+/-1, +/-2, +/-3}``: code[j] says where basis vector ``j`` is sent.

The compact composition law is proved by the column action and is checked
against the authoritative 3x3 integer-matrix implementation.  The generated
state-id transition table is therefore a derived accelerator, never the owner
of mathematical truth.  Inputs outside the signed-action domain fall back to
the exact matrix lane.
"""

from __future__ import annotations

import argparse
import json
from collections import deque
from dataclasses import dataclass
from hashlib import sha256
from itertools import product
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from chiral_operator_monoids import (
    HARD_DEPTH_CAP,
    HARD_STATE_CAP,
    I3,
    L_H,
    L_Q,
    R_H,
    R_Q,
    Matrix,
    determinant,
    enumerate_monoid,
    matrix_multiply,
    matrix_rows,
)


SignedCode = Tuple[int, int, int]
TransitionRow = Tuple[int, int, int, int]

SCHEMA_VERSION = 1
SYMBOLS: Tuple[str, ...] = ("Lh", "Lq", "Rh", "Rq")
GENERATOR_MATRICES: Tuple[Matrix, ...] = (L_H, L_Q, R_H, R_Q)
IDENTITY_CODE: SignedCode = (1, 2, 3)
SIGNED_AXES: Tuple[int, ...] = (-3, -2, -1, 1, 2, 3)

# These values bind the derived representation to the literal source model.
# They are filled from the exact compiler and asserted on every execution.
EXPECTED_MODEL_DIGEST = "c42d225ccda025a81fc3941cff9a541d85f1011030885e8553a5b7f64a1c9a3e"
EXPECTED_STATE_DIGEST = "82495596ee42be3ee8c946e5a64ebb93c2b2e9e43e24a074db7181800f02f971"
EXPECTED_TABLE_DIGEST = "8baeb58631b2c08f7c4e6bc88000258c01bec3d28fd1927ac87d21efeea530f7"


class OutsideCertifiedDomain(ValueError):
    """The compact signed-action proof does not cover this matrix."""


class CertificateMismatch(RuntimeError):
    """A derived table or its source-model binding failed validation."""


def stable_digest(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=True, separators=(",", ":"), sort_keys=True
    ).encode("ascii")
    return sha256(payload).hexdigest()


def sign(value: int) -> int:
    if value == 0:
        raise ValueError("zero has no signed-axis orientation")
    return 1 if value > 0 else -1


def validate_code(code: Sequence[int]) -> SignedCode:
    if len(code) != 3 or any(value not in SIGNED_AXES for value in code):
        raise OutsideCertifiedDomain(
            "a signed-action code must contain three values from +/-{1,2,3}"
        )
    return tuple(code)  # type: ignore[return-value]


def encode_matrix(matrix: Matrix) -> SignedCode:
    """Encode a signed-basis action; reject matrices outside the proof domain."""

    code: List[int] = []
    for column in range(3):
        nonzero = [
            (row, matrix[3 * row + column])
            for row in range(3)
            if matrix[3 * row + column] != 0
        ]
        if len(nonzero) != 1 or nonzero[0][1] not in (-1, 1):
            raise OutsideCertifiedDomain(
                "each matrix column must contain exactly one entry equal to +/-1"
            )
        row, orientation = nonzero[0]
        code.append(orientation * (row + 1))
    return tuple(code)  # type: ignore[return-value]


def decode_code(code: Sequence[int]) -> Matrix:
    checked = validate_code(code)
    entries = [0] * 9
    for column, target in enumerate(checked):
        entries[3 * (abs(target) - 1) + column] = sign(target)
    return tuple(entries)  # type: ignore[return-value]


def compose_codes(left: Sequence[int], right: Sequence[int]) -> SignedCode:
    """Return the code for ``decode(left) * decode(right)``.

    If ``right[j] = epsilon*k``, the right map sends ``e_j`` to
    ``epsilon*e_k``.  Applying the left map next gives
    ``epsilon * left[k]``.  This is exact, with no numerical approximation.
    """

    left_code = validate_code(left)
    right_code = validate_code(right)
    return tuple(
        sign(target) * left_code[abs(target) - 1] for target in right_code
    )  # type: ignore[return-value]


def absolute_permutation_is_even(code: Sequence[int]) -> bool:
    checked = validate_code(code)
    permutation = tuple(abs(value) for value in checked)
    if len(set(permutation)) != 3:
        raise ValueError("parity is defined here only for signed permutations")
    inversions = sum(
        permutation[left] > permutation[right]
        for left in range(3)
        for right in range(left + 1, 3)
    )
    return inversions % 2 == 0


def is_compiled_monoid_code(code: Sequence[int]) -> bool:
    """Closed-form predicate for the 192-state combined monoid."""

    checked = validate_code(code)
    targets = {abs(value) for value in checked}
    return len(targets) < 3 or absolute_permutation_is_even(checked)


def code_rank(code: Sequence[int]) -> int:
    return len({abs(value) for value in validate_code(code)})


def parity_character(code: Sequence[int]) -> int:
    """Return 0 on singular maps and +/-1 from absolute permutation parity."""

    checked = validate_code(code)
    if code_rank(checked) < 3:
        return 0
    return 1 if absolute_permutation_is_even(checked) else -1


def generated_code_closure(
    generators: Sequence[SignedCode],
) -> Dict[SignedCode, int]:
    """Exact BFS closure in the 216-state ambient signed transformation monoid."""

    checked_generators = tuple(validate_code(generator) for generator in generators)
    depths: Dict[SignedCode, int] = {IDENTITY_CODE: 0}
    queue = deque([IDENTITY_CODE])
    while queue:
        state = queue.popleft()
        for generator in checked_generators:
            target = compose_codes(state, generator)
            if target not in depths:
                depths[target] = depths[state] + 1
                queue.append(target)
    return depths


def model_digest() -> str:
    return stable_digest(
        {
            "schema_version": SCHEMA_VERSION,
            "basis": ["1", "h", "q"],
            "word_extension": "append generator on the right",
            "symbols": list(SYMBOLS),
            "generator_matrices": [list(matrix) for matrix in GENERATOR_MATRICES],
        }
    )


@dataclass(frozen=True)
class CompiledAutomaton:
    states: Tuple[SignedCode, ...]
    transitions: Tuple[TransitionRow, ...]
    state_index: Mapping[SignedCode, int]
    generator_codes: Tuple[SignedCode, ...]
    canonical_words: Tuple[Tuple[str, ...], ...]
    model_fingerprint: str
    state_fingerprint: str
    table_fingerprint: str

    @property
    def identity_state(self) -> int:
        return self.state_index[IDENTITY_CODE]


def enumerate_closed_form_states() -> Tuple[SignedCode, ...]:
    return tuple(
        sorted(
            code
            for code in product(SIGNED_AXES, repeat=3)
            if is_compiled_monoid_code(code)
        )
    )


def build_transition_rows(
    states: Sequence[SignedCode],
    state_index: Mapping[SignedCode, int],
    generator_codes: Sequence[SignedCode],
) -> Tuple[TransitionRow, ...]:
    rows: List[TransitionRow] = []
    for state in states:
        row = tuple(
            state_index[compose_codes(state, generator)]
            for generator in generator_codes
        )
        rows.append(row)  # type: ignore[arg-type]
    return tuple(rows)


def shortest_words(
    transitions: Sequence[TransitionRow], identity_state: int
) -> Tuple[Tuple[str, ...], ...]:
    words: List[Optional[Tuple[str, ...]]] = [None] * len(transitions)
    words[identity_state] = ()
    queue = deque([identity_state])
    while queue:
        source = queue.popleft()
        prefix = words[source]
        assert prefix is not None
        for symbol_index, target in enumerate(transitions[source]):
            if words[target] is None:
                words[target] = prefix + (SYMBOLS[symbol_index],)
                queue.append(target)
    if any(word is None for word in words):
        raise CertificateMismatch("derived transition graph is not fully reachable")
    return tuple(word for word in words if word is not None)


def baseline_mismatches(
    model_fingerprint: str,
    state_fingerprint: str,
    table_fingerprint: str,
) -> List[str]:
    expected = (
        ("model", EXPECTED_MODEL_DIGEST, model_fingerprint),
        ("state", EXPECTED_STATE_DIGEST, state_fingerprint),
        ("table", EXPECTED_TABLE_DIGEST, table_fingerprint),
    )
    return [name for name, wanted, actual in expected if wanted != actual]


def assert_baseline_fingerprints(automaton: CompiledAutomaton) -> None:
    mismatches = baseline_mismatches(
        automaton.model_fingerprint,
        automaton.state_fingerprint,
        automaton.table_fingerprint,
    )
    if mismatches:
        raise CertificateMismatch(
            "stale or changed derived model fingerprint(s): " + ", ".join(mismatches)
        )


def validate_against_exact_oracle(
    automaton: CompiledAutomaton, deep_check: bool
) -> Dict[str, object]:
    """Differentially certify the compact and table lanes."""

    exact = enumerate_monoid(
        "combined",
        GENERATOR_MATRICES,
        HARD_STATE_CAP,
        HARD_DEPTH_CAP,
    )
    if not exact.closed:
        raise CertificateMismatch("authoritative matrix monoid did not close")

    exact_states = exact.states
    decoded_states = {decode_code(code) for code in automaton.states}
    if decoded_states != exact_states:
        raise CertificateMismatch("closed-form state set differs from matrix oracle")

    transition_checks = 0
    for state_id, state in enumerate(automaton.states):
        left_matrix = decode_code(state)
        for symbol_index, generator_matrix in enumerate(GENERATOR_MATRICES):
            target_id = automaton.transitions[state_id][symbol_index]
            table_matrix = decode_code(automaton.states[target_id])
            exact_matrix = matrix_multiply(left_matrix, generator_matrix)
            if table_matrix != exact_matrix:
                raise CertificateMismatch(
                    "transition-table parity failure at state {} symbol {}".format(
                        state_id, SYMBOLS[symbol_index]
                    )
                )
            transition_checks += 1

    exact_depths_by_code = {
        encode_matrix(matrix): depth for matrix, depth in exact.depths.items()
    }
    compiled_depths = {
        state: len(automaton.canonical_words[state_id])
        for state_id, state in enumerate(automaton.states)
    }
    if exact_depths_by_code != compiled_depths:
        raise CertificateMismatch("canonical-word depths differ from exact BFS")

    pair_checks = 0
    character_checks = 0
    maximal_extension_checks = 0
    if deep_check:
        for left in automaton.states:
            left_matrix = decode_code(left)
            for right in automaton.states:
                compact = decode_code(compose_codes(left, right))
                exact_product = matrix_multiply(left_matrix, decode_code(right))
                if compact != exact_product:
                    raise CertificateMismatch("full pair-composition parity failure")
                pair_checks += 1

        ambient = tuple(product(SIGNED_AXES, repeat=3))
        for left in ambient:
            for right in ambient:
                if parity_character(compose_codes(left, right)) != (
                    parity_character(left) * parity_character(right)
                ):
                    raise CertificateMismatch("parity character is not multiplicative")
                character_checks += 1

        for code in ambient:
            column_sign_product = sign(code[0]) * sign(code[1]) * sign(code[2])
            matrix_character = determinant(decode_code(code)) * column_sign_product
            if matrix_character != parity_character(code):
                raise CertificateMismatch("matrix and tuple character formulas differ")

        excluded_odd_units = [code for code in ambient if parity_character(code) == -1]
        for odd_unit in excluded_odd_units:
            extension = generated_code_closure(
                automaton.generator_codes + (odd_unit,)
            )
            if len(extension) != 216:
                raise CertificateMismatch("odd-unit extension did not fill the ambient monoid")
            maximal_extension_checks += 1

    reduced_generators = (
        automaton.generator_codes[0],
        automaton.generator_codes[2],
        automaton.generator_codes[3],
    )
    reduced_closure = generated_code_closure(reduced_generators)
    if set(reduced_closure) != set(automaton.states):
        raise CertificateMismatch("the claimed three-generator presentation failed")

    return {
        "exact_oracle_status": exact.status,
        "exact_state_set_equality": True,
        "generator_transition_checks": transition_checks,
        "canonical_depth_equality": True,
        "full_pair_composition_checks": pair_checks,
        "parity_character_pair_checks": character_checks,
        "maximal_odd_unit_extension_checks": maximal_extension_checks,
        "three_generator_state_count": len(reduced_closure),
        "three_generator_max_minimal_depth": max(reduced_closure.values()),
        "Lq_is_redundant": True,
        "generator_rank": 3,
        "max_minimal_word_depth": max(map(len, automaton.canonical_words)),
    }


def build_automaton(
    deep_check: bool = False,
    enforce_baseline: bool = True,
) -> Tuple[CompiledAutomaton, Dict[str, object]]:
    generator_codes = tuple(encode_matrix(matrix) for matrix in GENERATOR_MATRICES)
    states = enumerate_closed_form_states()
    if len(states) != 192:
        raise CertificateMismatch("closed-form predicate did not produce 192 states")
    state_index = {state: index for index, state in enumerate(states)}
    transitions = build_transition_rows(states, state_index, generator_codes)

    model_fingerprint = model_digest()
    state_fingerprint = stable_digest([list(state) for state in states])
    table_fingerprint = stable_digest(
        {
            "model_fingerprint": model_fingerprint,
            "state_fingerprint": state_fingerprint,
            "symbols": list(SYMBOLS),
            "transitions": [list(row) for row in transitions],
        }
    )
    words = shortest_words(transitions, state_index[IDENTITY_CODE])
    automaton = CompiledAutomaton(
        states=states,
        transitions=transitions,
        state_index=state_index,
        generator_codes=generator_codes,
        canonical_words=words,
        model_fingerprint=model_fingerprint,
        state_fingerprint=state_fingerprint,
        table_fingerprint=table_fingerprint,
    )
    if enforce_baseline:
        assert_baseline_fingerprints(automaton)
    evidence = validate_against_exact_oracle(automaton, deep_check)
    return automaton, evidence


def multiply_certified_or_exact(left: Matrix, right: Matrix) -> Tuple[Matrix, str]:
    """Use the compact proof domain when possible, otherwise exact fallback."""

    try:
        left_code = encode_matrix(left)
        right_code = encode_matrix(right)
    except OutsideCertifiedDomain:
        return matrix_multiply(left, right), "exact_matrix_fallback"
    return decode_code(compose_codes(left_code, right_code)), "certified_signed_code"


def parse_word(raw: str) -> Tuple[str, ...]:
    aliases = {
        "lh": "Lh",
        "l_h": "Lh",
        "lq": "Lq",
        "l_q": "Lq",
        "rh": "Rh",
        "r_h": "Rh",
        "rq": "Rq",
        "r_q": "Rq",
    }
    pieces = raw.replace(",", " ").split()
    parsed: List[str] = []
    for piece in pieces:
        canonical = aliases.get(piece.lower())
        if canonical is None:
            raise ValueError(
                "unknown generator {!r}; use Lh, Lq, Rh, or Rq".format(piece)
            )
        parsed.append(canonical)
    return tuple(parsed)


def execute_word(
    automaton: CompiledAutomaton, word: Sequence[str], shadow: bool = True
) -> Dict[str, object]:
    symbol_index = {symbol: index for index, symbol in enumerate(SYMBOLS)}
    state_id = automaton.identity_state
    exact_matrix = I3
    trace: List[Dict[str, object]] = []
    for step, symbol in enumerate(word, start=1):
        index = symbol_index[symbol]
        state_id = automaton.transitions[state_id][index]
        if shadow:
            exact_matrix = matrix_multiply(exact_matrix, GENERATOR_MATRICES[index])
            if decode_code(automaton.states[state_id]) != exact_matrix:
                raise CertificateMismatch("runtime shadow parity failure")
        code = automaton.states[state_id]
        trace.append(
            {
                "step": step,
                "symbol": symbol,
                "state_id": state_id,
                "signed_code": list(code),
                "root_axis": code[0],
            }
        )

    code = automaton.states[state_id]
    matrix = decode_code(code)
    canonical = automaton.canonical_words[state_id]
    return {
        "input_word": list(word),
        "input_length": len(word),
        "state_id": state_id,
        "signed_code": list(code),
        "rank": code_rank(code),
        "root_axis": code[0],
        "matrix": matrix_rows(matrix),
        "canonical_shortest_word": list(canonical),
        "canonical_length": len(canonical),
        "shadow_exact_matrix_parity": shadow,
        "trace": trace,
    }


def corruption_rejection_checks(automaton: CompiledAutomaton) -> Dict[str, bool]:
    """Inject local copies of two faults and prove they are rejected."""

    rows = [list(row) for row in automaton.transitions]
    source = automaton.identity_state
    rows[source][0] = (rows[source][0] + 1) % len(automaton.states)
    corrupted_digest = stable_digest(
        {
            "model_fingerprint": automaton.model_fingerprint,
            "state_fingerprint": automaton.state_fingerprint,
            "symbols": list(SYMBOLS),
            "transitions": rows,
        }
    )
    fingerprint_rejected = corrupted_digest != EXPECTED_TABLE_DIGEST

    target = rows[source][0]
    exact_target = matrix_multiply(I3, L_H)
    transition_rejected = decode_code(automaton.states[target]) != exact_target
    if not fingerprint_rejected or not transition_rejected:
        raise CertificateMismatch("fault injection was not rejected")
    return {
        "corrupted_table_fingerprint_rejected": fingerprint_rejected,
        "corrupted_transition_exact_parity_rejected": transition_rejected,
    }


def structural_profile(states: Iterable[SignedCode]) -> Dict[str, object]:
    states_tuple = tuple(states)
    ranks = {rank: sum(code_rank(code) == rank for code in states_tuple) for rank in (1, 2, 3)}
    ambient = tuple(product(SIGNED_AXES, repeat=3))
    excluded = [code for code in ambient if not is_compiled_monoid_code(code)]
    return {
        "ambient_signed_transformation_count": len(ambient),
        "compiled_monoid_count": len(states_tuple),
        "rank_profile": ranks,
        "singular_ideal_count": ranks[1] + ranks[2],
        "even_permutation_unit_count": ranks[3],
        "excluded_odd_permutation_unit_count": len(excluded),
        "all_excluded_states_are_units": all(code_rank(code) == 3 for code in excluded),
        "closed_form": "parity_character inverse image of {0,+1}",
        "ambient_monoid": "C2 wreath T3",
        "unit_group": "C2^3 semidirect A3 = C2 x A4",
        "singular_set_is_two_sided_ideal": True,
    }


def build_report(word: Sequence[str], deep_check: bool) -> Dict[str, object]:
    automaton, evidence = build_automaton(deep_check=deep_check)
    corruption = corruption_rejection_checks(automaton) if deep_check else {}

    # Explicitly exercise both dispatch lanes.
    compact_product, compact_lane = multiply_certified_or_exact(L_H, R_Q)
    outside = tuple(2 * value for value in I3)  # type: ignore[assignment]
    fallback_product, fallback_lane = multiply_certified_or_exact(outside, L_H)
    assert compact_product == matrix_multiply(L_H, R_Q)
    assert fallback_product == matrix_multiply(outside, L_H)

    return {
        "status": "exact_matrix_oracle_certified_signed_table",
        "convention": "state * generator; append generator on the right",
        "symbols": list(SYMBOLS),
        "generator_codes": [list(code) for code in automaton.generator_codes],
        "fingerprints": {
            "model_sha256": automaton.model_fingerprint,
            "state_sha256": automaton.state_fingerprint,
            "transition_table_sha256": automaton.table_fingerprint,
            "baseline_match": not baseline_mismatches(
                automaton.model_fingerprint,
                automaton.state_fingerprint,
                automaton.table_fingerprint,
            ),
        },
        "structure": structural_profile(automaton.states),
        "certificate_evidence": evidence,
        "fault_injection": corruption,
        "dispatch_examples": {
            "inside_domain_lane": compact_lane,
            "outside_domain_lane": fallback_lane,
        },
        "execution": execute_word(automaton, word, shadow=True),
        "epistemic_scope": {
            "exact": (
                "The three-coordinate composition formula is algebraically equal to "
                "matrix multiplication on signed-basis actions."
            ),
            "computational_certificate": (
                "The closed-form 192-state set, all 768 generator transitions, and "
                "canonical BFS depths are compared with the source matrix oracle."
            ),
            "fallback": (
                "Matrices outside the signed-action domain bypass the compact lane "
                "and use exact integer matrix multiplication."
            ),
            "not_claimed": "No approximate, physical, or production-performance claim is made.",
        },
    }


def print_human(report: Mapping[str, object]) -> None:
    structure = report["structure"]
    evidence = report["certificate_evidence"]
    fingerprints = report["fingerprints"]
    execution = report["execution"]
    assert isinstance(structure, dict)
    assert isinstance(evidence, dict)
    assert isinstance(fingerprints, dict)
    assert isinstance(execution, dict)
    print("Certified signed metaspace VM")
    print("status:", report["status"])
    print(
        "ambient/monoid/singular/unit/excluded = {}/{}/{}/{}/{}".format(
            structure["ambient_signed_transformation_count"],
            structure["compiled_monoid_count"],
            structure["singular_ideal_count"],
            structure["even_permutation_unit_count"],
            structure["excluded_odd_permutation_unit_count"],
        )
    )
    print("rank profile:", structure["rank_profile"])
    print("generator transitions checked:", evidence["generator_transition_checks"])
    print("full pair checks:", evidence["full_pair_composition_checks"])
    print(
        "three-generator presentation / rank:",
        evidence["three_generator_state_count"],
        "/",
        evidence["generator_rank"],
    )
    print("baseline fingerprints match:", fingerprints["baseline_match"])
    print("word:", " ".join(execution["input_word"]))
    print(
        "state/code/root/rank = {}/{}/{}/{}".format(
            execution["state_id"],
            execution["signed_code"],
            execution["root_axis"],
            execution["rank"],
        )
    )
    print("shortest representative:", " ".join(execution["canonical_shortest_word"]) or "identity")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--word",
        default="Lh Lq Rh Rq Lh",
        help="comma- or space-separated generators from Lh,Lq,Rh,Rq",
    )
    parser.add_argument(
        "--deep-check",
        action="store_true",
        help="also compare all 36,864 compact pair products and inject faults",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()
    try:
        word = parse_word(args.word)
        report = build_report(word, args.deep_check)
    except (ValueError, CertificateMismatch) as error:
        raise SystemExit(str(error))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)


if __name__ == "__main__":
    main()
