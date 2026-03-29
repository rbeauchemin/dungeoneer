"""LangGraph tool definitions for Dungeoneer.

Each tool corresponds to one command a player can issue during their turn.
Tools delegate to the global ``_session``; call ``set_session()`` before
invoking any agent that uses these tools.
"""

from __future__ import annotations

from typing import Optional

from langchain_core.tools import tool

from src.agent.session import GameSession

_session: Optional[GameSession] = None


def set_session(session: GameSession) -> None:
    """Register the active GameSession used by all tools."""
    global _session
    _session = session


def _s() -> GameSession:
    if _session is None:
        raise RuntimeError("No active GameSession — call set_session() first.")
    return _session


# ── Tools ──────────────────────────────────────────────────────────────────────

@tool
def get_game_state() -> str:
    """Return the current combat state: player HP/position/resources and all
    living enemy HP/positions. Call this whenever you need situational awareness
    before deciding what to do."""
    return _s().get_state_description()


@tool
def move_to(x: int, y: int) -> str:
    """Move your character toward grid position (x, y) using pathfinding.
    Movement is limited by remaining speed this turn.
    Example: move_to(8, 5)"""
    return _s().send(f"move {x} {y}")


@tool
def move_toward(target_name: str) -> str:
    """Move toward a named enemy or destination using pathfinding.
    Useful when you don't know the exact coordinates.
    Example: move_toward("goblin")"""
    return _s().send(f"move {target_name}")


@tool
def attack(target_name: str, weapon_name: Optional[str] = None) -> str:
    """Make a weapon attack against a named enemy.
    Optionally specify which weapon to use (default: best available).
    Example: attack("goblin") or attack("goblin a", "longsword")"""
    cmd = f"attack {target_name}"
    if weapon_name:
        cmd += f" {weapon_name}"
    return _s().send(cmd)


@tool
def cast_spell(spell_name: str, target_name: Optional[str] = None) -> str:
    """Cast a prepared spell. Most offensive spells require a target.
    Use list_spells() to see what is available.
    Example: cast_spell("fireball", "goblin") or cast_spell("shield")"""
    cmd = f"cast {spell_name}"
    if target_name:
        cmd += f" {target_name}"
    return _s().send(cmd)


@tool
def use_ability(ability_name: str, target_name: Optional[str] = None) -> str:
    """Use a class special ability (Rage, Second Wind, Action Surge, etc.).
    Use list_abilities() to see what is available and how many uses remain.
    Example: use_ability("rage") or use_ability("second wind")"""
    cmd = f"ability {ability_name}"
    if target_name:
        cmd += f" {target_name}"
    return _s().send(cmd)


@tool
def dash() -> str:
    """Use your action to Dash, gaining additional movement equal to your speed."""
    return _s().send("dash")


@tool
def end_turn() -> str:
    """End your turn, passing any remaining actions and movement."""
    return _s().send("pass")


@tool
def list_spells() -> str:
    """List your prepared spells and remaining spell slots."""
    return _s().send("spells")


@tool
def list_abilities() -> str:
    """List your available special abilities and remaining uses."""
    return _s().send("abilities")


@tool
def reply(answer: str) -> str:
    """Send a direct answer to a game prompt.
    Use when a tool result ends with a question like '[Y/n]' or '[number or Enter to skip]'.
    Examples: reply('y') for yes, reply('n') for no, reply('1') to choose option 1, reply('') to skip."""
    return _s().send(answer)


ALL_TOOLS = [
    get_game_state,
    move_to,
    move_toward,
    attack,
    cast_spell,
    use_ability,
    dash,
    end_turn,
    list_spells,
    list_abilities,
    reply,
]
