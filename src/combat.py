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
  move <x> <y> [z]     Move toward grid cell (x, y) or (x, y, z).
                        Uses A* pathfinding; stops at the farthest cell
                        reachable within this turn's movement budget.
  attack [name] [wpn]  Attack a named enemy (partial match) with an optional
                        weapon name. Defaults to the nearest enemy and the
                        equipped/unarmed weapon.
  dash                  Use your action to gain a second move this turn.
  pass                  End your turn immediately.
"""

from __future__ import annotations

import math

from src.common import roll_dice


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
    """Restore per-turn action and speed resources."""
    creature.actions_left = 1
    if hasattr(creature, "bonus_actions_left"):
        creature.bonus_actions_left = 1
    creature.bonus_speed = 0


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
    lethal : bool
        When True (default), creatures reduced to 0 HP gain the Dead
        condition. When False they become Unconscious instead.
    """

    MELEE_REACH = 5   # feet — standard melee reach

    def __init__(self, map_, players: list, monsters: list, lethal: bool = True):
        self.map = map_
        self.players = list(players)
        self.monsters = list(monsters)
        self.lethal = lethal
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
                status = ""
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

    def _monster_melee_ai(self, monster, target, actions, dist):
        # Move toward target if not adjacent
        if dist > self.MELEE_REACH:
            tx, ty, tz = target.position
            result = monster.move(self.map, tx, ty, tz)
            dist = self.map.distance_ft(monster, target)
            if result["movement_used"]:
                print(f"    {monster.name} moves toward {target.name} "
                      f"({result['movement_used']} ft used, now {dist} ft away).")

        # Attack if now adjacent
        if dist <= self.MELEE_REACH and monster.actions_left > 0:
            monster.actions_left -= 1
            action = _best_action(actions)
            monster.attack(target, action_name=action["name"] if action else None,
                           lethal=self.lethal)

    def _monster_ranged_ai(self, monster, target, ranged, melee, dist):
        best = _best_action(ranged)
        max_range = best.get("range", 60) if best else 60

        # If in melee range and no melee fallback preferred, try to back away
        if dist <= self.MELEE_REACH:
            mx, my, mz = monster.position
            tx, ty, tz = target.position
            # Step in opposite direction, a few cells at a time, pick first valid far cell
            dx = int(math.copysign(1, mx - tx)) if mx != tx else 0
            dy = int(math.copysign(1, my - ty)) if my != ty else 0
            for steps in range(3, 0, -1):
                gx = mx + dx * steps
                gy = my + dy * steps
                if self.map._in_bounds(gx, gy) and self.map.is_passable(gx, gy, mz):
                    result = monster.move(self.map, gx, gy, mz)
                    if result["movement_used"]:
                        dist = self.map.distance_ft(monster, target)
                        print(f"    {monster.name} backs away "
                              f"({result['movement_used']} ft, now {dist} ft from {target.name}).")
                    break

        # Shoot if in range
        if dist <= max_range and monster.actions_left > 0:
            monster.actions_left -= 1
            monster.attack(target, action_name=best["name"] if best else None,
                           lethal=self.lethal)
        elif monster.actions_left > 0:
            # Too far — close the gap
            tx, ty, tz = target.position
            result = monster.move(self.map, tx, ty, tz)
            dist = self.map.distance_ft(monster, target)
            if result["movement_used"]:
                print(f"    {monster.name} advances ({result['movement_used']} ft, "
                      f"now {dist} ft from {target.name}).")
            # Attack with melee if now adjacent and has a melee option
            if dist <= self.MELEE_REACH and melee and monster.actions_left > 0:
                monster.actions_left -= 1
                action = _best_action(melee)
                monster.attack(target, action_name=action["name"] if action else None,
                               lethal=self.lethal)

    # ── Player turn helpers ───────────────────────────────────────────────────

    def _cmd_move(self, player, parts: list, moves_remaining: int) -> int:
        """Handle the ``move`` command. Returns new moves_remaining."""
        if moves_remaining <= 0:
            print("  No movement remaining this turn.")
            return moves_remaining
        if len(parts) < 3:
            print("  Usage: move <x> <y> [z]")
            return moves_remaining
        try:
            x, y = int(parts[1]), int(parts[2])
            z = int(parts[3]) if len(parts) > 3 else 0
        except ValueError:
            print("  Coordinates must be integers.")
            return moves_remaining
        result = player.move(self.map, x, y, z)
        if result["blocked"]:
            coord = f"({x}, {y}{f', {z}' if z else ''})"
            print(f"  No path to {coord}.")
        else:
            moves_remaining -= 1
            print(f"  Moved to {result['reached']}. "
                  f"{result['movement_used']} ft used, "
                  f"{result['movement_remaining']} ft remaining in pool.")
            self._print_nearby_enemies(player)
        return moves_remaining

    def _cmd_dash(self, player, actions_remaining: int, moves_remaining: int) -> tuple:
        """Handle the ``dash`` command. Returns (actions_remaining, moves_remaining)."""
        if actions_remaining <= 0:
            print("  No action left to dash.")
            return actions_remaining, moves_remaining
        if moves_remaining != 1:
            print("  Dash is only available before your first move or after moving once.")
            return actions_remaining, moves_remaining
        player.dash()
        actions_remaining -= 1
        moves_remaining += 1
        print(f"  {player.name} dashes! +{player.bonus_speed} ft added to movement pool.")
        return actions_remaining, moves_remaining

    def _cmd_attack(self, player, parts: list, actions_remaining: int) -> int:
        """Handle the ``attack`` command. Returns new actions_remaining."""
        alive_enemies = self._alive_monsters()
        if actions_remaining <= 0:
            print("  No action left to attack.")
            return actions_remaining
        if not alive_enemies:
            print("  No enemies to attack.")
            return actions_remaining

        target_name = parts[1] if len(parts) > 1 else None
        weapon_name = parts[2] if len(parts) > 2 else None

        target = self._resolve_target(target_name, alive_enemies)
        if target is None:
            return actions_remaining

        dist = self.map.distance_ft(player, target)
        if not _has_ranged_weapon(player) and dist > self.MELEE_REACH:
            print(f"  {target.name} is {dist} ft away — out of melee reach "
                  f"({self.MELEE_REACH} ft). Move closer or equip a ranged weapon.")
            return actions_remaining

        actions_remaining -= 1
        player.actions_left = actions_remaining
        player.attack(target, weapon_name=weapon_name, lethal=self.lethal)
        return actions_remaining

    def _resolve_target(self, target_name, alive_enemies: list):
        """Resolve a partial name to an enemy, or return None with an error message."""
        if target_name:
            for m in alive_enemies:
                if m.name.lower().startswith(target_name.lower()):
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
        self._print_nearby_enemies(player)

        moves_remaining = 1    # becomes 2 after Dash
        actions_remaining = 1  # attack or dash consumes this

        while True:
            alive_enemies = self._alive_monsters()
            opts = []
            if moves_remaining > 0:
                opts.append("move <x> <y> [z]")
            if actions_remaining > 0:
                if alive_enemies:
                    opts.append("attack [name] [weapon]")
                if moves_remaining == 1:
                    opts.append("dash")
            opts.append("pass")

            print(f"\n  [{player.name}] {_hp_bar(player)}"
                  f"  actions={actions_remaining} moves={moves_remaining}")
            print(f"  Commands: {' | '.join(opts)}")

            raw = input("  > ").strip()
            if not raw:
                continue

            parts = raw.split()
            cmd = parts[0].lower()

            if cmd in ("pass", "skip", "end", "done"):
                break
            if cmd == "move":
                moves_remaining = self._cmd_move(player, parts, moves_remaining)
            elif cmd == "dash":
                actions_remaining, moves_remaining = self._cmd_dash(
                    player, actions_remaining, moves_remaining
                )
            elif cmd == "attack":
                actions_remaining = self._cmd_attack(player, parts, actions_remaining)
            else:
                print(f"  Unknown command: '{cmd}'  — try: {' | '.join(opts)}")

            if actions_remaining <= 0 and moves_remaining <= 0:
                break

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
        while True:
            round_num += 1
            print(f"\n{'='*50}")
            print(f"  ROUND {round_num}")
            self._print_status()

            for combatant in self._order:
                if _is_incapacitated(combatant):
                    continue

                _reset_turn(combatant)

                if combatant in self.players:
                    self._player_turn(combatant)
                else:
                    self._monster_turn(combatant)

                # Check for end-of-combat after every turn
                if not self._alive_players():
                    self._print_status()
                    print("\nAll players have fallen. The monsters win.")
                    return "monsters"

                if not self._alive_monsters():
                    self._print_status()
                    print("\nAll monsters defeated. The players win!")
                    return "players"
