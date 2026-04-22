"""FastAPI server for the Dungeoneer web frontend.

Run::

    uvicorn src.agent.server:app --reload --port 8000

Then open http://localhost:8000 in a browser.

Requires ANTHROPIC_API_KEY in the environment or a .env file.
"""

from __future__ import annotations

import logging
import os
import pathlib
import cloudpickle as pickle
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

log = logging.getLogger(__name__)

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
_SAVE_DIR = pathlib.Path(__file__).parent.parent.parent / "campaigns"
_disk_loaded = False  # lazy-load flag; campaigns are scanned once on first list call


# ── Persistence ────────────────────────────────────────────────────────────────

def _persist(record: _CampaignRecord) -> None:
    """Pickle campaign state to disk after every message so restarts are safe."""
    _SAVE_DIR.mkdir(exist_ok=True)
    # If we're mid-combat the thread can't be restored, so rewind to story phase.
    save_phase = "story" if record.phase == "combat" else record.phase
    data = {
        "id": record.id,
        "name": record.name,
        "created_at": record.created_at,
        "phase": save_phase,
        "display_messages": record.display_messages,
        "creation_messages": record.creation_messages,
        "story_messages": record.story_messages,
        "players": record.players,
        "pending_character": record.pending_character,
        "setting_brief": record.setting_brief,
        "current_scene": record.current_scene,
        "story_log": record.story_log,
        "last_combat_result": record.last_combat_result,
        "combat_setting": record.combat_setting,
    }
    path = _SAVE_DIR / f"{record.id}.pkl"
    try:
        with open(path, "wb") as fh:
            pickle.dump(data, fh)
    except Exception:
        log.exception("Failed to persist campaign %s", record.id)


def _restore_from_disk(path: pathlib.Path) -> _CampaignRecord | None:
    """Load a pickled campaign snapshot and return a usable _CampaignRecord.

    Agents are *not* recreated here — they are built lazily the next time the
    campaign receives a message, keeping startup fast.
    """
    try:
        with open(path, "rb") as fh:
            data = pickle.load(fh)
    except Exception:
        log.exception("Failed to load campaign from %s", path)
        return None

    record = _CampaignRecord(id=data["id"])
    record.name = data.get("name", "Campaign")
    record.created_at = data.get("created_at", datetime.now().isoformat())
    record.phase = data.get("phase", "setting")
    record.display_messages = data.get("display_messages", [])
    record.creation_messages = data.get("creation_messages", [])
    record.story_messages = data.get("story_messages", [])
    record.players = data.get("players", [])
    record.pending_character = data.get("pending_character")
    record.setting_brief = data.get("setting_brief", "")
    record.current_scene = data.get("current_scene", "An unknown location.")
    record.story_log = data.get("story_log", [])
    record.last_combat_result = data.get("last_combat_result", "")
    record.combat_setting = data.get("combat_setting", "")
    return record


def _load_saved_campaigns() -> None:
    """Scan the save directory and register any campaigns not already in memory."""
    if not _SAVE_DIR.exists():
        return
    for path in sorted(_SAVE_DIR.glob("*.pkl")):
        cid = path.stem
        if cid not in _campaigns:
            record = _restore_from_disk(path)
            if record is not None:
                _campaigns[cid] = record


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
    global _disk_loaded
    if not _disk_loaded:
        _load_saved_campaigns()
        _disk_loaded = True
    return [
        _summary(r)
        for r in sorted(_campaigns.values(), key=lambda r: r.created_at)
    ]


@app.delete("/api/campaigns/{campaign_id}")
def delete_campaign(campaign_id: str):
    """Delete a campaign from memory and disk."""
    _get(campaign_id)  # raises 404 if not found
    del _campaigns[campaign_id]
    path = _SAVE_DIR / f"{campaign_id}.pkl"
    try:
        path.unlink(missing_ok=True)
    except Exception:
        log.exception("Failed to delete campaign file %s", path)
    return {"ok": True}


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
    _persist(record)

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
    from src.agent.creation import create_creation_agent

    # Recreate agent if it was lost across a server restart
    if record.creation_agent is None:
        record.creation_agent = create_creation_agent(model=_model())

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

    # Check whether creation completed during this turn
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
    from src.agent.story_tools import create_story_agent
    from langchain_core.messages import ToolMessage

    # Recreate agent if it was lost across a server restart
    if record.story_agent is None:
        record.story_agent = create_story_agent(model=_model())

    record.story_messages.append(HumanMessage(content=user_input))
    prev_len = len(record.story_messages)
    result = record.story_agent.invoke({"messages": record.story_messages})
    record.story_messages = result["messages"]
    reply = result["messages"][-1].content
    new_messages = result["messages"][prev_len:]

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
        for m in new_messages:
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

    session = _campaign.active_combat
    _campaign.active_combat = None
    record.combat_session = session
    record.phase = "combat"

    set_session(session)

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

    # Pass the player's input directly to the game engine — no LLM translation loop.
    mechanical = session.send(user_input)
    leftover = session._take_output()
    if leftover.strip():
        mechanical += f"\n\n{leftover.strip()}"

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
            content=(
                f"[COMBAT ENDED] Result: {combat_result}\n"
                f"Last turn: {mechanical}\n\n"
                f"Narrate the end of the battle and continue the story."
            )
        )
        record.story_messages.append(followup)
        result2 = record.story_agent.invoke({"messages": record.story_messages})
        record.story_messages = result2["messages"]
        return result2["messages"][-1].content

    return mechanical


# ── Frontend ───────────────────────────────────────────────────────────────────

@app.get("/")
def serve_frontend():
    if not _FRONTEND.exists():
        return JSONResponse(
            status_code=503,
            content={"detail": "Frontend not found. Build the frontend first."},
        )
    return FileResponse(str(_FRONTEND))
