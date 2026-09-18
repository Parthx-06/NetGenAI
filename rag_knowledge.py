"""
rag_knowledge.py — Retrieval-Augmented Generation Knowledge Base
for enterprise network topology design.

Contains curated best-practice documents from industry standards (Cisco SAFE,
Juniper design guides, NIST, IEEE) with TF-IDF based retrieval for contextual
recommendations during topology generation.
"""

import re
import math
from dataclasses import dataclass, field
from typing import List, Dict, Tuple


@dataclass
class KnowledgeEntry:
    """A single knowledge base entry."""
    id: str
    title: str
    source: str
    category: str
    content: str
    tags: List[str] = field(default_factory=list)
    applicability: Dict[str, List[str]] = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────
# Knowledge Base Entries
# ──────────────────────────────────────────────────────────────

KNOWLEDGE_BASE: List[KnowledgeEntry] = [
    KnowledgeEntry(
        id="KB001",
        title="Cisco 3-Tier Hierarchical Architecture",
        source="Cisco SAFE Architecture Guide",
        category="Architecture",
        content=(
            "The Cisco 3-Tier model (Core, Distribution, Access) is the gold standard for enterprise "
            "campus networks. The Core layer provides high-speed backbone with redundant L3 switches "
            "or routers (40-100 Gbps links). The Distribution layer aggregates access switches, "
            "enforces policies (ACLs, QoS), and performs inter-VLAN routing. The Access layer connects "
            "end devices with PoE switches. Design rules: Core should never span more than 2 hops. "
            "Distribution blocks should serve 2000-4000 users. Each access switch should uplink with "
            "redundant 10G connections. Use OSPF or EIGRP for L3 routing. Deploy HSRP/VRRP at distribution."
        ),
        tags=["3-tier", "hierarchical", "campus", "cisco", "core", "distribution", "access"],
        applicability={"org_size": ["Medium", "Large", "Enterprise"], "topology": ["3-Tier Hierarchical"]}
    ),
    KnowledgeEntry(
        id="KB002",
        title="Spine-Leaf Data Center Design",
        source="Arista Design Guide / RFC 7938",
        category="Data Center",
        content=(
            "Spine-Leaf (Clos) architecture eliminates oversubscription and provides deterministic latency. "
            "Every leaf switch connects to every spine switch with equal-cost links (typically 25G or 100G). "
            "L3 routing (BGP with EVPN/VXLAN) runs on every link for optimal path selection. Sizing: "
            "Leaf switches serve 48 servers each. Spine count = (number of leafs × oversubscription ratio) / "
            "spine port count. Typical oversubscription: 3:1 for general, 1:1 for HPC/storage. "
            "Never add a third tier; scale horizontally with super-spines if needed. ECMP across all spines "
            "ensures even traffic distribution. Use MLAG or EVPN multi-homing for server dual-homing."
        ),
        tags=["spine-leaf", "clos", "data-center", "bgp", "evpn", "vxlan", "low-latency"],
        applicability={"topology": ["Spine-Leaf (Data Center)"], "traffic": ["High", "Critical"]}
    ),
    KnowledgeEntry(
        id="KB003",
        title="High Availability Design Patterns",
        source="Cisco High Availability Configuration Guide",
        category="Redundancy",
        content=(
            "To achieve 99.99% (four nines) availability: Deploy all critical devices in active/standby or "
            "active/active pairs. Use HSRP v2 or VRRP v3 for gateway redundancy with sub-second failover. "
            "Implement VSS or StackWise-Virtual at distribution for single management plane. Use LACP "
            "port-channels (minimum 2 links) for all inter-switch connections. Deploy dual power supplies "
            "connected to separate PDUs. Use BFD (Bidirectional Forwarding Detection) with routing protocols "
            "for 50ms convergence. For 99.999% (five nines): Add geographic redundancy with separate buildings "
            "and diverse fiber paths. Implement NSF/SSO (Non-Stop Forwarding/Stateful Switchover)."
        ),
        tags=["high-availability", "redundancy", "hsrp", "vrrp", "failover", "nines", "bfd"],
        applicability={"fault_tolerance": ["High", "Mission Critical"]}
    ),
    KnowledgeEntry(
        id="KB004",
        title="Network Security Zone Design",
        source="NIST SP 800-41 / Palo Alto Best Practices",
        category="Security",
        content=(
            "Segment the network into trust zones with firewalls controlling inter-zone traffic. "
            "Standard zones: (1) UNTRUST — Internet-facing, highest threat. (2) DMZ — Public services "
            "(web servers, mail relays) with strict inbound/outbound rules. (3) TRUST — Internal users and "
            "applications. (4) MANAGEMENT — Out-of-band network device management. (5) RESTRICTED — "
            "PCI cardholder data, HIPAA ePHI. Deploy next-gen firewalls (NGFW) with IPS, App-ID, and "
            "SSL decryption between all zones. Use micro-segmentation within zones using SGTs or NSGs. "
            "Implement Zero Trust: verify every flow, assume breach, least privilege access."
        ),
        tags=["security", "firewall", "dmz", "zones", "zero-trust", "ngfw", "segmentation"],
        applicability={"security": ["Firewall", "DMZ", "IDS/IPS", "Zero-Trust"]}
    ),
    KnowledgeEntry(
        id="KB005",
        title="Small Office / Branch Network Design",
        source="Cisco SAFE Branch Architecture",
        category="Architecture",
        content=(
            "For small offices (10-50 users): Use a collapsed core design with a single L3 switch serving "
            "as both distribution and core. Deploy an integrated router with firewall functionality at the "
            "WAN edge. Stack 2 access switches for redundancy. Key components: ISR 4000-series router, "
            "Catalyst 9200 switches, Meraki/Catalyst AP. Use SD-WAN for WAN connectivity with MPLS primary "
            "and Internet backup. Implement local DNS/DHCP. Single VLAN for data, separate VLAN for voice. "
            "Budget: $15K-$40K for network infrastructure."
        ),
        tags=["small-office", "branch", "collapsed-core", "sd-wan", "simple"],
        applicability={"org_size": ["Small"]}
    ),
    KnowledgeEntry(
        id="KB006",
        title="QoS Design for Converged Networks",
        source="Cisco QoS SRND (Solutions Reference Network Design)",
        category="Performance",
        content=(
            "For converged voice/video/data networks, implement 4-class or 8-class QoS model. "
            "Priority queue (EF/DSCP 46): Voice — guaranteed 150ms max latency, <1% loss. "
            "Class AF41 (DSCP 34): Interactive video — 200ms budget. Class AF21 (DSCP 18): Business "
            "critical data. Class DF (DSCP 0): Best effort. Implement at access layer ingress: classify "
            "and mark. Distribution/core: honor markings, apply queuing. Allocate bandwidth: Voice 10%, "
            "Video 23%, Signaling 2%, Business Data 25%, Best Effort 25%, Scavenger 15%. "
            "Use WRED on data classes, strict priority on voice. Enable LLDP-MED for VoIP phone detection."
        ),
        tags=["qos", "voice", "video", "dscp", "priority", "convergence", "latency"],
        applicability={"traffic": ["Medium", "High", "Critical"]}
    ),
    KnowledgeEntry(
        id="KB007",
        title="SD-WAN Architecture & Deployment",
        source="Cisco SD-WAN Design Guide / MEF SD-WAN Standard",
        category="WAN",
        content=(
            "SD-WAN replaces traditional MPLS-centric WAN with transport-independent overlay. "
            "Architecture: vManage (management), vSmart (control), vBond (orchestration), vEdge/cEdge (data). "
            "Benefits: 40-60% WAN cost reduction, application-aware routing, zero-touch provisioning. "
            "Design: Deploy vEdge at each site with dual Internet + optional MPLS. Use TLOC extensions "
            "for hub-and-spoke or full-mesh overlay. Implement application-aware routing policies: "
            "voice → MPLS path, web → Internet path, critical apps → best-path selection. "
            "Security: integrated NGFW, IPS, URL filtering, AMP at branch. Use cloud on-ramps for SaaS."
        ),
        tags=["sd-wan", "wan", "mpls", "overlay", "vxlan", "application-aware"],
        applicability={"security": ["VPN"], "topology": ["Hybrid (Star + Mesh Core)"]}
    ),
    KnowledgeEntry(
        id="KB008",
        title="PCI-DSS Network Requirements",
        source="PCI DSS v4.0 / PA-QSA Guidelines",
        category="Compliance",
        content=(
            "PCI-DSS mandates network segmentation for systems processing cardholder data (CHD). "
            "Requirements: (1) Install firewalls between all wireless networks and the CDE. "
            "(2) Restrict inbound/outbound traffic to only necessary protocols. (3) Implement a DMZ "
            "for public-facing servers. (4) No direct Internet access to/from CDE. (5) Use stateful "
            "inspection or application proxies. (6) Place system components storing CHD in an internal "
            "network zone isolated from the DMZ and untrusted networks. (7) Annual penetration testing "
            "of network segmentation. (8) IDS/IPS monitoring on all traffic to/from CDE. "
            "(9) Document all network connections and data flows."
        ),
        tags=["pci-dss", "compliance", "cardholder", "segmentation", "firewall"],
        applicability={"compliance": ["PCI-DSS 4.0"]}
    ),
    KnowledgeEntry(
        id="KB009",
        title="HIPAA Network Safeguards",
        source="HIPAA Security Rule / NIST SP 800-66",
        category="Compliance",
        content=(
            "HIPAA requires technical safeguards for electronic Protected Health Information (ePHI). "
            "Network requirements: (1) Implement access controls: unique user IDs, emergency access procedures. "
            "(2) Encrypt ePHI in transit using TLS 1.2+ or IPsec VPN. (3) Audit controls: log all access to "
            "ePHI systems with SIEM integration. (4) Integrity controls: network monitoring for unauthorized "
            "alterations. (5) Transmission security: network segmentation isolating ePHI systems. "
            "(6) Deploy NAC (802.1X) to prevent unauthorized device connections. (7) Implement DLP at network "
            "egress points. (8) Regular vulnerability scanning and penetration testing."
        ),
        tags=["hipaa", "compliance", "ephi", "healthcare", "encryption", "audit"],
        applicability={"compliance": ["HIPAA"]}
    ),
    KnowledgeEntry(
        id="KB010",
        title="Wireless Network Design Best Practices",
        source="Cisco Wireless LAN Design Guide / IEEE 802.11ax",
        category="Wireless",
        content=(
            "Enterprise WLAN design: Conduct RF site survey before deployment. WiFi 6/6E APs should cover "
            "2500-3500 sq ft in office environments. Deploy in channel-layered design: non-overlapping channels "
            "only (1, 6, 11 for 2.4 GHz; all 5/6 GHz channels). AP density: 1 AP per 25-35 users for high-density. "
            "Backhaul: Each AP needs 2.5G or 5G uplink (mGig switches). Use WPA3-Enterprise (802.1X with RADIUS). "
            "Separate SSIDs: Corporate (802.1X), Guest (captive portal), IoT (PSK with isolation). "
            "Deploy wireless controller for central management, RF optimization, and client roaming. "
            "Use Wireless IPS (wIPS) for rogue AP detection."
        ),
        tags=["wireless", "wifi", "802.11ax", "wlan", "ap", "rf", "wpa3"],
        applicability={"security": ["Firewall"]}
    ),
    KnowledgeEntry(
        id="KB011",
        title="Network Monitoring & Observability",
        source="Cisco DNA Center / NIST Cybersecurity Framework",
        category="Operations",
        content=(
            "Implement comprehensive network monitoring: (1) SNMP v3 polling for device health (CPU, memory, "
            "interface utilization). (2) NetFlow/sFlow for traffic analysis and capacity planning. (3) Syslog "
            "centralization with SIEM (Splunk, ELK). (4) Streaming telemetry (gNMI/gRPC) for real-time data. "
            "(5) Synthetic monitoring: IP SLA probes for path health verification. (6) SPAN/TAP for packet "
            "capture and DPI. Deploy out-of-band management network (VLAN 100, 10.0.100.0/24) for device access. "
            "Implement NTP synchronization (Stratum 2+) on all devices. Use TACACS+ for centralized AAA."
        ),
        tags=["monitoring", "snmp", "netflow", "syslog", "telemetry", "observability"],
        applicability={"org_size": ["Medium", "Large", "Enterprise"]}
    ),
    KnowledgeEntry(
        id="KB012",
        title="IPv4 Addressing & Subnetting Strategy",
        source="RFC 1918 / Cisco IP Addressing Guide",
        category="Addressing",
        content=(
            "Use RFC 1918 private addressing with structured allocation: 10.{site}.{vlan}.{host}/24 scheme. "
            "Supernet by function: 10.0.0.0/16 = Headquarters, 10.1.0.0/16 = Branch 1, etc. "
            "Within each site: .10.0/24 = Data VLAN, .20.0/24 = Voice, .30.0/24 = Management, "
            ".100.0/24 = Servers, .200.0/24 = DMZ. Use /30 or /31 for point-to-point links. "
            "Reserve .1 for gateway (HSRP VIP), .2-.3 for HSRP active/standby. Allocate /22 per access "
            "block (~1000 hosts). Document all allocations in IPAM (InfoBlox, NetBox). "
            "Plan for IPv6 dual-stack: use ULA (fd00::/8) internally with GUA for external services."
        ),
        tags=["ipv4", "subnetting", "addressing", "rfc1918", "cidr", "ipam"],
        applicability={"org_size": ["Medium", "Large", "Enterprise"]}
    ),
    KnowledgeEntry(
        id="KB013",
        title="Network Redundancy Protocols Comparison",
        source="IEEE 802.3ad / RFC 5798 / Cisco VSS Guide",
        category="Redundancy",
        content=(
            "Gateway redundancy: HSRP v2 (Cisco proprietary, millisecond failover, preempt support) vs "
            "VRRP v3 (standards-based, multi-vendor). Both provide virtual IP gateway. "
            "Link redundancy: LACP (802.3ad) for link aggregation — minimum 2 links, max 8. Cross-link: "
            "vPC (Nexus), MLAG (Arista), VSS (Catalyst) for dual-homing to two switches. "
            "Layer 2 loop prevention: RSTP (802.1w) for <1s convergence. MST for VLAN-aware spanning tree. "
            "Chassis redundancy: VSS (Catalyst 6800) — two chassis act as one. StackWise-480 for access "
            "(up to 8 switches, 480 Gbps backplane). Recommendation: Use vPC/MLAG at distribution, "
            "LACP everywhere, HSRP at gateways, RSTP as safety net."
        ),
        tags=["redundancy", "hsrp", "vrrp", "lacp", "vpc", "mlag", "spanning-tree"],
        applicability={"fault_tolerance": ["Standard", "High", "Mission Critical"]}
    ),
    KnowledgeEntry(
        id="KB014",
        title="Zero Trust Network Architecture",
        source="NIST SP 800-207 / Forrester ZTX Framework",
        category="Security",
        content=(
            "Zero Trust principles: Never trust, always verify. Micro-segmentation: Use SGTs (Cisco TrustSec) "
            "or NSX micro-firewalls to enforce least-privilege between workloads. Identity-based access: "
            "802.1X with ISE/ClearPass for network admission control. Continuous verification: posture "
            "assessment, device compliance checks, behavioral analytics. East-west traffic inspection: "
            "deploy internal firewalls or distributed enforcement. Software-Defined Perimeter for remote access "
            "(replaces legacy VPN). Encrypt all traffic: MACsec (802.1AE) for LAN, IPsec/TLS for WAN. "
            "Implement DNS security (DoH/DoT). Log everything — full packet capture at trust boundaries."
        ),
        tags=["zero-trust", "microsegmentation", "identity", "802.1x", "nac", "macsec"],
        applicability={"security": ["Zero-Trust", "Firewall", "IDS/IPS"]}
    ),
    KnowledgeEntry(
        id="KB015",
        title="Disaster Recovery Network Design",
        source="NIST SP 800-34 / Uptime Institute Tier Standards",
        category="Resilience",
        content=(
            "DR network design tiers: Tier I (99.67%) — single path, no redundancy. Tier II (99.75%) — "
            "redundant components, single path. Tier III (99.982%) — concurrent maintainability, dual power/cooling. "
            "Tier IV (99.995%) — fault tolerant, fully redundant. For DR: Deploy geographically diverse sites "
            "(>100km apart) connected via dark fiber or DWDM. Use BGP with communities for traffic engineering. "
            "Implement GSLB for application-layer failover. RTO targets: Tier I = 24h, Tier II = 8h, "
            "Tier III = 1h, Tier IV = 0 (continuous). Bandwidth: DR link >= 50% of production inter-site traffic. "
            "Test failover quarterly with documented runbooks."
        ),
        tags=["disaster-recovery", "dr", "resilience", "failover", "gslb", "rto", "rpo"],
        applicability={"fault_tolerance": ["High", "Mission Critical"]}
    ),
    KnowledgeEntry(
        id="KB016",
        title="Campus Network Capacity Planning",
        source="Cisco Campus Network Design Guide",
        category="Performance",
        content=(
            "Capacity planning formulas: Per-user bandwidth = 2-5 Mbps (office), 10-20 Mbps (engineering), "
            "50-100 Mbps (media production). Access uplink ratio: 1:20 oversubscription for general office, "
            "1:4 for engineering. Distribution uplink: aggregate all access uplinks × 0.7 (burst factor). "
            "Core capacity: sum of all distribution uplinks × 0.5 (statistical multiplexing). Internet "
            "bandwidth: 0.5-2 Mbps per user. Growth factor: multiply by 1.5 for 3-year planning horizon. "
            "Switch port density: plan for 1.2 ports per user (desktops, phones, printers). "
            "Wireless backhaul: 2.5G per AP (WiFi 6) or 5G per AP (WiFi 6E)."
        ),
        tags=["capacity", "bandwidth", "planning", "oversubscription", "sizing"],
        applicability={"org_size": ["Medium", "Large", "Enterprise"]}
    ),
    KnowledgeEntry(
        id="KB017",
        title="SOC 2 Type II Network Controls",
        source="AICPA TSC (Trust Services Criteria)",
        category="Compliance",
        content=(
            "SOC 2 network controls for the Security trust principle: (1) CC6.1 — Logical access security: "
            "implement network ACLs, firewall rules, and VPN for remote access. (2) CC6.6 — Restrict transmission "
            "of sensitive data: encryption in transit (TLS 1.2+), DLP at egress. (3) CC7.1 — Detect unauthorized "
            "changes: file integrity monitoring, configuration management. (4) CC7.2 — Monitor for anomalies: "
            "IDS/IPS, SIEM with 90-day log retention. (5) CC8.1 — Change management: formal process for "
            "network changes with approval workflow. Network architecture evidence: maintain up-to-date "
            "network diagrams, device inventories, and firewall rule documentation."
        ),
        tags=["soc2", "compliance", "audit", "controls", "logging"],
        applicability={"compliance": ["SOC 2 Type II"]}
    ),
    KnowledgeEntry(
        id="KB018",
        title="VXLAN/EVPN Fabric Design",
        source="RFC 7348 (VXLAN) / RFC 8365 (EVPN)",
        category="Data Center",
        content=(
            "VXLAN/EVPN provides L2 extension over L3 underlay for data center fabrics. "
            "VXLAN encapsulation adds 50-byte overhead (plan MTU 9214 on fabric). EVPN control plane (MP-BGP) "
            "distributes MAC/IP routes, eliminating flood-and-learn. Design: Leaf switches are VXLAN tunnel "
            "endpoints (VTEPs). Spine switches are BGP route reflectors. Use eBGP underlay with ASN-per-leaf. "
            "EVPN route types: Type-2 (MAC/IP), Type-5 (IP prefix). Implement ARP suppression to reduce "
            "broadcast. Symmetric IRB for inter-VXLAN routing. Use EVPN multi-homing (ESI-LAG) for "
            "active-active server connectivity. Scale: up to 16M VNIs vs 4094 VLANs."
        ),
        tags=["vxlan", "evpn", "fabric", "overlay", "bgp", "vtep", "data-center"],
        applicability={"topology": ["Spine-Leaf (Data Center)"], "traffic": ["High", "Critical"]}
    ),
    KnowledgeEntry(
        id="KB019",
        title="Network Automation & Infrastructure as Code",
        source="Cisco DevNet / Ansible Network Automation Guide",
        category="Operations",
        content=(
            "Automate network operations for consistency and speed. Tools: Ansible (agentless, playbooks), "
            "Terraform (infrastructure provisioning), Nornir (Python framework), NAPALM (vendor-neutral API). "
            "Best practices: (1) Store configs in Git (version control). (2) Use Jinja2 templates for "
            "consistent device configs. (3) Implement CI/CD pipeline: lint → test → stage → deploy. "
            "(4) Use YANG models with NETCONF/RESTCONF for structured configuration. (5) Automated compliance "
            "checks: Batfish for network verification. (6) Deploy NetBox as source of truth for IPAM/DCIM. "
            "ROI: 60-80% reduction in provisioning time, 90% fewer configuration errors."
        ),
        tags=["automation", "ansible", "terraform", "devnet", "cicd", "iac"],
        applicability={"org_size": ["Large", "Enterprise"], "scalability": ["High Growth", "Hyper Growth"]}
    ),
    KnowledgeEntry(
        id="KB020",
        title="WAN Edge & Internet Connectivity Design",
        source="Cisco WAN Design Guide / MEF Carrier Ethernet",
        category="WAN",
        content=(
            "WAN edge design: Deploy redundant WAN routers (active/standby) with diverse carrier connections. "
            "Connectivity options: (1) MPLS L3VPN — guaranteed SLA, 99.99% availability, $500-2000/Mbps. "
            "(2) DIA (Direct Internet Access) — best effort, $10-50/Mbps. (3) SD-WAN overlay — combines both. "
            "Sizing: Primary circuit >= 80% of peak demand. Backup >= 50% of primary. "
            "BGP design: Obtain PI address space and ASN for multi-homing. Implement route filtering, "
            "prefix limits, and RTBH for DDoS mitigation. Use dual-stack (IPv4 + IPv6) on all external links. "
            "Deploy redundant DNS (primary + secondary in different sites)."
        ),
        tags=["wan", "internet", "bgp", "mpls", "carrier", "multihoming"],
        applicability={"org_size": ["Medium", "Large", "Enterprise"]}
    ),
    KnowledgeEntry(
        id="KB021",
        title="Collapsed Core Design for Medium Networks",
        source="Cisco Campus LAN Design Fundamentals",
        category="Architecture",
        content=(
            "For medium networks (200-2000 users), a collapsed core combines core and distribution into "
            "a single layer, reducing cost and complexity. Deploy 2 high-performance L3 switches "
            "(e.g., Catalyst 9500) as core/distribution. Connect all access switches via redundant 10G "
            "uplinks to both core switches. Use VSS or StackWise-Virtual to simplify management. "
            "Inter-VLAN routing occurs at the collapsed core. Scale limit: when the number of access "
            "switches exceeds 40 or STP domain becomes too large, migrate to full 3-tier. "
            "Cost savings: 30-40% less than full 3-tier for same coverage."
        ),
        tags=["collapsed-core", "medium", "campus", "cost-effective", "l3-switch"],
        applicability={"org_size": ["Medium"], "topology": ["Collapsed Core"]}
    ),
    KnowledgeEntry(
        id="KB022",
        title="Network Load Balancing Architecture",
        source="F5 BIG-IP Design Guide / Citrix ADC Best Practices",
        category="Performance",
        content=(
            "Deploy load balancers in one-arm or inline mode. Inline (routed mode): LB sits in the data path "
            "between clients and servers — simpler but creates bottleneck. One-arm (DSR mode): LB handles "
            "inbound only, servers respond directly — better throughput but complex. HA: Active/standby pair "
            "with connection mirroring. Algorithms: Round-robin (simple), Least connections (dynamic), "
            "Weighted (capacity-aware), IP hash (session persistence). Health checks: L3 (ICMP), L4 (TCP port), "
            "L7 (HTTP GET with content verification). Deploy GSLB across sites for DR failover. "
            "SSL offload: terminate TLS at LB to reduce server CPU load by 50-70%."
        ),
        tags=["load-balancer", "f5", "citrix", "ha", "ssl-offload", "gslb"],
        applicability={"traffic": ["High", "Critical"]}
    ),
    KnowledgeEntry(
        id="KB023",
        title="IoT Network Segmentation",
        source="NIST SP 1800-26 / Cisco IoT Architecture",
        category="Security",
        content=(
            "IoT devices introduce significant security risk due to limited patching and weak authentication. "
            "Design: Isolate all IoT devices in dedicated VLANs with restricted inter-VLAN access. "
            "Deploy IoT gateway/controller at the distribution layer for protocol translation. "
            "Use 802.1X with MAB (MAC Authentication Bypass) for IoT device onboarding. "
            "Implement micro-segmentation: building automation (VLAN 400), security cameras (VLAN 410), "
            "medical devices (VLAN 420). Apply strict ACLs: IoT → Internet (deny), IoT → Management server "
            "(permit specific ports only). Deploy NAC for device profiling and compliance checking. "
            "Monitor IoT traffic with dedicated IDS sensors for anomaly detection."
        ),
        tags=["iot", "segmentation", "security", "802.1x", "vlan", "nac"],
        applicability={"security": ["Firewall", "IDS/IPS"]}
    ),
    KnowledgeEntry(
        id="KB024",
        title="Network Cost Optimization Strategies",
        source="Gartner Network Cost Reduction Guide",
        category="Cost",
        content=(
            "Strategies to reduce network TCO: (1) SD-WAN migration: replace MPLS with Internet + SD-WAN "
            "for 40-60% WAN savings. (2) Open networking: use whitebox switches (Edgecore, Dell) with SONiC "
            "for 50% hardware savings in data centers. (3) Rightsize circuits: use NetFlow data to identify "
            "overprovisioned links. (4) Consolidate vendors: multi-vendor adds 15-25% management overhead. "
            "(5) Cloud-managed networking: Meraki/Mist for branch (reduces on-site IT by 60%). "
            "(6) Power optimization: use power scheduling for APs and switches (save 20% energy). "
            "(7) Automation: reduce MTTR by 50% and provisioning time by 80% with Ansible/Terraform. "
            "Typical enterprise network cost breakdown: Hardware 35%, Circuits 30%, Staff 25%, Software 10%."
        ),
        tags=["cost", "tco", "optimization", "sdwan", "opex", "capex"],
        applicability={"org_size": ["Small", "Medium", "Large", "Enterprise"]}
    ),
    KnowledgeEntry(
        id="KB025",
        title="BGP Routing Design for Enterprise",
        source="RFC 4271 / Cisco BGP Design Guide",
        category="Routing",
        content=(
            "BGP deployment in enterprise: Use eBGP for external (Internet/MPLS) and iBGP for internal "
            "route distribution. Design: (1) Obtain AS number from RIR (public or private 64512-65534). "
            "(2) Implement prefix filtering: only advertise owned prefixes, filter bogons inbound. "
            "(3) Use BGP communities for traffic engineering (e.g., local-pref for primary/backup path). "
            "(4) Deploy route reflectors for iBGP scalability (2 RRs per cluster). "
            "(5) Implement RPKI for route origin validation. (6) Use BFD for sub-second failure detection. "
            "(7) Set maximum prefix limits to prevent route leaks. "
            "For data center: eBGP underlay with unique ASN per leaf switch (RFC 7938)."
        ),
        tags=["bgp", "routing", "ebgp", "ibgp", "prefix-filtering", "rpki"],
        applicability={"topology": ["Spine-Leaf (Data Center)", "Full Mesh"]}
    ),
    KnowledgeEntry(
        id="KB026",
        title="Network Segmentation with VLANs and VRFs",
        source="IEEE 802.1Q / RFC 4364",
        category="Architecture",
        content=(
            "VLAN design best practices: (1) Limit broadcast domain to 250 hosts max (/24 subnet). "
            "(2) Use structured VLAN numbering: 10-99 = Data, 100-199 = Management, 200-299 = Servers, "
            "300-399 = Voice, 400-499 = IoT, 500-599 = DMZ, 900-999 = Guest. "
            "(3) Prune VLANs on trunks — only allow needed VLANs per link. "
            "(4) Use VRF (Virtual Routing and Forwarding) for L3 isolation between tenants or security zones. "
            "VRF-Lite: separate routing tables on a single router without MPLS. "
            "(5) Implement private VLANs for server isolation within the same subnet. "
            "(6) VLAN 1 should be unused (native VLAN security). "
            "Scale: up to 4094 VLANs per switch (use VXLAN for larger scale)."
        ),
        tags=["vlan", "vrf", "segmentation", "802.1q", "broadcast-domain", "isolation"],
        applicability={"org_size": ["Medium", "Large", "Enterprise"]}
    ),
    KnowledgeEntry(
        id="KB027",
        title="Fat-Tree (k-ary) Topology for Large-Scale Networks",
        source="Al-Fares et al. (SIGCOMM 2008) / Google Jupiter",
        category="Data Center",
        content=(
            "Fat-tree topology provides full bisection bandwidth using commodity switches. "
            "A k-ary fat-tree: k pods, each with k/2 aggregation and k/2 edge switches. "
            "(k/2)² core switches. Supports k³/4 hosts. For k=48 (typical): 27,648 hosts with "
            "full 1:1 bandwidth. ECMP across all paths provides load balancing. Cost: 3-5x cheaper "
            "than equivalent chassis-based designs. Google's Jupiter network uses this approach for "
            "1+ Pbps aggregate bandwidth. Key: all switches are identical (modular ops), "
            "all paths are equal-cost (simplified routing). Use ECMP with flowlet-based hashing "
            "for optimal load distribution."
        ),
        tags=["fat-tree", "clos", "data-center", "ecmp", "bisection-bandwidth", "scale"],
        applicability={"topology": ["Fat-Tree (k-ary)"], "traffic": ["Critical"]}
    ),
    KnowledgeEntry(
        id="KB028",
        title="ISO 27001 Network Security Controls",
        source="ISO/IEC 27001:2022 Annex A",
        category="Compliance",
        content=(
            "ISO 27001 Annex A network controls: A.8.20 — Network security: segment networks by trust level "
            "with firewalls and ACLs. A.8.21 — Security of network services: define SLAs with providers, "
            "implement monitoring. A.8.22 — Segregation in networks: isolate critical systems, use DMZ. "
            "A.8.23 — Web filtering: deploy URL filtering and DNS security. A.8.24 — Use of cryptography: "
            "encrypt sensitive data in transit (TLS 1.2+, IPsec). A.8.26 — Application security requirements: "
            "WAF for web applications. A.5.23 — Information security for cloud services. "
            "Implementation: Maintain network security policy, conduct annual risk assessments, "
            "perform quarterly vulnerability scans, document all network changes."
        ),
        tags=["iso27001", "compliance", "controls", "risk-assessment", "segmentation"],
        applicability={"compliance": ["ISO 27001"]}
    ),
    KnowledgeEntry(
        id="KB029",
        title="Ring Topology with Redundant Paths",
        source="IEEE 802.17 (RPR) / Cisco Metro Ethernet Design",
        category="Architecture",
        content=(
            "Ring topology provides inherent redundancy through dual counter-rotating paths. "
            "Modern ring designs: Use RSTP/MSTP for L2 rings with <1s convergence. For L3: "
            "OSPF/IS-IS with BFD for 50ms failover. G.8032 (ERPS) for carrier-grade Ethernet rings "
            "with 50ms protection switching. Design rules: Maximum 16 nodes per ring for optimal "
            "convergence. Use dual rings for mission-critical paths. Bandwidth: each link must carry "
            "full ring traffic during single-link failure. Best for: metro/campus interconnection, "
            "industrial networks, and sites arranged in geographical loops. "
            "Avoid for: high-density data centers (use spine-leaf instead)."
        ),
        tags=["ring", "redundancy", "rstp", "erps", "metro", "dual-ring"],
        applicability={"topology": ["Redundant Ring"]}
    ),
    KnowledgeEntry(
        id="KB030",
        title="NIST 800-53 Network Security Controls",
        source="NIST SP 800-53 Rev. 5",
        category="Compliance",
        content=(
            "Key NIST 800-53 network controls: SC-7 Boundary Protection: implement managed interfaces "
            "at network boundaries (firewalls, proxies). SC-8 Transmission Confidentiality: encrypt all "
            "sensitive data in transit. AC-4 Information Flow Enforcement: control information flows "
            "between security domains using firewall policies. SI-4 System Monitoring: deploy IDS/IPS "
            "at network boundaries and key internal segments. SC-22 Architecture and Provisioning: "
            "fault-tolerant name resolution services. AU-3 Content of Audit Records: log source, "
            "destination, timestamp, outcome for network events. SC-39 Process Isolation: use network "
            "segmentation to support process isolation. CM-7 Least Functionality: disable unnecessary "
            "network services and protocols on all devices."
        ),
        tags=["nist", "800-53", "compliance", "federal", "boundary-protection", "monitoring"],
        applicability={"compliance": ["NIST 800-53"]}
    ),
]


# ──────────────────────────────────────────────────────────────
# TF-IDF Retrieval Engine
# ──────────────────────────────────────────────────────────────

class RAGEngine:
    """Simple TF-IDF based retrieval engine for the knowledge base."""

    def __init__(self, knowledge_base: List[KnowledgeEntry] = None):
        self.kb = knowledge_base or KNOWLEDGE_BASE
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize and normalize text."""
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s\-/]', ' ', text)
        tokens = text.split()
        # Remove very short tokens
        return [t for t in tokens if len(t) > 2]

    def _build_index(self):
        """Build TF-IDF index over the knowledge base."""
        self.doc_tokens: List[List[str]] = []
        self.df: Dict[str, int] = {}  # document frequency

        for entry in self.kb:
            combined = f"{entry.title} {entry.content} {' '.join(entry.tags)}"
            tokens = self._tokenize(combined)
            self.doc_tokens.append(tokens)
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.df[token] = self.df.get(token, 0) + 1

        self.n_docs = len(self.kb)

    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        """Compute term frequency for a token list."""
        tf: Dict[str, float] = {}
        total = len(tokens)
        if total == 0:
            return tf
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1
        for t in tf:
            tf[t] = tf[t] / total
        return tf

    def _compute_tfidf(self, tokens: List[str]) -> Dict[str, float]:
        """Compute TF-IDF scores."""
        tf = self._compute_tf(tokens)
        tfidf: Dict[str, float] = {}
        for t, freq in tf.items():
            idf = math.log((self.n_docs + 1) / (self.df.get(t, 0) + 1)) + 1
            tfidf[t] = freq * idf
        return tfidf

    def _cosine_similarity(self, vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        """Compute cosine similarity between two sparse vectors."""
        common_keys = set(vec_a.keys()) & set(vec_b.keys())
        if not common_keys:
            return 0.0
        dot = sum(vec_a[k] * vec_b[k] for k in common_keys)
        norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
        norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def retrieve(self, query: str, top_k: int = 5,
                 context: Dict[str, any] = None) -> List[Tuple[KnowledgeEntry, float]]:
        """
        Retrieve top-k relevant knowledge entries for a query.

        Args:
            query: Natural language query or keywords
            top_k: Number of results to return
            context: Optional context dict with keys like 'org_size', 'topology',
                     'fault_tolerance', 'security', 'compliance', 'traffic'

        Returns:
            List of (KnowledgeEntry, relevance_score) tuples
        """
        query_tokens = self._tokenize(query)

        # Add context-based tokens
        if context:
            for key, value in context.items():
                if isinstance(value, list):
                    for v in value:
                        query_tokens.extend(self._tokenize(str(v)))
                else:
                    query_tokens.extend(self._tokenize(str(value)))

        query_tfidf = self._compute_tfidf(query_tokens)

        scores = []
        for i, entry in enumerate(self.kb):
            doc_tfidf = self._compute_tfidf(self.doc_tokens[i])
            sim = self._cosine_similarity(query_tfidf, doc_tfidf)

            # Boost score based on applicability match
            if context:
                boost = 0.0
                for key, values in entry.applicability.items():
                    ctx_val = context.get(key)
                    if ctx_val:
                        if isinstance(ctx_val, list):
                            for cv in ctx_val:
                                if str(cv) in values:
                                    boost += 0.15
                        elif str(ctx_val) in values:
                            boost += 0.15
                sim += boost

            scores.append((entry, round(sim, 4)))

        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def get_recommendations(self, requirements) -> List[Tuple[KnowledgeEntry, float]]:
        """
        Get recommendations based on NetworkRequirements object.
        Builds a contextual query from requirements.
        """
        # Build query from requirements
        query_parts = [
            requirements.org_size.value,
            requirements.traffic_load.value,
            requirements.fault_tolerance.value,
            requirements.scalability.value,
            requirements.preferred_topology.value,
        ]
        query_parts.extend(requirements.security_features)
        query_parts.extend(requirements.compliance_frameworks)

        if requirements.wireless_required:
            query_parts.append("wireless wifi access point")
        if requirements.dmz_required:
            query_parts.append("dmz demilitarized zone")
        if requirements.sd_wan:
            query_parts.append("sd-wan software-defined wan")
        if requirements.redundant_wan:
            query_parts.append("redundant wan dual circuit")

        query = " ".join(query_parts)

        context = {
            "org_size": [requirements.org_size.value.split("(")[0].strip()],
            "topology": [requirements.preferred_topology.value],
            "fault_tolerance": [requirements.fault_tolerance.value.split("(")[0].strip()],
            "security": requirements.security_features,
            "compliance": requirements.compliance_frameworks,
            "traffic": [requirements.traffic_load.value.split("(")[0].strip()],
        }

        return self.retrieve(query, top_k=8, context=context)
