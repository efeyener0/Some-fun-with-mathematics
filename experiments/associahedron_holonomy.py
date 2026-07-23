#!/usr/bin/env python3
"""Contextual associator transport on the exact associahedron graph.

For each rotation ``((A B) C) -> (A (B C))`` this probe constructs the exact
linear one-hole context operator C_e: A -> A from the rotated subtree to the
whole-tree root.  It verifies

    root_delta_e = C_e(local_associator_e)

edge by edge, then studies square and pentagon 2-faces.  The root delta is an
exact gradient and therefore flat.  More structure survives below that flat
projection: raw local-frame holonomy, context compensation, and a square
mixed finite difference measuring interaction between commuting rotations.

All arithmetic is exact.  The script reuses ``bracket_garden`` and
``associahedron_weather`` locally and has no third-party dependency.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from itertools import product
from math import comb
from typing import Iterable, Sequence

import associahedron_weather as weather
import bracket_garden as garden


Matrix = tuple[int, int, int, int, int, int, int, int, int]
I3: Matrix = (1, 0, 0, 0, 1, 0, 0, 0, 1)
BASIS = (garden.ONE, garden.H, garden.Q)
FACE_LIMIT = 8
SEARCH_LIMIT = 7


@dataclass(frozen=True, slots=True)
class ConnectionEdge:
    weather: weather.EdgeWeather
    context_matrix: Matrix
    context_rank: int


@dataclass(frozen=True, slots=True)
class FaceHolonomy:
    kind: str
    index: int
    cycle: tuple[int, ...]
    root_circulation: garden.Element
    raw_local_holonomy: garden.Element
    context_compensation: garden.Element
    short_path_root_delta: garden.Element
    long_path_root_delta: garden.Element
    short_path_raw_delta: garden.Element
    long_path_raw_delta: garden.Element
    active_edges: int
    damped_edges: int
    calm_edges: int
    context_rank_profile: tuple[tuple[int, int], ...]
    square_mixed_curvature: garden.Element | None = None
    square_cross_effect_a: garden.Element | None = None
    square_cross_effect_b: garden.Element | None = None


@dataclass(frozen=True, slots=True)
class HolonomyReport:
    atoms: tuple[garden.Atom, ...]
    weather: weather.WeatherReport
    connections: tuple[ConnectionEdge, ...]
    squares: tuple[FaceHolonomy, ...]
    pentagons: tuple[FaceHolonomy, ...]


@dataclass(frozen=True, slots=True)
class SearchChampions:
    square_raw: str
    pentagon_raw: str
    square_curvature: str
    damping: str


def add(*elements: garden.Element) -> garden.Element:
    return garden.Element(
        sum(element.r for element in elements),
        sum(element.h for element in elements),
        sum(element.q for element in elements),
    )


def negate(element: garden.Element) -> garden.Element:
    return garden.Element(-element.r, -element.h, -element.q)


def subtract(left: garden.Element, right: garden.Element) -> garden.Element:
    return add(left, negate(right))


def scale(sign: int, element: garden.Element) -> garden.Element:
    if sign not in {-1, 1}:
        raise ValueError("orientation sign must be +1 or -1")
    return element if sign == 1 else negate(element)


def element_key(element: garden.Element) -> tuple[int, int, int]:
    return (element.r, element.h, element.q)


def element_profile(elements: Iterable[garden.Element]) -> dict[str, int]:
    counter = Counter(str(element) for element in elements)
    return dict(sorted(counter.items()))


def matrix_apply(matrix: Matrix, element: garden.Element) -> garden.Element:
    vector = element_key(element)
    return garden.Element(
        *(sum(matrix[3 * row + column] * vector[column] for column in range(3))
          for row in range(3))
    )


def matrix_subtract(left: Matrix, right: Matrix) -> Matrix:
    return tuple(a - b for a, b in zip(left, right, strict=True))  # type: ignore[return-value]


def determinant(matrix: Matrix) -> int:
    return (
        matrix[0] * (matrix[4] * matrix[8] - matrix[5] * matrix[7])
        - matrix[1] * (matrix[3] * matrix[8] - matrix[5] * matrix[6])
        + matrix[2] * (matrix[3] * matrix[7] - matrix[4] * matrix[6])
    )


def matrix_rank(matrix: Matrix) -> int:
    if determinant(matrix):
        return 3
    for row_a, row_b in ((0, 1), (0, 2), (1, 2)):
        for column_a, column_b in ((0, 1), (0, 2), (1, 2)):
            minor = (
                matrix[3 * row_a + column_a] * matrix[3 * row_b + column_b]
                - matrix[3 * row_a + column_b] * matrix[3 * row_b + column_a]
            )
            if minor:
                return 2
    return 1 if any(matrix) else 0


def evaluate_with_hole(
    tree: garden.Tree,
    path: tuple[str, ...],
    hole: garden.Element,
    values: Sequence[garden.Element],
) -> garden.Element:
    """Evaluate a tree after replacing exactly one path-selected subtree."""

    if not path:
        return hole
    if not isinstance(tree, garden.Branch):
        raise AssertionError("context path crossed a leaf")
    head, remainder = path[0], path[1:]
    if head == "L":
        return evaluate_with_hole(tree.left, remainder, hole, values) * garden.evaluate(
            tree.right, values
        )
    if head == "R":
        return garden.evaluate(tree.left, values) * evaluate_with_hole(
            tree.right, remainder, hole, values
        )
    raise AssertionError(f"invalid context path step {head!r}")


def context_matrix(
    tree: garden.Tree,
    path: tuple[str, ...],
    values: Sequence[garden.Element],
) -> Matrix:
    columns = tuple(evaluate_with_hole(tree, path, basis, values) for basis in BASIS)
    return tuple(
        element_key(columns[column])[row]
        for row in range(3)
        for column in range(3)
    )  # type: ignore[return-value]


@lru_cache(maxsize=None)
def tree_leaf_indices(tree: garden.Tree) -> tuple[int, ...]:
    if isinstance(tree, garden.Leaf):
        return (tree.index,)
    return tree_leaf_indices(tree.left) + tree_leaf_indices(tree.right)


def rotation_signature(rotation: weather.Rotation) -> tuple[tuple[int, int], ...]:
    signature = []
    for subtree in (rotation.a, rotation.b, rotation.c):
        leaves = tree_leaf_indices(subtree)
        signature.append((min(leaves), max(leaves)))
    return tuple(signature)


def expected_pentagons(leaves: int) -> int:
    return comb(2 * leaves - 4, leaves - 4) if leaves >= 4 else 0


def expected_squares(leaves: int) -> int:
    if leaves < 5:
        return 0
    return (leaves - 4) * expected_pentagons(leaves) // 2


@lru_cache(maxsize=None)
def induced_cycles(leaves: int, length: int) -> tuple[tuple[int, ...], ...]:
    if length not in {4, 5}:
        raise ValueError("only square and pentagon cycles are supported")
    graph = weather.rotation_graph(leaves)
    adjacency = tuple(frozenset(neighbors) for neighbors in graph.adjacency)
    cycles: set[tuple[int, ...]] = set()

    def visit(start: int, path: tuple[int, ...]) -> None:
        current = path[-1]
        if len(path) == length:
            if start not in adjacency[current]:
                return
            cycle = path if path[1] < path[-1] else (path[0],) + tuple(reversed(path[1:]))
            for left in range(length):
                for right in range(left + 1, length):
                    consecutive = right == left + 1 or (left == 0 and right == length - 1)
                    if not consecutive and cycle[right] in adjacency[cycle[left]]:
                        return
            cycles.add(cycle)
            return
        for neighbor in adjacency[current]:
            if neighbor <= start or neighbor in path:
                continue
            visit(start, path + (neighbor,))

    for start in range(len(graph.trees)):
        visit(start, (start,))
    result = tuple(sorted(cycles))
    expected = expected_squares(leaves) if length == 4 else expected_pentagons(leaves)
    if len(result) != expected:
        raise AssertionError(
            f"n={leaves} length-{length} faces: found {len(result)}, expected {expected}"
        )
    return result


def build_connections(report: weather.WeatherReport) -> tuple[ConnectionEdge, ...]:
    graph = report.graph
    values = tuple(atom.value for atom in report.atoms)
    connections: list[ConnectionEdge] = []
    for edge in report.edges:
        rotation = edge.rotation
        source_tree = graph.trees[rotation.source]
        target_tree = graph.trees[rotation.target]
        source_context = context_matrix(source_tree, rotation.path, values)
        target_context = context_matrix(target_tree, rotation.path, values)
        if source_context != target_context:
            raise AssertionError("rotation changed its outer one-hole context")
        transported = matrix_apply(source_context, edge.local_associator)
        if transported != edge.root_delta:
            raise AssertionError("root delta does not factor through the context operator")
        rank = matrix_rank(source_context)
        if edge.state == "DAMPED":
            if edge.local_associator == garden.ZERO or transported != garden.ZERO:
                raise AssertionError("damped edge does not carry a kernel residual")
            if rank == 3:
                raise AssertionError("an invertible context damped a non-zero residual")
        connections.append(ConnectionEdge(edge, source_context, rank))
    return tuple(connections)


def connection_lookup(
    connections: Sequence[ConnectionEdge],
) -> dict[tuple[int, int], ConnectionEdge]:
    return {
        tuple(sorted((edge.weather.rotation.source, edge.weather.rotation.target))): edge
        for edge in connections
    }


def oriented_connection(
    lookup: dict[tuple[int, int], ConnectionEdge],
    start: int,
    end: int,
) -> tuple[ConnectionEdge, int]:
    edge = lookup[tuple(sorted((start, end)))]
    rotation = edge.weather.rotation
    sign = 1 if (rotation.source, rotation.target) == (start, end) else -1
    return edge, sign


def path_sum(
    lookup: dict[tuple[int, int], ConnectionEdge],
    path: Sequence[int],
    field: str,
) -> garden.Element:
    total = garden.ZERO
    for start, end in zip(path, path[1:]):
        edge, sign = oriented_connection(lookup, start, end)
        value = (
            edge.weather.root_delta
            if field == "root"
            else edge.weather.local_associator
        )
        total = add(total, scale(sign, value))
    return total


def analyze_face(
    kind: str,
    index: int,
    cycle: tuple[int, ...],
    report: weather.WeatherReport,
    lookup: dict[tuple[int, int], ConnectionEdge],
) -> FaceHolonomy:
    root_circulation = garden.ZERO
    raw_holonomy = garden.ZERO
    compensation = garden.ZERO
    states = Counter()
    ranks = Counter()

    for offset, start in enumerate(cycle):
        end = cycle[(offset + 1) % len(cycle)]
        edge, sign = oriented_connection(lookup, start, end)
        root_increment = scale(sign, edge.weather.root_delta)
        local_increment = scale(sign, edge.weather.local_associator)
        correction = scale(
            sign,
            matrix_apply(
                matrix_subtract(edge.context_matrix, I3),
                edge.weather.local_associator,
            ),
        )
        if add(local_increment, correction) != root_increment:
            raise AssertionError("edge context decomposition failed")
        root_circulation = add(root_circulation, root_increment)
        raw_holonomy = add(raw_holonomy, local_increment)
        compensation = add(compensation, correction)
        states[edge.weather.state] += 1
        ranks[edge.context_rank] += 1

    if root_circulation != garden.ZERO:
        raise AssertionError("root delta 1-form has non-zero face circulation")
    if add(raw_holonomy, compensation) != garden.ZERO:
        raise AssertionError("context compensation does not close the raw holonomy")

    short_path = (cycle[0], cycle[1], cycle[2])
    if kind == "square":
        long_path = (cycle[0], cycle[3], cycle[2])
    else:
        long_path = (cycle[0], cycle[4], cycle[3], cycle[2])
    short_root = path_sum(lookup, short_path, "root")
    long_root = path_sum(lookup, long_path, "root")
    short_raw = path_sum(lookup, short_path, "local")
    long_raw = path_sum(lookup, long_path, "local")
    if short_root != long_root:
        raise AssertionError("two face paths disagree after root transport")
    if subtract(short_raw, long_raw) != raw_holonomy:
        raise AssertionError("raw path mismatch disagrees with face holonomy")

    mixed: garden.Element | None = None
    cross_a: garden.Element | None = None
    cross_b: garden.Element | None = None
    if kind == "square":
        signatures = []
        for offset, start in enumerate(cycle):
            end = cycle[(offset + 1) % 4]
            edge, _ = oriented_connection(lookup, start, end)
            signatures.append(rotation_signature(edge.weather.rotation))
        if not (
            signatures[0] == signatures[2]
            and signatures[1] == signatures[3]
            and signatures[0] != signatures[1]
        ):
            raise AssertionError("square does not alternate two commuting rotations")

        potential = report.phenotypes
        mixed = add(
            potential[cycle[0]],
            negate(potential[cycle[1]]),
            potential[cycle[2]],
            negate(potential[cycle[3]]),
        )
        effect_a_before = subtract(potential[cycle[0]], potential[cycle[1]])
        effect_a_after = subtract(potential[cycle[3]], potential[cycle[2]])
        effect_b_before = subtract(potential[cycle[0]], potential[cycle[3]])
        effect_b_after = subtract(potential[cycle[1]], potential[cycle[2]])
        cross_a = subtract(effect_a_after, effect_a_before)
        cross_b = subtract(effect_b_after, effect_b_before)
        if cross_a != cross_b or cross_a != negate(mixed):
            raise AssertionError("square mixed cross-effects do not agree")
    else:
        signatures = []
        for offset, start in enumerate(cycle):
            end = cycle[(offset + 1) % 5]
            edge, _ = oriented_connection(lookup, start, end)
            signatures.append(rotation_signature(edge.weather.rotation))
        if len(set(signatures)) != 5:
            raise AssertionError("pentagon does not contain five distinct rotations")

    return FaceHolonomy(
        kind=kind,
        index=index,
        cycle=cycle,
        root_circulation=root_circulation,
        raw_local_holonomy=raw_holonomy,
        context_compensation=compensation,
        short_path_root_delta=short_root,
        long_path_root_delta=long_root,
        short_path_raw_delta=short_raw,
        long_path_raw_delta=long_raw,
        active_edges=states["ACTIVE"],
        damped_edges=states["DAMPED"],
        calm_edges=states["CALM"],
        context_rank_profile=tuple(sorted(ranks.items())),
        square_mixed_curvature=mixed,
        square_cross_effect_a=cross_a,
        square_cross_effect_b=cross_b,
    )


def analyze_word(word: str) -> HolonomyReport:
    atoms = weather.parse_hq_word(word)
    weather_report = weather.analyze_weather(atoms)
    connections = build_connections(weather_report)
    lookup = connection_lookup(connections)
    leaves = len(atoms)
    squares = tuple(
        analyze_face("square", index, cycle, weather_report, lookup)
        for index, cycle in enumerate(induced_cycles(leaves, 4))
    )
    pentagons = tuple(
        analyze_face("pentagon", index, cycle, weather_report, lookup)
        for index, cycle in enumerate(induced_cycles(leaves, 5))
    )
    return HolonomyReport(atoms, weather_report, connections, squares, pentagons)


def face_summary(faces: Sequence[FaceHolonomy]) -> dict[str, object]:
    raw_nonzero = sum(face.raw_local_holonomy != garden.ZERO for face in faces)
    summary: dict[str, object] = {
        "face_count": len(faces),
        "root_flat_face_count": sum(
            face.root_circulation == garden.ZERO for face in faces
        ),
        "nonzero_raw_local_holonomy_count": raw_nonzero,
        "raw_local_holonomy_profile": element_profile(
            face.raw_local_holonomy for face in faces
        ),
        "active_edges_per_face_profile": {
            str(key): value
            for key, value in sorted(Counter(face.active_edges for face in faces).items())
        },
    }
    if faces and faces[0].kind == "square":
        curvatures = tuple(face.square_mixed_curvature for face in faces)
        assert all(curvature is not None for curvature in curvatures)
        summary["nonzero_square_mixed_curvature_count"] = sum(
            curvature != garden.ZERO for curvature in curvatures
        )
        summary["square_mixed_curvature_profile"] = element_profile(
            curvature for curvature in curvatures if curvature is not None
        )
    return summary


def connection_summary(report: HolonomyReport) -> dict[str, object]:
    return {
        "edge_count": len(report.connections),
        "factorization_verified_count": len(report.connections),
        "context_rank_profile": {
            str(key): value
            for key, value in sorted(
                Counter(edge.context_rank for edge in report.connections).items()
            )
        },
        "weather_by_context_rank": {
            f"{state}/rank-{rank}": count
            for (state, rank), count in sorted(
                Counter(
                    (edge.weather.state, edge.context_rank)
                    for edge in report.connections
                ).items()
            )
        },
    }


def face_id(face: FaceHolonomy, leaves: int) -> str:
    prefix = "Q" if face.kind == "square" else "P"
    return f"{prefix}{leaves}:{face.index:03d}"


def tree_ids(report: HolonomyReport, cycle: Sequence[int]) -> str:
    total = len(report.weather.graph.trees)
    leaves = len(report.atoms)
    return " -> ".join(garden.tree_id(leaves, vertex, total) for vertex in cycle)


def print_face(report: HolonomyReport, face: FaceHolonomy) -> None:
    print(f"{face_id(face, len(report.atoms))} {tree_ids(report, face.cycle)}")
    print(
        f"  root circulation={face.root_circulation}; raw local holonomy="
        f"{face.raw_local_holonomy}; context compensation={face.context_compensation}"
    )
    print(
        f"  two paths root={face.short_path_root_delta}={face.long_path_root_delta}; "
        f"raw={face.short_path_raw_delta} vs {face.long_path_raw_delta}"
    )
    if face.kind == "square":
        print(
            f"  mixed curvature={face.square_mixed_curvature}; "
            f"cross effects={face.square_cross_effect_a}={face.square_cross_effect_b}"
        )


def print_report(report: HolonomyReport, face_limit: int) -> None:
    word = garden.word_label(report.atoms, compact=True)
    connection = connection_summary(report)
    square = face_summary(report.squares)
    pentagon = face_summary(report.pentagons)
    print("ASSOCIAHEDRON HOLONOMY / contextual associator transport")
    print(f"word       : {word}")
    print(
        f"graph      : vertices={len(report.weather.graph.trees)} "
        f"edges={len(report.weather.graph.rotations)}"
    )
    print(f"connection : C_e(local associator)=root delta on {connection['edge_count']} edges")
    print("context ranks:", connection["context_rank_profile"])
    print("weather/rank:", connection["weather_by_context_rank"])
    print(
        f"squares    : {square['face_count']} faces; raw-holonomy nonzero="
        f"{square['nonzero_raw_local_holonomy_count']}; mixed-curvature nonzero="
        f"{square.get('nonzero_square_mixed_curvature_count', 0)}"
    )
    print(
        f"pentagons  : {pentagon['face_count']} faces; raw-holonomy nonzero="
        f"{pentagon['nonzero_raw_local_holonomy_count']}"
    )
    print("root 1-form: exact gradient; every enumerated face circulation is zero")

    for label, faces in (("SQUARE SAMPLES", report.squares), ("PENTAGON SAMPLES", report.pentagons)):
        if not faces:
            continue
        print(f"\n{label}")
        visible = faces if face_limit == 0 else faces[:face_limit]
        for face in visible:
            print_face(report, face)
        hidden = len(faces) - len(visible)
        if hidden:
            print(f"... {hidden} more exact face records")


def print_topology(max_leaves: int) -> None:
    if not 3 <= max_leaves <= FACE_LIMIT:
        raise ValueError(f"--max-leaves must be between 3 and {FACE_LIMIT}")
    print("ASSOCIAHEDRON 2-CELLS / induced face ledger")
    print(" n  vertices  edges  squares  expected  pentagons  expected")
    print("--  --------  -----  -------  --------  ---------  --------")
    for leaves in range(3, max_leaves + 1):
        graph = weather.rotation_graph(leaves)
        squares = len(induced_cycles(leaves, 4))
        pentagons = len(induced_cycles(leaves, 5))
        print(
            f"{leaves:>2}  {len(graph.trees):>8}  {len(graph.rotations):>5}  "
            f"{squares:>7}  {expected_squares(leaves):>8}  "
            f"{pentagons:>9}  {expected_pentagons(leaves):>8}"
        )


def light_face_metrics(word: str) -> tuple[int, int, int, int]:
    weather_report = weather.report_for_symbols(word)
    lookup = {
        tuple(sorted((edge.rotation.source, edge.rotation.target))): edge
        for edge in weather_report.edges
    }

    def raw_holonomy(cycle: tuple[int, ...]) -> garden.Element:
        total = garden.ZERO
        for offset, start in enumerate(cycle):
            end = cycle[(offset + 1) % len(cycle)]
            edge = lookup[tuple(sorted((start, end)))]
            sign = 1 if (edge.rotation.source, edge.rotation.target) == (start, end) else -1
            total = add(total, scale(sign, edge.local_associator))
        return total

    square_raw = sum(
        raw_holonomy(cycle) != garden.ZERO
        for cycle in induced_cycles(len(word), 4)
    )
    pentagon_raw = sum(
        raw_holonomy(cycle) != garden.ZERO
        for cycle in induced_cycles(len(word), 5)
    )
    square_curvature = 0
    for cycle in induced_cycles(len(word), 4):
        potential = weather_report.phenotypes
        mixed = add(
            potential[cycle[0]],
            negate(potential[cycle[1]]),
            potential[cycle[2]],
            negate(potential[cycle[3]]),
        )
        square_curvature += mixed != garden.ZERO
    return square_raw, pentagon_raw, square_curvature, weather_report.damped_count


@lru_cache(maxsize=None)
def champion_search(leaves: int) -> SearchChampions:
    if not 4 <= leaves <= SEARCH_LIMIT:
        raise ValueError(f"champion search is bounded at {SEARCH_LIMIT} leaves")
    best: list[tuple[tuple[int, ...], str] | None] = [None, None, None, None]
    for symbols in product(("h", "q"), repeat=leaves):
        word = "".join(symbols)
        metrics = light_face_metrics(word)
        for objective in range(4):
            score = (metrics[objective],) + metrics[:objective] + metrics[objective + 1 :]
            if best[objective] is None or score > best[objective][0]:
                best[objective] = (score, word)
    if any(record is None for record in best):
        raise AssertionError("face champion search produced no word")
    return SearchChampions(
        square_raw=best[0][1],  # type: ignore[index]
        pentagon_raw=best[1][1],  # type: ignore[index]
        square_curvature=best[2][1],  # type: ignore[index]
        damping=best[3][1],  # type: ignore[index]
    )


def print_expedition() -> None:
    print("CONTEXTUAL HOLONOMY EXPEDITION")
    print("Named exact fronts:\n")
    print(" word     edges  context ranks       square raw/K   pentagon raw  A/D/C")
    print("--------  -----  ------------------  -------------  ------------  -----------")
    for word in ("hhhh", "hhqqh", "hhqqhq", "hhhhhhh"):
        report = analyze_word(word)
        ranks = Counter(edge.context_rank for edge in report.connections)
        square = face_summary(report.squares)
        pentagon = face_summary(report.pentagons)
        square_pair = (
            f"{square['nonzero_raw_local_holonomy_count']}/"
            f"{square.get('nonzero_square_mixed_curvature_count', 0)}"
        )
        pentagon_pair = (
            f"{pentagon['nonzero_raw_local_holonomy_count']}/"
            f"{pentagon['face_count']}"
        )
        print(
            f"{word:<8}  {len(report.connections):>5}  {str(dict(sorted(ranks.items()))):<18}  "
            f"{square_pair:<13}  {pentagon_pair:<12}  "
            f"{report.weather.active_count}/{report.weather.damped_count}/{report.weather.calm_count}"
        )

    print("\nExhaustive h/q champions (primary metric first; h<q breaks full ties):")
    print(" n  square-raw  pentagon-raw  square-curvature  damping")
    print("--  ----------  ------------  ----------------  -------")
    for leaves in range(4, SEARCH_LIMIT + 1):
        champion = champion_search(leaves)
        print(
            f"{leaves:>2}  {champion.square_raw:<10}  {champion.pentagon_raw:<12}  "
            f"{champion.square_curvature:<16}  {champion.damping}"
        )


def associator(
    left: garden.Element,
    middle: garden.Element,
    right: garden.Element,
) -> garden.Element:
    return subtract((left * middle) * right, left * (middle * right))


def pentagon_identity_residual(
    a: garden.Element,
    b: garden.Element,
    c: garden.Element,
    d: garden.Element,
) -> garden.Element:
    three_step = add(
        associator(a, b, c) * d,
        associator(a, b * c, d),
        a * associator(b, c, d),
    )
    two_step = add(
        associator(a * b, c, d),
        associator(a, b, c * d),
    )
    return subtract(three_step, two_step)


def run_self_tests(deep: bool) -> None:
    topology_max = 8 if deep else 7
    expected_square_counts = (0, 0, 3, 28, 180, 990)
    expected_pentagon_counts = (0, 1, 6, 28, 120, 495)
    for offset, leaves in enumerate(range(3, topology_max + 1)):
        assert len(induced_cycles(leaves, 4)) == expected_square_counts[offset]
        assert len(induced_cycles(leaves, 5)) == expected_pentagon_counts[offset]

    basis_checks = 0
    for a, b, c, d in product(BASIS, repeat=4):
        basis_checks += 1
        assert pentagon_identity_residual(a, b, c, d) == garden.ZERO
    assert basis_checks == 81

    named_reports = {
        word: analyze_word(word)
        for word in ("hhhh", "hhqqh", "hhqqhq", "hhhhhhh")
    }
    named_edge_checks = sum(
        len(report.connections) for report in named_reports.values()
    )
    assert named_edge_checks == 440

    witness = named_reports["hhqqhq"]
    assert Counter(edge.context_rank for edge in witness.connections) == Counter(
        {3: 47, 2: 34, 1: 3}
    )
    assert len(witness.squares) == 28 and len(witness.pentagons) == 28
    assert sum(face.raw_local_holonomy != garden.ZERO for face in witness.squares) == 14
    assert sum(
        face.square_mixed_curvature != garden.ZERO for face in witness.squares
    ) == 15
    assert sum(
        face.raw_local_holonomy != garden.ZERO for face in witness.pentagons
    ) == 17

    pure_h = named_reports["hhhhhhh"]
    assert Counter(edge.context_rank for edge in pure_h.connections) == Counter(
        {3: 258, 2: 68, 1: 4}
    )
    assert sum(face.raw_local_holonomy != garden.ZERO for face in pure_h.squares) == 105
    assert sum(
        face.square_mixed_curvature != garden.ZERO for face in pure_h.squares
    ) == 117
    assert sum(
        face.raw_local_holonomy != garden.ZERO for face in pure_h.pentagons
    ) == 90

    full_word_checks = 0
    if deep:
        for leaves in range(1, SEARCH_LIMIT + 1):
            for symbols in product(("h", "q"), repeat=leaves):
                analyze_word("".join(symbols))
                full_word_checks += 1
        assert full_word_checks == sum(2**leaves for leaves in range(1, 8)) == 254

        expected = {
            4: SearchChampions("hqqq", "hqqq", "hqqq", "hqqq"),
            5: SearchChampions("hhqqh", "qhhhh", "hhqqh", "qhhhq"),
            6: SearchChampions("hhhqhh", "qhhhhh", "hhhqhh", "qhqqhq"),
            7: SearchChampions("hhhhhhh", "qhhhhhh", "hhhhhhh", "qhqqqhq"),
        }
        for leaves, champions in expected.items():
            assert champion_search(leaves) == champions

    print("SELF-TEST PASS")
    print(f"2-cell counts      : exact through n={topology_max}")
    print("pentagon identity  : 81 tensor-basis quadruples")
    print(f"edge connection    : {named_edge_checks} named-front edges")
    print("hhqqhq              : square raw=14, square K=15, pentagon raw=17")
    print("h^7                 : square raw=105, square K=117, pentagon raw=90")
    print(
        "full word reports   : "
        f"{'254 exhaustive words through n=7' if deep else 'use --deep'}"
    )
    print(f"word champions      : {'exhaustive through n=7' if deep else 'use --deep'}")


def non_negative(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Exact contextual associator transport on associahedron 2-faces.",
        epilog="With no command, the deterministic expedition runs.",
    )
    subparsers = parser.add_subparsers(dest="command")

    analyze = subparsers.add_parser("analyze", help="analyze one positive h/q word")
    analyze.add_argument("word")
    analyze.add_argument(
        "--face-limit",
        type=non_negative,
        default=3,
        help="sample faces printed per kind; 0 prints all",
    )

    topology = subparsers.add_parser("topology", help="enumerate square/pentagon 2-cells")
    topology.add_argument("--max-leaves", type=int, default=8)

    subparsers.add_parser("expedition", help="run named fronts and exhaustive champions")

    test = subparsers.add_parser("test", help="run exact self-tests")
    test.add_argument("--deep", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "analyze":
            print_report(analyze_word(args.word), args.face_limit)
        elif args.command == "topology":
            print_topology(args.max_leaves)
        elif args.command == "test":
            run_self_tests(args.deep)
        else:
            print_expedition()
    except ValueError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
