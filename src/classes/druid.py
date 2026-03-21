from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.classes._base import (
    Class, _FULL_CASTER_SLOTS,
)


class Druid(Class):
    DRUID_SUBCLASSES = ["Circle of the Land", "Circle of the Moon", "Circle of the Sea", "Circle of the Stars"]

    def __init__(self, level):
        super().__init__(name="Druid", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 8
        self.primary_ability = "Wisdom"
        self.spellcasting_ability = "Wisdom"
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.proficiencies["Armor"] = ["Light", "Medium", "Shield"]
        self.proficiencies["Weapons"] = ["Simple"]
        self.proficiencies["Tools"] = ["Herbalism Kit"]
        self.proficiencies["Saving Throws"] = ["Intelligence", "Wisdom"]
        self.proficiencies["Skills"] = []
        self.wild_shape_uses = 2
        self.completed_levelup_to = 1

    def _set_skill_proficiencies(self, character: Character, choices):
        character.proficiencies["Skills"] += choices

    def _set_subclass(self, character: Character, choices):
        self.subclass = choices[0]

    def _apply_primal_order(self, character: Character, choices):
        if "Warden" in choices:
            character.proficiencies["Armor"] += ["Heavy"]
            character.proficiencies["Weapons"] += ["Martial"]
        else:
            character.proficiencies["Skills"] += choices[1:]

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 50
        else:
            character.add_item([LeatherArmor(), Shield(), Sickle(), DruidicFocus(), HerbalismKit(), ExplorersPack()])

    def _apply_level(self, character: Character, level: int):
        if level == 2:
            character.special_abilities.append(Spell(
                name="Wild Shape",
                casting_time="Bonus Action", range_="Self", components=[],
                duration="Concentration, up to 1 hour",
                description=(
                    "You magically assume the shape of a Beast with a Challenge Rating "
                    "equal to or less than your allowed CR (1/4 at level 2, 1/2 at level 4, "
                    "1 at level 8). You retain your mental ability scores and can't cast "
                    "spells while transformed."
                ),
                uses_left=2, cooldown="Short Rest",
            ))
            character.todo.append({
                "Text": "Choose your Druid subclass (Druid Circle).",
                "Options": self.DRUID_SUBCLASSES,
                "Function": self._set_subclass,
            })
        elif level == 3:
            character.special_traits.append(
                "Wild Resurgence: Once per turn, if you have no Wild Shape uses, you can expend "
                "a spell slot to regain one use. If you have no spell slots, you can expend a "
                "Wild Shape use to regain one 1st-level spell slot."
            )
        elif level == 7:
            character.special_traits.append(
                "Elemental Fury: Choose Cold, Fire, Lightning, or Thunder. "
                "Once per turn your cantrip or melee attack deals an extra 1d6 damage of that type."
            )
        elif level == 18:
            character.special_traits.append(
                "Beast Spells: You can cast Druid spells while in Wild Shape form, "
                "using verbal and somatic components but not material ones."
            )
        elif level == 20:
            character.special_traits.append(
                "Archdruid: Unlimited Wild Shape uses per day. "
                "You can ignore Concentration for one Wild Shape spell at a time."
            )
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
                    "(Leather Armor, Shield, Sickle, Druidic Focus, Herbalism Kit, Explorer's Pack) or (50 GP)"
                ),
                "Options": ["Starting Equipment", "Gold"],
                "Function": self.select_starting_equipment,
            },
            {
                "Text": "Choose 2 skills: Arcana, Animal Handling, Insight, Medicine, Nature, Perception, Religion, Survival.",
                "Options": ["Arcana", "Animal Handling", "Insight", "Medicine", "Nature", "Perception", "Religion", "Survival"],
                "Choices": 2,
                "Function": self._set_skill_proficiencies,
            },
            {
                "Text": (
                    "Choose Primal Order: Warden (Heavy Armor + Martial Weapon proficiency) "
                    "or Magician (choose 2 skills from Arcana, History, Nature, Religion)."
                ),
                "Options": ["Warden", "Magician", "Arcana", "History", "Nature", "Religion"],
                "Function": self._apply_primal_order,
            },
        ])
        return character

    def level_up(self, character: Character):
        super().level_up(character)
        self._apply_level(character, self.level)
        return character

# ── Fighter ────────────────────────────────────────────────────────────────
