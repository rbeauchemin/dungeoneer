from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.common import dnd_skills, artisans_tools
from src.classes._base import (
    Class, _FULL_CASTER_SLOTS, _HALF_CASTER_SLOTS,
    _WARLOCK_PACT_SLOTS, _FIGHTING_STYLES,
)


class Paladin(Class):
    PALADIN_SUBCLASSES = ["Oath of Devotion", "Oath of Glory", "Oath of the Ancients", "Oath of Vengeance"]
    PALADIN_FIGHTING_STYLES = [
        "Blessed Warrior", "Blind Fighting", "Defense",
        "Dueling", "Great Weapon Fighting", "Interception", "Protection",
    ]

    def __init__(self, level):
        super().__init__(name="Paladin", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 10
        self.primary_ability = "Strength and Charisma"
        self.spellcasting_ability = "Charisma"
        self.spell_slots = dict(_HALF_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_HALF_CASTER_SLOTS[level - 1])
        self.proficiencies["Armor"] = ["Light", "Medium", "Heavy", "Shield"]
        self.proficiencies["Weapons"] = ["Simple", "Martial"]
        self.proficiencies["Saving Throws"] = ["Wisdom", "Charisma"]
        self.proficiencies["Skills"] = []
        self.lay_on_hands_pool = 5 * level
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
            character.gold += 150
        else:
            character.add_item([ChainMail(), Shield(), Longsword(), HolySymbol(), ScholarsPack()])
            character.gold += 9

    def _apply_level(self, character: Character, level: int):
        if level == 2:
            character.special_traits.append(
                "Paladin's Smite: When you hit with a melee weapon or Unarmed Strike, expend a spell slot "
                "(Bonus Action) for extra Radiant damage: 2d8 for a 1st-level slot, +1d8 per slot level above 1st."
            )
            character.todo.append({
                "Text": "Choose a Paladin Fighting Style.",
                "Options": self.PALADIN_FIGHTING_STYLES,
                "Function": self._apply_fighting_style,
            })
        elif level == 3:
            character.special_traits.append("Divine Health: You are immune to disease.")
            character.special_abilities.append(Spell(
                name="Channel Divinity",
                casting_time="Action", range_="Self", components=[],
                duration="Instantaneous",
                description=(
                    "Channel divine energy for an effect from your Sacred Oath. "
                    "Sacred Weapon (Devotion): Imbue a weapon with +Cha modifier to attack rolls "
                    "and bright light (20 ft) for 10 minutes."
                ),
                uses_left=2, cooldown="Short Rest",
            ))
            character.todo.append({
                "Text": "Choose your Paladin subclass (Sacred Oath).",
                "Options": self.PALADIN_SUBCLASSES,
                "Function": self._set_subclass,
            })
        elif level == 5:
            character.special_traits.append("Extra Attack: You can attack twice when you take the Attack action.")
            character.special_traits.append("Faithful Steed: Cast Find Steed without expending a spell slot.")
        elif level == 6:
            cha_mod = max(1, (character.ability_scores.get("Charisma", 10) - 10) // 2)
            character.special_traits.append(
                f"Aura of Protection: You and friendly creatures within 10 feet add +{cha_mod} "
                "(your Charisma modifier) to all saving throws while you are conscious."
            )
        elif level == 7:
            character.special_traits.append(
                "Aura of Courage: You and friendly creatures within 10 feet are immune to the "
                "Frightened condition while you are conscious."
            )
        elif level == 9:
            character.special_traits.append(
                "Abjure Foes: Use Channel Divinity to frighten Fiends and Undead within 60 feet "
                "(Wisdom save or Frightened for 1 minute with speed 0)."
            )
        elif level == 11:
            character.special_traits.append(
                "Radiant Strikes: Melee weapon attacks and Unarmed Strikes deal an extra 1d8 Radiant damage."
            )
        elif level == 14:
            character.special_traits.append(
                "Restoring Touch: When you use Lay on Hands, also remove one of: "
                "Blinded, Charmed, Deafened, Frightened, Paralyzed, or Stunned."
            )
        elif level == 18:
            character.special_traits.append("Aura Expansion: Aura of Protection and Aura of Courage extend to 30 feet.")
        self.spell_slots = dict(_HALF_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_HALF_CASTER_SLOTS[level - 1])
        self.lay_on_hands_pool = 5 * level
        self.completed_levelup_to = level

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        self.completed_levelup_to = 1
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        character.special_abilities.append(Spell(
            name="Lay on Hands",
            casting_time="Action", range_="Touch", components=[],
            duration="Instantaneous",
            description=(
                f"You have a pool of {self.lay_on_hands_pool} HP (restored on Long Rest). "
                "Restore HP to a creature you touch, or spend 5 HP to cure one disease or "
                "neutralize one poison."
            ),
            uses_left=self.lay_on_hands_pool, cooldown="Long Rest",
        ))
        for lv in range(2, self.level + 1):
            self._apply_level(character, lv)
        character.todo.extend([
            {
                "Text": (
                    "Select starting equipment or gold: "
                    "(Chain Mail, Shield, Longsword, Holy Symbol, Scholar's Pack, 9 GP) or (150 GP)"
                ),
                "Options": ["Starting Equipment", "Gold"],
                "Function": self.select_starting_equipment,
            },
            {
                "Text": "Choose 2 skills: Athletics, Insight, Intimidation, Medicine, Persuasion, Religion.",
                "Options": ["Athletics", "Insight", "Intimidation", "Medicine", "Persuasion", "Religion"],
                "Choices": 2,
                "Function": self._set_skill_proficiencies,
            },
            {
                "Text": "Choose 2 weapons to gain Weapon Mastery in.",
                "Options": ["Battleaxe", "Flail", "Glaive", "Greataxe", "Greatsword", "Halberd", "Handaxe", "Lance", "Longsword", "Maul", "Morningstar", "Pike", "Rapier", "Scimitar", "Shortsword", "Trident", "Warhammer", "War Pick", "Whip"],
                "Choices": 2,
                "Function": self._apply_weapon_mastery,
            },
        ])
        return character

    def level_up(self, character: Character):
        self.level += 1
        self._apply_level(character, self.level)
        character.classes = [cls for cls in character.classes if cls.name != self.name] + [self]
        return character

# ── Ranger ─────────────────────────────────────────────────────────────────

