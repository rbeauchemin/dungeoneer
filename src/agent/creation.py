"""Character creation tools and agent.

The creation agent guides the user through building a D&D 5e character
one decision at a time.  It uses the Character/class/species constructors
from the main codebase, then resolves todo items (skill choices, equipment
selections, etc.) conversationally before handing the finished character
back to the campaign.
"""

from __future__ import annotations

import importlib
from typing import Optional

from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from src.agent.campaign import _campaign

# ── Static option lists (populated from the codebase) ─────────────────────────

AVAILABLE_SPECIES = [
    "Aasimar", "Dragonborn", "Dwarf", "Elf", "Gnome",
    "Goliath", "Halfling", "Human", "Orc", "Tiefling",
]

AVAILABLE_BACKGROUNDS = [
    "Acolyte", "Artisan", "Charlatan", "Criminal", "Entertainer",
    "Farmer", "Guard", "Guide", "Hermit", "Merchant", "Noble",
    "Sage", "Sailor", "Scribe", "Soldier", "Wayfarer",
]

AVAILABLE_CLASSES = [
    "Artificer", "Barbarian", "Bard", "Cleric", "Druid",
    "Fighter", "Monk", "Paladin", "Ranger", "Rogue",
    "Sorcerer", "Warlock", "Wizard",
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _char():
    """Return the character currently under construction (or None)."""
    return _campaign.pending_character


def _next_todo_item():
    """Peek at the next pending todo item (last in the LIFO list)."""
    char = _char()
    if char is None or not char.todo:
        return None
    return char.todo[-1]


# ── Tools ──────────────────────────────────────────────────────────────────────

@tool
def list_options(category: str) -> str:
    """List available options for a character creation category.
    category must be one of: 'species', 'backgrounds', 'classes'."""
    if category == "species":
        return "Available species:\n" + "\n".join(f"  - {s}" for s in AVAILABLE_SPECIES)
    if category == "backgrounds":
        return "Available backgrounds:\n" + "\n".join(f"  - {b}" for b in AVAILABLE_BACKGROUNDS)
    if category == "classes":
        return "Available classes:\n" + "\n".join(f"  - {c}" for c in AVAILABLE_CLASSES)
    return f"Unknown category '{category}'. Use: species, backgrounds, or classes."


@tool
def create_character(
    name: str,
    species: str,
    background: str,
    class_name: str,
    level: int = 1,
) -> str:
    """Create a character with the given traits.
    After creation, call get_next_todo() to see what decisions remain."""
    if species not in AVAILABLE_SPECIES:
        return f"Unknown species '{species}'. Use list_options('species') to see valid choices."
    if background not in AVAILABLE_BACKGROUNDS:
        return f"Unknown background '{background}'. Use list_options('backgrounds')."
    if class_name not in AVAILABLE_CLASSES:
        return f"Unknown class '{class_name}'. Use list_options('classes')."

    try:
        mod = importlib.import_module(f"src.classes.{class_name.lower()}")
        cls = getattr(mod, class_name)
    except (ImportError, AttributeError) as exc:
        return f"Could not load class '{class_name}': {exc}"

    try:
        from src.creatures.character import Character

        char = Character(
            name=name,
            species=species,
            background=background,
            classes=[cls(level)],
        )
        _campaign.pending_character = char

        pending = sum(1 for t in char.todo if isinstance(t, dict))
        species_name = type(char.species).__name__
        bg_name = type(char.background).__name__
        return (
            f"Character '{name}' created!\n"
            f"  Species: {species_name}  Background: {bg_name}  Class: {class_name} {level}\n"
            f"  HP: {char.current_hp}/{char.max_hp}  Speed: {char.speed}ft\n"
            f"  {pending} decision(s) still need to be made."
        )
    except Exception as exc:
        return f"Error creating character: {exc}"


@tool
def get_next_todo() -> str:
    """Get the next pending character-creation decision.
    Returns the prompt text, all available options, and how many to choose."""
    char = _char()
    if char is None:
        return "No character is currently being created. Call create_character() first."
    if not char.todo:
        return "No pending decisions — the character is ready to adventure!"

    item = _next_todo_item()
    if isinstance(item, str):
        return f"Note: {item}\n(Call resolve_todo with any value to acknowledge.)"

    if isinstance(item, dict):
        text = item.get("Text", "Make a choice.")
        options: list = item.get("Options", [])
        n = item.get("Choices", 1)
        allow_same = item.get("AllowSame", False)

        # Show up to 40 options (spell lists can be very long)
        shown = options[:40]
        opts_block = "\n".join(f"  {i + 1}. {o}" for i, o in enumerate(shown))
        more = f"\n  … and {len(options) - 40} more options" if len(options) > 40 else ""

        return (
            f"Decision ({n} choice{'s' if n != 1 else ''}"
            f"{', duplicates allowed' if allow_same else ''}):\n"
            f"{text}\n\n"
            f"Options:\n{opts_block}{more}"
        )

    return "Unknown todo format."


@tool
def resolve_todo(choices: str) -> str:
    """Resolve the next pending decision with the given choice(s).
    choices: comma-separated option names exactly as shown in get_next_todo().
    Example: resolve_todo('Athletics, Perception')"""
    char = _char()
    if char is None:
        return "No character is being created."
    if not char.todo:
        return "No pending decisions to resolve."

    item = _next_todo_item()

    # Acknowledge a plain string note
    if isinstance(item, str):
        char.todo.pop()
        return f"Acknowledged: {item}"

    if isinstance(item, dict):
        options: list = item.get("Options", [])
        n: int = item.get("Choices", 1)
        allow_same: bool = item.get("AllowSame", False)

        choice_list = [c.strip() for c in choices.split(",") if c.strip()]

        # Validate each choice exists
        for c in choice_list:
            if c not in options:
                close = [o for o in options if c.lower() in o.lower()][:3]
                hint = f"  Did you mean: {close}?" if close else ""
                return f"'{c}' is not a valid option.{hint}\nCall get_next_todo() to see valid options."

        if not allow_same and len(set(choice_list)) != len(choice_list):
            return "Cannot select the same option twice."

        if len(choice_list) != n:
            return f"Expected {n} choice(s), got {len(choice_list)}."

        char.todo.pop()
        try:
            item["Function"](char, choice_list)
            remaining = len(char.todo)
            return (
                f"Resolved! Selected: {', '.join(choice_list)}\n"
                f"{remaining} decision(s) remaining."
            )
        except Exception as exc:
            char.todo.append(item)   # put it back on failure
            return f"Error applying choice: {exc}"

    return "Unknown todo format."


@tool
def get_character_summary() -> str:
    """Return a summary of the character currently being built."""
    char = _char()
    if char is None:
        return "No character is being created yet."

    species_name = type(char.species).__name__
    bg_name = type(char.background).__name__
    classes_str = ", ".join(f"{c.name} {c.level}" for c in char.classes)
    scores = "  ".join(
        f"{k[:3]}: {v}" for k, v in char.ability_scores.items()
    )
    pending = len([t for t in char.todo if isinstance(t, dict)])

    profs = char.proficiencies.get("Skills", [])
    profs_str = ", ".join(profs) if profs else "none yet"

    return (
        f"Name: {char.name}\n"
        f"Species: {species_name}  Background: {bg_name}  Class: {classes_str}\n"
        f"HP: {char.current_hp}/{char.max_hp}  Speed: {char.speed}ft  Level: {char.level}\n"
        f"Ability scores: {scores}\n"
        f"Skill proficiencies: {profs_str}\n"
        f"Pending decisions: {pending}"
    )


_CREATION_TOOLS = [
    list_options,
    create_character,
    get_next_todo,
    resolve_todo,
    get_character_summary,
]

_CREATION_SYSTEM = """\
You are a friendly D&D 5e character-creation guide helping a player build their
first character for a campaign.

Your job:
1. Learn what kind of character the player wants to play (ask about personality,
   fighting style, fantasy archetype — *not* raw stats).
2. Map their vision to a species, background, and class. Use list_options() if
   you want to confirm what is available.
3. Call create_character() once you have enough information.
4. Work through every pending decision with get_next_todo() and resolve_todo().
   - List every option verbatim as shown in get_next_todo() when asking the player to choose.
   - Suggest and summarize the top handful of choices in plain English.
5. When get_next_todo() says "No pending decisions", call get_character_summary()
   and present the finished character warmly to the player.

Tone: enthusiastic, encouraging, brief. Never use game jargon without explaining it.
"""


def create_creation_agent(model: str = "gemma4"):
    """Return a LangGraph agent for interactive character creation."""
    if model.startswith("claude"):
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model=model)
    else:
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model=model)
    return create_react_agent(llm, _CREATION_TOOLS, prompt=_CREATION_SYSTEM)
