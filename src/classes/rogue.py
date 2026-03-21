from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.common import dnd_skills
from src.classes._base import Class


class Rogue(Class):
    ROGUE_SUBCLASSES = ["Arcane Trickster", "Assassin", "Soulknife", "Thief"]
    SNEAK_ATTACK_DICE = [
        "1d6",  "1d6",  "2d6",  "2d6",  "3d6",  "3d6",
        "4d6",  "4d6",  "5d6",  "5d6",  "6d6",  "6d6",
        "7d6",  "7d6",  "8d6",  "8d6",  "9d6",  "9d6",
        "10d6", "10d6",
    ]

    def __init__(self, level):
        super().__init__(name="Rogue", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 8
        self.primary_ability = "Dexterity"
        self.proficiencies["Armor"] = ["Light"]
        self.proficiencies["Weapons"] = ["Simple", "Martial"]
        self.proficiencies["Tools"] = ["Thieves' Tools"]
        self.proficiencies["Saving Throws"] = ["Dexterity", "Intelligence"]
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

    def _apply_weapon_mastery(self, character: Character, choices):
        character.weapon_mastery += choices

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 100
        else:
            character.add_item([Dagger(quantity=2), ThievesTools(), LeatherArmor(), BurglarsPack()])
            character.gold += 8

    def _apply_level(self, character: Character, level: int):
        sneak_dice = self.SNEAK_ATTACK_DICE[level - 1]
        for trait in character.special_traits:
            if "Sneak Attack" in trait:
                character.special_traits.remove(trait)
                break
        character.special_traits.append(
            f"Sneak Attack ({sneak_dice}): Once per turn, deal extra {sneak_dice} damage when "
            "you hit with a Finesse or Ranged weapon and have Advantage, or an ally is adjacent to the target."
        )
        if level == 2:
            character.special_traits.append(
                "Cunning Action: Dash, Disengage, or Hide as a Bonus Action on each of your turns."
            )
        elif level == 3:
            character.todo.append({
                "Text": "Choose your Rogue subclass (Roguish Archetype).",
                "Options": self.ROGUE_SUBCLASSES,
                "Function": self._set_subclass,
            })
            character.special_traits.append(
                "Steady Aim: As a Bonus Action, gain Advantage on your next attack roll this turn "
                "(your speed becomes 0 until the end of the turn)."
            )
        elif level == 5:
            character.special_traits.append(
                "Cunning Strike: When you deal Sneak Attack damage, you can forgo one Sneak Attack die "
                "for an effect: Disarm, Poison (Con save or Poisoned), Trip (Str save or Prone), "
                "or Withdraw (move up to half your speed without provoking opportunity attacks)."
            )
            character.special_abilities.append(Spell(
                name="Uncanny Dodge",
                casting_time="Reaction", range_="Self", components=[],
                duration="Instantaneous",
                description="When an attacker hits you with an attack roll, halve the attack's damage against you.",
            ))
        elif level == 6:
            character.todo.append({
                "Text": "Expertise (Level 6): Choose 2 more skills or tools to gain Expertise in.",
                "Options": list(dnd_skills.keys()) + ["Thieves' Tools"],
                "Choices": 2,
                "Function": self._apply_expertise,
            })
        elif level == 7:
            character.special_traits.append("Evasion: On a Dex save for half damage, take none on success and half on failure.")
            character.special_traits.append(
                "Reliable Talent: When you make an ability check using a skill or tool you are "
                "proficient in, treat any roll of 9 or lower as a 10."
            )
        elif level == 11:
            character.special_traits.append(
                "Improved Cunning Strike: You can use Cunning Strike without losing a Sneak Attack die."
            )
        elif level == 14:
            character.special_traits.append(
                "Devious Strikes: New Cunning Strike options — Daze (Con save or Incapacitated until "
                "end of their next turn), Knock Out (Con save or Unconscious for 1 minute), "
                "Obscure (Dex save or Blinded until end of their next turn)."
            )
        elif level == 15:
            if "Wisdom" not in character.proficiencies["Saving Throws"]:
                character.proficiencies["Saving Throws"].append("Wisdom")
            character.special_traits.append("Slippery Mind: You gain proficiency in Wisdom saving throws.")
        elif level == 18:
            character.special_traits.append(
                "Elusive: No attack roll has Advantage against you while you aren't Incapacitated."
            )
        elif level == 20:
            character.special_abilities.append(Spell(
                name="Stroke of Luck",
                casting_time="Free Action", range_="Self", components=[],
                duration="Instantaneous",
                description=(
                    "If you fail an ability check, turn it into a 20. "
                    "If you miss an attack roll, turn it into a hit."
                ),
                uses_left=1, cooldown="Long Rest",
            ))
        self.completed_levelup_to = level

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        self.completed_levelup_to = 1
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        character.special_traits.append(
            f"Sneak Attack ({self.SNEAK_ATTACK_DICE[0]}): Once per turn, deal extra "
            f"{self.SNEAK_ATTACK_DICE[0]} damage when you have Advantage or an ally is adjacent."
        )
        character.special_traits.append(
            "Thieves' Cant: You know Thieves' Cant — a secret mix of dialect, jargon, and code "
            "that lets you hide messages in seemingly normal conversation."
        )
        for lv in range(2, self.level + 1):
            self._apply_level(character, lv)
        character.todo.extend([
            {
                "Text": (
                    "Select starting equipment or gold: "
                    "(2 Daggers, Thieves' Tools, Leather Armor, Burglar's Pack, 8 GP) or (100 GP)"
                ),
                "Options": ["Starting Equipment", "Gold"],
                "Function": self.select_starting_equipment,
            },
            {
                "Text": "Choose 4 skills: Acrobatics, Athletics, Deception, Insight, Intimidation, Investigation, Perception, Persuasion, Sleight of Hand, Stealth.",
                "Options": ["Acrobatics", "Athletics", "Deception", "Insight", "Intimidation", "Investigation", "Perception", "Persuasion", "Sleight of Hand", "Stealth"],
                "Choices": 4,
                "Function": self._set_skill_proficiencies,
            },
            {
                "Text": "Expertise (Level 1): Choose 2 skills or Thieves' Tools to gain Expertise in (double proficiency bonus).",
                "Options": ["Acrobatics", "Athletics", "Deception", "Insight", "Intimidation", "Investigation", "Perception", "Persuasion", "Sleight of Hand", "Stealth", "Thieves' Tools"],
                "Choices": 2,
                "Function": self._apply_expertise,
            },
            {
                "Text": "Choose 2 weapons to gain Weapon Mastery in.",
                "Options": ["Dagger", "Dart", "Handaxe", "Javelin", "Light Hammer", "Mace", "Quarterstaff", "Sickle", "Spear", "Light Crossbow", "Shortbow", "Sling", "Hand Crossbow", "Rapier", "Scimitar", "Shortsword", "Whip"],
                "Choices": 2,
                "Function": self._apply_weapon_mastery,
            },
        ])
        return character

    def level_up(self, character: Character):
        super().level_up(character)
        self._apply_level(character, self.level)
        return character
