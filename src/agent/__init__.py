"""Dungeoneer LangGraph agent module.

Exposes the GameSession wrapper and agent factory so the game can be driven
via natural language chat instead of raw terminal input.

Quickstart::

    from src.agent import run
    run()                 # starts a default Fighter-vs-Goblins encounter

Custom encounter::

    from src.combat import Combat
    from src.agent import GameSession, set_session, create_agent, run

    combat = Combat(...)
    run(combat=combat)
"""

from src.agent.session import GameSession
from src.agent.tools import set_session
from src.agent.graph import create_agent
from src.agent.chat import run

__all__ = ["GameSession", "set_session", "create_agent", "run"]
