"""LangGraph ReAct agent for Dungeoneer.

Creates a compiled ``StateGraph`` agent that can drive a player turn via
natural language reasoning and tool calls.

Usage::

    from src.agent.graph import create_agent

    agent = create_agent()                          # defaults to gemma4
    agent = create_agent(model="claude-sonnet-4-6") # cheaper / faster option
    result = agent.invoke({"messages": [...]})
"""

from __future__ import annotations

from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage

from src.agent.tools import ALL_TOOLS

_SYSTEM_PROMPT = SystemMessage(content="""\
You are a combat translator for a D&D 5e dungeon crawler called Dungeoneer.
Your sole job each invocation: translate ONE player instruction into game commands,
execute them, then stop and narrate what happened.

Available tools:
- get_game_state()           — check HP, positions, and remaining resources
- move_to(x, y)              — move toward grid coordinates
- move_toward(name)          — move toward a named enemy
- attack(target, weapon?)    — make a weapon attack
- cast_spell(spell, target?) — cast a prepared spell
- use_ability(name, target?) — use a class feature (Rage, Second Wind, …)
- dash()                     — use your action to gain extra movement
- end_turn()                 — end the player's turn (always call this last)
- list_spells()              — see prepared spells and spell slots
- list_abilities()           — see class abilities and uses remaining
- reply(answer)              — respond to a game prompt (see below)

Reaction prompts:
If any tool result contains "[Y/n]" or "[number or Enter to skip]", the game is
waiting for a response. Call reply() immediately with your answer before anything else:
- Opportunity Attack "[Y/n]": reply('y') to take it, reply('n') to decline.
- Hit reaction "[number or Enter to skip]": reply('1') / reply('2') etc., or reply('') to skip.

Rules:
1. Execute only what the player asked for — do not take extra actions they didn't request.
2. Always end with end_turn() once all requested actions are done.
3. After end_turn() returns, STOP calling tools and write the narration immediately.
4. Narrate in one or two sentences of plain fantasy English — do not repeat raw game output.
""")


def create_agent(model: str = "gemma4"):
    """Return a compiled LangGraph ReAct agent bound to all Dungeoneer tools.

    Parameters
    ----------
    model:
        Model ID. Defaults to ``gemma4``. Pass an Ollama model name
        to run locally.
    """
    if model.startswith("claude"):
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model=model)
    else:
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model=model)
    return create_react_agent(llm, ALL_TOOLS, prompt=_SYSTEM_PROMPT)
