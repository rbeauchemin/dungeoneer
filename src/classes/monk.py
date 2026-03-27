from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.common import artisans_tools
from src.classes._base import (
    Class, _HALF_CASTER_SLOTS,
)


# Martial Arts damage die by Monk level
_MARTIAL_ARTS_DIE = {
    **{lv: "1d6"  for lv in range(1,  5)},
    **{lv: "1d8"  for lv in range(5,  11)},
    **{lv: "1d10" for lv in range(11, 17)},
    **{lv: "1d12" for lv in range(17, 21)},
}

# Unarmored Movement speed bonus (feet) by Monk level
_UNARMORED_MOVEMENT_BONUS = {
    **{lv: 10 for lv in range(1,  6)},
    **{lv: 15 for lv in range(6,  10)},
    **{lv: 20 for lv in range(10, 14)},
    **{lv: 25 for lv in range(14, 18)},
    **{lv: 30 for lv in range(18, 21)},
}

# Focus Points equal to Monk level
_FOCUS_POINTS_PER_LEVEL = {lv: lv for lv in range(1, 21)}


class Monk(Class):
    MONK_SUBCLASSES = [
        "Warrior of the Elements", "Warrior of Mercy",
        "Warrior of Shadow", "Warrior of the Open Hand",
    ]

    def __init__(self, level):
        super().__init__(name="Monk", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 8
        self.primary_ability = "Dexterity and Wisdom"
        self.proficiencies["Weapons"] = ["Simple", "Martial"]
        self.proficiencies["Saving Throws"] = ["Strength", "Dexterity"]
        self.proficiencies["Skills"] = []
        self.completed_levelup_to = 0

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_skill_proficiencies(self, character: Character, choices, **kwargs):
        character.proficiencies["Skills"] += choices

    def _set_subclass(self, character: Character, choices, **kwargs):
        self.subclass = choices[0]

    def _apply_tool_proficiency(self, character: Character, choices, **kwargs):
        character.proficiencies["Tools"] += choices

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 50
        else:
            character.add_item([Shortsword(), DungeoneersPack()])
            character.gold += 11

    # ── Level feature application ─────────────────────────────────────────────

    def _apply_level_features(self, character: Character, level: int):
        """Apply all Monk features unlocked at the given level."""

        if level == 1:
            if not isinstance(character.special_abilities, list):
                character.special_abilities = []

            # ── Martial Arts ──────────────────────────────────────────────────
            ma_die = _MARTIAL_ARTS_DIE[self.level]
            character.special_traits.append(
                f"Martial Arts ({ma_die}): Unarmed Strikes and Monk weapons use {ma_die} for damage. "
                "Use Dexterity instead of Strength for attack and damage rolls. "
                "After the Attack action, make one Unarmed Strike as a Bonus Action."
            )

            # ── Unarmored Defense ─────────────────────────────────────────────
            character.special_traits.append(
                "Unarmored Defense: While wearing no armor and carrying no Shield, your AC equals "
                "10 + your Dexterity modifier + your Wisdom modifier."
            )

            # ── Unarmored Movement ────────────────────────────────────────────
            bonus = _UNARMORED_MOVEMENT_BONUS[self.level]
            character.special_traits.append(
                f"Unarmored Movement: Your Speed increases by {bonus} feet while you aren't "
                "wearing armor or carrying a Shield."
            )

            # ── Starting equipment / skills / tool proficiency ─────────────────
            character.todo.extend([
                {
                    "Text": "Select starting equipment or gold: (Shortsword, Dungeoneer's Pack, 11 GP) or (50 GP)",
                    "Options": ["Starting Equipment", "Gold"],
                    "Function": self.select_starting_equipment,
                },
                {
                    "Text": "Choose 2 skills: Acrobatics, Athletics, History, Insight, Religion, Stealth.",
                    "Options": ["Acrobatics", "Athletics", "History", "Insight", "Religion", "Stealth"],
                    "Choices": 2,
                    "Function": self._set_skill_proficiencies,
                },
                {
                    "Text": "Choose 1 tool proficiency: an Artisan's Tool or Musical Instrument.",
                    "Options": (
                        artisans_tools
                        + ["Bagpipes", "Drum", "Dulcimer", "Flute", "Horn",
                           "Lute", "Lyre", "Pan Flute", "Shawm", "Viol"]
                    ),
                    "Function": self._apply_tool_proficiency,
                },
            ])

        elif level == 2:
            # ── Monk's Focus ──────────────────────────────────────────────────
            fp = _FOCUS_POINTS_PER_LEVEL[self.level]
            character.special_traits.append(
                f"Monk's Focus: You have {fp} Focus Points (regain all on a Short or Long Rest). "
                "Flurry of Blows (1 FP, Bonus Action): Immediately after the Attack action, "
                "make two Unarmed Strikes. "
                "Patient Defense (1 FP, Bonus Action): Take the Dodge action. "
                "Step of the Wind (1 FP, Bonus Action): Take the Dash or Disengage action; "
                "your jump distance is doubled for the turn."
            )
            # Flurry of Blows as a castable ability
            character.special_abilities.append(Spell(
                name="Flurry of Blows",
                casting_time="Bonus Action", range_="Self", components=[],
                duration="Instantaneous",
                description=(
                    "Costs 1 Focus Point. Immediately after the Attack action, "
                    "make two Unarmed Strikes."
                ),
            ))

        elif level == 3:
            # ── Deflect Attacks ───────────────────────────────────────────────
            character.special_abilities.append(Spell(
                name="Deflect Attacks",
                casting_time="Reaction", range_="Self", components=[],
                duration="Instantaneous",
                description=(
                    "When you take Bludgeoning, Piercing, or Slashing damage, reduce it by "
                    "1d10 + your Dexterity modifier + your Monk level. "
                    "If the damage is reduced to 0, you can spend 1 Focus Point to redirect "
                    "the attack as a ranged Unarmed Strike (range 20/60 ft) against the attacker."
                ),
            ))

            # ── Subclass ──────────────────────────────────────────────────────
            character.todo.append({
                "Text": "Choose your Monk subclass.",
                "Options": self.MONK_SUBCLASSES,
                "Function": self._set_subclass,
            })

        elif level == 4:
            # ── Slow Fall ─────────────────────────────────────────────────────
            character.special_traits.append(
                "Slow Fall: As a Reaction when you fall, reduce the fall damage you take "
                "by an amount equal to five times your Monk level."
            )

            # ── ASI ───────────────────────────────────────────────────────────
            character.todo.append({
                "Text": "Ability Score Improvement: Increase one ability score by 2, or two ability scores by 1 each (max 20).",
                "Options": ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"],
                "Function": lambda char, choices, **kw: None,  # handled by caller
            })

        elif level == 5:
            # ── Extra Attack ──────────────────────────────────────────────────
            character.extra_attacks = getattr(character, "extra_attacks", 0) + 1
            character.special_traits.append(
                "Extra Attack: You can attack twice instead of once when you take the Attack action."
            )

            # ── Stunning Strike ───────────────────────────────────────────────
            character.special_traits.append(
                "Stunning Strike: When you hit a creature with a Monk weapon or an Unarmed Strike, "
                "spend 1 Focus Point to attempt a Stunning Strike. The target must make a Constitution "
                "saving throw (DC = 8 + your proficiency bonus + your Wisdom modifier). On a failure, "
                "the target has the Stunned condition until the start of your next turn."
            )

        elif level == 6:
            # ── Empowered Strikes ─────────────────────────────────────────────
            character.special_traits.append(
                "Empowered Strikes: Whenever you deal damage with your Unarmed Strike, it can deal "
                "your choice of Force damage or its normal damage type. It also counts as Magical "
                "for the purpose of overcoming Resistance and Immunity to nonmagical attacks."
            )

            # ── Subclass feature (level 6) ────────────────────────────────────
            # Subclass grants its own features; tracked via subclass choice.

            # ── Unarmored Movement update ─────────────────────────────────────
            # Update trait to reflect new bonus (15 ft at level 6)
            bonus = _UNARMORED_MOVEMENT_BONUS[self.level]
            character.special_traits = [
                t for t in character.special_traits
                if not t.startswith("Unarmored Movement:")
            ]
            character.special_traits.append(
                f"Unarmored Movement: Your Speed increases by {bonus} feet while you aren't "
                "wearing armor or carrying a Shield."
            )

        elif level == 7:
            # ── Evasion ───────────────────────────────────────────────────────
            character.special_traits.append(
                "Evasion: When you are subjected to an effect that allows a Dexterity saving throw "
                "to take only half damage, you instead take no damage on a success and only half "
                "damage on a failure. You can't use this if you have the Incapacitated condition."
            )

            # ── Self-Restoration ──────────────────────────────────────────────
            character.special_traits.append(
                "Self-Restoration: At the start of each of your turns, you can end one of the "
                "following conditions on yourself: Charmed, Frightened, or Poisoned."
            )

        elif level == 8:
            # ── ASI ───────────────────────────────────────────────────────────
            character.todo.append({
                "Text": "Ability Score Improvement: Increase one ability score by 2, or two ability scores by 1 each (max 20).",
                "Options": ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"],
                "Function": lambda char, choices, **kw: None,
            })

        elif level == 9:
            # ── Acrobatic Movement ────────────────────────────────────────────
            character.special_traits.append(
                "Acrobatic Movement: While you aren't wearing armor or carrying a Shield, "
                "you can move along vertical surfaces and across liquids on your turn without falling "
                "during the movement."
            )

        elif level == 10:
            # ── Heightened Focus ──────────────────────────────────────────────
            character.special_traits.append(
                "Heightened Focus: Flurry of Blows, Patient Defense, and Step of the Wind "
                "gain the following benefits. "
                "Flurry of Blows: You can spend 1 additional Focus Point (2 total) to make "
                "one of the Unarmed Strikes push the target up to 10 feet away or cause it to have "
                "the Prone condition. "
                "Patient Defense: You gain a number of Temporary Hit Points equal to two rolls of "
                "your Martial Arts die when you use this. "
                "Step of the Wind: You may fly up to your Speed when you use this, "
                "though you fall if you end your movement in the air and nothing supports you."
            )

            # ── Self-Restoration update ────────────────────────────────────────
            character.special_traits.append(
                "Self-Restoration (expanded): You can also end the Blinded, Deafened, or Stunned "
                "condition on yourself at the start of your turn."
            )

            # ── Unarmored Movement update ─────────────────────────────────────
            bonus = _UNARMORED_MOVEMENT_BONUS[self.level]
            character.special_traits = [
                t for t in character.special_traits
                if not t.startswith("Unarmored Movement:")
            ]
            character.special_traits.append(
                f"Unarmored Movement: Your Speed increases by {bonus} feet while you aren't "
                "wearing armor or carrying a Shield."
            )

        elif level == 11:
            # Subclass feature only (no base class feature at 11).
            pass

        elif level == 12:
            # ── ASI ───────────────────────────────────────────────────────────
            character.todo.append({
                "Text": "Ability Score Improvement: Increase one ability score by 2, or two ability scores by 1 each (max 20).",
                "Options": ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"],
                "Function": lambda char, choices, **kw: None,
            })

        elif level == 13:
            # ── Deflect Energy ────────────────────────────────────────────────
            character.special_traits.append(
                "Deflect Energy: Your Deflect Attacks feature can now deflect damage of any type, "
                "not just Bludgeoning, Piercing, and Slashing."
            )

        elif level == 14:
            # ── Disciplined Survivor ──────────────────────────────────────────
            character.proficiencies["Saving Throws"] = list(set(
                character.proficiencies["Saving Throws"]
                + ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
            ))
            character.special_traits.append(
                "Disciplined Survivor: You gain proficiency in all saving throws. "
                "Additionally, whenever you make a saving throw and fail, you can spend 1 Focus Point "
                "to reroll it and take the second result."
            )

            # ── Unarmored Movement update ─────────────────────────────────────
            bonus = _UNARMORED_MOVEMENT_BONUS[self.level]
            character.special_traits = [
                t for t in character.special_traits
                if not t.startswith("Unarmored Movement:")
            ]
            character.special_traits.append(
                f"Unarmored Movement: Your Speed increases by {bonus} feet while you aren't "
                "wearing armor or carrying a Shield."
            )

        elif level == 15:
            # ── Perfect Focus ─────────────────────────────────────────────────
            character.special_traits.append(
                "Perfect Focus: When you roll Initiative and have fewer than 4 Focus Points, "
                "you regain Focus Points until you have 4."
            )

        elif level == 16:
            # ── ASI ───────────────────────────────────────────────────────────
            character.todo.append({
                "Text": "Ability Score Improvement: Increase one ability score by 2, or two ability scores by 1 each (max 20).",
                "Options": ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"],
                "Function": lambda char, choices, **kw: None,
            })

        elif level == 17:
            # Subclass feature only.
            pass

        elif level == 18:
            # ── Superior Defense ──────────────────────────────────────────────
            character.special_abilities.append(Spell(
                name="Superior Defense",
                casting_time="Bonus Action", range_="Self", components=[],
                duration="1 minute",
                description=(
                    "Spend 3 Focus Points. Until the start of your next turn you gain Resistance "
                    "to all damage except Psychic damage."
                ),
                uses_left=None, cooldown=None,
            ))

            # ── Unarmored Movement update ─────────────────────────────────────
            bonus = _UNARMORED_MOVEMENT_BONUS[self.level]
            character.special_traits = [
                t for t in character.special_traits
                if not t.startswith("Unarmored Movement:")
            ]
            character.special_traits.append(
                f"Unarmored Movement: Your Speed increases by {bonus} feet while you aren't "
                "wearing armor or carrying a Shield."
            )

        elif level == 19:
            # ── Epic Boon ─────────────────────────────────────────────────────
            character.todo.append({
                "Text": "Epic Boon: Choose an Epic Boon feat.",
                "Options": [],
                "Function": lambda char, choices, **kw: None,
            })

        elif level == 20:
            # ── Body and Mind ─────────────────────────────────────────────────
            character.ability_scores["Dexterity"] = min(
                25, character.ability_scores.get("Dexterity", 10) + 4
            )
            character.ability_scores["Wisdom"] = min(
                25, character.ability_scores.get("Wisdom", 10) + 4
            )
            character.special_traits.append(
                "Body and Mind: Your Dexterity and Wisdom scores each increase by 4 "
                "(maximum 25). Your Focus Point maximum also increases by 4."
            )

    # ── Class interface ───────────────────────────────────────────────────────

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        # Apply features for every level from 1 up to the monk's starting level
        for lvl in range(1, self.level + 1):
            self._apply_level_features(character, lvl)
        self.completed_levelup_to = self.level
        return character

    def level_up(self, character: Character):
        super().level_up(character)  # increments self.level
        self._apply_level_features(character, self.level)
        return character
