"""Shared campaign state.

All agent modules import the singleton ``_campaign`` from here so they share
one source of truth for players, scene, and active combat.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from src.agent.session import GameSession


@dataclass
class CampaignState:
    players: list = field(default_factory=list)          # list[Character]
    current_scene: str = "An unknown location."
    story_log: list[str] = field(default_factory=list)   # narrative history

    # Combat handoff
    active_combat: Optional["GameSession"] = None
    combat_setting: str = ""
    last_combat_result: str = ""

    # Character-creation scratch pad (one character at a time)
    pending_character: object = None


# Module-level singleton — import this everywhere
_campaign = CampaignState()
