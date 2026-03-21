from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.classes._base import (
    Class, _HALF_CASTER_SLOTS,
)


class Ranger(Class):
    RANGER_SUBCLASSES = ["Beast Master", "Fey Wanderer", "Gloom Stalker", "Hunter"]
    RANGER_FIGHTING_STYLES = [
        "Archery", "Blind Fighting", "Defense", "Druidic Warrior",
        "Thrown Weapon Fighting", "Two-Weapon Fighting",
    ]
    FAVORED_ENEMY_TYPES = [
        "Aberrations", "Beasts", "Celestials", "Constructs", "Dragons",
        "Elementals", "Fey", "Fiends", "Giants", "Monstrosities",
        "Oozes", "Plants", "Undead",
    ]

    def __init__(self, level):
        super().__init__(name="Ranger", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 10
        self.primary_ability = "Dexterity or Wisdom"
        self.spellcasting_ability = "Wisdom"
        self.spell_slots = dict(_HALF_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_HALF_CASTER_SLOTS[level - 1])
        self.proficiencies["Armor"] = ["Light", "Medium", "Shield"]
        self.proficiencies["Weapons"] = ["Simple", "Martial"]
        self.proficiencies["Saving Throws"] = ["Strength", "Dexterity"]
        self.proficiencies["Skills"] = []
        self.completed_levelup_to = 1

    def _set_skill_proficiencies(self, character: Character, choices):
        character.proficiencies["Skills"] += choices

    def _set_subclass(self, character: Character, choices):
        self.subclass = choices[0]

    def _apply_fighting_style(self, character: Character, choices):
        character.special_traits.append(f"Fighting Style: {choices[0]}")

    def _apply_weapon_mastery(self, character: Character, choices):
        character.weapon_mastery += choices

    def _apply_favored_enemy(self, character: Character, choices):
        character.special_traits.append(
            f"Favored Enemy: {choices[0]}. You have Advantage on Wisdom saving throws against "
            f"{choices[0]} and can always get a Hunter's Mark against them (no slot expended, 1/long rest)."
        )

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 150
        else:
            character.add_item([StuddedLeatherArmor(), Shortsword(quantity=2), Longbow(), Quiver(), Arrows(quantity=20), ExplorersPack()])
            character.gold += 7

    def _apply_level(self, character: Character, level: int):
        if level == 2:
            character.todo.append({
                "Text": "Choose a Ranger Fighting Style.",
                "Options": self.RANGER_FIGHTING_STYLES,
                "Function": self._apply_fighting_style,
            })
            character.special_traits.append(
                "Deft Explorer: Gain Expertise in one skill you are proficient in. "
                "Also gain one of: Climb speed equals movement, Swim speed equals movement, "
                "or difficult terrain in natural environments doesn't cost extra movement."
            )
        elif level == 3:
            character.todo.append({
                "Text": "Choose your Ranger subclass (Ranger Archetype).",
                "Options": self.RANGER_SUBCLASSES,
                "Function": self._set_subclass,
            })
            character.special_traits.append(
                "Tireless: As a Bonus Action, gain 1d8 + Wisdom modifier Temporary HP. "
                "Usable a number of times equal to your Proficiency Bonus per Short Rest."
            )
        elif level == 5:
            character.special_traits.append("Extra Attack: You can attack twice when you take the Attack action.")
        elif level == 6:
            character.special_traits.append("Roving: Your speed increases by 10 feet. You gain Climb and Swim speeds equal to your movement speed.")
        elif level == 9:
            character.special_traits.append("Conjure Barrage: You can cast Conjure Barrage without expending a spell slot (once per Short Rest).")
        elif level == 14:
            character.special_abilities.append(Spell(
                name="Nature's Veil",
                casting_time="Bonus Action", range_="Self", components=[],
                duration="Until the start of your next turn",
                description="You become Invisible until the start of your next turn.",
                uses_left=None, cooldown=None,
            ))
            character.special_traits.append("Nature's Veil: Become Invisible as a Bonus Action (uses = Proficiency Bonus per Long Rest).")
        elif level == 17:
            character.special_traits.append(
                "Precise Hunter: You have Advantage on attack rolls against creatures marked "
                "by your Hunter's Mark."
            )
        elif level == 18:
            character.special_traits.append(
                "Feral Senses: You don't have Disadvantage on attack rolls against creatures you "
                "can't see. You are also aware of invisible creatures within 30 feet."
            )
        elif level == 20:
            character.special_traits.append(
                "Foe Slayer: Once per turn, add your Wisdom modifier to the attack roll or damage "
                "roll of an attack against your Favored Enemy."
            )
        self.spell_slots = dict(_HALF_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_HALF_CASTER_SLOTS[level - 1])
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
                    "(Studded Leather Armor, 2 Shortswords, Longbow, Quiver, 20 Arrows, Explorer's Pack, 7 GP) or (150 GP)"
                ),
                "Options": ["Starting Equipment", "Gold"],
                "Function": self.select_starting_equipment,
            },
            {
                "Text": "Choose 3 skills: Animal Handling, Athletics, Insight, Investigation, Nature, Perception, Stealth, Survival.",
                "Options": ["Animal Handling", "Athletics", "Insight", "Investigation", "Nature", "Perception", "Stealth", "Survival"],
                "Choices": 3,
                "Function": self._set_skill_proficiencies,
            },
            {
                "Text": "Choose 2 weapons to gain Weapon Mastery in.",
                "Options": ["Battleaxe", "Flail", "Glaive", "Greataxe", "Greatsword", "Halberd", "Handaxe", "Javelin", "Lance", "Light Hammer", "Longsword", "Maul", "Morningstar", "Pike", "Rapier", "Scimitar", "Shortsword", "Trident", "Warhammer", "War Pick", "Whip", "Light Crossbow", "Hand Crossbow", "Heavy Crossbow", "Longbow", "Shortbow"],
                "Choices": 2,
                "Function": self._apply_weapon_mastery,
            },
            {
                "Text": "Choose a Favored Enemy type.",
                "Options": self.FAVORED_ENEMY_TYPES,
                "Function": self._apply_favored_enemy,
            },
        ])
        return character

    def level_up(self, character: Character):
        super().level_up(character)
        self._apply_level(character, self.level)
        return character
