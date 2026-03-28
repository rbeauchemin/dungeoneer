"""Map system for tracking spatial positions of creatures and objects.

Coordinates: (x, y, z) where (0, 0, 0) is the map origin.
  - x, y  : horizontal grid position; bounded by Map.width and Map.height.
  - z      : elevation in grid squares (0 = ground, +z = airborne, -z = underwater).
             x/y are bounded by the map; z is unbounded.

Each cell is cell_size feet wide (default 5 ft — one D&D square).
Distance uses Chebyshev metric: diagonals and vertical steps cost the same as
orthogonals, matching the D&D 5e 2024 movement rule.

Pathfinding (find_path / creature.move) uses A* with 3D Chebyshev heuristic,
accounting for difficult terrain (2x movement cost per cell).
"""

from __future__ import annotations

import heapq
import math
from typing import Optional


# ── Object types ──────────────────────────────────────────────────────────────

OBJECT_TYPES = {"rock", "wall", "tree", "chest", "door", "stairs"}

SIZE_TO_SQUARES = {
    "Tiny": 1,
    "Small": 1,
    "Medium": 1,
    "Large": 2,
    "Huge": 3,
    "Gargantuan": 4,
}


# ── MapObject and terrain/interactive subclasses ──────────────────────────────

class MapObject:
    """A non-creature object placed on the map (terrain or interactive)."""

    def __init__(
        self,
        name: str,
        object_type: str,
        x: int,
        y: int,
        z: int = 0,
        passable: bool = False,
        blocking_sight: bool = True,
        **kwargs,
    ):
        if object_type not in OBJECT_TYPES:
            raise ValueError(
                f"Unknown object type '{object_type}'. Must be one of {OBJECT_TYPES}."
            )
        self.name = name
        self.object_type = object_type
        self.x = x
        self.y = y
        self.z = z
        self.passable = passable
        self.blocking_sight = blocking_sight
        self.position: Optional[tuple[int, int, int]] = (x, y, z)
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return (
            f"{self.__class__.__name__}({self.name!r}, "
            f"pos=({self.x}, {self.y}, {self.z}))"
        )


class Rock(MapObject):
    """An impassable rock formation; does not block line of sight."""

    def __init__(self, name: str = "Rock", x: int = 0, y: int = 0, z: int = 0, **kwargs):
        super().__init__(
            name=name, object_type="rock", x=x, y=y, z=z,
            passable=False, blocking_sight=False, **kwargs,
        )


class Wall(MapObject):
    """A solid wall — impassable and blocks line of sight."""

    def __init__(self, name: str = "Wall", x: int = 0, y: int = 0, z: int = 0, **kwargs):
        super().__init__(
            name=name, object_type="wall", x=x, y=y, z=z,
            passable=False, blocking_sight=True, **kwargs,
        )


class Tree(MapObject):
    """A tree — impassable and blocks line of sight."""

    def __init__(self, name: str = "Tree", x: int = 0, y: int = 0, z: int = 0, **kwargs):
        super().__init__(
            name=name, object_type="tree", x=x, y=y, z=z,
            passable=False, blocking_sight=True, **kwargs,
        )


class Chest(MapObject):
    """An interactive chest that may be locked and contain items."""

    def __init__(
        self,
        name: str = "Chest",
        x: int = 0,
        y: int = 0,
        z: int = 0,
        locked: bool = False,
        contents: Optional[list] = None,
        **kwargs,
    ):
        super().__init__(
            name=name, object_type="chest", x=x, y=y, z=z,
            passable=False, blocking_sight=False, **kwargs,
        )
        self.locked = locked
        self.contents: list = contents if contents is not None else []


class Door(MapObject):
    """A door that can be opened or closed (and optionally locked)."""

    def __init__(
        self,
        name: str = "Door",
        x: int = 0,
        y: int = 0,
        z: int = 0,
        open: bool = False,
        locked: bool = False,
        **kwargs,
    ):
        super().__init__(
            name=name, object_type="door", x=x, y=y, z=z,
            passable=open, blocking_sight=not open, **kwargs,
        )
        self.open = open
        self.locked = locked

    def open_door(self):
        self.open = True
        self.passable = True
        self.blocking_sight = False

    def close_door(self):
        self.open = False
        self.passable = False
        self.blocking_sight = True


class Stairs(MapObject):
    """Stairs leading to another level or map."""

    def __init__(
        self,
        name: str = "Stairs",
        x: int = 0,
        y: int = 0,
        z: int = 0,
        direction: str = "down",
        destination=None,
        **kwargs,
    ):
        super().__init__(
            name=name, object_type="stairs", x=x, y=y, z=z,
            passable=True, blocking_sight=False, **kwargs,
        )
        self.direction = direction
        self.destination = destination


# ── MapZone ───────────────────────────────────────────────────────────────────

class MapZone:
    """A persistent area-of-effect region on the map.

    Callbacks receive ``(creature)`` as their only argument.
    ``on_entry``  — fired when a creature enters the zone.
    ``on_exit``   — fired when a creature leaves the zone.
    ``on_turn``   — fired at the end of each creature's turn while inside.

    ``duration`` is in rounds; ``None`` means the zone persists until explicitly
    removed with ``Map.remove_zone``.
    """

    def __init__(
        self,
        name: str,
        x: float,
        y: float,
        z: float = 0,
        radius_ft: float = 5,
        duration: Optional[int] = None,
        created_by=None,
        on_entry=None,
        on_exit=None,
        on_turn=None,
    ):
        self.name = name
        self.x = x
        self.y = y
        self.z = z
        self.radius_ft = radius_ft
        self.duration = duration
        self.created_by = created_by
        self.on_entry = on_entry
        self.on_exit = on_exit
        self.on_turn = on_turn
        self._occupants: set = set()   # creatures currently tracked inside

    def __repr__(self):
        return (
            f"MapZone({self.name!r}, pos=({self.x}, {self.y}, {self.z}), "
            f"r={self.radius_ft}ft, duration={self.duration})"
        )


# ── Map ───────────────────────────────────────────────────────────────────────

class Map:
    """A 3D grid that tracks positions of creatures and objects.

    Positions are (x, y, z) tuples. x and y are bounded by width x height;
    z is unbounded (positive = airborne, negative = underwater).

    Usage::

        dungeon = Map(20, 15, name="Dungeon Level 1")
        dungeon.place_object(Wall(x=0, y=0))
        dungeon.mark_difficult_terrain(3, 4)        # swampy ground
        dungeon.place_creature(goblin, 5, 3)         # z=0 by default
        dungeon.place_creature(dragon, 10, 7, z=2)   # airborne

        dungeon.distance_ft(hero, goblin)
        result = hero.move(dungeon, 8, 5)
        result = dragon.move(dungeon, 5, 5, z=3)
    """

    _OBJECT_GLYPHS = {
        "wall": "█",
        "rock": "●",
        "tree": "♣",
        "chest": "☐",
        "door": "▣",
        "stairs": "≡",
    }

    def __init__(self, width: int, height: int, cell_size: int = 5, name: str = ""):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.name = name
        self._creatures: dict = {}        # creature -> (x, y, z)
        self._objects: dict = {}          # (x, y, z) -> list[MapObject]
        self._creature_grid: dict = {}    # (x, y, z) -> list[creature]
        self.difficult_terrain: set = set()  # set of (x, y, z) cells
        self._zones: list = []            # active MapZone instances

    # ── Bounds ────────────────────────────────────────────────────────────────

    def _in_bounds(self, x: int, y: int) -> bool:
        """x and y must lie within the map grid; z is unrestricted."""
        return 0 <= x < self.width and 0 <= y < self.height

    def _check_bounds(self, x: int, y: int):
        if not self._in_bounds(x, y):
            raise ValueError(
                f"Position ({x}, {y}) is out of map bounds "
                f"({self.width}x{self.height})."
            )

    # ── Difficult terrain ──────────────────────────────────────────────────────

    def mark_difficult_terrain(self, x: int, y: int, z: int = 0):
        """Mark a cell as difficult terrain (costs 2 movement squares to enter)."""
        self._check_bounds(x, y)
        self.difficult_terrain.add((x, y, z))

    def clear_difficult_terrain(self, x: int, y: int, z: int = 0):
        """Remove the difficult terrain flag from a cell."""
        self.difficult_terrain.discard((x, y, z))

    # ── Object placement ──────────────────────────────────────────────────────

    def place_object(self, obj: MapObject) -> MapObject:
        """Place a MapObject on the map at its current (x, y, z)."""
        self._check_bounds(obj.x, obj.y)
        key = (obj.x, obj.y, obj.z)
        self._objects.setdefault(key, []).append(obj)
        obj.position = key
        return obj

    def remove_object(self, obj: MapObject) -> bool:
        """Remove a MapObject from the map. Returns True if found."""
        key = (obj.x, obj.y, obj.z)
        cell = self._objects.get(key, [])
        for o in cell:
            if o.name == obj.name and o.object_type == obj.object_type:
                cell.remove(o)
                if not cell:
                    del self._objects[key]
                obj.position = None
                return True
        return False

    def move_object(self, obj: MapObject, x: int, y: int, z: int = 0):
        """Relocate a MapObject to a new (x, y, z) cell."""
        self._check_bounds(x, y)
        self.remove_object(obj)
        obj.x, obj.y, obj.z = x, y, z
        self.place_object(obj)

    # ── Creature placement ────────────────────────────────────────────────────

    # ── Zone management ───────────────────────────────────────────────────────

    def add_zone(self, zone: MapZone) -> MapZone:
        """Add a MapZone to this map and return it."""
        self._zones.append(zone)
        return zone

    def remove_zone(self, zone: MapZone) -> bool:
        """Remove a zone. Returns True if it was present."""
        if zone in self._zones:
            self._zones.remove(zone)
            return True
        return False

    def get_zones_containing(self, creature) -> list:
        """Return all active zones whose radius includes the creature's position."""
        pos = self._creatures.get(creature)
        if pos is None:
            return []
        cx, cy, cz = pos
        result = []
        for zone in self._zones:
            dx = (cx - zone.x) * self.cell_size
            dy = (cy - zone.y) * self.cell_size
            dz = (cz - zone.z) * self.cell_size
            if math.sqrt(dx * dx + dy * dy + dz * dz) <= zone.radius_ft:
                result.append(zone)
        return result

    def tick_zones(self) -> list:
        """Decrement zone durations by one round; remove and return expired zones."""
        expired = []
        for zone in list(self._zones):
            if zone.duration is not None:
                zone.duration -= 1
                if zone.duration <= 0:
                    expired.append(zone)
                    self._zones.remove(zone)
        return expired

    def check_zone_transitions(self, creature) -> tuple:
        """Compare current zone membership against tracked occupants.

        Fires ``on_entry`` for newly entered zones and ``on_exit`` for
        newly exited ones.  Updates each zone's ``_occupants`` set.

        Returns ``(entered, exited)`` as sets of MapZone objects.
        """
        current = set(self.get_zones_containing(creature))
        previous = {z for z in self._zones if creature in z._occupants}

        entered = current - previous
        exited = previous - current

        for zone in entered:
            zone._occupants.add(creature)
            if zone.on_entry:
                zone.on_entry(creature)

        for zone in exited:
            zone._occupants.discard(creature)
            if zone.on_exit:
                zone.on_exit(creature)

        return entered, exited

    # ── Creature placement ────────────────────────────────────────────────────

    def place_creature(self, creature, x: int, y: int, z: int = 0):
        """Place or teleport a creature to (x, y, z). Sets creature.position."""
        self._check_bounds(x, y)
        if creature in self._creatures:
            old = self._creatures[creature]
            old_list = self._creature_grid.get(old, [])
            if creature in old_list:
                old_list.remove(creature)
            if not old_list:
                self._creature_grid.pop(old, None)
        key = (x, y, z)
        self._creatures[creature] = key
        self._creature_grid.setdefault(key, []).append(creature)
        creature.position = key
        creature._map = self

    def remove_creature(self, creature) -> bool:
        """Remove a creature from the map. Sets creature.position = None."""
        if creature not in self._creatures:
            return False
        key = self._creatures.pop(creature)
        cell = self._creature_grid.get(key, [])
        if creature in cell:
            cell.remove(creature)
        if not cell:
            self._creature_grid.pop(key, None)
        creature.position = None
        creature._map = None
        return True

    def move_creature(self, creature, x: int, y: int, z: int = 0):
        """Teleport an already-placed creature to (x, y, z).

        Does not enforce movement speed or pathfinding — use creature.move()
        for speed-limited, path-aware movement.
        """
        if creature not in self._creatures:
            raise ValueError(f"{getattr(creature, 'name', creature)} is not on this map.")
        self.place_creature(creature, x, y, z)

    # ── Passability ───────────────────────────────────────────────────────────

    def is_passable(self, x: int, y: int, z: int = 0) -> bool:
        """True if a creature could occupy (x, y, z).

        Cells at z ≠ 0 have no objects, so they are always passable
        (callers must separately check fly/swim capability for z ≠ 0).
        """
        if not self._in_bounds(x, y):
            return False
        if z != 0:
            return True
        return all(obj.passable for obj in self._objects.get((x, y, 0), []))

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_position(self, entity) -> Optional[tuple[int, int, int]]:
        """Return (x, y, z) position of a creature or MapObject."""
        if isinstance(entity, MapObject):
            return entity.position
        return self._creatures.get(entity)

    def get_objects_at(self, x: int, y: int, z: int = 0) -> list:
        return list(self._objects.get((x, y, z), []))

    def get_creatures_at(self, x: int, y: int, z: int = 0) -> list:
        return list(self._creature_grid.get((x, y, z), []))

    def get_all_at(self, x: int, y: int, z: int = 0) -> dict:
        return {
            "creatures": self.get_creatures_at(x, y, z),
            "objects": self.get_objects_at(x, y, z),
        }

    @property
    def all_creatures(self) -> list:
        return list(self._creatures.keys())

    @property
    def all_objects(self) -> list:
        return [obj for objs in self._objects.values() for obj in objs]

    # ── Distance ─────────────────────────────────────────────────────────────

    def _get_xyz(self, entity) -> tuple[int, int, int]:
        """Resolve any entity to its (x, y, z) grid position."""
        if isinstance(entity, tuple):
            return entity if len(entity) == 3 else (entity[0], entity[1], 0)
        if isinstance(entity, MapObject):
            if entity.position is None:
                raise ValueError(f"MapObject '{entity.name}' is not on this map.")
            return (entity.x, entity.y, entity.z)
        pos = self._creatures.get(entity)
        if pos is None:
            raise ValueError(f"'{getattr(entity, 'name', entity)}' is not on this map.")
        return pos

    def distance_squares(self, entity1, entity2) -> int:
        """3D Chebyshev distance in grid squares."""
        x1, y1, z1 = self._get_xyz(entity1)
        x2, y2, z2 = self._get_xyz(entity2)
        return max(abs(x2 - x1), abs(y2 - y1), abs(z2 - z1))

    def distance_ft(self, entity1, entity2) -> int:
        """Distance in feet using 3D Chebyshev metric (D&D 5e default)."""
        return self.distance_squares(entity1, entity2) * self.cell_size

    def distance_euclidean_ft(self, entity1, entity2) -> float:
        """True straight-line distance in feet (useful for area-of-effect radii)."""
        x1, y1, z1 = self._get_xyz(entity1)
        x2, y2, z2 = self._get_xyz(entity2)
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2 + (z2 - z1)**2) * self.cell_size

    def get_creatures_in_range(self, entity, range_ft: int) -> list:
        """All creatures within range_ft feet (3D Chebyshev, excludes self)."""
        range_sq = range_ft // self.cell_size
        x0, y0, z0 = self._get_xyz(entity)
        return [
            c for c, (cx, cy, cz) in self._creatures.items()
            if c is not entity
            and max(abs(cx - x0), abs(cy - y0), abs(cz - z0)) <= range_sq
        ]

    def get_objects_in_range(self, entity, range_ft: int) -> list:
        """All MapObjects within range_ft feet (3D Chebyshev)."""
        range_sq = range_ft // self.cell_size
        x0, y0, z0 = self._get_xyz(entity)
        return [
            obj
            for (ox, oy, oz), objs in self._objects.items()
            if max(abs(ox - x0), abs(oy - y0), abs(oz - z0)) <= range_sq
            for obj in objs
        ]

    def get_all_in_range(self, entity, range_ft: int) -> dict:
        return {
            "creatures": self.get_creatures_in_range(entity, range_ft),
            "objects": self.get_objects_in_range(entity, range_ft),
        }

    def in_melee_range(self, attacker, target, reach_ft: int = 5) -> bool:
        return self.distance_ft(attacker, target) <= reach_ft

    def in_spell_range(self, caster, target, range_ft: int) -> bool:
        return self.distance_ft(caster, target) <= range_ft

    def has_line_of_sight(self, entity1, entity2) -> bool:
        """True if no sight-blocking object lies between *entity1* and *entity2*.

        Samples cells along the straight line between the two positions by
        linear interpolation and rounding. The source and destination cells are
        not checked, so a creature standing in/beside a blocking object can
        still draw LoS from its own cell.
        """
        x1, y1, z1 = self._get_xyz(entity1)
        x2, y2, z2 = self._get_xyz(entity2)

        steps = max(abs(x2 - x1), abs(y2 - y1), abs(z2 - z1))
        if steps == 0:
            return True  # same cell

        for i in range(1, steps):
            t = i / steps
            ix = round(x1 + t * (x2 - x1))
            iy = round(y1 + t * (y2 - y1))
            iz = round(z1 + t * (z2 - z1))
            for obj in self._objects.get((ix, iy, iz), []):
                if obj.blocking_sight:
                    return False

        return True

    # ── Pathfinding ───────────────────────────────────────────────────────────

    @staticmethod
    def _step_cost(from_pos: tuple, to_pos: tuple, is_difficult: bool) -> float:
        """Movement cost for one step, applying Pythagorean multi-axis penalty.

        Moving through d changed axes costs sqrt(d) squares:
          - cardinal (1 axis)  → 1.0
          - diagonal (2 axes)  → √2 ≈ 1.414
          - 3-D diagonal       → √3 ≈ 1.732
        Difficult terrain doubles the cost.
        """
        dims = sum(1 for a, b in zip(from_pos, to_pos) if a != b)
        cost = math.sqrt(dims) if dims else 0.0
        return cost * 2 if is_difficult else cost

    @staticmethod
    def _movement_flags(creature) -> tuple[bool, bool, bool]:
        """Return (can_fly, can_swim, can_climb) based on creature speed attributes."""
        can_fly = getattr(creature, "flying_speed", 0) > 0
        can_swim = getattr(creature, "swimming_speed", 0) > 0
        can_climb = getattr(creature, "climbing_speed", 0) > 0
        return can_fly, can_swim, can_climb

    def _neighbors(
        self, x: int, y: int, z: int,
        can_fly: bool, can_swim: bool, can_climb: bool,
        blocked_positions: set = None,
    ) -> list[tuple[int, int, int]]:
        """All cells reachable in a single step from (x, y, z).

        blocked_positions — set of (x, y, z) cells occupied by enemy creatures
        that cannot be entered at all (treated as impassable terrain for this move).
        """
        blocked_positions = blocked_positions or set()
        result = []

        if can_fly:
            # Full 3D movement — all 26 adjacent cells
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        if dx == dy == dz == 0:
                            continue
                        nx, ny, nz = x + dx, y + dy, z + dz
                        if (self._in_bounds(nx, ny)
                                and self.is_passable(nx, ny, nz)
                                and (nx, ny, nz) not in blocked_positions):
                            result.append((nx, ny, nz))
        else:
            # Ground movement — 8 lateral neighbours at the same z
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if (self._in_bounds(nx, ny)
                            and self.is_passable(nx, ny, z)
                            and (nx, ny, z) not in blocked_positions):
                        result.append((nx, ny, z))

            # Vertical transitions at the same (x, y)
            if can_climb and self._in_bounds(x, y):
                result.append((x, y, z + 1))   # climb up
            if can_swim and z >= 0 and self._in_bounds(x, y):
                result.append((x, y, z - 1))   # dive down

            # Any creature can descend from airborne (gravity)
            if z > 0 and self.is_passable(x, y, z - 1):
                candidate = (x, y, z - 1)
                if candidate not in result:
                    result.append(candidate)

        return result

    def find_path(
        self, creature, tx: int, ty: int, tz: int = 0,
        blocked_creatures=None,
    ) -> Optional[list[tuple[int, int, int]]]:
        """A* shortest path from creature's position to (tx, ty, tz).

        Accounts for:
          - impassable terrain (walls, closed doors, rocks, trees at z=0)
          - difficult terrain (2 movement squares to enter)
          - creature movement capabilities (fly / swim / climb)
          - enemy creatures (blocked_creatures) whose cells cannot be entered

        Ally creature cells are passable for routing but the caller is responsible
        for ensuring the creature does not land on an occupied cell.

        blocked_creatures — iterable of creatures whose positions are impassable
          (typically enemies of the moving creature).

        Returns an ordered list of (x, y, z) cells to traverse, excluding the
        starting cell and including the destination, or None if unreachable.
        """
        if creature not in self._creatures:
            raise ValueError(f"'{getattr(creature, 'name', creature)}' is not on this map.")

        start = self._creatures[creature]
        goal = (tx, ty, tz)

        if start == goal:
            return []

        can_fly, can_swim, can_climb = self._movement_flags(creature)

        # Build set of enemy-occupied positions that cannot be traversed
        blocked_positions: set = set()
        if blocked_creatures:
            for bc in blocked_creatures:
                pos = self._creatures.get(bc)
                if pos and pos != start:
                    blocked_positions.add(pos)

        # heap: (f_score, g_score, position)
        heap: list = []
        heapq.heappush(heap, (0.0, 0.0, start))
        came_from: dict[tuple, tuple] = {}
        g_cost: dict[tuple, float] = {start: 0.0}

        while heap:
            _, g, current = heapq.heappop(heap)

            if current == goal:
                # Reconstruct path
                path: list[tuple] = []
                node = current
                while node in came_from:
                    path.append(node)
                    node = came_from[node]
                path.reverse()
                return path

            if g > g_cost.get(current, float("inf")):
                continue  # stale heap entry

            cx, cy, cz = current
            for nb in self._neighbors(cx, cy, cz, can_fly, can_swim, can_climb, blocked_positions):
                step = self._step_cost(current, nb, nb in self.difficult_terrain)
                new_g = g + step
                if new_g < g_cost.get(nb, float("inf")):
                    g_cost[nb] = new_g
                    nx, ny, nz = nb
                    # Euclidean heuristic — admissible since sqrt(dims) >= Euclidean per step
                    h = math.sqrt((tx - nx) ** 2 + (ty - ny) ** 2 + (tz - nz) ** 2)
                    heapq.heappush(heap, (new_g + h, new_g, nb))
                    came_from[nb] = current

        return None  # no path exists

    # ── Display ───────────────────────────────────────────────────────────────

    def render(self, z: int = 0, cell_width: int = 3) -> str:
        """Render a single z-layer as an ASCII grid.

        Creatures at this z-level appear as the first letter of their name.
        Objects appear as their type glyph.
        """
        obj_glyph: dict[tuple[int, int], str] = {}
        for (ox, oy, oz), objs in self._objects.items():
            if oz == z:
                obj_glyph[(ox, oy)] = self._OBJECT_GLYPHS.get(objs[0].object_type, "?")

        creature_glyph: dict[tuple[int, int], str] = {}
        for creature, (cx, cy, cz) in self._creatures.items():
            if cz == z:
                creature_glyph[(cx, cy)] = getattr(creature, "name", "?")[0].upper()

        z_label = "ground" if z == 0 else f"z={z} ({'airborne' if z > 0 else 'underwater'})"
        border = "+" + ("-" * cell_width + "+") * self.width
        lines = [f"[{self.name} — {z_label}]", border]
        for y in range(self.height):
            row = "|"
            for x in range(self.width):
                if (x, y) in creature_glyph:
                    cell = creature_glyph[(x, y)].center(cell_width)
                elif (x, y) in obj_glyph:
                    cell = obj_glyph[(x, y)].center(cell_width)
                else:
                    cell = " " * cell_width
                row += cell + "|"
            lines.append(row)
            lines.append(border)
        return "\n".join(lines)

    def __repr__(self):
        n_obj = sum(len(v) for v in self._objects.values())
        return (
            f"Map({self.name!r}, {self.width}x{self.height}, "
            f"cell_size={self.cell_size}ft, "
            f"creatures={len(self._creatures)}, objects={n_obj})"
        )
