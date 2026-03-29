"""Dungeoneer agent chat loop.

Starts a game session and runs a human-in-the-loop chat interface: the user
gives high-level instructions each turn and the LangGraph agent translates
them into game commands.

Run the default Fighter-vs-Goblins demo::

    python -m src.agent.chat

Or import and call ``run()`` with a custom encounter::

    from src.combat import Combat
    from src.agent.chat import run
    run(combat=my_combat)

Requires ``ANTHROPIC_API_KEY`` in the environment (or in a ``.env`` file if
``python-dotenv`` is installed).
"""

from __future__ import annotations

import os
import sys
from typing import Optional

from langchain_core.messages import HumanMessage

from src.map import Map
from src.creatures.character import Character
from src.creatures.monsters import Goblin
from src.classes.fighter import Fighter
from src.combat import Combat

from src.agent.session import GameSession
from src.agent.tools import set_session
from src.agent.graph import create_agent


# ── Default encounter ──────────────────────────────────────────────────────────

def _build_default_encounter() -> Combat:
    """Fighter level 3 vs two Goblins on a 20×12 grid."""
    hero = Character(
        name="Aldric",
        species="Human",
        background="Soldier",
        classes=[Fighter(3)],
    )

    dungeon = Map(20, 12, name="Goblin Cave")
    goblin_a = Goblin(name="Goblin A")
    goblin_b = Goblin(name="Goblin B")

    dungeon.place_creature(hero, 3, 6)
    dungeon.place_creature(goblin_a, 16, 4)
    dungeon.place_creature(goblin_b, 16, 8)

    return Combat(dungeon, players=[hero], monsters=[goblin_a, goblin_b])


# ── Chat loop ──────────────────────────────────────────────────────────────────

def run(
    combat: Optional[Combat] = None,
    model: str = "claude-opus-4-6",
) -> None:
    """Start a Dungeoneer game session driven by a LangGraph agent.

    Parameters
    ----------
    combat:
        A pre-built ``Combat`` instance.  When ``None`` a default
        Fighter-vs-two-Goblins encounter is created automatically.
    model:
        Anthropic model ID passed to ``create_agent()``.
    """
    if combat is None:
        combat = _build_default_encounter()

    session = GameSession(combat)
    set_session(session)
    agent = create_agent(model=model)

    print("\n" + "=" * 60)
    print("  DUNGEONEER — Agent Mode")
    print("  Type instructions for your character, or 'quit' to exit.")
    print("  Leave blank to let the agent act on its own judgment.")
    print("=" * 60)

    # Boot the game and display opening output
    initial_output = session.start()
    if initial_output.strip():
        print(initial_output)

    conversation: list = []

    while not session.is_game_over:
        state = session.get_state_description()

        print("\n" + "-" * 40)
        try:
            user_input = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if user_input.lower() in ("quit", "exit", "q"):
            break

        # Fall back to autonomous play if the user gives no instruction
        if not user_input:
            user_input = "Take your turn using your best judgment."

        full_prompt = (
            f"Current game state:\n{state}\n\n"
            f"Player instruction: {user_input}"
        )
        conversation.append(HumanMessage(content=full_prompt))

        # Run the agent — it calls tools until the turn is over
        result = agent.invoke({"messages": conversation})
        conversation = result["messages"]

        ai_response = result["messages"][-1].content
        print(f"\nAgent: {ai_response}")

        # Flush any remaining game output captured after the last tool call
        leftover = session._take_output()
        if leftover.strip():
            print(leftover)

    if session.is_game_over:
        print(f"\n{'=' * 60}")
        print(f"  GAME OVER — {(session.winner or 'unknown').upper()} WIN")
        print("=" * 60)


if __name__ == "__main__":
    # Try loading a .env file if python-dotenv is available
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    if not os.getenv("ANTHROPIC_API_KEY"):
        print(
            "Error: ANTHROPIC_API_KEY is not set.\n"
            "Export it in your shell or create a .env file.",
            file=sys.stderr,
        )
        sys.exit(1)

    run()
