from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.common import dnd_skills
from src.classes._base import Class


SNEAK_ATTACK_DICE = [
    "1d6",  "1d6",  "2d6",  "2d6",  "3d6",  "3d6",
    "4d6",  "4d6",  "5d6",  "5d6",  "6d6",  "6d6",
    "7d6",  "7d6",  "8d6",  "8d6",  "9d6",  "9d6",
    "10d6", "10d6",
]

_ROGUE_SUBCLASSES = ["Arcane Trickster", "Assassin", "Soulknife", "Thief"]

_ROGUE_SKILL_OPTIONS = [
    "Acrobatics", "Athletics", "Deception", "Insight", "Intimidation",
    "Investigation", "Perception", "Persuasion", "Sleight of Hand", "Stealth",
]

_ROGUE_WEAPON_MASTERY_OPTIONS = [
    "Dagger", "Dart", "Handaxe", "Javelin", "Light Hammer", "Mace",
    "Quarterstaff", "Sickle", "Spear", "Light Crossbow", "Shortbow", "Sling",
    "Hand Crossbow", "Rapier", "Scimitar", "Shortsword", "Whip",
]


class Rogue(Class):
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
        self.completed_levelup_to = 0

    # ── Equipment ──────────────────────────────────────────────────────────────

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 100
        else:
            character.add_item([Dagger(quantity=2), ThievesTools(), LeatherArmor(), BurglarsPack()])
            character.gold += 8
        return character

    # ── Proficiency helpers ────────────────────────────────────────────────────

    def _set_skill_proficiencies(self, character: Character, choices, **kwargs):
        character.proficiencies["Skills"] += choices

    def _set_subclass(self, character: Character, choices, **kwargs):
        self.subclass = choices[0]

    def _apply_expertise(self, character: Character, choices, **kwargs):
        if not hasattr(character, "expertise"):
            character.expertise = []
        character.expertise += choices

    def _apply_weapon_mastery(self, character: Character, choices, **kwargs):
        character.weapon_mastery += choices

    # ── Sneak Attack helper ────────────────────────────────────────────────────

    def _refresh_sneak_attack(self, character: Character):
        """Replace the Sneak Attack trait with an updated version for the current level."""
        sneak_dice = SNEAK_ATTACK_DICE[self.level - 1]
        character.special_traits = [
            t for t in character.special_traits if not t.startswith("Sneak Attack")
        ]
        character.special_traits.append(
            f"Sneak Attack ({sneak_dice}): Once per turn, deal extra {sneak_dice} damage when "
            "you hit with a Finesse or Ranged weapon and have Advantage, or an ally is adjacent "
            "to the target."
        )

    # ── Level feature application ──────────────────────────────────────────────

    def _apply_level_features(self, character: Character, level: int):
        """Apply all Rogue features unlocked at the given level."""

        # Sneak Attack always updates each level.
        self._refresh_sneak_attack(character)

        if level == 1:
            if not isinstance(character.special_abilities, list):
                character.special_abilities = []

            character.special_traits.append(
                "Thieves' Cant: You know Thieves' Cant — a secret mix of dialect, jargon, and "
                "code that lets you hide messages in seemingly normal conversation."
            )
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
                    "Text": (
                        "Choose 4 skills to gain proficiency in: Acrobatics, Athletics, Deception, "
                        "Insight, Intimidation, Investigation, Perception, Persuasion, Sleight of Hand, Stealth."
                    ),
                    "Options": _ROGUE_SKILL_OPTIONS,
                    "Choices": 4,
                    "Function": self._set_skill_proficiencies,
                },
                {
                    "Text": "Expertise (Level 1): Choose 2 skills or Thieves' Tools to gain Expertise in (double proficiency bonus).",
                    "Options": _ROGUE_SKILL_OPTIONS + ["Thieves' Tools"],
                    "Choices": 2,
                    "Function": self._apply_expertise,
                },
                {
                    "Text": "Weapon Mastery: Choose 2 weapons to gain Weapon Mastery in.",
                    "Options": _ROGUE_WEAPON_MASTERY_OPTIONS,
                    "Choices": 2,
                    "Function": self._apply_weapon_mastery,
                },
            ])

        elif level == 2:
            character.special_traits.append(
                "Cunning Action: Dash, Disengage, or Hide as a Bonus Action on each of your turns."
            )

        elif level == 3:
            character.todo.append({
                "Text": "Choose your Rogue subclass (Roguish Archetype).",
                "Options": _ROGUE_SUBCLASSES,
                "Function": self._set_subclass,
            })
            character.special_traits.append(
                "Steady Aim: As a Bonus Action, gain Advantage on your next attack roll this turn "
                "(your speed becomes 0 until the end of the turn)."
            )

        elif level == 5:
            character.todo.append({
                "Text": "Expertise (Level 5): Choose 2 more skills or Thieves' Tools to gain Expertise in.",
                "Options": _ROGUE_SKILL_OPTIONS + ["Thieves' Tools"],
                "Choices": 2,
                "Function": self._apply_expertise,
            })
            character.special_traits.append(
                "Cunning Strike: When you deal Sneak Attack damage, you can forgo one Sneak Attack "
                "die for an effect — Disarm (Dex save or drop one item), Poison (Con save or Poisoned "
                "until end of their next turn), Trip (Dex save or Prone), or Withdraw (move up to "
                "half your Speed without provoking Opportunity Attacks)."
            )
            character.special_abilities.append(Spell(
                name="Uncanny Dodge",
                casting_time="Reaction",
                range_="Self",
                components=[],
                duration="Instantaneous",
                description=(
                    "When an attacker that you can see hits you with an attack roll, halve the "
                    "attack's damage against you."
                ),
            ))

        elif level == 7:
            character.special_traits.append(
                "Evasion: When you are subjected to an effect that allows a Dexterity saving throw "
                "to take only half damage, you take no damage on a success and only half on a failure. "
                "You can't use this if you're Incapacitated."
            )
            character.special_traits.append(
                "Reliable Talent: When you make an ability check using a skill or tool you are "
                "proficient in, treat any d20 roll of 9 or lower as a 10."
            )

        elif level == 10:
            # Rogue gets an extra ASI at level 10 (not in the base class default of 4/8/12/16).
            character.todo.append({
                "Text": "Ability Score Improvement (Level 10): Choose an Ability Score Improvement or Feat.",
                "Options": ["Ability Score Improvement", "Feat"],
                "Function": self.select_ability_score_improvement_or_feat,
            })

        elif level == 11:
            character.special_traits.append(
                "Improved Cunning Strike: You can use two Cunning Strike effects when you deal "
                "Sneak Attack damage, instead of one, but you still forgo only one Sneak Attack die."
            )

        elif level == 14:
            character.special_traits.append(
                "Devious Strikes: You gain three new Cunning Strike options — "
                "Daze (Con save or Incapacitated until end of their next turn, losing their Reaction), "
                "Knock Out (Con save or Unconscious for 1 minute or until they take damage or someone "
                "uses an action to wake them), "
                "Obscure (Dex save or Blinded until end of their next turn)."
            )

        elif level == 15:
            if "Wisdom" not in character.proficiencies["Saving Throws"]:
                character.proficiencies["Saving Throws"].append("Wisdom")
            character.special_traits.append(
                "Slippery Mind: You gain proficiency in Wisdom saving throws. If you already have "
                "this proficiency, you instead gain proficiency in Intelligence or Charisma saving "
                "throws (your choice)."
            )

        elif level == 18:
            character.special_traits.append(
                "Elusive: No attack roll has Advantage against you while you aren't Incapacitated."
            )

        elif level == 19:
            # Epic Boon replaces ASI at level 19 for the Rogue.
            character.todo.append({
                "Text": "Epic Boon (Level 19): Choose an Epic Boon feat.",
                "Options": ["Feat"],
                "Function": self.select_feat,
            })

        elif level == 20:
            character.special_abilities.append(Spell(
                name="Stroke of Luck",
                casting_time="Free Action",
                range_="Self",
                components=[],
                duration="Instantaneous",
                description=(
                    "If you fail an ability check, turn the roll into a 20. "
                    "If you miss an attack roll, turn the miss into a hit."
                ),
                uses_left=1,
                cooldown="Short Rest",
            ))

    # ── Class interface ────────────────────────────────────────────────────────

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        # Apply features for every level from 1 up to the rogue's starting level.
        for lvl in range(1, self.level + 1):
            self._apply_level_features(character, lvl)
        self.completed_levelup_to = self.level
        return character

    def level_up(self, character: Character):
        super().level_up(character)  # increments self.level, handles ASIs at 4/8/12/16
        self._apply_level_features(character, self.level)
        return character
