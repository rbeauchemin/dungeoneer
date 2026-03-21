"""Encounter generator — builds same-type monster groups scaled to party strength.

Difficulty budget
-----------------
The generator sums the levels of every party member to form a *party level total*,
then applies a difficulty multiplier to set the maximum total CR for the encounter:

    easy   → CR budget = party_level_total x 0.5
    medium → CR budget = party_level_total x 1.0
    hard   → CR budget = party_level_total x 2.0

A monster type is chosen at random from all monsters whose individual CR fits within
the budget (so at least one creature can be fielded). The group size is then:

    count = floor(budget / monster_cr),  capped at MAX_GROUP_SIZE

CR 0 creatures use an effective CR of 1/8 for division so the count stays finite.

Usage::

    from src.encounter import generate_encounter
    from src.map import Map

    dungeon = Map(20, 15, name="Dungeon Level 1")
    # players: list of Character objects already placed on the map
    monsters = generate_encounter(
        party=players,
        difficulty="medium",       # "easy" | "medium" | "hard"
        map_=dungeon,
        spawn_region=(12, 2, 19, 12),  # (x1, y1, x2, y2) bounding box
    )
    # monsters are already placed on dungeon; pass to Combat to run the fight
"""

from __future__ import annotations

import random
from typing import Optional

from src.creatures.monsters import (
    Commoner, Rat, Bat, Cat,
    Bandit, Guard, Kobold, PoisonousSnake, Stirge,
    Goblin, Skeleton, Zombie, Wolf,
    Hobgoblin, Orc, Scout,
    Bugbear, DireWolf, Ghoul, GiantSpider, Harpy,
    Ogre, SeaHag,
    Manticore, Mummy, Wight,
    Banshee, Ettin,
    HillGiant, Troll, VampireSpawn,
    Assassin, CloudGiant, Vampire,
    AdultRedDragon, Lich, AncientRedDragon,
)


# ── Registry ──────────────────────────────────────────────────────────────────

# (MonsterClass, challenge_rating)
_MONSTER_TABLE: list[tuple] = [
    (Commoner,        0),
    (Rat,             0),
    (Bat,             0),
    (Cat,             0),
    (Bandit,          0.125),
    (Guard,           0.125),
    (Kobold,          0.125),
    (PoisonousSnake,  0.125),
    (Stirge,          0.125),
    (Goblin,          0.25),
    (Skeleton,        0.25),
    (Zombie,          0.25),
    (Wolf,            0.25),
    (Hobgoblin,       0.5),
    (Orc,             0.5),
    (Scout,           0.5),
    (Bugbear,         1),
    (DireWolf,        1),
    (Ghoul,           1),
    (GiantSpider,     1),
    (Harpy,           1),
    (Ogre,            2),
    (SeaHag,          2),
    (Manticore,       3),
    (Mummy,           3),
    (Wight,           3),
    (Banshee,         4),
    (Ettin,           4),
    (HillGiant,       5),
    (Troll,           5),
    (VampireSpawn,    5),
    (Assassin,        8),
    (CloudGiant,      9),
    (Vampire,         13),
    (AdultRedDragon,  17),
    (Lich,            21),
    (AncientRedDragon, 24),
]

DIFFICULTY_MULTIPLIERS: dict[str, float] = {
    "easy":   0.5,
    "medium": 1.0,
    "hard":   2.0,
}

# Upper bound on encounter group size regardless of budget
MAX_GROUP_SIZE = 8

# Minimum effective CR used for count division (prevents ÷0 for CR 0 creatures)
_MIN_EFFECTIVE_CR = 0.125


# ── Public API ────────────────────────────────────────────────────────────────

def generate_encounter(
    party: list,
    difficulty: str = "medium",
    map_=None,
    spawn_region: Optional[tuple[int, int, int, int]] = None,
) -> list:
    """Generate a group of same-type monsters scaled to the party.

    Parameters
    ----------
    party : list
        List of :class:`~src.creatures.Character` objects in the party.
        Each member's ``.level`` attribute is used for budget calculation.
    difficulty : str
        ``"easy"``, ``"medium"``, or ``"hard"``.
    map_ : Map, optional
        If provided together with *spawn_region*, the returned monsters are
        placed on the map at random passable cells within the region.
    spawn_region : (x1, y1, x2, y2), optional
        Bounding box of cells in which to scatter the monsters.  Ignored if
        *map_* is not given.

    Returns
    -------
    list
        Freshly instantiated Monster objects.  If placement was requested
        and there were not enough free cells, any remaining monsters are
        returned without a map position.

    Raises
    ------
    ValueError
        If *party* is empty or *difficulty* is not a recognised string.
    """
    if not party:
        raise ValueError("party cannot be empty.")

    key = difficulty.lower()
    if key not in DIFFICULTY_MULTIPLIERS:
        raise ValueError(
            f"difficulty must be one of {list(DIFFICULTY_MULTIPLIERS)}, got {difficulty!r}."
        )

    multiplier = DIFFICULTY_MULTIPLIERS[key]
    party_level_total = sum(getattr(member, "level", 1) for member in party)
    budget = party_level_total * multiplier

    monster_cls, monster_cr, count = _select_monster_and_count(budget)

    monsters = [monster_cls() for _ in range(count)]

    if map_ is not None and spawn_region is not None:
        _place_monsters(monsters, map_, spawn_region)

    total_cr = monster_cr * count
    print(
        f"Encounter ({difficulty}): {count}x {monster_cls.__name__} "
        f"(CR {_cr_str(monster_cr)} each, total CR {_cr_str(total_cr)}) "
        f"[budget: {_cr_str(budget)}]"
    )
    return monsters


def encounter_info(party: list) -> None:
    """Print the CR budget for every difficulty tier given the current party."""
    if not party:
        print("No party members.")
        return
    total = sum(getattr(m, "level", 1) for m in party)
    print(f"Party of {len(party)}, total level {total}")
    for label, mult in DIFFICULTY_MULTIPLIERS.items():
        budget = total * mult
        eligible = _eligible_monsters(budget)
        crs = sorted({cr for _, cr in eligible})
        print(f"  {label:<8} budget CR {_cr_str(budget):>5}   "
              f"eligible CRs: {[_cr_str(c) for c in crs]}")


# ── Internal helpers ──────────────────────────────────────────────────────────

def _eligible_monsters(budget: float) -> list[tuple]:
    """All (class, cr) pairs whose CR fits within the budget (at least 1 unit)."""
    eligible = [(cls, cr) for cls, cr in _MONSTER_TABLE if cr <= budget]
    # Fall back to the lowest-CR tier if nothing fits
    if not eligible:
        min_cr = min(cr for _, cr in _MONSTER_TABLE)
        eligible = [(cls, cr) for cls, cr in _MONSTER_TABLE if cr == min_cr]
    return eligible


def _select_monster_and_count(budget: float) -> tuple:
    """Pick a random monster type and calculate how many to field."""
    eligible = _eligible_monsters(budget)
    monster_cls, monster_cr = random.choice(eligible)
    effective_cr = max(monster_cr, _MIN_EFFECTIVE_CR)
    count = min(MAX_GROUP_SIZE, max(1, int(budget / effective_cr)))
    return monster_cls, monster_cr, count


def _place_monsters(monsters: list, map_, spawn_region: tuple[int, int, int, int]):
    """Scatter monsters across random passable cells in spawn_region."""
    x1, y1, x2, y2 = spawn_region
    candidates = [
        (x, y)
        for x in range(min(x1, x2), max(x1, x2) + 1)
        for y in range(min(y1, y2), max(y1, y2) + 1)
        if map_.is_passable(x, y, 0) and not map_.get_creatures_at(x, y, 0)
    ]
    random.shuffle(candidates)
    for monster, (x, y) in zip(monsters, candidates):
        map_.place_creature(monster, x, y)


def _cr_str(cr: float) -> str:
    """Human-readable CR: 0.125 → '1/8', 0.25 → '1/4', 0.5 → '1/2', else int/float."""
    fractions = {0.125: "1/8", 0.25: "1/4", 0.5: "1/2"}
    if cr in fractions:
        return fractions[cr]
    return str(int(cr)) if cr == int(cr) else str(cr)
