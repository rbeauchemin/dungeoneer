from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.common import dnd_skills, artisans_tools
from src.classes._base import (
    Class, _FULL_CASTER_SLOTS, _HALF_CASTER_SLOTS,
    _WARLOCK_PACT_SLOTS, _FIGHTING_STYLES,
)


class Cleric(Class):
    CLERIC_SUBCLASSES = ["Life Domain", "Light Domain", "Trickery Domain", "War Domain"]

    def __init__(self, level):
        super().__init__(name="Cleric", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 8
        self.primary_ability = "Wisdom"
        self.spellcasting_ability = "Wisdom"
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.proficiencies["Armor"] = ["Light", "Medium", "Shield"]
        self.proficiencies["Weapons"] = ["Simple"]
        self.proficiencies["Saving Throws"] = ["Wisdom", "Charisma"]
        self.proficiencies["Skills"] = []
        self.completed_levelup_to = 1

    def _set_skill_proficiencies(self, character: Character, choices):
        character.proficiencies["Skills"] += choices

    def _set_subclass(self, character: Character, choices):
        self.subclass = choices[0]

    def _apply_divine_order(self, character: Character, choices):
        if "Protector" in choices:
            character.proficiencies["Armor"] += ["Heavy"]
            character.proficiencies["Weapons"] += ["Martial"]
        else:
            character.proficiencies["Skills"] += choices[1:]

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 110
        else:
            character.add_item([ChainShirt(), Shield(), Mace(), HolySymbol(), ScholarsPack()])
            character.gold += 7

    def _apply_level(self, character: Character, level: int):
        if level == 2:
            channel_uses = [2,2,2,2,2,3,3,3,3,3,4,4,4,4,4,4,4,5,5,5]
            character.special_abilities.append(Spell(
                name="Channel Divinity",
                casting_time="Action", range_="Self", components=[],
                duration="Instantaneous",
                description=(
                    "You channel divine energy to fuel magical effects. "
                    "You have Turn Undead and one effect from your subclass. "
                    "Turn Undead: each undead that can see or hear you must make a Wisdom save "
                    "or be Turned for 1 minute."
                ),
                uses_left=channel_uses[self.level - 1],
                cooldown="Short Rest",
            ))
        elif level == 3:
            character.todo.append({
                "Text": "Choose your Divine Domain (Cleric subclass).",
                "Options": self.CLERIC_SUBCLASSES,
                "Function": self._set_subclass,
            })
        elif level == 5:
            character.special_traits.append(
                "Sear Undead: When you use Turn Undead, undead that aren't turned "
                "take Radiant damage equal to your Wisdom modifier (minimum 1)."
            )
        elif level == 7:
            character.special_traits.append(
                "Blessed Strikes: When a cantrip damages a creature or you hit with a weapon "
                "attack, you can deal an extra 1d8 Radiant or Necrotic damage once per turn."
            )
        elif level == 10:
            character.special_abilities.append(Spell(
                name="Divine Intervention",
                casting_time="Action", range_="Self", components=[],
                duration="Instantaneous",
                description=(
                    "You call on your deity to intervene. You can cast any Cleric spell "
                    "without expending a spell slot or requiring material components."
                ),
                uses_left=1, cooldown="Long Rest",
            ))
        elif level == 14:
            character.special_traits.append("Improved Blessed Strikes: Blessed Strikes damage increases to 2d8.")
        elif level == 20:
            character.special_abilities.append(Spell(
                name="Greater Divine Intervention",
                casting_time="Action", range_="Self", components=[],
                duration="Instantaneous",
                description=(
                    "You can cast any spell from the Divine Magic spell list without "
                    "expending a spell slot or requiring material components."
                ),
                uses_left=1, cooldown="Long Rest",
            ))
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.completed_levelup_to = level

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        self.completed_levelup_to = 1
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        for lv in range(2, self.level + 1):
            self._apply_level(character, lv)
        character.todo.extend([
            {
                "Text": (
                    "Select starting equipment or gold: "
                    "(Chain Shirt, Shield, Mace, Holy Symbol, Scholar's Pack, 7 GP) or (110 GP)"
                ),
                "Options": ["Starting Equipment", "Gold"],
                "Function": self.select_starting_equipment,
            },
            {
                "Text": "Choose 2 skills: History, Insight, Medicine, Persuasion, Religion.",
                "Options": ["History", "Insight", "Medicine", "Persuasion", "Religion"],
                "Choices": 2,
                "Function": self._set_skill_proficiencies,
            },
            {
                "Text": (
                    "Choose Divine Order: Protector (Heavy Armor + Martial Weapon proficiency) "
                    "or Thaumaturge (choose 2 skills from Arcana, History, Nature, Religion)."
                ),
                "Options": ["Protector", "Thaumaturge", "Arcana", "History", "Nature", "Religion"],
                "Function": self._apply_divine_order,
            },
        ])
        return character

    def level_up(self, character: Character):
        self.level += 1
        self._apply_level(character, self.level)
        character.classes = [cls for cls in character.classes if cls.name != self.name] + [self]
        return character


# ── Druid ──────────────────────────────────────────────────────────────────

