"""
visualizer.py — Interactive Topology and Analytics Visualization Engine
Renders interactive PyVis physics network graphs and Plotly analytics charts.
"""

import json
from typing import Dict, List, Optional
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from pyvis.network import Network
from network_models import NetworkTier, DeviceType


# Tier-based color scheme (cyber-enterprise dark palette)
TIER_COLORS = {
    NetworkTier.WAN_EDGE.value: "#ff4d4f",       # Crimson Red
    NetworkTier.CORE.value: "#00d4ff",           # Electric Cyan
    NetworkTier.DISTRIBUTION.value: "#7b2ff7",   # Vivid Violet
    NetworkTier.ACCESS.value: "#10b981",         # Emerald Green
    NetworkTier.DMZ.value: "#f59e0b",            # Amber Orange
    NetworkTier.MANAGEMENT.value: "#6366f1",     # Indigo
    NetworkTier.DATA_CENTER.value: "#ec4899",    # Bright Pink
}

DEVICE_SHAPES = {
    DeviceType.CORE_ROUTER.value: "diamond",
    DeviceType.DISTRIBUTION_ROUTER.value: "diamond",
    DeviceType.L3_SWITCH.value: "box",
    DeviceType.L2_SWITCH.value: "box",
    DeviceType.FIREWALL.value: "triangle",
    DeviceType.IDS_IPS.value: "triangleDown",
    DeviceType.LOAD_BALANCER.value: "hexagon",
    DeviceType.SERVER.value: "square",
    DeviceType.WIRELESS_CONTROLLER.value: "star",
    DeviceType.WIRELESS_AP.value: "dot",
    DeviceType.INTERNET_GATEWAY.value: "ellipse",
    DeviceType.DMZ_SWITCH.value: "box",
    DeviceType.STORAGE.value: "database",
    DeviceType.WAN_OPTIMIZER.value: "diamond",
    DeviceType.SDN_CONTROLLER.value: "star",
}


def build_pyvis_network_html(engine_nodes: Dict, engine_links: List, height: str = "620px") -> str:
    """Build interactive physics-enabled PyVis network HTML string."""
    net = Network(height=height, width="100%", bgcolor="#0b0f19", font_color="#e2e8f0", directed=False)
    
    # Configure physics for clear enterprise tier separation
    net.set_options("""
    {
      "nodes": {
        "borderWidth": 2,
        "borderWidthSelected": 4,
        "font": {
          "size": 12,
          "face": "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto",
          "color": "#ffffff"
        },
        "shadow": {
          "enabled": true,
          "color": "rgba(0,0,0,0.6)",
          "size": 8,
          "x": 2,
          "y": 2
        }
      },
      "edges": {
        "smooth": {
          "type": "continuous",
          "roundness": 0.2
        },
        "shadow": {
          "enabled": false
        }
      },
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -45,
          "centralGravity": 0.008,
          "springLength": 85,
          "springConstant": 0.07,
          "damping": 0.88,
          "avoidOverlap": 0.45
        },
        "solver": "forceAtlas2Based",
        "stabilization": {
          "iterations": 150
        }
      },
      "interaction": {
        "hover": true,
        "navigationButtons": true,
        "keyboard": true,
        "tooltipDelay": 150
      }
    }
    """)

    # Add nodes with custom tooltip and styling
    for nid, node in engine_nodes.items():
        color = TIER_COLORS.get(node.tier.value, "#94a3b8")
        shape = DEVICE_SHAPES.get(node.device_type.value, "dot")
        spec = node.device_spec
        
        vlans_str = ", ".join(str(v) for v in node.vlan_ids) if node.vlan_ids else "None"
        ha_status = "Active/Standby HA" if node.is_redundant else "Single Unit"
        
        # HTML Tooltip
        title = f"""
        <div style="font-family: sans-serif; padding: 6px; font-size: 13px; line-height: 1.4; color: #f8fafc; background: #1e293b; border-radius: 6px; border: 1px solid #334155;">
            <b style="color: {color}; font-size: 14px;">{node.label.replace(chr(10), ' ')}</b><br/>
            <b>Tier:</b> {node.tier.value}<br/>
            <b>Type:</b> {node.device_type.value}<br/>
            <b>IP Address:</b> {node.ip_address}<br/>
            <b>Subnet:</b> {node.subnet}<br/>
            <b>Model:</b> {spec.model if spec else 'Virtual / Gateway'}<br/>
            <b>Ports:</b> {f'{spec.ports_1g}x 1G, {spec.ports_10g}x 10G' if spec else 'N/A'}<br/>
            <b>Power:</b> {f'{spec.power_watts} W' if spec else 'N/A'}<br/>
            <b>VLANs:</b> {vlans_str}<br/>
            <b>Redundancy:</b> {ha_status}
        </div>
        """
        
        size = 26 if node.tier in (NetworkTier.CORE, NetworkTier.WAN_EDGE) else (22 if node.tier == NetworkTier.DISTRIBUTION else 17)
        label = node.label.split("\n")[0]
        
        net.add_node(
            nid,
            label=label,
            title=title,
            color=color,
            shape=shape,
            size=size,
            borderWidth=3 if node.is_redundant else 1.5,
            borderWidthSelected=4
        )

    # Add edges
    for link in engine_links:
        bw = link.bandwidth_gbps
        edge_color = "#38bdf8" if bw >= 40 else ("#818cf8" if bw >= 10 else "#64748b")
        if link.is_redundant:
            edge_color = "#34d399"
        
        width = 3.5 if bw >= 40 else (2.5 if bw >= 10 else 1.5)
        title = f"Bandwidth: {bw} Gbps | Protocol: {link.protocol or 'Standard'} | Redundant: {'Yes' if link.is_redundant else 'No'}"
        
        net.add_edge(
            link.source,
            link.target,
            color=edge_color,
            width=width,
            title=title,
            dashes=True if link.is_redundant else False
        )

    return net.generate_html()


def build_fitness_chart(history_data: Dict[str, List[float]]) -> go.Figure:
    """Create Plotly fitness progression line chart."""
    fig = go.Figure()

    gens = history_data.get("generation", [])
    best = history_data.get("best", [])
    avg = history_data.get("average", [])
    worst = history_data.get("worst", [])

    fig.add_trace(go.Scatter(
        x=gens, y=best, mode='lines+markers', name='Best Fitness',
        line=dict(color='#00d4ff', width=3),
        marker=dict(size=6, color='#00d4ff')
    ))
    fig.add_trace(go.Scatter(
        x=gens, y=avg, mode='lines', name='Average Fitness',
        line=dict(color='#a855f7', width=2, dash='dash')
    ))
    fig.add_trace(go.Scatter(
        x=gens, y=worst, mode='lines', name='Worst Fitness',
        line=dict(color='#64748b', width=1, dash='dot')
    ))

    fig.update_layout(
        title="Genetic Algorithm Fitness Evolution Across Generations",
        paper_bgcolor="#0b0f19",
        plot_bgcolor="#111827",
        font=dict(color="#94a3b8", family="Inter, sans-serif"),
        xaxis=dict(title="Generation", gridcolor="#1f2937", zerolinecolor="#1f2937"),
        yaxis=dict(title="Multi-Objective Fitness Score", gridcolor="#1f2937", zerolinecolor="#1f2937"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=30, t=50, b=40),
        hovermode="x unified"
    )
    return fig


def build_radar_chart(summary: Dict) -> go.Figure:
    """Create multi-objective radar/spider chart for topology evaluation."""
    categories = ['Cost Efficiency', 'Fault Redundancy', 'Low Latency', 'Throughput Capacity', 'Scalability']
    
    cost_score = max(0.0, min(1.0, 1.0 - (summary.get("best_cost_score", 0.3))))
    redundancy_score = min(1.0, max(0.0, summary.get("best_redundancy_score", 0.5)))
    latency_score = max(0.0, min(1.0, 1.0 - (summary.get("best_latency_score", 0.3))))
    throughput_score = min(1.0, max(0.0, summary.get("best_throughput_score", 0.6)))
    scalability_score = min(1.0, max(0.0, summary.get("best_scalability_score", 0.6)))
    
    values = [cost_score * 100, redundancy_score * 100, latency_score * 100, throughput_score * 100, scalability_score * 100]
    values.append(values[0])
    categories.append(categories[0])

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(0, 212, 255, 0.25)',
        line=dict(color='#00d4ff', width=2.5),
        name='Optimized Topology'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor="#1f2937",
                linecolor="#1f2937",
                tickfont=dict(color="#64748b")
            ),
            angularaxis=dict(
                gridcolor="#1f2937",
                linecolor="#1f2937",
                tickfont=dict(color="#cbd5e1", size=11)
            ),
            bgcolor="#111827"
        ),
        paper_bgcolor="#0b0f19",
        font=dict(color="#94a3b8", family="Inter, sans-serif"),
        title="Multi-Objective Architecture Trade-Off Radar",
        margin=dict(l=50, r=50, t=50, b=40),
        showlegend=False
    )
    return fig


def build_cost_donut_chart(cost_breakdown: List[Dict]) -> go.Figure:
    """Create cost breakdown donut chart by device category."""
    categories = [row["Category"] for row in cost_breakdown]
    capex_values = [float(row["CapEx"].replace("$", "").replace(",", "")) for row in cost_breakdown]

    colors = ["#00d4ff", "#7b2ff7", "#10b981", "#f59e0b", "#ec4899", "#6366f1", "#06b6d4"]

    fig = go.Figure(data=[go.Pie(
        labels=categories,
        values=capex_values,
        hole=0.55,
        marker=dict(colors=colors, line=dict(color='#0b0f19', width=2)),
        textinfo='percent+label',
        textposition='inside',
        hoverinfo='label+value+percent'
    )])

    fig.update_layout(
        title="Capital Expenditure (CapEx) Distribution",
        paper_bgcolor="#0b0f19",
        plot_bgcolor="#0b0f19",
        font=dict(color="#94a3b8", family="Inter, sans-serif"),
        margin=dict(l=30, r=30, t=50, b=30),
        showlegend=False
    )
    return fig
