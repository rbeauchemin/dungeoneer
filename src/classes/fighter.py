from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.common import dnd_skills, artisans_tools
from src.classes._base import (
    Class, _FULL_CASTER_SLOTS, _HALF_CASTER_SLOTS,
    _WARLOCK_PACT_SLOTS, _FIGHTING_STYLES,
)


class Fighter(Class):
    FIGHTER_SUBCLASSES = ["Battle Master", "Champion", "Eldritch Knight", "Psi Warrior"]

    def __init__(self, level):
        super().__init__(name="Fighter", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 10
        self.primary_ability = "Strength or Dexterity"
        self.proficiencies["Armor"] = ["Light", "Medium", "Heavy", "Shield"]
        self.proficiencies["Weapons"] = ["Simple", "Martial"]
        self.proficiencies["Saving Throws"] = ["Strength", "Constitution"]
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

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 155
        else:
            character.add_item([ChainMail(), Flail(), Shield(), LightCrossbow(), Bolts(quantity=20), DungeoneersPack()])
            character.gold += 4

    def _apply_level(self, character: Character, level: int):
        if level == 2:
            character.special_abilities.append(Spell(
                name="Action Surge",
                casting_time="Bonus Action", range_="Self", components=[],
                duration="Instantaneous",
                description="On your turn, take one additional action on top of your regular action and possible bonus action.",
                uses_left=1, cooldown="Short Rest",
            ))
        elif level == 3:
            character.todo.append({
                "Text": "Choose your Fighter subclass (Martial Archetype).",
                "Options": self.FIGHTER_SUBCLASSES,
                "Function": self._set_subclass,
            })
        elif level == 5:
            character.special_traits.append("Extra Attack: You can attack twice when you take the Attack action.")
        elif level == 9:
            character.special_abilities.append(Spell(
                name="Indomitable",
                casting_time="Free Action", range_="Self", components=[],
                duration="Instantaneous",
                description="When you fail a saving throw, you can reroll it using the new result.",
                uses_left=1, cooldown="Long Rest",
            ))
            character.special_traits.append(
                "Tactical Master: When you use Weapon Mastery, you can swap one mastery property for Push, Sap, or Slow."
            )
        elif level == 11:
            character.special_traits.append("Extra Attack (2): You can attack three times when you take the Attack action.")
        elif level == 13:
            character.special_traits.append(
                "Studied Attacks: If you miss an attack, you have Advantage on your next attack "
                "roll against that same creature before the end of your next turn."
            )
        elif level == 17:
            for ability in character.special_abilities:
                if ability.name in ("Action Surge", "Indomitable"):
                    ability.uses_left = 2
        elif level == 20:
            character.special_traits.append("Extra Attack (3): You can attack four times when you take the Attack action.")
            for ability in character.special_abilities:
                if ability.name == "Indomitable":
                    ability.uses_left = 3
        self.completed_levelup_to = level

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        self.completed_levelup_to = 1
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        character.special_abilities.append(Spell(
            name="Second Wind",
            casting_time="Bonus Action", range_="Self", components=[],
            duration="Instantaneous",
            description="Regain HP equal to 1d10 + your Fighter level. Usable twice per Short Rest.",
            uses_left=2, cooldown="Short Rest",
        ))
        for lv in range(2, self.level + 1):
            self._apply_level(character, lv)
        character.todo.extend([
            {
                "Text": (
                    "Select starting equipment or gold: "
                    "(Chain Mail, Flail, Shield, Light Crossbow, 20 Bolts, Dungeoneer's Pack, 4 GP) or (155 GP)"
                ),
                "Options": ["Starting Equipment", "Gold"],
                "Function": self.select_starting_equipment,
            },
            {
                "Text": "Choose 2 skills: Acrobatics, Animal Handling, Athletics, History, Insight, Intimidation, Perception, Survival.",
                "Options": ["Acrobatics", "Animal Handling", "Athletics", "History", "Insight", "Intimidation", "Perception", "Survival"],
                "Choices": 2,
                "Function": self._set_skill_proficiencies,
            },
            {
                "Text": "Choose a Fighting Style.",
                "Options": _FIGHTING_STYLES,
                "Function": self._apply_fighting_style,
            },
            {
                "Text": "Choose 3 weapons to gain Weapon Mastery in.",
                "Options": ["Battleaxe", "Flail", "Glaive", "Greataxe", "Greatsword", "Halberd", "Handaxe", "Javelin", "Lance", "Light Hammer", "Longsword", "Maul", "Morningstar", "Pike", "Rapier", "Scimitar", "Shortsword", "Trident", "Warhammer", "War Pick", "Whip", "Light Crossbow", "Hand Crossbow", "Heavy Crossbow", "Longbow", "Shortbow"],
                "Choices": 3,
                "Function": self._apply_weapon_mastery,
            },
        ])
        return character

    def level_up(self, character: Character):
        self.level += 1
        self._apply_level(character, self.level)
        character.classes = [cls for cls in character.classes if cls.name != self.name] + [self]
        return character


# ── Monk ───────────────────────────────────────────────────────────────────

