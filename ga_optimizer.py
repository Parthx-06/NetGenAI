"""
ga_optimizer.py — Multi-Objective Genetic Algorithm Optimizer
for enterprise network topology optimization.

Optimizes topologies for cost, redundancy, latency, throughput, and scalability
using tournament selection, crossover, and mutation operators with elitism.
Provides real-time progress tracking for the Streamlit UI.
"""

import random
import copy
import math
import time
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Callable, Optional
import networkx as nx

from network_models import (
    DeviceType, NetworkTier, DEVICE_CATALOG, LINK_SPECS,
    select_device, select_link, calculate_availability,
    NetworkRequirements, TopologyMetrics,
)


@dataclass
class FitnessScores:
    """Multi-objective fitness breakdown."""
    cost_score: float = 0.0       # Lower is better (normalized)
    redundancy_score: float = 0.0  # Higher is better (0-1)
    latency_score: float = 0.0    # Lower is better (normalized)
    throughput_score: float = 0.0  # Higher is better (0-1)
    scalability_score: float = 0.0 # Higher is better (0-1)
    total_fitness: float = 0.0     # Weighted sum


@dataclass
class Chromosome:
    """Encoded network topology for genetic algorithm."""
    adjacency: List[Tuple[str, str, float]]  # (source, target, bandwidth)
    device_tiers: Dict[str, int]  # node_id → device tier index (0=cheapest, 2=premium)
    link_redundancy: Dict[str, bool]  # edge_key → is_redundant
    fitness: FitnessScores = field(default_factory=FitnessScores)
    generation: int = 0


@dataclass
class GAConfig:
    """Configuration for the genetic algorithm."""
    population_size: int = 24
    max_generations: int = 50
    tournament_size: int = 3
    crossover_rate: float = 0.85
    mutation_rate: float = 0.15
    elitism_count: int = 2

    # Fitness weights (must sum to 1.0)
    w_cost: float = 0.30
    w_redundancy: float = 0.25
    w_latency: float = 0.15
    w_throughput: float = 0.15
    w_scalability: float = 0.15


@dataclass
class GAProgress:
    """Progress tracking for each generation."""
    generation: int
    best_fitness: float
    avg_fitness: float
    worst_fitness: float
    best_cost: float
    best_redundancy: float
    improvement: float  # vs previous generation
    mutation_events: List[str] = field(default_factory=list)


class GeneticOptimizer:
    """
    Multi-objective genetic algorithm for network topology optimization.

    Encodes topology as chromosome (adjacency list + device tiers),
    evaluates fitness across cost, redundancy, latency, throughput, scalability,
    and evolves population using tournament selection, crossover, and mutation.
    """

    def __init__(self, config: GAConfig = None):
        self.config = config or GAConfig()
        self.population: List[Chromosome] = []
        self.history: List[GAProgress] = []
        self.best_chromosome: Optional[Chromosome] = None
        self.base_graph: Optional[nx.Graph] = None
        self.node_list: List[str] = []
        self.requirements: Optional[NetworkRequirements] = None

    def optimize(self, graph: nx.Graph, requirements: NetworkRequirements,
                 progress_callback: Callable = None) -> Tuple[nx.Graph, List[GAProgress]]:
        """
        Run genetic algorithm optimization on the given topology.

        Args:
            graph: NetworkX graph of the initial topology
            requirements: Network requirements for fitness evaluation
            progress_callback: Optional callback(GAProgress) for UI updates

        Returns:
            Optimized graph and history of progress per generation
        """
        self.base_graph = graph.copy()
        self.node_list = list(graph.nodes())
        self.requirements = requirements
        self.history = []

        if len(self.node_list) < 3:
            return graph, []

        # Initialize population
        self._initialize_population()

        # Evolve
        for gen in range(self.config.max_generations):
            # Evaluate fitness
            for chromo in self.population:
                chromo.fitness = self._evaluate_fitness(chromo)
                chromo.generation = gen

            # Sort by fitness (descending)
            self.population.sort(key=lambda c: c.fitness.total_fitness, reverse=True)

            # Track progress
            fitnesses = [c.fitness.total_fitness for c in self.population]
            prev_best = self.history[-1].best_fitness if self.history else 0
            progress = GAProgress(
                generation=gen,
                best_fitness=round(fitnesses[0], 4),
                avg_fitness=round(sum(fitnesses) / len(fitnesses), 4),
                worst_fitness=round(fitnesses[-1], 4),
                best_cost=round(self.population[0].fitness.cost_score, 4),
                best_redundancy=round(self.population[0].fitness.redundancy_score, 4),
                improvement=round(fitnesses[0] - prev_best, 4) if prev_best > 0 else 0,
            )
            self.history.append(progress)

            # Update best
            if self.best_chromosome is None or fitnesses[0] > self.best_chromosome.fitness.total_fitness:
                self.best_chromosome = copy.deepcopy(self.population[0])

            # Callback for UI
            if progress_callback:
                progress_callback(progress)

            # Create next generation
            new_population = []

            # Elitism: carry over top individuals unchanged
            for i in range(self.config.elitism_count):
                new_population.append(copy.deepcopy(self.population[i]))

            # Fill remaining with selection + crossover + mutation
            while len(new_population) < self.config.population_size:
                # Tournament selection
                parent1 = self._tournament_select()
                parent2 = self._tournament_select()

                # Crossover
                if random.random() < self.config.crossover_rate:
                    child1, child2 = self._crossover(parent1, parent2)
                else:
                    child1 = copy.deepcopy(parent1)
                    child2 = copy.deepcopy(parent2)

                # Mutation
                if random.random() < self.config.mutation_rate:
                    events = self._mutate(child1)
                    progress.mutation_events.extend(events)
                if random.random() < self.config.mutation_rate:
                    events = self._mutate(child2)
                    progress.mutation_events.extend(events)

                new_population.append(child1)
                if len(new_population) < self.config.population_size:
                    new_population.append(child2)

            self.population = new_population

        # Build optimized graph from best chromosome
        optimized_graph = self._decode_chromosome(self.best_chromosome)
        return optimized_graph, self.history

    # ────────────────────────────────────────────────────────
    # Population Initialization
    # ────────────────────────────────────────────────────────

    def _initialize_population(self):
        """Create initial population with random variations of the base topology."""
        self.population = []

        # Extract base adjacency
        base_adj = []
        for u, v, data in self.base_graph.edges(data=True):
            base_adj.append((u, v, data.get('bandwidth', 1.0)))

        base_tiers = {n: 1 for n in self.node_list}  # Default mid-tier
        base_redundancy = {f"{u}-{v}": data.get('redundant', False)
                          for u, v, data in self.base_graph.edges(data=True)}

        for i in range(self.config.population_size):
            adj = list(base_adj)
            tiers = dict(base_tiers)
            redundancy = dict(base_redundancy)

            if i > 0:  # First individual is the original
                # Randomize device tiers
                for node in self.node_list:
                    tiers[node] = random.choice([0, 1, 2])

                # Randomly add/remove some links
                if random.random() < 0.5 and len(adj) > 3:
                    # Add a random link
                    n1 = random.choice(self.node_list)
                    n2 = random.choice(self.node_list)
                    if n1 != n2 and (n1, n2, None) not in [(a, b, None) for a, b, _ in adj]:
                        bw = random.choice([1.0, 10.0, 25.0, 40.0])
                        adj.append((n1, n2, bw))
                        redundancy[f"{n1}-{n2}"] = random.random() < 0.3

                if random.random() < 0.3 and len(adj) > 5:
                    # Toggle some redundancy
                    key = random.choice(list(redundancy.keys()))
                    redundancy[key] = not redundancy[key]

            chromo = Chromosome(
                adjacency=adj,
                device_tiers=tiers,
                link_redundancy=redundancy,
            )
            self.population.append(chromo)

    # ────────────────────────────────────────────────────────
    # Fitness Evaluation
    # ────────────────────────────────────────────────────────

    def _evaluate_fitness(self, chromo: Chromosome) -> FitnessScores:
        """Evaluate multi-objective fitness for a chromosome."""
        scores = FitnessScores()
        graph = self._decode_chromosome(chromo)

        if graph.number_of_nodes() == 0:
            return scores

        # --- Cost Score (lower is better → invert for fitness) ---
        total_cost = 0
        for node in graph.nodes():
            tier = chromo.device_tiers.get(node, 1)
            # Approximate cost by tier
            tier_multiplier = [0.7, 1.0, 1.4][tier]
            node_data = self.base_graph.nodes.get(node, {})
            base_cost = 10000  # default if no spec
            # Use original node data to estimate base cost
            total_cost += base_cost * tier_multiplier

        for u, v, data in graph.edges(data=True):
            link_bw = data.get('bandwidth', 1.0)
            total_cost += link_bw * 50  # approximate link cost

        # Normalize cost: 0 = most expensive possible, 1 = cheapest
        max_possible_cost = len(self.node_list) * 15000 * 1.4 + len(list(graph.edges())) * 100 * 50
        scores.cost_score = max(0, 1.0 - (total_cost / max(max_possible_cost, 1)))

        # --- Redundancy Score ---
        if graph.number_of_nodes() > 1 and nx.is_connected(graph):
            connectivity = nx.node_connectivity(graph)
            n_edges = graph.number_of_edges()
            min_edges = graph.number_of_nodes() - 1  # tree
            redundant_ratio = (n_edges - min_edges) / max(min_edges, 1)
            scores.redundancy_score = min(1.0, (connectivity * 0.3 + redundant_ratio * 0.7))
        else:
            scores.redundancy_score = 0.0

        # --- Latency Score (average path length → lower is better) ---
        if nx.is_connected(graph) and graph.number_of_nodes() > 1:
            avg_path = nx.average_shortest_path_length(graph)
            max_path = graph.number_of_nodes() - 1
            scores.latency_score = max(0, 1.0 - (avg_path / max(max_path, 1)))
        else:
            scores.latency_score = 0.0

        # --- Throughput Score ---
        total_bw = sum(data.get('bandwidth', 1.0) for _, _, data in graph.edges(data=True))
        max_possible_bw = len(list(graph.edges())) * 100
        scores.throughput_score = min(1.0, total_bw / max(max_possible_bw * 0.5, 1))

        # --- Scalability Score ---
        # Based on port headroom and modular design
        degree_variance = 0
        degrees = [d for _, d in graph.degree()]
        if degrees:
            mean_degree = sum(degrees) / len(degrees)
            degree_variance = sum((d - mean_degree) ** 2 for d in degrees) / len(degrees)
        # Lower variance = more uniform = better scalability
        scores.scalability_score = max(0, 1.0 - (degree_variance / max(len(self.node_list), 1)))

        # --- Weighted Total ---
        cfg = self.config
        scores.total_fitness = round(
            cfg.w_cost * scores.cost_score +
            cfg.w_redundancy * scores.redundancy_score +
            cfg.w_latency * scores.latency_score +
            cfg.w_throughput * scores.throughput_score +
            cfg.w_scalability * scores.scalability_score,
            4
        )

        return scores

    # ────────────────────────────────────────────────────────
    # Selection, Crossover, Mutation
    # ────────────────────────────────────────────────────────

    def _tournament_select(self) -> Chromosome:
        """Tournament selection: pick best from random subset."""
        candidates = random.sample(self.population,
                                   min(self.config.tournament_size, len(self.population)))
        return max(candidates, key=lambda c: c.fitness.total_fitness)

    def _crossover(self, p1: Chromosome, p2: Chromosome) -> Tuple[Chromosome, Chromosome]:
        """Single-point crossover on adjacency list and device tiers."""
        # Adjacency crossover
        min_len = min(len(p1.adjacency), len(p2.adjacency))
        if min_len > 1:
            point = random.randint(1, min_len - 1)
            c1_adj = p1.adjacency[:point] + p2.adjacency[point:]
            c2_adj = p2.adjacency[:point] + p1.adjacency[point:]
        else:
            c1_adj = list(p1.adjacency)
            c2_adj = list(p2.adjacency)

        # Device tier crossover (uniform)
        c1_tiers = {}
        c2_tiers = {}
        all_nodes = set(p1.device_tiers.keys()) | set(p2.device_tiers.keys())
        for node in all_nodes:
            if random.random() < 0.5:
                c1_tiers[node] = p1.device_tiers.get(node, 1)
                c2_tiers[node] = p2.device_tiers.get(node, 1)
            else:
                c1_tiers[node] = p2.device_tiers.get(node, 1)
                c2_tiers[node] = p1.device_tiers.get(node, 1)

        # Redundancy crossover (uniform)
        c1_red = {}
        c2_red = {}
        all_keys = set(p1.link_redundancy.keys()) | set(p2.link_redundancy.keys())
        for key in all_keys:
            if random.random() < 0.5:
                c1_red[key] = p1.link_redundancy.get(key, False)
                c2_red[key] = p2.link_redundancy.get(key, False)
            else:
                c1_red[key] = p2.link_redundancy.get(key, False)
                c2_red[key] = p1.link_redundancy.get(key, False)

        child1 = Chromosome(adjacency=c1_adj, device_tiers=c1_tiers, link_redundancy=c1_red)
        child2 = Chromosome(adjacency=c2_adj, device_tiers=c2_tiers, link_redundancy=c2_red)
        return child1, child2

    def _mutate(self, chromo: Chromosome) -> List[str]:
        """Apply random mutations to a chromosome."""
        events = []
        mutation_type = random.choice(["add_link", "remove_link", "upgrade_device",
                                       "downgrade_device", "change_bandwidth", "toggle_redundancy"])

        if mutation_type == "add_link" and len(self.node_list) >= 2:
            n1 = random.choice(self.node_list)
            n2 = random.choice(self.node_list)
            if n1 != n2:
                bw = random.choice([1.0, 10.0, 25.0])
                chromo.adjacency.append((n1, n2, bw))
                events.append(f"Added link {n1} ↔ {n2} ({bw}G)")

        elif mutation_type == "remove_link" and len(chromo.adjacency) > 3:
            idx = random.randint(0, len(chromo.adjacency) - 1)
            removed = chromo.adjacency.pop(idx)
            events.append(f"Removed link {removed[0]} ↔ {removed[1]}")

        elif mutation_type == "upgrade_device":
            node = random.choice(self.node_list)
            old_tier = chromo.device_tiers.get(node, 1)
            new_tier = min(old_tier + 1, 2)
            chromo.device_tiers[node] = new_tier
            if new_tier != old_tier:
                events.append(f"Upgraded {node} to tier {new_tier}")

        elif mutation_type == "downgrade_device":
            node = random.choice(self.node_list)
            old_tier = chromo.device_tiers.get(node, 1)
            new_tier = max(old_tier - 1, 0)
            chromo.device_tiers[node] = new_tier
            if new_tier != old_tier:
                events.append(f"Downgraded {node} to tier {new_tier}")

        elif mutation_type == "change_bandwidth" and chromo.adjacency:
            idx = random.randint(0, len(chromo.adjacency) - 1)
            u, v, _ = chromo.adjacency[idx]
            new_bw = random.choice([1.0, 10.0, 25.0, 40.0, 100.0])
            chromo.adjacency[idx] = (u, v, new_bw)
            events.append(f"Changed {u} ↔ {v} bandwidth to {new_bw}G")

        elif mutation_type == "toggle_redundancy" and chromo.link_redundancy:
            key = random.choice(list(chromo.link_redundancy.keys()))
            chromo.link_redundancy[key] = not chromo.link_redundancy[key]
            state = "enabled" if chromo.link_redundancy[key] else "disabled"
            events.append(f"Redundancy {state} on {key}")

        return events

    # ────────────────────────────────────────────────────────
    # Decoding
    # ────────────────────────────────────────────────────────

    def _decode_chromosome(self, chromo: Chromosome) -> nx.Graph:
        """Decode a chromosome back into a NetworkX graph."""
        graph = nx.Graph()

        # Add nodes from base graph
        for node in self.node_list:
            if node in self.base_graph.nodes:
                graph.add_node(node, **dict(self.base_graph.nodes[node]))

        # Add edges from chromosome
        for source, target, bandwidth in chromo.adjacency:
            if source in graph.nodes and target in graph.nodes:
                key = f"{source}-{target}"
                graph.add_edge(source, target,
                             bandwidth=bandwidth,
                             redundant=chromo.link_redundancy.get(key, False))

        return graph

    def get_optimization_summary(self) -> Dict:
        """Get a summary of the optimization results."""
        if not self.best_chromosome or not self.history:
            return {}

        initial = self.history[0] if self.history else None
        final = self.history[-1] if self.history else None

        return {
            "generations_run": len(self.history),
            "population_size": self.config.population_size,
            "initial_fitness": initial.best_fitness if initial else 0,
            "final_fitness": final.best_fitness if final else 0,
            "improvement_pct": round(
                ((final.best_fitness - initial.best_fitness) / max(initial.best_fitness, 0.001)) * 100, 1
            ) if initial and final else 0,
            "best_cost_score": round(self.best_chromosome.fitness.cost_score, 3),
            "best_redundancy_score": round(self.best_chromosome.fitness.redundancy_score, 3),
            "best_latency_score": round(self.best_chromosome.fitness.latency_score, 3),
            "best_throughput_score": round(self.best_chromosome.fitness.throughput_score, 3),
            "best_scalability_score": round(self.best_chromosome.fitness.scalability_score, 3),
            "total_mutations": sum(len(h.mutation_events) for h in self.history),
            "convergence_gen": self._find_convergence_gen(),
            "weights": {
                "cost": self.config.w_cost,
                "redundancy": self.config.w_redundancy,
                "latency": self.config.w_latency,
                "throughput": self.config.w_throughput,
                "scalability": self.config.w_scalability,
            }
        }

    def _find_convergence_gen(self) -> int:
        """Find the generation where improvement plateaued."""
        if len(self.history) < 5:
            return len(self.history)
        for i in range(len(self.history) - 5, -1, -1):
            window = self.history[i:i+5]
            improvements = [abs(w.improvement) for w in window]
            if max(improvements) > 0.001:
                return i + 5
        return 1

    def get_fitness_history(self) -> Dict[str, List[float]]:
        """Get fitness history for plotting."""
        return {
            "generation": [h.generation for h in self.history],
            "best": [h.best_fitness for h in self.history],
            "average": [h.avg_fitness for h in self.history],
            "worst": [h.worst_fitness for h in self.history],
        }
