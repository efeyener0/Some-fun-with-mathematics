#!/usr/bin/env python3
"""Exact synchronization probe for the 192-state chiral operator monoid.

The four generators and integer matrix multiplication are imported from
``chiral_operator_monoids.py``.  Words are extended on the right:

    product(g1 ... gk) = (((I * g1) * g2) ... * gk)
    delta(x, g) = x * g

Thus the image of the right-action word represented by ``p`` is ``M*p``.
This is a principal *left* ideal, despite the generators acting on the right.
Principal right ideals ``p*M`` and Green-R data are computed separately.

Every search is over the already finite 192-element monoid.  No unbounded
word enumeration, random sampling, or floating-point arithmetic is used.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable, Mapping, Optional, Sequence

import chiral_operator_monoids as source


Matrix = source.Matrix

GENERATOR_NAMES = ("L_h", "L_q", "R_h", "R_q")
GENERATORS: tuple[Matrix, ...] = (
    source.L_H,
    source.L_Q,
    source.R_H,
    source.R_Q,
)
COLUMN_NAMES = ("1", "h", "q")

EXPECTED_STATE_COUNT = 192
EXPECTED_STATE_DIGEST = "c7c110dce5fc69818255a07552b35c0b50f163aa624a63e06ade0eaa1db1c9fc"
EXPECTED_DEPTH_PROFILE = {0: 1, 1: 4, 2: 14, 3: 32, 4: 44, 5: 37, 6: 24, 7: 20, 8: 12, 9: 4}


@dataclass(frozen=True, slots=True)
class MonoidAutomaton:
    states: tuple[Matrix, ...]
    index: Mapping[Matrix, int]
    depths: tuple[int, ...]
    words: tuple[tuple[int, ...], ...]
    generator_state_indices: tuple[int, ...]
    transitions: tuple[tuple[int, ...], ...]
    multiplication: tuple[tuple[int, ...], ...]


def counter_dict(counter: Counter[int]) -> dict[str, int]:
    return {str(key): counter[key] for key in sorted(counter)}


def tuple_counter_dict(counter: Counter[tuple[int, ...]]) -> dict[str, int]:
    return {
        ",".join(str(value) for value in key): counter[key]
        for key in sorted(counter)
    }


def word_text(word: Sequence[int]) -> str:
    return "epsilon" if not word else " ".join(GENERATOR_NAMES[index] for index in word)


def state_id(index: int) -> str:
    return f"S{index:03d}"


def matrix_column(matrix: Matrix, column: int) -> tuple[int, int, int]:
    return (matrix[column], matrix[3 + column], matrix[6 + column])


def matrix_rows(matrix: Matrix) -> list[list[int]]:
    return source.matrix_rows(matrix)


def ideal_digest(indices: Iterable[int]) -> str:
    payload = ",".join(str(index) for index in sorted(indices)).encode("ascii")
    return sha256(payload).hexdigest()


def enumerate_automaton() -> MonoidAutomaton:
    """Shortlex BFS of monoid products, followed by the exact Cayley table."""

    states: list[Matrix] = [source.I3]
    index: dict[Matrix, int] = {source.I3: 0}
    depths: list[int] = [0]
    words: list[tuple[int, ...]] = [()]
    queue: deque[int] = deque([0])

    while queue:
        state_index = queue.popleft()
        state = states[state_index]
        for generator_index, generator in enumerate(GENERATORS):
            candidate = source.matrix_multiply(state, generator)
            if candidate in index:
                continue
            index[candidate] = len(states)
            states.append(candidate)
            depths.append(depths[state_index] + 1)
            words.append(words[state_index] + (generator_index,))
            queue.append(len(states) - 1)

    if len(states) != EXPECTED_STATE_COUNT:
        raise AssertionError(f"combined monoid has {len(states)} states, expected 192")
    if source.matrix_digest(states) != EXPECTED_STATE_DIGEST:
        raise AssertionError("combined state-set digest disagrees with the source probe")
    if Counter(depths) != Counter(EXPECTED_DEPTH_PROFILE):
        raise AssertionError("minimal-word depth profile changed")
    if depths != sorted(depths):
        raise AssertionError("BFS state order is not nondecreasing in word length")
    if words != sorted(words, key=lambda word: (len(word), word)):
        raise AssertionError("BFS representatives are not in deterministic shortlex order")

    table_rows: list[tuple[int, ...]] = []
    for left in states:
        row: list[int] = []
        for right in states:
            product_matrix = source.matrix_multiply(left, right)
            try:
                row.append(index[product_matrix])
            except KeyError as error:
                raise AssertionError("combined state set is not pairwise closed") from error
        table_rows.append(tuple(row))
    multiplication = tuple(table_rows)

    generator_state_indices = tuple(index[generator] for generator in GENERATORS)
    transitions = tuple(
        tuple(multiplication[state][generator] for generator in generator_state_indices)
        for state in range(len(states))
    )
    return MonoidAutomaton(
        states=tuple(states),
        index=index,
        depths=tuple(depths),
        words=tuple(words),
        generator_state_indices=generator_state_indices,
        transitions=transitions,
        multiplication=multiplication,
    )


def shortest_representative(data: MonoidAutomaton, members: Iterable[int]) -> int:
    return min(members, key=lambda index: (data.depths[index], data.words[index]))


def principal_left_ideals(data: MonoidAutomaton) -> tuple[frozenset[int], ...]:
    """Return M*p, the right-action automaton images."""

    size = len(data.states)
    return tuple(
        frozenset(data.multiplication[left][product] for left in range(size))
        for product in range(size)
    )


def principal_right_ideals(data: MonoidAutomaton) -> tuple[frozenset[int], ...]:
    """Return p*M, the ideals defining Green-R equivalence."""

    return tuple(frozenset(data.multiplication[product]) for product in range(len(data.states)))


def kernel_fiber_signature(data: MonoidAutomaton, product: int) -> tuple[tuple[int, int], ...]:
    fibers = Counter(
        data.multiplication[start][product] for start in range(len(data.states))
    )
    return tuple(sorted(Counter(fibers.values()).items()))


def analyze_images(
    data: MonoidAutomaton,
    left_ideals: Sequence[frozenset[int]],
) -> dict[str, object]:
    image_sizes = tuple(len(ideal) for ideal in left_ideals)
    profile = Counter(image_sizes)
    if profile != Counter({192: 24, 36: 144, 6: 24}):
        raise AssertionError(f"unexpected transformation image profile: {profile}")

    first_by_size: dict[int, int] = {}
    for product, image_size in enumerate(image_sizes):
        first_by_size.setdefault(image_size, product)

    record_minimum = len(data.states) + 1
    drop_events: list[dict[str, object]] = []
    for product, image_size in enumerate(image_sizes):
        if image_size >= record_minimum:
            continue
        record_minimum = image_size
        drop_events.append(
            {
                "depth": data.depths[product],
                "word": word_text(data.words[product]),
                "state_id": state_id(product),
                "matrix_rank": source.matrix_rank(data.states[product]),
                "image_size": image_size,
            }
        )

    shortest_by_size = []
    for image_size in sorted(first_by_size, reverse=True):
        product = first_by_size[image_size]
        shortest_by_size.append(
            {
                "image_size": image_size,
                "depth": data.depths[product],
                "word": word_text(data.words[product]),
                "state_id": state_id(product),
                "matrix_rank": source.matrix_rank(data.states[product]),
                "matrix": matrix_rows(data.states[product]),
            }
        )

    depth_profile: list[dict[str, object]] = []
    for depth in range(max(data.depths) + 1):
        products = [index for index, value in enumerate(data.depths) if value == depth]
        depth_profile.append(
            {
                "depth": depth,
                "state_count": len(products),
                "image_size_profile": counter_dict(
                    Counter(image_sizes[index] for index in products)
                ),
            }
        )

    fiber_profiles: dict[int, Counter[tuple[tuple[int, int], ...]]] = defaultdict(Counter)
    for product, image_size in enumerate(image_sizes):
        fiber_profiles[image_size][kernel_fiber_signature(data, product)] += 1
    expected_fibers = {
        192: Counter({((1, 192),): 24}),
        36: Counter({((4, 12), (6, 24)): 144}),
        6: Counter({((32, 6),): 24}),
    }
    if dict(fiber_profiles) != expected_fibers:
        raise AssertionError("right-transformation kernel fiber profiles changed")
    rendered_fibers: list[dict[str, object]] = []
    for image_size in sorted(fiber_profiles, reverse=True):
        for signature, element_count in sorted(fiber_profiles[image_size].items()):
            rendered_fibers.append(
                {
                    "image_size": image_size,
                    "element_count": element_count,
                    "fiber_size_multiplicity": {
                        str(fiber_size): multiplicity
                        for fiber_size, multiplicity in signature
                    },
                }
            )

    minimum = min(image_sizes)
    minimum_products = [
        index for index, image_size in enumerate(image_sizes) if image_size == minimum
    ]
    minimum_witness = shortest_representative(data, minimum_products)
    transformations = {
        tuple(data.multiplication[start][product] for start in range(len(data.states)))
        for product in range(len(data.states))
    }
    if len(transformations) != len(data.states):
        raise AssertionError("distinct products induced the same right transformation")

    return {
        "reachable_image_sizes": sorted(profile),
        "image_size_profile_over_192_word_products": counter_dict(profile),
        "shortest_representative_by_image_size": shortest_by_size,
        "record_image_size_drops": drop_events,
        "depth_image_profile": depth_profile,
        "minimum_image_size": minimum,
        "minimum_image_product_count": len(minimum_products),
        "minimum_word_length": data.depths[minimum_witness],
        "minimum_word": word_text(data.words[minimum_witness]),
        "minimum_word_state_id": state_id(minimum_witness),
        "reset_word_exists": minimum == 1,
        "right_transformation_count": len(transformations),
        "right_regular_action_is_faithful": len(transformations) == len(data.states),
        "faithfulness_witness": "R_p(identity)=p",
        "kernel_fiber_profiles": rendered_fibers,
    }


def column_subset_label(columns: Sequence[int]) -> str:
    return "{" + ",".join(COLUMN_NAMES[index] for index in columns) + "}"


def graph_connected(adjacency: Sequence[set[int]]) -> bool:
    reached = {0}
    stack = [0]
    while stack:
        current = stack.pop()
        for neighbor in adjacency[current]:
            if neighbor not in reached:
                reached.add(neighbor)
                stack.append(neighbor)
    return len(reached) == len(adjacency)


def analyze_pairs(data: MonoidAutomaton) -> dict[str, object]:
    size = len(data.states)
    total_pairs = size * (size - 1) // 2
    merge_depths: Counter[int] = Counter()
    merge_witness_ranks: Counter[tuple[int, int]] = Counter()
    subset_counts: Counter[tuple[int, ...]] = Counter()
    subset_records: dict[tuple[int, ...], dict[str, object]] = {}
    nonsync_rank_pairs: Counter[tuple[int, int]] = Counter()
    synchronizable_type_profile: Counter[str] = Counter()
    sync_adjacency = [set() for _ in range(size)]
    synchronizable = 0

    for left in range(size):
        for right in range(left + 1, size):
            equal_columns = tuple(
                column
                for column in range(3)
                if matrix_column(data.states[left], column)
                == matrix_column(data.states[right], column)
            )
            witness = next(
                (
                    product
                    for product in range(size)
                    if data.multiplication[left][product]
                    == data.multiplication[right][product]
                ),
                None,
            )
            if (witness is not None) != bool(equal_columns):
                raise AssertionError("pair synchronization disagrees with column equality")

            if witness is None:
                ranks = tuple(
                    sorted(
                        (
                            source.matrix_rank(data.states[left]),
                            source.matrix_rank(data.states[right]),
                        )
                    )
                )
                nonsync_rank_pairs[ranks] += 1
                continue

            synchronizable += 1
            sync_adjacency[left].add(right)
            sync_adjacency[right].add(left)
            depth = data.depths[witness]
            merge_depths[depth] += 1
            merge_witness_ranks[(depth, source.matrix_rank(data.states[witness]))] += 1
            subset_counts[equal_columns] += 1
            unit_count = sum(
                abs(source.determinant(data.states[index])) == 1
                for index in (left, right)
            )
            synchronizable_type_profile[
                {0: "singular-singular", 1: "unit-singular", 2: "unit-unit"}[unit_count]
            ] += 1

            candidate = (
                depth,
                data.words[witness],
                left,
                right,
            )
            previous = subset_records.get(equal_columns)
            if previous is None or candidate < previous["sort_key"]:
                subset_records[equal_columns] = {
                    "sort_key": candidate,
                    "equal_columns": column_subset_label(equal_columns),
                    "pair_count": 0,
                    "shortest_merge_depth": depth,
                    "word": word_text(data.words[witness]),
                    "word_state_id": state_id(witness),
                    "left_state": state_id(left),
                    "right_state": state_id(right),
                }

    nonsynchronizable = total_pairs - synchronizable
    if synchronizable != 7632 or nonsynchronizable != 10704:
        raise AssertionError("pair synchronization profile changed")
    if merge_depths != Counter({1: 432, 2: 2976, 3: 2112, 4: 2112}):
        raise AssertionError(f"unexpected shortest merge-depth profile: {merge_depths}")
    if subset_counts != Counter(
        {
            (0,): 2112,
            (1,): 2112,
            (2,): 2112,
            (0, 1): 432,
            (0, 2): 432,
            (1, 2): 432,
        }
    ):
        raise AssertionError("equal-column subset profile changed")

    subset_summaries = []
    for columns in sorted(subset_records):
        record = dict(subset_records[columns])
        record.pop("sort_key")
        record["pair_count"] = subset_counts[columns]
        subset_summaries.append(record)
    expected_subset_witnesses = {
        (0,): (3, "L_h L_q L_q"),
        (1,): (4, "L_h L_h L_q L_q"),
        (2,): (2, "L_q L_q"),
        (0, 1): (2, "L_h L_q"),
        (0, 2): (1, "L_q"),
        (1, 2): (2, "L_q L_q"),
    }
    actual_subset_witnesses = {
        columns: (
            int(record["shortest_merge_depth"]),
            str(record["word"]),
        )
        for columns, record in subset_records.items()
    }
    if actual_subset_witnesses != expected_subset_witnesses:
        raise AssertionError("deterministic equal-column merge witnesses changed")

    witness_rank_profile: dict[str, dict[str, int]] = {}
    for (depth, rank), count in sorted(merge_witness_ranks.items()):
        witness_rank_profile.setdefault(str(depth), {})[str(rank)] = count

    rank_one_image_lines: set[tuple[int, ...]] = set()
    for matrix in data.states:
        if source.matrix_rank(matrix) != 1:
            continue
        nonzero_rows = tuple(
            row
            for row in range(3)
            if any(matrix[3 * row + column] for column in range(3))
        )
        if len(nonzero_rows) != 1:
            raise AssertionError("rank-one signed-basis action has a non-coordinate image")
        rank_one_image_lines.add(nonzero_rows)
    if rank_one_image_lines != {(0,), (1,), (2,)}:
        raise AssertionError("rank-one products do not reach all three coordinate lines")

    return {
        "unordered_pair_count": total_pairs,
        "synchronizable_pair_count": synchronizable,
        "nonsynchronizable_pair_count": nonsynchronizable,
        "all_pairs_synchronizable": nonsynchronizable == 0,
        "shortest_merge_depth_profile": counter_dict(merge_depths),
        "maximum_shortest_merge_depth": max(merge_depths),
        "synchronizable_pair_type_profile": dict(sorted(synchronizable_type_profile.items())),
        "nonsynchronizable_pair_matrix_rank_profile": tuple_counter_dict(
            nonsync_rank_pairs
        ),
        "equal_column_subset_profile": {
            column_subset_label(columns): subset_counts[columns]
            for columns in sorted(subset_counts)
        },
        "deterministic_merge_witness_by_exact_equal_column_set": subset_summaries,
        "merge_witness_matrix_rank_by_depth": witness_rank_profile,
        "pair_synchronization_criterion": (
            "x and y are synchronizable iff their 3x3 action matrices have "
            "at least one identical basis column"
        ),
        "criterion_verified_for_all_pairs": True,
        "rank_one_product_image_coordinate_lines": [
            COLUMN_NAMES[rows[0]] for rows in sorted(rank_one_image_lines)
        ],
        "synchronizability_graph_connected": graph_connected(sync_adjacency),
    }


def classify_ideal_family(
    data: MonoidAutomaton,
    ideals: Sequence[frozenset[int]],
    prefix: str,
    convention: str,
) -> dict[str, object]:
    grouped: dict[frozenset[int], list[int]] = {}
    for element, ideal in enumerate(ideals):
        grouped.setdefault(ideal, []).append(element)

    ordered = sorted(
        grouped.items(),
        key=lambda item: (
            -len(item[0]),
            data.depths[shortest_representative(data, item[1])],
            data.words[shortest_representative(data, item[1])],
        ),
    )
    ideal_ids = {ideal: f"{prefix}{index}" for index, (ideal, _) in enumerate(ordered)}

    classes: list[dict[str, object]] = []
    for ideal, members in ordered:
        representative = shortest_representative(data, members)
        ranks = Counter(source.matrix_rank(data.states[index]) for index in members)
        classes.append(
            {
                "class_id": ideal_ids[ideal],
                "ideal_size": len(ideal),
                "class_size": len(members),
                "matrix_rank_profile": counter_dict(ranks),
                "minimum_word_length": data.depths[representative],
                "witness_word": word_text(data.words[representative]),
                "witness_state_id": state_id(representative),
                "class_members": [state_id(index) for index in members],
                "ideal_state_id_sha256": ideal_digest(ideal),
            }
        )

    covers: list[dict[str, object]] = []
    for lower, _ in ordered:
        for upper, _ in ordered:
            if not lower < upper:
                continue
            if any(lower < middle < upper for middle, _ in ordered):
                continue
            covers.append(
                {
                    "lower": ideal_ids[lower],
                    "upper": ideal_ids[upper],
                    "lower_size": len(lower),
                    "upper_size": len(upper),
                }
            )

    cover_profile = Counter((entry["lower_size"], entry["upper_size"]) for entry in covers)
    return {
        "convention": convention,
        "distinct_ideal_count": len(ordered),
        "element_ideal_size_profile": counter_dict(Counter(len(ideal) for ideal in ideals)),
        "distinct_ideal_size_profile": counter_dict(
            Counter(len(ideal) for ideal, _ in ordered)
        ),
        "green_class_size_profile": counter_dict(
            Counter(len(members) for _, members in ordered)
        ),
        "classes": classes,
        "hasse_cover_count": len(covers),
        "hasse_cover_size_profile": {
            f"{lower}->{upper}": cover_profile[(lower, upper)]
            for lower, upper in sorted(cover_profile)
        },
        "hasse_covers": covers,
    }


def two_sided_ideals(data: MonoidAutomaton) -> tuple[frozenset[int], ...]:
    size = len(data.states)
    ideals: list[frozenset[int]] = []
    for product in range(size):
        values: set[int] = set()
        for left in range(size):
            left_product = data.multiplication[left][product]
            values.update(data.multiplication[left_product])
        ideals.append(frozenset(values))
    return tuple(ideals)


def green_structure(
    data: MonoidAutomaton,
    left_ideals: Sequence[frozenset[int]],
    right_ideals: Sequence[frozenset[int]],
) -> dict[str, object]:
    left = classify_ideal_family(
        data,
        left_ideals,
        "L",
        "M*p; automaton image under right multiplication; Green-L",
    )
    right = classify_ideal_family(
        data,
        right_ideals,
        "R",
        "p*M; principal right ideal; Green-R",
    )
    if (
        left["distinct_ideal_size_profile"] != {"6": 4, "36": 6, "192": 1}
        or left["green_class_size_profile"] != {"6": 4, "24": 7}
        or left["hasse_cover_size_profile"]
        != {"6->36": 12, "36->192": 6}
    ):
        raise AssertionError("Green-L profile changed")
    if (
        right["distinct_ideal_size_profile"] != {"8": 3, "64": 3, "192": 1}
        or right["green_class_size_profile"] != {"8": 3, "24": 1, "48": 3}
        or right["hasse_cover_size_profile"]
        != {"8->64": 6, "64->192": 3}
    ):
        raise AssertionError("Green-R profile changed")

    j_ideals = two_sided_ideals(data)
    j = classify_ideal_family(
        data,
        j_ideals,
        "J",
        "M*p*M; principal two-sided ideal; Green-J",
    )
    if j["distinct_ideal_size_profile"] != {"24": 1, "168": 1, "192": 1}:
        raise AssertionError("Green-J profile changed")
    if j["hasse_cover_size_profile"] != {"24->168": 1, "168->192": 1}:
        raise AssertionError("Green-J Hasse chain changed")

    h_groups: dict[tuple[frozenset[int], frozenset[int]], list[int]] = defaultdict(list)
    for element in range(len(data.states)):
        h_groups[(left_ideals[element], right_ideals[element])].append(element)
    h_size_profile = Counter(len(members) for members in h_groups.values())
    h_rank_profile: dict[str, Counter[int]] = defaultdict(Counter)
    idempotent_bearing = 0
    for members in h_groups.values():
        rank = source.matrix_rank(data.states[members[0]])
        h_rank_profile[str(rank)][len(members)] += 1
        idempotents = [
            element
            for element in members
            if data.multiplication[element][element] == element
        ]
        if idempotents:
            if len(idempotents) != 1:
                raise AssertionError("an H-class contains multiple idempotents")
            idempotent_bearing += 1
    if (
        len(h_groups) != 31
        or h_size_profile != Counter({8: 18, 2: 12, 24: 1})
        or idempotent_bearing != 25
    ):
        raise AssertionError("Green-H profile changed")

    # Green-D is the connectivity closure of L and R equivalence.
    adjacency = [set() for _ in data.states]
    left_groups: dict[frozenset[int], list[int]] = defaultdict(list)
    right_groups: dict[frozenset[int], list[int]] = defaultdict(list)
    for element in range(len(data.states)):
        left_groups[left_ideals[element]].append(element)
        right_groups[right_ideals[element]].append(element)
    for family in (left_groups, right_groups):
        for members in family.values():
            anchor = members[0]
            for member in members[1:]:
                adjacency[anchor].add(member)
                adjacency[member].add(anchor)
    remaining = set(range(len(data.states)))
    d_classes: list[frozenset[int]] = []
    while remaining:
        start = min(remaining)
        reached = {start}
        stack = [start]
        while stack:
            current = stack.pop()
            for neighbor in adjacency[current]:
                if neighbor not in reached:
                    reached.add(neighbor)
                    stack.append(neighbor)
        component = frozenset(reached)
        d_classes.append(component)
        remaining.difference_update(component)
    # Elements have equal J-ideal exactly when they are J-related.
    grouped_j_members: dict[frozenset[int], set[int]] = defaultdict(set)
    for element, ideal in enumerate(j_ideals):
        grouped_j_members[ideal].add(element)
    if {frozenset(members) for members in grouped_j_members.values()} != set(d_classes):
        raise AssertionError("Green-D and Green-J partitions differ")
    if Counter(len(group) for group in d_classes) != Counter({24: 2, 144: 1}):
        raise AssertionError("Green-D class profile changed")

    return {
        "principal_left_ideals_green_L": left,
        "principal_right_ideals_green_R": right,
        "principal_two_sided_ideals_green_J": j,
        "green_H": {
            "class_count": len(h_groups),
            "class_size_profile": counter_dict(h_size_profile),
            "class_size_profile_by_matrix_rank": {
                rank: counter_dict(profile)
                for rank, profile in sorted(h_rank_profile.items())
            },
            "idempotent_bearing_H_class_count": idempotent_bearing,
            "H_classes_without_idempotent": len(h_groups) - idempotent_bearing,
        },
        "green_D": {
            "class_count": len(d_classes),
            "class_size_profile": counter_dict(Counter(len(group) for group in d_classes)),
            "D_equals_J_verified": True,
        },
        "computed_incidence_reading": {
            "green_L": (
                "4 size-6 bottom ideals, each covered by 3 of 6 size-36 ideals; "
                "each size-36 ideal covers 2 bottoms; then one size-192 top"
            ),
            "green_R": (
                "3 size-8 bottom ideals, each covered by 2 of 3 size-64 ideals; "
                "each size-64 ideal covers 2 bottoms; then one size-192 top"
            ),
            "green_J": "a three-level chain of ideal sizes 24 < 168 < 192",
        },
    }


def analyze_rank_relation(
    data: MonoidAutomaton,
    left_ideals: Sequence[frozenset[int]],
    right_ideals: Sequence[frozenset[int]],
) -> dict[str, object]:
    ranks = tuple(source.matrix_rank(matrix) for matrix in data.states)
    rows: list[dict[str, object]] = []
    image_mapping: dict[int, set[int]] = defaultdict(set)
    right_mapping: dict[int, set[int]] = defaultdict(set)
    for element, rank in enumerate(ranks):
        image_mapping[rank].add(len(left_ideals[element]))
        right_mapping[rank].add(len(right_ideals[element]))
    for rank in sorted(set(ranks), reverse=True):
        rows.append(
            {
                "matrix_rank": rank,
                "element_count": ranks.count(rank),
                "right_action_image_sizes_M_times_p": sorted(image_mapping[rank]),
                "principal_right_ideal_sizes_p_times_M": sorted(right_mapping[rank]),
            }
        )
    if {rank: values for rank, values in image_mapping.items()} != {
        3: {192},
        2: {36},
        1: {6},
    }:
        raise AssertionError("matrix rank no longer determines automaton image size")
    if {rank: values for rank, values in right_mapping.items()} != {
        3: {192},
        2: {64},
        1: {8},
    }:
        raise AssertionError("matrix rank no longer determines principal right-ideal size")
    return {
        "matrix_rank_profile": counter_dict(Counter(ranks)),
        "matrix_rank_determines_both_sizes_in_this_monoid": True,
        "relation": rows,
        "warning": (
            "matrix rank and transformation image size are different invariants; "
            "the exact one-to-one profile here is a property of this finite monoid"
        ),
    }


def run_deep_checks(
    data: MonoidAutomaton,
    left_ideals: Sequence[frozenset[int]],
    right_ideals: Sequence[frozenset[int]],
) -> dict[str, object]:
    size = len(data.states)
    associativity_checks = 0
    for left in range(size):
        left_row = data.multiplication[left]
        for middle in range(size):
            left_middle_row = data.multiplication[left_row[middle]]
            middle_row = data.multiplication[middle]
            for right in range(size):
                associativity_checks += 1
                if left_middle_row[right] != left_row[middle_row[right]]:
                    raise AssertionError("Cayley table is not associative")

    word_replays = 0
    for expected, word in enumerate(data.words):
        current = 0
        for generator in word:
            word_replays += 1
            current = data.transitions[current][generator]
        if current != expected:
            raise AssertionError("stored shortest word does not replay to its state")

    left_closure_checks = 0
    for ideal in set(left_ideals):
        for multiplier in range(size):
            row = data.multiplication[multiplier]
            for element in ideal:
                left_closure_checks += 1
                if row[element] not in ideal:
                    raise AssertionError("M*p is not closed under left multiplication")

    right_closure_checks = 0
    for ideal in set(right_ideals):
        for multiplier in range(size):
            for element in ideal:
                right_closure_checks += 1
                if data.multiplication[element][multiplier] not in ideal:
                    raise AssertionError("p*M is not closed under right multiplication")

    return {
        "performed": True,
        "associativity_triples_checked": associativity_checks,
        "stored_word_generator_steps_replayed": word_replays,
        "principal_left_ideal_closure_products_checked": left_closure_checks,
        "principal_right_ideal_closure_products_checked": right_closure_checks,
        "all_checks_passed": True,
    }


def build_report(deep_check: bool) -> dict[str, object]:
    data = enumerate_automaton()
    left_ideals = principal_left_ideals(data)
    right_ideals = principal_right_ideals(data)
    images = analyze_images(data, left_ideals)
    pairs = analyze_pairs(data)
    green = green_structure(data, left_ideals, right_ideals)
    rank_relation = analyze_rank_relation(data, left_ideals, right_ideals)

    if images["reset_word_exists"] or pairs["all_pairs_synchronizable"]:
        raise AssertionError("reset/pair conclusion changed")
    if (images["reset_word_exists"] is False) != (
        pairs["all_pairs_synchronizable"] is False
    ):
        raise AssertionError("reset theorem and pair profile disagree")

    deep = (
        run_deep_checks(data, left_ideals, right_ideals)
        if deep_check
        else {
            "performed": False,
            "all_checks_passed": None,
            "note": "use --deep-check for all 192^3 Cayley associativity triples and ideal closure products",
        }
    )
    return {
        "method": {
            "source": "local chiral_operator_monoids.py literal matrices",
            "state_enumeration": "shortlex BFS of products; append generators on the right",
            "state_transition": "delta(x,g)=x*g",
            "word_product": "(((I*g1)*g2)*...)*gk",
            "automaton_image_for_product_p": "M*p (a principal left ideal)",
            "principal_right_ideal": "p*M (computed separately for Green-R)",
            "arithmetic": "exact Python integers and finite set operations",
            "generator_order": list(GENERATOR_NAMES),
        },
        "monoid": {
            "state_count": len(data.states),
            "generator_count": len(GENERATORS),
            "minimal_word_depth_profile": counter_dict(Counter(data.depths)),
            "maximum_minimal_word_depth": max(data.depths),
            "state_set_sha256": source.matrix_digest(data.states),
            "pairwise_products_materialized": len(data.states) ** 2,
            "zero_matrix_present": source.ZERO3 in data.index,
        },
        "right_action_synchronization": images,
        "pair_synchronizability": pairs,
        "matrix_rank_vs_finite_image_size": rank_relation,
        "green_structure": green,
        "deep_check": deep,
        "epistemic_bounds": {
            "exact_scope": (
                "All 192 monoid products and their right transformations were exhausted; "
                "pair claims cover all 18,336 unordered state pairs."
            ),
            "reset_claim": (
                "No reset word exists because all 192 distinct product transformations "
                "were enumerated and the minimum image size is 6."
            ),
            "green_convention_warning": (
                "Right multiplication of starting states has image M*p and therefore "
                "measures principal left ideals/Green-L, not principal right ideals/Green-R."
            ),
            "no_generalization": (
                "Rank/image formulas and the equal-column synchronization criterion are "
                "verified properties of this literal finite monoid, not general matrix-monoid theorems."
            ),
        },
    }


def print_human(report: Mapping[str, object]) -> None:
    method = report["method"]
    monoid = report["monoid"]
    sync = report["right_action_synchronization"]
    pairs = report["pair_synchronizability"]
    ranks = report["matrix_rank_vs_finite_image_size"]
    green = report["green_structure"]
    deep = report["deep_check"]
    assert all(isinstance(value, dict) for value in (method, monoid, sync, pairs, ranks, green, deep))

    print("METASPACE SYNCHRONIZER / exact 192-state right action")
    print("convention : word generators append right; delta(x,g)=x*g")
    print("image      : M*p (principal left ideal); Green-R p*M is separate")
    print(
        f"monoid     : states={monoid['state_count']} generators={monoid['generator_count']} "
        f"max-shortest-depth={monoid['maximum_minimal_word_depth']}"
    )

    print("\nIMAGE COMPRESSION")
    print("reachable image sizes:", sync["reachable_image_sizes"])
    print("product profile      :", sync["image_size_profile_over_192_word_products"])
    for event in sync["record_image_size_drops"]:
        print(
            f"  depth {event['depth']}: {event['word']} -> image {event['image_size']} "
            f"(matrix rank {event['matrix_rank']}, {event['state_id']})"
        )
    print(
        f"minimum={sync['minimum_image_size']} via {sync['minimum_word']} at depth "
        f"{sync['minimum_word_length']}; reset-word={sync['reset_word_exists']}"
    )
    print("kernel fibers:")
    for profile in sync["kernel_fiber_profiles"]:
        print(
            f"  image {profile['image_size']}: {profile['element_count']} products, "
            f"fiber-size multiplicity {profile['fiber_size_multiplicity']}"
        )

    print("\nPAIR SYNCHRONIZABILITY")
    print(
        f"pairs={pairs['unordered_pair_count']} sync={pairs['synchronizable_pair_count']} "
        f"never-sync={pairs['nonsynchronizable_pair_count']}"
    )
    print("shortest merge depths:", pairs["shortest_merge_depth_profile"])
    print("criterion:", pairs["pair_synchronization_criterion"])
    print("equal-column subsets:", pairs["equal_column_subset_profile"])

    print("\nMATRIX RANK / FINITE IMAGE")
    for row in ranks["relation"]:
        print(
            f"rank {row['matrix_rank']}: elements={row['element_count']} "
            f"|M*p|={row['right_action_image_sizes_M_times_p']} "
            f"|p*M|={row['principal_right_ideal_sizes_p_times_M']}"
        )

    left = green["principal_left_ideals_green_L"]
    right = green["principal_right_ideals_green_R"]
    two_sided = green["principal_two_sided_ideals_green_J"]
    print("\nGREEN STRUCTURE")
    print(
        f"Green-L: ideals={left['distinct_ideal_count']} sizes={left['distinct_ideal_size_profile']} "
        f"classes={left['green_class_size_profile']}"
    )
    print(
        f"Green-R: ideals={right['distinct_ideal_count']} sizes={right['distinct_ideal_size_profile']} "
        f"classes={right['green_class_size_profile']}"
    )
    print(
        f"Green-J: ideals={two_sided['distinct_ideal_count']} "
        f"sizes={two_sided['distinct_ideal_size_profile']}; D=J verified"
    )
    print("R-poset:", green["computed_incidence_reading"]["green_R"])
    print(
        f"H-classes={green['green_H']['class_count']} "
        f"profile={green['green_H']['class_size_profile']}"
    )
    print("\nDEEP CHECK:", deep)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the exact JSON certificate")
    parser.add_argument(
        "--deep-check",
        action="store_true",
        help="also verify all 192^3 Cayley associativity triples and ideal closure products",
    )
    args = parser.parse_args(argv)
    report = build_report(args.deep_check)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
