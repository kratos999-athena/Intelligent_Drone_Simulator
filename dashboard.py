import streamlit as st
import time
import random
import environment
from environment import Environment, EMPTY, BASE, FIRE, HIKER
from production_rules import ProductionSystem, WorkingMemory

st.set_page_config(
    page_title="AeroGuard UAV Control Center",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=Share+Tech+Mono&display=swap');

    html, body, [class*="css"] {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 15px;
        background-color: #0b0c10;
        color: #c5c6c7;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: #0d0e14;
        border-right: 1px solid #1f2335;
    }
    section[data-testid="stSidebar"] * { color: #a8b2d8 !important; }

    /* ── Metrics ── */
    div[data-testid="stMetric"] {
        background: #11131a;
        border: 1px solid #1f2335;
        border-radius: 10px;
        padding: 10px 14px;
    }
    div[data-testid="stMetricLabel"] p {
        font-size: 11px !important;
        color: #446 !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    div[data-testid="stMetricValue"] {
        font-size: 22px !important;
        font-family: 'Share Tech Mono', monospace !important;
        color: #66fcf1 !important;
    }
    div[data-testid="stMetricDelta"] { font-size: 11px !important; }

    /* ── Grid: cells sized to fit 15 cols comfortably ── */
    .grid-outer {
        width: 100%;
        overflow-x: auto;   /* scroll if viewport is tiny; normally not needed */
    }
    .grid-container {
        display: inline-grid;
        grid-template-columns: repeat(15, 36px);
        grid-template-rows:    repeat(15, 36px);
        gap: 2px;
        background: #0b0c10;
        padding: 12px;
        border-radius: 10px;
        border: 1px solid #1f2335;
        box-shadow: 0 0 40px rgba(102,252,241,0.04);
    }
    .cell {
        width: 36px; height: 36px;
        border-radius: 4px;
        display: flex; align-items: center; justify-content: center;
        font-family: 'Share Tech Mono', monospace;
        font-size: 15px;
        font-weight: 700;
    }
    .cell-empty { background: #13151d; color: #252737; }
    .cell-base  { background: #0d2137; color: #4fc3f7; border: 1px solid #1565c0; }
    .cell-fire  { background: #3b0f08; color: #ff6b35; border: 1px solid #7b1a0a;
                  animation: flicker 1.4s infinite alternate; }
    .cell-hiker { background: #0a2e1a; color: #69f0ae; border: 1px solid #1b5e20; }
    .cell-path  { background: #1e1a08; color: #ffd54f; opacity: 0.75; }
    .drone-cell { background: #0f2020 !important; border: 1px solid #66fcf1 !important; }
    .drone-icon {
        font-size: 18px;
        color: #66fcf1;
        text-shadow: 0 0 8px #66fcf1, 0 0 16px #66fcf188;
    }

    @keyframes flicker {
        0%   { opacity: 0.80; }
        50%  { opacity: 1.00; box-shadow: 0 0 6px #ff6b35aa; }
        100% { opacity: 0.88; }
    }

    /* ── Telemetry row cards ── */
    .tele-grid {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 10px;
        margin-top: 4px;
    }
    .tele-card {
        background: #0d0e14;
        border: 1px solid #1f2335;
        border-radius: 8px;
        padding: 14px 16px;
        font-family: 'Share Tech Mono', monospace;
        font-size: 13px;
        line-height: 1.8;
    }
    .tele-card-wide {
        background: #0d0e14;
        border: 1px solid #1f2335;
        border-radius: 8px;
        padding: 14px 16px;
        font-family: 'Share Tech Mono', monospace;
        font-size: 13px;
        line-height: 1.8;
        grid-column: span 3;
    }
    .tele-header {
        color: #66fcf1;
        font-size: 11px;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        border-bottom: 1px solid #1f2335;
        padding-bottom: 6px;
        margin-bottom: 10px;
    }
    .tele-label { color: #446; font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; }
    .tele-value { color: #c5c6c7; font-size: 14px; }
    .rule-win   { color: #69f0ae; font-weight: 700; font-size: 13px; }
    .rule-lose  { color: #2a2d3e; text-decoration: line-through; font-size: 12px; }
    .hazard-warn { color: #ff6b35; }
    .hazard-ok   { color: #69f0ae; }

    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.05em;
    }
    .badge-payload { background: #0d2137; color: #4fc3f7; border: 1px solid #1565c0; }
    .badge-empty   { background: #13151d; color: #446;    border: 1px solid #252737; }

    /* ── Battery bar ── */
    .bat-track {
        background: #13151d;
        border-radius: 3px;
        height: 6px;
        width: 100%;
        margin: 4px 0 2px;
        overflow: hidden;
    }
    .bat-fill { height: 6px; border-radius: 3px; }

    /* ── Mission log ── */
    .log-entry {
        font-size: 12px;
        padding: 3px 0;
        border-bottom: 1px solid #13151d;
        color: #446;
        font-family: 'Share Tech Mono', monospace;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .log-entry-new { color: #a8b2d8 !important; }

    /* headings */
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif !important; color: #66fcf1 !important; }
    h1 { font-size: 26px !important; letter-spacing: -0.02em; }
</style>
""", unsafe_allow_html=True)

WIND_OPTIONS = {
    "North":      (-1, 0), "South":      (1, 0),
    "East":       (0, 1),  "West":       (0, -1),
    "North-East": (-1, 1), "North-West": (-1, -1),
    "South-East": (1, 1),  "South-West": (1, -1),
}
WIND_ARROWS = {
    "North": "↑", "South": "↓", "East": "→", "West": "←",
    "North-East": "↗", "North-West": "↖", "South-East": "↘", "South-West": "↙",
}


def init_simulation(seed: int | None = None):
    if seed is None:
        seed = random.randint(0, 99999)
    env = Environment(size=15, seed=seed)
    wm  = WorkingMemory(start_pos=env.base_pos, battery=100)
    ps  = ProductionSystem(env)
    st.session_state.env            = env
    st.session_state.wm             = wm
    st.session_state.ps             = ps
    st.session_state.tick           = 0
    st.session_state.is_running     = False
    st.session_state.initial_hikers = len(env.get_unrescued_hikers())
    st.session_state.mission_log    = []
    st.session_state.seed           = seed


if "env" not in st.session_state:
    init_simulation()

env: Environment     = st.session_state.env
wm:  WorkingMemory   = st.session_state.wm
ps:  ProductionSystem = st.session_state.ps


def log_event(msg: str):
    st.session_state.mission_log.insert(
        0, f"T{st.session_state.tick:03d}  {msg}"
    )
    st.session_state.mission_log = st.session_state.mission_log[:20]



with st.sidebar:
    st.markdown("## AeroGuard Comm")
    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("▶ Play/Pause", use_container_width=True):
            st.session_state.is_running = not st.session_state.is_running
    with c2:
        if st.button("⏭ Step", use_container_width=True):
            st.session_state.is_running = False
            env.tick()
            old_rule = wm.last_rule_fired
            ps.run_cycle(wm)
            st.session_state.tick += 1
            if wm.status_message:
                log_event(wm.status_message)

    st.markdown("---")
    seed_input = st.number_input(
        "Map Seed", value=int(st.session_state.seed),
        min_value=0, max_value=999999, step=1,
        help="Edit seed then press Reset to load that exact map"
    )

    rb, rr = st.columns(2)
    with rb:
        if st.button("↺ Reset", type="primary", use_container_width=True):
            init_simulation(seed=int(seed_input))
            st.rerun()
    with rr:
        if st.button(" Random", use_container_width=True):
            init_simulation(seed=random.randint(0, 999999))
            st.rerun()

    st.markdown("---")
    st.markdown("**Wind Direction**")
    current_wind_key = list(WIND_OPTIONS.keys())[
        list(WIND_OPTIONS.values()).index(environment.WIND_DIRECTION)
    ]
    selected_wind = st.selectbox(
        "Wind", list(WIND_OPTIONS.keys()),
        index=list(WIND_OPTIONS.keys()).index(current_wind_key),
        label_visibility="collapsed",
    )
    environment.WIND_DIRECTION = WIND_OPTIONS[selected_wind]
    environment._WIND_UNIT     = environment._wind_unit()

    st.markdown("**Fire Dynamics**")
    environment.FIRE_SPREAD_BASE_PROB = st.slider(
        "Base Spread Prob", 0.0, 0.5,
        float(environment.FIRE_SPREAD_BASE_PROB), 0.01
    )
    environment.WIND_STRENGTH = st.slider(
        "Wind Strength", 0.0, 0.5,
        float(environment.WIND_STRENGTH), 0.01
    )

    st.markdown("---")
    sim_speed = st.slider("Speed (ticks/sec)", 1, 10, 3)
    st.markdown(
        f"<small style='color:#252737;font-family:Share Tech Mono,monospace;'>"
        f"seed: {st.session_state.seed}</small>",
        unsafe_allow_html=True,
    )
st.markdown("# AeroGuard UAV · Live Telemetry")

rescued_count    = len(env.rescued)
hikers_remaining = len(env.get_unrescued_hikers())
bat_pct          = wm.battery
wind_arrow       = WIND_ARROWS.get(selected_wind, "?")

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Tick",        f"{st.session_state.tick:03d}")
m2.metric("Battery",     f"{bat_pct}%",
          delta=f"-{100-bat_pct}%" if bat_pct < 100 else None,
          delta_color="inverse")
m3.metric("Rescued",     f"{rescued_count}/{st.session_state.initial_hikers}")
m4.metric("Hikers Left", str(hikers_remaining))
m5.metric("Wind",        f"{wind_arrow} {selected_wind}")
m6.metric("Rule",        wm.last_rule_fired or "INIT")

st.markdown("---")
grid_col, tele_col = st.columns([596, 500], gap="medium")

with grid_col:
    path_set = set(map(tuple, wm.path)) if wm.path else set()

    grid_html = '<div class="grid-outer"><div class="grid-container">'
    for r in range(env.size):
        for c in range(env.size):
            cell_type = env.grid[r][c]
            is_drone  = (r, c) == wm.position
            is_path   = (r, c) in path_set

            if is_drone:
                grid_html += (
                    '<div class="cell drone-cell">'
                    '<span class="drone-icon">◈</span></div>'
                )
                continue

            if cell_type == BASE:
                grid_html += '<div class="cell cell-base">B</div>'
            elif cell_type == FIRE:
                grid_html += '<div class="cell cell-fire">F</div>'
            elif cell_type == HIKER:
                grid_html += '<div class="cell cell-hiker">H</div>'
            elif is_path:
                grid_html += '<div class="cell cell-path">+</div>'
            else:
                grid_html += '<div class="cell cell-empty">·</div>'

    grid_html += "</div></div>"
    st.markdown(grid_html, unsafe_allow_html=True)

    st.markdown(
        "<small style='color:#252737;font-family:Share Tech Mono,monospace;'>"
        "◈ Drone &nbsp;·&nbsp; B Base &nbsp;·&nbsp; H Hiker "
        "&nbsp;·&nbsp; F Fire &nbsp;·&nbsp; + Path</small>",
        unsafe_allow_html=True,
    )

# ── Telemetry cards ───────────────────────────────────────────────────────────
with tele_col:
    bat_color = (
        "#ff6b35" if bat_pct < 25 else
        "#ffd54f" if bat_pct < 50 else
        "#69f0ae"
    )
    payload_badge = (
        '<span class="badge badge-payload">HIKER ON BOARD</span>'
        if wm.carrying_hiker
        else '<span class="badge badge-empty">EMPTY</span>'
    )
    hazard_html = (
        f'<span class="hazard-warn">⚠ {len(wm.hazard_sensors)} fire(s) in r=2 zone</span>'
        if wm.hazard_sensors
        else '<span class="hazard-ok">✓ Sensors clear</span>'
    )

    cs_html = ""
    if wm.conflict_set:
        for i, rule in enumerate(wm.conflict_set):
            cls = "rule-win" if i == 0 else "rule-lose"
            prefix = "▶ " if i == 0 else "  "
            cs_html += f'<div class="{cls}">{prefix}{rule}</div>'
    else:
        cs_html = "<div style='color:#252737'>No rules matched</div>"

    log_html = ""
    for i, entry in enumerate((st.session_state.mission_log or ["— no events yet"])[:10]):
        cls = "log-entry log-entry-new" if i == 0 else "log-entry"
        log_html += f'<div class="{cls}">{entry}</div>'

    tele_html = f"""
    <div class="tele-grid">

      <!-- Status + payload -->
      <div class="tele-card" style="grid-column: span 2;">
        <div class="tele-header">◈ Current Action</div>
        <div class="tele-value" style="color:#a8b2d8; font-size:13px;">
          {wm.status_message or "—"}
        </div>
        <div style="margin-top:10px;">
          <span class="tele-label">Goal:</span>
          <span class="tele-value"> {wm.goal or "None"}</span>
        </div>
        <div style="margin-top:6px;">{payload_badge}</div>
      </div>

      <!-- Battery -->
      <div class="tele-card">
        <div class="tele-header">◈ Battery</div>
        <div class="tele-value" style="font-size:28px; color:{bat_color};">
          {bat_pct}%
        </div>
        <div class="bat-track">
          <div class="bat-fill" style="width:{bat_pct}%; background:{bat_color};"></div>
        </div>
        <div style="margin-top:8px;">{hazard_html}</div>
      </div>

      <!-- Conflict set -->
      <div class="tele-card" style="grid-column: span 3;">
        <div class="tele-header">◈ Conflict Set Resolution</div>
        {cs_html}
      </div>

      <!-- Mission log -->
      <div class="tele-card" style="grid-column: span 3;">
        <div class="tele-header">◈ Mission Log</div>
        {log_html}
      </div>

    </div>
    """
    st.markdown(tele_html, unsafe_allow_html=True)

if wm.battery <= 0:
    st.error("MISSION FAILED — UAV battery depleted.")
    st.session_state.is_running = False
elif hikers_remaining == 0 and not wm.carrying_hiker and wm.position == env.base_pos:
    st.success("MISSION COMPLETE — All targets rescued and drone recovered.")
    st.session_state.is_running = False
if st.session_state.is_running:
    mission_over = wm.battery <= 0 or (
        hikers_remaining == 0
        and not wm.carrying_hiker
        and wm.position == env.base_pos
    )
    if not mission_over:
        time.sleep(1.0 / sim_speed)
        env.tick()
        ps.run_cycle(wm)
        st.session_state.tick += 1
        if wm.status_message:
            log_event(wm.status_message)
        st.rerun()
    else:
        st.session_state.is_running = False