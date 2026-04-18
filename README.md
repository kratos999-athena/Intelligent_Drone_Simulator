#  AeroGuard UAV Control Center

> **A production-rules–based autonomous drone simulation for wildfire search-and-rescue missions.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Hugging Face Spaces](https://img.shields.io/badge/🤗%20Hugging%20Face-Spaces-orange)](https://huggingface.co/spaces)

---

##  Overview

AeroGuard is an AI-driven UAV (Unmanned Aerial Vehicle) simulator that models an autonomous search-and-rescue drone operating in a dynamic wildfire environment. The system uses a **forward-chaining production rule engine** with salience-based conflict resolution to make real-time decisions under constraint — navigating fire spread, limited battery, and multiple rescue targets simultaneously.

The simulation runs on a 15×15 procedurally-generated grid and features a fully interactive Streamlit dashboard for live telemetry visualization.

---

##  Features

- **Production Rule Engine** — 8 prioritized rules (CRITICAL_BATTERY → IDLE) with salience-based conflict resolution and a visible conflict set
- **Battery-Aware A\* Pathfinding** — Round-trip feasibility check before committing to any rescue mission
- **Dynamic Fire Spread** — Wind-direction and wind-strength parameters influence probabilistic fire propagation each tick
- **Live Telemetry Dashboard** — Real-time grid visualization, mission log, battery bar, sensor readout, and rule trace
- **Procedural Map Generation** — Seed-controlled random environments for reproducible experiments
- **Play / Pause / Step** — Full simulation speed control (1–10 ticks/sec)

---

## Architecture

```
aeroguard/
├── dashboard.py          # Streamlit UI — rendering, controls, telemetry
├── environment.py        # Grid world, fire dynamics, hiker placement
├── production_rules.py   # Production system, working memory, rule specs
├── search.py             # A* search (standard + battery-aware variant)
├── requirements.txt      # Python dependencies
└── README.md
```

### Module Responsibilities

| Module | Responsibility |
|---|---|
| `environment.py` | Grid state, fire spread physics, hiker management, tick loop |
| `production_rules.py` | Working memory, salience table, conflict set, rule conditions/actions |
| `search.py` | `astar()`, `astar_battery_aware()`, `path_is_safe()` helpers |
| `dashboard.py` | Streamlit layout, sidebar controls, metric cards, grid HTML rendering |

### Production Rule Salience Table

| Rule | Salience | Trigger Condition |
|---|---|---|
| `CRITICAL_BATTERY` | 100 | Battery < 25% and not carrying hiker |
| `ABORT_LOW_BATTERY` | 95 | Round-trip to hiker would exhaust battery |
| `HAZARD_AVOIDANCE` | 90 | Planned path intersects active fire |
| `DROP_HIKER_AT_BASE` | 80 | Carrying hiker and at base |
| `RETURN_WITH_HIKER` | 75 | Carrying hiker and not heading to base |
| `TARGET_ACQUIRED` | 60 | New nearest hiker identified or no goal set |
| `EXECUTE_PLAN` | 40 | Valid goal exists and drone is not at goal |
| `IDLE` | 0 | Catch-all / no other rule matches |

---

## Quick Start

### Prerequisites

- Python **3.10** or higher
- `pip` package manager

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/aeroguard-uav.git
cd aeroguard-uav

# 2. (Recommended) Create a virtual environment
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the dashboard
streamlit run dashboard.py
```

The app will open at `http://localhost:8501`.

---

## 🎮 Usage

| Control | Description |
|---|---|
| **▶ Play / Pause** | Toggle continuous simulation |
| **⏭ Step** | Advance exactly one tick |
| **↺ Reset** | Reload map with the current seed |
| **🎲 Random** | Generate a new random map |
| **Map Seed** | Enter any integer to reproduce an exact scenario |
| **Wind Direction** | 8-directional wind selector |
| **Base Spread Prob** | Slider `0.0 – 0.5` — baseline fire spread probability per tick |
| **Wind Strength** | Slider `0.0 – 0.5` — how much wind amplifies spread in its direction |
| **Speed** | Slider `1 – 10` ticks per second |

### Grid Legend

| Symbol | Meaning |
|---|---|
| `◈` | Drone (UAV) |
| `B` | Base / recharge station |
| `H` | Hiker (rescue target) |
| `F` | Active fire cell |
| `+` | Planned drone path |
| `·` | Empty cell |

---

## Configuration

Key constants can be tuned directly in the source files:

**`environment.py`**
```python
FIRE_SPREAD_BASE_PROB = 0.25   # baseline spread probability
WIND_STRENGTH         = 0.35   # wind amplification factor
WIND_MIN_PROB         = 0.05   # minimum spread probability (floor)
```

**`production_rules.py`**
```python
BATTERY_MAX                = 100
BATTERY_CRITICAL_THRESHOLD = 0.25   # fraction — triggers emergency return
SENSOR_RADIUS              = 2      # cells — hazard sensor detection range
```

**`search.py`**
```python
MOVE_BASE_COST = 1    # cost per normal step
HAZARD_COST    = 5    # cost penalty for cells adjacent to fire
```

---

## Dependencies

```
streamlit>=1.35.0
```

> Standard library modules used: `heapq`, `math`, `random`, `dataclasses`, `typing`

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "feat: add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

Please follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](./LICENSE) file for full details.

Copyright © 2025 Aarush

---

## Acknowledgements

- Pathfinding inspired by Hart, Nilsson & Raphael's original A* paper (1968)
- Production system architecture based on classical forward-chaining expert systems (CLIPS / OPS5 tradition)
- UI built with [Streamlit](https://streamlit.io/)