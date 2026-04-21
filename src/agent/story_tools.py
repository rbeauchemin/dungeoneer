"""Story / Dungeon-Master tools and agent.

The story agent narrates exploration, resolves skill challenges, and triggers
combat encounters.  When it calls start_combat(), the campaign loop detects the
active_combat flag and switches to the combat sub-loop automatically.
"""

from __future__ import annotations

import json
import random
from typing import Union

from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from src.agent.campaign import _campaign
from src.creatures.character import Character

# Monsters available for random encounters (subset with friendly names)
_MONSTER_REGISTRY: dict[str, str] = {
    "Goblin": "Goblin",
    "Skeleton": "Skeleton",
    "Orc": "Orc",
    "Zombie": "Zombie",
    "Wolf": "Wolf",
    "Giant Spider": "GiantSpider",
    "Bandit": "Bandit",
    "Troll": "Troll",
    "Vampire Spawn": "VampireSpawn",
    "Animated Armor": "AnimatedArmor",
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_player(name: str) -> Character:
    """Case-insensitive partial name search over campaign players."""
    for p in _campaign.players:
        if name.lower() in p.name.lower():
            return p
    return None


# ── Tools ──────────────────────────────────────────────────────────────────────

@tool
def get_campaign_state() -> str:
    """Return the current scene and status of all player characters."""
    from src.combat import _is_dead, _is_incapacitated

    lines = [f"Scene: {_campaign.current_scene}\n"]
    for p in _campaign.players:
        conds = [getattr(e, "name", str(e)) for e in p.active_effects]
        cond_str = f"  [{', '.join(conds)}]" if conds else ""
        status = "DEAD" if _is_dead(p) else ("DOWN" if _is_incapacitated(p) else "OK")
        lines.append(f"  {p.name}: {p.current_hp}/{p.max_hp} HP  [{status}]{cond_str}")

    if _campaign.last_combat_result:
        lines.append(f"\nLast combat: {_campaign.last_combat_result}")

    return "\n".join(lines)


@tool
def set_scene(description: str) -> str:
    """Update the current scene description (called when players move to a new area)."""
    _campaign.current_scene = description
    _campaign.story_log.append(f"[SCENE] {description}")
    return f"Scene updated: {description}"


@tool
def roll_skill_check(player_name: str, skill: str, dc: int) -> str:
    """Roll a skill check for a player character against a difficulty class (DC).
    skill: one of the standard D&D skills (e.g. 'Perception', 'Stealth', 'Athletics').
    dc: 5=very easy, 10=easy, 15=medium, 20=hard, 25=very hard."""
    player = _get_player(player_name)
    if player is None:
        names = [p.name for p in _campaign.players]
        return f"No player matching '{player_name}'. Available: {names}"

    success, total, crit_fail, crit_success, modifier = player.roll_check(skill, check_type="Skills", beat=dc)

    mod_str = f"+{modifier}" if modifier >= 0 else str(modifier)
    outcome = "SUCCESS" if success else "FAILURE"
    if any([crit_fail, crit_success]):
        outcome += " (CRITICAL)"

    result = (
        f"{player.name} — {skill} check:\n"
        f"  d20{mod_str} = {total} vs DC {dc} → {outcome}"
    )
    _campaign.story_log.append(result)
    return result


@tool
def roll_ability_check(player_name: str, ability: str, dc: int) -> str:
    """Roll a raw ability check (Strength, Dexterity, etc.) for a player.
    Use for checks that don't map to a named skill (e.g. raw Strength to lift a gate).
    ability: Strength, Dexterity, Constitution, Intelligence, Wisdom, or Charisma.
    dc: 5=very easy, 10=easy, 15=medium, 20=hard, 25=very hard."""
    player = _get_player(player_name)
    if player is None:
        return f"No player matching '{player_name}'."

    ability = ability.capitalize()
    success, total, crit_fail, crit_success, modifier = player.roll_check(ability, check_type="Abilities", beat=dc)

    mod_str = f"+{modifier}" if modifier >= 0 else str(modifier)
    outcome = "SUCCESS" if success else "FAILURE"
    if any([crit_fail, crit_success]):
        outcome += " (CRITICAL)"

    result = (
        f"{player.name} — {ability} check:\n"
        f"  d20{mod_str} = {total} vs DC {dc} → {outcome}"
    )
    _campaign.story_log.append(result)
    return result


@tool
def roll_saving_throw(player_name: str, ability: str, dc: int) -> str:
    """Roll a saving throw for a player against a DC.
    Adds proficiency bonus if the character is proficient in that saving throw.
    ability: Strength, Dexterity, Constitution, Intelligence, Wisdom, or Charisma.
    dc: 5=very easy, 10=easy, 15=medium, 20=hard, 25=very hard.
    Use when a player faces: traps, spells, environmental hazards, poison, fear, etc."""
    player = _get_player(player_name)
    if player is None:
        return f"No player matching '{player_name}'."

    ability = ability.capitalize()
    success, total, crit_fail, crit_success, modifier = player.roll_check(ability, check_type="Saving Throws", beat=dc)
    mod_str = f"+{modifier}" if modifier >= 0 else str(modifier)
    outcome = "SUCCESS" if success else "FAILURE"
    if any([crit_fail, crit_success]):
        outcome += " (CRITICAL)"

    result = (
        f"{player.name} — {ability} saving throw:\n"
        f"  d20{mod_str} = {total} vs DC {dc} → {outcome}"
    )
    _campaign.story_log.append(result)
    return result


@tool
def list_available_monsters() -> str:
    """List the monster types available for combat encounters."""
    return "Available monsters:\n" + "\n".join(f"  - {name}" for name in _MONSTER_REGISTRY)


@tool
def start_combat(setting: str, monster_specs: Union[str, list], map_layout: Union[str, list] = "[]") -> str:
    """Begin a combat encounter.

    setting: a brief description of the combat location (used as map name).
    monster_specs: stringified JSON array of objects with 'type' and 'count' fields.
      Example: '[{\"type\": \"Goblin\", \"count\": 3}]'
      Use list_available_monsters() to see valid type names.
    map_layout: optional stringified JSON array of terrain objects to place on the map.
      Each object: {\"type\": \"wall\"|\"rock\"|\"tree\"|\"door\", \"x\": int, \"y\": int}
      Map is 22 cells wide. Players spawn around x=3 (left), enemies around x=17 (right).
      Map height depends on combatant count (typically 10-20 cells).
      Use walls for barriers/corridors, rocks for cover, trees for outdoor terrain.
      Keep the center corridor clear so both sides can engage.
      Example dungeon corridor: walls along top/bottom rows with a gap in the middle.
      Example: '[{\"type\":\"wall\",\"x\":5,\"y\":0},{\"type\":\"rock\",\"x\":10,\"y\":5}]'
    """
    from src.map import Map, Wall, Rock, Tree, Door
    import src.creatures.monsters as monsters_module
    from src.combat import Combat
    from src.agent.session import GameSession

    specs = []
    layout_items = []

    if isinstance(monster_specs, str):
        try:
            specs: list[dict] = json.loads(monster_specs)
        except json.JSONDecodeError as exc:
            return f"Invalid monster_specs JSON: {exc}"
    elif isinstance(monster_specs, list):
        specs = monster_specs
    elif not isinstance(monster_specs, list):
        return "monster_specs must be a JSON string or a list of monster spec objects."

    if isinstance(map_layout, str):
        try:
            layout_items: list[dict] = json.loads(map_layout)
        except json.JSONDecodeError as exc:
            return f"Invalid map_layout JSON: {exc}"
    elif isinstance(map_layout, list):
        layout_items = map_layout
    elif not isinstance(map_layout, list):
        return "map_layout must be a JSON string or a list of terrain spec objects."

    alive_players = [
        p for p in _campaign.players
        if p.current_hp > 0
    ]
    if not alive_players:
        return "No living players to fight!"

    # Build a map sized to the encounter
    total_combatants = len(alive_players) + sum(s.get("count", 1) for s in specs)
    map_height = max(10, total_combatants * 2 + 4)
    dungeon_map = Map(22, map_height, name=setting[:30])

    # Place players on the left, spread vertically
    mid_y = map_height // 2
    for i, player in enumerate(alive_players):
        px = 3
        py = mid_y - (len(alive_players) - 1) + i * 2
        py = max(1, min(py, map_height - 2))
        dungeon_map.place_creature(player, px, py)

    # Instantiate and place monsters
    monster_list: list = []
    mx_base = 17
    monster_idx = 0
    errors: list[str] = []

    for spec in specs:
        type_name = spec.get("type", "")
        count = spec.get("count", 1)
        class_name = _MONSTER_REGISTRY.get(type_name)
        if class_name is None:
            errors.append(f"Unknown monster type '{type_name}'")
            continue

        monster_cls = getattr(monsters_module, class_name, None)
        if monster_cls is None:
            errors.append(f"Monster class '{class_name}' not found in monsters module")
            continue

        for j in range(count):
            m = monster_cls()
            if count > 1:
                m.name = f"{type_name} {j + 1}"
            mx = mx_base + (monster_idx % 2)
            my = mid_y - (count - 1) + monster_idx * 2
            my = max(1, min(my, map_height - 2))
            dungeon_map.place_creature(m, mx, my)
            monster_list.append(m)
            monster_idx += 1

    if not monster_list:
        msg = "No valid monsters could be created."
        if errors:
            msg += " Errors: " + "; ".join(errors)
        return msg

    # Place terrain objects from map_layout
    _OBJ_CLASSES = {"wall": Wall, "rock": Rock, "tree": Tree, "door": Door}
    for item in layout_items:
        obj_type = str(item.get("type", "")).lower()
        obj_cls = _OBJ_CLASSES.get(obj_type)
        if obj_cls is None:
            continue
        ox, oy = item.get("x", 0), item.get("y", 0)
        if dungeon_map._in_bounds(ox, oy):
            try:
                dungeon_map.place_object(obj_cls(x=ox, y=oy))
            except Exception:
                pass

    combat = Combat(dungeon_map, players=alive_players, monsters=monster_list)
    session = GameSession(combat)
    _campaign.active_combat = session
    _campaign.combat_setting = setting

    monster_summary = ", ".join(
        f"{s.get('count', 1)}x {s.get('type', '?')}" for s in specs
    )
    note = (" (Errors: " + "; ".join(errors) + ")") if errors else ""
    return (
        f"COMBAT_INITIATED — {setting}\n"
        f"Enemies: {monster_summary}{note}\n"
        f"The battle is about to begin!"
    )


@tool
def take_long_rest() -> str:
    """The party takes a long rest: restores all HP and resets spell slots/abilities."""
    from src.combat import _is_dead

    results: list[str] = []
    for p in _campaign.players:
        if _is_dead(p):
            continue
        old_hp = p.current_hp
        p.current_hp = p.max_hp

        # Reset spell slots if present
        if hasattr(p, "spell_slots"):
            if hasattr(p, "_max_spell_slots"):
                p.spell_slots = dict(p._max_spell_slots)
            elif isinstance(p.spell_slots, dict):
                p.spell_slots = {k: v for k, v in p.spell_slots.items()}

        # Reset ability uses
        for ability in getattr(p, "special_abilities", []):
            if hasattr(ability, "max_uses") and ability.max_uses is not None:
                ability.uses_left = ability.max_uses

        results.append(f"  {p.name}: {old_hp} → {p.max_hp} HP (fully restored)")

    _campaign.story_log.append("[LONG REST]")
    return "The party takes a long rest.\n" + "\n".join(results)


@tool
def take_short_rest() -> str:
    """The party takes a short rest: each player rolls their hit dice to recover HP."""
    from src.common import roll_dice
    from src.combat import _is_dead

    results: list[str] = []
    for p in _campaign.players:
        if _is_dead(p) or p.current_hp <= 0:
            continue
        hit_die = max(
            (c.hit_dice for c in p.classes),
            default=8,
        )
        roll = roll_dice(1, hit_die)
        con_mod = (p.ability_scores.get("Constitution", 10) - 10) // 2
        healed = max(1, roll + con_mod)
        old_hp = p.current_hp
        p.current_hp = min(p.max_hp, p.current_hp + healed)
        results.append(
            f"  {p.name}: rolled d{hit_die}({roll})+{con_mod} = {healed} HP  "
            f"({old_hp} → {p.current_hp})"
        )

    _campaign.story_log.append("[SHORT REST]")
    return "The party takes a short rest.\n" + "\n".join(results)


# ── Character inspection & action tools ────────────────────────────────────────

@tool
def get_character_sheet(player_name: str) -> str:
    """Return the full character sheet for a player: stats, AC, HP, proficiencies,
    equipped items, spells, and abilities."""
    player = _get_player(player_name)
    if player is None:
        return f"No player matching '{player_name}'. Available: {[p.name for p in _campaign.players]}"

    species_name = type(player.species).__name__
    bg_name = type(player.background).__name__
    classes_str = ", ".join(f"{c.name} {c.level}" for c in player.classes)
    scores = "  ".join(
        f"{k[:3]}: {v} ({(v-10)//2:+d})" for k, v in player.ability_scores.items()
    )

    equipped = [i.name for i in player.equipped_items] or ["nothing"]
    inv = [f"{i.name} x{i.quantity}" for i in player.inventory] or ["empty"]

    skills = player.proficiencies.get("Skills", [])
    saves = player.proficiencies.get("Saving Throws", [])

    spells = list(getattr(player, "spells", []))
    spells += [s for s in getattr(player, "prepared_spells", []) if s not in spells]
    spell_lines = []
    for s in spells:
        uses = "∞" if s.uses_left is None else str(s.uses_left)
        ct = getattr(s, "casting_time", "Action")
        spell_lines.append(f"  {s.name} ({ct}, uses: {uses})")

    ability_lines = []
    for a in getattr(player, "special_abilities", []):
        uses = "∞" if a.uses_left is None else str(a.uses_left)
        ct = getattr(a, "casting_time", "Action")
        ability_lines.append(f"  {a.name} ({ct}, uses: {uses})")

    ac = player.get_armor_class() if callable(getattr(player, "get_armor_class", None)) else "?"

    lines = [
        f"=== {player.name} ===",
        f"Species: {species_name}  Background: {bg_name}  Class: {classes_str}",
        f"HP: {player.current_hp}/{player.max_hp}  AC: {ac}  Speed: {player.speed}ft",
        f"Ability Scores:  {scores}",
        f"Saving Throw proficiencies: {', '.join(saves) or 'none'}",
        f"Skill proficiencies: {', '.join(skills) or 'none'}",
        f"Equipped: {', '.join(equipped)}",
        f"Inventory: {', '.join(inv)}",
        f"Spells ({len(spell_lines)}):",
    ] + (spell_lines or ["  (none)"]) + [
        f"Special Abilities ({len(ability_lines)}):",
    ] + (ability_lines or ["  (none)"])
    return "\n".join(lines)


@tool
def list_character_inventory(player_name: str) -> str:
    """List all items in a player's inventory and currently equipped items."""
    player = _get_player(player_name)
    if player is None:
        return f"No player matching '{player_name}'."

    equipped = player.equipped_items
    inv = player.inventory

    lines = [f"{player.name}'s Equipment:"]
    if equipped:
        lines.append("  Equipped:")
        for item in equipped:
            lines.append(f"    {item.name}  [{getattr(item, 'type', '?')}]")
    else:
        lines.append("  Equipped: nothing")

    lines.append("  Inventory:")
    if inv:
        for item in inv:
            qty = getattr(item, "quantity", 1)
            lines.append(f"    {item.name} x{qty}  [{getattr(item, 'type', '?')}]")
    else:
        lines.append("    (empty)")
    return "\n".join(lines)


@tool
def equip_character_item(player_name: str, item_name: str) -> str:
    """Equip an item from a player's inventory.
    The item must already be in the player's inventory."""
    player = _get_player(player_name)
    if player is None:
        return f"No player matching '{player_name}'."

    # Check item exists
    found = any(
        item_name.lower() in i.name.lower() for i in player.inventory
    )
    if not found:
        inv_names = [i.name for i in player.inventory]
        return f"{player.name} doesn't have '{item_name}' in their inventory. Inventory: {inv_names}"

    # Find exact or partial match
    match = next((i for i in player.inventory if item_name.lower() in i.name.lower()), None)
    player.equip_item(match.name)
    equipped = [i.name for i in player.equipped_items]
    return f"{player.name} equipped {match.name}. Now equipped: {', '.join(equipped)}"


@tool
def unequip_character_item(player_name: str, item_name: str) -> str:
    """Unequip an item from a player, returning it to inventory."""
    player = _get_player(player_name)
    if player is None:
        return f"No player matching '{player_name}'."

    match = next((i for i in player.equipped_items if item_name.lower() in i.name.lower()), None)
    if match is None:
        equipped_names = [i.name for i in player.equipped_items]
        return f"{player.name} doesn't have '{item_name}' equipped. Equipped: {equipped_names}"

    player.unequip_item(match.name)
    equipped = [i.name for i in player.equipped_items]
    return f"{player.name} unequipped {match.name}. Now equipped: {', '.join(equipped) or 'nothing'}"


@tool
def cast_character_spell(
    player_name: str,
    spell_name: str,
    target_name: str = "self",
) -> str:
    """Cast a spell for a player character outside of combat.
    target_name: 'self', or the name of another party member. Defaults to 'self'.
    Use list_character_spells to see available spells and remaining uses."""
    player = _get_player(player_name)
    if player is None:
        return f"No player matching '{player_name}'."

    all_spells = list(getattr(player, "spells", []))
    all_spells += [s for s in getattr(player, "prepared_spells", []) if s not in all_spells]
    spell = next((s for s in all_spells if spell_name.lower() in s.name.lower()), None)
    if spell is None:
        avail = [s.name for s in all_spells if s.uses_left is None or s.uses_left > 0]
        return f"Spell '{spell_name}' not found. Available: {avail}"
    if spell.uses_left == 0:
        return f"{spell.name} has no uses remaining."

    # Resolve target
    if not target_name or target_name.lower() in ("self", "me", player.name.lower()):
        targets = [player]
    else:
        target = _get_player(target_name)
        if target is None:
            return f"No party member matching '{target_name}'. Party: {[p.name for p in _campaign.players]}"
        targets = [target]

    try:
        player.cast_spell(spell.name, targets=targets)
        target_str = targets[0].name if targets else "self"
        return f"{player.name} casts {spell.name} on {target_str}."
    except Exception as exc:
        return f"Error casting {spell.name}: {exc}"


@tool
def use_character_ability(
    player_name: str,
    ability_name: str,
    target_name: str = "self",
) -> str:
    """Use a special ability for a player character outside of combat.
    target_name: 'self', or the name of another party member. Defaults to 'self'."""
    player = _get_player(player_name)
    if player is None:
        return f"No player matching '{player_name}'."

    abilities = getattr(player, "special_abilities", [])
    ability = next((a for a in abilities if ability_name.lower() in a.name.lower()), None)
    if ability is None:
        avail = [a.name for a in abilities if a.uses_left is None or a.uses_left > 0]
        return f"Ability '{ability_name}' not found. Available: {avail}"
    if ability.uses_left == 0:
        return f"{ability.name} has no uses remaining."

    if not target_name or target_name.lower() in ("self", "me", player.name.lower()):
        targets = [player]
    else:
        target = _get_player(target_name)
        if target is None:
            return f"No party member matching '{target_name}'."
        targets = [target]

    try:
        player.use_special_ability(ability.name, targets=targets)
        target_str = targets[0].name if targets else "self"
        return f"{player.name} uses {ability.name} on {target_str}."
    except Exception as exc:
        return f"Error using {ability.name}: {exc}"


@tool
def prepare_character_spell(player_name: str, spell_name: str) -> str:
    """Prepare a spell from a player's spellbook (Wizard, Cleric, etc.).
    The spell must be in the character's spellbook and the character must have
    preparation slots remaining. Call get_character_sheet to see current spells."""
    player = _get_player(player_name)
    if player is None:
        return f"No player matching '{player_name}'."

    try:
        player.prepare_spell(spell_name)
        prepared = [s.name for s in getattr(player, "prepared_spells", [])]
        return f"{player.name} has prepared {spell_name}. Prepared spells: {prepared}"
    except Exception as exc:
        return f"Error preparing {spell_name}: {exc}"


_CHARACTER_TOOLS = [
    get_character_sheet,
    list_character_inventory,
    equip_character_item,
    unequip_character_item,
    cast_character_spell,
    use_character_ability,
    prepare_character_spell,
]

_STORY_TOOLS = [
    get_campaign_state,
    set_scene,
    roll_skill_check,
    roll_ability_check,
    roll_saving_throw,
    list_available_monsters,
    start_combat,
    take_long_rest,
    take_short_rest,
    *_CHARACTER_TOOLS,
]

_STORY_SYSTEM = """\
You are the Dungeon Master for a text-based D&D 5e campaign called Dungeoneer.
Your role is to narrate the world, drive the story, respond to player actions,
and manage non-combat challenges through dice checks.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE #0 — COMBAT IS HANDLED BY THE ENGINE, NOT YOU
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is the most important rule. Read it carefully.

YOU MUST NEVER narrate attack rolls, damage, hit points, monster actions, or
combat outcomes in text. The game engine handles all of that. Your job is to:

  1. Describe the scene leading up to the fight (what the enemies look like,
     where they are, how the confrontation escalates).
  2. Call start_combat() with the enemy list and a map_layout that matches
     the scene (walls, rocks, trees, etc.).
  3. After start_combat() returns "COMBAT_INITIATED", stop — do NOT write
     anything more. The engine takes over from that point.
  4. After combat ends and control returns to you, narrate the aftermath.

If you describe fighting without calling start_combat(), the player cannot
participate and the game is broken. Always hand control to the engine.

WHEN TO CALL start_combat():
  - Any NPC or monster becomes aggressive and attacks, or is attacked.
  - Ambush, bar fight, assassination attempt, monster encounter — all combat.
  - When in doubt, call it. Err on the side of triggering combat.

HOW TO CALL start_combat():
  start_combat(
    setting="brief location description",
    monster_specs='[{"type": "Goblin", "count": 3}]',
    map_layout='[{"type":"wall","x":0,"y":0}, ...]'
  )
  - Use list_available_monsters() first if unsure of valid monster names.
  - map_layout shapes the battlefield visually for the player. See MAP LAYOUT
    section below for guidance.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RULE #1: ALWAYS ASK "DOES THIS NEED A CHECK?"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Before narrating the outcome of ANY non-combat player action, decide:
  A) Is there a meaningful chance of failure?
  B) Would failure have a real consequence?
If both are yes, call a check tool FIRST, then narrate the result.
If the action is trivial or automatic, narrate freely.

DC guidelines:
  DC  5 — very easy    DC 10 — easy    DC 15 — medium
  DC 20 — hard         DC 25 — very hard

  roll_skill_check(name, skill, dc)  → Athletics, Stealth, Perception, etc.
  roll_ability_check(name, ability, dc) → Raw Strength, Constitution, etc.
  roll_saving_throw(name, ability, dc) → Traps, poison, spells, fear, etc.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAP LAYOUT — BUILDING THE BATTLEFIELD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
When calling start_combat(), always build a map_layout that reflects the scene.
The player sees this map visually — make it match what you described.

Map dimensions: 22 cells wide. Height depends on combatant count (10–20 cells).
Players spawn at x≈3 (left side). Enemies spawn at x≈17 (right side).
Top-left is (0,0). Keep a clear path between both sides.

Terrain types:
  "wall"  — solid barrier, blocks movement and sight (dungeon walls, buildings)
  "rock"  — impassable cover, doesn't block sight (boulders, rubble)
  "tree"  — impassable, blocks sight (forests, gardens)
  "door"  — passable barrier (open doorways, gates)

Pattern examples (map height h):
  Dungeon corridor (h=12):
    walls along entire y=0 row, entire y=11 row, maybe a pillar at (10,5) and (10,6)
    '[{"type":"wall","x":0,"y":0},{"type":"wall","x":1,"y":0},...,
      {"type":"wall","x":0,"y":11},...,
      {"type":"rock","x":10,"y":5},{"type":"rock","x":10,"y":6}]'

  Forest clearing (h=14):
    trees scattered at edges (x<3 and x>18), rocks at mid-map for cover
    '[{"type":"tree","x":0,"y":3},{"type":"tree","x":1,"y":7},...,
      {"type":"rock","x":9,"y":5},{"type":"rock","x":12,"y":9}]'

  Open dungeon room (h=12):
    walls along all four borders (x=0, x=21, y=0, y=11), except a doorway
    '[{"type":"wall","x":0,"y":0},...,{"type":"wall","x":21,"y":11},...]'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CORE STORY RESPONSIBILITIES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Paint vivid scenes in 2-4 sentences. React to everything the player does.
- Call set_scene() whenever the party moves to a meaningfully new location.
- Suggest long or short rests when it makes narrative sense and call the tool.
- Keep secrets: don't reveal DCs, exact HP, or raw mechanical details unless asked.
- After combat ends, weave the outcome naturally into the ongoing story.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CHARACTER MANAGEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Respond naturally to requests like "I check my sheet", "equip my sword":
- get_character_sheet(name) / list_character_inventory(name)
- equip_character_item(name, item) / unequip_character_item(name, item)
- cast_character_spell(name, spell, target?) — outside combat only
- use_character_ability(name, ability, target?) — outside combat only
- prepare_character_spell(name, spell)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TONE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Epic fantasy, vivid but concise. Use second person ("You enter the hall…").
Never break character unless the player explicitly asks an out-of-game question.
"""


def create_story_agent(model: str = "gemma4"):
    """Return a compiled LangGraph ReAct agent for story / DM mode."""
    if model.startswith("claude"):
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model=model)
    else:
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model=model)
    return create_react_agent(llm, _STORY_TOOLS, prompt=_STORY_SYSTEM)
