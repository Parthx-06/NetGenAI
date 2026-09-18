"""
Verification test for core Python modules:
- network_models
- rag_knowledge
- topology_engine
- ga_optimizer
"""

from network_models import (
    NetworkRequirements, OrgSize, TrafficLoad, 
    FaultTolerance, ScalabilityNeed, TopologyType
)
from topology_engine import TopologyEngine
from rag_knowledge import RAGEngine
from ga_optimizer import GeneticOptimizer, GAConfig

def test_all():
    req = NetworkRequirements(
        org_size=OrgSize.MEDIUM,
        num_departments=5,
        num_users=350,
        traffic_load=TrafficLoad.MEDIUM,
        budget_usd=150000,
        fault_tolerance=FaultTolerance.HIGH,
        scalability=ScalabilityNeed.MODERATE,
        security_features=['Firewall', 'IDS/IPS', 'DMZ'],
        preferred_topology=TopologyType.AUTO,
        compliance_frameworks=['ISO 27001'],
        wan_sites=1,
        wireless_required=True,
        dmz_required=True,
        redundant_wan=True,
        sd_wan=False
    )

    print("1. Testing Topology Engine...")
    engine = TopologyEngine()
    graph, metrics = engine.generate(req)
    print(f"   Devices: {metrics.total_devices}, Links: {metrics.total_links}")
    print(f"   CapEx: ${metrics.total_cost_capex:,.0f}, OpEx: ${metrics.annual_opex:,.0f}")
    print(f"   Availability: {metrics.availability_percent}% ({metrics.availability_nines})")
    print(f"   Redundancy Score: {metrics.redundancy_score}/100")
    print(f"   Security Score: {metrics.security_score}/100")
    print(f"   AI Reasoning steps: {len(engine.ai_reasoning)}")

    print("\n2. Testing Failure Simulation...")
    node_to_fail = list(engine.nodes.keys())[0]
    sim = engine.simulate_failure(node_to_fail)
    print(f"   Failed node: {sim.get('failed_device')}")
    print(f"   Status: {sim.get('network_status')}, Connectivity: {sim.get('connectivity')}%")

    print("\n3. Testing RAG Engine...")
    rag = RAGEngine()
    recs = rag.get_recommendations(req)
    print(f"   Retrieved recommendations: {len(recs)}")
    for entry, score in recs[:3]:
        print(f"   - [{score:.3f}] {entry.title} ({entry.source}) [{entry.category}]")

    print("\n4. Testing Genetic Algorithm Optimizer...")
    opt = GeneticOptimizer(config=GAConfig(population_size=12, max_generations=6))
    best_graph, history = opt.optimize(graph, req)
    summary = opt.get_optimization_summary()
    print(f"   Generations run: {summary.get('generations_run')}")
    print(f"   Initial Fitness: {summary.get('initial_fitness'):.4f} -> Final: {summary.get('final_fitness'):.4f}")
    print(f"   Improvement: {summary.get('improvement_pct')}%")
    print("\nALL TESTS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    test_all()
