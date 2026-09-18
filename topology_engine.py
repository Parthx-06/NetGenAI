"""
topology_engine.py — Enterprise network topology generation engine.

Generates industry-standard network topologies (3-Tier, Spine-Leaf, Collapsed Core,
Mesh, Ring, Fat-Tree, Hybrid) using NetworkX, with proper device selection,
IP addressing, VLAN design, and network metrics calculation.
"""

import networkx as nx
import random
import math
import copy
from typing import List, Dict, Tuple, Optional
from network_models import (
    DeviceType, NetworkTier, LinkMedia, TopologyType, OrgSize,
    TrafficLoad, FaultTolerance, ScalabilityNeed,
    DeviceSpec, LinkSpec, VLANConfig, NetworkRequirements,
    NetworkNode, NetworkLink, TopologyMetrics,
    DEVICE_CATALOG, LINK_SPECS, VLAN_TEMPLATES,
    select_device, select_link, estimate_users_per_switch,
    calculate_availability, availability_to_nines, calculate_power_cost,
)


class TopologyEngine:
    """
    Generates and analyzes enterprise network topologies based on requirements.
    Uses NetworkX for graph modeling and provides industry-standard layouts.
    """

    def __init__(self):
        self.graph: nx.Graph = nx.Graph()
        self.nodes: Dict[str, NetworkNode] = {}
        self.links: List[NetworkLink] = []
        self.metrics: TopologyMetrics = TopologyMetrics()
        self.vlans: List[VLANConfig] = []
        self.ai_reasoning: List[str] = []

    def reset(self):
        """Reset the engine state."""
        self.graph = nx.Graph()
        self.nodes = {}
        self.links = []
        self.metrics = TopologyMetrics()
        self.vlans = []
        self.ai_reasoning = []

    # ────────────────────────────────────────────────────────
    # Main Generation Entry Point
    # ────────────────────────────────────────────────────────

    def generate(self, requirements: NetworkRequirements) -> Tuple[nx.Graph, TopologyMetrics]:
        """
        Generate a complete network topology based on requirements.
        Returns the NetworkX graph and computed metrics.
        """
        self.reset()
        self.requirements = requirements

        # Determine budget factor (0-1 scale for device selection tier)
        budget_ranges = {
            OrgSize.SMALL: (15_000, 100_000),
            OrgSize.MEDIUM: (100_000, 1_000_000),
            OrgSize.LARGE: (500_000, 5_000_000),
            OrgSize.ENTERPRISE: (2_000_000, 20_000_000),
        }
        bmin, bmax = budget_ranges.get(requirements.org_size, (100_000, 1_000_000))
        self.budget_factor = min(max((requirements.budget_usd - bmin) / max(bmax - bmin, 1), 0.0), 1.0)

        # Determine topology type
        topo_type = requirements.preferred_topology
        if topo_type == TopologyType.AUTO:
            topo_type = self._recommend_topology(requirements)
            self.ai_reasoning.append(
                f"🤖 AI RECOMMENDATION: Based on {requirements.org_size.value}, "
                f"{requirements.traffic_load.value} traffic, and {requirements.fault_tolerance.value} "
                f"fault tolerance → Selected **{topo_type.value}** topology."
            )

        self.ai_reasoning.append(f"📐 Generating {topo_type.value} topology for {requirements.num_users} users...")

        # Generate topology based on type
        generators = {
            TopologyType.STAR: self._gen_star,
            TopologyType.THREE_TIER: self._gen_three_tier,
            TopologyType.COLLAPSED_CORE: self._gen_collapsed_core,
            TopologyType.SPINE_LEAF: self._gen_spine_leaf,
            TopologyType.MESH: self._gen_mesh,
            TopologyType.PARTIAL_MESH: self._gen_partial_mesh,
            TopologyType.HYBRID: self._gen_hybrid,
            TopologyType.RING: self._gen_ring,
            TopologyType.FAT_TREE: self._gen_fat_tree,
        }

        gen_func = generators.get(topo_type, self._gen_three_tier)
        gen_func(requirements)

        # Add security devices
        if "Firewall" in requirements.security_features or requirements.dmz_required:
            self._add_security_layer(requirements)

        # Add wireless infrastructure
        if requirements.wireless_required:
            self._add_wireless(requirements)

        # Assign VLANs
        self._assign_vlans(requirements)

        # Assign IP addresses
        self._assign_ip_addresses()

        # Build NetworkX graph
        self._build_nx_graph()

        # Compute metrics
        self._compute_metrics(requirements)

        self.ai_reasoning.append(
            f"✅ Topology generated: {self.metrics.total_devices} devices, "
            f"{self.metrics.total_links} links, CapEx ${self.metrics.total_cost_capex:,.0f}"
        )

        return self.graph, self.metrics

    # ────────────────────────────────────────────────────────
    # AI Topology Recommendation
    # ────────────────────────────────────────────────────────

    def _recommend_topology(self, req: NetworkRequirements) -> TopologyType:
        """AI-based topology recommendation using weighted scoring."""
        scores = {}

        # Star — simple, small networks
        scores[TopologyType.STAR] = 0
        if req.org_size == OrgSize.SMALL:
            scores[TopologyType.STAR] += 40
        if req.fault_tolerance == FaultTolerance.BASIC:
            scores[TopologyType.STAR] += 20
        if req.budget_usd < 50_000:
            scores[TopologyType.STAR] += 20

        # 3-Tier — enterprise standard
        scores[TopologyType.THREE_TIER] = 10  # slight default preference
        if req.org_size in (OrgSize.LARGE, OrgSize.ENTERPRISE):
            scores[TopologyType.THREE_TIER] += 35
        if req.org_size == OrgSize.MEDIUM:
            scores[TopologyType.THREE_TIER] += 20
        if req.fault_tolerance in (FaultTolerance.HIGH, FaultTolerance.MISSION_CRITICAL):
            scores[TopologyType.THREE_TIER] += 15

        # Collapsed Core — medium networks, cost-conscious
        scores[TopologyType.COLLAPSED_CORE] = 0
        if req.org_size == OrgSize.MEDIUM:
            scores[TopologyType.COLLAPSED_CORE] += 35
        if req.budget_usd < 500_000:
            scores[TopologyType.COLLAPSED_CORE] += 15
        if req.fault_tolerance == FaultTolerance.STANDARD:
            scores[TopologyType.COLLAPSED_CORE] += 10

        # Spine-Leaf — data center, high traffic
        scores[TopologyType.SPINE_LEAF] = 0
        if req.traffic_load in (TrafficLoad.HIGH, TrafficLoad.CRITICAL):
            scores[TopologyType.SPINE_LEAF] += 35
        if req.org_size == OrgSize.ENTERPRISE:
            scores[TopologyType.SPINE_LEAF] += 20
        if req.scalability in (ScalabilityNeed.HIGH, ScalabilityNeed.HYPER):
            scores[TopologyType.SPINE_LEAF] += 20

        # Full Mesh — small, maximum redundancy
        scores[TopologyType.MESH] = 0
        if req.fault_tolerance == FaultTolerance.MISSION_CRITICAL:
            scores[TopologyType.MESH] += 25
        if req.org_size == OrgSize.SMALL and req.num_departments <= 5:
            scores[TopologyType.MESH] += 20

        # Hybrid — large with diverse needs
        scores[TopologyType.HYBRID] = 0
        if req.org_size in (OrgSize.LARGE, OrgSize.ENTERPRISE):
            scores[TopologyType.HYBRID] += 20
        if req.fault_tolerance == FaultTolerance.HIGH:
            scores[TopologyType.HYBRID] += 15
        if req.wan_sites > 1:
            scores[TopologyType.HYBRID] += 15

        # Ring — geographical loops, metro
        scores[TopologyType.RING] = 0
        if req.wan_sites > 2:
            scores[TopologyType.RING] += 20
        if req.fault_tolerance == FaultTolerance.HIGH:
            scores[TopologyType.RING] += 10

        # Fat-Tree — hyperscale
        scores[TopologyType.FAT_TREE] = 0
        if req.traffic_load == TrafficLoad.CRITICAL:
            scores[TopologyType.FAT_TREE] += 30
        if req.num_users > 5000:
            scores[TopologyType.FAT_TREE] += 20
        if req.scalability == ScalabilityNeed.HYPER:
            scores[TopologyType.FAT_TREE] += 25

        best = max(scores, key=scores.get)
        self.ai_reasoning.append(
            f"🧠 Topology scoring: " +
            ", ".join(f"{t.value}={s}" for t, s in sorted(scores.items(), key=lambda x: -x[1])[:4])
        )
        return best

    # ────────────────────────────────────────────────────────
    # Topology Generators
    # ────────────────────────────────────────────────────────

    def _add_node(self, node_id: str, label: str, device_type: DeviceType,
                  tier: NetworkTier, device_spec: DeviceSpec = None,
                  is_redundant: bool = False) -> NetworkNode:
        """Add a node to the topology."""
        node = NetworkNode(
            id=node_id, label=label, device_type=device_type,
            tier=tier, device_spec=device_spec, is_redundant=is_redundant
        )
        self.nodes[node_id] = node
        return node

    def _add_link(self, source: str, target: str, bandwidth_gbps: float = 1.0,
                  is_redundant: bool = False, protocol: str = "") -> NetworkLink:
        """Add a link between two nodes."""
        link_spec = select_link(bandwidth_gbps)
        cost = link_spec.cost_per_meter * 50  # assume 50m average
        link = NetworkLink(
            source=source, target=target, link_spec=link_spec,
            bandwidth_gbps=bandwidth_gbps, is_redundant=is_redundant,
            protocol=protocol, cost=cost
        )
        self.links.append(link)
        return link

    def _calc_access_switches(self, num_users: int) -> int:
        """Calculate number of access switches needed."""
        switch = select_device("access_switch", self.budget_factor)
        per_switch = estimate_users_per_switch(switch)
        return max(math.ceil(num_users / per_switch), 1)

    def _gen_star(self, req: NetworkRequirements):
        """Generate star topology with central switch."""
        self.ai_reasoning.append("🌟 Star topology: Central L3 switch with radial access switches")
        central = select_device("distribution_switch", self.budget_factor)
        self._add_node("core-1", f"Central Switch\n{central.model}", DeviceType.L3_SWITCH,
                       NetworkTier.CORE, central)

        n_access = self._calc_access_switches(req.num_users)
        access_spec = select_device("access_switch", self.budget_factor)

        for i in range(n_access):
            dept = f"Dept-{i+1}" if i < req.num_departments else f"Access-{i+1}"
            nid = f"access-{i+1}"
            self._add_node(nid, f"{dept}\n{access_spec.model}", DeviceType.L2_SWITCH,
                          NetworkTier.ACCESS, access_spec)
            self._add_link("core-1", nid, bandwidth_gbps=10, protocol="LACP")

    def _gen_collapsed_core(self, req: NetworkRequirements):
        """Generate collapsed core (2-tier) topology."""
        self.ai_reasoning.append("🏗️ Collapsed Core: 2× L3 switches as core/distribution, redundant uplinks")
        core_spec = select_device("distribution_switch", self.budget_factor)

        # Dual core/distribution switches
        self._add_node("core-1", f"Core/Dist-1\n{core_spec.model}", DeviceType.L3_SWITCH,
                       NetworkTier.CORE, core_spec, is_redundant=True)
        self._add_node("core-2", f"Core/Dist-2\n{core_spec.model}", DeviceType.L3_SWITCH,
                       NetworkTier.CORE, core_spec, is_redundant=True)
        self._add_link("core-1", "core-2", bandwidth_gbps=40, protocol="vPC/MLAG Peer-Link")

        n_access = self._calc_access_switches(req.num_users)
        access_spec = select_device("access_switch", self.budget_factor)

        for i in range(n_access):
            nid = f"access-{i+1}"
            dept = f"Dept-{i+1}" if i < req.num_departments else f"Block-{i+1}"
            self._add_node(nid, f"{dept}\n{access_spec.model}", DeviceType.L2_SWITCH,
                          NetworkTier.ACCESS, access_spec)
            # Dual uplinks to both core switches
            self._add_link("core-1", nid, bandwidth_gbps=10, protocol="LACP")
            self._add_link("core-2", nid, bandwidth_gbps=10, is_redundant=True, protocol="LACP")

    def _gen_three_tier(self, req: NetworkRequirements):
        """Generate Cisco 3-Tier hierarchical topology."""
        self.ai_reasoning.append("🏛️ 3-Tier Architecture: Core → Distribution → Access (Cisco SAFE model)")

        # Core layer (redundant pair)
        core_spec = select_device("core_router", self.budget_factor)
        self._add_node("core-1", f"Core-1\n{core_spec.model}", DeviceType.CORE_ROUTER,
                       NetworkTier.CORE, core_spec, is_redundant=True)
        self._add_node("core-2", f"Core-2\n{core_spec.model}", DeviceType.CORE_ROUTER,
                       NetworkTier.CORE, core_spec, is_redundant=True)
        self._add_link("core-1", "core-2", bandwidth_gbps=100, protocol="OSPF + BFD")

        # Distribution layer (blocks of 2)
        dist_spec = select_device("distribution_switch", self.budget_factor)
        n_dist_blocks = max(math.ceil(req.num_departments / 3), 1)
        n_dist = n_dist_blocks * 2  # pairs

        for i in range(0, n_dist, 2):
            block = i // 2 + 1
            d1 = f"dist-{i+1}"
            d2 = f"dist-{i+2}"
            self._add_node(d1, f"Dist-{block}A\n{dist_spec.model}", DeviceType.L3_SWITCH,
                          NetworkTier.DISTRIBUTION, dist_spec, is_redundant=True)
            self._add_node(d2, f"Dist-{block}B\n{dist_spec.model}", DeviceType.L3_SWITCH,
                          NetworkTier.DISTRIBUTION, dist_spec, is_redundant=True)
            # Peer link
            self._add_link(d1, d2, bandwidth_gbps=40, protocol="vPC Peer-Link")
            # Uplinks to both core switches
            self._add_link("core-1", d1, bandwidth_gbps=40, protocol="OSPF")
            self._add_link("core-1", d2, bandwidth_gbps=40, protocol="OSPF")
            self._add_link("core-2", d1, bandwidth_gbps=40, is_redundant=True, protocol="OSPF")
            self._add_link("core-2", d2, bandwidth_gbps=40, is_redundant=True, protocol="OSPF")

        # Access layer
        n_access = self._calc_access_switches(req.num_users)
        access_spec = select_device("access_switch", self.budget_factor)

        dist_nodes = [nid for nid in self.nodes if nid.startswith("dist-")]
        for i in range(n_access):
            nid = f"access-{i+1}"
            dept = f"Dept-{i+1}" if i < req.num_departments else f"Floor-{i+1}"
            self._add_node(nid, f"{dept}\n{access_spec.model}", DeviceType.L2_SWITCH,
                          NetworkTier.ACCESS, access_spec)
            # Connect to distribution pair
            block_idx = (i % n_dist_blocks) * 2
            if block_idx < len(dist_nodes):
                self._add_link(dist_nodes[block_idx], nid, bandwidth_gbps=10, protocol="LACP")
            if block_idx + 1 < len(dist_nodes):
                self._add_link(dist_nodes[block_idx + 1], nid, bandwidth_gbps=10,
                             is_redundant=True, protocol="LACP")

    def _gen_spine_leaf(self, req: NetworkRequirements):
        """Generate Spine-Leaf (Clos) data center topology."""
        self.ai_reasoning.append("🌿 Spine-Leaf: Full bipartite mesh with BGP EVPN/VXLAN underlay")

        # Calculate dimensions
        n_leaf = max(self._calc_access_switches(req.num_users), 4)
        n_spine = max(math.ceil(n_leaf / 4), 2)  # 4:1 ratio

        core_spec = select_device("core_router", self.budget_factor)
        dist_spec = select_device("distribution_switch", self.budget_factor)

        # Spine switches
        for i in range(n_spine):
            self._add_node(f"spine-{i+1}", f"Spine-{i+1}\n{core_spec.model}",
                          DeviceType.L3_SWITCH, NetworkTier.CORE, core_spec)

        # Leaf switches
        access_spec = select_device("access_switch", self.budget_factor)
        for i in range(n_leaf):
            self._add_node(f"leaf-{i+1}", f"Leaf-{i+1}\n{access_spec.model}",
                          DeviceType.L2_SWITCH, NetworkTier.ACCESS, access_spec)
            # Connect to ALL spines
            for j in range(n_spine):
                self._add_link(f"spine-{j+1}", f"leaf-{i+1}", bandwidth_gbps=25,
                             protocol="eBGP + EVPN/VXLAN")

    def _gen_mesh(self, req: NetworkRequirements):
        """Generate full mesh topology."""
        self.ai_reasoning.append("🕸️ Full Mesh: Every node connected to every other node (maximum redundancy)")
        n_nodes = min(req.num_departments + 1, 8)  # cap for practicality
        core_spec = select_device("distribution_switch", self.budget_factor)

        for i in range(n_nodes):
            label = "Hub" if i == 0 else f"Site-{i}"
            self._add_node(f"mesh-{i+1}", f"{label}\n{core_spec.model}",
                          DeviceType.L3_SWITCH, NetworkTier.CORE, core_spec)

        # Full mesh links
        for i in range(n_nodes):
            for j in range(i + 1, n_nodes):
                self._add_link(f"mesh-{i+1}", f"mesh-{j+1}", bandwidth_gbps=10,
                             protocol="OSPF")

    def _gen_partial_mesh(self, req: NetworkRequirements):
        """Generate partial mesh topology."""
        self.ai_reasoning.append("🔗 Partial Mesh: Hub nodes fully meshed, spokes connected to nearest hubs")
        n_hubs = max(math.ceil(req.num_departments / 3), 2)
        n_spokes_per_hub = max(req.num_departments // n_hubs, 1)

        core_spec = select_device("core_router", self.budget_factor)
        access_spec = select_device("access_switch", self.budget_factor)

        # Hub nodes (fully meshed)
        for i in range(n_hubs):
            self._add_node(f"hub-{i+1}", f"Hub-{i+1}\n{core_spec.model}",
                          DeviceType.CORE_ROUTER, NetworkTier.CORE, core_spec)
        for i in range(n_hubs):
            for j in range(i + 1, n_hubs):
                self._add_link(f"hub-{i+1}", f"hub-{j+1}", bandwidth_gbps=40, protocol="OSPF Area 0")

        # Spoke nodes
        spoke_count = 0
        for i in range(n_hubs):
            for j in range(n_spokes_per_hub):
                spoke_count += 1
                nid = f"spoke-{spoke_count}"
                self._add_node(nid, f"Branch-{spoke_count}\n{access_spec.model}",
                              DeviceType.L2_SWITCH, NetworkTier.ACCESS, access_spec)
                self._add_link(f"hub-{i+1}", nid, bandwidth_gbps=10, protocol="OSPF Area " + str(i + 1))

    def _gen_hybrid(self, req: NetworkRequirements):
        """Generate hybrid topology (mesh core + star access)."""
        self.ai_reasoning.append("🔀 Hybrid: Meshed core routers with hierarchical access distribution")

        core_spec = select_device("core_router", self.budget_factor)
        n_core = max(min(req.wan_sites + 1, 4), 2)

        # Meshed core
        for i in range(n_core):
            label = "HQ-Core" if i == 0 else f"Site-{i}-Core"
            self._add_node(f"core-{i+1}", f"{label}\n{core_spec.model}",
                          DeviceType.CORE_ROUTER, NetworkTier.CORE, core_spec, is_redundant=True)
        for i in range(n_core):
            for j in range(i + 1, n_core):
                self._add_link(f"core-{i+1}", f"core-{j+1}", bandwidth_gbps=40, protocol="iBGP + OSPF")

        # Distribution per core
        dist_spec = select_device("distribution_switch", self.budget_factor)
        access_spec = select_device("access_switch", self.budget_factor)
        access_per_core = max(self._calc_access_switches(req.num_users) // n_core, 1)
        access_count = 0

        for i in range(n_core):
            dist_id = f"dist-{i+1}"
            self._add_node(dist_id, f"Dist-{i+1}\n{dist_spec.model}",
                          DeviceType.L3_SWITCH, NetworkTier.DISTRIBUTION, dist_spec)
            self._add_link(f"core-{i+1}", dist_id, bandwidth_gbps=40, protocol="OSPF")

            for j in range(access_per_core):
                access_count += 1
                aid = f"access-{access_count}"
                self._add_node(aid, f"Access-{access_count}\n{access_spec.model}",
                              DeviceType.L2_SWITCH, NetworkTier.ACCESS, access_spec)
                self._add_link(dist_id, aid, bandwidth_gbps=10, protocol="LACP")

    def _gen_ring(self, req: NetworkRequirements):
        """Generate redundant ring topology."""
        self.ai_reasoning.append("💍 Ring: Bidirectional ring with ERPS (G.8032) for 50ms failover")

        core_spec = select_device("distribution_switch", self.budget_factor)
        n_nodes = max(req.num_departments + 1, 4)
        n_nodes = min(n_nodes, 12)

        for i in range(n_nodes):
            label = "HQ" if i == 0 else f"Site-{i}"
            self._add_node(f"ring-{i+1}", f"{label}\n{core_spec.model}",
                          DeviceType.L3_SWITCH, NetworkTier.CORE, core_spec)

        # Ring links
        for i in range(n_nodes):
            next_i = (i + 1) % n_nodes
            self._add_link(f"ring-{i+1}", f"ring-{next_i+1}", bandwidth_gbps=10,
                         protocol="ERPS / G.8032")

        # Add access switches to ring nodes
        access_spec = select_device("access_switch", self.budget_factor)
        n_access = self._calc_access_switches(req.num_users)
        for i in range(n_access):
            aid = f"access-{i+1}"
            ring_parent = f"ring-{(i % n_nodes) + 1}"
            self._add_node(aid, f"Access-{i+1}\n{access_spec.model}",
                          DeviceType.L2_SWITCH, NetworkTier.ACCESS, access_spec)
            self._add_link(ring_parent, aid, bandwidth_gbps=10, protocol="LACP")

    def _gen_fat_tree(self, req: NetworkRequirements):
        """Generate k-ary fat-tree topology."""
        # Determine k (must be even)
        k = 4
        if req.num_users > 500:
            k = 6
        if req.num_users > 2000:
            k = 8

        self.ai_reasoning.append(f"🌳 Fat-Tree: k={k} fat-tree ({k}³/4 = {k**3//4} host capacity)")

        core_spec = select_device("core_router", self.budget_factor)
        dist_spec = select_device("distribution_switch", self.budget_factor)
        access_spec = select_device("access_switch", self.budget_factor)

        n_pods = k
        n_core = (k // 2) ** 2
        n_agg_per_pod = k // 2
        n_edge_per_pod = k // 2

        # Core switches
        for i in range(n_core):
            self._add_node(f"core-{i+1}", f"Core-{i+1}\n{core_spec.model}",
                          DeviceType.L3_SWITCH, NetworkTier.CORE, core_spec)

        # Pods
        for p in range(n_pods):
            # Aggregation switches
            for a in range(n_agg_per_pod):
                agg_id = f"agg-p{p+1}-{a+1}"
                self._add_node(agg_id, f"Pod{p+1}-Agg{a+1}\n{dist_spec.model}",
                              DeviceType.L3_SWITCH, NetworkTier.DISTRIBUTION, dist_spec)
                # Connect to core
                core_start = a * (k // 2)
                for c in range(k // 2):
                    core_idx = core_start + c
                    if core_idx < n_core:
                        self._add_link(f"core-{core_idx+1}", agg_id, bandwidth_gbps=25,
                                     protocol="eBGP")

            # Edge (access) switches
            for e in range(n_edge_per_pod):
                edge_id = f"edge-p{p+1}-{e+1}"
                self._add_node(edge_id, f"Pod{p+1}-Edge{e+1}\n{access_spec.model}",
                              DeviceType.L2_SWITCH, NetworkTier.ACCESS, access_spec)
                # Connect to all aggregation switches in this pod
                for a in range(n_agg_per_pod):
                    agg_id = f"agg-p{p+1}-{a+1}"
                    self._add_link(agg_id, edge_id, bandwidth_gbps=10, protocol="ECMP")

    # ────────────────────────────────────────────────────────
    # Security, Wireless, VLANs, IP
    # ────────────────────────────────────────────────────────

    def _add_security_layer(self, req: NetworkRequirements):
        """Add firewall, IDS/IPS, and DMZ to the topology."""
        self.ai_reasoning.append("🔒 Adding security layer: Firewall HA pair + DMZ segment")

        fw_spec = select_device("firewall", self.budget_factor)

        # Find a core node to attach firewall
        core_nodes = [n for n in self.nodes.values() if n.tier == NetworkTier.CORE]
        if not core_nodes:
            core_nodes = list(self.nodes.values())[:1]

        # Internet gateway
        self._add_node("inet-gw", "Internet\nGateway", DeviceType.INTERNET_GATEWAY,
                       NetworkTier.WAN_EDGE)

        # Firewall HA pair
        self._add_node("fw-1", f"Firewall-1\n{fw_spec.model}", DeviceType.FIREWALL,
                       NetworkTier.CORE, fw_spec, is_redundant=True)
        self._add_node("fw-2", f"Firewall-2\n{fw_spec.model}", DeviceType.FIREWALL,
                       NetworkTier.CORE, fw_spec, is_redundant=True)

        # Internet → Firewall
        self._add_link("inet-gw", "fw-1", bandwidth_gbps=10, protocol="BGP")
        self._add_link("inet-gw", "fw-2", bandwidth_gbps=10, is_redundant=True, protocol="BGP")
        self._add_link("fw-1", "fw-2", bandwidth_gbps=10, protocol="HA Heartbeat")

        # Firewall → Core
        if core_nodes:
            cn = core_nodes[0]
            self._add_link("fw-1", cn.id, bandwidth_gbps=10, protocol="OSPF")
            if len(core_nodes) > 1:
                self._add_link("fw-2", core_nodes[1].id, bandwidth_gbps=10, protocol="OSPF")
            else:
                self._add_link("fw-2", cn.id, bandwidth_gbps=10, is_redundant=True, protocol="OSPF")

        # DMZ segment
        if req.dmz_required:
            access_spec = select_device("access_switch", self.budget_factor)
            self._add_node("dmz-sw", f"DMZ Switch\n{access_spec.model}", DeviceType.DMZ_SWITCH,
                          NetworkTier.DMZ, access_spec)
            self._add_link("fw-1", "dmz-sw", bandwidth_gbps=10, protocol="DMZ Zone")
            self._add_node("dmz-srv", "DMZ Servers\n(Web/Mail/DNS)", DeviceType.SERVER,
                          NetworkTier.DMZ)
            self._add_link("dmz-sw", "dmz-srv", bandwidth_gbps=10)

        # IDS/IPS
        if "IDS/IPS" in req.security_features:
            ids_spec = select_device("ids_ips", self.budget_factor)
            self._add_node("ids-1", f"IDS/IPS\n{ids_spec.model}", DeviceType.IDS_IPS,
                          NetworkTier.CORE, ids_spec)
            if core_nodes:
                self._add_link(core_nodes[0].id, "ids-1", bandwidth_gbps=10, protocol="SPAN/TAP")

        # Load Balancer
        if "Load Balancer" in req.security_features or req.traffic_load in (TrafficLoad.HIGH, TrafficLoad.CRITICAL):
            lb_spec = select_device("load_balancer", self.budget_factor)
            self._add_node("lb-1", f"Load Balancer\n{lb_spec.model}", DeviceType.LOAD_BALANCER,
                          NetworkTier.DATA_CENTER, lb_spec, is_redundant=True)
            if core_nodes:
                self._add_link(core_nodes[0].id, "lb-1", bandwidth_gbps=10, protocol="L4/L7 LB")

    def _add_wireless(self, req: NetworkRequirements):
        """Add wireless infrastructure."""
        self.ai_reasoning.append("📡 Adding wireless: Controller + Access Points")

        wlc_spec = select_device("wireless_controller", self.budget_factor)
        ap_spec = select_device("wireless_ap", self.budget_factor)

        # Wireless controller
        core_nodes = [n for n in self.nodes.values() if n.tier in (NetworkTier.CORE, NetworkTier.DISTRIBUTION)]
        self._add_node("wlc-1", f"WLC\n{wlc_spec.model}", DeviceType.WIRELESS_CONTROLLER,
                       NetworkTier.DISTRIBUTION, wlc_spec)
        if core_nodes:
            self._add_link(core_nodes[0].id, "wlc-1", bandwidth_gbps=10, protocol="CAPWAP Control")

        # APs — attach to access switches
        n_aps = max(req.num_users // 30, 2)  # 1 AP per 30 users
        access_nodes = [n for n in self.nodes.values() if n.tier == NetworkTier.ACCESS]
        for i in range(min(n_aps, 6)):  # cap display at 6
            ap_id = f"ap-{i+1}"
            self._add_node(ap_id, f"AP-{i+1}\n{ap_spec.model}", DeviceType.WIRELESS_AP,
                          NetworkTier.ACCESS, ap_spec)
            if access_nodes:
                parent = access_nodes[i % len(access_nodes)]
                self._add_link(parent.id, ap_id, bandwidth_gbps=2.5, protocol="PoE + CAPWAP")

    def _assign_vlans(self, req: NetworkRequirements):
        """Assign VLANs based on requirements."""
        self.vlans = [
            VLAN_TEMPLATES["management"],
            VLAN_TEMPLATES["data"],
            VLAN_TEMPLATES["servers"],
        ]
        if req.wireless_required:
            self.vlans.append(VLAN_TEMPLATES["wireless"])
            self.vlans.append(VLAN_TEMPLATES["guest"])
        if req.dmz_required:
            self.vlans.append(VLAN_TEMPLATES["dmz"])
        if "VoIP" in req.security_features or req.num_users > 100:
            self.vlans.append(VLAN_TEMPLATES["voip"])

        # Assign VLAN IDs to access switches
        for node in self.nodes.values():
            if node.tier == NetworkTier.ACCESS:
                node.vlan_ids = [v.vlan_id for v in self.vlans if v.purpose != "Demilitarized Zone"]
            elif node.tier == NetworkTier.DMZ:
                node.vlan_ids = [VLAN_TEMPLATES["dmz"].vlan_id]

    def _assign_ip_addresses(self):
        """Assign IP addresses to all nodes."""
        subnet_counter = {
            NetworkTier.CORE: 1,
            NetworkTier.DISTRIBUTION: 10,
            NetworkTier.ACCESS: 20,
            NetworkTier.DMZ: 50,
            NetworkTier.WAN_EDGE: 60,
            NetworkTier.MANAGEMENT: 100,
            NetworkTier.DATA_CENTER: 110,
        }
        host_counter = {}

        for node in self.nodes.values():
            tier = node.tier
            base = subnet_counter.get(tier, 1)
            if tier not in host_counter:
                host_counter[tier] = 1
            host = host_counter[tier]
            host_counter[tier] += 1

            if tier == NetworkTier.DMZ:
                node.ip_address = f"172.16.0.{host}"
                node.subnet = "172.16.0.0/24"
            elif tier == NetworkTier.WAN_EDGE:
                node.ip_address = f"203.0.113.{host}"
                node.subnet = "203.0.113.0/24"
            else:
                node.ip_address = f"10.0.{base}.{host}"
                node.subnet = f"10.0.{base}.0/24"

    # ────────────────────────────────────────────────────────
    # Graph & Metrics
    # ────────────────────────────────────────────────────────

    def _build_nx_graph(self):
        """Build NetworkX graph from nodes and links."""
        self.graph = nx.Graph()
        for nid, node in self.nodes.items():
            self.graph.add_node(nid, **{
                'label': node.label,
                'device_type': node.device_type.value,
                'tier': node.tier.value,
                'ip': node.ip_address,
                'subnet': node.subnet,
            })
        for link in self.links:
            self.graph.add_edge(link.source, link.target, **{
                'bandwidth': link.bandwidth_gbps,
                'redundant': link.is_redundant,
                'protocol': link.protocol,
                'cost': link.cost,
            })

    def _compute_metrics(self, req: NetworkRequirements):
        """Compute comprehensive topology metrics."""
        m = self.metrics
        m.total_devices = len(self.nodes)
        m.total_links = len(self.links)

        # Cost
        capex = 0
        annual_maint = 0
        total_power = 0
        total_ru = 0
        mtbf_values = []

        for node in self.nodes.values():
            if node.device_spec:
                capex += node.device_spec.price_usd
                annual_maint += node.device_spec.annual_maintenance_usd
                total_power += node.device_spec.power_watts
                total_ru += node.device_spec.rack_units
                mtbf_values.append(node.device_spec.mtbf_hours)

        for link in self.links:
            capex += link.cost

        m.total_cost_capex = capex
        m.annual_opex = annual_maint
        m.power_total_watts = total_power
        m.annual_power_cost = calculate_power_cost(total_power)
        m.tco_3yr = capex + (annual_maint + m.annual_power_cost) * 3
        m.tco_5yr = capex + (annual_maint + m.annual_power_cost) * 5
        m.rack_units_total = total_ru

        # Graph metrics
        if self.graph.number_of_nodes() > 0 and nx.is_connected(self.graph):
            m.avg_path_length = round(nx.average_shortest_path_length(self.graph), 2)
            m.max_hops = nx.diameter(self.graph)
        else:
            # Handle disconnected graphs
            components = list(nx.connected_components(self.graph))
            if components:
                largest = self.graph.subgraph(max(components, key=len))
                if largest.number_of_nodes() > 1:
                    m.avg_path_length = round(nx.average_shortest_path_length(largest), 2)
                    m.max_hops = nx.diameter(largest)

        # Connectivity & redundancy
        if self.graph.number_of_nodes() > 1:
            m.graph_connectivity = nx.node_connectivity(self.graph) if nx.is_connected(self.graph) else 0
            # Single points of failure (cut vertices)
            cut_vertices = list(nx.articulation_points(self.graph))
            m.single_points_of_failure = len(cut_vertices)
        else:
            m.graph_connectivity = 0
            m.single_points_of_failure = 0

        # Redundancy score (0-100)
        redundant_links = sum(1 for l in self.links if l.is_redundant)
        redundant_devices = sum(1 for n in self.nodes.values() if n.is_redundant)
        link_ratio = redundant_links / max(m.total_links, 1)
        device_ratio = redundant_devices / max(m.total_devices, 1)
        spof_penalty = min(m.single_points_of_failure * 5, 30)
        m.redundancy_score = round(min((link_ratio * 40 + device_ratio * 40 + m.graph_connectivity * 10 - spof_penalty), 100), 1)
        m.redundancy_score = max(m.redundancy_score, 0)

        # Availability
        avg_mtbf = sum(mtbf_values) / max(len(mtbf_values), 1) if mtbf_values else 100000
        n_redundant = max(redundant_devices, 1)
        m.availability_percent = round(calculate_availability(n_redundant, avg_mtbf) * 100, 4)
        m.availability_nines = availability_to_nines(m.availability_percent / 100)

        # Throughput capacity
        m.throughput_capacity_gbps = round(sum(l.bandwidth_gbps for l in self.links) / max(m.total_links / 2, 1), 1)

        # Scalability score
        access_ports = sum(
            n.device_spec.ports_1g for n in self.nodes.values()
            if n.device_spec and n.tier == NetworkTier.ACCESS
        )
        used_ports = req.num_users * 1.2
        port_headroom = (access_ports - used_ports) / max(access_ports, 1)
        m.scalability_score = round(min(max(port_headroom * 100, 0), 100), 1)

        # Security score
        security_points = 0
        device_types = {n.device_type for n in self.nodes.values()}
        if DeviceType.FIREWALL in device_types:
            security_points += 25
        if DeviceType.IDS_IPS in device_types:
            security_points += 20
        if DeviceType.DMZ_SWITCH in device_types:
            security_points += 15
        if DeviceType.LOAD_BALANCER in device_types:
            security_points += 10
        if len(self.vlans) >= 5:
            security_points += 15
        if "Zero-Trust" in req.security_features:
            security_points += 15
        m.security_score = min(security_points, 100)

        # Compliance
        for fw in req.compliance_frameworks:
            if fw == "PCI-DSS 4.0":
                m.compliance_status[fw] = "Pass" if (DeviceType.FIREWALL in device_types and DeviceType.DMZ_SWITCH in device_types) else "Review"
            elif fw == "HIPAA":
                m.compliance_status[fw] = "Pass" if (DeviceType.FIREWALL in device_types and len(self.vlans) >= 4) else "Review"
            elif fw == "SOC 2 Type II":
                m.compliance_status[fw] = "Pass" if (DeviceType.FIREWALL in device_types and DeviceType.IDS_IPS in device_types) else "Review"
            elif fw == "ISO 27001":
                m.compliance_status[fw] = "Pass" if security_points >= 50 else "Review"
            elif fw == "NIST 800-53":
                m.compliance_status[fw] = "Pass" if security_points >= 60 else "Review"
            else:
                m.compliance_status[fw] = "Review"

        # Deployment estimate
        m.estimated_deploy_weeks = max(2, m.total_devices // 5)

    def get_device_summary(self) -> List[Dict]:
        """Get a summary table of all devices with specs."""
        rows = []
        for node in self.nodes.values():
            row = {
                "Device": node.label.replace('\n', ' — '),
                "Type": node.device_type.value,
                "Tier": node.tier.value,
                "IP Address": node.ip_address,
                "VLANs": ", ".join(str(v) for v in node.vlan_ids) if node.vlan_ids else "—",
                "Price": f"${node.device_spec.price_usd:,.0f}" if node.device_spec else "—",
                "Power (W)": node.device_spec.power_watts if node.device_spec else 0,
                "HA": "✓" if node.is_redundant else "—",
            }
            rows.append(row)
        return rows

    def get_cost_breakdown(self) -> List[Dict]:
        """Get itemized cost breakdown."""
        categories = {}
        for node in self.nodes.values():
            if node.device_spec:
                cat = node.device_type.value
                if cat not in categories:
                    categories[cat] = {"capex": 0, "opex": 0, "count": 0}
                categories[cat]["capex"] += node.device_spec.price_usd
                categories[cat]["opex"] += node.device_spec.annual_maintenance_usd
                categories[cat]["count"] += 1

        rows = []
        for cat, vals in sorted(categories.items(), key=lambda x: -x[1]["capex"]):
            rows.append({
                "Category": cat,
                "Count": vals["count"],
                "CapEx": f"${vals['capex']:,.0f}",
                "Annual OpEx": f"${vals['opex']:,.0f}",
                "3-Year TCO": f"${vals['capex'] + vals['opex'] * 3:,.0f}",
            })

        # Cabling
        total_cable = sum(l.cost for l in self.links)
        rows.append({
            "Category": "Cabling & Optics",
            "Count": len(self.links),
            "CapEx": f"${total_cable:,.0f}",
            "Annual OpEx": "$0",
            "3-Year TCO": f"${total_cable:,.0f}",
        })

        return rows

    def simulate_failure(self, node_id: str) -> Dict:
        """Simulate a node failure and analyze impact."""
        if node_id not in self.nodes:
            return {"error": "Node not found"}

        node = self.nodes[node_id]
        test_graph = self.graph.copy()
        test_graph.remove_node(node_id)

        result = {
            "failed_device": node.label.replace('\n', ' — '),
            "type": node.device_type.value,
            "affected_links": sum(1 for l in self.links if l.source == node_id or l.target == node_id),
        }

        if test_graph.number_of_nodes() == 0:
            result["network_status"] = "TOTAL FAILURE"
            result["isolated_segments"] = 0
            result["connectivity"] = 0
        else:
            components = list(nx.connected_components(test_graph))
            result["isolated_segments"] = len(components)
            result["network_status"] = "PARTITIONED" if len(components) > 1 else "OPERATIONAL"
            result["connectivity"] = round(len(max(components, key=len)) / test_graph.number_of_nodes() * 100, 1)

        return result
