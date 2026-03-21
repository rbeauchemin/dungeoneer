from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.classes._base import (
    Class, _FULL_CASTER_SLOTS,
)


class Wizard(Class):
    WIZARD_SUBCLASSES = ["Abjurer", "Diviner", "Evoker", "Illusionist"]
    CANTRIPS_KNOWN = [3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5]

    def __init__(self, level):
        super().__init__(name="Wizard", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 6
        self.primary_ability = "Intelligence"
        self.spellcasting_ability = "Intelligence"
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.proficiencies["Weapons"] = ["Simple"]
        self.proficiencies["Saving Throws"] = ["Intelligence", "Wisdom"]
        self.proficiencies["Skills"] = []
        self.completed_levelup_to = 1

    def _set_skill_proficiencies(self, character: Character, choices):
        character.proficiencies["Skills"] += choices

    def _set_subclass(self, character: Character, choices):
        self.subclass = choices[0]

    def _apply_expertise(self, character: Character, choices):
        if not hasattr(character, "expertise"):
            character.expertise = []
        character.expertise += choices

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 110
        else:
            character.add_item([Quarterstaff(), ArcaneFocus(), ComponentPouch(), ScholarsPack()])
            character.gold += 5
            character.special_traits.append(
                "Spellbook: You have a spellbook containing 6 1st-level Wizard spells of your choice."
            )

    def _apply_level(self, character: Character, level: int):
        if level == 2:
            character.todo.append({
                "Text": "Choose your Wizard subclass (Arcane Tradition).",
                "Options": self.WIZARD_SUBCLASSES,
                "Function": self._set_subclass,
            })
            character.todo.append({
                "Text": "Scholar: Choose 1 skill to gain Expertise in (Arcana or History).",
                "Options": ["Arcana", "History"],
                "Function": self._apply_expertise,
            })
            character.special_traits.append(
                "Memorize Spell: Once per day you can study a spell from another Wizard's spellbook "
                "and add it to your own without the usual gold cost."
            )
        elif level == 3:
            character.special_traits.append(
                "Cantrip Formulas: During a Short Rest, you can replace one Wizard cantrip you know "
                "with another Wizard cantrip."
            )
        elif level == 18:
            character.special_abilities.append(Spell(
                name="Spell Mastery",
                casting_time="Special", range_="Self", components=[],
                duration="Permanent",
                description=(
                    "Choose one 1st-level and one 2nd-level Wizard spell in your spellbook. "
                    "You can cast each of those spells at their lowest level without expending a spell slot. "
                    "You can change your chosen spells after a Long Rest."
                ),
            ))
        elif level == 20:
            character.special_abilities.append(Spell(
                name="Signature Spells",
                casting_time="Special", range_="Self", components=[],
                duration="Permanent",
                description=(
                    "Choose two 3rd-level Wizard spells in your spellbook as your signature spells. "
                    "You always have them prepared and can cast each of them once without expending "
                    "a spell slot (regain uses on Long Rest)."
                ),
                uses_left=2, cooldown="Long Rest",
            ))
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.completed_levelup_to = level

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        self.completed_levelup_to = 1
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        arcane_recovery_slots = (self.level + 1) // 2
        character.special_abilities.append(Spell(
            name="Arcane Recovery",
            casting_time="Special", range_="Self", components=[],
            duration="Instantaneous",
            description=(
                f"Once per day during a Short Rest, you can recover expended spell slots "
                f"with a combined level up to {arcane_recovery_slots} (max 5th level each)."
            ),
            uses_left=1, cooldown="Long Rest",
        ))
        character.special_traits.append(
            "Spellbook: You possess a spellbook containing your prepared Wizard spells. "
            "You can prepare a number of spells equal to your Intelligence modifier + your Wizard level."
        )
        for lv in range(2, self.level + 1):
            self._apply_level(character, lv)
        character.todo.extend([
            {
                "Text": (
                    "Select starting equipment or gold: "
                    "(Quarterstaff, Arcane Focus, Component Pouch, Scholar's Pack, Spellbook, 5 GP) or (110 GP)"
                ),
                "Options": ["Starting Equipment", "Gold"],
                "Function": self.select_starting_equipment,
            },
            {
                "Text": "Choose 2 skills: Arcana, History, Insight, Investigation, Medicine, Religion.",
                "Options": ["Arcana", "History", "Insight", "Investigation", "Medicine", "Religion"],
                "Choices": 2,
                "Function": self._set_skill_proficiencies,
            },
        ])
        return character

    def level_up(self, character: Character):
        super().level_up(character)
        self._apply_level(character, self.level)
        return character
