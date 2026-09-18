"""
network_models.py — Industry-grade device catalog, cost models, and data structures
for enterprise network topology design.

Includes real-world device specifications from Cisco, Juniper, Arista, Palo Alto,
and F5 product lines with accurate port counts, throughput, pricing, and MTBF data.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict
import random


# ──────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────

class DeviceType(Enum):
    CORE_ROUTER = "Core Router"
    DISTRIBUTION_ROUTER = "Distribution Router"
    L3_SWITCH = "L3 Switch"
    L2_SWITCH = "L2 Switch"
    FIREWALL = "Firewall"
    LOAD_BALANCER = "Load Balancer"
    SERVER = "Server"
    WIRELESS_AP = "Wireless AP"
    WIRELESS_CONTROLLER = "Wireless Controller"
    IDS_IPS = "IDS/IPS"
    WAN_OPTIMIZER = "WAN Optimizer"
    SDN_CONTROLLER = "SDN Controller"
    INTERNET_GATEWAY = "Internet Gateway"
    DMZ_SWITCH = "DMZ Switch"
    STORAGE = "Storage Array"


class NetworkTier(Enum):
    CORE = "Core"
    DISTRIBUTION = "Distribution"
    ACCESS = "Access"
    DMZ = "DMZ"
    MANAGEMENT = "Management"
    WAN_EDGE = "WAN Edge"
    DATA_CENTER = "Data Center"


class LinkMedia(Enum):
    COPPER_1G = "Cat6a (1 Gbps)"
    FIBER_10G = "OM4 MMF (10 Gbps)"
    FIBER_25G = "OM4 MMF (25 Gbps)"
    FIBER_40G = "OS2 SMF (40 Gbps)"
    FIBER_100G = "OS2 SMF (100 Gbps)"
    FIBER_400G = "OS2 SMF (400 Gbps)"
    WIRELESS = "802.11ax (WiFi 6E)"


class RoutingProtocol(Enum):
    OSPF = "OSPF"
    BGP = "BGP"
    EIGRP = "EIGRP"
    IS_IS = "IS-IS"
    STATIC = "Static"
    SD_WAN = "SD-WAN (VXLAN/EVPN)"


class RedundancyProtocol(Enum):
    HSRP = "HSRP"
    VRRP = "VRRP"
    VSS = "VSS"
    VPC = "vPC"
    MLAG = "MLAG"
    STACK = "StackWise"
    LACP = "LACP"


class ComplianceFramework(Enum):
    PCI_DSS = "PCI-DSS 4.0"
    HIPAA = "HIPAA"
    SOC2 = "SOC 2 Type II"
    ISO_27001 = "ISO 27001"
    NIST = "NIST 800-53"
    GDPR = "GDPR"


class TopologyType(Enum):
    AUTO = "AI Recommended"
    STAR = "Star"
    MESH = "Full Mesh"
    PARTIAL_MESH = "Partial Mesh"
    THREE_TIER = "3-Tier Hierarchical"
    SPINE_LEAF = "Spine-Leaf (Data Center)"
    HYBRID = "Hybrid (Star + Mesh Core)"
    RING = "Redundant Ring"
    FAT_TREE = "Fat-Tree (k-ary)"
    COLLAPSED_CORE = "Collapsed Core"


class OrgSize(Enum):
    SMALL = "Small (10-50 users)"
    MEDIUM = "Medium (50-500 users)"
    LARGE = "Large (500-5000 users)"
    ENTERPRISE = "Enterprise (5000+ users)"


class TrafficLoad(Enum):
    LOW = "Low (< 1 Gbps)"
    MEDIUM = "Medium (1-10 Gbps)"
    HIGH = "High (10-100 Gbps)"
    CRITICAL = "Critical (100+ Gbps)"


class FaultTolerance(Enum):
    BASIC = "Basic (99.0%)"
    STANDARD = "Standard (99.9%)"
    HIGH = "High (99.99%)"
    MISSION_CRITICAL = "Mission Critical (99.999%)"


class ScalabilityNeed(Enum):
    STATIC = "Static (No growth)"
    MODERATE = "Moderate (10-20% yearly)"
    HIGH = "High Growth (30-50% yearly)"
    HYPER = "Hyper Growth (50%+ yearly)"


# ──────────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────────

@dataclass
class DeviceSpec:
    """Specification for a network device model."""
    model: str
    vendor: str
    device_type: DeviceType
    ports_1g: int = 0
    ports_10g: int = 0
    ports_25g: int = 0
    ports_40g: int = 0
    ports_100g: int = 0
    throughput_gbps: float = 0.0
    pps_mpps: float = 0.0  # million packets per second
    price_usd: float = 0.0
    annual_maintenance_usd: float = 0.0
    power_watts: int = 0
    mtbf_hours: int = 100_000
    rack_units: int = 1
    supports_ha: bool = False
    supports_stacking: bool = False
    max_vlans: int = 4094
    features: List[str] = field(default_factory=list)


@dataclass
class LinkSpec:
    """Specification for a network link type."""
    media: LinkMedia
    bandwidth_gbps: float
    cost_per_meter: float
    max_distance_m: int
    latency_us_per_km: float  # microseconds per km


@dataclass
class VLANConfig:
    """VLAN assignment."""
    vlan_id: int
    name: str
    subnet: str
    gateway: str
    purpose: str
    qos_priority: int = 0  # 0-7, DSCP mapping


@dataclass
class NetworkRequirements:
    """User-specified network requirements."""
    org_size: OrgSize = OrgSize.MEDIUM
    num_departments: int = 5
    num_users: int = 200
    traffic_load: TrafficLoad = TrafficLoad.MEDIUM
    budget_usd: float = 500_000
    fault_tolerance: FaultTolerance = FaultTolerance.STANDARD
    scalability: ScalabilityNeed = ScalabilityNeed.MODERATE
    security_features: List[str] = field(default_factory=lambda: ["Firewall", "VPN"])
    preferred_topology: TopologyType = TopologyType.AUTO
    compliance_frameworks: List[str] = field(default_factory=list)
    wan_sites: int = 1
    wireless_required: bool = True
    dmz_required: bool = True
    redundant_wan: bool = False
    sd_wan: bool = False


@dataclass
class NetworkNode:
    """A node in the network topology graph."""
    id: str
    label: str
    device_type: DeviceType
    tier: NetworkTier
    device_spec: Optional[DeviceSpec] = None
    ip_address: str = ""
    subnet: str = ""
    vlan_ids: List[int] = field(default_factory=list)
    redundancy_group: str = ""
    x: float = 0.0
    y: float = 0.0
    is_redundant: bool = False


@dataclass
class NetworkLink:
    """A link between two nodes."""
    source: str
    target: str
    link_spec: Optional[LinkSpec] = None
    bandwidth_gbps: float = 1.0
    is_redundant: bool = False
    protocol: str = ""
    cost: float = 0.0


@dataclass
class TopologyMetrics:
    """Computed metrics for a network topology."""
    total_devices: int = 0
    total_links: int = 0
    total_cost_capex: float = 0.0
    annual_opex: float = 0.0
    tco_3yr: float = 0.0
    tco_5yr: float = 0.0
    power_total_watts: int = 0
    annual_power_cost: float = 0.0
    availability_percent: float = 99.0
    availability_nines: str = "2 nines"
    max_hops: int = 0
    avg_path_length: float = 0.0
    redundancy_score: float = 0.0  # 0-100
    graph_connectivity: float = 0.0
    single_points_of_failure: int = 0
    throughput_capacity_gbps: float = 0.0
    scalability_score: float = 0.0  # 0-100
    security_score: float = 0.0  # 0-100
    compliance_status: Dict[str, str] = field(default_factory=dict)
    rack_units_total: int = 0
    estimated_deploy_weeks: int = 4


# ──────────────────────────────────────────────────────────────
# Device Catalog — Real-world device models
# ──────────────────────────────────────────────────────────────

DEVICE_CATALOG: Dict[str, List[DeviceSpec]] = {
    "core_router": [
        DeviceSpec(
            model="Cisco Catalyst 8500-12X",
            vendor="Cisco", device_type=DeviceType.CORE_ROUTER,
            ports_10g=12, ports_100g=2,
            throughput_gbps=240, pps_mpps=350,
            price_usd=85_000, annual_maintenance_usd=12_000,
            power_watts=750, mtbf_hours=300_000, rack_units=2,
            supports_ha=True,
            features=["OSPF", "BGP", "MPLS", "SD-WAN", "NetFlow", "QoS", "IPv6"]
        ),
        DeviceSpec(
            model="Juniper MX204",
            vendor="Juniper", device_type=DeviceType.CORE_ROUTER,
            ports_10g=8, ports_100g=4,
            throughput_gbps=400, pps_mpps=500,
            price_usd=95_000, annual_maintenance_usd=14_000,
            power_watts=550, mtbf_hours=350_000, rack_units=1,
            supports_ha=True,
            features=["OSPF", "BGP", "IS-IS", "MPLS", "SR-MPLS", "EVPN", "Telemetry"]
        ),
        DeviceSpec(
            model="Arista 7280R3",
            vendor="Arista", device_type=DeviceType.CORE_ROUTER,
            ports_10g=24, ports_100g=6,
            throughput_gbps=600, pps_mpps=800,
            price_usd=120_000, annual_maintenance_usd=18_000,
            power_watts=650, mtbf_hours=400_000, rack_units=1,
            supports_ha=True,
            features=["BGP", "OSPF", "VXLAN", "EVPN", "SR", "CloudVision", "gNMI"]
        ),
    ],
    "distribution_switch": [
        DeviceSpec(
            model="Cisco Catalyst 9500-48Y4C",
            vendor="Cisco", device_type=DeviceType.L3_SWITCH,
            ports_1g=48, ports_10g=4, ports_25g=4,
            throughput_gbps=176, pps_mpps=260,
            price_usd=32_000, annual_maintenance_usd=4_800,
            power_watts=450, mtbf_hours=250_000, rack_units=1,
            supports_ha=True, supports_stacking=True,
            features=["OSPF", "BGP", "VXLAN", "SD-Access", "StackWise-Virtual", "MACsec"]
        ),
        DeviceSpec(
            model="Juniper EX4650-48Y",
            vendor="Juniper", device_type=DeviceType.L3_SWITCH,
            ports_25g=48, ports_100g=8,
            throughput_gbps=240, pps_mpps=360,
            price_usd=35_000, annual_maintenance_usd=5_200,
            power_watts=400, mtbf_hours=260_000, rack_units=1,
            supports_ha=True, supports_stacking=True,
            features=["OSPF", "BGP", "EVPN-VXLAN", "Virtual Chassis", "Automation"]
        ),
        DeviceSpec(
            model="Arista 7050X4-32",
            vendor="Arista", device_type=DeviceType.L3_SWITCH,
            ports_25g=32, ports_100g=4,
            throughput_gbps=320, pps_mpps=450,
            price_usd=38_000, annual_maintenance_usd=5_700,
            power_watts=380, mtbf_hours=280_000, rack_units=1,
            supports_ha=True, supports_stacking=True,
            features=["BGP", "OSPF", "VXLAN", "MLAG", "CloudVision", "ZTP"]
        ),
    ],
    "access_switch": [
        DeviceSpec(
            model="Cisco Catalyst 9300-48UXM",
            vendor="Cisco", device_type=DeviceType.L2_SWITCH,
            ports_1g=48, ports_10g=4,
            throughput_gbps=32, pps_mpps=48,
            price_usd=8_500, annual_maintenance_usd=1_200,
            power_watts=1100, mtbf_hours=200_000, rack_units=1,
            supports_stacking=True,
            features=["PoE+", "StackWise-480", "DNA Center", "TrustSec", "mGig"]
        ),
        DeviceSpec(
            model="Juniper EX3400-48P",
            vendor="Juniper", device_type=DeviceType.L2_SWITCH,
            ports_1g=48, ports_10g=4,
            throughput_gbps=24, pps_mpps=36,
            price_usd=6_800, annual_maintenance_usd=1_000,
            power_watts=900, mtbf_hours=180_000, rack_units=1,
            supports_stacking=True,
            features=["PoE+", "Virtual Chassis", "802.1X", "Storm Control"]
        ),
        DeviceSpec(
            model="Arista 720XP-48ZC2",
            vendor="Arista", device_type=DeviceType.L2_SWITCH,
            ports_1g=48, ports_10g=4,
            throughput_gbps=28, pps_mpps=42,
            price_usd=7_200, annual_maintenance_usd=1_080,
            power_watts=950, mtbf_hours=200_000, rack_units=1,
            supports_stacking=True,
            features=["PoE++", "CloudVision", "802.1X", "MLAG", "ZTP"]
        ),
    ],
    "firewall": [
        DeviceSpec(
            model="Palo Alto PA-5260",
            vendor="Palo Alto", device_type=DeviceType.FIREWALL,
            ports_1g=12, ports_10g=4, ports_40g=4,
            throughput_gbps=72, pps_mpps=30,
            price_usd=120_000, annual_maintenance_usd=25_000,
            power_watts=600, mtbf_hours=200_000, rack_units=2,
            supports_ha=True,
            features=["NGFW", "IPS", "URL Filtering", "WildFire", "GlobalProtect", "Zero Trust"]
        ),
        DeviceSpec(
            model="Fortinet FortiGate 600F",
            vendor="Fortinet", device_type=DeviceType.FIREWALL,
            ports_1g=16, ports_10g=4, ports_25g=4,
            throughput_gbps=80, pps_mpps=55,
            price_usd=65_000, annual_maintenance_usd=15_000,
            power_watts=450, mtbf_hours=220_000, rack_units=1,
            supports_ha=True,
            features=["NGFW", "IPS", "SD-WAN", "SSL Inspection", "ZTNA", "FortiGuard AI"]
        ),
        DeviceSpec(
            model="Cisco Secure Firewall 3120",
            vendor="Cisco", device_type=DeviceType.FIREWALL,
            ports_1g=8, ports_10g=8,
            throughput_gbps=38, pps_mpps=25,
            price_usd=55_000, annual_maintenance_usd=12_000,
            power_watts=500, mtbf_hours=190_000, rack_units=1,
            supports_ha=True,
            features=["NGFW", "IPS", "AMP", "Umbrella", "SecureX", "Snort 3"]
        ),
    ],
    "load_balancer": [
        DeviceSpec(
            model="F5 BIG-IP i5800",
            vendor="F5", device_type=DeviceType.LOAD_BALANCER,
            ports_1g=8, ports_10g=4,
            throughput_gbps=40,
            price_usd=80_000, annual_maintenance_usd=16_000,
            power_watts=400, mtbf_hours=180_000, rack_units=1,
            supports_ha=True,
            features=["L4/L7 LB", "SSL Offload", "WAF", "GSLB", "iRules", "APM"]
        ),
        DeviceSpec(
            model="Citrix ADC MPX 8900",
            vendor="Citrix", device_type=DeviceType.LOAD_BALANCER,
            ports_1g=8, ports_10g=4,
            throughput_gbps=50,
            price_usd=70_000, annual_maintenance_usd=14_000,
            power_watts=350, mtbf_hours=200_000, rack_units=1,
            supports_ha=True,
            features=["L4/L7 LB", "SSL Offload", "GSLB", "WAF", "Bot Management"]
        ),
    ],
    "wireless_controller": [
        DeviceSpec(
            model="Cisco Catalyst 9800-80",
            vendor="Cisco", device_type=DeviceType.WIRELESS_CONTROLLER,
            ports_10g=4,
            throughput_gbps=80,
            price_usd=45_000, annual_maintenance_usd=6_700,
            power_watts=350, mtbf_hours=200_000, rack_units=2,
            supports_ha=True,
            features=["WiFi 6E", "AI/ML Analytics", "DNA Spaces", "CleanAir Pro", "WIPS"]
        ),
    ],
    "wireless_ap": [
        DeviceSpec(
            model="Cisco Catalyst 9136AXI",
            vendor="Cisco", device_type=DeviceType.WIRELESS_AP,
            ports_1g=2,
            throughput_gbps=5.38,
            price_usd=1_800, annual_maintenance_usd=200,
            power_watts=30, mtbf_hours=150_000, rack_units=0,
            features=["WiFi 6E", "Tri-band", "OFDMA", "MU-MIMO", "BLE", "USB"]
        ),
    ],
    "ids_ips": [
        DeviceSpec(
            model="Cisco Secure IPS 4345",
            vendor="Cisco", device_type=DeviceType.IDS_IPS,
            ports_1g=8, ports_10g=2,
            throughput_gbps=6, pps_mpps=4,
            price_usd=35_000, annual_maintenance_usd=8_000,
            power_watts=350, mtbf_hours=180_000, rack_units=1,
            supports_ha=True,
            features=["IPS", "IDS", "Threat Intelligence", "Snort 3", "Encrypted Visibility"]
        ),
    ],
    "wan_optimizer": [
        DeviceSpec(
            model="Cisco Catalyst SD-WAN (vEdge 2000)",
            vendor="Cisco", device_type=DeviceType.WAN_OPTIMIZER,
            ports_1g=4, ports_10g=2,
            throughput_gbps=10,
            price_usd=18_000, annual_maintenance_usd=3_600,
            power_watts=200, mtbf_hours=180_000, rack_units=1,
            supports_ha=True,
            features=["SD-WAN", "VXLAN", "App-Aware Routing", "DPI", "ZTP", "TLOC"]
        ),
    ],
    "sdn_controller": [
        DeviceSpec(
            model="Cisco DNA Center Appliance",
            vendor="Cisco", device_type=DeviceType.SDN_CONTROLLER,
            ports_10g=2,
            throughput_gbps=10,
            price_usd=200_000, annual_maintenance_usd=40_000,
            power_watts=800, mtbf_hours=200_000, rack_units=1,
            features=["Intent-Based Networking", "AI/ML", "Assurance", "Automation", "ISE Integration"]
        ),
    ],
}


# ──────────────────────────────────────────────────────────────
# Link Specifications
# ──────────────────────────────────────────────────────────────

LINK_SPECS: Dict[str, LinkSpec] = {
    "copper_1g": LinkSpec(LinkMedia.COPPER_1G, 1.0, 0.50, 100, 5.0),
    "fiber_10g": LinkSpec(LinkMedia.FIBER_10G, 10.0, 2.50, 400, 4.9),
    "fiber_25g": LinkSpec(LinkMedia.FIBER_25G, 25.0, 4.00, 300, 4.9),
    "fiber_40g": LinkSpec(LinkMedia.FIBER_40G, 40.0, 8.00, 10_000, 4.9),
    "fiber_100g": LinkSpec(LinkMedia.FIBER_100G, 100.0, 15.00, 40_000, 4.9),
    "fiber_400g": LinkSpec(LinkMedia.FIBER_400G, 400.0, 45.00, 10_000, 4.9),
    "wireless": LinkSpec(LinkMedia.WIRELESS, 2.4, 0.0, 30, 0.0),
}


# ──────────────────────────────────────────────────────────────
# Standard VLAN Templates
# ──────────────────────────────────────────────────────────────

VLAN_TEMPLATES = {
    "management": VLANConfig(100, "MGMT", "10.0.100.0/24", "10.0.100.1", "Network Management", 7),
    "servers": VLANConfig(200, "SERVERS", "10.0.200.0/24", "10.0.200.1", "Server Farm", 6),
    "voip": VLANConfig(300, "VOIP", "10.0.30.0/24", "10.0.30.1", "Voice over IP", 5),
    "data": VLANConfig(10, "DATA", "10.0.10.0/24", "10.0.10.1", "General Data", 3),
    "guest": VLANConfig(900, "GUEST", "10.0.90.0/24", "10.0.90.1", "Guest WiFi", 0),
    "iot": VLANConfig(400, "IOT", "10.0.40.0/24", "10.0.40.1", "IoT Devices", 1),
    "dmz": VLANConfig(500, "DMZ", "172.16.0.0/24", "172.16.0.1", "Demilitarized Zone", 4),
    "security": VLANConfig(600, "SECURITY", "10.0.60.0/24", "10.0.60.1", "Security Cameras", 2),
    "wireless": VLANConfig(700, "WIRELESS", "10.0.70.0/24", "10.0.70.1", "Corporate WiFi", 3),
    "backup": VLANConfig(800, "BACKUP", "10.0.80.0/24", "10.0.80.1", "Backup Network", 1),
}


# ──────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────

def select_device(category: str, budget_factor: float = 1.0) -> DeviceSpec:
    """Select a device from the catalog based on budget factor (0.0 = cheapest, 1.0 = most expensive)."""
    devices = DEVICE_CATALOG.get(category, [])
    if not devices:
        raise ValueError(f"Unknown device category: {category}")
    sorted_devices = sorted(devices, key=lambda d: d.price_usd)
    idx = min(int(budget_factor * len(sorted_devices)), len(sorted_devices) - 1)
    return sorted_devices[idx]


def select_link(bandwidth_needed_gbps: float) -> LinkSpec:
    """Select the cheapest link type that meets bandwidth requirements."""
    sorted_links = sorted(LINK_SPECS.values(), key=lambda l: l.bandwidth_gbps)
    for link in sorted_links:
        if link.bandwidth_gbps >= bandwidth_needed_gbps:
            return link
    return sorted_links[-1]  # Return highest if nothing fits


def estimate_users_per_switch(switch: DeviceSpec) -> int:
    """Estimate how many end users a switch can support."""
    usable_ports = int(switch.ports_1g * 0.85)  # 15% for uplinks/infra
    return max(usable_ports, 1)


def calculate_availability(redundant_devices: int, mtbf: int, mttr_hours: float = 4.0) -> float:
    """Calculate system availability using MTBF and MTTR with redundancy."""
    single_avail = mtbf / (mtbf + mttr_hours)
    if redundant_devices <= 1:
        return single_avail
    # Parallel redundancy: A = 1 - (1-a)^n
    return 1.0 - (1.0 - single_avail) ** redundant_devices


def availability_to_nines(availability: float) -> str:
    """Convert availability percentage to 'nines' notation."""
    if availability >= 0.99999:
        return "5 nines (99.999%)"
    elif availability >= 0.9999:
        return "4 nines (99.99%)"
    elif availability >= 0.999:
        return "3 nines (99.9%)"
    elif availability >= 0.99:
        return "2 nines (99.0%)"
    else:
        return f"{availability*100:.1f}%"


def get_org_user_range(org_size: OrgSize) -> tuple:
    """Return (min, max) user count for org size."""
    ranges = {
        OrgSize.SMALL: (10, 50),
        OrgSize.MEDIUM: (50, 500),
        OrgSize.LARGE: (500, 5000),
        OrgSize.ENTERPRISE: (5000, 50000),
    }
    return ranges.get(org_size, (50, 500))


def calculate_power_cost(total_watts: int, cost_per_kwh: float = 0.12) -> float:
    """Calculate annual power cost including PUE overhead."""
    pue = 1.6  # Power Usage Effectiveness (typical)
    annual_kwh = (total_watts * pue * 8760) / 1000
    return annual_kwh * cost_per_kwh
