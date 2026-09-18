"""
test_suite.py — Full Integration & Unit Test Suite for NetGenAI
Verifies all 9 topology architectures, RAG knowledge retrieval,
Genetic Algorithm multi-objective optimization, failure simulation,
and IaC configuration exporters.
"""

import unittest
import networkx as nx
from network_models import (
    NetworkRequirements, OrgSize, TrafficLoad, FaultTolerance,
    ScalabilityNeed, TopologyType, DeviceType, NetworkTier
)
from topology_engine import TopologyEngine
from rag_knowledge import RAGEngine
from ga_optimizer import GeneticOptimizer, GAConfig
from export_generator import ExportGenerator


class TestNetGenAI(unittest.TestCase):

    def setUp(self):
        self.req = NetworkRequirements(
            org_size=OrgSize.MEDIUM,
            num_departments=4,
            num_users=300,
            traffic_load=TrafficLoad.MEDIUM,
            budget_usd=160000,
            fault_tolerance=FaultTolerance.HIGH,
            scalability=ScalabilityNeed.MODERATE,
            security_features=["Firewall", "IDS/IPS", "DMZ"],
            preferred_topology=TopologyType.AUTO,
            compliance_frameworks=["ISO 27001", "PCI-DSS 4.0"],
            wan_sites=1,
            wireless_required=True,
            dmz_required=True,
            redundant_wan=True,
            sd_wan=False
        )
        self.engine = TopologyEngine()

    def test_all_topology_types(self):
        """Test generation across all supported architectural templates."""
        topo_types = [
            TopologyType.STAR,
            TopologyType.THREE_TIER,
            TopologyType.COLLAPSED_CORE,
            TopologyType.SPINE_LEAF,
            TopologyType.MESH,
            TopologyType.PARTIAL_MESH,
            TopologyType.HYBRID,
            TopologyType.RING,
            TopologyType.FAT_TREE,
        ]
        for tt in topo_types:
            with self.subTest(topology_type=tt):
                req = self.req
                req.preferred_topology = tt
                engine = TopologyEngine()
                graph, metrics = engine.generate(req)
                self.assertGreater(len(engine.nodes), 0)
                self.assertGreater(len(engine.links), 0)
                self.assertGreater(metrics.total_cost_capex, 0)
                self.assertGreater(metrics.availability_percent, 90.0)

    def test_rag_retrieval(self):
        """Test RAG knowledge base search and contextual recommendations."""
        rag = RAGEngine()
        recs = rag.get_recommendations(self.req)
        self.assertGreater(len(recs), 0)
        top_entry, top_score = recs[0]
        self.assertTrue(hasattr(top_entry, "title"))
        self.assertTrue(hasattr(top_entry, "content"))
        self.assertGreater(top_score, 0.0)

        # Natural language query
        results = rag.retrieve("spine-leaf BGP EVPN data center", top_k=3)
        self.assertGreater(len(results), 0)

    def test_genetic_algorithm(self):
        """Test GA chromosome evolution and fitness convergence."""
        graph, metrics = self.engine.generate(self.req)
        config = GAConfig(population_size=10, max_generations=5)
        optimizer = GeneticOptimizer(config=config)
        best_graph, history = optimizer.optimize(graph, self.req)
        
        self.assertEqual(len(history), 5)
        summary = optimizer.get_optimization_summary()
        self.assertIn("generations_run", summary)
        self.assertIn("initial_fitness", summary)
        self.assertIn("final_fitness", summary)
        self.assertGreaterEqual(summary["final_fitness"], summary["initial_fitness"] * 0.95)

    def test_failure_simulation(self):
        """Test SPOF and partition analysis during node failure."""
        self.engine.generate(self.req)
        first_node = list(self.engine.nodes.keys())[0]
        sim = self.engine.simulate_failure(first_node)
        self.assertIn("network_status", sim)
        self.assertIn("isolated_segments", sim)
        self.assertIn("connectivity", sim)

    def test_iac_exports(self):
        """Test generation of Cisco, Terraform, Ansible, and IPAM exports."""
        self.engine.generate(self.req)
        cisco = ExportGenerator.generate_cisco_ios_config(
            self.engine.nodes, self.engine.links, self.engine.vlans
        )
        self.assertIn("hostname", cisco)
        self.assertIn("interface", cisco)

        terraform = ExportGenerator.generate_terraform(
            self.engine.nodes, self.engine.vlans
        )
        self.assertIn('resource "aws_vpc"', terraform)

        ansible = ExportGenerator.generate_ansible_playbook(self.engine.nodes)
        self.assertIn("cisco.ios.ios", ansible)

        ipam = ExportGenerator.generate_ipam_json(
            self.engine.nodes, self.engine.vlans
        )
        self.assertIn("enterprise_ipam", ipam)


if __name__ == "__main__":
    unittest.main()
