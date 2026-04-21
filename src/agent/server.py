"""FastAPI server for the Dungeoneer web frontend.

Run::

    uvicorn src.agent.server:app --reload --port 8000

Then open http://localhost:8000 in a browser.

Requires ANTHROPIC_API_KEY in the environment or a .env file.
"""

from __future__ import annotations

import os
import pathlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

app = FastAPI(title="Dungeoneer")

# Disable ASCII map rendering — the frontend draws the map on a canvas instead.
import src.agent.story_tools as _story_tools
_story_tools.SHOW_ASCII_MAP = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_FRONTEND = pathlib.Path(__file__).parent.parent.parent / "frontend" / "index.html"

_CREATION_WELCOME = """\
Welcome to **Dungeoneer** — a D&D 5e text adventure.

Before we begin, tell me about the world you'd like to explore. \
A single word or a full paragraph works:

- **Setting & genre** — classic fantasy, dark gothic, nautical, sci-fantasy…
- **Tone** — heroic epic, gritty survival, political intrigue, comedy…
- **Themes** — underdark, dragons, heists, ancient ruins, war, horror…
- **Hard no's** — anything you'd rather the story avoid

*What kind of campaign would you like?*
"""


# ── Per-campaign state ─────────────────────────────────────────────────────────

@dataclass
class _CampaignRecord:
    id: str
    name: str = "New Campaign"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    phase: str = "setting"  # setting | creation | story | combat

    display_messages: list = field(default_factory=list)
    creation_messages: list = field(default_factory=list)
    story_messages: list = field(default_factory=list)
    combat_messages: list = field(default_factory=list)

    creation_agent: object = None
    story_agent: object = None
    combat_agent: object = None
    combat_session: object = None

    # Snapshot of _campaign singleton fields
    players: list = field(default_factory=list)
    pending_character: object = None
    setting_brief: str = ""
    current_scene: str = "An unknown location."
    story_log: list = field(default_factory=list)
    active_combat: object = None
    last_combat_result: str = ""
    combat_setting: str = ""


_campaigns: dict[str, _CampaignRecord] = {}


# ── Global state helpers ───────────────────────────────────────────────────────

def _load(record: _CampaignRecord) -> None:
    """Swap the global _campaign singleton to this campaign's saved state."""
    from src.agent.campaign import _campaign
    _campaign.players = record.players
    _campaign.pending_character = record.pending_character
    _campaign.setting_brief = record.setting_brief
    _campaign.current_scene = record.current_scene
    _campaign.story_log = record.story_log
    _campaign.active_combat = record.active_combat
    _campaign.last_combat_result = record.last_combat_result
    _campaign.combat_setting = record.combat_setting


def _save(record: _CampaignRecord) -> None:
    """Snapshot the global _campaign singleton back into this campaign's record."""
    from src.agent.campaign import _campaign
    record.players = _campaign.players
    record.pending_character = _campaign.pending_character
    record.setting_brief = _campaign.setting_brief
    record.current_scene = _campaign.current_scene
    record.story_log = _campaign.story_log
    record.active_combat = _campaign.active_combat
    record.last_combat_result = _campaign.last_combat_result
    record.combat_setting = _campaign.combat_setting


def _model() -> str:
    return os.getenv("DUNGEONEER_MODEL", "gemma4")


def _msg(role: str, content: str) -> dict:
    return {"role": role, "content": content, "timestamp": datetime.now().isoformat()}


def _summary(record: _CampaignRecord) -> dict:
    return {
        "id": record.id,
        "name": record.name,
        "phase": record.phase,
        "created_at": record.created_at,
        "message_count": len(record.display_messages),
    }


def _get(campaign_id: str) -> _CampaignRecord:
    if campaign_id not in _campaigns:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return _campaigns[campaign_id]


# ── API endpoints ──────────────────────────────────────────────────────────────

class _SendBody(BaseModel):
    content: str


@app.post("/api/campaigns")
def create_campaign():
    """Create a new campaign and return its summary + initial welcome message."""
    campaign_id = str(uuid.uuid4())
    record = _CampaignRecord(id=campaign_id)
    welcome = _msg("assistant", _CREATION_WELCOME)
    record.display_messages.append(welcome)
    _campaigns[campaign_id] = record
    return {**_summary(record), "messages": record.display_messages}


@app.get("/api/campaigns")
def list_campaigns():
    """Return all campaigns sorted by creation time."""
    return [
        _summary(r)
        for r in sorted(_campaigns.values(), key=lambda r: r.created_at)
    ]


@app.get("/api/campaigns/{campaign_id}/messages")
def get_messages(campaign_id: str):
    return _get(campaign_id).display_messages


@app.post("/api/campaigns/{campaign_id}/message")
def send_message(campaign_id: str, body: _SendBody):
    """Send a player message and return the assistant reply."""
    record = _get(campaign_id)
    user_content = body.content.strip()
    if not user_content:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    user_msg = _msg("user", user_content)
    record.display_messages.append(user_msg)

    _load(record)
    try:
        reply = _process(record, user_content)
    except Exception as exc:
        # Roll back the user message so the conversation stays consistent
        record.display_messages.pop()
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        _save(record)

    assistant_msg = _msg("assistant", reply)
    record.display_messages.append(assistant_msg)

    # Include map state whenever a combat session is active
    map_data = None
    if record.combat_session is not None:
        try:
            map_data = record.combat_session.get_map_dict()
        except Exception:
            pass

    return {
        "content": reply,
        "phase": record.phase,
        "campaign": _summary(record),
        "map": map_data,
    }


# ── Phase routing ──────────────────────────────────────────────────────────────

def _process(record: _CampaignRecord, user_input: str) -> str:
    if record.phase == "setting":
        return _handle_setting(record, user_input)
    if record.phase == "creation":
        return _handle_creation(record, user_input)
    if record.phase == "story":
        return _handle_story(record, user_input)
    if record.phase == "combat":
        return _handle_combat(record, user_input)
    return "Unknown game phase."


def _handle_setting(record: _CampaignRecord, user_input: str) -> str:
    from src.agent.campaign import _campaign
    from src.agent.creation import create_creation_agent

    _campaign.setting_brief = user_input
    record.name = user_input[:60] + ("…" if len(user_input) > 60 else "")
    record.phase = "creation"

    record.creation_agent = create_creation_agent(model=_model())

    # Kick off the creation agent with a synthetic opener
    opener = (
        "Welcome, adventurer! I'm here to help you create your character. "
        "What kind of hero do you want to be? Tell me about your vision — "
        "fighting style, personality, fantasy archetype — anything that inspires you."
    )
    record.creation_messages.append(HumanMessage(content=opener))
    result = record.creation_agent.invoke({"messages": record.creation_messages})
    record.creation_messages = result["messages"]
    return result["messages"][-1].content


def _handle_creation(record: _CampaignRecord, user_input: str) -> str:
    from src.agent.campaign import _campaign
    from src.agent.creation import finalize_character

    # Check whether creation completed during the *previous* turn
    char = _campaign.pending_character
    if char is not None and not char.todo:
        _campaign.players.append(char)
        _campaign.pending_character = None
        return _kickoff_story(record)

    record.creation_messages.append(HumanMessage(content=user_input))
    result = record.creation_agent.invoke({"messages": record.creation_messages})
    record.creation_messages = result["messages"]
    reply = result["messages"][-1].content

    # Safety net: if a character exists but the agent left todos unresolved,
    # auto-finalize so creation never gets permanently stuck.
    char = _campaign.pending_character
    if char is not None and char.todo:
        finalize_character.invoke({})   # resolves remaining todos in-place

    # Check whether creation completed during *this* turn (or via safety net)
    char = _campaign.pending_character
    if char is not None and not char.todo:
        _campaign.players.append(char)
        _campaign.pending_character = None
        record.phase = "story"
        story_intro = _kickoff_story(record)
        return reply + "\n\n---\n\n" + story_intro

    return reply


def _kickoff_story(record: _CampaignRecord) -> str:
    """Initialise the story agent and get the opening scene. Returns the DM's first narration."""
    from src.agent.campaign import _campaign
    from src.agent.story_tools import create_story_agent

    record.phase = "story"
    record.story_agent = create_story_agent(model=_model())

    player_names = " and ".join(p.name for p in _campaign.players)
    setting_ctx = (
        f' The player requested this setting: "{_campaign.setting_brief}".'
        if _campaign.setting_brief else ""
    )
    kick_off = (
        f"Begin the campaign for {player_names}.{setting_ctx} "
        f"Set an opening scene that fits the requested setting and tone, "
        f"then invite the player(s) to act."
    )
    record.story_messages.append(HumanMessage(content=kick_off))
    result = record.story_agent.invoke({"messages": record.story_messages})
    record.story_messages = result["messages"]
    reply = result["messages"][-1].content

    # The DM may have triggered combat in the opening scene
    if _campaign.active_combat is not None:
        reply += "\n\n" + _begin_combat(record)

    return reply


_COMBAT_WORDS = frozenset([
    "attack", "attacks", "strikes", "charges", "assaults", "lunges", "swings",
    "slashes", "stabs", "fires", "shoots", "casts", "combat", "battle",
    "fight", "fighting", "initiative", "hostile", "ambush", "ambushes",
    "draw their weapon", "draw their sword", "draw their axe",
    "moves to attack", "springs into action", "roll for initiative",
    "combat begins", "the battle", "clash", "clashes",
])


def _has_combat_language(text: str) -> bool:
    """Return True if the text describes active combat starting."""
    t = text.lower()
    return any(w in t for w in _COMBAT_WORDS)


def _handle_story(record: _CampaignRecord, user_input: str) -> str:
    from src.agent.campaign import _campaign
    from langchain_core.messages import ToolMessage

    record.story_messages.append(HumanMessage(content=user_input))
    result = record.story_agent.invoke({"messages": record.story_messages})
    record.story_messages = result["messages"]
    reply = result["messages"][-1].content

    # If the reply describes combat but start_combat() was not called, nudge the agent
    # once to make the tool call it forgot.
    if _campaign.active_combat is None and _has_combat_language(reply):
        nudge = (
            "SYSTEM REMINDER: Your last response described combat starting, but you "
            "did not call start_combat(). You MUST call start_combat() right now with "
            "the enemies you just described. Do not add more narration — only call the tool."
        )
        record.story_messages.append(HumanMessage(content=nudge))
        result2 = record.story_agent.invoke({"messages": record.story_messages})
        record.story_messages = result2["messages"]

    if _campaign.active_combat is not None:
        reply += "\n\n" + _begin_combat(record)
    else:
        # Surface any tool errors so the player can see what went wrong
        for m in result["messages"]:
            if isinstance(m, ToolMessage) and "COMBAT_INITIATED" not in (m.content or ""):
                if hasattr(m, "name") and m.name == "start_combat":
                    reply += (
                        f"\n\n*⚠ Combat failed to start: {m.content}*"
                        "\n*Check that monster names are valid — use list_available_monsters.*"
                    )
                    break

    return reply


def _begin_combat(record: _CampaignRecord) -> str:
    """Transition to combat phase and return the combat intro text."""
    from src.agent.campaign import _campaign
    from src.agent.tools import set_session
    from src.agent.graph import create_agent as _create_combat_agent

    session = _campaign.active_combat
    _campaign.active_combat = None
    record.combat_session = session
    record.phase = "combat"

    set_session(session)
    record.combat_agent = _create_combat_agent(model=_model())
    record.combat_messages = []

    initial_output = session.start()
    lines = [f"⚔ **Combat: {_campaign.combat_setting}**"]
    if initial_output.strip():
        lines.append(initial_output.strip())
    lines.append("*What do you do?*")
    return "\n\n".join(lines)


def _handle_combat(record: _CampaignRecord, user_input: str) -> str:
    from src.agent.campaign import _campaign
    from src.combat import _is_dead

    session = record.combat_session
    state = session.get_state_description()

    record.combat_messages.append(HumanMessage(
        content=f"Current state:\n{state}\n\nInstruction: {user_input}"
    ))
    result = record.combat_agent.invoke({"messages": record.combat_messages})
    record.combat_messages = result["messages"]
    reply = result["messages"][-1].content

    leftover = session._take_output()
    if leftover.strip():
        reply += f"\n\n{leftover.strip()}"

    if session.is_game_over:
        winner = session.winner or "unknown"
        combat_result = (
            "The players won the battle!"
            if winner == "players"
            else "The party was defeated."
        )
        _campaign.last_combat_result = combat_result
        _campaign.players = [p for p in _campaign.players if not _is_dead(p)]

        record.combat_session = None
        record.phase = "story"

        followup = HumanMessage(
            content=f"The combat has ended. Result: {combat_result}. Continue the story."
        )
        record.story_messages.append(followup)
        result = record.story_agent.invoke({"messages": record.story_messages})
        record.story_messages = result["messages"]
        story_reply = result["messages"][-1].content
        reply += f"\n\n---\n\n{story_reply}"

    return reply


# ── Frontend ───────────────────────────────────────────────────────────────────

@app.get("/")
def serve_frontend():
    if not _FRONTEND.exists():
        return JSONResponse(
            status_code=503,
            content={"detail": "Frontend not found. Build the frontend first."},
        )
    return FileResponse(str(_FRONTEND))
