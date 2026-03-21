import importlib
import inspect
import sys
from src.common import roll_dice


def get_monsters(
        monster_types=None, cr_min=None, cr_max=None, name_contains=None):
    # Get the current module object
    current_module = sys.modules[__name__]

    # Get all members of the current module that are classes
    all_members = inspect.getmembers(current_module, inspect.isclass)

    # Filter out classes that were imported from other modules,
    # keeping only those defined in the current file.
    monsters = [
        (name, cls) for name, cls in all_members
        if cls.__module__ == current_module.__name__
    ]
    if monster_types is not None:
        monsters = [
            (name, cls) for name, cls in monsters
            if getattr(cls, "type", "") in monster_types
        ]
    if cr_min is not None:
        monsters = [
            (name, cls) for name, cls in monsters
            if getattr(cls, "cr", 0) >= cr_min
        ]
    if cr_max is not None:
        monsters = [
            (name, cls) for name, cls in monsters
            if getattr(cls, "cr", 0) <= cr_max
        ]
    if name_contains is not None:
        monsters = [
            (name, cls) for name, cls in monsters
            if name_contains.lower() in name.lower()
        ]

    return monsters


def _proficiency_bonus_for_cr(cr):
    """Return proficiency bonus based on Challenge Rating."""
    if cr < 5:
        return 2
    elif cr < 9:
        return 3
    elif cr < 13:
        return 4
    elif cr < 17:
        return 5
    elif cr < 21:
        return 6
    elif cr < 25:
        return 7
    elif cr < 29:
        return 8
    else:
        return 9


_DEFAULT_PARAMS = {
    "Saving Throws": [],
    "Skills": [],
    "Abilities": [],
    "Attack": 0,
    "ToBeAttacked": 0,
    "Initiative": 0,
}


class Monster:
    """Stat-block-based creature for use as encounter targets or enemies."""

    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "Monster")
        self.size = kwargs.get("size", "Medium")
        self.type = kwargs.get("type", "Beast")
        self.alignment = kwargs.get("alignment", "Unaligned")
        self.cr = kwargs.get("cr", 0)
        self._ac_value = kwargs.get("ac", 10)
        self.max_hp = kwargs.get("max_hp", 10)
        self.current_hp = self.max_hp
        self._base_speed = kwargs.get("speed", 30)
        self.swimming_speed = kwargs.get("swimming_speed", 0)
        self.flying_speed = kwargs.get("flying_speed", 0)
        self.climbing_speed = kwargs.get("climbing_speed", 0)
        self.ability_scores = kwargs.get("ability_scores", {
            "Strength": 10, "Dexterity": 10, "Constitution": 10,
            "Intelligence": 10, "Wisdom": 10, "Charisma": 10,
        })
        self.proficiency_bonus = _proficiency_bonus_for_cr(self.cr)
        self.saving_throw_proficiencies = kwargs.get("saving_throw_proficiencies", [])
        self.skill_proficiencies = kwargs.get("skill_proficiencies", {})  # {skill: bonus_override}
        self._base_resistances = list(kwargs.get("resistances", []))
        self._base_immunities = list(kwargs.get("immunities", []))
        self.vulnerabilities = kwargs.get("vulnerabilities", [])
        self.condition_immunities = kwargs.get("condition_immunities", [])
        self.senses = kwargs.get("senses", {})          # e.g. {"Darkvision": 60, "Passive Perception": 11}
        self.languages = kwargs.get("languages", [])
        self.special_abilities = kwargs.get("special_abilities", [])  # list of description strings or Spell objects
        self.actions = kwargs.get("actions", [])         # list of action dicts (see below)
        self.bonus_actions = kwargs.get("bonus_actions", [])
        self.reactions = kwargs.get("reactions", [])
        self.legendary_actions = kwargs.get("legendary_actions", [])
        self.description = kwargs.get("description", "")
        self.active_effects = []
        self.position = None   # set by Map.place_creature / Map.move_creature
        self._base_advantages = dict(_DEFAULT_PARAMS)
        self._base_disadvantages = dict(_DEFAULT_PARAMS)
        self._base_auto_fail = dict(_DEFAULT_PARAMS)
        self.actions_left = 1

    # ── Computed stat properties ────────────────────────────────────────────

    @property
    def speed(self) -> int:
        """Effective walking speed, derived from base speed and active conditions."""
        for e in self.active_effects:
            if getattr(e, "speed_override", None) is not None:
                return 0
        s = self._base_speed + getattr(self, "bonus_speed", 0)
        for e in self.active_effects:
            s += getattr(e, "speed_delta", 0)
        return max(0, s)

    @property
    def d20_modifier(self) -> int:
        """Flat modifier applied to every d20 roll, derived from active conditions."""
        mod = 0
        for e in self.active_effects:
            mod += getattr(e, "d20_delta", 0)
        return mod

    @property
    def advantages(self) -> dict:
        """Effective advantages merged from base values and active conditions."""
        result = {
            "Saving Throws": list(self._base_advantages.get("Saving Throws", [])),
            "Skills": list(self._base_advantages.get("Skills", [])),
            "Abilities": list(self._base_advantages.get("Abilities", [])),
            "Attack": self._base_advantages.get("Attack", 0),
            "ToBeAttacked": self._base_advantages.get("ToBeAttacked", 0),
            "Initiative": self._base_advantages.get("Initiative", 0),
        }
        for e in self.active_effects:
            result["Attack"] += getattr(e, "adv_attack", 0)
            result["ToBeAttacked"] += getattr(e, "adv_to_be_attacked", 0)
            result["Initiative"] += getattr(e, "adv_initiative", 0)
            for item in getattr(e, "adv_saving_throws", ()):
                if item not in result["Saving Throws"]:
                    result["Saving Throws"].append(item)
            for item in getattr(e, "adv_skills", ()):
                if item not in result["Skills"]:
                    result["Skills"].append(item)
            for item in getattr(e, "adv_abilities", ()):
                if item not in result["Abilities"]:
                    result["Abilities"].append(item)
        return result

    @property
    def disadvantages(self) -> dict:
        """Effective disadvantages merged from base values and active conditions."""
        result = {
            "Saving Throws": list(self._base_disadvantages.get("Saving Throws", [])),
            "Skills": list(self._base_disadvantages.get("Skills", [])),
            "Abilities": list(self._base_disadvantages.get("Abilities", [])),
            "Attack": self._base_disadvantages.get("Attack", 0),
            "ToBeAttacked": self._base_disadvantages.get("ToBeAttacked", 0),
            "Initiative": self._base_disadvantages.get("Initiative", 0),
        }
        for e in self.active_effects:
            result["Attack"] += getattr(e, "disadv_attack", 0)
            result["ToBeAttacked"] += getattr(e, "disadv_to_be_attacked", 0)
            result["Initiative"] += getattr(e, "disadv_initiative", 0)
            for item in getattr(e, "disadv_saving_throws", ()):
                if item not in result["Saving Throws"]:
                    result["Saving Throws"].append(item)
            for item in getattr(e, "disadv_skills", ()):
                if item not in result["Skills"]:
                    result["Skills"].append(item)
            for item in getattr(e, "disadv_abilities", ()):
                if item not in result["Abilities"]:
                    result["Abilities"].append(item)
        return result

    @property
    def auto_fail(self) -> dict:
        """Effective auto-fail dict merged from base values and active conditions."""
        result = {
            "Saving Throws": list(self._base_auto_fail.get("Saving Throws", [])),
            "Skills": list(self._base_auto_fail.get("Skills", [])),
            "Abilities": list(self._base_auto_fail.get("Abilities", [])),
            "Attack": self._base_auto_fail.get("Attack", 0),
            "ToBeAttacked": self._base_auto_fail.get("ToBeAttacked", 0),
            "Initiative": self._base_auto_fail.get("Initiative", 0),
        }
        for e in self.active_effects:
            for ability in getattr(e, "auto_fail_saving_throws", ()):
                if ability not in result["Saving Throws"]:
                    result["Saving Throws"].append(ability)
        return result

    @property
    def resistances(self) -> list:
        """Effective damage resistances merged from base and active conditions."""
        result = list(self._base_resistances)
        for e in self.active_effects:
            for dtype in getattr(e, "bonus_resistances", ()):
                if dtype not in result:
                    result.append(dtype)
        return result

    @property
    def immunities(self) -> list:
        """Effective damage immunities merged from base and active conditions."""
        result = list(self._base_immunities)
        for e in self.active_effects:
            for dtype in getattr(e, "bonus_immunities", ()):
                if dtype not in result:
                    result.append(dtype)
        return result

    # ── Compatibility helpers ───────────────────────────────────────────────

    def ac(self):
        return self._ac_value

    def get_ability_bonus(self, ability):
        return (self.ability_scores[ability] - 10) // 2

    def add_condition(self, condition):
        if condition in self.condition_immunities:
            return
        if isinstance(condition, str):
            try:
                cond_obj = getattr(importlib.import_module("src.conditions"), condition)()
                cond_obj.apply(self)
                return
            except (AttributeError, TypeError):
                pass
        self.active_effects.append(condition)

    def remove_condition(self, condition):
        name = condition if isinstance(condition, str) else condition.name
        self.active_effects = [e for e in self.active_effects if getattr(e, "name", e) != name]

    # ── Combat ─────────────────────────────────────────────────────────────

    def attack(self, target, action_name: str = None, lethal: bool = True):
        """Perform a monster attack against a target using its actions list."""
        action = None
        if action_name:
            for a in self.actions:
                if a.get("name") == action_name:
                    action = a
                    break
        if action is None and self.actions:
            action = self.actions[0]
        if action is None:
            print(f"{self.name} has no attacks defined.")
            return

        attack_bonus = action.get("attack_bonus", self.proficiency_bonus + self.get_ability_bonus("Strength"))
        print(f"{self.name} attacks {target.name} with {action['name']}.")
        roll = roll_dice(1, 20)
        total = roll + attack_bonus
        target_ac = target.ac() if callable(target.ac) else target.ac
        hit = total >= target_ac or roll == 20
        crit = roll == 20
        miss = roll == 1
        self.actions_left -= 1

        if miss:
            print(f"Critical miss! Roll: {roll}")
            return
        if hit:
            damage_str = action.get("damage", "1d4")
            num, die = [int(x) for x in damage_str.split("d")]
            if crit:
                num *= 2
                print("Critical hit!")
            damage = roll_dice(num, die) + action.get("damage_bonus", 0)
            damage_type = action.get("damage_type", "bludgeoning")
            print(f"Hit! {self.name} deals {damage} {damage_type} damage.")
            if damage_type in target.resistances:
                damage //= 2
                print("Resistance — damage halved.")
            if damage_type in target.immunities:
                damage = 0
                print("Immunity — no damage.")
            target.current_hp -= damage
            if target.current_hp <= 0:
                target.current_hp = 0
                target.add_condition("Dead" if lethal else "Unconscious")
        else:
            print(f"Miss! Roll: {total} vs AC {target_ac}")

    def move(self, map_, x: int, y: int, z: int = 0, budget: float = None) -> dict:
        """Move toward (x, y, z) using A* pathfinding.

        Step costs follow the Pythagorean theorem — moving through d axes costs
        sqrt(d) feet of movement per cell_size (e.g. pure cardinal = 1x cell,
        diagonal = √2 x cell, full 3-D diagonal = √3 x cell). Difficult terrain
        doubles each step's cost.

        The correct speed pool is chosen automatically:
          - any step with z > 0  → flying_speed
          - any step with z < 0  → swimming_speed
          - otherwise            → speed (walking, includes bonus_speed)

        Args:
          budget — optional cap on feet for this call (supports split movement).

        Returns a dict:
          path              — full planned path as list of (x, y, z) cells
          reached           — final position after consuming available movement
          movement_used     — feet spent (rounded to nearest foot)
          movement_remaining — feet remaining within this call's budget
          blocked           — True if no path to the target exists
        """
        import math as _math
        if self.position is None:
            raise RuntimeError(f"{self.name} is not placed on a map.")

        path = map_.find_path(self, x, y, z)
        avail = budget if budget is not None else self.speed
        if path is None:
            return {
                "path": [], "reached": self.position,
                "movement_used": 0, "movement_remaining": round(avail),
                "blocked": True,
            }
        if not path:
            return {
                "path": [], "reached": self.position,
                "movement_used": 0, "movement_remaining": round(avail),
                "blocked": False,
            }

        needs_fly  = any(pz > 0 for _, _, pz in path)
        needs_swim = any(pz < 0 for _, _, pz in path)
        if needs_fly:
            speed_ft = self.flying_speed
        elif needs_swim:
            speed_ft = self.swimming_speed
        else:
            # self.speed already incorporates bonus_speed and condition overrides
            speed_ft = self.speed
        if budget is not None:
            speed_ft = min(speed_ft, budget)

        cost_ft = 0.0
        prev = self.position
        final_pos = self.position
        for cell in path:
            dims = sum(1 for a, b in zip(prev, cell) if a != b)
            step_ft = _math.sqrt(dims) * map_.cell_size
            if cell in map_.difficult_terrain:
                step_ft *= 2
            if cost_ft + step_ft > speed_ft:
                break
            cost_ft += step_ft
            final_pos = cell
            prev = cell

        fx, fy, fz = final_pos
        map_.move_creature(self, fx, fy, fz)
        return {
            "path": path,
            "reached": final_pos,
            "movement_used": round(cost_ft),
            "movement_remaining": round(speed_ft - cost_ft),
            "blocked": False,
        }

    def dash(self):
        if self.actions_left <= 0:
            print(f"{self.name} has no actions left to dash.")
            return
        self.actions_left -= 1
        self.bonus_speed = max([self._base_speed, self.swimming_speed, self.flying_speed, self.climbing_speed])

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name!r} CR={self.cr} HP={self.current_hp}/{self.max_hp}>"


# ── NPC ────────────────────────────────────────────────────────────────────

class NPC(Monster):
    """
    A named non-player character with a simple stat block.
    More fleshed-out than a generic Monster but doesn't go through the full
    Character creation pipeline (no species/background module loading).
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("type", "Humanoid")
        kwargs.setdefault("alignment", "Neutral")
        super().__init__(**kwargs)
        self.role = kwargs.get("role", "")           # e.g. "Innkeeper", "Bandit Captain"
        self.personality = kwargs.get("personality", "")
        self.ideals = kwargs.get("ideals", "")
        self.bonds = kwargs.get("bonds", "")
        self.flaws = kwargs.get("flaws", "")

    def __repr__(self):
        role = f" ({self.role})" if self.role else ""
        return f"<NPC name={self.name!r}{role} CR={self.cr} HP={self.current_hp}/{self.max_hp}>"


# ══════════════════════════════════════════════════════════════════════════════
# D&D 5e 2024 Monsters
# Stats sourced from the 2024 Monster Manual / System Reference Document.
# ══════════════════════════════════════════════════════════════════════════════

# ── CR 0 ───────────────────────────────────────────────────────────────────

class Commoner(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Commoner"),
            size="Medium", type="Humanoid", alignment="Any",
            cr=0, ac=10, max_hp=4,
            speed=30,
            ability_scores={"Strength": 10, "Dexterity": 10, "Constitution": 10,
                            "Intelligence": 10, "Wisdom": 10, "Charisma": 10},
            senses={"Passive Perception": 10},
            languages=["Common"],
            actions=[{"name": "Club", "attack_bonus": 2, "damage": "1d4", "damage_bonus": 0, "damage_type": "bludgeoning"}],
            **kwargs,
        )


class Rat(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Rat"),
            size="Tiny", type="Beast", alignment="Unaligned",
            cr=0, ac=10, max_hp=1,
            speed=20, swimming_speed=20,
            ability_scores={"Strength": 2, "Dexterity": 11, "Constitution": 9,
                            "Intelligence": 2, "Wisdom": 10, "Charisma": 4},
            senses={"Darkvision": 30, "Passive Perception": 10},
            special_abilities=["Keen Smell: Advantage on Perception checks that rely on smell."],
            actions=[{"name": "Bite", "attack_bonus": 0, "damage": "1d1", "damage_bonus": 0, "damage_type": "piercing"}],
            **kwargs,
        )


class Bat(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Bat"),
            size="Tiny", type="Beast", alignment="Unaligned",
            cr=0, ac=12, max_hp=1,
            speed=5, flying_speed=30,
            ability_scores={"Strength": 2, "Dexterity": 15, "Constitution": 8,
                            "Intelligence": 2, "Wisdom": 12, "Charisma": 4},
            senses={"Blindsight": 60, "Passive Perception": 11},
            special_abilities=["Echolocation: Can't use Blindsight while Deafened.",
                               "Keen Hearing: Advantage on Perception checks relying on hearing."],
            actions=[{"name": "Bite", "attack_bonus": 0, "damage": "1d1", "damage_bonus": 0, "damage_type": "piercing"}],
            **kwargs,
        )


class Cat(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Cat"),
            size="Tiny", type="Beast", alignment="Unaligned",
            cr=0, ac=12, max_hp=2,
            speed=40, climbing_speed=30,
            ability_scores={"Strength": 3, "Dexterity": 15, "Constitution": 10,
                            "Intelligence": 3, "Wisdom": 12, "Charisma": 7},
            skill_proficiencies={"Perception": 3, "Stealth": 4},
            senses={"Passive Perception": 13},
            special_abilities=["Keen Smell: Advantage on Perception checks that rely on smell."],
            actions=[{"name": "Claws", "attack_bonus": 0, "damage": "1d1", "damage_bonus": 0, "damage_type": "slashing"}],
            **kwargs,
        )


# ── CR 1/8 ─────────────────────────────────────────────────────────────────

class Bandit(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Bandit"),
            size="Medium", type="Humanoid", alignment="Any Non-Lawful",
            cr=0.125, ac=12, max_hp=11,
            speed=30,
            ability_scores={"Strength": 11, "Dexterity": 12, "Constitution": 12,
                            "Intelligence": 10, "Wisdom": 10, "Charisma": 10},
            senses={"Passive Perception": 10},
            languages=["Common"],
            actions=[
                {"name": "Scimitar", "attack_bonus": 3, "damage": "1d6", "damage_bonus": 1, "damage_type": "slashing"},
                {"name": "Light Crossbow", "attack_bonus": 3, "damage": "1d8", "damage_bonus": 1, "damage_type": "piercing"},
            ],
            **kwargs,
        )


class Guard(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Guard"),
            size="Medium", type="Humanoid", alignment="Any",
            cr=0.125, ac=16, max_hp=11,
            speed=30,
            ability_scores={"Strength": 13, "Dexterity": 12, "Constitution": 12,
                            "Intelligence": 10, "Wisdom": 11, "Charisma": 10},
            skill_proficiencies={"Perception": 2},
            senses={"Passive Perception": 12},
            languages=["Common"],
            actions=[{"name": "Spear", "attack_bonus": 3, "damage": "1d6", "damage_bonus": 1, "damage_type": "piercing"}],
            **kwargs,
        )


class Kobold(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Kobold"),
            size="Small", type="Humanoid", alignment="Lawful Evil",
            cr=0.125, ac=12, max_hp=5,
            speed=30,
            ability_scores={"Strength": 7, "Dexterity": 15, "Constitution": 9,
                            "Intelligence": 8, "Wisdom": 7, "Charisma": 8},
            senses={"Darkvision": 60, "Passive Perception": 8},
            languages=["Common", "Draconic"],
            special_abilities=["Pack Tactics: Advantage on attack rolls if an ally is adjacent to target and not incapacitated.",
                               "Sunlight Sensitivity: Disadvantage on attack rolls and Perception checks in sunlight."],
            actions=[{"name": "Dagger", "attack_bonus": 4, "damage": "1d4", "damage_bonus": 2, "damage_type": "piercing"}],
            **kwargs,
        )


class Stirge(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Stirge"),
            size="Tiny", type="Beast", alignment="Unaligned",
            cr=0.125, ac=14, max_hp=2,
            speed=10, flying_speed=40,
            ability_scores={"Strength": 4, "Dexterity": 16, "Constitution": 11,
                            "Intelligence": 2, "Wisdom": 8, "Charisma": 6},
            senses={"Darkvision": 60, "Passive Perception": 9},
            special_abilities=["Blood Drain: On hit, attaches and drains 1d4+3 HP per turn. DC 10 Strength to detach."],
            actions=[{"name": "Blood Drain", "attack_bonus": 5, "damage": "1d4", "damage_bonus": 3, "damage_type": "piercing"}],
            **kwargs,
        )


# ── CR 1/4 ─────────────────────────────────────────────────────────────────

class Goblin(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Goblin"),
            size="Small", type="Humanoid", alignment="Neutral Evil",
            cr=0.25, ac=15, max_hp=7,
            speed=30,
            ability_scores={"Strength": 8, "Dexterity": 14, "Constitution": 10,
                            "Intelligence": 10, "Wisdom": 8, "Charisma": 8},
            skill_proficiencies={"Stealth": 6},
            senses={"Darkvision": 60, "Passive Perception": 9},
            languages=["Common", "Goblin"],
            special_abilities=["Nimble Escape: Can Disengage or Hide as a Bonus Action."],
            actions=[
                {"name": "Scimitar", "attack_bonus": 4, "damage": "1d6", "damage_bonus": 2, "damage_type": "slashing"},
                {"name": "Shortbow", "attack_bonus": 4, "damage": "1d6", "damage_bonus": 2, "damage_type": "piercing"},
            ],
            **kwargs,
        )


class Skeleton(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Skeleton"),
            size="Medium", type="Undead", alignment="Lawful Evil",
            cr=0.25, ac=13, max_hp=13,
            speed=30,
            ability_scores={"Strength": 10, "Dexterity": 14, "Constitution": 15,
                            "Intelligence": 6, "Wisdom": 8, "Charisma": 5},
            vulnerabilities=["bludgeoning"],
            immunities=["poison"],
            condition_immunities=["Exhaustion", "Poisoned"],
            senses={"Darkvision": 60, "Passive Perception": 9},
            actions=[
                {"name": "Shortsword", "attack_bonus": 4, "damage": "1d6", "damage_bonus": 2, "damage_type": "piercing"},
                {"name": "Shortbow", "attack_bonus": 4, "damage": "1d6", "damage_bonus": 2, "damage_type": "piercing"},
            ],
            **kwargs,
        )


class Zombie(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Zombie"),
            size="Medium", type="Undead", alignment="Neutral Evil",
            cr=0.25, ac=8, max_hp=22,
            speed=20,
            ability_scores={"Strength": 13, "Dexterity": 6, "Constitution": 16,
                            "Intelligence": 3, "Wisdom": 6, "Charisma": 5},
            saving_throw_proficiencies=["Wisdom"],
            immunities=["poison"],
            condition_immunities=["Poisoned"],
            senses={"Darkvision": 60, "Passive Perception": 8},
            special_abilities=["Undead Fortitude: When reduced to 0 HP, DC 5 + damage taken Constitution save to drop to 1 HP instead (not radiant damage or crit)."],
            actions=[{"name": "Slam", "attack_bonus": 3, "damage": "1d6", "damage_bonus": 1, "damage_type": "bludgeoning"}],
            **kwargs,
        )


class Wolf(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Wolf"),
            size="Medium", type="Beast", alignment="Unaligned",
            cr=0.25, ac=13, max_hp=11,
            speed=40,
            ability_scores={"Strength": 12, "Dexterity": 15, "Constitution": 12,
                            "Intelligence": 3, "Wisdom": 12, "Charisma": 6},
            skill_proficiencies={"Perception": 3, "Stealth": 4},
            senses={"Passive Perception": 13},
            special_abilities=["Keen Hearing and Smell: Advantage on Perception checks relying on hearing or smell.",
                               "Pack Tactics: Advantage on attack rolls if ally is adjacent to target and not incapacitated."],
            actions=[{"name": "Bite", "attack_bonus": 4, "damage": "2d4", "damage_bonus": 2, "damage_type": "piercing",
                      "notes": "DC 11 Strength or target is knocked Prone."}],
            **kwargs,
        )


class PoisonousSnake(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Poisonous Snake"),
            size="Tiny", type="Beast", alignment="Unaligned",
            cr=0.125, ac=13, max_hp=2,
            speed=30, swimming_speed=30,
            ability_scores={"Strength": 2, "Dexterity": 16, "Constitution": 11,
                            "Intelligence": 1, "Wisdom": 10, "Charisma": 3},
            senses={"Blindsight": 10, "Passive Perception": 10},
            special_abilities=["Bite: On hit, target makes DC 10 Con save or takes 2d4 poison damage (half on save)."],
            actions=[{"name": "Bite", "attack_bonus": 5, "damage": "1d1", "damage_bonus": 0, "damage_type": "piercing",
                      "notes": "Plus 2d4 poison damage (DC 10 Con save halves)."}],
            **kwargs,
        )


# ── CR 1/2 ─────────────────────────────────────────────────────────────────

class Hobgoblin(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Hobgoblin"),
            size="Medium", type="Humanoid", alignment="Lawful Evil",
            cr=0.5, ac=18, max_hp=11,
            speed=30,
            ability_scores={"Strength": 13, "Dexterity": 12, "Constitution": 12,
                            "Intelligence": 10, "Wisdom": 10, "Charisma": 9},
            senses={"Darkvision": 60, "Passive Perception": 10},
            languages=["Common", "Goblin"],
            special_abilities=["Martial Advantage: Once per turn, +2d6 damage if an ally is adjacent to target."],
            actions=[
                {"name": "Longsword", "attack_bonus": 3, "damage": "1d8", "damage_bonus": 1, "damage_type": "slashing"},
                {"name": "Longbow", "attack_bonus": 3, "damage": "1d8", "damage_bonus": 1, "damage_type": "piercing"},
            ],
            **kwargs,
        )


class Orc(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Orc"),
            size="Medium", type="Humanoid", alignment="Chaotic Evil",
            cr=0.5, ac=13, max_hp=15,
            speed=30,
            ability_scores={"Strength": 16, "Dexterity": 12, "Constitution": 16,
                            "Intelligence": 7, "Wisdom": 11, "Charisma": 10},
            skill_proficiencies={"Intimidation": 2},
            senses={"Darkvision": 60, "Passive Perception": 10},
            languages=["Common", "Orc"],
            special_abilities=["Aggressive: As a Bonus Action, move up to speed toward a hostile creature."],
            actions=[
                {"name": "Greataxe", "attack_bonus": 5, "damage": "1d12", "damage_bonus": 3, "damage_type": "slashing"},
                {"name": "Javelin", "attack_bonus": 5, "damage": "1d6", "damage_bonus": 3, "damage_type": "piercing"},
            ],
            **kwargs,
        )


class Scout(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Scout"),
            size="Medium", type="Humanoid", alignment="Any",
            cr=0.5, ac=13, max_hp=16,
            speed=30,
            ability_scores={"Strength": 11, "Dexterity": 14, "Constitution": 12,
                            "Intelligence": 11, "Wisdom": 13, "Charisma": 11},
            skill_proficiencies={"Nature": 4, "Perception": 5, "Stealth": 6, "Survival": 5},
            senses={"Passive Perception": 15},
            languages=["Common"],
            special_abilities=["Keen Hearing and Sight: Advantage on Perception checks relying on hearing or sight."],
            actions=[
                {"name": "Multiattack", "notes": "Two Shortsword attacks or two Longbow attacks."},
                {"name": "Shortsword", "attack_bonus": 4, "damage": "1d6", "damage_bonus": 2, "damage_type": "piercing"},
                {"name": "Longbow", "attack_bonus": 4, "damage": "1d8", "damage_bonus": 2, "damage_type": "piercing"},
            ],
            **kwargs,
        )


# ── CR 1 ───────────────────────────────────────────────────────────────────

class Bugbear(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Bugbear"),
            size="Medium", type="Humanoid", alignment="Chaotic Evil",
            cr=1, ac=16, max_hp=27,
            speed=30,
            ability_scores={"Strength": 15, "Dexterity": 14, "Constitution": 13,
                            "Intelligence": 8, "Wisdom": 11, "Charisma": 9},
            skill_proficiencies={"Stealth": 6, "Survival": 2},
            senses={"Darkvision": 60, "Passive Perception": 10},
            languages=["Common", "Goblin"],
            special_abilities=["Brute: Melee attacks deal one extra die of damage on hit (included).",
                               "Surprise Attack: +2d6 damage on first attack if target hasn't acted yet."],
            actions=[
                {"name": "Morningstar", "attack_bonus": 4, "damage": "2d8", "damage_bonus": 2, "damage_type": "piercing"},
                {"name": "Javelin", "attack_bonus": 4, "damage": "2d6", "damage_bonus": 2, "damage_type": "piercing"},
            ],
            **kwargs,
        )


class DireWolf(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Dire Wolf"),
            size="Large", type="Beast", alignment="Unaligned",
            cr=1, ac=14, max_hp=37,
            speed=50,
            ability_scores={"Strength": 17, "Dexterity": 15, "Constitution": 15,
                            "Intelligence": 3, "Wisdom": 12, "Charisma": 7},
            skill_proficiencies={"Perception": 3, "Stealth": 4},
            senses={"Passive Perception": 13},
            special_abilities=["Keen Hearing and Smell: Advantage on Perception checks relying on hearing or smell.",
                               "Pack Tactics: Advantage on attacks if ally is adjacent to target."],
            actions=[{"name": "Bite", "attack_bonus": 5, "damage": "2d6", "damage_bonus": 3, "damage_type": "piercing",
                      "notes": "DC 13 Strength save or target is knocked Prone."}],
            **kwargs,
        )


class Ghoul(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Ghoul"),
            size="Medium", type="Undead", alignment="Chaotic Evil",
            cr=1, ac=12, max_hp=22,
            speed=30,
            ability_scores={"Strength": 13, "Dexterity": 15, "Constitution": 10,
                            "Intelligence": 7, "Wisdom": 10, "Charisma": 6},
            immunities=["poison"],
            condition_immunities=["Charmed", "Exhaustion", "Poisoned"],
            senses={"Darkvision": 60, "Passive Perception": 10},
            special_abilities=["Claws: On hit, target makes DC 10 Con save or is Paralyzed until end of its next turn (not elves or undead)."],
            actions=[
                {"name": "Bite", "attack_bonus": 2, "damage": "2d6", "damage_bonus": 2, "damage_type": "piercing"},
                {"name": "Claws", "attack_bonus": 4, "damage": "2d4", "damage_bonus": 2, "damage_type": "slashing",
                 "notes": "DC 10 Con save or target is Paralyzed until end of its next turn."},
            ],
            **kwargs,
        )


class Harpy(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Harpy"),
            size="Medium", type="Monstrosity", alignment="Chaotic Evil",
            cr=1, ac=11, max_hp=38,
            speed=20, flying_speed=40,
            ability_scores={"Strength": 12, "Dexterity": 13, "Constitution": 12,
                            "Intelligence": 7, "Wisdom": 10, "Charisma": 13},
            senses={"Passive Perception": 10},
            languages=["Common"],
            special_abilities=["Luring Song: Each humanoid/giant within 300 ft that can hear must succeed DC 11 Wis save or be Charmed and Incapacitated, moving toward the harpy each turn."],
            actions=[
                {"name": "Multiattack", "notes": "Two attacks: one Claws and one Club."},
                {"name": "Claws", "attack_bonus": 3, "damage": "2d4", "damage_bonus": 1, "damage_type": "slashing"},
                {"name": "Club", "attack_bonus": 3, "damage": "1d4", "damage_bonus": 1, "damage_type": "bludgeoning"},
            ],
            **kwargs,
        )


# ── CR 2 ───────────────────────────────────────────────────────────────────

class Ogre(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Ogre"),
            size="Large", type="Giant", alignment="Chaotic Evil",
            cr=2, ac=11, max_hp=59,
            speed=40,
            ability_scores={"Strength": 19, "Dexterity": 8, "Constitution": 16,
                            "Intelligence": 5, "Wisdom": 7, "Charisma": 7},
            senses={"Darkvision": 60, "Passive Perception": 8},
            languages=["Common", "Giant"],
            actions=[
                {"name": "Greatclub", "attack_bonus": 6, "damage": "2d8", "damage_bonus": 4, "damage_type": "bludgeoning"},
                {"name": "Javelin", "attack_bonus": 6, "damage": "2d6", "damage_bonus": 4, "damage_type": "piercing"},
            ],
            **kwargs,
        )


class GiantSpider(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Giant Spider"),
            size="Large", type="Beast", alignment="Unaligned",
            cr=1, ac=14, max_hp=26,
            speed=30, climbing_speed=30,
            ability_scores={"Strength": 14, "Dexterity": 16, "Constitution": 12,
                            "Intelligence": 2, "Wisdom": 11, "Charisma": 4},
            skill_proficiencies={"Stealth": 7},
            senses={"Blindsight": 10, "Darkvision": 60, "Passive Perception": 10},
            special_abilities=["Spider Climb: Can climb difficult surfaces including ceilings without a check.",
                               "Web Sense: While in contact with a web, knows location of other creatures touching it.",
                               "Web Walker: Ignores movement restrictions from webs."],
            actions=[
                {"name": "Bite", "attack_bonus": 5, "damage": "1d8", "damage_bonus": 3, "damage_type": "piercing",
                 "notes": "DC 11 Con save or take 2d8 poison (half on save). Fail by 5+ = Poisoned for 1 hour."},
                {"name": "Web", "attack_bonus": 5, "damage": "0d0", "damage_bonus": 0, "damage_type": "none",
                 "notes": "Recharge 5-6. DC 12 Dex save or target is Restrained. DC 12 Str check to break free."},
            ],
            **kwargs,
        )


class SeaHag(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Sea Hag"),
            size="Medium", type="Fey", alignment="Chaotic Evil",
            cr=2, ac=14, max_hp=52,
            speed=30, swimming_speed=40,
            ability_scores={"Strength": 16, "Dexterity": 13, "Constitution": 16,
                            "Intelligence": 12, "Wisdom": 12, "Charisma": 13},
            senses={"Darkvision": 60, "Passive Perception": 11},
            languages=["Aquan", "Common", "Giant"],
            special_abilities=["Horrific Appearance: Humanoid that sees the hag makes DC 11 Wis save or is Frightened for 1 minute.",
                               "Death Glare: Stare at one Frightened creature within 30 ft — it drops to 0 HP on failed DC 11 Wis save."],
            actions=[{"name": "Claws", "attack_bonus": 5, "damage": "2d6", "damage_bonus": 3, "damage_type": "slashing"}],
            **kwargs,
        )


# ── CR 3 ───────────────────────────────────────────────────────────────────

class Manticore(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Manticore"),
            size="Large", type="Monstrosity", alignment="Lawful Evil",
            cr=3, ac=14, max_hp=68,
            speed=30, flying_speed=50,
            ability_scores={"Strength": 17, "Dexterity": 16, "Constitution": 17,
                            "Intelligence": 7, "Wisdom": 12, "Charisma": 8},
            senses={"Darkvision": 60, "Passive Perception": 11},
            languages=["Common"],
            special_abilities=["Tail Spike Regrowth: Has 24 tail spikes. Used spikes regrow when taking a Long Rest."],
            actions=[
                {"name": "Multiattack", "notes": "Three attacks: one Bite and two Claws, or three Tail Spikes."},
                {"name": "Bite", "attack_bonus": 5, "damage": "1d8", "damage_bonus": 3, "damage_type": "piercing"},
                {"name": "Claw", "attack_bonus": 5, "damage": "1d6", "damage_bonus": 3, "damage_type": "slashing"},
                {"name": "Tail Spike", "attack_bonus": 5, "damage": "1d8", "damage_bonus": 3, "damage_type": "piercing"},
            ],
            **kwargs,
        )


class Mummy(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Mummy"),
            size="Medium", type="Undead", alignment="Lawful Evil",
            cr=3, ac=11, max_hp=58,
            speed=20,
            ability_scores={"Strength": 16, "Dexterity": 8, "Constitution": 15,
                            "Intelligence": 6, "Wisdom": 10, "Charisma": 12},
            saving_throw_proficiencies=["Wisdom"],
            resistances=["bludgeoning", "piercing", "slashing"],
            immunities=["necrotic", "poison"],
            condition_immunities=["Charmed", "Exhaustion", "Frightened", "Paralyzed", "Poisoned"],
            senses={"Darkvision": 60, "Passive Perception": 10},
            languages=["The languages it knew in life"],
            special_abilities=["Mummy Rot: Humanoid hit by Rotting Fist can't regain HP and max HP decreases by 3d6 each long rest until cured (Remove Curse or similar)."],
            actions=[
                {"name": "Multiattack", "notes": "Two attacks: one Dreadful Glare and one Rotting Fist."},
                {"name": "Dreadful Glare", "attack_bonus": 0, "damage": "0d0", "damage_bonus": 0, "damage_type": "none",
                 "notes": "Target within 60 ft: DC 11 Wis save or Frightened until end of mummy's next turn. Fail by 5+ = also Paralyzed."},
                {"name": "Rotting Fist", "attack_bonus": 5, "damage": "2d6", "damage_bonus": 3, "damage_type": "bludgeoning",
                 "notes": "Plus 3d6 necrotic damage and Mummy Rot curse."},
            ],
            **kwargs,
        )


class Wight(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Wight"),
            size="Medium", type="Undead", alignment="Neutral Evil",
            cr=3, ac=14, max_hp=45,
            speed=30,
            ability_scores={"Strength": 15, "Dexterity": 14, "Constitution": 16,
                            "Intelligence": 10, "Wisdom": 13, "Charisma": 15},
            saving_throw_proficiencies=["Strength", "Constitution", "Wisdom"],
            skill_proficiencies={"Perception": 3, "Stealth": 4},
            resistances=["necrotic", "bludgeoning", "piercing", "slashing"],
            immunities=["poison"],
            condition_immunities=["Exhaustion", "Poisoned"],
            senses={"Darkvision": 60, "Passive Perception": 13},
            languages=["The languages it knew in life"],
            special_abilities=["Sunlight Sensitivity: Disadvantage on attacks and Perception checks in sunlight.",
                               "Life Drain: On Longsword hit, DC 13 Con save or max HP reduced by damage dealt. Dies if max HP drops to 0. Rises as zombie under wight's control."],
            actions=[
                {"name": "Multiattack", "notes": "Two Longsword attacks or two Longbow attacks."},
                {"name": "Longsword", "attack_bonus": 4, "damage": "1d8", "damage_bonus": 2, "damage_type": "slashing",
                 "notes": "Plus life drain effect."},
                {"name": "Longbow", "attack_bonus": 4, "damage": "1d8", "damage_bonus": 2, "damage_type": "piercing"},
            ],
            **kwargs,
        )


# ── CR 4 ───────────────────────────────────────────────────────────────────

class Banshee(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Banshee"),
            size="Medium", type="Undead", alignment="Chaotic Evil",
            cr=4, ac=12, max_hp=58,
            speed=0, flying_speed=40,
            ability_scores={"Strength": 1, "Dexterity": 14, "Constitution": 10,
                            "Intelligence": 12, "Wisdom": 11, "Charisma": 17},
            saving_throw_proficiencies=["Wisdom", "Charisma"],
            resistances=["acid", "fire", "lightning", "thunder", "bludgeoning", "piercing", "slashing"],
            immunities=["cold", "necrotic", "poison"],
            condition_immunities=["Charmed", "Exhaustion", "Frightened", "Grappled", "Paralyzed",
                                  "Petrified", "Poisoned", "Prone", "Restrained"],
            senses={"Darkvision": 60, "Passive Perception": 10},
            languages=["Common", "Elvish"],
            special_abilities=["Detect Life: Senses living creatures within 5 miles.",
                               "Incorporeal Movement: Can move through creatures and objects (costs 5 ft per ft to move through solid objects)."],
            actions=[
                {"name": "Corrupting Touch", "attack_bonus": 4, "damage": "3d6", "damage_bonus": 0, "damage_type": "necrotic"},
                {"name": "Horrifying Visage", "attack_bonus": 0, "damage": "0d0", "damage_bonus": 0, "damage_type": "none",
                 "notes": "Each non-undead within 60 ft: DC 13 Wis save or Frightened for 1 minute. Fails by 5+ = ages 1d4 x 10 years."},
                {"name": "Wail", "attack_bonus": 0, "damage": "0d0", "damage_bonus": 0, "damage_type": "none",
                 "notes": "Recharge 1/day. Each non-undead within 30 ft: DC 13 Con save or drop to 0 HP. Save = 3d6 psychic damage."},
            ],
            **kwargs,
        )


class Ettin(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Ettin"),
            size="Large", type="Giant", alignment="Chaotic Evil",
            cr=4, ac=12, max_hp=85,
            speed=40,
            ability_scores={"Strength": 21, "Dexterity": 8, "Constitution": 17,
                            "Intelligence": 6, "Wisdom": 10, "Charisma": 8},
            skill_proficiencies={"Perception": 4},
            senses={"Darkvision": 60, "Passive Perception": 14},
            languages=["Giant", "Orc"],
            special_abilities=["Two Heads: Advantage on Perception checks and Wis saving throws.",
                               "Wakeful: When one head sleeps, the other stays awake."],
            actions=[
                {"name": "Multiattack", "notes": "Two attacks: one Battleaxe (right head) and one Morningstar (left head)."},
                {"name": "Battleaxe", "attack_bonus": 7, "damage": "2d8", "damage_bonus": 5, "damage_type": "slashing"},
                {"name": "Morningstar", "attack_bonus": 7, "damage": "2d8", "damage_bonus": 5, "damage_type": "piercing"},
            ],
            **kwargs,
        )


# ── CR 5 ───────────────────────────────────────────────────────────────────

class HillGiant(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Hill Giant"),
            size="Huge", type="Giant", alignment="Chaotic Evil",
            cr=5, ac=13, max_hp=105,
            speed=40,
            ability_scores={"Strength": 21, "Dexterity": 8, "Constitution": 19,
                            "Intelligence": 5, "Wisdom": 9, "Charisma": 6},
            skill_proficiencies={"Perception": 2},
            senses={"Passive Perception": 12},
            languages=["Giant"],
            actions=[
                {"name": "Multiattack", "notes": "Two Greatclub attacks."},
                {"name": "Greatclub", "attack_bonus": 8, "damage": "3d8", "damage_bonus": 5, "damage_type": "bludgeoning"},
                {"name": "Rock", "attack_bonus": 8, "damage": "3d10", "damage_bonus": 5, "damage_type": "bludgeoning"},
            ],
            **kwargs,
        )


class Troll(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Troll"),
            size="Large", type="Giant", alignment="Chaotic Evil",
            cr=5, ac=15, max_hp=84,
            speed=30,
            ability_scores={"Strength": 18, "Dexterity": 13, "Constitution": 20,
                            "Intelligence": 7, "Wisdom": 9, "Charisma": 7},
            skill_proficiencies={"Perception": 2},
            senses={"Darkvision": 60, "Passive Perception": 12},
            languages=["Giant"],
            special_abilities=["Keen Smell: Advantage on Perception checks relying on smell.",
                               "Regeneration: Regain 10 HP at start of turn unless took acid or fire damage this turn. Dies at 0 HP only if it can't regenerate."],
            actions=[
                {"name": "Multiattack", "notes": "One Bite and two Claw attacks."},
                {"name": "Bite", "attack_bonus": 7, "damage": "1d6", "damage_bonus": 4, "damage_type": "piercing"},
                {"name": "Claw", "attack_bonus": 7, "damage": "2d6", "damage_bonus": 4, "damage_type": "slashing"},
            ],
            **kwargs,
        )


class VampireSpawn(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Vampire Spawn"),
            size="Medium", type="Undead", alignment="Neutral Evil",
            cr=5, ac=15, max_hp=82,
            speed=30, climbing_speed=30,
            ability_scores={"Strength": 16, "Dexterity": 16, "Constitution": 16,
                            "Intelligence": 11, "Wisdom": 10, "Charisma": 12},
            saving_throw_proficiencies=["Dexterity", "Wisdom"],
            skill_proficiencies={"Perception": 3, "Stealth": 6},
            resistances=["necrotic", "bludgeoning", "piercing", "slashing"],
            senses={"Darkvision": 60, "Passive Perception": 13},
            languages=["The languages it knew in life"],
            special_abilities=["Regeneration: Regain 10 HP at start of turn if above 0 HP (not radiant or running water).",
                               "Spider Climb: Can climb difficult surfaces including ceilings.",
                               "Vampire Weaknesses: Destroyed by sunlight (20 radiant at start of turn); can't cross running water; repelled by garlic/holy symbols."],
            actions=[
                {"name": "Multiattack", "notes": "Two attacks: one Claws and one Bite."},
                {"name": "Claws", "attack_bonus": 6, "damage": "2d4", "damage_bonus": 3, "damage_type": "slashing"},
                {"name": "Bite", "attack_bonus": 6, "damage": "1d6", "damage_bonus": 3, "damage_type": "piercing",
                 "notes": "Plus 2d6 necrotic. Target's max HP reduced by necrotic taken. Spawn regains HP equal to necrotic dealt."},
            ],
            **kwargs,
        )


# ── CR 8 ───────────────────────────────────────────────────────────────────

class Assassin(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Assassin"),
            size="Medium", type="Humanoid", alignment="Any Non-Good",
            cr=8, ac=15, max_hp=78,
            speed=30,
            ability_scores={"Strength": 11, "Dexterity": 16, "Constitution": 14,
                            "Intelligence": 13, "Wisdom": 11, "Charisma": 10},
            saving_throw_proficiencies=["Dexterity", "Intelligence"],
            skill_proficiencies={"Acrobatics": 6, "Deception": 3, "Perception": 3, "Stealth": 9},
            resistances=["poison"],
            senses={"Passive Perception": 13},
            languages=["Thieves' Cant", "Common"],
            special_abilities=["Assassinate: Advantage on attacks against creatures that haven't acted. Any hit against Surprised creatures is a critical hit.",
                               "Evasion: On Dex save vs area: no damage on success, half on fail.",
                               "Sneak Attack: +4d6 damage once per turn if advantage or ally adjacent to target."],
            actions=[
                {"name": "Multiattack", "notes": "Two Shortsword attacks."},
                {"name": "Shortsword", "attack_bonus": 6, "damage": "1d6", "damage_bonus": 3, "damage_type": "piercing",
                 "notes": "Plus 4d6 poison (DC 15 Con save halves)."},
                {"name": "Hand Crossbow", "attack_bonus": 6, "damage": "1d6", "damage_bonus": 3, "damage_type": "piercing",
                 "notes": "Plus 4d6 poison (DC 15 Con save halves)."},
            ],
            **kwargs,
        )


# ── CR 9 ───────────────────────────────────────────────────────────────────

class CloudGiant(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Cloud Giant"),
            size="Huge", type="Giant", alignment="Neutral Good or Neutral Evil",
            cr=9, ac=14, max_hp=200,
            speed=40, flying_speed=0,
            ability_scores={"Strength": 27, "Dexterity": 10, "Constitution": 22,
                            "Intelligence": 12, "Wisdom": 16, "Charisma": 16},
            saving_throw_proficiencies=["Constitution", "Wisdom", "Charisma"],
            skill_proficiencies={"Insight": 7, "Perception": 7},
            senses={"Passive Perception": 17},
            languages=["Common", "Giant"],
            special_abilities=["Keen Smell: Advantage on Perception checks relying on smell.",
                               "Innate Spellcasting: Wis-based DC 15. At will: Detect Magic, Fog Cloud, Light. 3/day: Feather Fall, Fly, Misty Step, Telekinesis. 1/day: Control Weather, Gaseous Form."],
            actions=[
                {"name": "Multiattack", "notes": "Two Morningstar attacks."},
                {"name": "Morningstar", "attack_bonus": 12, "damage": "3d8", "damage_bonus": 8, "damage_type": "piercing"},
                {"name": "Rock", "attack_bonus": 12, "damage": "4d10", "damage_bonus": 8, "damage_type": "bludgeoning"},
            ],
            **kwargs,
        )


# ── CR 13 ──────────────────────────────────────────────────────────────────

class Vampire(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Vampire"),
            size="Medium", type="Undead", alignment="Lawful Evil",
            cr=13, ac=16, max_hp=144,
            speed=30, climbing_speed=30,
            ability_scores={"Strength": 18, "Dexterity": 18, "Constitution": 18,
                            "Intelligence": 17, "Wisdom": 15, "Charisma": 18},
            saving_throw_proficiencies=["Dexterity", "Wisdom", "Charisma"],
            skill_proficiencies={"Perception": 7, "Stealth": 9},
            resistances=["necrotic", "bludgeoning", "piercing", "slashing"],
            senses={"Darkvision": 120, "Passive Perception": 17},
            languages=["The languages it knew in life"],
            special_abilities=["Legendary Resistance (3/Day): Choose to succeed a failed saving throw.",
                               "Regeneration: Regain 20 HP at start of turn (not sunlight or running water).",
                               "Spider Climb: Can climb difficult surfaces including ceilings.",
                               "Vampire Weaknesses: Destroyed by sunlight; can't cross running water; repelled by garlic/holy symbols."],
            actions=[
                {"name": "Multiattack", "notes": "Two attacks: one Unarmed Strike and one Bite, or use Charm."},
                {"name": "Unarmed Strike", "attack_bonus": 9, "damage": "1d8", "damage_bonus": 4, "damage_type": "bludgeoning",
                 "notes": "Target is Grappled (escape DC 18) on hit."},
                {"name": "Bite", "attack_bonus": 9, "damage": "1d6", "damage_bonus": 4, "damage_type": "piercing",
                 "notes": "Only vs Grappled, Incapacitated, or Restrained target. Plus 3d6 necrotic. Max HP reduced by necrotic. Vampire regains that HP."},
                {"name": "Charm", "attack_bonus": 0, "damage": "0d0", "damage_bonus": 0, "damage_type": "none",
                 "notes": "Target within 30 ft: DC 17 Wis save or Charmed for 24 hours (repeats when damaged)."},
            ],
            legendary_actions=[
                {"name": "Move", "notes": "Move up to speed without provoking opportunity attacks."},
                {"name": "Unarmed Strike", "notes": "Make one Unarmed Strike."},
                {"name": "Bite (Costs 2)", "notes": "Make one Bite attack."},
            ],
            **kwargs,
        )


# ── CR 17 ──────────────────────────────────────────────────────────────────

class AdultRedDragon(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Adult Red Dragon"),
            size="Huge", type="Dragon", alignment="Chaotic Evil",
            cr=17, ac=19, max_hp=256,
            speed=40, climbing_speed=40, flying_speed=80,
            ability_scores={"Strength": 27, "Dexterity": 10, "Constitution": 25,
                            "Intelligence": 16, "Wisdom": 13, "Charisma": 21},
            saving_throw_proficiencies=["Dexterity", "Constitution", "Wisdom", "Charisma"],
            skill_proficiencies={"Perception": 13, "Stealth": 6},
            immunities=["fire"],
            senses={"Blindsight": 60, "Darkvision": 120, "Passive Perception": 23},
            languages=["Common", "Draconic"],
            special_abilities=["Legendary Resistance (3/Day): Choose to succeed a failed saving throw.",
                               "Fire Aura (Lair only): Difficult terrain within 20 ft. Creatures that start their turn there take 5 fire damage."],
            actions=[
                {"name": "Multiattack", "notes": "One Frightful Presence + three attacks: one Bite and two Claws."},
                {"name": "Bite", "attack_bonus": 14, "damage": "2d10", "damage_bonus": 8, "damage_type": "piercing",
                 "notes": "Plus 4d6 fire damage."},
                {"name": "Claw", "attack_bonus": 14, "damage": "2d6", "damage_bonus": 8, "damage_type": "slashing"},
                {"name": "Tail", "attack_bonus": 14, "damage": "2d8", "damage_bonus": 8, "damage_type": "bludgeoning"},
                {"name": "Frightful Presence", "attack_bonus": 0, "damage": "0d0", "damage_bonus": 0, "damage_type": "none",
                 "notes": "Each creature of choice within 120 ft: DC 19 Wis save or Frightened for 1 minute."},
                {"name": "Fire Breath", "attack_bonus": 0, "damage": "16d6", "damage_bonus": 0, "damage_type": "fire",
                 "notes": "Recharge 5-6. 60-ft cone. DC 21 Dex save; half on success."},
            ],
            legendary_actions=[
                {"name": "Detect", "notes": "Make a Perception check."},
                {"name": "Tail Attack", "notes": "Make a Tail attack."},
                {"name": "Wing Attack (Costs 2)", "notes": "Beat wings. Each creature within 10 ft: DC 22 Dex save or take 15 damage and knocked Prone. Dragon then flies up to half speed."},
            ],
            **kwargs,
        )


# ── CR 21 ──────────────────────────────────────────────────────────────────

class Lich(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Lich"),
            size="Medium", type="Undead", alignment="Any Evil",
            cr=21, ac=17, max_hp=135,
            speed=30,
            ability_scores={"Strength": 11, "Dexterity": 16, "Constitution": 16,
                            "Intelligence": 20, "Wisdom": 14, "Charisma": 16},
            saving_throw_proficiencies=["Constitution", "Intelligence", "Wisdom"],
            skill_proficiencies={"Arcana": 18, "History": 12, "Insight": 9, "Perception": 9},
            resistances=["cold", "lightning", "necrotic"],
            immunities=["poison", "bludgeoning", "piercing", "slashing"],
            condition_immunities=["Charmed", "Exhaustion", "Frightened", "Paralyzed", "Poisoned"],
            senses={"Truesight": 120, "Passive Perception": 19},
            languages=["Common and up to five other languages"],
            special_abilities=["Legendary Resistance (3/Day): Choose to succeed a failed saving throw.",
                               "Rejuvenation: If the lich has a phylactery, it regains a new body in 1d10 days after being destroyed.",
                               "Spellcasting: Int-based DC 20, +12 to hit. Prepared spells include Fireball, Lightning Bolt, Power Word Kill, Time Stop, and many more."],
            actions=[
                {"name": "Paralyzing Touch", "attack_bonus": 7, "damage": "3d6", "damage_bonus": 0, "damage_type": "cold",
                 "notes": "DC 18 Con save or Paralyzed for 1 minute (repeats at end of each turn)."},
            ],
            legendary_actions=[
                {"name": "Cantrip", "notes": "Cast a cantrip."},
                {"name": "Paralyzing Touch (Costs 2)", "notes": "Use Paralyzing Touch."},
                {"name": "Frightening Gaze (Costs 2)", "notes": "Target within 10 ft: DC 18 Wis save or Frightened for 1 minute."},
                {"name": "Disrupt Life (Costs 3)", "notes": "Each non-undead within 20 ft: DC 18 Con save or take 6d6 necrotic damage."},
            ],
            **kwargs,
        )


# ── CR 24 ──────────────────────────────────────────────────────────────────

class AncientRedDragon(Monster):
    def __init__(self, **kwargs):
        super().__init__(
            name=kwargs.pop("name", "Ancient Red Dragon"),
            size="Gargantuan", type="Dragon", alignment="Chaotic Evil",
            cr=24, ac=22, max_hp=546,
            speed=40, climbing_speed=40, flying_speed=80,
            ability_scores={"Strength": 30, "Dexterity": 10, "Constitution": 29,
                            "Intelligence": 18, "Wisdom": 15, "Charisma": 23},
            saving_throw_proficiencies=["Dexterity", "Constitution", "Wisdom", "Charisma"],
            skill_proficiencies={"Perception": 16, "Stealth": 7},
            immunities=["fire"],
            senses={"Blindsight": 60, "Darkvision": 120, "Passive Perception": 26},
            languages=["Common", "Draconic"],
            special_abilities=["Legendary Resistance (3/Day): Choose to succeed a failed saving throw.",
                               "Volcanic Aura (Lair only): Ranged weapon attacks within 60 ft have disadvantage. Fire in lair can erupt from ground."],
            actions=[
                {"name": "Multiattack", "notes": "One Frightful Presence + three attacks: one Bite and two Claws."},
                {"name": "Bite", "attack_bonus": 17, "damage": "2d10", "damage_bonus": 10, "damage_type": "piercing",
                 "notes": "Plus 4d6 fire damage."},
                {"name": "Claw", "attack_bonus": 17, "damage": "2d6", "damage_bonus": 10, "damage_type": "slashing"},
                {"name": "Tail", "attack_bonus": 17, "damage": "2d8", "damage_bonus": 10, "damage_type": "bludgeoning"},
                {"name": "Frightful Presence", "attack_bonus": 0, "damage": "0d0", "damage_bonus": 0, "damage_type": "none",
                 "notes": "Each creature of choice within 120 ft: DC 21 Wis save or Frightened for 1 minute."},
                {"name": "Fire Breath", "attack_bonus": 0, "damage": "26d6", "damage_bonus": 0, "damage_type": "fire",
                 "notes": "Recharge 5-6. 90-ft cone. DC 24 Dex save; half on success."},
            ],
            legendary_actions=[
                {"name": "Detect", "notes": "Make a Perception check."},
                {"name": "Tail Attack", "notes": "Make a Tail attack."},
                {"name": "Wing Attack (Costs 2)", "notes": "Beat wings. Each creature within 15 ft: DC 25 Dex save or take 17 damage and knocked Prone. Dragon then flies up to half speed."},
            ],
            **kwargs,
        )
