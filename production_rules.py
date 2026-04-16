

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable

from environment import BASE, FIRE, HIKER, WIND_DIRECTION
from search import astar_battery_aware, astar, path_is_safe

BATTERY_MAX:                int   = 100
BATTERY_CRITICAL_THRESHOLD: float = 0.25   
SENSOR_RADIUS:              int   = 2       

SALIENCE: dict[str, int] = {
    "CRITICAL_BATTERY":   100,
    "ABORT_LOW_BATTERY":   95,
    "HAZARD_AVOIDANCE":    90,
    "DROP_HIKER_AT_BASE":  80,
    "RETURN_WITH_HIKER":   75,
    "TARGET_ACQUIRED":     60,
    "EXECUTE_PLAN":        40,
    "IDLE":                 0,
}



@dataclass(order=False)
class RuleCandidate:
    name:     str
    salience: int
    action:   Callable[["WorkingMemory"], None]



class WorkingMemory:

    def __init__(self, start_pos: tuple[int, int], battery: int = BATTERY_MAX):
        self.position:       tuple[int, int]      = start_pos
        self.battery:        int                  = battery
        self.payload:        bool                 = False
        self.goal:           tuple[int, int] | None = None
        self.path:           list[tuple[int, int]] = []
        self.hazard_sensors: list[tuple[int, int]] = []
        self.last_rule_fired: str | None           = None
        self.carrying_hiker: bool                  = False
        self.status_message: str                   = ""
        # Upgrade 2
        self.abort_reason:   str | None            = None
        # Upgrade 3
        self.conflict_set:   list[str]             = []

    def battery_fraction(self) -> float:
        return self.battery / BATTERY_MAX

    def update_sensors(self, env) -> None:
        r, c = self.position
        self.hazard_sensors = [
            (nr, nc)
            for (nr, nc) in env.get_cells_in_radius(r, c, SENSOR_RADIUS)
            if env.grid[nr][nc] == FIRE
        ]

class ProductionSystem:
    def __init__(self, env):
        self.env = env

        self._rule_specs: list[tuple[
            Callable[["WorkingMemory"], bool],
            Callable[["WorkingMemory"], None],
            str,
        ]] = [
            (self._cond_critical_battery,   self._act_critical_battery,   "CRITICAL_BATTERY"),
            (self._cond_abort_low_battery,  self._act_abort_low_battery,  "ABORT_LOW_BATTERY"),
            (self._cond_hazard_avoidance,   self._act_hazard_avoidance,   "HAZARD_AVOIDANCE"),
            (self._cond_drop_hiker_at_base, self._act_drop_hiker_at_base, "DROP_HIKER_AT_BASE"),
            (self._cond_return_with_hiker,  self._act_return_with_hiker,  "RETURN_WITH_HIKER"),
            (self._cond_target_acquired,    self._act_target_acquired,    "TARGET_ACQUIRED"),
            (self._cond_execute_plan,       self._act_execute_plan,       "EXECUTE_PLAN"),
            (self._cond_idle,               self._act_idle,               "IDLE"),
        ]


    def _cond_critical_battery(self, wm: WorkingMemory) -> bool:
        return (wm.battery_fraction() < BATTERY_CRITICAL_THRESHOLD
                and wm.goal != self.env.base_pos
                and not wm.carrying_hiker)

    def _act_critical_battery(self, wm: WorkingMemory) -> None:
        wm.goal           = self.env.base_pos
        wm.path           = []
        wm.last_rule_fired = "CRITICAL_BATTERY"
        wm.status_message  = "Battery critical — emergency return to base"


    def _cond_abort_low_battery(self, wm: WorkingMemory) -> bool:
        return wm.abort_reason == "BATTERY_INSUFFICIENT"

    def _act_abort_low_battery(self, wm: WorkingMemory) -> None:

        wm.abort_reason    = None          # consume the signal
        wm.goal            = self.env.base_pos
        wm.path            = []
        wm.last_rule_fired = "ABORT_LOW_BATTERY"
        wm.status_message  = ("Rescue aborted — insufficient battery for "
                              "round trip; returning to base")


    def _cond_hazard_avoidance(self, wm: WorkingMemory) -> bool:
        if not wm.path:
            return False
        if not path_is_safe(self.env, wm.path):
            return True
        if len(wm.path) > 1:
            nr, nc = wm.path[1]
            if self.env.grid[nr][nc] == FIRE:
                return True
        return False

    def _act_hazard_avoidance(self, wm: WorkingMemory) -> None:
        wm.path            = []
        wm.last_rule_fired = "HAZARD_AVOIDANCE"
        wm.status_message  = "Path compromised by fire — recalculating"

    def _cond_drop_hiker_at_base(self, wm: WorkingMemory) -> bool:
        return wm.carrying_hiker and wm.position == self.env.base_pos

    def _act_drop_hiker_at_base(self, wm: WorkingMemory) -> None:
        wm.carrying_hiker  = False
        wm.payload         = False
        wm.goal            = None
        wm.path            = []
        wm.last_rule_fired = "DROP_HIKER_AT_BASE"
        wm.battery         = BATTERY_MAX
        wm.status_message  = "Hiker delivered to base — battery recharged, ready for next mission"


    def _cond_return_with_hiker(self, wm: WorkingMemory) -> bool:
        return wm.carrying_hiker and wm.goal != self.env.base_pos

    def _act_return_with_hiker(self, wm: WorkingMemory) -> None:
        wm.goal            = self.env.base_pos
        wm.path            = []
        wm.last_rule_fired = "RETURN_WITH_HIKER"
        wm.status_message  = "Hiker on board — returning to base"

    def _cond_target_acquired(self, wm: WorkingMemory) -> bool:
        if wm.carrying_hiker:
            return False
        if wm.battery_fraction() <= BATTERY_CRITICAL_THRESHOLD:
            return False
        hikers = self.env.get_unrescued_hikers()
        if hikers:
            nearest = min(
                hikers,
                key=lambda h: abs(h[0] - wm.position[0]) + abs(h[1] - wm.position[1])
            )
            
            if wm.goal == nearest and wm.path:
                return False
            return wm.goal != nearest
       
        return wm.goal != self.env.base_pos

    def _act_target_acquired(self, wm: WorkingMemory) -> None:
        
        hikers = self.env.get_unrescued_hikers()
        if not hikers:
            wm.goal            = self.env.base_pos
            wm.path            = []
            wm.last_rule_fired = "TARGET_ACQUIRED"
            wm.status_message  = "No hikers remaining — returning to base"
            return

        nearest = min(
            hikers,
            key=lambda h: abs(h[0] - wm.position[0]) + abs(h[1] - wm.position[1])
        )

      
        path, reason = astar_battery_aware(
            env     = self.env,
            start   = wm.position,
            goal    = nearest,
            battery = wm.battery,
            base    = self.env.base_pos,
        )

        if reason == "OK":
            wm.goal            = nearest
            wm.path            = path   
            wm.abort_reason    = None
            wm.last_rule_fired = "TARGET_ACQUIRED"
            wm.status_message  = f"Hiker at {nearest} is reachable — plotting course"
        elif reason == "BATTERY_INSUFFICIENT":
            
            wm.abort_reason    = "BATTERY_INSUFFICIENT"
            wm.last_rule_fired = "TARGET_ACQUIRED"
            wm.status_message  = (f"Hiker at {nearest} unreachable on current "
                                   f"battery ({wm.battery}%) — aborting")
        else:
            
            wm.goal            = nearest
            wm.path            = []
            wm.abort_reason    = None
            wm.last_rule_fired = "TARGET_ACQUIRED"
            wm.status_message  = f"No viable path to {nearest} ({reason})"

    def _cond_execute_plan(self, wm: WorkingMemory) -> bool:
        
        if wm.goal is None:
            return False
        if wm.position == wm.goal:
            return False
        return True

    def _act_execute_plan(self, wm: WorkingMemory) -> None:

        if not wm.path:
            new_path = astar(self.env, wm.position, wm.goal)
            if new_path:
                wm.path            = new_path
                wm.last_rule_fired = "EXECUTE_PLAN"
                wm.status_message  = f"Path recalculated to {wm.goal}"
            else:
                wm.last_rule_fired = "NO_PATH"
                wm.status_message  = f"No path available to {wm.goal}"
            return

        if len(wm.path) > 1:
            wm.path.pop(0)
            new_pos = wm.path[0]
            r, c = new_pos

            if self.env.grid[r][c] == FIRE:
                wm.path           = []
                wm.status_message = "Next step caught fire — recalculating"
                return

            wm.position  = new_pos
            wm.battery  -= 1

            if self.env.grid[r][c] == HIKER:
                rescued = self.env.rescue_hiker(r, c)
                if rescued:
                    wm.carrying_hiker = True
                    wm.payload        = True
                    wm.goal           = self.env.base_pos
                    wm.path           = []
                    wm.status_message = f"Hiker rescued at {new_pos} — returning to base"

            wm.last_rule_fired = "EXECUTE_PLAN"

        elif len(wm.path) == 1 and wm.path[0] == wm.goal:
            wm.last_rule_fired = "GOAL_REACHED"
            wm.status_message  = f"Goal {wm.goal} reached"
            wm.path            = []
            wm.goal            = None

    def _cond_idle(self, wm: WorkingMemory) -> bool:

        return True

    def _act_idle(self, wm: WorkingMemory) -> None:
        wm.last_rule_fired = "IDLE"
        wm.status_message  = "No active task — holding position"

    def _build_conflict_set(self, wm: WorkingMemory) -> list[RuleCandidate]:
        
        conflict_set: list[RuleCandidate] = []
        for cond_fn, act_fn, name in self._rule_specs:
            if cond_fn(wm):
                conflict_set.append(
                    RuleCandidate(
                        name=name,
                        salience=SALIENCE[name],
                        action=act_fn,
                    )
                )
        conflict_set.sort(key=lambda rc: rc.salience, reverse=True)
        return conflict_set

    def run_cycle(self, wm: WorkingMemory) -> None:

        wm.update_sensors(self.env)
        conflict_set = self._build_conflict_set(wm)
        wm.conflict_set = [rc.name for rc in conflict_set]   

        if not conflict_set:
            wm.last_rule_fired = "NONE"
            wm.status_message  = "No rules matched — system error"
            return

        winner: RuleCandidate = conflict_set[0]  
        winner.action(wm)