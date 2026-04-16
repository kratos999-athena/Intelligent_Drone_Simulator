import random
import math

EMPTY = 0
BASE  = 1
FIRE  = 2
HIKER = 3

GRID_SIZE = 15

FIRE_SPREAD_BASE_PROB: float = 0.25
WIND_STRENGTH: float = 0.35
WIND_MIN_PROB: float = 0.05

WIND_DIRECTION: tuple[int, int] = (1, 1)

def _wind_unit() -> tuple[float, float]:
    dr, dc = WIND_DIRECTION
    magnitude = math.sqrt(dr ** 2 + dc ** 2)
    if magnitude == 0:
        return (0.0, 0.0)
    return (dr / magnitude, dc / magnitude)

_WIND_UNIT: tuple[float, float] = _wind_unit()

def _spread_probability(from_r: int, from_c: int,
                        to_r: int,   to_c: int) -> float:
    d_r = to_r - from_r
    d_c = to_c - from_c
    spread_mag = math.sqrt(d_r ** 2 + d_c ** 2)

    if spread_mag == 0:
        return FIRE_SPREAD_BASE_PROB

    s_r = d_r / spread_mag
    s_c = d_c / spread_mag

    wu_r, wu_c = _WIND_UNIT
    alignment = wu_r * s_r + wu_c * s_c

    raw = FIRE_SPREAD_BASE_PROB + alignment * WIND_STRENGTH
    return max(WIND_MIN_PROB, min(1.0, raw))

class Environment:
    def __init__(self, size: int = GRID_SIZE, seed: int | None = None):
        if seed is not None:
            random.seed(seed)
        self.size = size
        self.grid: list[list[int]] = [
            [EMPTY for _ in range(size)] for _ in range(size)
        ]
        self.hikers:    list[tuple[int, int]] = []
        self.rescued:   set[tuple[int, int]]  = set()
        self.tick_count: int = 0
        self._place_base()
        self._place_initial_fires()
        self._place_hikers()

    def _place_base(self) -> None:
        self.base_pos = (0, 0)
        self.grid[0][0] = BASE

    def _place_initial_fires(self, n_fires: int = 3) -> None:
        placed = []
        min_dist_from_base = 4
        min_dist_between   = 3
        attempts = 0

        while len(placed) < n_fires and attempts < 2000:
            attempts += 1
            r = random.randint(0, self.size - 1)
            c = random.randint(0, self.size - 1)

            if self.grid[r][c] != EMPTY:
                continue
            if abs(r) + abs(c) < min_dist_from_base:
                continue
            if any(abs(r - pr) + abs(c - pc) < min_dist_between
                   for pr, pc in placed):
                continue

            self.grid[r][c] = FIRE
            placed.append((r, c))

    def _place_hikers(self, n_hikers: int = 5) -> None:
        placed = []
        attempts = 0

        while len(placed) < n_hikers and attempts < 2000:
            attempts += 1
            r = random.randint(0, self.size - 1)
            c = random.randint(0, self.size - 1)

            if self.grid[r][c] != EMPTY:
                continue
            if abs(r) + abs(c) < 3:
                continue
            if any(self.grid[nr][nc] == FIRE
                   for nr, nc in self.get_neighbors_8(r, c)):
                continue

            self.grid[r][c] = HIKER
            self.hikers.append((r, c))
            placed.append((r, c))

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.size and 0 <= c < self.size

    def is_fire(self, r: int, c: int) -> bool:
        return self.in_bounds(r, c) and self.grid[r][c] == FIRE

    def get_adjacent(self, r: int, c: int) -> list[tuple[int, int]]:
        return [
            (r + dr, c + dc)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]
            if self.in_bounds(r + dr, c + dc)
        ]

    def get_neighbors_8(self, r: int, c: int) -> list[tuple[int, int]]:
        return [
            (r + dr, c + dc)
            for dr in [-1, 0, 1]
            for dc in [-1, 0, 1]
            if not (dr == 0 and dc == 0) and self.in_bounds(r + dr, c + dc)
        ]

    def get_cells_in_radius(self, r: int, c: int,
                             radius: int = 2) -> list[tuple[int, int]]:
        result = []
        for dr in range(-radius, radius + 1):
            for dc in range(-radius, radius + 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if self.in_bounds(nr, nc):
                    result.append((nr, nc))
        return result

    def is_adjacent_to_fire(self, r: int, c: int) -> bool:
        return any(self.grid[nr][nc] == FIRE
                   for nr, nc in self.get_neighbors_8(r, c))

    def is_fire_within_radius(self, r: int, c: int, radius: int = 2) -> bool:
        return any(self.grid[nr][nc] == FIRE
                   for nr, nc in self.get_cells_in_radius(r, c, radius))

    def tick(self) -> None:
        self.tick_count += 1
        new_fires: list[tuple[int, int]] = []

        for r in range(self.size):
            for c in range(self.size):
                if self.grid[r][c] == FIRE:
                    for nr, nc in self.get_adjacent(r, c):
                        if self.grid[nr][nc] in (EMPTY, HIKER):
                            p = _spread_probability(r, c, nr, nc)
                            if random.random() < p:
                                new_fires.append((nr, nc))

        for r, c in new_fires:
            if self.grid[r][c] == HIKER and (r, c) in self.hikers:
                self.hikers.remove((r, c))
            self.grid[r][c] = FIRE

    def rescue_hiker(self, r: int, c: int) -> bool:
        if (r, c) in self.hikers:
            self.hikers.remove((r, c))
            self.rescued.add((r, c))
            self.grid[r][c] = EMPTY
            return True
        return False

    def get_unrescued_hikers(self) -> list[tuple[int, int]]:
        return list(self.hikers)

    def cell_type(self, r: int, c: int) -> int | None:
        return self.grid[r][c] if self.in_bounds(r, c) else None