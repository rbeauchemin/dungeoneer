from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.classes._base import (
    Class, _FULL_CASTER_SLOTS,
)


class Sorcerer(Class):
    SORCERER_SUBCLASSES = ["Aberrant Mind", "Clockwork Soul", "Draconic Sorcery", "Wild Magic"]
    METAMAGIC_OPTIONS = [
        "Careful Spell", "Distant Spell", "Empowered Spell", "Extended Spell",
        "Heightened Spell", "Quickened Spell", "Seeking Spell", "Subtle Spell",
        "Transmuted Spell", "Twinned Spell",
    ]
    CANTRIPS_KNOWN = [4, 4, 4, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6]

    def __init__(self, level):
        super().__init__(name="Sorcerer", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 6
        self.primary_ability = "Charisma"
        self.spellcasting_ability = "Charisma"
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.proficiencies["Weapons"] = ["Simple"]
        self.proficiencies["Saving Throws"] = ["Constitution", "Charisma"]
        self.proficiencies["Skills"] = []
        self.sorcery_points = level
        self.completed_levelup_to = 1

    def _set_skill_proficiencies(self, character: Character, choices):
        character.proficiencies["Skills"] += choices

    def _set_subclass(self, character: Character, choices):
        self.subclass = choices[0]

    def _apply_metamagic(self, character: Character, choices):
        if not hasattr(character, "metamagic"):
            character.metamagic = []
        character.metamagic += choices

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 50
        else:
            character.add_item([Dagger(quantity=2), ComponentPouch(), ArcaneFocus(), BurglarsPack()])
            character.gold += 28

    def _apply_level(self, character: Character, level: int):
        self.sorcery_points = level
        if level == 2:
            character.special_traits.append(
                f"Font of Magic: You have {level} Sorcery Points (regain on Long Rest). "
                "Convert spell slots to Sorcery Points (1 point per slot level) or vice versa "
                "(spend points equal to the slot level to create a slot, max 5th level)."
            )
            character.todo.append({
                "Text": "Choose 2 Metamagic options.",
                "Options": self.METAMAGIC_OPTIONS,
                "Choices": 2,
                "Function": self._apply_metamagic,
            })
        elif level == 3:
            character.todo.append({
                "Text": "Choose your Sorcerer subclass (Sorcerous Origin).",
                "Options": self.SORCERER_SUBCLASSES,
                "Function": self._set_subclass,
            })
            character.special_traits.append(
                "Sorcery Incarnate: While Innate Sorcery is active, you can apply two Metamagic "
                "options to a single spell instead of one."
            )
        elif level == 5:
            character.special_traits.append(
                "Sorcerous Restoration: When you finish a Short Rest, you regain 4 expended Sorcery Points."
            )
        elif level == 7:
            character.special_traits.append(
                "Arcane Apotheosis: While Innate Sorcery is active, once per turn you can apply "
                "one Metamagic option to a spell without spending Sorcery Points."
            )
        elif level == 10:
            character.todo.append({
                "Text": "Choose a 3rd Metamagic option.",
                "Options": self.METAMAGIC_OPTIONS,
                "Function": self._apply_metamagic,
            })
        elif level == 17:
            character.todo.append({
                "Text": "Choose a 4th Metamagic option.",
                "Options": self.METAMAGIC_OPTIONS,
                "Function": self._apply_metamagic,
            })
        elif level == 20:
            character.special_traits.append(
                "Arcane Apotheosis (Improved): While Innate Sorcery is active, you can apply any "
                "number of Metamagic options for free each turn."
            )
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.completed_levelup_to = level

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        self.completed_levelup_to = 1
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        character.special_abilities.append(Spell(
            name="Innate Sorcery",
            casting_time="Bonus Action", range_="Self", components=[],
            duration="1 minute",
            description=(
                "You emanate an aura of magical power. For 1 minute: you have Advantage on "
                "spell attack rolls, and creatures have Disadvantage on saving throws against "
                "your spells that deal damage."
            ),
            uses_left=1, cooldown="Long Rest",
        ))
        for lv in range(2, self.level + 1):
            self._apply_level(character, lv)
        character.todo.extend([
            {
                "Text": (
                    "Select starting equipment or gold: "
                    "(2 Daggers, Component Pouch, Arcane Focus, Burglar's Pack, 28 GP) or (50 GP)"
                ),
                "Options": ["Starting Equipment", "Gold"],
                "Function": self.select_starting_equipment,
            },
            {
                "Text": "Choose 2 skills: Arcana, Deception, Insight, Intimidation, Persuasion, Religion.",
                "Options": ["Arcana", "Deception", "Insight", "Intimidation", "Persuasion", "Religion"],
                "Choices": 2,
                "Function": self._set_skill_proficiencies,
            },
        ])
        return character

    def level_up(self, character: Character):
        super().level_up(character)
        self._apply_level(character, self.level)
        return character
