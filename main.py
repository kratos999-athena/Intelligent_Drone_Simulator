"""
main.py  –  AeroGuard UAV Simulation  (Postgraduate Upgrade v2)
================================================================

Visual output is preserved from the baseline.

ADDITIONS
---------
* Wind indicator in ``render_status``:  a compass-rose arrow derived from
  ``WIND_DIRECTION`` is shown on the status panel so the operator can
  instantly see which way the fire is being pushed.

* Conflict-set display:  the status panel now shows all rules that matched
  in the last cycle alongside the winner, making the salience-based
  conflict resolution visible at runtime.
"""

import time
import os
from environment import Environment, EMPTY, BASE, FIRE, HIKER, WIND_DIRECTION
from production_rules import ProductionSystem, WorkingMemory

GRID_SIZE  = 15
MAX_TICKS  = 30
TICK_DELAY = 0.4

SYMBOL_EMPTY   = "."
SYMBOL_BASE    = "B"
SYMBOL_FIRE    = "#"
SYMBOL_HIKER   = "H"
SYMBOL_DRONE   = "D"
SYMBOL_UNKNOWN = "?"


# ── Wind display helper ───────────────────────────────────────────────────────

_WIND_ARROWS: dict[tuple[int, int], str] = {
    (-1,  0): "↑  (North)",
    ( 1,  0): "↓  (South)",
    ( 0,  1): "→  (East)",
    ( 0, -1): "←  (West)",
    (-1,  1): "↗  (North-East)",
    (-1, -1): "↖  (North-West)",
    ( 1,  1): "↘  (South-East)",
    ( 1, -1): "↙  (South-West)",
}


def wind_label() -> str:
    """
    Convert the global ``WIND_DIRECTION`` vector to a human-readable
    compass arrow string for the status panel.

    The vector is normalised to its sign components so that any magnitude
    maps to the same compass label — e.g. both (2, 2) and (1, 1) display
    as "↘  (South-East)".
    """
    dr, dc = WIND_DIRECTION
    key = (
        0 if dr == 0 else (1 if dr > 0 else -1),
        0 if dc == 0 else (1 if dc > 0 else -1),
    )
    return _WIND_ARROWS.get(key, f"? {WIND_DIRECTION}")


# ── Screen helpers ────────────────────────────────────────────────────────────

def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


# ── Renderers ─────────────────────────────────────────────────────────────────

def render_grid(env: Environment, drone_pos: tuple[int, int]) -> str:
    """Render the 15 × 15 grid with the drone overlaid at ``drone_pos``."""
    lines: list[str] = []
    col_header = "   " + " ".join(
        f"{c:1}" if c < 10 else f"{c}" for c in range(env.size)
    )
    lines.append(col_header)
    lines.append("   " + "-" * (env.size * 2 - 1))

    for r in range(env.size):
        row_str = f"{r:2}|"
        for c in range(env.size):
            if (r, c) == drone_pos:
                ch = SYMBOL_DRONE
            else:
                cell = env.grid[r][c]
                if cell == EMPTY:
                    ch = SYMBOL_EMPTY
                elif cell == BASE:
                    ch = SYMBOL_BASE
                elif cell == FIRE:
                    ch = SYMBOL_FIRE
                elif cell == HIKER:
                    ch = SYMBOL_HIKER
                else:
                    ch = SYMBOL_UNKNOWN
            row_str += ch + " "
        lines.append(row_str)

    return "\n".join(lines)


def render_status(wm: WorkingMemory,
                  tick: int,
                  total_rescued: int,
                  hikers_remaining: int) -> str:
    """
    Render the status panel beneath the grid.

    ADDITIONS vs baseline
    ---------------------
    * **Wind**        : compass arrow + direction label derived from
                        ``WIND_DIRECTION``.
    * **Conflict Set**: names of all rules that matched this cycle,
                        showing the salience competition in real time.
    """
    bar_len  = 20
    filled   = int(bar_len * wm.battery / 100)
    battery_bar = "[" + "=" * filled + "-" * (bar_len - filled) + "]"

    # Conflict-set display: highlight winner with ★
    if wm.conflict_set:
        winner = wm.last_rule_fired or ""
        cs_str = ", ".join(
            f"★{n}" if n == winner else n
            for n in wm.conflict_set
        )
    else:
        cs_str = "—"

    # Sensor display: abbreviate long lists
    if wm.hazard_sensors:
        sensor_str = f"{len(wm.hazard_sensors)} fire cell(s) in r={2} zone"
    else:
        sensor_str = "Clear"

    lines = [
        "=" * 55,
        f"  AEROGUARD AUTONOMOUS UAV  —  TICK {tick:02d} / {MAX_TICKS}",
        "=" * 55,
        f"  Position     : {wm.position}",
        f"  Battery      : {battery_bar} {wm.battery}%",
        f"  Wind         : {wind_label()}",          # ← NEW
        f"  Goal         : {wm.goal}",
        f"  Payload      : {'HIKER ON BOARD' if wm.carrying_hiker else 'None'}",
        f"  Rule Fired   : {wm.last_rule_fired}",
        f"  Conflict Set : {cs_str}",                # ← NEW
        f"  Status       : {wm.status_message}",
        f"  Rescued      : {total_rescued}",
        f"  Hikers Left  : {hikers_remaining}",
        f"  Fire Sensors : {sensor_str}",
        "=" * 55,
    ]
    return "\n".join(lines)


def render_legend() -> str:
    return "  LEGEND: D=Drone  B=Base  H=Hiker  #=Fire  .=Empty"


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    env            = Environment(size=GRID_SIZE, seed=42)
    start          = env.base_pos
    wm             = WorkingMemory(start_pos=start, battery=100)
    ps             = ProductionSystem(env)
    initial_hikers = len(env.get_unrescued_hikers())

    for tick in range(1, MAX_TICKS + 1):
        env.tick()
        ps.run_cycle(wm)

        rescued_count    = len(env.rescued)
        hikers_remaining = len(env.get_unrescued_hikers())

        clear_screen()
        print(render_grid(env, wm.position))
        print()
        print(render_status(wm, tick, rescued_count, hikers_remaining))
        print(render_legend())
        print()

        if wm.battery <= 0:
            print("  UAV battery depleted. Mission terminated.")
            break

        if hikers_remaining == 0 and not wm.carrying_hiker:
            if rescued_count == initial_hikers:
                print("  All hikers rescued. Mission complete.")
            else:
                print("  No more accessible hikers. Mission ended.")
            time.sleep(1)
            break

        time.sleep(TICK_DELAY)

    print()
    print(f"  Final rescued   : {len(env.rescued)} / {initial_hikers}")
    print(f"  Ticks elapsed   : {env.tick_count}")
    print(f"  Battery remaining: {wm.battery}%")
    print()


if __name__ == "__main__":
    main()