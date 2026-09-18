# NetGenAI — Generative AI-Based Automatic Network Topology Design & Optimization

An industry-ready, AI-assisted platform that automates the end-to-end design, sizing, visualization, and multi-objective optimization of enterprise network topologies based on organizational requirements, traffic load, budget constraints, and fault tolerance.

---

## 🌟 Key Features

1. **Generative AI Architectural Sizing**:
   - Synthesizes 9 enterprise topology architectures (Cisco 3-Tier Hierarchical, Spine-Leaf Clos, Collapsed Core, Fat-Tree k-ary, Full/Partial Mesh, Ring, Star, Hybrid).
   - Dynamic oversubscription calculation, port density sizing, and automated security perimeter placement (HA Firewalls, DMZ, IDS/IPS, Load Balancers).
   - Generative Chain-of-Thought reasoning explaining every architectural decision.

2. **Retrieval-Augmented Generation (RAG)**:
   - Built-in technical knowledge base with 30+ curated industry standards from **Cisco SAFE**, **Arista RFC 7938**, **NIST SP 800-207 Zero-Trust**, **PCI-DSS 4.0**, and **HIPAA**.
   - TF-IDF vectorization with cosine similarity scoring for contextual recommendations.
   - Interactive search bar for querying networking standards in natural language.

3. **Multi-Objective Genetic Algorithm (GA) Optimization**:
   - Encodes network topologies as chromosomes with adjacency lists and device tiers.
   - Optimizes across 5 competing objectives: **CapEx/OpEx Cost**, **Redundancy & High Availability**, **Hop Latency**, **Cross-Sectional Throughput**, and **Port Scalability Headroom**.
   - 6 evolutionary mutation operators, tournament selection, single-point crossover, and elitism.
   - Real-time Plotly convergence charts, radar trade-off diagrams, and mutation logs.

4. **Interactive Topology Visualization & Resilience Simulation**:
   - Physics-based dynamic network graph powered by PyVis with tier color-coding and device tooltips.
   - Interactive Failure Simulator: Click any device to simulate an outage and instantly observe blast radius, cut-vertex partitions, and surviving connectivity.

5. **Financial & Compliance Intelligence**:
   - Full TCO modeling: CapEx, Annual OpEx, 3-Yr/5-Yr TCO, Power (Watts & $/yr), MTBF-based "Five Nines" (99.999%) availability.
   - Itemized Bill of Materials (BOM) with download CSV button.
   - Automated Compliance Assessment for PCI-DSS 4.0, HIPAA, SOC 2, and ISO 27001.

6. **Infrastructure as Code (IaC) & Configuration Exporters**:
   - **Cisco IOS-XE**: Ready-to-deploy switch/router configuration scripts (VLANs, Trunks, Rapid-PVST+, OSPF/BGP).
   - **Terraform HCL (`main.tf`)**: Cloud/Hybrid VPC & Subnet provisioning code.
   - **Ansible Automation Playbook (`playbook.yml`)**: Network CLI configuration playbooks.
   - **IPAM Inventory (`JSON`)**: IP address management and VLAN allocation mappings.

---

## 📂 Project Structure

```
CN/
├── app.py                  # Main Streamlit enterprise application
├── visualizer.py           # PyVis physics graph and Plotly visualizer
├── export_generator.py     # Cisco IOS-XE, Terraform, Ansible, and IPAM exporters
├── network_models.py       # Enterprise hardware catalog, link specs, and dataclasses
├── rag_knowledge.py        # RAG technical knowledge base & TF-IDF search engine
├── topology_engine.py      # Multi-architecture generation & failure simulation engine
├── ga_optimizer.py         # Multi-objective genetic algorithm optimizer
├── test_suite.py           # Full integration & unit test suite
├── requirements.txt        # Python dependencies
└── README.md               # Documentation
```

---

## 🚀 Getting Started

### 1. Install Dependencies

Ensure Python 3.10+ is installed, then run:

```bash
pip install -r requirements.txt
```

### 2. Run the Test Suite

```bash
python test_suite.py
```

### 3. Launch the Application Locally

```bash
streamlit run app.py
```

Open your browser and navigate to **`http://localhost:8501`**.

---

## 🌐 Deploy to Render (Cloud Hosting)

NetGenAI includes full out-of-the-box configuration files for [Render](https://render.com):
- `render.yaml` (Render Blueprint specification)
- `.streamlit/config.toml` (Headless and CORS configuration for cloud hosting)
- `runtime.txt` (Python 3.11.9 runtime definition)

### Option 1: One-Click Render Blueprint
1. Go to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** $\to$ **Blueprint**.
3. Connect your GitHub repository: `https://github.com/Parthx-06/NetGenAI`.
4. Render will automatically detect `render.yaml` and configure everything! Click **Apply**.

### Option 2: Manual Web Service Setup
1. On [Render Dashboard](https://dashboard.render.com), click **New +** $\to$ **Web Service**.
2. Select your repository: `Parthx-06/NetGenAI`.
3. Configure the settings:
   - **Name**: `netgenai`
   - **Language / Runtime**: `Python 3`
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`
4. Under **Advanced** $\to$ **Add Environment Variable**:
   - `PYTHON_VERSION`: `3.11.9`
5. Click **Create Web Service**. Your app will be live on Render in 2–3 minutes!
