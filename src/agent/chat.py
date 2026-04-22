"""Dungeoneer — main campaign entry point.

Phases
------
1. Character Creation  — the creation agent walks each player through building
   their character conversationally (species, background, class, skill choices …).

2. Story / Exploration — the DM agent narrates the world and responds to player
   actions.  Non-combat challenges are resolved with skill-check tools.

3. Combat             — triggered automatically when the DM calls start_combat().
   The combat agent drives player turns; the GameSession thread runs the engine.
   On completion the story resumes with the battle result folded in.

Run::

    python -m src.agent.chat

Requires ANTHROPIC_API_KEY (shell env or .env file).
"""

from __future__ import annotations

import os
import sys
from typing import Optional

from langchain_core.messages import HumanMessage

from src.agent.campaign import _campaign
from src.agent.creation import create_creation_agent
from src.agent.story_tools import create_story_agent
from src.agent.session import GameSession


# ── Utilities ──────────────────────────────────────────────────────────────────

_COMBAT_WORDS = frozenset([
    "attack", "attacks", "strikes", "charges", "assaults", "lunges", "swings",
    "slashes", "stabs", "fires", "shoots", "combat", "battle", "fight",
    "fighting", "initiative", "hostile", "ambush", "ambushes",
    "draw their weapon", "moves to attack", "springs into action",
    "roll for initiative", "combat begins", "the battle", "clash",
])


def _has_combat_language(text: str) -> bool:
    """Return True if text describes active combat starting."""
    t = text.lower()
    return any(w in t for w in _COMBAT_WORDS)


def _hr(char: str = "=", width: int = 60) -> str:
    return char * width


def _prompt(label: str = "You") -> str:
    """Read a line from stdin; raise SystemExit on quit commands."""
    try:
        line = input(f"\n{label} > ").strip()
    except (EOFError, KeyboardInterrupt):
        raise SystemExit(0)
    if line.lower() in ("quit", "exit", "q"):
        raise SystemExit(0)
    return line


# ── Phase 0: Campaign setting ──────────────────────────────────────────────────

def run_setting_phase() -> None:
    """Ask the player(s) what kind of campaign they want and store a setting brief."""
    print(_hr())
    print("  CAMPAIGN SETUP")
    print(_hr())
    print("""
  Before we begin, tell me about the world you want to adventure in.
  You can describe as much or as little as you like — a single word
  or a full paragraph. Consider:

    • Setting & genre  (classic fantasy, dark gothic, nautical, sci-fantasy…)
    • Tone             (heroic epic, gritty survival, political intrigue, comedy…)
    • Specific themes  (underdark, dragons, heists, ancient ruins, war, horror…)
    • Any hard no's    (content you want to avoid or things you don't want in the world)
""")
    try:
        raw = input("  What kind of campaign would you like? > ").strip()
    except (EOFError, KeyboardInterrupt):
        raise SystemExit(0)

    if not raw:
        raw = "A classic fantasy adventure with exciting combat and exploration."

    _campaign.setting_brief = raw
    print(f"\n  Got it — I'll craft a world around: \"{raw}\"")


# ── Phase 1: Character Creation ────────────────────────────────────────────────

def run_creation_phase(model: str) -> None:
    """Interactively create one character per player and add them to _campaign."""
    print(_hr())
    print("  CHARACTER CREATION")
    print(_hr())

    try:
        raw = input("\nHow many players? [1] ").strip()
        n_players = int(raw) if raw.isdigit() else 1
    except (EOFError, KeyboardInterrupt):
        raise SystemExit(0)

    n_players = max(1, min(n_players, 4))

    agent = create_creation_agent(model=model)

    for player_num in range(1, n_players + 1):
        print(f"\n{_hr('-')}")
        if n_players > 1:
            print(f"  Player {player_num} of {n_players}")
        print(_hr("-"))

        _campaign.pending_character = None
        messages: list = []

        player_tag = f" (player {player_num} of {n_players})" if n_players > 1 else ""
        opener = (
            "Welcome, adventurer! I'm here to help you create your character"
            + player_tag
            + ". What kind of hero do you want to be?"
        )
        messages.append(HumanMessage(content=opener))
        result = agent.invoke({"messages": messages})
        messages = result["messages"]
        print(f"\nAgent: {result['messages'][-1].content}")

        # Conversation loop until character is complete
        while True:
            # Check if creation is done
            char = _campaign.pending_character
            if char is not None and not char.todo:
                _campaign.players.append(char)
                _campaign.pending_character = None
                print(f"\n  ✓ {char.name} is ready to adventure!")
                break

            user_input = _prompt("You")
            if not user_input:
                user_input = "Continue."

            messages.append(HumanMessage(content=user_input))
            result = agent.invoke({"messages": messages})
            messages = result["messages"]
            print(f"\nAgent: {result['messages'][-1].content}")


# ── Phase 3: Combat sub-loop ───────────────────────────────────────────────────

def run_combat_loop(session: GameSession) -> str:
    """Drive a full combat encounter interactively. Returns a result summary."""
    print(f"\n{_hr()}")
    print(f"  ⚔  COMBAT — {_campaign.combat_setting}")
    print(_hr())
    print("  Commands: attack <name>  |  move <x> <y>  |  move <name>")
    print("            cast <spell> [target]  |  ability <name> [target]")
    print("            dash  |  spells  |  abilities  |  pass (end turn)  |  state")
    print(_hr())

    initial_output = session.start()
    if initial_output.strip():
        print(initial_output)

    while not session.is_game_over:
        user_input = _prompt("Combat")
        if not user_input:
            continue

        output = session.send(user_input)
        if output.strip():
            print(output)

    winner = session.winner or "unknown"
    return (
        f"The players won the battle against {_campaign.combat_setting}!"
        if winner == "players"
        else f"The party was defeated at {_campaign.combat_setting}."
    )


# ── Phase 2: Story / exploration loop ─────────────────────────────────────────

def run_story_phase(model: str) -> None:
    """Run the main campaign story loop, weaving in combat as the DM decides."""
    print(f"\n{_hr()}")
    print("  THE ADVENTURE BEGINS")
    print(_hr())
    print("  (Type your actions, questions, or 'quit' to exit.)")
    print(_hr())

    agent = create_story_agent(model=model)
    messages: list = []

    # Kick off the story
    player_names = " and ".join(p.name for p in _campaign.players)
    setting_context = (
        f" The player requested this setting: \"{_campaign.setting_brief}\"."
        if _campaign.setting_brief else ""
    )
    kick_off = (
        f"Begin the campaign for {player_names}.{setting_context} "
        f"Set an opening scene that fits the requested setting and tone, "
        f"then invite the player(s) to act."
    )
    messages.append(HumanMessage(content=kick_off))
    result = agent.invoke({"messages": messages})
    messages = result["messages"]
    print(f"\nDM: {result['messages'][-1].content}")

    session: Optional[GameSession] = None

    # Helper: enter combat when active_combat is set by the story agent
    def _enter_combat() -> None:
        nonlocal session
        session = _campaign.active_combat
        _campaign.active_combat = None
        print(f"\n{_hr()}")
        print(f"  ⚔  COMBAT — {_campaign.combat_setting}")
        print(_hr())
        print("  Commands: attack <name>  |  move <x> <y>  |  move <name>")
        print("            cast <spell> [target]  |  ability <name> [target]")
        print("            dash  |  spells  |  abilities  |  pass (end turn)  |  state")
        print(_hr())
        initial = session.start()
        if initial.strip():
            print(initial)

    # Helper: leave combat and let the story agent narrate the aftermath
    def _leave_combat(combat_result: str) -> None:
        nonlocal session
        from src.combat import _is_dead
        _campaign.last_combat_result = combat_result
        _campaign.players = [p for p in _campaign.players if not _is_dead(p)]
        session = None
        print(f"\n{_hr()}")
        print("  RETURNING TO THE STORY …")
        print(_hr())
        followup = HumanMessage(
            content=f"The combat has ended. Result: {combat_result}. Continue the story."
        )
        messages.append(followup)
        result = agent.invoke({"messages": messages})
        messages[:] = result["messages"]
        print(f"\nDM: {result['messages'][-1].content}")

    # Check if combat was already triggered by the opening scene
    if _campaign.active_combat is not None:
        _enter_combat()

    while True:
        label = "Combat" if session is not None else "You"
        user_input = _prompt(label)
        if not user_input:
            continue

        if session is not None:
            # ── Combat mode: forward input directly to the game engine ────────
            output = session.send(user_input)
            if output.strip():
                print(output)

            if session.is_game_over:
                winner = session.winner or "unknown"
                result_str = (
                    f"The players won the battle against {_campaign.combat_setting}!"
                    if winner == "players"
                    else f"The party was defeated at {_campaign.combat_setting}."
                )
                _leave_combat(result_str)
                # Story agent may itself trigger another encounter
                if _campaign.active_combat is not None:
                    _enter_combat()
        else:
            # ── Story mode: run through the story agent ───────────────────────
            messages.append(HumanMessage(content=user_input))
            result = agent.invoke({"messages": messages})
            messages = result["messages"]
            dm_reply = result["messages"][-1].content
            print(f"\nDM: {dm_reply}")

            # Nudge the agent if it described combat without calling start_combat()
            if _campaign.active_combat is None and _has_combat_language(dm_reply):
                nudge = (
                    "SYSTEM REMINDER: Your last response described combat starting, "
                    "but you did not call start_combat(). Call start_combat() right now "
                    "with the enemies you just mentioned. Only call the tool — no narration."
                )
                messages.append(HumanMessage(content=nudge))
                result = agent.invoke({"messages": messages})
                messages = result["messages"]

            if _campaign.active_combat is not None:
                _enter_combat()


# ── Entry point ────────────────────────────────────────────────────────────────

def run(
    combat=None,
    model: str = None,
) -> None:
    """Start a Dungeoneer campaign.

    Parameters
    ----------
    combat:
        Pass a pre-built ``Combat`` instance to skip character creation and
        jump straight into a single combat encounter (useful for testing).
    model:
        Model ID used for all agents. Defaults to DUNGEONEER_MODEL env var,
        or ``gemma4`` if unset. Use an Ollama model name (e.g.
        ``llama3``) to run locally without an Anthropic key.
    """
    if model is None:
        model = os.getenv("DUNGEONEER_MODEL", "gemma4")
    print(_hr())
    print("  DUNGEONEER")
    print("  A D&D 5e Text Adventure")
    print(_hr())

    if combat is not None:
        # ── Test mode: single combat, no story wrapping ───────────────────────
        from src.agent.session import GameSession
        session = GameSession(combat)
        _campaign.combat_setting = "Test Encounter"
        result = run_combat_loop(session)
        print(f"\n{_hr()}")
        print(f"  {result}")
        print(_hr())
        return

    # ── Full campaign mode ─────────────────────────────────────────────────────
    run_setting_phase()
    run_creation_phase(model=model)

    if not _campaign.players:
        print("No characters created. Exiting.")
        return

    run_story_phase(model=model)


if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    if not os.getenv("ANTHROPIC_API_KEY"):
        print(
            "Error: ANTHROPIC_API_KEY is not set.\n"
            "Export it in your shell or add it to a .env file.",
            file=sys.stderr,
        )
        sys.exit(1)

    run()
