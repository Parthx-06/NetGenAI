"""
app.py — Generative AI-Based Automatic Network Topology Design and Optimization
Enterprise-Grade Streamlit Web Application
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import time

from network_models import (
    NetworkRequirements, OrgSize, TrafficLoad, FaultTolerance,
    ScalabilityNeed, TopologyType, DeviceType, NetworkTier
)
from topology_engine import TopologyEngine
from rag_knowledge import RAGEngine
from ga_optimizer import GeneticOptimizer, GAConfig
from visualizer import (
    build_pyvis_network_html, build_fitness_chart,
    build_radar_chart, build_cost_donut_chart, TIER_COLORS
)
from export_generator import ExportGenerator


# ──────────────────────────────────────────────────────────────
# Page Configuration & Dark Cyber Theme Styling
# ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="NetGenAI — Autonomous Enterprise Network Topology Designer",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Cyberpunk / Dark Glassmorphism CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    code, pre {
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    .stApp {
        background-color: #080c14;
        color: #f1f5f9;
    }
    
    /* Header Gradient Banner */
    .hero-banner {
        background: linear-gradient(135deg, rgba(14, 23, 42, 0.95) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(0, 212, 255, 0.25);
        box-shadow: 0 8px 32px 0 rgba(0, 212, 255, 0.1);
        border-radius: 12px;
        padding: 24px 30px;
        margin-bottom: 24px;
    }
    
    .hero-title {
        font-size: 28px;
        font-weight: 700;
        letter-spacing: -0.5px;
        background: linear-gradient(90deg, #00d4ff 0%, #7b2ff7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    .hero-subtitle {
        color: #94a3b8;
        font-size: 14px;
        margin-top: 6px;
        margin-bottom: 12px;
    }
    
    .status-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 8px;
    }
    .badge-cyan { background: rgba(0, 212, 255, 0.15); color: #00d4ff; border: 1px solid rgba(0, 212, 255, 0.4); }
    .badge-purple { background: rgba(123, 47, 247, 0.15); color: #a855f7; border: 1px solid rgba(123, 47, 247, 0.4); }
    .badge-green { background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4); }
    
    /* Metrics Card Styling */
    .metric-card {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        transition: transform 0.2s, border-color 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #00d4ff;
    }
    .metric-val {
        font-size: 24px;
        font-weight: 700;
        color: #ffffff;
        font-family: 'JetBrains Mono', monospace;
    }
    .metric-lbl {
        font-size: 12px;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }
    
    /* RAG Card */
    .rag-card {
        background: #0f172a;
        border-left: 4px solid #00d4ff;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
        border-top: 1px solid #1e293b;
        border-right: 1px solid #1e293b;
        border-bottom: 1px solid #1e293b;
    }
    .rag-title {
        font-size: 15px;
        font-weight: 600;
        color: #e2e8f0;
    }
    .rag-meta {
        font-size: 12px;
        color: #00d4ff;
        margin-bottom: 8px;
    }
    .rag-content {
        font-size: 13px;
        color: #94a3b8;
        line-height: 1.5;
    }
    
    /* Chain of Thought Box */
    .cot-step {
        background: rgba(15, 23, 42, 0.6);
        border-left: 3px solid #7b2ff7;
        padding: 10px 14px;
        margin-bottom: 8px;
        border-radius: 4px;
        font-size: 13px;
        color: #cbd5e1;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# State Initialization
# ──────────────────────────────────────────────────────────────

if "engine" not in st.session_state:
    st.session_state.engine = TopologyEngine()
if "rag" not in st.session_state:
    st.session_state.rag = RAGEngine()
if "current_requirements" not in st.session_state:
    st.session_state.current_requirements = None
if "current_graph" not in st.session_state:
    st.session_state.current_graph = None
if "current_metrics" not in st.session_state:
    st.session_state.current_metrics = None
if "ga_summary" not in st.session_state:
    st.session_state.ga_summary = None
if "ga_history" not in st.session_state:
    st.session_state.ga_history = None
if "sim_result" not in st.session_state:
    st.session_state.sim_result = None


# ──────────────────────────────────────────────────────────────
# Sidebar: Requirements & Parameters Intake
# ──────────────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/network-cable.png", width=55)
    st.title("Network Parameters")
    
    # Preset Selector
    preset = st.selectbox(
        "⚡ Enterprise Profile Preset",
        [
            "Custom Configuration",
            "🏢 Global Financial Campus (Ultra-HA)",
            "🏥 Regional Healthcare Hospital (HIPAA)",
            "☁️ High-Scale SaaS Data Center (Clos)",
            "🏬 Mid-Sized Corporate HQ (3-Tier)"
        ]
    )
    
    # Preset defaults
    if preset == "🏢 Global Financial Campus (Ultra-HA)":
        p_size = OrgSize.ENTERPRISE
        p_users = 2500
        p_depts = 12
        p_traffic = TrafficLoad.CRITICAL
        p_budget = 450000
        p_ft = FaultTolerance.MISSION_CRITICAL
        p_scale = ScalabilityNeed.HIGH
        p_sec = ["Firewall", "IDS/IPS", "DMZ", "Zero-Trust", "Load Balancer"]
        p_comp = ["PCI-DSS 4.0", "SOC 2 Type II", "ISO 27001"]
        p_topo = TopologyType.THREE_TIER
        p_wan = 2
        p_wifi = True
        p_dmz = True
    elif preset == "🏥 Regional Healthcare Hospital (HIPAA)":
        p_size = OrgSize.LARGE
        p_users = 1200
        p_depts = 8
        p_traffic = TrafficLoad.HIGH
        p_budget = 280000
        p_ft = FaultTolerance.HIGH
        p_scale = ScalabilityNeed.MODERATE
        p_sec = ["Firewall", "IDS/IPS", "DMZ"]
        p_comp = ["HIPAA", "NIST 800-53"]
        p_topo = TopologyType.HYBRID
        p_wan = 1
        p_wifi = True
        p_dmz = True
    elif preset == "☁️ High-Scale SaaS Data Center (Clos)":
        p_size = OrgSize.ENTERPRISE
        p_users = 5000
        p_depts = 16
        p_traffic = TrafficLoad.CRITICAL
        p_budget = 650000
        p_ft = FaultTolerance.MISSION_CRITICAL
        p_scale = ScalabilityNeed.HYPER
        p_sec = ["Firewall", "IDS/IPS", "Load Balancer", "Zero-Trust"]
        p_comp = ["SOC 2 Type II", "ISO 27001"]
        p_topo = TopologyType.SPINE_LEAF
        p_wan = 3
        p_wifi = False
        p_dmz = True
    elif preset == "🏬 Mid-Sized Corporate HQ (3-Tier)":
        p_size = OrgSize.MEDIUM
        p_users = 350
        p_depts = 5
        p_traffic = TrafficLoad.MEDIUM
        p_budget = 140000
        p_ft = FaultTolerance.HIGH
        p_scale = ScalabilityNeed.MODERATE
        p_sec = ["Firewall", "DMZ"]
        p_comp = ["ISO 27001"]
        p_topo = TopologyType.COLLAPSED_CORE
        p_wan = 1
        p_wifi = True
        p_dmz = True
    else:
        p_size = OrgSize.MEDIUM
        p_users = 500
        p_depts = 6
        p_traffic = TrafficLoad.HIGH
        p_budget = 180000
        p_ft = FaultTolerance.HIGH
        p_scale = ScalabilityNeed.MODERATE
        p_sec = ["Firewall", "IDS/IPS", "DMZ"]
        p_comp = ["ISO 27001"]
        p_topo = TopologyType.AUTO
        p_wan = 1
        p_wifi = True
        p_dmz = True

    with st.expander("🏢 Organizational Scope", expanded=True):
        org_size_choice = st.selectbox(
            "Organization Scale",
            options=list(OrgSize),
            format_func=lambda x: x.value,
            index=list(OrgSize).index(p_size)
        )
        num_users = st.slider("Total Active Endpoints/Users", 50, 8000, p_users, step=50)
        num_depts = st.slider("Departments / Broadcast Domains", 2, 24, p_depts)
        budget_usd = st.slider("CapEx Budget Limit (USD)", 25000, 1000000, p_budget, step=10000, format="$%d")

    with st.expander("⚡ Performance & Reliability", expanded=True):
        traffic_load = st.selectbox(
            "Expected Traffic Profile",
            options=list(TrafficLoad),
            format_func=lambda x: x.value,
            index=list(TrafficLoad).index(p_traffic)
        )
        fault_tolerance = st.selectbox(
            "Fault Tolerance Requirement",
            options=list(FaultTolerance),
            format_func=lambda x: x.value,
            index=list(FaultTolerance).index(p_ft)
        )
        scalability = st.selectbox(
            "Growth Scalability",
            options=list(ScalabilityNeed),
            format_func=lambda x: x.value,
            index=list(ScalabilityNeed).index(p_scale)
        )

    with st.expander("🔒 Security & Compliance", expanded=False):
        security_features = st.multiselect(
            "Security Perimeters",
            ["Firewall", "IDS/IPS", "DMZ", "Zero-Trust", "Load Balancer", "VoIP"],
            default=p_sec
        )
        compliance_frameworks = st.multiselect(
            "Compliance Mandates",
            ["PCI-DSS 4.0", "HIPAA", "SOC 2 Type II", "ISO 27001", "NIST 800-53"],
            default=p_comp
        )
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            wireless_req = st.checkbox("Enterprise Wi-Fi", value=p_wifi)
            redundant_wan = st.checkbox("Dual WAN Circuits", value=p_wan > 1)
        with col_w2:
            dmz_req = st.checkbox("DMZ Segment", value=p_dmz)
            sd_wan = st.checkbox("SD-WAN Overlay", value=False)
        wan_sites = st.slider("Branch / Remote WAN Sites", 1, 10, p_wan)

    with st.expander("📐 Topology Engine Selection", expanded=False):
        preferred_topo = st.selectbox(
            "Architecture Template",
            options=list(TopologyType),
            format_func=lambda x: x.value,
            index=list(TopologyType).index(p_topo)
        )

    with st.expander("🧬 Genetic Algorithm Hyperparameters", expanded=False):
        ga_pop_size = st.slider("Population Size", 10, 50, 20, step=2)
        ga_max_gens = st.slider("Generations Count", 5, 40, 15, step=5)
        st.markdown("**Objective Optimization Weights:**")
        w_cost = st.slider("Cost Efficiency", 0.0, 1.0, 0.30, 0.05)
        w_red = st.slider("Redundancy", 0.0, 1.0, 0.25, 0.05)
        w_lat = st.slider("Low Latency", 0.0, 1.0, 0.15, 0.05)
        w_thr = st.slider("Throughput", 0.0, 1.0, 0.15, 0.05)
        w_scale = st.slider("Scalability", 0.0, 1.0, 0.15, 0.05)
        
        # Normalize weights
        total_w = w_cost + w_red + w_lat + w_thr + w_scale
        if total_w == 0:
            total_w = 1.0
        w_cost, w_red, w_lat, w_thr, w_scale = (
            w_cost / total_w, w_red / total_w, w_lat / total_w, w_thr / total_w, w_scale / total_w
        )

    generate_clicked = st.button("🚀 Generate & Optimize Topology", type="primary", use_container_width=True)


# ──────────────────────────────────────────────────────────────
# Trigger Generation & GA Workflow
# ──────────────────────────────────────────────────────────────

if generate_clicked or st.session_state.current_graph is None:
    req = NetworkRequirements(
        org_size=org_size_choice,
        num_departments=num_depts,
        num_users=num_users,
        traffic_load=traffic_load,
        budget_usd=budget_usd,
        fault_tolerance=fault_tolerance,
        scalability=scalability,
        security_features=security_features,
        preferred_topology=preferred_topo,
        compliance_frameworks=compliance_frameworks,
        wan_sites=wan_sites,
        wireless_required=wireless_req,
        dmz_required=dmz_req,
        redundant_wan=redundant_wan,
        sd_wan=sd_wan
    )
    
    with st.spinner("🧠 Generative AI Engine: Analyzing requirements, sizing tiers, and generating topology..."):
        engine = TopologyEngine()
        graph, metrics = engine.generate(req)
        
        # Run Genetic Algorithm
        ga_config = GAConfig(
            population_size=ga_pop_size,
            max_generations=ga_max_gens,
            w_cost=w_cost,
            w_redundancy=w_red,
            w_latency=w_lat,
            w_throughput=w_thr,
            w_scalability=w_scale
        )
        optimizer = GeneticOptimizer(config=ga_config)
        optimized_graph, history = optimizer.optimize(graph, req)
        
        st.session_state.engine = engine
        st.session_state.current_requirements = req
        st.session_state.current_graph = optimized_graph
        st.session_state.current_metrics = metrics
        st.session_state.ga_summary = optimizer.get_optimization_summary()
        st.session_state.ga_history = optimizer.get_fitness_history()
        st.session_state.sim_result = None

engine = st.session_state.engine
req = st.session_state.current_requirements
metrics = st.session_state.current_metrics
ga_summary = st.session_state.ga_summary
ga_history = st.session_state.ga_history


# ──────────────────────────────────────────────────────────────
# Header & Executive Status Banner
# ──────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero-banner">
    <div class="hero-title">🌐 NetGenAI — Enterprise Network Topology Designer</div>
    <div class="hero-subtitle">Generative AI-Assisted Architecture Sizing • RAG Knowledge Retrieval • Multi-Objective Genetic Algorithm Optimization</div>
    <div>
        <span class="status-badge badge-cyan">● LLM Synthesis Engine Active</span>
        <span class="status-badge badge-purple">● RAG Vector Index: 30 Curated RFC/NIST Standards</span>
        <span class="status-badge badge-green">● GA Optimizer: Multi-Objective Pareto Convergence</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# Key Metrics Row
# ──────────────────────────────────────────────────────────────

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val">${metrics.total_cost_capex:,.0f}</div>
        <div class="metric-lbl">Total CapEx</div>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val">${metrics.annual_opex:,.0f}</div>
        <div class="metric-lbl">Annual OpEx</div>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val" style="color: #10b981;">{metrics.availability_nines.split()[0]} 9s</div>
        <div class="metric-lbl">{metrics.availability_percent:.3f}% Uptime</div>
    </div>
    """, unsafe_allow_html=True)
with c4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val" style="color: #00d4ff;">{metrics.redundancy_score}/100</div>
        <div class="metric-lbl">Resilience Score</div>
    </div>
    """, unsafe_allow_html=True)
with c5:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val">{metrics.total_devices} Dev / {metrics.total_links} Links</div>
        <div class="metric-lbl">Total Density</div>
    </div>
    """, unsafe_allow_html=True)
with c6:
    budget_delta = req.budget_usd - metrics.total_cost_capex
    b_color = "#10b981" if budget_delta >= 0 else "#ef4444"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-val" style="color: {b_color};">${abs(budget_delta):,.0f}</div>
        <div class="metric-lbl">{'Under Budget' if budget_delta >= 0 else 'Over Budget'}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("")


# ──────────────────────────────────────────────────────────────
# Main Application Tabs
# ──────────────────────────────────────────────────────────────

tab_topo, tab_ai, tab_ga, tab_bom, tab_iac = st.tabs([
    "🌐 Interactive Topology Graph",
    "🤖 Generative AI & RAG Insights",
    "🧬 Genetic Algorithm Evolution",
    "📊 Financials & BOM Dashboard",
    "📄 Infrastructure as Code (IaC) Export"
])


# ══════════════════════════════════════════════════════════════
# TAB 1: INTERACTIVE TOPOLOGY GRAPH & FAILURE SIMULATION
# ══════════════════════════════════════════════════════════════

with tab_topo:
    col_graph, col_ctrl = st.columns([3, 1])

    with col_ctrl:
        st.subheader("🛠️ Topology Controls")
        
        # Legend
        st.markdown("**Network Tiers:**")
        for tier_name, color in TIER_COLORS.items():
            st.markdown(f"<span style='color:{color}; font-size:16px;'>■</span> **{tier_name}**", unsafe_allow_html=True)
        
        st.divider()
        st.subheader("💥 Failure Simulation")
        st.caption("Select a core router, switch, or firewall to test single-point-of-failure (SPOF) resilience.")
        
        node_options = {nid: f"{n.label.replace(chr(10), ' ')} ({n.tier.value})" for nid, n in engine.nodes.items()}
        target_node = st.selectbox("Select Target Device to Fail", options=list(node_options.keys()), format_func=lambda x: node_options[x])
        
        if st.button("Simulate Device Failure", use_container_width=True):
            st.session_state.sim_result = engine.simulate_failure(target_node)
            st.rerun()

        if st.session_state.sim_result:
            res = st.session_state.sim_result
            st.markdown("### Simulation Blast Radius:")
            status_color = "#10b981" if res.get("network_status") == "OPERATIONAL" else "#ef4444"
            st.markdown(f"**Status:** <span style='color:{status_color}; font-weight:700;'>{res.get('network_status')}</span>", unsafe_allow_html=True)
            st.markdown(f"- **Failed Device:** `{res.get('failed_device')}`")
            st.markdown(f"- **Affected Direct Links:** {res.get('affected_links')}")
            st.markdown(f"- **Isolated Network Segments:** {res.get('isolated_segments')}")
            st.markdown(f"- **Surviving Connectivity:** `{res.get('connectivity')}%`")
            if st.button("Reset Simulation", use_container_width=True):
                st.session_state.sim_result = None
                st.rerun()

    with col_graph:
        st.caption("Physics-based dynamic graph. Drag nodes to inspect links, scroll to zoom, hover for hardware specs and IP allocations.")
        pyvis_html = build_pyvis_network_html(engine.nodes, engine.links, height="600px")
        components.html(pyvis_html, height=620, scrolling=False)


# ══════════════════════════════════════════════════════════════
# TAB 2: GENERATIVE AI REASONING & RAG RETRIEVAL
# ══════════════════════════════════════════════════════════════

with tab_ai:
    col_cot, col_rag = st.columns([1, 1])

    with col_cot:
        st.subheader("🧠 Generative AI Chain-of-Thought")
        st.caption("Step-by-step synthetic LLM reasoning generated for this specific topology configuration:")
        
        for idx, thought in enumerate(engine.ai_reasoning):
            st.markdown(f"""
            <div class="cot-step">
                <b>Step {idx+1}:</b> {thought}
            </div>
            """, unsafe_allow_html=True)
            
        st.divider()
        st.markdown("### 📋 Topology Design Decision Matrix")
        st.markdown(f"""
        - **Calculated Access Layer Switches:** `{len([n for n in engine.nodes.values() if n.tier == NetworkTier.ACCESS])}` units (Sized for `{req.num_users}` endpoints with 20% growth headroom).
        - **Core Backbone Capacity:** `{metrics.throughput_capacity_gbps} Gbps` aggregated cross-sectional bandwidth.
        - **Redundant Link Pairs:** `{sum(1 for l in engine.links if l.is_redundant)}` failover interfaces.
        - **Calculated Subnet Allocation:** `{len(engine.vlans)}` isolated broadcast domains & security zones.
        """)

    with col_rag:
        st.subheader("📚 RAG Knowledge Retrieval")
        st.caption("Semantically relevant industry best-practice standards retrieved for this architecture:")
        
        # Natural language query box for on-demand RAG search
        rag_query = st.text_input("🔍 Query Architecture Knowledge Base", placeholder="e.g., 'spine-leaf oversubscription', 'PCI-DSS firewall rules'")
        if rag_query:
            retrieved_docs = st.session_state.rag.retrieve(rag_query, top_k=4)
        else:
            retrieved_docs = st.session_state.rag.get_recommendations(req)[:4]

        for entry, score in retrieved_docs:
            st.markdown(f"""
            <div class="rag-card">
                <div class="rag-title">{entry.title}</div>
                <div class="rag-meta">Source: {entry.source} • Category: {entry.category} • Match Score: {score:.3f}</div>
                <div class="rag-content">{entry.content}</div>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# TAB 3: GENETIC ALGORITHM OPTIMIZATION
# ══════════════════════════════════════════════════════════════

with tab_ga:
    if ga_summary and ga_history:
        g1, g2, g3, g4 = st.columns(4)
        with g1:
            st.metric("Generations Evaluated", ga_summary.get("generations_run"))
        with g2:
            st.metric("Initial Fitness", f"{ga_summary.get('initial_fitness', 0):.4f}")
        with g3:
            st.metric("Optimized Fitness", f"{ga_summary.get('final_fitness', 0):.4f}",
                      delta=f"+{ga_summary.get('improvement_pct', 0)}%")
        with g4:
            st.metric("Plateau / Convergence Gen", f"Gen #{ga_summary.get('convergence_gen')}")

        st.divider()

        col_fit_chart, col_radar = st.columns([3, 2])
        with col_fit_chart:
            fit_fig = build_fitness_chart(ga_history)
            st.plotly_chart(fit_fig, use_container_width=True)

        with col_radar:
            radar_fig = build_radar_chart(ga_summary)
            st.plotly_chart(radar_fig, use_container_width=True)

        st.subheader("🧬 Evolutionary Mutation Operators Applied")
        st.markdown(f"""
        During the multi-objective run, **{ga_summary.get('total_mutations', 0)}** genetic mutations were tested across chromosomes:
        - **Link Additions / Pruning:** Iterative addition of high-bandwidth redundant links and elimination of redundant routing loops.
        - **Hardware Upgrades / Right-Sizing:** Evaluating device tiers to maintain throughput while minimizing unnecessary CapEx.
        - **Bandwidth Reallocation:** Dynamically scaling trunk uplinks (10G ↔ 25G ↔ 40G ↔ 100G) based on simulated egress traffic loads.
        - **Failover Redundancy Toggling:** Tuning HSRP/VRRP gateway pairs to eliminate single points of failure.
        """)
    else:
        st.info("Run optimization to view genetic algorithm metrics.")


# ══════════════════════════════════════════════════════════════
# TAB 4: FINANCIALS, BOM, & COMPLIANCE
# ══════════════════════════════════════════════════════════════

with tab_bom:
    col_donut, col_cost_tbl = st.columns([2, 3])

    cost_data = engine.get_cost_breakdown()
    with col_donut:
        st.subheader("💰 CapEx Distribution")
        donut_fig = build_cost_donut_chart(cost_data)
        st.plotly_chart(donut_fig, use_container_width=True)

    with col_cost_tbl:
        st.subheader("📋 Itemized Bill of Materials (BOM)")
        df_cost = pd.DataFrame(cost_data)
        st.dataframe(df_cost, use_container_width=True, hide_index=True)
        
        # Download BOM CSV
        csv_bom = df_cost.to_csv(index=False)
        st.download_button("📥 Download BOM (CSV)", csv_bom, "network_bill_of_materials.csv", "text/csv")

    st.divider()

    col_comp, col_vlans = st.columns([1, 1])

    with col_comp:
        st.subheader("🛡️ Regulatory Compliance Assessment")
        if metrics.compliance_status:
            for fw, status in metrics.compliance_status.items():
                badge_style = "color: #10b981; font-weight: bold;" if status == "Pass" else "color: #f59e0b; font-weight: bold;"
                st.markdown(f"**{fw}:** <span style='{badge_style}'>{status}</span>", unsafe_allow_html=True)
        else:
            st.write("No specific regulatory frameworks selected.")

        st.markdown(f"""
        - **Estimated Deployment Window:** `{metrics.estimated_deploy_weeks}` Weeks
        - **Total Rack Units (RU):** `{metrics.rack_units_total} RU`
        - **Total Power Consumption:** `{metrics.power_total_watts} Watts` (Est. `${metrics.annual_power_cost:,.0f}`/year)
        - **3-Year Total Cost of Ownership (TCO):** `${metrics.tco_3yr:,.0f}`
        """)

    with col_vlans:
        st.subheader("🏷️ Subnet & VLAN Allocation Plan (IPAM)")
        vlan_rows = [
            {"VLAN ID": v.vlan_id, "Name": v.name, "Subnet": v.subnet, "Gateway": v.gateway, "Purpose": v.purpose}
            for v in engine.vlans
        ]
        df_vlans = pd.DataFrame(vlan_rows)
        st.dataframe(df_vlans, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════
# TAB 5: INFRASTRUCTURE AS CODE (IAC) & EXPORTS
# ══════════════════════════════════════════════════════════════

with tab_iac:
    st.subheader("⚙️ Automated Network Provisioning Exports")
    st.caption("Generate copy-paste configuration scripts for physical enterprise switches and cloud infrastructure.")

    iac_type = st.radio(
        "Export Target Format",
        ["Cisco IOS-XE Configuration Script", "Terraform Cloud/Hybrid Infrastructure (main.tf)", "Ansible Network Automation Playbook", "IPAM Inventory Data (JSON)"],
        horizontal=True
    )

    if iac_type == "Cisco IOS-XE Configuration Script":
        cisco_cfg = ExportGenerator.generate_cisco_ios_config(engine.nodes, engine.links, engine.vlans)
        st.download_button("📥 Download Cisco Config (.cfg)", cisco_cfg, "cisco_ios_running_config.cfg", "text/plain")
        st.code(cisco_cfg, language="text", line_numbers=True)

    elif iac_type == "Terraform Cloud/Hybrid Infrastructure (main.tf)":
        tf_cfg = ExportGenerator.generate_terraform(engine.nodes, engine.vlans)
        st.download_button("📥 Download Terraform (.tf)", tf_cfg, "main.tf", "hcl")
        st.code(tf_cfg, language="hcl", line_numbers=True)

    elif iac_type == "Ansible Network Automation Playbook":
        ansible_cfg = ExportGenerator.generate_ansible_playbook(engine.nodes)
        st.download_button("📥 Download Ansible Playbook (.yml)", ansible_cfg, "playbook.yml", "yaml")
        st.code(ansible_cfg, language="yaml", line_numbers=True)

    elif iac_type == "IPAM Inventory Data (JSON)":
        ipam_json = ExportGenerator.generate_ipam_json(engine.nodes, engine.vlans)
        st.download_button("📥 Download IPAM Data (.json)", ipam_json, "network_ipam.json", "application/json")
        st.code(ipam_json, language="json", line_numbers=True)
