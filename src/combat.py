"""Turn-based combat encounter manager.

Usage::

    from src.map import Map, Wall
    from src.creatures import Character
    from src.creatures.monsters import Goblin, Orc
    from src.combat import Combat

    dungeon = Map(20, 15, name="Dungeon Level 1")
    dungeon.place_creature(hero, 5, 7)
    dungeon.place_creature(goblin, 14, 7)

    battle = Combat(dungeon, players=[hero], monsters=[goblin])
    result = battle.run()   # "players" | "monsters"

Monster AI
----------
- Ranged preference: if the monster has any action with a ``"range"`` key > 5 ft,
  it tries to stay at optimal range, backing away when cornered, and attacks
  with its best ranged action.  Falls back to melee if the target is beyond
  ranged reach or if it has no ranged option.
- Melee preference: charges the nearest player and attacks when adjacent.

Player turn commands
--------------------
  move <x> <y> [z]            Move toward grid cell (x, y) or (x, y, z).
  attack [name] [weapon]       Attack a named enemy with an optional weapon.
  cast <spell> [target]        Cast a spell (action or bonus action).
  ability <name> [target]      Use a special ability (action or bonus action).
  dash                         Use your action to gain a second move this turn.
  spells                       List your available spells.
  abilities                    List your available special abilities.
  pass                         End your turn immediately.
"""

from __future__ import annotations

import math
import re
import shlex

from src.common import roll_dice
from src.creatures import Character


# ── Internal helpers ──────────────────────────────────────────────────────────

def _is_dead(creature) -> bool:
    return creature.current_hp <= 0 or any(
        getattr(e, "name", e) == "Dead" for e in creature.active_effects
    )


def _is_incapacitated(creature) -> bool:
    bad = {"Dead", "Unconscious", "Paralyzed", "Stunned", "Petrified"}
    return any(getattr(e, "name", e) in bad for e in creature.active_effects)


def _hp_bar(creature, width: int = 10) -> str:
    pct = max(0.0, creature.current_hp / creature.max_hp)
    filled = round(pct * width)
    bar = "#" * filled + "." * (width - filled)
    return f"[{bar}] {creature.current_hp}/{creature.max_hp} HP"


def _reset_turn(creature):
    """Restore per-turn action and speed resources, reset activity tracking flags."""
    creature.actions_left = 1
    creature.attack_actions_left = 0
    if hasattr(creature, "bonus_actions_left"):
        creature.bonus_actions_left = 1
    creature.bonus_speed = 0
    # Per-turn activity flags used for Rage end-condition and similar tracking
    creature._attacked_this_turn = False
    creature._took_damage_this_turn = False
    creature._forced_save_this_turn = False


def _tick_conditions(creature, start_of_turn=False) -> list[str]:
    """Decrement duration on all timed conditions; remove any that reach 0.

    Returns the list of condition names that expired.
    """
    expired = []
    for effect in list(creature.active_effects):
        if (getattr(effect, "expires_at_start", False) and start_of_turn) or not start_of_turn:
            if effect.duration is not None:
                effect.duration -= 1
                if effect.duration <= 0:
                    expired.append(effect.name)
                    effect.remove(creature)
    return expired


def _check_rage_end(player) -> bool:
    """Check Rage's activity conditions at end of the barbarian's turn.

    With Persistent Rage (level 15+), the rage never ends from inactivity.
    Otherwise, Rage ends if the player finished their turn without:
      - making a weapon attack, OR
      - taking damage since their last turn started, OR
      - forcing an enemy to make a saving throw.

    Returns True if Rage ended.
    """
    rage = next(
        (e for e in player.active_effects if getattr(e, "name", None) == "Rage"),
        None,
    )
    if rage is None:
        return False
    # Persistent Rage (level 15): no activity check needed
    if getattr(player, "persistent_rage", False):
        return False
    attacked = getattr(player, "_attacked_this_turn", False)
    took_damage = getattr(player, "_took_damage_this_turn", False)
    forced_save = getattr(player, "_forced_save_this_turn", False)
    if not (attacked or took_damage or forced_save):
        player.remove_condition("Rage")
        print(f"  {player.name}'s Rage ends — no attack, damage taken, or saving throw forced.")
        return True
    return False


def _check_relentless_rage(player) -> bool:
    """When a barbarian with Relentless Rage drops to 0 HP while raging, attempt a Con save.

    On success, HP is set to twice the barbarian level instead of 0.
    The DC starts at 10 and increases by 5 per use; resets on Short/Long Rest.

    Returns True if Relentless Rage saved the player.
    """
    if player.current_hp > 0:
        return False
    dc = getattr(player, "relentless_rage_dc", None)
    if dc is None:
        return False
    if not any(getattr(e, "name", None) == "Rage" for e in player.active_effects):
        return False
    print(f"  {player.name} drops to 0 HP while raging! Relentless Rage activates (DC {dc} Con save).")
    success, _, _, _ = player.roll_check("Constitution", beat=dc, check_type="Saving Throws")
    if success:
        barb_level = next((cls.level for cls in player.classes if cls.name == "Barbarian"), 1)
        player.current_hp = barb_level * 2
        player.relentless_rage_dc = dc + 5
        print(f"  Success! {player.name} surges with rage — HP set to {player.current_hp}. (Next DC: {player.relentless_rage_dc})")
        return True
    else:
        print(f"  {player.name} fails the Relentless Rage save and goes down.")
        player.relentless_rage_dc = dc + 5
        return False


_RANGED_KEYWORDS = {
    "bow", "crossbow", "dart", "sling", "javelin", "spear",
    "net", "spit", "breath", "ray", "bolt",
}


def _ranged_actions(monster) -> list[dict]:
    """Monster actions that are ranged — either via an explicit ``range`` key
    greater than 5 ft, or whose name contains a known ranged-weapon keyword."""
    result = []
    for a in monster.actions:
        if a.get("range", 0) > 5:
            result.append(a)
        elif any(kw in a.get("name", "").lower() for kw in _RANGED_KEYWORDS):
            result.append(a)
    return result


def _melee_actions(monster) -> list[dict]:
    return [a for a in monster.actions if a.get("range", 0) <= 5]


def _best_action(actions: list[dict]) -> dict | None:
    """Pick the action with the highest average damage."""
    if not actions:
        return None

    def avg_dmg(a: dict) -> float:
        try:
            n, d = (int(x) for x in a.get("damage", "1d1").split("d"))
            return n * (d + 1) / 2.0 + a.get("damage_bonus", 0)
        except (ValueError, AttributeError):
            return 0.0

    return max(actions, key=avg_dmg)


def _has_ranged_weapon(player) -> bool:
    """True if the player has a Ranged or Thrown weapon equipped."""
    for item in player.equipped_items:
        if item.type == "Weapon":
            if item.melee_or_ranged == "Ranged":
                return True
            if "Thrown" in getattr(item, "properties", []):
                return True
    return False


# ── Combat ────────────────────────────────────────────────────────────────────

class Combat:
    """Manages one combat encounter on a Map.

    Parameters
    ----------
    map_ : Map
        The map on which the encounter takes place. All combatants must be
        placed on it before ``run()`` is called.
    players : list
        Player-controlled :class:`~src.creatures.Character` instances.
    monsters : list
        AI-controlled :class:`~src.creatures.monsters.Monster` instances.
    """

    MELEE_REACH = 5   # feet — standard melee reach

    def __init__(self, map_, players: list, monsters: list):
        self.map = map_
        self.players = list(players)
        self.monsters = list(monsters)
        self._order: list = []

    # ── Internal state checks ─────────────────────────────────────────────────

    def _alive_players(self) -> list:
        return [p for p in self.players if not _is_dead(p) and p.position]

    def _alive_monsters(self) -> list:
        return [m for m in self.monsters if not _is_dead(m) and m.position]

    # ── Initiative ────────────────────────────────────────────────────────────

    def _roll_initiative(self):
        print("\nRolling initiative...")
        rolls: list[tuple[float, object]] = []

        for p in self.players:
            dex = p.get_ability_bonus("Dexterity")
            _, total, _, _ = p.roll_check(
                None, beat=None, bonus=dex, check_type="Initiative"
            )
            rolls.append((total + dex * 0.001, p))

        for m in self.monsters:
            dex = m.get_ability_bonus("Dexterity")
            raw = roll_dice(1, 20) + dex
            print(f"  {m.name} rolls initiative: {raw}")
            rolls.append((raw + dex * 0.001, m))

        rolls.sort(key=lambda t: t[0], reverse=True)
        self._order = [creature for _, creature in rolls]
        for i, creature in enumerate(self._order, start=1):
            # Add numbers as prefix to names for easier reference during combat
            creature.name = f"{i}. {creature.name}"

        print("\nInitiative order:")
        for i, c in enumerate(self._order, 1):
            side = "Player" if c in self.players else "Monster"
            print(f"  {i}. {c.name}  ({side})")

    # ── Display ───────────────────────────────────────────────────────────────

    def _print_status(self):
        print()
        print(self.map.render())
        print()
        print("COMBATANTS")
        print("-" * 48)
        for c in self._order:
            if _is_dead(c):
                status = " [DEAD]"
            elif _is_incapacitated(c):
                status = " [DOWN]"
            else:
                conditions = [getattr(e, "name", str(e)) for e in c.active_effects]
                status = f"  [{', '.join(conditions)}]" if conditions else ""
            side = "P" if c in self.players else "M"
            pos = c.position or "—"
            print(f"  [{side}] {c.name:<18} {_hp_bar(c)}  @{pos}{status}")
        print("-" * 48)

    def _print_nearby_enemies(self, actor):
        enemies = self._alive_monsters() if actor in self.players else self._alive_players()
        if not enemies:
            return
        print("  Enemies:")
        for e in enemies:
            try:
                dist = self.map.distance_ft(actor, e)
            except ValueError:
                dist = -1
            in_range = " <-- in melee range" if 0 < dist <= self.MELEE_REACH else ""
            print(f"    {e.name:<18} {_hp_bar(e)}  {dist} ft{in_range}")

    # ── Monster attack (tracks damage for rage-end check) ─────────────────────

    def _monster_attack(self, monster, target, action_name=None):
        """Execute a monster attack and flag the target if damage was dealt."""
        prev_hp = target.current_hp
        monster.attack(target, action_name=action_name, lethal=True)
        if target.current_hp < prev_hp:
            target._took_damage_this_turn = True
        # Relentless Rage: intercept a killing blow while raging
        if target.current_hp <= 0:
            _check_relentless_rage(target)

    # ── Monster AI ────────────────────────────────────────────────────────────

    def _monster_turn(self, monster):
        print(f"\n  {monster.name}'s turn  {_hp_bar(monster)}")

        targets = self._alive_players()
        if not targets:
            return

        target = min(targets, key=lambda p: self.map.distance_ft(monster, p))
        dist = self.map.distance_ft(monster, target)

        ranged = _ranged_actions(monster)
        melee = _melee_actions(monster)

        if ranged and (_best_action(ranged) or not melee):
            self._monster_ranged_ai(monster, target, ranged, melee, dist)
        else:
            self._monster_melee_ai(monster, target, melee or ranged, dist)

    def _approach_cell(self, mover, target) -> tuple | None:
        """Return the free cell adjacent to *target* that is closest to *mover*.

        Used so monsters aim for an open cell beside a player rather than the
        player's own (now-blocked) cell.  Returns None if no adjacent free cell
        exists on the map.
        """
        tx, ty, tz = target.position
        candidates = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = tx + dx, ty + dy
                if not self.map._in_bounds(nx, ny):
                    continue
                if not self.map.is_passable(nx, ny, tz):
                    continue
                # Cell must be empty or already occupied only by the mover
                occupants = self.map.get_creatures_at(nx, ny, tz)
                if any(c is not mover for c in occupants):
                    continue
                dist_to_candidate = self.map.distance_ft(mover, (nx, ny, tz))
                candidates.append((dist_to_candidate, nx, ny, tz))
        if not candidates:
            return None
        candidates.sort()
        _, nx, ny, nz = candidates[0]
        return (nx, ny, nz)

    def _monster_melee_ai(self, monster, target, actions, dist):
        # Move toward target if not adjacent
        if dist > self.MELEE_REACH:
            cell = self._approach_cell(monster, target)
            if cell is not None:
                gx, gy, gz = cell
                result = monster.move(self.map, gx, gy, gz,
                                      blocked_creatures=self._alive_players())
                dist = self.map.distance_ft(monster, target)
                if result["movement_used"]:
                    print(f"    {monster.name} moves toward {target.name} "
                          f"({result['movement_used']} ft used, now {dist} ft away).")

        # Attack if now adjacent
        if dist <= self.MELEE_REACH and monster.actions_left + monster.attack_actions_left > 0:
            if monster.actions_left > 0:
                monster.actions_left -= 1
                monster.attack_actions_left += getattr(monster, "extra_attacks", 0)
            else:
                monster.attack_actions_left -= 1
            action = _best_action(actions)
            self._monster_attack(monster, target, action["name"] if action else None)

    def _monster_ranged_ai(self, monster, target, ranged, melee, dist):
        best = _best_action(ranged)
        max_range = best.get("range", 60) if best else 60

        # If in melee range and no melee fallback preferred, try to back away
        if dist <= self.MELEE_REACH:
            mx, my, mz = monster.position
            tx, ty, _ = target.position
            dx = int(math.copysign(1, mx - tx)) if mx != tx else 0
            dy = int(math.copysign(1, my - ty)) if my != ty else 0
            for steps in range(3, 0, -1):
                gx = mx + dx * steps
                gy = my + dy * steps
                if self.map._in_bounds(gx, gy) and self.map.is_passable(gx, gy, mz):
                    result = monster.move(self.map, gx, gy, mz,
                                         blocked_creatures=self._alive_players())
                    if result["movement_used"]:
                        dist = self.map.distance_ft(monster, target)
                        print(f"    {monster.name} backs away "
                              f"({result['movement_used']} ft, now {dist} ft from {target.name}).")
                    break

        # Shoot if in range
        if dist <= max_range and monster.actions_left > 0 + monster.attack_actions_left > 0:
            if monster.actions_left > 0:
                monster.actions_left -= 1
                monster.attack_actions_left += getattr(monster, "extra_attacks", 0)
            else:
                monster.attack_actions_left -= 1
            self._monster_attack(monster, target, best["name"] if best else None)
        elif monster.actions_left > 0:
            # Too far — close the gap
            cell = self._approach_cell(monster, target)
            if cell is not None:
                gx, gy, gz = cell
                result = monster.move(self.map, gx, gy, gz,
                                      blocked_creatures=self._alive_players())
                dist = self.map.distance_ft(monster, target)
                if result["movement_used"]:
                    print(f"    {monster.name} advances ({result['movement_used']} ft, "
                          f"now {dist} ft from {target.name}).")
            # Melee fallback if now adjacent
            if dist <= self.MELEE_REACH and melee and monster.actions_left > 0:
                monster.actions_left -= 1
                action = _best_action(melee)
                self._monster_attack(monster, target, action["name"] if action else None)

    # ── Player turn helpers ───────────────────────────────────────────────────

    def _cmd_move(self, player, parts: list, movement_remaining_ft: int) -> tuple[Character, int]:
        """Handle the ``move`` command. Returns new movement_remaining_ft."""
        if movement_remaining_ft <= 0:
            print("  No movement remaining this turn.")
            return player, movement_remaining_ft
        if len(parts) < 3:
            # go to space near target creature if specified, otherwise give usage message
            if len(parts) == 2:
                target_name = parts[1]
                targets = self._alive_monsters() if player in self.players else self._alive_players()
                target = self._resolve_target(target_name, targets)
                if target is None:
                    return player, movement_remaining_ft
                tx, ty, tz = target.position
                # Move to an adjacent cell if possible
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        if dx == 0 and dy == 0:
                            continue
                        gx, gy, gz = tx + dx, ty + dy, tz
                        if self.map._in_bounds(gx, gy) and self.map.is_passable(gx, gy, gz):
                            result = player.move(self.map, gx, gy, gz, budget=movement_remaining_ft,
                                             blocked_creatures=self._alive_monsters())
                            if result["movement_used"]:
                                print(f"  Moved adjacent to {target.name} at {result['reached']}. "
                                      f"{result['movement_used']} ft used, "
                                      f"{movement_remaining_ft - result['movement_used']} ft remaining.")
                                movement_remaining_ft -= result["movement_used"]
                                self._print_nearby_enemies(player)
                            else:
                                print(f"  No path to get adjacent to {target.name}.")
                            return player, movement_remaining_ft
                print(f"  No passable adjacent cell near {target.name}.")
            print("  Usage: move <x> <y> [z] OR move <target_name>")
            return player, movement_remaining_ft
        try:
            x, y = int(parts[1]), int(parts[2])
            z = int(parts[3]) if len(parts) > 3 else 0
        except ValueError:
            print("  Coordinates must be integers.")
            return player, movement_remaining_ft
        result = player.move(self.map, x, y, z, budget=movement_remaining_ft,
                             blocked_creatures=self._alive_monsters())
        if result["blocked"]:
            coord = f"({x}, {y}{f', {z}' if z else ''})"
            print(f"  No path to {coord}.")
        else:
            movement_remaining_ft -= result["movement_used"]
            print(f"  Moved to {result['reached']}. "
                  f"{result['movement_used']} ft used, "
                  f"{movement_remaining_ft} ft remaining.")
            self._print_nearby_enemies(player)
        return player, movement_remaining_ft

    def _cmd_dash(self, player, movement_remaining_ft: int) -> tuple[Character, int]:
        """Handle the ``dash`` command. Returns (actions_remaining, movement_remaining_ft)."""
        actions_remaining = getattr(player, "actions_left", 0)
        if actions_remaining <= 0:
            print("  No action left to dash.")
            return player, movement_remaining_ft
        player.dash()
        actions_remaining -= 1
        movement_remaining_ft += player.bonus_speed
        print(f"  {player.name} dashes! +{player.bonus_speed} ft "
              f"({movement_remaining_ft} ft remaining).")
        return player, movement_remaining_ft

    def _cmd_attack(self, player, parts: list) -> Character:
        """Handle the ``attack`` command. Returns new actions_remaining."""
        alive_enemies = self._alive_monsters()
        if not alive_enemies:
            print("  No enemies to attack.")
            return player

        # Parse optional target, weapon, and lethal flag
        target_name = None
        weapon_name = None
        lethal = True
        for part in parts[1:]:
            if part in [w.name for w in player.equipped_items if w.type == "Weapon"]:
                weapon_name = part
            elif part.lower() in ("lethal=false", "lethal=no", "nonlethal", "non-lethal"):
                lethal = False
            elif part.lower() in ("lethal=true", "lethal=yes", "true", "yes"):
                lethal = True
            else:
                target_name = part

        target = self._resolve_target(target_name, alive_enemies)
        if target is None:
            return player

        dist = self.map.distance_ft(player, target)
        if not _has_ranged_weapon(player) and dist > self.MELEE_REACH:
            print(f"  {target.name} is {dist} ft away — out of melee reach "
                  f"({self.MELEE_REACH} ft). Move closer or equip a ranged weapon.")
            return player
        # TODO: Check for specific weapon range if weapon_name given or if player has a single equipped weapon with a range.

        if player.actions_left + player.attack_actions_left > 0:
            if player.actions_left > 0:
                player.actions_left -= 1
                if player.attack_actions_left == 0:
                    # Once per turn when taking an Attack action, add any extra attacks from class features (e.g. Extra Attack)
                    player.attack_actions_left += getattr(player, "extra_attacks", 0)
            else:
                player.attack_actions_left -= 1
            # Attempting an attack (hit or miss) counts for Rage
            player._attacked_this_turn = True
            player.attack(target, weapon_name=weapon_name, lethal=lethal)
        else:
            print("No attack actions remaining.")
        return player

    def _cmd_cast(self, player, parts: list) -> Character:
        """Handle the ``cast`` command. Returns (player)."""
        spells = getattr(player, "spells", [])
        if len(parts) < 2:
            self._list_spells(player)
            return player

        spell_name = parts[1]
        target_name = parts[2] if len(parts) > 2 else None

        spell = next(
            (s for s in spells if spell_name.lower() in s.name.lower()), None
        )
        if spell is None:
            avail = [s.name for s in spells if s.uses_left is None or s.uses_left > 0]
            print(f"  Spell '{spell_name}' not found. Available: {avail}")
            return player
        if spell.uses_left == 0:
            print(f"  {spell.name} has no uses remaining.")
            return player

        is_free = getattr(spell, "casting_time", "Action") == "Free Action"
        is_bonus = getattr(spell, "casting_time", "Action") == "Bonus Action"

        if is_free:
            pass
        elif is_bonus and player.bonus_actions_left <= 0:
            print("  No bonus action remaining to cast this spell.")
            return player
        elif not is_bonus and player.actions_left <= 0:
            print("  No action remaining to cast this spell.")
            return player

        targets, ok = self._resolve_cast_targets(player, target_name)
        if not ok:
            return player
        # Casting at an enemy counts as forcing a saving throw for Rage purposes
        if any(t in self._alive_monsters() for t in targets):
            player._forced_save_this_turn = True

        # TODO: Check for spell range if target is not self and spell has a range component (Touch = melee)

        print(f"  {player.name} casts {spell.name}!")
        player.cast_spell(spell.name, targets=targets)

        if is_free:
            pass
        elif is_bonus:
            player.bonus_actions_left -= 1
        else:
            player.actions_left -= 1
        return player

    def _cmd_ability(self, player, parts: list) -> Character:
        """Handle the ``ability`` command. Returns (player)."""
        abilities = getattr(player, "special_abilities", [])
        if len(parts) < 2:
            self._list_abilities(player)
            return player

        ability_name = parts[1]
        target_name = parts[2] if len(parts) > 2 else None

        ability = next(
            (a for a in abilities if ability_name.lower() in a.name.lower()), None
        )
        if ability is None:
            avail = [a.name for a in abilities if a.uses_left is None or a.uses_left > 0]
            print(f"  Ability '{ability_name}' not found. Available: {avail}")
            return player
        if ability.uses_left == 0:
            print(f"  {ability.name} has no uses remaining.")
            return player

        is_free = getattr(ability, "casting_time", "Action") == "Free Action"
        is_bonus = getattr(ability, "casting_time", "Action") == "Bonus Action"

        if is_free:
            pass
        elif is_bonus and player.bonus_actions_left <= 0:
            print("  No bonus action remaining to use this ability.")
            return player
        elif not is_bonus and player.actions_left <= 0:
            print("  No action remaining to use this ability.")
            return player

        targets, ok = self._resolve_cast_targets(player, target_name)
        if not ok:
            return player
        if any(t in self._alive_monsters() for t in targets):
            player._forced_save_this_turn = True

        print(f"  {player.name} uses {ability.name}!")
        # TODO: Check range on abilities if they have a range component
        player.use_special_ability(ability.name, targets=targets)

        if is_free:
            pass
        elif is_bonus:
            player.bonus_actions_left -= 1
        else:
            player.actions_left -= 1
        return player

    def _resolve_cast_targets(self, player, target_name) -> tuple[list, bool]:
        """Return (targets list, success bool). Defaults to self if no target given."""
        if not target_name or target_name.lower() in ("self", "me"):
            return [player], True
        target = self._resolve_target(target_name, self._alive_monsters())
        if target is None:
            return [], False
        return [target], True

    def _list_spells(self, player):
        spells = getattr(player, "spells", [])
        # check for prepared spells
        spells += [s for s in getattr(player, "prepared_spells", []) if s not in spells]
        if not spells:
            print("  No spells known.")
            return
        print("  Spells:")
        for s in spells:
            uses = "∞" if s.uses_left is None else s.uses_left
            ct = getattr(s, "casting_time", "Action")
            print(f"    {s.name:<25} ({ct}, uses left: {uses})")

    def _list_abilities(self, player):
        abilities = getattr(player, "special_abilities", [])
        if not abilities:
            print("  No special abilities.")
            return
        print("  Special Abilities:")
        for a in abilities:
            uses = "∞" if a.uses_left is None else a.uses_left
            ct = getattr(a, "casting_time", "Action")
            print(f"    {a.name:<25} ({ct}, uses left: {uses})")

    def _resolve_target(self, target_name, alive_enemies: list):
        """Resolve a partial name to an enemy, or return None with an error message."""
        if target_name:
            for m in alive_enemies:
                if m.name.lower().startswith(target_name.lower()):
                    return m
                elif target_name.lower() in m.name.lower():
                    return m
            print(f"  No enemy matching '{target_name}'. "
                  f"Options: {[m.name for m in alive_enemies]}")
            return None
        if len(alive_enemies) == 1:
            return alive_enemies[0]
        print(f"  Multiple enemies — specify one: {[m.name for m in alive_enemies]}")
        return None

    # ── Player turn (interactive) ─────────────────────────────────────────────

    def _player_turn(self, player):
        print(f"\n  {player.name}'s turn  {_hp_bar(player)}")
        active = [getattr(e, "name", str(e)) for e in player.active_effects]
        if active:
            print(f"  Active conditions: {', '.join(active)}")
        self._print_nearby_enemies(player)

        movement_remaining_ft = max(player.speed, player.flying_speed)
        player.actions_left = 1
        player.attack_actions_left = 0
        player.bonus_actions_left = 1
        player.reaction_available = True

        has_spells = bool(getattr(player, "spells", []))
        has_abilities = bool(getattr(player, "special_abilities", []))

        while True:
            alive_enemies = self._alive_monsters()
            opts = []
            if movement_remaining_ft > 0:
                opts.append("move <x> <y> [z] OR move <target_name>")
            if player.actions_left > 0:
                if alive_enemies:
                    opts.append("attack [name] [weapon] [lethal=True]")
                opts.append("dash")
                if has_spells:
                    opts.append("cast <spell> [target]")
            elif player.attack_actions_left > 0:
                if alive_enemies:
                    opts.append("attack [name] [weapon] [lethal=True]")
            if has_abilities:
                opts.append("ability <name> [target]")
            if has_spells:
                opts.append("spells")
            if has_abilities:
                opts.append("abilities")
            opts.append("pass")

            print(f"\n  [{player.name}] {_hp_bar(player)}"
                  f"  actions={player.actions_left}"
                  f"  bonus={player.bonus_actions_left}"
                  f"  movement={movement_remaining_ft}ft")
            print(f"  Commands: {' | '.join(opts)}")

            raw = input("  > ").strip()
            if not raw:
                continue

            parts = shlex.split(raw)
            cmd = parts[0].lower()

            if cmd in ("pass", "skip", "end", "done"):
                break
            elif cmd == "move":
                player, movement_remaining_ft = self._cmd_move(player, parts, movement_remaining_ft)
            elif cmd == "dash":
                player, movement_remaining_ft = self._cmd_dash(player, movement_remaining_ft)
            elif cmd == "attack":
                player = self._cmd_attack(player, parts)
            elif cmd == "cast":
                player = self._cmd_cast(player, parts)
            elif cmd == "ability":
                player = self._cmd_ability(player, parts)
            elif cmd in ("spells", "spell"):
                self._list_spells(player)
            elif cmd in ("abilities",):
                self._list_abilities(player)
            else:
                print(f"  Unknown command: '{cmd}'  — try: {' | '.join(opts)}")

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self) -> str:
        """Run the encounter until one side is eliminated.

        Returns ``"players"`` if the players win or ``"monsters"`` if the
        monsters win.
        """
        print("\n" + "=" * 50)
        print("  COMBAT BEGINS")
        print("=" * 50)

        self._roll_initiative()

        round_num = 0
        winner = None
        while not winner:
            round_num += 1
            print(f"\n{'=' * 50}")
            print(f"  ROUND {round_num}")
            self._print_status()

            for combatant in list(self._order):
                if _is_incapacitated(combatant):
                    # Still tick conditions for incapacitated creatures
                    expired = _tick_conditions(combatant)
                    for name in expired:
                        print(f"  {combatant.name}'s {name} expires.")
                    continue

                _reset_turn(combatant)
                # Tick timed conditions that expire at the start of the turn (e.g. Reckless Attack)
                expired = _tick_conditions(combatant, start_of_turn=True)
                # Zone entry/exit check at start of turn
                self.map.check_zone_transitions(combatant)
                if combatant in self.players:
                    self._player_turn(combatant)
                    # Rage end-condition check: must have acted this turn
                    _check_rage_end(combatant)
                else:
                    self._monster_turn(combatant)

                # Tick timed conditions at the end of each combatant's own turn
                expired = _tick_conditions(combatant)
                for name in expired:
                    print(f"  {combatant.name}'s {name} expires.")
                # Zone on_turn callbacks at end of turn
                for zone in self.map.get_zones_containing(combatant):
                    if zone.on_turn:
                        zone.on_turn(combatant)

                # Check for end-of-combat after every turn
                if not self._alive_players():
                    self._print_status()
                    print("\nAll players have fallen. The monsters win.")
                    winner = "monsters"
                    break

                if not self._alive_monsters():
                    self._print_status()
                    print("\nAll monsters defeated. The players win!")
                    winner = "players"
                    break
        # Clean up names by removing initiative prefixes
        for c in self._order:
            c.name = re.sub(r"^\d+\.\s*", "", c.name)
        return winner