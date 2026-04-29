# Steward
### Reinforcement Learning Based Resource Manager

---

## Overview

Steward is an AI-powered operating system resource manager that employs a Reinforcement Learning agent to make intelligent, adaptive scheduling decisions across CPU and RAM resources. Unlike conventional schedulers that operate on fixed heuristics, Steward's agent learns an optimal scheduling policy through direct interaction with a simulated OS environment — dynamically responding to system load, minimizing process wait time, and maximizing throughput.

Developed as part of an Operating Systems course project, Steward demonstrates the practical application of deep RL in systems-level decision making, and provides a live dashboard for real-time visualization of agent behaviour under varying load conditions.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Training the Agent](#training-the-agent)
- [Benchmarking](#benchmarking)
- [Features](#features)
- [Results](#results)
- [Conclusions](#conclusions)
- [Team](#team)

---

## Architecture

Steward is composed of four layers:

**1. RL Environment (`env/`)**
A custom Gymnasium environment that simulates an OS resource manager. Processes arrive stochastically with random CPU and RAM demands. At each timestep, the agent observes the current system state and selects one of three actions: schedule, defer, or kill. The environment enforces resource constraints and returns a shaped reward signal to guide learning.

**2. RL Agent (`train.py`)**
A Proximal Policy Optimization (PPO) agent trained via Stable-Baselines3. The agent learns a policy mapping observations to actions over 100,000 timesteps. Training progress is logged episode-by-episode and visualized as a reward curve.

**3. Backend (`backend/`)**
A Flask server with Socket.IO that runs the simulation loop in real time. The trained agent is loaded and queried at each tick. Resource state, scheduling decisions, and reward signals are emitted as events to connected frontend clients. Exposes REST endpoints for stress testing and simulation reset.

**4. Frontend (`frontend/`)**
A browser-based dashboard built with HTML, CSS, JavaScript, and Chart.js. Subscribes to Socket.IO events and renders live CPU/RAM usage charts, a scrolling decision log, and a side-by-side comparison panel between the RL agent and a Round-Robin baseline scheduler.

---

## Tech Stack

| Layer | Technology |
|---|---|
| RL Agent | Stable-Baselines3 (PPO), Gymnasium |
| Simulation Engine | Python, NumPy |
| Backend Server | Flask, Flask-SocketIO |
| Frontend Dashboard | HTML, CSS, JavaScript, Chart.js |
| Version Control | Git, GitHub |

---

## Project Structure

steward/
├── env/
│   ├── init.py
│   ├── resource_env.py       # Custom Gymnasium environment
│   └── process_queue.py      # Process generator and queue manager
├── baseline/
│   ├── init.py
│   └── round_robin.py        # Round-Robin baseline scheduler
├── backend/
│   ├── init.py
│   └── server.py             # Flask + Socket.IO server
├── frontend/
│   └── index.html            # Live dashboard
├── models/
│   └── steward_ppo.zip       # Saved trained model (generated after training)
├── assets/
│   └── reward_curve.png      # Training reward curve (generated after training)
├── train.py                  # Training script
├── benchmark.py              # RL vs Round-Robin benchmark
├── main.py                   # Environment sanity check
├── requirements.txt
└── README.md

---

## Getting Started

### Prerequisites

- Python 3.9 or higher
- pip

### Installation

Clone the repository:

```bash
git clone https://github.com/<your-username>/steward.git
cd steward
```

Create and activate a virtual environment:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Verify Environment

Run the environment check to confirm the Gymnasium environment is set up correctly:

```bash
python main.py
```

Expected output:
Environment check passed.
Initial obs: [0. 0. 5. 1.]

---

## Training the Agent

Train the PPO agent for 100,000 timesteps:

```bash
python train.py
```

This will:
- Train the agent and log per-episode rewards
- Save the trained model to `models/steward_ppo.zip`
- Generate and save the reward curve to `assets/reward_curve.png`

Training takes approximately 5–10 minutes on CPU.

---

## Benchmarking

Compare the trained RL agent against the Round-Robin baseline:

```bash
python benchmark.py
```

This runs both schedulers over 200 ticks under identical conditions and prints a comparison table of completed processes, final CPU/RAM usage, and average wait time.

---

## Features

**Adaptive Scheduling**
The PPO agent learns to balance CPU and RAM consumption dynamically, deferring or killing low-priority processes when resources are constrained rather than following a fixed rule.

**Stress Test Mode**
A dedicated API endpoint (`/api/stress-test`) injects a burst of 20 processes simultaneously, allowing real-time observation of how the RL agent adapts under sudden load spikes compared to Round-Robin.

**Live Dashboard**
The frontend dashboard streams real-time CPU and RAM usage charts, a live decision log showing per-process scheduling actions, and a side-by-side throughput comparison panel between the RL agent and the baseline scheduler.

**Reward Replay Panel**
The dashboard displays the agent's cumulative reward curve from training, providing visual evidence of the learning process over time.

---

## Results

> This section will be updated upon project completion.

| Metric | RL Agent (Steward) | Round-Robin |
|---|---|---|
| Processes Completed (200 ticks) | — | — |
| Average Wait Time | — | — |
| Final CPU Usage % | — | — |
| Final RAM Usage % | — | — |
| Crash Incidents | — | — |

**Reward Curve**

> `assets/reward_curve.png` — to be added after training.

**Stress Test Observations**

> Qualitative and quantitative observations from the stress test scenario to be documented here.

---

## Conclusions

> This section will be completed after final evaluation and benchmarking.

Areas to be addressed:
- Summary of agent performance relative to the Round-Robin baseline
- Analysis of reward function design and its effect on learned behaviour
- Limitations of the current simulation (single-node, discrete action space)
- Potential extensions: multi-resource scheduling, continuous action spaces, real OS integration via `/proc` filesystem

---

## Team

| Name | Role |
|---|---|
| Anvi Trivedi | RL & AI Core |
| Zakiur Rahman | Backend & Integration |
| Prachi Bhowal | Frontend & Documentation |

---
