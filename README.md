# LLM-RAG-Cluster

A distributed system for serving Large Language Model (LLM) inference with Retrieval-Augmented Generation (RAG) at scale, built to handle up to **1,000 concurrent users**.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Device Roles](#device-roles)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the System](#running-the-system)
- [Monitoring](#monitoring)
- [Load Testing](#load-testing)
- [Fault Tolerance](#fault-tolerance)
- [System Limitations](#system-limitations)

---

## Architecture Overview

The cluster is built on five physical machines connected over a **ZeroTier** virtual private network. Traffic enters through a **Virtual IP (VIP)** managed by **Keepalived** in an active-passive configuration, then gets routed by a custom **NGINX** instance (with the VTS module) to one of four **GPU worker nodes**. Each worker runs a **FastAPI** service that handles RAG retrieval via a local **FAISS** vector store and LLM inference via a local **Ollama** instance.

```
[Locust Load Generator]
        |
        ▼
[Virtual IP: 10.2.213.200:8085]  ← managed by Keepalived (VRRP)
        |
  ┌─────┴─────┐
  ▼           ▼
[NGINX       [NGINX          ← Active / Passive Masters
 Active]      Passive]         (least_conn load balancing)
  └─────┬─────┘
        |
  ┌─────┼─────┬─────┐
  ▼     ▼     ▼     ▼
[GPU  [GPU  [GPU  [GPU        ← FastAPI + Ollama (SmolLM2 135M)
Worker] Worker] Worker] Worker]  + local FAISS RAG index
```

**Monitoring:** Prometheus scrapes all worker `/metrics` endpoints. Grafana visualizes the data. Locust annotates the Grafana timeline with test start/stop markers.

---

## Project Structure

```
LLM-RAG-CLUSTER/
│
├── client/
│   ├── load_generator.py      # Locust users, retry logic, StepLoadShape, Grafana annotations
│   └── run_load_test.py       # Spawns Locust master + 4 worker processes
│
├── common/
│   ├── __init__.py
│   └── models.py              # Shared Request / Response dataclasses
│
├── data/                      # Place your PDF and Markdown knowledge base files here
│
├── lb/                        # Load balancer configuration files
│
├── llm/
│   ├── __init__.py
│   └── inference.py           # Ollama API call, Prometheus LLM metrics
│
├── nginx/                     # Custom NGINX build with VTS module
│   ├── conf/
│   │   └── nginx.conf         # Upstream pool, least_conn, VTS dashboard, health checks
│   ├── contrib/
│   ├── docs/
│   ├── html/
│   ├── logs/
│   └── temp/
│
├── rag/
│   ├── __init__.py
│   ├── requirements.txt       # RAG-specific Python dependencies
│   └── retriever.py           # FAISS index builder, HuggingFace embeddings, context retrieval
│
├── workers/
│   └── gpu_worker.py          # FastAPI app: /process, /health, /metrics, GPU telemetry
│
├── .env                       # Environment variables (see Configuration)
├── .gitignore
└── main.py                    # Entry point — calls run_load_test.start_locust_cluster()
```

---

## Device Roles

| Device | Role | Key Components |
|---|---|---|
| Device 1 | Load Generator | Locust (1,000 users) |
| Device 2 | Active Master + GPU Worker | Keepalived (Active), NGINX, FastAPI, Ollama |
| Device 3 | Passive Master + GPU Worker | Keepalived (Passive), NGINX, FastAPI, Ollama |
| Device 4 | GPU Worker + Monitoring Hub | FastAPI, Ollama, Prometheus, Grafana |
| Device 5 | GPU Worker | FastAPI, Ollama |

---

## Prerequisites

### All Nodes
- Python 3.10+
- [ZeroTier](https://www.zerotier.com/) — all devices must be joined to the same virtual network

### GPU Worker Nodes (Devices 2, 3, 4, 5)
- NVIDIA GPU with drivers installed
- [Ollama](https://ollama.com/) installed and running
- The `smollm2:135m` model pulled:
  ```bash
  ollama pull smollm2:135m
  ```

### Master Nodes (Devices 2, 3) — Windows + WSL
- WSL2 with a Debian/Ubuntu distribution
- `keepalived` installed inside WSL:
  ```bash
  sudo apt install keepalived
  ```
- Custom NGINX 1.24.0 with the [VTS module](https://github.com/vozlt/nginx-module-vts) compiled and available in the `nginx/` directory
- `netsh` port proxy configured on the Windows host to bridge ZeroTier traffic into WSL:
  ```powershell
  netsh interface portproxy add v4tov4 listenaddress=10.2.213.200 listenport=8085 connectaddress=127.0.0.1 connectport=8085
  ```

### Monitoring Node (Device 4)
- [Prometheus](https://prometheus.io/) configured to scrape all worker `/metrics` endpoints
- [Grafana](https://grafana.com/) connected to Prometheus as a data source (default: `http://localhost:9090`)

---

## Installation

### 1. Clone the repository on all nodes
```bash
git clone <repo-url>
cd LLM-RAG-CLUSTER
```

### 2. Install RAG dependencies (GPU Worker Nodes)
```bash
pip install -r rag/requirements.txt
```

### 3. Install worker dependencies (GPU Worker Nodes)
```bash
pip install fastapi uvicorn pynvml psutil prometheus-fastapi-instrumentator prometheus-client
```

### 4. Install load generator dependencies (Device 1)
```bash
pip install locust requests gevent python-dotenv
```

### 5. Populate the knowledge base (GPU Worker Nodes)
Place your `.pdf` and `.md` documents inside the `data/` folder at the project root on **each worker node**. The RAG index is built locally on startup — all nodes must have the same documents for consistent responses.

---

## Configuration

Create a `.env` file at the project root:

```env
API=<your-grafana-api-token>
```

This token is used by Locust to send start/stop annotations to the Grafana dashboard. Generate it from **Grafana → Administration → Service Accounts**.

---

## Running the System

Start the components in this order:

### Step 1 — Start Ollama on each GPU Worker Node
```bash
ollama serve
```

### Step 2 — Start the FastAPI worker on each GPU Worker Node
```bash
cd LLM-RAG-CLUSTER
python workers/gpu_worker.py
```
The worker listens on `0.0.0.0:8000`. Verify it is healthy:
```bash
curl http://localhost:8000/health
```

### Step 3 — Start NGINX on the Master Nodes (inside WSL)
```bash
# Kill any existing NGINX process that may be holding the port
sudo pkill -9 nginx

# Start the custom VTS-enabled NGINX binary
sudo /usr/sbin/nginx
```

### Step 4 — Start Keepalived on the Master Nodes (inside WSL)
```bash
sudo service keepalived start
```
Device 2 (priority 100) will claim the VIP. Device 3 (priority 90) will enter standby.

### Step 5 — Start the Load Generator (Device 1)
```bash
cd LLM-RAG-CLUSTER
python main.py
```
Then open `http://localhost:8089` in your browser to access the Locust UI and start the test.

---

## Monitoring

| Dashboard | URL | What it shows |
|---|---|---|
| Locust UI | `http://localhost:8089` | Live request rate, failure rate, response times |
| Grafana | `http://<Device-4-IP>:3000` | GPU utilization, VRAM, temperature, TPS, active tasks, CPU/RAM |
| Prometheus | `http://<Device-4-IP>:9090` | Raw metrics scrape targets and PromQL queries |
| NGINX VTS | `http://10.2.213.200:8085/status` | Per-worker request count, response time, error codes, node state |

**Key Grafana metrics tracked:**
- `gpu_utilization_percent` — real-time GPU load per node
- `gpu_memory_used_bytes` — VRAM consumption (critical for OOM detection)
- `gpu_temperature_celsius` — thermal monitoring
- `worker_active_tasks` — concurrent requests in-flight per worker
- `llm_tokens_per_second` — generation throughput
- `llm_eval_duration_seconds` / `llm_load_duration_seconds` — inference vs. cold-start latency
- `worker_errors_total` — labelled by error type (`OOM_GPU_Exhausted`, `Ollama_Timeout`, `General_Exception`)

---

## Load Testing

The load test ramps from 0 to 1,000 users in steps of 100 users every 20 seconds, spawning 20 new users per second per step.

**Retry behavior:** Each Locust user retries failed requests up to 5 times with a 3-second delay between attempts. Retryable status codes are `500`, `502`, `503`, and `504`. A single telemetry event is reported to the Locust master only after the final outcome (success or exhausted retries), so reported latency reflects true end-to-end processing time.

To adjust the load shape, edit the following constants in `client/load_generator.py`:

```python
class StepLoadShape(LoadTestShape):
    step_time   = 20    # seconds per step
    step_users  = 100   # users added per step
    spawn_rate  = 20    # users spawned per second during ramp-up
    max_users   = 1000  # hard ceiling
```

---

## Fault Tolerance

**GPU Worker Node failure:** NGINX detects failures passively. After `max_fails=3` failures within a `fail_timeout=60s` window, the node is removed from the pool and traffic is redistributed to the remaining workers. The client-side retry loop ensures in-flight requests are re-routed transparently.

**Load Balancer (Master Node) failure:** Keepalived monitors the heartbeat between Device 2 and Device 3. If Device 2 goes offline, Device 3 promotes itself to Master and claims the VIP within seconds. When Device 2 comes back online, it preempts Device 3 (higher priority) and reclaims the VIP. Both failover scenarios were validated during load testing with a **0% request failure rate**.

---

## System Limitations

- **Model reasoning capacity:** The SmolLM2 (135M) model is chosen for throughput and memory efficiency on consumer hardware. It trades complex reasoning capability for speed and low VRAM usage.
- **WSL network overhead:** Routing ZeroTier traffic through a `netsh` portproxy bridge into WSL adds a virtualization layer that may introduce minor latency.
- **ZeroTier overhead:** The overlay VPN introduces additional latency and potential packet loss compared to a wired LAN.
- **Thermal throttling:** Consumer laptop GPUs are susceptible to throttling under sustained load, which can degrade tokens-per-second over long test windows.
- **Decentralized knowledge base:** The FAISS index is built locally on each worker. Adding or updating documents requires re-indexing on every node manually.


