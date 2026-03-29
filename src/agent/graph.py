"""LangGraph ReAct agent for Dungeoneer.

Creates a compiled ``StateGraph`` agent that can drive a player turn via
natural language reasoning and tool calls.

Usage::

    from src.agent.graph import create_agent

    agent = create_agent()                          # defaults to claude-opus-4-6
    agent = create_agent(model="claude-sonnet-4-6") # cheaper / faster option
    result = agent.invoke({"messages": [...]})
"""

from __future__ import annotations

from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage

from src.agent.tools import ALL_TOOLS

_SYSTEM_PROMPT = SystemMessage(content="""\
You are an expert D&D 5e dungeon master for a turn-based dungeon \
crawler called Dungeoneer. You help the player control their character \
in combat encounters by calling tools that interact with the game state and \
narrating the results in fantasy language. Your goal is to guide the player \
through the dungeon and provide an engaging and fun narrative experience.

On each turn you may use these tools:
- get_game_state()           — check HP, positions, and remaining resources
- move_to(x, y)              — move toward grid coordinates
- move_toward(name)          — move toward a named enemy
- attack(target, weapon?)    — make a weapon attack
- cast_spell(spell, target?) — cast a prepared spell
- use_ability(name, target?) — use a class feature (Rage, Second Wind, …)
- dash()                     — use your action to gain extra movement
- end_turn()                 — pass remaining actions and end your turn
- list_spells()              — see prepared spells and spell slots
- list_abilities()           — see class abilities and uses remaining

Decision guidelines:
1. Call get_game_state() first if you are unsure of your position or the situation.
6. Always call end_turn() when your actions and movement are spent.

After acting, briefly narrate what happened in plain, but slightly fantasy-embellished English (one or two sentences).
Do not repeat the raw game output verbatim — summarize it naturally.
""")


def create_agent(model: str = "claude-opus-4-6"):
    """Return a compiled LangGraph ReAct agent bound to all Dungeoneer tools.

    Parameters
    ----------
    model:
        Anthropic model ID.  Defaults to ``claude-opus-4-6``.
    """
    llm = ChatAnthropic(model=model)
    return create_react_agent(llm, ALL_TOOLS, prompt=_SYSTEM_PROMPT)
