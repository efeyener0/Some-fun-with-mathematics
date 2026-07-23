"""Exact shortlex normalizer and finite complete rewriting system.

The authoritative semantics are the literal 3x3 integer matrices from
``chiral_operator_monoids.py``.  The compact signed-code oracle from
``certified_signed_metaspace.py`` derives a three-generator automaton over

    Lh < Rh < Lq.

Every input word is evaluated by a 192-state deterministic transition table
and emitted as the shortlex-least word for its exact monoid element.  A finite
context rewriting system is derived independently from the same canonical
representatives.  Its termination and confluence claims are justified by a
shortlex proof and can additionally be checked by exhaustive critical-pair
joining with ``--deep-check``.

``Rq`` is accepted at the CLI boundary only as an exact macro.  It is not a
fourth presentation generator.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, deque
from dataclasses import dataclass
from itertools import product
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from certified_signed_metaspace import (
    CertificateMismatch,
    CompiledAutomaton,
    IDENTITY_CODE,
    SignedCode,
    build_automaton,
    compose_codes,
    decode_code,
    encode_matrix,
    enumerate_closed_form_states,
    stable_digest,
)
from chiral_operator_monoids import (
    HARD_DEPTH_CAP,
    HARD_STATE_CAP,
    I3,
    L_H,
    L_Q,
    R_H,
    R_Q,
    Matrix,
    enumerate_monoid,
    matrix_multiply,
    matrix_rows,
)


Word = Tuple[str, ...]
TransitionRow = Tuple[int, int, int]

SCHEMA_VERSION = 1
ALPHABET: Tuple[str, ...] = ("Lh", "Rh", "Lq")
GENERATOR_MATRICES: Tuple[Matrix, ...] = (L_H, R_H, L_Q)
SYMBOL_INDEX = {symbol: index for index, symbol in enumerate(ALPHABET)}
# Contextual rewriting is a diagnostic shadow of the authoritative O(n)
# transition-table lane.  Large inputs still normalize exactly; they simply
# skip this deliberately more expensive parity lane.
RUNTIME_CONTEXTUAL_SHADOW_MAX_INPUT = 4_096

# Filled from this exact compiler and checked by default.  The source oracle
# has its own independent model/state/table fingerprints as well.
EXPECTED_MODEL_DIGEST = "d86c1c741cb0d28002545c20d6a9fc4f0cc177aab2d3f8cabcd77d1aeda6a613"
EXPECTED_TRANSITION_DIGEST = "0dd3b3bd279edacc36e34d0574e6504fd7535beadcd68cb2f6bd062cdda318ad"
EXPECTED_CANONICAL_DIGEST = "92485d18b58f39deb7e9acecb41313940b2ffa86b20fa49b5c6ec40907fd1691"
EXPECTED_REWRITE_DIGEST = "23f954b9117dee22a863bb6f995bbdcb64fc6a3719fa999d255fc0f79ca24101"
EXPECTED_BUNDLE_DIGEST = "bfb3087acbc013daa613434e5fe05a4171a5a16893236ad28b91890df3c27701"
EXPECTED_CRITICAL_PEAK_COUNT = 56_725
EXPECTED_CRITICAL_PEAK_DIGEST = "5e525e1e74ded91a1e082b916a86d5c98783c5e4fb4b426e0c472bb259e6af13"
EXPECTED_CONTEXT_WORD_CHECKS = 88_573


@dataclass(frozen=True)
class RewriteRule:
    rule_id: int
    lhs: Word
    rhs: Word
    source_state: int
    appended_symbol: str
    target_state: int


@dataclass(frozen=True)
class WordNormalizer:
    states: Tuple[SignedCode, ...]
    state_index: Mapping[SignedCode, int]
    generator_codes: Tuple[SignedCode, ...]
    transitions: Tuple[TransitionRow, ...]
    canonical_words: Tuple[Word, ...]
    rules: Tuple[RewriteRule, ...]
    identity_state: int
    rq_macro: Word
    model_fingerprint: str
    transition_fingerprint: str
    canonical_fingerprint: str
    rewrite_fingerprint: str
    bundle_fingerprint: str


def encoded_word(word: Sequence[str]) -> Tuple[int, ...]:
    return tuple(SYMBOL_INDEX[symbol] for symbol in word)


def word_key(word: Sequence[str]) -> Tuple[int, Tuple[int, ...]]:
    """The declared shortlex order, independent of Python string ordering."""

    return len(word), encoded_word(word)


def word_less(left: Sequence[str], right: Sequence[str]) -> bool:
    return word_key(left) < word_key(right)


def evaluate_code(word: Sequence[str], generator_codes: Sequence[SignedCode]) -> SignedCode:
    state = IDENTITY_CODE
    for symbol in word:
        state = compose_codes(state, generator_codes[SYMBOL_INDEX[symbol]])
    return state


def evaluate_matrix(word: Sequence[str]) -> Matrix:
    state = I3
    for symbol in word:
        state = matrix_multiply(state, GENERATOR_MATRICES[SYMBOL_INDEX[symbol]])
    return state


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


def shortlex_bfs_words(
    transitions: Sequence[TransitionRow], identity_state: int
) -> Tuple[Word, ...]:
    """First discovery under ordered BFS is the shortlex-least representative."""

    words: List[Optional[Word]] = [None] * len(transitions)
    words[identity_state] = ()
    queue = deque([identity_state])
    while queue:
        source = queue.popleft()
        prefix = words[source]
        assert prefix is not None
        for symbol_index, target in enumerate(transitions[source]):
            if words[target] is None:
                words[target] = prefix + (ALPHABET[symbol_index],)
                queue.append(target)
    if any(word is None for word in words):
        raise CertificateMismatch("three-generator transition graph is not reachable")
    return tuple(word for word in words if word is not None)


def build_rewrite_rules(
    transitions: Sequence[TransitionRow], canonical_words: Sequence[Word]
) -> Tuple[RewriteRule, ...]:
    raw: List[Tuple[Word, Word, int, str, int]] = []
    for source, canonical in enumerate(canonical_words):
        for symbol_index, target in enumerate(transitions[source]):
            symbol = ALPHABET[symbol_index]
            lhs = canonical + (symbol,)
            rhs = canonical_words[target]
            if lhs != rhs:
                raw.append((lhs, rhs, source, symbol, target))
    raw.sort(key=lambda item: (word_key(item[0]), word_key(item[1]), item[2], item[4]))
    return tuple(
        RewriteRule(rule_id, lhs, rhs, source, symbol, target)
        for rule_id, (lhs, rhs, source, symbol, target) in enumerate(raw)
    )


def model_fingerprint(source: CompiledAutomaton, generator_codes: Sequence[SignedCode]) -> str:
    return stable_digest(
        {
            "schema_version": SCHEMA_VERSION,
            "source_model_fingerprint": source.model_fingerprint,
            "source_state_fingerprint": source.state_fingerprint,
            "alphabet_shortlex_order": list(ALPHABET),
            "generator_codes": [list(code) for code in generator_codes],
            "word_action": "append on right",
        }
    )


def transition_fingerprint(model_digest: str, transitions: Sequence[TransitionRow]) -> str:
    return stable_digest(
        {
            "model_fingerprint": model_digest,
            "transitions": [list(row) for row in transitions],
        }
    )


def canonical_fingerprint(
    transition_digest: str, canonical_words: Sequence[Word]
) -> str:
    return stable_digest(
        {
            "transition_fingerprint": transition_digest,
            "canonical_words": [list(word) for word in canonical_words],
        }
    )


def rewrite_fingerprint(
    canonical_digest: str, rules: Sequence[RewriteRule]
) -> str:
    return stable_digest(
        {
            "canonical_fingerprint": canonical_digest,
            "rules": [
                {
                    "lhs": list(rule.lhs),
                    "rhs": list(rule.rhs),
                    "source_state": rule.source_state,
                    "symbol": rule.appended_symbol,
                    "target_state": rule.target_state,
                }
                for rule in rules
            ],
        }
    )


def bundle_fingerprint(
    model_digest: str,
    transition_digest: str,
    canonical_digest: str,
    rewrite_digest: str,
) -> str:
    return stable_digest(
        {
            "model": model_digest,
            "transition": transition_digest,
            "canonical": canonical_digest,
            "rewrite": rewrite_digest,
        }
    )


def baseline_mismatches(normalizer: WordNormalizer) -> List[str]:
    expected = (
        ("model", EXPECTED_MODEL_DIGEST, normalizer.model_fingerprint),
        ("transition", EXPECTED_TRANSITION_DIGEST, normalizer.transition_fingerprint),
        ("canonical", EXPECTED_CANONICAL_DIGEST, normalizer.canonical_fingerprint),
        ("rewrite", EXPECTED_REWRITE_DIGEST, normalizer.rewrite_fingerprint),
        ("bundle", EXPECTED_BUNDLE_DIGEST, normalizer.bundle_fingerprint),
    )
    return [name for name, wanted, actual in expected if wanted != actual]


def assert_baseline(normalizer: WordNormalizer) -> None:
    mismatches = baseline_mismatches(normalizer)
    if mismatches:
        raise CertificateMismatch(
            "stale or changed word-normalizer fingerprint(s): " + ", ".join(mismatches)
        )


def rules_by_first_symbol(
    rules: Sequence[RewriteRule],
) -> Mapping[str, Tuple[RewriteRule, ...]]:
    buckets: Dict[str, List[RewriteRule]] = {symbol: [] for symbol in ALPHABET}
    for rule in rules:
        buckets[rule.lhs[0]].append(rule)
    # Longest-first gives a deterministic contextual strategy.  Confluence
    # means the selected strategy cannot change the resulting normal form.
    return {
        symbol: tuple(
            sorted(
                bucket,
                key=lambda rule: (-len(rule.lhs), encoded_word(rule.lhs), rule.rule_id),
            )
        )
        for symbol, bucket in buckets.items()
    }


def first_redex(
    word: Word, buckets: Mapping[str, Tuple[RewriteRule, ...]]
) -> Optional[Tuple[int, RewriteRule]]:
    for position, symbol in enumerate(word):
        for rule in buckets[symbol]:
            if word[position : position + len(rule.lhs)] == rule.lhs:
                return position, rule
    return None


def contextual_normal_form(
    word: Sequence[str],
    rules: Sequence[RewriteRule],
    step_cap: Optional[int] = None,
    buckets: Optional[Mapping[str, Tuple[RewriteRule, ...]]] = None,
) -> Tuple[Word, int]:
    """Normalize by contextual rewriting, independently of the state table."""

    current = tuple(word)
    if buckets is None:
        buckets = rules_by_first_symbol(rules)
    steps = 0
    while True:
        redex = first_redex(current, buckets)
        if redex is None:
            return current, steps
        position, rule = redex
        current = (
            current[:position]
            + rule.rhs
            + current[position + len(rule.lhs) :]
        )
        steps += 1
        if step_cap is not None and steps > step_cap:
            raise CertificateMismatch("context rewrite exceeded its termination guard")


def table_state(normalizer: WordNormalizer, word: Sequence[str]) -> int:
    state = normalizer.identity_state
    for symbol in word:
        state = normalizer.transitions[state][SYMBOL_INDEX[symbol]]
    return state


def normalize_word(
    normalizer: WordNormalizer, word: Sequence[str], shadow: bool = True
) -> Dict[str, object]:
    state = normalizer.identity_state
    exact_matrix = I3
    trace: List[Dict[str, object]] = []
    for step, symbol in enumerate(word, start=1):
        symbol_index = SYMBOL_INDEX[symbol]
        state = normalizer.transitions[state][symbol_index]
        if shadow:
            exact_matrix = matrix_multiply(exact_matrix, GENERATOR_MATRICES[symbol_index])
            if decode_code(normalizer.states[state]) != exact_matrix:
                raise CertificateMismatch("runtime table/matrix shadow parity failure")
        trace.append(
            {
                "step": step,
                "symbol": symbol,
                "state_id": state,
                "signed_code": list(normalizer.states[state]),
            }
        )
    canonical = normalizer.canonical_words[state]
    context_checked = len(word) <= RUNTIME_CONTEXTUAL_SHADOW_MAX_INPUT
    rewrite_steps: Optional[int]
    if context_checked:
        rewritten, rewrite_steps = contextual_normal_form(word, normalizer.rules)
        if rewritten != canonical:
            raise CertificateMismatch("context rewriter and finite-state normalizer disagree")
    else:
        rewrite_steps = None
    return {
        "expanded_input_word": list(word),
        "expanded_input_length": len(word),
        "state_id": state,
        "signed_code": list(normalizer.states[state]),
        "matrix": matrix_rows(decode_code(normalizer.states[state])),
        "canonical_shortlex_word": list(canonical),
        "canonical_length": len(canonical),
        "context_rewrite_checked": context_checked,
        "context_rewrite_steps": rewrite_steps,
        "context_rewrite_input_limit": RUNTIME_CONTEXTUAL_SHADOW_MAX_INPUT,
        "table_matrix_shadow_parity": shadow,
        "trace": trace,
    }


def parse_source_word(raw: str) -> Word:
    aliases = {
        "lh": "Lh",
        "l_h": "Lh",
        "rh": "Rh",
        "r_h": "Rh",
        "lq": "Lq",
        "l_q": "Lq",
        "rq": "Rq",
        "r_q": "Rq",
    }
    parsed: List[str] = []
    for piece in raw.replace(",", " ").split():
        symbol = aliases.get(piece.lower())
        if symbol is None:
            raise ValueError("unknown symbol {!r}; use Lh, Rh, Lq, or macro Rq".format(piece))
        parsed.append(symbol)
    return tuple(parsed)


def expand_rq_macro(source_word: Sequence[str], rq_macro: Word) -> Word:
    expanded: List[str] = []
    for symbol in source_word:
        if symbol == "Rq":
            expanded.extend(rq_macro)
        else:
            expanded.append(symbol)
    return tuple(expanded)


def generic_shortlex_closure(
    symbols: Sequence[str], generator_codes: Sequence[SignedCode]
) -> Mapping[SignedCode, Word]:
    words: Dict[SignedCode, Word] = {IDENTITY_CODE: ()}
    queue = deque([IDENTITY_CODE])
    while queue:
        source = queue.popleft()
        for symbol, generator in zip(symbols, generator_codes):
            target = compose_codes(source, generator)
            if target not in words:
                words[target] = words[source] + (symbol,)
                queue.append(target)
    return words


def shortlex_enumeration_oracle(
    normalizer: WordNormalizer,
) -> Tuple[Mapping[int, Word], int]:
    """Independently enumerate every word through the discovered diameter."""

    diameter = max(map(len, normalizer.canonical_words))
    first: Dict[int, Word] = {}
    checks = 0
    for length in range(diameter + 1):
        for word in product(ALPHABET, repeat=length):
            state = table_state(normalizer, word)
            first.setdefault(state, tuple(word))
            checks += 1
    return first, checks


def exact_relation_checks(normalizer: WordNormalizer) -> Dict[str, object]:
    lh, rh, lq = normalizer.generator_codes
    rq = encode_matrix(R_Q)

    def compose_word(codes: Sequence[SignedCode]) -> SignedCode:
        value = IDENTITY_CODE
        for code in codes:
            value = compose_codes(value, code)
        return value

    involution = compose_word((lh, rh, lh))
    identity = IDENTITY_CODE
    facts = {
        "S_code": list(involution),
        "S_word": ["Lh", "Rh", "Lh"],
        "S_squared_is_identity": compose_codes(involution, involution) == identity,
        "Rq_equals_Lq_times_S": compose_codes(lq, involution) == rq,
        "Lq_equals_Rq_times_S": compose_codes(rq, involution) == lq,
        "S_Rq_S_equals_Lq": compose_word((involution, rq, involution)) == lq,
        "S_Lq_equals_Lq": compose_codes(involution, lq) == lq,
        "Rq_canonical_macro": list(normalizer.rq_macro),
        "Rq_macro_is_exact": evaluate_code(normalizer.rq_macro, normalizer.generator_codes) == rq,
    }
    required_checks = (
        "S_squared_is_identity",
        "Rq_equals_Lq_times_S",
        "Lq_equals_Rq_times_S",
        "S_Rq_S_equals_Lq",
        "S_Lq_equals_Lq",
        "Rq_macro_is_exact",
    )
    if not all(facts[key] is True for key in required_checks):
        raise CertificateMismatch("Lq/Rq symmetry relation failed")

    alternate_symbols = ("Lh", "Rh", "Rq")
    alternate_codes = (lh, rh, rq)
    alternate = generic_shortlex_closure(alternate_symbols, alternate_codes)
    if set(alternate) != set(normalizer.states):
        raise CertificateMismatch("the Lh/Rh/Rq alternate alphabet did not generate M")
    canonical_lq = alternate[lq]
    return {
        **facts,
        "Lq_alphabet_closure_count": len(normalizer.states),
        "Rq_alphabet_closure_count": len(alternate),
        "Lq_alphabet_depth_profile": dict(
            sorted(Counter(map(len, normalizer.canonical_words)).items())
        ),
        "Rq_alphabet_depth_profile": dict(
            sorted(Counter(map(len, alternate.values())).items())
        ),
        "Lq_alphabet_diameter": max(map(len, normalizer.canonical_words)),
        "Rq_alphabet_diameter": max(map(len, alternate.values())),
        "Lq_canonical_macro_over_Rq_alphabet": list(canonical_lq),
        "algebraic_substitutability_is_not_shortlex_isometry": (
            Counter(map(len, normalizer.canonical_words))
            != Counter(map(len, alternate.values()))
        ),
    }


def validate_default(normalizer: WordNormalizer) -> Dict[str, object]:
    exact = enumerate_monoid(
        "word_normalizer_triple",
        GENERATOR_MATRICES,
        HARD_STATE_CAP,
        HARD_DEPTH_CAP,
    )
    if not exact.closed:
        raise CertificateMismatch("authoritative three-generator matrix monoid did not close")
    decoded = {decode_code(code) for code in normalizer.states}
    if decoded != exact.states:
        raise CertificateMismatch("three-generator signed states differ from matrix oracle")

    transition_checks = 0
    for state_id, code in enumerate(normalizer.states):
        matrix = decode_code(code)
        for symbol_index, generator in enumerate(GENERATOR_MATRICES):
            target = normalizer.transitions[state_id][symbol_index]
            if decode_code(normalizer.states[target]) != matrix_multiply(matrix, generator):
                raise CertificateMismatch("normalizer transition differs from matrix oracle")
            transition_checks += 1

    exact_depths = {encode_matrix(matrix): depth for matrix, depth in exact.depths.items()}
    compiled_depths = {
        code: len(normalizer.canonical_words[state_id])
        for state_id, code in enumerate(normalizer.states)
    }
    if exact_depths != compiled_depths:
        raise CertificateMismatch("canonical lengths differ from exact matrix BFS")

    first_words, word_checks = shortlex_enumeration_oracle(normalizer)
    if len(first_words) != len(normalizer.states):
        raise CertificateMismatch("shortlex enumeration did not reach every state")
    if any(
        first_words[state] != normalizer.canonical_words[state]
        for state in range(len(normalizer.states))
    ):
        raise CertificateMismatch("ordered enumeration differs from canonical shortlex words")

    rule_soundness_checks = 0
    for rule in normalizer.rules:
        if not word_less(rule.rhs, rule.lhs):
            raise CertificateMismatch("rewrite rule does not strictly decrease shortlex")
        if evaluate_matrix(rule.lhs) != evaluate_matrix(rule.rhs):
            raise CertificateMismatch("rewrite rule is not sound in the matrix oracle")
        rule_soundness_checks += 1

    buckets = rules_by_first_symbol(normalizer.rules)
    canonical_set = set(normalizer.canonical_words)
    for state_id, canonical in enumerate(normalizer.canonical_words):
        if first_redex(canonical, buckets) is not None:
            raise CertificateMismatch("a canonical representative is context-reducible")
        for prefix_length in range(len(canonical) + 1):
            if canonical[:prefix_length] not in canonical_set:
                raise CertificateMismatch("canonical language is not prefix-closed")
        if table_state(normalizer, canonical) != state_id:
            raise CertificateMismatch("canonical representative evaluates to wrong state")

    rule_pairs = {(rule.lhs, rule.rhs) for rule in normalizer.rules}
    boundary_checks = 0
    tree_edges = 0
    for state, canonical in enumerate(normalizer.canonical_words):
        for symbol_index, target in enumerate(normalizer.transitions[state]):
            lhs = canonical + (ALPHABET[symbol_index],)
            rhs = normalizer.canonical_words[target]
            if lhs == rhs:
                tree_edges += 1
            elif (lhs, rhs) not in rule_pairs:
                raise CertificateMismatch("canonical boundary transition lacks rewrite rule")
            boundary_checks += 1
    if tree_edges != len(normalizer.states) - 1:
        raise CertificateMismatch("canonical BFS tree does not have 191 edges")

    # Regression for the former fixed 100,000-step runtime guard.  The exact
    # table lane must accept long finite inputs without forcing the contextual
    # diagnostic lane to materialize a long rewrite sequence.
    long_word = ("Lh",) * (RUNTIME_CONTEXTUAL_SHADOW_MAX_INPUT + 2)
    long_execution = normalize_word(normalizer, long_word, shadow=True)
    if long_execution["context_rewrite_checked"]:
        raise CertificateMismatch("long input unexpectedly entered contextual shadow")
    if long_execution["canonical_shortlex_word"] != []:
        raise CertificateMismatch("long Lh^3k regression normalized incorrectly")

    relations = exact_relation_checks(normalizer)
    return {
        "exact_matrix_status": exact.status,
        "exact_state_set_equality": True,
        "generator_transition_checks": transition_checks,
        "canonical_depth_equality": True,
        "shortlex_words_enumerated_through_diameter": word_checks,
        "shortlex_first_word_equality": True,
        "rule_soundness_and_orientation_checks": rule_soundness_checks,
        "canonical_irreducibility_checks": len(normalizer.canonical_words),
        "canonical_prefix_closure": True,
        "canonical_boundary_checks": boundary_checks,
        "canonical_tree_edges": tree_edges,
        "nontrivial_boundary_rules": len(normalizer.rules),
        "long_input_table_lane_regression": {
            "input_length": len(long_word),
            "canonical": [],
            "contextual_shadow_skipped": True,
        },
        "rq_symmetry": relations,
    }


def critical_peaks(rules: Sequence[RewriteRule]) -> Tuple[Tuple[Word, Word, Word], ...]:
    """Enumerate every distinct nontrivial overlap/inclusion critical peak."""

    peaks: Dict[
        Tuple[Tuple[int, ...], Tuple[int, ...], Tuple[int, ...]],
        Tuple[Word, Word, Word],
    ] = {}
    for first in rules:
        for second in rules:
            left = first.lhs
            right = second.lhs
            for relative in range(-len(right) + 1, len(left)):
                start = min(0, relative)
                end = max(len(left), relative + len(right))
                first_offset = -start
                second_offset = relative - start
                if (first_offset, first.rule_id) >= (second_offset, second.rule_id):
                    continue
                overlap_start = max(0, relative)
                overlap_end = min(len(left), relative + len(right))
                if any(
                    left[index] != right[index - relative]
                    for index in range(overlap_start, overlap_end)
                ):
                    continue
                merged: List[Optional[str]] = [None] * (end - start)
                for index, symbol in enumerate(left):
                    merged[first_offset + index] = symbol
                compatible = True
                for index, symbol in enumerate(right):
                    slot = second_offset + index
                    if merged[slot] is not None and merged[slot] != symbol:
                        compatible = False
                        break
                    merged[slot] = symbol
                if not compatible or any(symbol is None for symbol in merged):
                    continue
                superword = tuple(symbol for symbol in merged if symbol is not None)
                first_branch = (
                    superword[:first_offset]
                    + first.rhs
                    + superword[first_offset + len(left) :]
                )
                second_branch = (
                    superword[:second_offset]
                    + second.rhs
                    + superword[second_offset + len(right) :]
                )
                if first_branch == second_branch:
                    continue
                branch_a, branch_b = sorted(
                    (first_branch, second_branch), key=word_key
                )
                key = (
                    encoded_word(superword),
                    encoded_word(branch_a),
                    encoded_word(branch_b),
                )
                peaks[key] = (superword, branch_a, branch_b)
    return tuple(
        peaks[key]
        for key in sorted(
            peaks,
            key=lambda item: (
                (len(item[0]), item[0]),
                (len(item[1]), item[1]),
                (len(item[2]), item[2]),
            ),
        )
    )


def corruption_rejection(normalizer: WordNormalizer) -> Dict[str, bool]:
    rows = [list(row) for row in normalizer.transitions]
    rows[normalizer.identity_state][0] = (
        rows[normalizer.identity_state][0] + 1
    ) % len(normalizer.states)
    corrupted_transition = transition_fingerprint(
        normalizer.model_fingerprint,
        tuple(tuple(row) for row in rows),  # type: ignore[arg-type]
    )
    transition_fingerprint_rejected = (
        corrupted_transition != normalizer.transition_fingerprint
    )
    corrupted_target = rows[normalizer.identity_state][0]
    transition_exact_parity_rejected = (
        decode_code(normalizer.states[corrupted_target]) != L_H
    )

    first = normalizer.rules[0]
    corrupt_rhs: Word = ("Lh",) if first.rhs != ("Lh",) else ("Rh",)
    corrupted_rules = list(normalizer.rules)
    corrupted_rules[0] = RewriteRule(
        first.rule_id,
        first.lhs,
        corrupt_rhs,
        first.source_state,
        first.appended_symbol,
        first.target_state,
    )
    corrupted_rule_digest = rewrite_fingerprint(
        normalizer.canonical_fingerprint, corrupted_rules
    )
    rule_fingerprint_rejected = corrupted_rule_digest != normalizer.rewrite_fingerprint
    rule_exact_parity_rejected = evaluate_matrix(first.lhs) != evaluate_matrix(corrupt_rhs)
    if not all(
        (
            transition_fingerprint_rejected,
            transition_exact_parity_rejected,
            rule_fingerprint_rejected,
            rule_exact_parity_rejected,
        )
    ):
        raise CertificateMismatch("normalizer fault injection was not rejected")
    return {
        "corrupted_transition_fingerprint_rejected": transition_fingerprint_rejected,
        "corrupted_transition_exact_parity_rejected": transition_exact_parity_rejected,
        "corrupted_rule_fingerprint_rejected": rule_fingerprint_rejected,
        "corrupted_rule_exact_parity_rejected": rule_exact_parity_rejected,
    }


def validate_deep(normalizer: WordNormalizer) -> Dict[str, object]:
    buckets = rules_by_first_symbol(normalizer.rules)
    maximum_lhs_length = max(len(rule.lhs) for rule in normalizer.rules)
    context_word_checks = 0
    maximum_word_steps = 0
    for length in range(maximum_lhs_length + 1):
        for word in product(ALPHABET, repeat=length):
            normal, steps = contextual_normal_form(
                word, normalizer.rules, buckets=buckets
            )
            expected = normalizer.canonical_words[table_state(normalizer, word)]
            if normal != expected:
                raise CertificateMismatch(
                    "context rewriter differs from table normalizer"
                )
            maximum_word_steps = max(maximum_word_steps, steps)
            context_word_checks += 1
    if context_word_checks != EXPECTED_CONTEXT_WORD_CHECKS:
        raise CertificateMismatch("context-word exhaustive corpus size changed")

    peaks = critical_peaks(normalizer.rules)
    maximum_steps = 0
    for superword, first_branch, second_branch in peaks:
        first_normal, first_steps = contextual_normal_form(
            first_branch, normalizer.rules, buckets=buckets
        )
        second_normal, second_steps = contextual_normal_form(
            second_branch, normalizer.rules, buckets=buckets
        )
        maximum_steps = max(maximum_steps, first_steps, second_steps)
        if first_normal != second_normal:
            raise CertificateMismatch("non-joinable critical rewrite peak")
        expected = normalizer.canonical_words[table_state(normalizer, superword)]
        if first_normal != expected:
            raise CertificateMismatch("critical peak joined outside canonical oracle")
    peak_digest = stable_digest(
        [
            {
                "superword": list(superword),
                "first_branch": list(first_branch),
                "second_branch": list(second_branch),
            }
            for superword, first_branch, second_branch in peaks
        ]
    )
    if len(peaks) != EXPECTED_CRITICAL_PEAK_COUNT:
        raise CertificateMismatch("critical-peak baseline count changed")
    if peak_digest != EXPECTED_CRITICAL_PEAK_DIGEST:
        raise CertificateMismatch("critical-peak baseline fingerprint changed")
    return {
        "context_words_checked_through_maximum_lhs_length": context_word_checks,
        "maximum_context_steps_in_word_corpus": maximum_word_steps,
        "critical_peak_count": len(peaks),
        "critical_peak_sha256": peak_digest,
        "all_critical_peaks_join": True,
        "maximum_context_steps_to_join_branch": maximum_steps,
        "fault_injection": corruption_rejection(normalizer),
    }


def build_normalizer(
    deep_check: bool = False,
    enforce_baseline: bool = True,
) -> Tuple[WordNormalizer, Dict[str, object], Dict[str, object]]:
    source, source_evidence = build_automaton(deep_check=deep_check)
    states = enumerate_closed_form_states()
    if states != source.states:
        raise CertificateMismatch("source signed oracle state ordering changed")
    state_index = {state: index for index, state in enumerate(states)}
    generator_codes = tuple(encode_matrix(matrix) for matrix in GENERATOR_MATRICES)
    transitions = build_transition_rows(states, state_index, generator_codes)
    canonical_words = shortlex_bfs_words(
        transitions, state_index[IDENTITY_CODE]
    )
    rules = build_rewrite_rules(transitions, canonical_words)

    model_digest = model_fingerprint(source, generator_codes)
    transition_digest = transition_fingerprint(model_digest, transitions)
    canonical_digest = canonical_fingerprint(transition_digest, canonical_words)
    rewrite_digest = rewrite_fingerprint(canonical_digest, rules)
    bundle_digest = bundle_fingerprint(
        model_digest, transition_digest, canonical_digest, rewrite_digest
    )
    rq_code = encode_matrix(R_Q)
    rq_macro = canonical_words[state_index[rq_code]]
    normalizer = WordNormalizer(
        states=states,
        state_index=state_index,
        generator_codes=generator_codes,
        transitions=transitions,
        canonical_words=canonical_words,
        rules=rules,
        identity_state=state_index[IDENTITY_CODE],
        rq_macro=rq_macro,
        model_fingerprint=model_digest,
        transition_fingerprint=transition_digest,
        canonical_fingerprint=canonical_digest,
        rewrite_fingerprint=rewrite_digest,
        bundle_fingerprint=bundle_digest,
    )
    if enforce_baseline:
        assert_baseline(normalizer)
    default_evidence = validate_default(normalizer)
    default_evidence["source_signed_oracle"] = source_evidence
    deep_evidence = validate_deep(normalizer) if deep_check else {
        "performed": False,
        "note": "use --deep-check to join every finite critical overlap and inject faults",
    }
    return normalizer, default_evidence, deep_evidence


def rule_record(rule: RewriteRule) -> Dict[str, object]:
    return {
        "rule_id": rule.rule_id,
        "lhs": list(rule.lhs),
        "rhs": list(rule.rhs),
        "source_state": rule.source_state,
        "appended_symbol": rule.appended_symbol,
        "target_state": rule.target_state,
    }


def build_report(source_word: Sequence[str], deep_check: bool) -> Dict[str, object]:
    normalizer, default_evidence, deep_evidence = build_normalizer(
        deep_check=deep_check
    )
    expanded = expand_rq_macro(source_word, normalizer.rq_macro)
    execution = normalize_word(normalizer, expanded, shadow=True)
    execution["source_word"] = list(source_word)
    execution["source_length"] = len(source_word)
    execution["Rq_macro_expansions"] = sum(symbol == "Rq" for symbol in source_word)

    depth_profile = dict(
        sorted(Counter(map(len, normalizer.canonical_words)).items())
    )
    lhs_profile = dict(sorted(Counter(len(rule.lhs) for rule in normalizer.rules).items()))
    rhs_profile = dict(sorted(Counter(len(rule.rhs) for rule in normalizer.rules).items()))
    core_rules = [
        rule_record(rule)
        for rule in normalizer.rules
        if len(rule.lhs) == min(len(candidate.lhs) for candidate in normalizer.rules)
    ]
    return {
        "status": "exact_finite_complete_shortlex_rewriting_system",
        "alphabet": list(ALPHABET),
        "shortlex_order": "Lh < Rh < Lq; length first, then declared symbol order",
        "action_convention": "append symbol on right; state * generator",
        "fingerprints": {
            "model_sha256": normalizer.model_fingerprint,
            "transition_sha256": normalizer.transition_fingerprint,
            "canonical_language_sha256": normalizer.canonical_fingerprint,
            "rewrite_system_sha256": normalizer.rewrite_fingerprint,
            "bundle_sha256": normalizer.bundle_fingerprint,
            "baseline_match": not baseline_mismatches(normalizer),
        },
        "canonical_language": {
            "state_count": len(normalizer.states),
            "diameter": max(map(len, normalizer.canonical_words)),
            "depth_profile": depth_profile,
            "maximum_output_length": max(map(len, normalizer.canonical_words)),
            "prefix_closed": True,
            "normalizer_kind": (
                "192-state deterministic subsequential transducer with final canonical-word output"
            ),
        },
        "rewrite_system": {
            "classification": "finite complete string rewriting system",
            "finite_presentation": "M = <Lh,Rh,Lq | lhs = rhs for the 385 listed rules>",
            "rule_count": len(normalizer.rules),
            "canonical_tree_transition_count": len(normalizer.states) - 1,
            "all_transition_equations": len(normalizer.states) * len(ALPHABET),
            "lhs_length_profile": lhs_profile,
            "rhs_length_profile": rhs_profile,
            "maximum_lhs_length": max(len(rule.lhs) for rule in normalizer.rules),
            "maximum_rhs_length": max(len(rule.rhs) for rule in normalizer.rules),
            "shortest_core_rules": core_rules,
            "rules": [rule_record(rule) for rule in normalizer.rules],
            "proof": {
                "sound": "every rule has equal exact 3x3 matrix semantics",
                "terminating": (
                    "every rule strictly decreases the context-compatible shortlex order"
                ),
                "irreducibles": (
                    "exactly the 192 canonical shortlex representatives; a noncanonical word has a shortest noncanonical prefix c_s*a and therefore a rule"
                ),
                "confluent": (
                    "termination plus one irreducible per exact semantic class gives a unique normal form"
                ),
                "presentation": (
                    "sound rules and one normal form for each of the 192 oracle states identify the quotient with the literal monoid"
                ),
            },
        },
        "default_evidence": default_evidence,
        "deep_evidence": deep_evidence,
        "execution": execution,
        "epistemic_scope": {
            "algebraic": (
                "The signed-code product equals matrix composition; the shortlex-decrease and unique-irreducible argument proves termination and confluence."
            ),
            "finite_certificate": (
                "All 192 states, 576 generator transitions, 385 rule equations, exact BFS depths, and every word through diameter nine are compared with the matrix oracle."
            ),
            "deep_certificate": (
                "--deep-check additionally normalizes every word through maximum rule-left-side length, joins every nontrivial finite rule overlap, and injects table/rule corruption."
            ),
            "boundary": (
                "This presentation is only for the literal Lh/Rh/Lq-generated 192-state monoid. Rq is an exact boundary macro; unknown symbols are rejected."
            ),
            "not_claimed": (
                "No smaller relation basis, Knuth-Bendix completion minimality, physical interpretation, or performance benchmark is claimed."
            ),
        },
    }


def print_human(report: Mapping[str, object]) -> None:
    language = report["canonical_language"]
    rewrite = report["rewrite_system"]
    fingerprints = report["fingerprints"]
    execution = report["execution"]
    deep = report["deep_evidence"]
    assert isinstance(language, dict)
    assert isinstance(rewrite, dict)
    assert isinstance(fingerprints, dict)
    assert isinstance(execution, dict)
    assert isinstance(deep, dict)
    print("Metaspace exact word normalizer")
    print("status:", report["status"])
    print("alphabet/order:", " < ".join(report["alphabet"]))
    print(
        "states/diameter/depth-profile = {}/{}/{}".format(
            language["state_count"], language["diameter"], language["depth_profile"]
        )
    )
    print(
        "rules/max-lhs/max-rhs = {}/{}/{}".format(
            rewrite["rule_count"],
            rewrite["maximum_lhs_length"],
            rewrite["maximum_rhs_length"],
        )
    )
    print("baseline fingerprints match:", fingerprints["baseline_match"])
    print("source word:", " ".join(execution["source_word"]) or "epsilon")
    print("expanded word:", " ".join(execution["expanded_input_word"]) or "epsilon")
    print(
        "canonical:",
        " ".join(execution["canonical_shortlex_word"]) or "epsilon",
    )
    print("state/code:", execution["state_id"], execution["signed_code"])
    if deep.get("performed") is False:
        print("deep critical-pair check: not requested")
    else:
        print(
            "critical peaks joined:",
            deep["critical_peak_count"],
            deep["all_critical_peaks_join"],
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--word",
        default="Rq Rh Lq Lh Rh Rq Lq Lq Lh",
        help="space/comma word over Lh,Rh,Lq; Rq is accepted as an exact macro",
    )
    parser.add_argument(
        "--deep-check",
        action="store_true",
        help="join every critical overlap and inject deterministic corruptions",
    )
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    args = parser.parse_args()
    try:
        source_word = parse_source_word(args.word)
        report = build_report(source_word, args.deep_check)
    except (ValueError, CertificateMismatch) as error:
        raise SystemExit(str(error))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)


if __name__ == "__main__":
    main()
