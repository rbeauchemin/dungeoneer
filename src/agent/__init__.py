"""Dungeoneer LangGraph agent module.

Full campaign mode (character creation → story → combat)::

    from src.agent import run
    run()

    # or: python -m src.agent.chat

Direct combat test (skips creation/story)::

    from src.combat import Combat
    from src.agent import run
    run(combat=my_combat)
"""

from src.agent.session import GameSession
from src.agent.tools import set_session
from src.agent.graph import create_agent as create_combat_agent
from src.agent.creation import create_creation_agent
from src.agent.story_tools import create_story_agent
from src.agent.campaign import _campaign
from src.agent.chat import run

__all__ = [
    "GameSession",
    "set_session",
    "create_combat_agent",
    "create_creation_agent",
    "create_story_agent",
    "_campaign",
    "run",
]
