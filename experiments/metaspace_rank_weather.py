"""Exact rank weather for uniform random words in the signed metaspace.

The literal 192-state right-action automaton is minimized with matrix rank as
its Moore output.  Rank alone is not Markov: rank two contains three distinct
phases.  The exact five-state quotient is then read as a uniform finite Markov
chain, with Fraction-valued hitting times and absorption probabilities.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from fractions import Fraction
from typing import Dict, Hashable, Iterable, List, Mapping, Sequence, Set, Tuple

import certified_signed_metaspace as signed


RANK1 = "rank1_absorbing"
RANK2_FUNNEL = "rank2_funnel"
RANK2_GATE = "rank2_drop_gate"
RANK2_RETURN = "rank2_return"
RANK3 = "rank3_unit_weather"
WEATHER_ORDER = (RANK1, RANK2_FUNNEL, RANK2_GATE, RANK2_RETURN, RANK3)


def canonical_colors(values: Sequence[Hashable]) -> List[int]:
    mapping: Dict[Hashable, int] = {}
    colors: List[int] = []
    for value in values:
        if value not in mapping:
            mapping[value] = len(mapping)
        colors.append(mapping[value])
    return colors


def refine_deterministic(
    outputs: Sequence[Hashable], transitions: Sequence[Sequence[int]]
) -> Tuple[List[int], List[int]]:
    colors = canonical_colors(outputs)
    profile = [len(set(colors))]
    while True:
        signatures = [
            (colors[state], tuple(colors[target] for target in transitions[state]))
            for state in range(len(colors))
        ]
        refined = canonical_colors(signatures)
        profile.append(len(set(refined)))
        if profile[-1] == profile[-2]:
            return refined, profile
        colors = refined


def refine_uniform_counts(
    outputs: Sequence[Hashable], transitions: Sequence[Sequence[int]]
) -> Tuple[List[int], List[int]]:
    """Coarsest strong lumping for the uniform generator distribution."""

    colors = canonical_colors(outputs)
    profile = [len(set(colors))]
    while True:
        signatures = [
            (
                colors[state],
                tuple(
                    sorted(Counter(colors[target] for target in transitions[state]).items())
                ),
            )
            for state in range(len(colors))
        ]
        refined = canonical_colors(signatures)
        profile.append(len(set(refined)))
        if profile[-1] == profile[-2]:
            return refined, profile
        colors = refined


def blocks_from_colors(colors: Sequence[int]) -> Dict[int, Tuple[int, ...]]:
    return {
        color: tuple(index for index, value in enumerate(colors) if value == color)
        for color in sorted(set(colors))
    }


def stable_symbol_targets(
    colors: Sequence[int],
    transitions: Sequence[Sequence[int]],
) -> Dict[int, Tuple[int, ...]]:
    blocks = blocks_from_colors(colors)
    result: Dict[int, Tuple[int, ...]] = {}
    for color, members in blocks.items():
        signatures = {
            tuple(colors[target] for target in transitions[state]) for state in members
        }
        if len(signatures) != 1:
            raise AssertionError("deterministic quotient block is not transition-stable")
        result[color] = next(iter(signatures))
    return result


def semantic_weather_labels(
    colors: Sequence[int],
    transitions: Sequence[Sequence[int]],
    ranks: Sequence[int],
) -> Dict[int, str]:
    blocks = blocks_from_colors(colors)
    targets = stable_symbol_targets(colors, transitions)
    labels: Dict[int, str] = {}
    rank_by_color = {color: ranks[members[0]] for color, members in blocks.items()}
    rank1 = next(color for color, rank in rank_by_color.items() if rank == 1)
    rank3 = next(color for color, rank in rank_by_color.items() if rank == 3)
    labels[rank1] = RANK1
    labels[rank3] = RANK3

    rank2_colors = [color for color, rank in rank_by_color.items() if rank == 2]
    gate = next(
        color for color in rank2_colors if rank1 in set(targets[color])
    )
    funnel = next(
        color
        for color in rank2_colors
        if color != gate and len(set(targets[color])) == 1
    )
    returning = next(color for color in rank2_colors if color not in (gate, funnel))
    labels[gate] = RANK2_GATE
    labels[funnel] = RANK2_FUNNEL
    labels[returning] = RANK2_RETURN
    return labels


def build_rank_weather(
    automaton: signed.CompiledAutomaton,
) -> Tuple[List[int], Dict[int, str], Dict[str, Tuple[str, ...]], List[int]]:
    ranks = [signed.code_rank(code) for code in automaton.states]
    colors, profile = refine_deterministic(ranks, automaton.transitions)
    labels = semantic_weather_labels(colors, automaton.transitions, ranks)
    raw_targets = stable_symbol_targets(colors, automaton.transitions)
    table = {
        labels[color]: tuple(labels[target] for target in targets)
        for color, targets in raw_targets.items()
    }
    expected = {
        RANK1: (RANK1, RANK1, RANK1, RANK1),
        RANK2_FUNNEL: (RANK2_GATE, RANK2_GATE, RANK2_GATE, RANK2_GATE),
        RANK2_GATE: (RANK2_RETURN, RANK1, RANK2_RETURN, RANK1),
        RANK2_RETURN: (
            RANK2_FUNNEL,
            RANK2_GATE,
            RANK2_FUNNEL,
            RANK2_GATE,
        ),
        RANK3: (RANK3, RANK2_GATE, RANK3, RANK2_GATE),
    }
    if table != expected or profile != [3, 4, 5, 5]:
        raise AssertionError("rank-weather quotient profile changed")
    block_sizes = Counter(labels[color] for color in colors)
    if block_sizes != Counter(
        {
            RANK1: 24,
            RANK2_FUNNEL: 48,
            RANK2_GATE: 48,
            RANK2_RETURN: 48,
            RANK3: 24,
        }
    ):
        raise AssertionError("rank-weather block sizes changed")
    return colors, labels, table, profile


def fraction_payload(value: Fraction) -> Dict[str, object]:
    return {
        "exact": str(value),
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": float(value),
    }


def solve_linear(
    coefficients: Sequence[Sequence[Fraction]],
    right_sides: Sequence[Sequence[Fraction]],
) -> List[List[Fraction]]:
    rows = [list(left) + list(right) for left, right in zip(coefficients, right_sides)]
    size = len(rows)
    rhs_count = len(rows[0]) - size
    for column in range(size):
        pivot = next(
            (row for row in range(column, size) if rows[row][column]), None
        )
        if pivot is None:
            raise AssertionError("singular exact linear system")
        rows[column], rows[pivot] = rows[pivot], rows[column]
        scale = rows[column][column]
        rows[column] = [value / scale for value in rows[column]]
        for row in range(size):
            if row == column or not rows[row][column]:
                continue
            factor = rows[row][column]
            rows[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(rows[row], rows[column])
            ]
    return [row[size : size + rhs_count] for row in rows]


def uniform_weather_probabilities(
    table: Mapping[str, Sequence[str]],
) -> Dict[str, Dict[str, Fraction]]:
    return {
        state: {
            target: Fraction(count, len(signed.SYMBOLS))
            for target, count in Counter(targets).items()
        }
        for state, targets in table.items()
    }


def hitting_moments(
    probabilities: Mapping[str, Mapping[str, Fraction]],
) -> Dict[str, Dict[str, Fraction]]:
    transient = [state for state in WEATHER_ORDER if state != RANK1]
    index = {state: position for position, state in enumerate(transient)}
    coefficients: List[List[Fraction]] = []
    ones: List[List[Fraction]] = []
    for state in transient:
        row = [Fraction(int(state == target)) for target in transient]
        for target, probability in probabilities[state].items():
            if target in index:
                row[index[target]] -= probability
        coefficients.append(row)
        ones.append([Fraction(1)])
    means_vector = solve_linear(coefficients, ones)
    means = {state: means_vector[index[state]][0] for state in transient}

    second_rhs: List[List[Fraction]] = []
    for state in transient:
        expected_next = sum(
            probability * means.get(target, Fraction(0))
            for target, probability in probabilities[state].items()
        )
        second_rhs.append([Fraction(1) + 2 * expected_next])
    second_vector = solve_linear(coefficients, second_rhs)
    second = {state: second_vector[index[state]][0] for state in transient}
    result: Dict[str, Dict[str, Fraction]] = {
        RANK1: {
            "mean": Fraction(0),
            "second_moment": Fraction(0),
            "variance": Fraction(0),
        }
    }
    for state in transient:
        result[state] = {
            "mean": means[state],
            "second_moment": second[state],
            "variance": second[state] - means[state] * means[state],
        }
    return result


def hitting_distribution(
    probabilities: Mapping[str, Mapping[str, Fraction]],
    horizon: int,
) -> List[Dict[str, object]]:
    distribution: Dict[str, Fraction] = {state: Fraction(0) for state in WEATHER_ORDER}
    distribution[RANK3] = Fraction(1)
    prior_absorbed = Fraction(0)
    rows: List[Dict[str, object]] = []
    for step in range(1, horizon + 1):
        nxt = {state: Fraction(0) for state in WEATHER_ORDER}
        for state, mass in distribution.items():
            for target, probability in probabilities[state].items():
                nxt[target] += mass * probability
        absorbed = nxt[RANK1]
        first_hit = absorbed - prior_absorbed
        rows.append(
            {
                "step": step,
                "first_hit_probability": fraction_payload(first_hit),
                "absorbed_by_step": fraction_payload(absorbed),
                "survival_after_step": fraction_payload(Fraction(1) - absorbed),
            }
        )
        distribution = nxt
        prior_absorbed = absorbed
    return rows


def uniform_lumped_targets(
    colors: Sequence[int], transitions: Sequence[Sequence[int]]
) -> Dict[int, Counter[int]]:
    blocks = blocks_from_colors(colors)
    result: Dict[int, Counter[int]] = {}
    for color, members in blocks.items():
        signatures = {
            tuple(sorted(Counter(colors[target] for target in transitions[state]).items()))
            for state in members
        }
        if len(signatures) != 1:
            raise AssertionError("uniform quotient is not strongly lumpable")
        result[color] = Counter(dict(next(iter(signatures))))
    return result


def axis_absorption(
    automaton: signed.CompiledAutomaton,
) -> Dict[str, object]:
    ranks = [signed.code_rank(code) for code in automaton.states]
    outputs: List[Hashable] = [
        ("absorbed_axis", abs(code[0])) if rank == 1 else ("rank", rank)
        for code, rank in zip(automaton.states, ranks)
    ]
    colors, profile = refine_uniform_counts(outputs, automaton.transitions)
    blocks = blocks_from_colors(colors)
    targets = uniform_lumped_targets(colors, automaton.transitions)
    rank_by_color = {color: ranks[members[0]] for color, members in blocks.items()}
    absorbing = {
        color: abs(automaton.states[members[0]][0])
        for color, members in blocks.items()
        if rank_by_color[color] == 1
    }
    transient = [color for color in blocks if color not in absorbing]
    index = {color: position for position, color in enumerate(transient)}
    coefficients: List[List[Fraction]] = []
    right_sides: List[List[Fraction]] = []
    for color in transient:
        row = [Fraction(int(color == target)) for target in transient]
        rhs = [Fraction(0), Fraction(0), Fraction(0)]
        for target, count in targets[color].items():
            probability = Fraction(count, len(signed.SYMBOLS))
            if target in index:
                row[index[target]] -= probability
            else:
                rhs[absorbing[target] - 1] += probability
        coefficients.append(row)
        right_sides.append(rhs)
    solution = solve_linear(coefficients, right_sides)
    identity_color = colors[automaton.identity_state]
    probabilities = solution[index[identity_color]]
    if probabilities != [Fraction(1, 3), Fraction(1, 6), Fraction(1, 2)]:
        raise AssertionError("axis absorption probabilities changed")
    if sum(probabilities) != 1:
        raise AssertionError("axis absorption probability mass is not one")
    return {
        "uniform_lumping_block_count": len(blocks),
        "uniform_lumping_refinement_profile": profile,
        "block_size_profile": {
            str(size): count for size, count in sorted(Counter(map(len, blocks.values())).items())
        },
        "probability_from_identity": {
            name: fraction_payload(probability)
            for name, probability in zip(("1", "h", "q"), probabilities)
        },
        "probability_sum": fraction_payload(sum(probabilities)),
        "equal_island_sizes_do_not_imply_equal_entry_measure": True,
    }


def strongly_connected_components(
    transitions: Sequence[Sequence[int]],
) -> Tuple[Tuple[int, ...], ...]:
    indices = [-1] * len(transitions)
    low = [0] * len(transitions)
    stack: List[int] = []
    on_stack: Set[int] = set()
    components: List[Tuple[int, ...]] = []
    next_index = 0

    def visit(state: int) -> None:
        nonlocal next_index
        indices[state] = low[state] = next_index
        next_index += 1
        stack.append(state)
        on_stack.add(state)
        for target in transitions[state]:
            if indices[target] < 0:
                visit(target)
                low[state] = min(low[state], low[target])
            elif target in on_stack:
                low[state] = min(low[state], indices[target])
        if low[state] == indices[state]:
            members: List[int] = []
            while True:
                target = stack.pop()
                on_stack.remove(target)
                members.append(target)
                if target == state:
                    break
            components.append(tuple(sorted(members)))

    for state in range(len(transitions)):
        if indices[state] < 0:
            visit(state)
    return tuple(components)


def scc_weather_transversality(
    automaton: signed.CompiledAutomaton,
    weather_colors: Sequence[int],
    weather_labels: Mapping[int, str],
) -> Dict[str, object]:
    ranks = [signed.code_rank(code) for code in automaton.states]
    components = strongly_connected_components(automaton.transitions)
    component_of = {
        state: component_index
        for component_index, members in enumerate(components)
        for state in members
    }
    profile = Counter((ranks[members[0]], len(members)) for members in components)
    if profile != Counter({(1, 8): 3, (2, 48): 3, (3, 24): 1}):
        raise AssertionError("SCC profile changed")

    rank2_components = [
        (index, members)
        for index, members in enumerate(components)
        if ranks[members[0]] == 2
    ]
    grid: Dict[str, Dict[str, int]] = {}
    for component_index, members in rank2_components:
        image_sets = {
            tuple(sorted({abs(value) for value in automaton.states[state]}))
            for state in members
        }
        if len(image_sets) != 1:
            raise AssertionError("rank-two SCC does not preserve its signed image axes")
        image = next(iter(image_sets))
        image_label = "image{" + ",".join(COLUMN_NAMES[value - 1] for value in image) + "}"
        grid[image_label] = {
            weather_labels[color]: sum(
                1 for state in members if weather_colors[state] == color
            )
            for color in sorted(set(weather_colors[state] for state in members))
        }
        if set(grid[image_label].values()) != {16}:
            raise AssertionError("rank-two SCC/weather phase grid changed")

    closed_components = []
    for component_index, members in enumerate(components):
        member_set = set(members)
        if all(
            target in member_set
            for state in members
            for target in automaton.transitions[state]
        ):
            closed_components.append(component_index)
    if len(closed_components) != 3 or any(
        ranks[components[index][0]] != 1 for index in closed_components
    ):
        raise AssertionError("closed SCC profile changed")

    return {
        "scc_count": len(components),
        "scc_rank_size_profile": {
            "rank{}_size{}".format(rank, size): count
            for (rank, size), count in sorted(profile.items())
        },
        "closed_rank_one_island_count": len(closed_components),
        "rank_two_green_R_by_weather_phase_grid": grid,
        "grid_cell_size": 16,
        "interpretation": (
            "three rank-two Green-R/SCC image classes and three rank-weather "
            "phases are transverse 3x3 decompositions"
        ),
        "component_index_is_internal_only": sorted(set(component_of.values()))
        == list(range(len(components))),
    }


COLUMN_NAMES = ("1", "h", "q")


def build_report(horizon: int, deep_check: bool) -> Dict[str, object]:
    automaton, certificate = signed.build_automaton(deep_check=False)
    weather_colors, weather_labels, table, refinement = build_rank_weather(automaton)
    probabilities = uniform_weather_probabilities(table)
    moments = hitting_moments(probabilities)
    if moments[RANK3]["mean"] != Fraction(11, 2):
        raise AssertionError("identity absorption mean changed")
    if moments[RANK3]["variance"] != Fraction(59, 4):
        raise AssertionError("identity absorption variance changed")

    rank_counts = Counter(signed.code_rank(code) for code in automaton.states)
    report: Dict[str, object] = {
        "status": "exact_uniform_rank_weather_verified",
        "source_fingerprints": {
            "model_sha256": automaton.model_fingerprint,
            "state_sha256": automaton.state_fingerprint,
            "transition_table_sha256": automaton.table_fingerprint,
        },
        "source_certificate": certificate,
        "rank_observation": {
            "raw_rank_profile": {
                str(rank): count for rank, count in sorted(rank_counts.items())
            },
            "rank_is_not_itself_Markov": True,
            "minimal_deterministic_Moore_block_count": len(set(weather_colors)),
            "refinement_class_counts": refinement,
            "block_sizes": dict(sorted(Counter(weather_labels[color] for color in weather_colors).items())),
            "transition_table": {
                state: dict(zip(signed.SYMBOLS, table[state])) for state in WEATHER_ORDER
            },
        },
        "uniform_generator_weather": {
            "generator_probability": fraction_payload(Fraction(1, 4)),
            "h_family_probability": fraction_payload(Fraction(1, 2)),
            "q_family_probability": fraction_payload(Fraction(1, 2)),
            "transition_probabilities": {
                state: {
                    target: fraction_payload(probability)
                    for target, probability in sorted(targets.items())
                }
                for state, targets in probabilities.items()
            },
            "rank_one_hitting_moments": {
                state: {name: fraction_payload(value) for name, value in values.items()}
                for state, values in moments.items()
            },
            "identity_mean_steps_to_rank_one": fraction_payload(moments[RANK3]["mean"]),
            "identity_variance_steps_to_rank_one": fraction_payload(
                moments[RANK3]["variance"]
            ),
            "first_hit_distribution_through_horizon": hitting_distribution(
                probabilities, horizon
            ),
        },
        "absorbing_axis_measure": axis_absorption(automaton),
        "scc_geometry": scc_weather_transversality(
            automaton, weather_colors, weather_labels
        ),
        "epistemic_scope": {
            "exact": "All probabilities are fractions induced by four equiprobable literal generators.",
            "lumping": (
                "The five-state weather machine is the exact deterministic Moore "
                "quotient for rank output, not an assumed three-rank approximation."
            ),
            "not_claimed": (
                "No thermodynamic equilibrium, physical randomness, entropy law, or "
                "non-uniform generator distribution is inferred."
            ),
        },
    }
    if deep_check:
        import metaspace_synchronizer as synchronizer

        companion = synchronizer.build_report(False)
        green = companion["green_structure"]["principal_right_ideals_green_R"]
        assert isinstance(green, dict)
        report["deep_cross_check"] = {
            "performed": True,
            "green_R_class_profile_matches_SCC_profile": green[
                "green_class_size_profile"
            ]
            == {"8": 3, "24": 1, "48": 3},
            "minimum_image_matches_absorbing_floor": companion[
                "right_action_synchronization"
            ]["minimum_image_size"]
            == 6,
        }
        if not all(report["deep_cross_check"].values()):
            raise AssertionError("weather companion cross-check failed")
    else:
        report["deep_cross_check"] = {
            "performed": False,
            "available_via": "--deep-check",
        }
    return report


def print_human(report: Mapping[str, object]) -> None:
    rank = report["rank_observation"]
    weather = report["uniform_generator_weather"]
    axis = report["absorbing_axis_measure"]
    scc = report["scc_geometry"]
    assert isinstance(rank, dict)
    assert isinstance(weather, dict)
    assert isinstance(axis, dict)
    assert isinstance(scc, dict)
    print("Metaspace rank weather (exact uniform random words)")
    print(
        "rank profile / Moore refinement:",
        rank["raw_rank_profile"],
        "/",
        rank["refinement_class_counts"],
    )
    print("weather blocks:", rank["block_sizes"])
    print("mean steps identity -> rank1:", weather["identity_mean_steps_to_rank_one"]["exact"])
    print("variance:", weather["identity_variance_steps_to_rank_one"]["exact"])
    print("absorbing axis probabilities:")
    for name, probability in axis["probability_from_identity"].items():
        print("  {}: {}".format(name, probability["exact"]))
    print("SCC profile:", scc["scc_rank_size_profile"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--horizon",
        type=int,
        default=12,
        help="finite first-hit distribution horizon (1..64; default: 12)",
    )
    parser.add_argument("--deep-check", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.horizon <= 64:
        raise SystemExit("--horizon must be between 1 and 64")
    report = build_report(args.horizon, args.deep_check)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)


if __name__ == "__main__":
    main()
