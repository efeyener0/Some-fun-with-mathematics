#!/usr/bin/env python3
"""Exact weather on the associahedron graph of bracket histories.

Vertices are the full binary trees supplied by ``bracket_garden``.  An
undirected edge is exactly one local rotation

    ((A*B)*C)  <->  (A*(B*C)).

For an h/q leaf word, every vertex receives its exact algebra phenotype.  A
rotation receives both its local associator and the resulting whole-tree
delta.  Those two quantities are deliberately not conflated: an outer
context may annihilate a non-zero local associator.

Standard library only; all arithmetic is exact integer arithmetic.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from functools import lru_cache
from itertools import product
from typing import Iterator, Sequence

import bracket_garden as garden


TOPOLOGY_LIMIT = 8
SEARCH_LIMIT = 7
WEATHER_LIMIT = 9


@dataclass(frozen=True, slots=True)
class Rotation:
    """One canonically oriented associahedron edge.

    ``source`` contains the local form ``((A B) C)`` and ``target`` contains
    ``(A (B C))``.  The graph itself is undirected; the orientation exists so
    every delta has one reproducible sign convention.
    """

    index: int
    source: int
    target: int
    path: tuple[str, ...]
    a: garden.Tree
    b: garden.Tree
    c: garden.Tree


@dataclass(frozen=True, slots=True)
class RotationGraph:
    leaves: int
    trees: tuple[garden.Tree, ...]
    rotations: tuple[Rotation, ...]
    adjacency: tuple[tuple[int, ...], ...]

    @property
    def connected(self) -> bool:
        return len(reachable_vertices(self.adjacency, 0)) == len(self.trees)


@dataclass(frozen=True, slots=True)
class EdgeWeather:
    rotation: Rotation
    source_phenotype: garden.Element
    target_phenotype: garden.Element
    a_value: garden.Element
    b_value: garden.Element
    c_value: garden.Element
    local_associator: garden.Element
    root_delta: garden.Element
    state: str


@dataclass(frozen=True, slots=True)
class PhenotypeRegion:
    phenotype: garden.Element
    vertices: tuple[int, ...]
    induced_edges: int
    components: tuple[tuple[int, ...], ...]


@dataclass(frozen=True, slots=True)
class WeatherReport:
    atoms: tuple[garden.Atom, ...]
    graph: RotationGraph
    phenotypes: tuple[garden.Element, ...]
    edges: tuple[EdgeWeather, ...]
    regions: tuple[PhenotypeRegion, ...]

    @property
    def active_count(self) -> int:
        return sum(edge.state == "ACTIVE" for edge in self.edges)

    @property
    def damped_count(self) -> int:
        return sum(edge.state == "DAMPED" for edge in self.edges)

    @property
    def calm_count(self) -> int:
        return sum(edge.state == "CALM" for edge in self.edges)

    @property
    def silent_count(self) -> int:
        return self.damped_count + self.calm_count

    @property
    def phenotype_count(self) -> int:
        return len(self.regions)

    @property
    def component_count(self) -> int:
        return sum(len(region.components) for region in self.regions)

    @property
    def component_excess(self) -> int:
        """Extra same-phenotype islands beyond one island per phenotype."""

        return self.component_count - self.phenotype_count


@dataclass(frozen=True, slots=True)
class Champions:
    storm: WeatherReport
    damping: WeatherReport
    fracture: WeatherReport


def subtract(left: garden.Element, right: garden.Element) -> garden.Element:
    return garden.Element(
        left.r - right.r,
        left.h - right.h,
        left.q - right.q,
    )


def expected_edge_count(leaves: int) -> int:
    if leaves < 1:
        raise ValueError("leaf count must be positive")
    if leaves < 3:
        return 0
    return garden.catalan(leaves - 1) * (leaves - 2) // 2


def expected_degree(leaves: int) -> int:
    return max(leaves - 2, 0)


def rotation_id(leaves: int, index: int, total: int) -> str:
    width = max(2, len(str(max(total - 1, 0))))
    return f"E{leaves}:{index:0{width}d}"


def path_label(path: Sequence[str]) -> str:
    return "root" + "".join(f".{step}" for step in path)


def _replace_subtree(
    tree: garden.Tree,
    path: tuple[str, ...],
    replacement: garden.Tree,
) -> garden.Tree:
    if not path:
        return replacement
    if not isinstance(tree, garden.Branch):
        raise AssertionError("rotation path crossed a leaf")
    head, *tail = path
    remainder = tuple(tail)
    if head == "L":
        return garden.Branch(
            _replace_subtree(tree.left, remainder, replacement),
            tree.right,
        )
    if head == "R":
        return garden.Branch(
            tree.left,
            _replace_subtree(tree.right, remainder, replacement),
        )
    raise AssertionError(f"invalid tree path step: {head!r}")


def _forward_rotation_sites(
    root: garden.Tree,
    node: garden.Tree | None = None,
    path: tuple[str, ...] = (),
) -> Iterator[tuple[tuple[str, ...], garden.Tree, garden.Tree, garden.Tree, garden.Tree]]:
    """Yield every local ``((A B) C) -> (A (B C))`` rotation once."""

    node = root if node is None else node
    if not isinstance(node, garden.Branch):
        return

    if isinstance(node.left, garden.Branch):
        a = node.left.left
        b = node.left.right
        c = node.right
        rotated = garden.Branch(a, garden.Branch(b, c))
        yield path, a, b, c, _replace_subtree(root, path, rotated)

    yield from _forward_rotation_sites(root, node.left, path + ("L",))
    yield from _forward_rotation_sites(root, node.right, path + ("R",))


def reachable_vertices(
    adjacency: Sequence[Sequence[int]],
    start: int,
    allowed: frozenset[int] | None = None,
) -> frozenset[int]:
    if not 0 <= start < len(adjacency):
        raise ValueError("start vertex is outside the graph")
    permitted = frozenset(range(len(adjacency))) if allowed is None else allowed
    if start not in permitted:
        return frozenset()
    reached = {start}
    stack = [start]
    while stack:
        vertex = stack.pop()
        for neighbor in adjacency[vertex]:
            if neighbor in permitted and neighbor not in reached:
                reached.add(neighbor)
                stack.append(neighbor)
    return frozenset(reached)


@lru_cache(maxsize=None)
def rotation_graph(leaves: int) -> RotationGraph:
    if not 1 <= leaves <= WEATHER_LIMIT:
        raise ValueError(f"rotation graphs are bounded at {WEATHER_LIMIT} leaves")

    trees = garden.full_binary_trees(leaves)
    tree_indices = {tree: index for index, tree in enumerate(trees)}
    rotations: list[Rotation] = []
    undirected_pairs: set[tuple[int, int]] = set()

    for source_index, source_tree in enumerate(trees):
        for path, a, b, c, target_tree in _forward_rotation_sites(source_tree):
            try:
                target_index = tree_indices[target_tree]
            except KeyError as error:
                raise AssertionError("rotation escaped the Catalan tree ledger") from error
            pair = tuple(sorted((source_index, target_index)))
            if pair in undirected_pairs:
                raise AssertionError(f"duplicate rotation edge: {pair}")
            undirected_pairs.add(pair)
            rotations.append(
                Rotation(
                    index=len(rotations),
                    source=source_index,
                    target=target_index,
                    path=path,
                    a=a,
                    b=b,
                    c=c,
                )
            )

    adjacency_sets: list[set[int]] = [set() for _ in trees]
    for rotation in rotations:
        adjacency_sets[rotation.source].add(rotation.target)
        adjacency_sets[rotation.target].add(rotation.source)
    adjacency = tuple(tuple(sorted(neighbors)) for neighbors in adjacency_sets)

    expected_edges = expected_edge_count(leaves)
    if len(rotations) != expected_edges:
        raise AssertionError(
            f"rotation graph made {len(rotations)} edges, expected {expected_edges}"
        )
    expected_vertex_degree = expected_degree(leaves)
    degrees = {len(neighbors) for neighbors in adjacency}
    if degrees != {expected_vertex_degree}:
        raise AssertionError(
            f"unexpected degree set {sorted(degrees)}, expected {expected_vertex_degree}"
        )

    graph = RotationGraph(leaves, trees, tuple(rotations), adjacency)
    if not graph.connected:
        raise AssertionError("rotation graph is disconnected")
    return graph


def parse_hq_word(source: str) -> tuple[garden.Atom, ...]:
    atoms = garden.parse_word(source)
    invalid = [atom.glyph for atom in atoms if atom.glyph not in {"h", "q"}]
    if invalid:
        raise ValueError(
            "associahedron weather accepts positive h/q leaves only; "
            f"invalid atom(s): {', '.join(invalid)}"
        )
    if len(atoms) > WEATHER_LIMIT:
        raise ValueError(f"weather words are bounded at {WEATHER_LIMIT} leaves")
    return atoms


def _induced_components(
    graph: RotationGraph,
    vertices: tuple[int, ...],
) -> tuple[tuple[int, ...], ...]:
    allowed = frozenset(vertices)
    remaining = set(vertices)
    components: list[tuple[int, ...]] = []
    while remaining:
        start = min(remaining)
        component = reachable_vertices(graph.adjacency, start, allowed)
        ordered = tuple(sorted(component))
        components.append(ordered)
        remaining.difference_update(component)
    components.sort(key=lambda component: (-len(component), component[0]))
    return tuple(components)


def analyze_weather(atoms: tuple[garden.Atom, ...]) -> WeatherReport:
    graph = rotation_graph(len(atoms))
    values = tuple(atom.value for atom in atoms)
    phenotypes = tuple(garden.evaluate(tree, values) for tree in graph.trees)

    edge_weather: list[EdgeWeather] = []
    for rotation in graph.rotations:
        a_value = garden.evaluate(rotation.a, values)
        b_value = garden.evaluate(rotation.b, values)
        c_value = garden.evaluate(rotation.c, values)
        local_left = (a_value * b_value) * c_value
        local_right = a_value * (b_value * c_value)
        local_associator = subtract(local_left, local_right)

        source_phenotype = phenotypes[rotation.source]
        target_phenotype = phenotypes[rotation.target]
        root_delta = subtract(source_phenotype, target_phenotype)
        if root_delta != garden.ZERO:
            state = "ACTIVE"
        elif local_associator != garden.ZERO:
            state = "DAMPED"
        else:
            state = "CALM"
        if local_associator == garden.ZERO and root_delta != garden.ZERO:
            raise AssertionError("a zero local associator changed the root")

        edge_weather.append(
            EdgeWeather(
                rotation=rotation,
                source_phenotype=source_phenotype,
                target_phenotype=target_phenotype,
                a_value=a_value,
                b_value=b_value,
                c_value=c_value,
                local_associator=local_associator,
                root_delta=root_delta,
                state=state,
            )
        )

    mutable_groups: dict[garden.Element, list[int]] = {}
    for index, phenotype in enumerate(phenotypes):
        mutable_groups.setdefault(phenotype, []).append(index)

    regions: list[PhenotypeRegion] = []
    for phenotype, mutable_vertices in mutable_groups.items():
        vertices = tuple(mutable_vertices)
        vertex_set = frozenset(vertices)
        induced_edges = sum(
            rotation.source in vertex_set and rotation.target in vertex_set
            for rotation in graph.rotations
        )
        regions.append(
            PhenotypeRegion(
                phenotype=phenotype,
                vertices=vertices,
                induced_edges=induced_edges,
                components=_induced_components(graph, vertices),
            )
        )

    report = WeatherReport(atoms, graph, phenotypes, tuple(edge_weather), tuple(regions))
    if report.active_count + report.damped_count + report.calm_count != len(graph.rotations):
        raise AssertionError("weather states do not partition the edge ledger")
    if sum(region.induced_edges for region in report.regions) != report.silent_count:
        raise AssertionError("silent rotations disagree with phenotype-induced edges")
    return report


def report_for_symbols(symbols: Sequence[str] | str) -> WeatherReport:
    return analyze_weather(garden.atoms_from_symbols(symbols))


def tree_label(report: WeatherReport, index: int) -> str:
    return garden.tree_id(report.graph.leaves, index, len(report.graph.trees))


def edge_label(report: WeatherReport, index: int) -> str:
    return rotation_id(report.graph.leaves, index, len(report.graph.rotations))


def print_region(report: WeatherReport, region: PhenotypeRegion, limit: int) -> None:
    sizes = "+".join(str(len(component)) for component in region.components)
    representatives = ",".join(tree_label(report, component[0]) for component in region.components)
    print(
        f"phenotype {region.phenotype}: vertices={len(region.vertices)} "
        f"induced_edges={region.induced_edges} components={len(region.components)} "
        f"sizes={sizes} reps={representatives}"
    )
    visible = region.vertices if limit == 0 else region.vertices[:limit]
    for index in visible:
        tree = report.graph.trees[index]
        expression = garden.render_tree(tree, report.atoms)
        print(f"  {tree_label(report, index)} shape={garden.shape_code(tree)} {expression}")
    hidden = len(region.vertices) - len(visible)
    if hidden:
        print(f"  ... {hidden} more explicit vertex ID(s); use --limit 0 for all")


def print_edge_weather(report: WeatherReport, edge: EdgeWeather) -> None:
    rotation = edge.rotation
    source_id = tree_label(report, rotation.source)
    target_id = tree_label(report, rotation.target)
    source_tree = report.graph.trees[rotation.source]
    target_tree = report.graph.trees[rotation.target]
    print(
        f"{edge_label(report, rotation.index)} [{edge.state}] "
        f"{source_id} -> {target_id} at {path_label(rotation.path)}"
    )
    print(
        f"  rotate : {garden.render_tree(source_tree, report.atoms)} "
        f"=> {garden.render_tree(target_tree, report.atoms)}"
    )
    print(
        f"  local  : [{edge.a_value},{edge.b_value},{edge.c_value}] "
        f"= ((A*B)*C)-(A*(B*C)) = {edge.local_associator}"
    )
    print(
        f"  root   : {edge.source_phenotype} -> {edge.target_phenotype}; "
        f"delta(source-target)={edge.root_delta}"
    )


def select_edges(report: WeatherReport, mode: str) -> tuple[EdgeWeather, ...]:
    if mode == "all":
        return report.edges
    if mode == "silent":
        return tuple(edge for edge in report.edges if edge.state != "ACTIVE")
    state = mode.upper()
    return tuple(edge for edge in report.edges if edge.state == state)


def print_forecast(report: WeatherReport, edge_mode: str, limit: int) -> None:
    graph = report.graph
    print("ASSOCIAHEDRON WEATHER / exact rotation forecast")
    print(f"word       : {garden.word_label(report.atoms, compact=True)}")
    print(f"vertices   : {len(graph.trees)} = Catalan({graph.leaves - 1})")
    print(
        f"rotations  : {len(graph.rotations)} observed / "
        f"{expected_edge_count(graph.leaves)} expected"
    )
    print(f"topology   : connected={graph.connected} degree={expected_degree(graph.leaves)}")
    print(f"phenotypes : {report.phenotype_count}")
    print(
        f"weather    : active={report.active_count} silent={report.silent_count} "
        f"(damped={report.damped_count}, calm={report.calm_count})"
    )
    print(
        f"islands    : {report.component_count} induced component(s); "
        f"excess={report.component_excess}"
    )
    print("delta sign : canonical ((A*B)*C) source minus A*(B*C) target")

    print("\nPHENOTYPE-INDUCED COMPONENTS")
    for region in report.regions:
        print_region(report, region, limit)

    chosen = select_edges(report, edge_mode)
    print(f"\nROTATION LABELS / mode={edge_mode} count={len(chosen)}")
    visible = chosen if limit == 0 else chosen[:limit]
    for edge in visible:
        print_edge_weather(report, edge)
    hidden = len(chosen) - len(visible)
    if hidden:
        print(f"... {hidden} more labeled edge(s); use --limit 0 to show all")


def print_topology(max_leaves: int) -> None:
    if not 1 <= max_leaves <= TOPOLOGY_LIMIT:
        raise ValueError(f"topology verification is bounded at {TOPOLOGY_LIMIT} leaves")
    print("ASSOCIAHEDRON 1-SKELETON / topology ledger")
    print(" n  vertices  edges  expected  degree  connected")
    print("--  --------  -----  --------  ------  ---------")
    for leaves in range(1, max_leaves + 1):
        graph = rotation_graph(leaves)
        print(
            f"{leaves:>2}  {len(graph.trees):>8}  {len(graph.rotations):>5}  "
            f"{expected_edge_count(leaves):>8}  {expected_degree(leaves):>6}  "
            f"{str(graph.connected):>9}"
        )


def champion_search(leaves: int) -> Champions:
    if not 1 <= leaves <= SEARCH_LIMIT:
        raise ValueError(f"word search is bounded at {SEARCH_LIMIT} leaves")

    best_reports: dict[str, WeatherReport | None] = {
        "storm": None,
        "damping": None,
        "fracture": None,
    }
    best_scores: dict[str, tuple[int, ...] | None] = {key: None for key in best_reports}
    for symbols in product(("h", "q"), repeat=leaves):
        report = report_for_symbols(symbols)
        scores = {
            "storm": (
                report.active_count,
                report.phenotype_count,
                report.damped_count,
                report.component_excess,
            ),
            "damping": (
                report.damped_count,
                report.component_excess,
                report.phenotype_count,
                report.active_count,
            ),
            "fracture": (
                report.component_excess,
                report.phenotype_count,
                report.active_count,
                report.damped_count,
            ),
        }
        for category, score in scores.items():
            old_score = best_scores[category]
            if old_score is None or score > old_score:
                best_scores[category] = score
                best_reports[category] = report

    storm = best_reports["storm"]
    damping = best_reports["damping"]
    fracture = best_reports["fracture"]
    if storm is None or damping is None or fracture is None:
        raise AssertionError("champion search found no words")
    return Champions(storm, damping, fracture)


def compact_metrics(report: WeatherReport) -> str:
    return (
        f"p={report.phenotype_count},a={report.active_count},"
        f"d={report.damped_count},x={report.component_excess}"
    )


def region_signature(report: WeatherReport) -> str:
    fields: list[str] = []
    for region in report.regions:
        sizes = "+".join(str(len(component)) for component in region.components)
        fields.append(f"{region.phenotype}:{sizes}")
    return "  ".join(fields)


def print_expedition(max_leaves: int) -> None:
    if not 3 <= max_leaves <= SEARCH_LIMIT:
        raise ValueError(f"--max-leaves must be between 3 and {SEARCH_LIMIT}")
    print("ASSOCIAHEDRON WEATHER EXPEDITION")
    print("Exhaustive h/q search; h<q breaks exact score ties. No randomness.\n")
    print(" n  storm champion          damping champion        fracture champion")
    print("--  ----------------------  ----------------------  ----------------------")
    for leaves in range(3, max_leaves + 1):
        champions = champion_search(leaves)
        storm_word = garden.word_label(champions.storm.atoms, compact=True)
        damping_word = garden.word_label(champions.damping.atoms, compact=True)
        fracture_word = garden.word_label(champions.fracture.atoms, compact=True)
        print(
            f"{leaves:>2}  {storm_word:<7} {compact_metrics(champions.storm):<14}  "
            f"{damping_word:<7} {compact_metrics(champions.damping):<14}  "
            f"{fracture_word:<7} {compact_metrics(champions.fracture):<14}"
        )

    print("\nNAMED FRONTS")
    if max_leaves >= 6:
        witness = report_for_symbols("hhqqhq")
        print(
            f"six-mask hhqqhq: {compact_metrics(witness)}, "
            f"silent={witness.silent_count}, regions=[{region_signature(witness)}]"
        )
    if max_leaves >= 7:
        pure_h = report_for_symbols("hhhhhhh")
        print(
            f"pure h^7       : {compact_metrics(pure_h)}, "
            f"silent={pure_h.silent_count}, regions=[{region_signature(pure_h)}]"
        )
    print("\nScores are declared objectives, not universal notions of interestingness:")
    print("storm=max(active,p,damped,excess); damping=max(damped,excess,p,active);")
    print("fracture=max(component-excess,p,active,damped).")


def run_self_tests(deep: bool) -> None:
    expected_vertices = (1, 1, 2, 5, 14, 42, 132, 429)
    expected_edges = (0, 0, 1, 5, 21, 84, 330, 1287)
    for leaves, (vertices, edges) in enumerate(
        zip(expected_vertices, expected_edges, strict=True), 1
    ):
        graph = rotation_graph(leaves)
        assert len(graph.trees) == vertices
        assert len(graph.rotations) == edges == expected_edge_count(leaves)
        assert graph.connected
        assert {len(neighbors) for neighbors in graph.adjacency} == {
            expected_degree(leaves)
        }
        assert len(
            {
                tuple(sorted((rotation.source, rotation.target)))
                for rotation in graph.rotations
            }
        ) == edges

    hhh = report_for_symbols("hhh")
    assert (
        hhh.phenotype_count,
        hhh.active_count,
        hhh.damped_count,
        hhh.calm_count,
        hhh.component_excess,
    ) == (2, 1, 0, 0, 0)

    hhhh = report_for_symbols("hhhh")
    assert (
        hhhh.phenotype_count,
        hhhh.active_count,
        hhhh.damped_count,
        hhhh.calm_count,
        hhhh.component_excess,
    ) == (3, 5, 0, 0, 2)

    witness = report_for_symbols("hhqqhq")
    assert (
        witness.phenotype_count,
        witness.active_count,
        witness.silent_count,
        witness.damped_count,
        witness.calm_count,
        witness.component_excess,
    ) == (6, 40, 44, 5, 39, 1)

    pure_h = report_for_symbols("hhhhhhh")
    assert (
        pure_h.phenotype_count,
        pure_h.active_count,
        pure_h.silent_count,
        pure_h.damped_count,
        pure_h.calm_count,
        pure_h.component_excess,
    ) == (6, 236, 94, 8, 86, 32)

    for report in (hhh, hhhh, witness, pure_h):
        assert report.active_count + report.silent_count == len(report.graph.rotations)
        assert report.damped_count + report.calm_count == report.silent_count
        assert sum(len(region.vertices) for region in report.regions) == len(
            report.graph.trees
        )
        for edge in report.edges:
            assert edge.root_delta == subtract(
                edge.source_phenotype, edge.target_phenotype
            )
            assert (edge.state == "ACTIVE") == (edge.root_delta != garden.ZERO)

    if deep:
        storm_words: list[str] = []
        damping_words: list[str] = []
        fracture_words: list[str] = []
        for leaves in range(3, SEARCH_LIMIT + 1):
            champions = champion_search(leaves)
            storm_words.append(garden.word_label(champions.storm.atoms, compact=True))
            damping_words.append(
                garden.word_label(champions.damping.atoms, compact=True)
            )
            fracture_words.append(
                garden.word_label(champions.fracture.atoms, compact=True)
            )
        assert storm_words == ["hhh", "hhhh", "hhhhh", "hhhhhh", "hhhhhhh"]
        assert damping_words == ["hhh", "hqqq", "qhhhq", "qhqqhq", "qhqqqhq"]
        assert fracture_words == ["hhh", "hhhh", "hhhhh", "hhhhhh", "hhhhhhh"]

    print("SELF-TEST PASS")
    print("vertices n=1..8 : 1,1,2,5,14,42,132,429")
    print("edges n=1..8    : 0,0,1,5,21,84,330,1287")
    print("connectivity     : verified through n=8")
    print("regular degree   : max(n-2,0) through n=8")
    print("hhqqhq weather   : p=6 active=40 damped=5 calm=39 excess=1")
    print("h^7 weather      : p=6 active=236 damped=8 calm=86 excess=32")
    print(f"word search      : {'exhaustive through n=7' if deep else 'not run (use --deep)'}")


def non_negative(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Put exact 1,h,q phenotypes on the associahedron rotation graph.",
        epilog="With no command, the deterministic expedition runs through n=7.",
    )
    subparsers = parser.add_subparsers(dest="command")

    forecast = subparsers.add_parser(
        "forecast", help="analyze one h/q word on its full rotation graph"
    )
    forecast.add_argument("word", help="positive h/q word, e.g. hhqqhq")
    forecast.add_argument(
        "--edges",
        choices=("all", "active", "silent", "damped", "calm"),
        default="all",
        help="edge-weather filter (default: all)",
    )
    forecast.add_argument(
        "--limit",
        type=non_negative,
        default=8,
        help="vertices per phenotype and edges printed; 0 prints all",
    )

    inspect = subparsers.add_parser("rotation", help="inspect one exact rotation label")
    inspect.add_argument("word", help="positive h/q word")
    inspect.add_argument("--edge", type=non_negative, required=True, help="zero-based edge index")

    topology = subparsers.add_parser(
        "topology", help="verify associahedron vertex/edge counts and connectivity"
    )
    topology.add_argument("--max-leaves", type=int, default=8)

    expedition = subparsers.add_parser(
        "expedition", help="search deterministic storm, damping, and fracture champions"
    )
    expedition.add_argument("--max-leaves", type=int, default=7)

    test = subparsers.add_parser("test", help="run exact topology and weather tests")
    test.add_argument(
        "--deep",
        action="store_true",
        help="also exhaustively reproduce all champions through n=7",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "forecast":
            report = analyze_weather(parse_hq_word(args.word))
            print_forecast(report, args.edges, args.limit)
        elif args.command == "rotation":
            report = analyze_weather(parse_hq_word(args.word))
            if not report.edges:
                raise ValueError("this word has no rotation edges")
            if not 0 <= args.edge < len(report.edges):
                raise ValueError(
                    f"edge index must be between 0 and {len(report.edges) - 1}"
                )
            print_edge_weather(report, report.edges[args.edge])
        elif args.command == "topology":
            print_topology(args.max_leaves)
        elif args.command == "test":
            run_self_tests(args.deep)
        else:
            max_leaves = args.max_leaves if args.command == "expedition" else 7
            print_expedition(max_leaves)
    except ValueError as error:
        parser.error(str(error))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
