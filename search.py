
import heapq
from environment import FIRE

MOVE_BASE_COST: int   = 1
HAZARD_COST:    int   = 5
INFINITY:       float = float('inf')



class Node:

    __slots__ = ("position", "g", "h", "f", "parent", "steps")

    def __init__(self, position: tuple[int, int],
                 g: float, h: float,
                 parent: "Node | None" = None,
                 steps: int = 0):
        self.position = position
        self.g        = g
        self.h        = h
        self.f        = g + h
        self.parent   = parent
        self.steps    = steps         

    def __lt__(self, other: "Node") -> bool:
        return self.f < other.f

def manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    """Admissible Manhattan distance heuristic."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def step_cost(env, nr: int, nc: int) -> float:
    if env.grid[nr][nc] == FIRE:
        return INFINITY
    if env.is_adjacent_to_fire(nr, nc):
        return HAZARD_COST
    return MOVE_BASE_COST


def get_neighbors(env, r: int, c: int) -> list[tuple[int, int]]:
    
    neighbors = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if env.in_bounds(nr, nc) and env.grid[nr][nc] != FIRE:
            neighbors.append((nr, nc))
    return neighbors


def _astar_raw(env, start: tuple[int, int],
               goal:  tuple[int, int]) -> "Node | None":
    if start == goal:
        return Node(start, 0, 0, steps=0)

    open_heap: list[Node] = []
    start_node = Node(start, g=0, h=manhattan(start, goal), steps=0)
    heapq.heappush(open_heap, start_node)

    g_costs: dict[tuple[int, int], float] = {start: 0.0}
    closed_set: set[tuple[int, int]] = set()

    while open_heap:
        current = heapq.heappop(open_heap)
        pos = current.position

        if pos in closed_set:
            continue
        closed_set.add(pos)

        if pos == goal:
            return current         

        r, c = pos
        for nr, nc in get_neighbors(env, r, c):
            if (nr, nc) in closed_set:
                continue
            cost = step_cost(env, nr, nc)
            if cost == INFINITY:
                continue
            new_g = current.g + cost
            if (nr, nc) not in g_costs or new_g < g_costs[(nr, nc)]:
                g_costs[(nr, nc)] = new_g
                h = manhattan((nr, nc), goal)
                child = Node((nr, nc), new_g, h,
                             parent=current,
                             steps=current.steps + 1)
                heapq.heappush(open_heap, child)

    return None


def _reconstruct_path(goal_node: "Node") -> list[tuple[int, int]]:
    """Walk the parent chain from ``goal_node`` back to the root."""
    path: list[tuple[int, int]] = []
    node: "Node | None" = goal_node
    while node is not None:
        path.append(node.position)
        node = node.parent
    path.reverse()
    return path

def astar_battery_aware(
    env,
    start:   tuple[int, int],
    goal:    tuple[int, int],
    battery: int,
    base:    tuple[int, int],
) -> tuple[list[tuple[int, int]] | None, str]:
    goal_node = _astar_raw(env, start, goal)
    if goal_node is None:
        return (None, "NO_PATH")

    outbound_steps = goal_node.steps
    outbound_path  = _reconstruct_path(goal_node)
    return_node = _astar_raw(env, goal, base)
    if return_node is None:
        return (None, "NO_RETURN_PATH")

    return_steps = return_node.steps
    total_steps  = outbound_steps + return_steps

    if total_steps >= battery:
        return (None, "BATTERY_INSUFFICIENT")

    return (outbound_path, "OK")


def astar(env,
          start: tuple[int, int],
          goal:  tuple[int, int]) -> list[tuple[int, int]] | None:
    node = _astar_raw(env, start, goal)
    return _reconstruct_path(node) if node is not None else None



def path_is_safe(env, path: list[tuple[int, int]]) -> bool:
    if not path:
        return False
    return all(env.grid[r][c] != FIRE for r, c in path)