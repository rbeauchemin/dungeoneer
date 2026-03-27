from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.classes._base import (
    Class, _FIGHTING_STYLES,
)

# Weapon options available for Fighter Weapon Mastery
_FIGHTER_WEAPON_MASTERY_OPTIONS = [
    "Battleaxe", "Flail", "Glaive", "Greataxe", "Greatsword", "Halberd",
    "Handaxe", "Javelin", "Lance", "Light Hammer", "Longsword", "Maul",
    "Morningstar", "Pike", "Rapier", "Scimitar", "Shortsword", "Trident",
    "Warhammer", "War Pick", "Whip", "Light Crossbow", "Hand Crossbow",
    "Heavy Crossbow", "Longbow", "Shortbow",
]


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
        self.proficiencies["Skills"] = [
            "Acrobatics", "Animal Handling", "Athletics", "History",
            "Insight", "Intimidation", "Perception", "Survival",
        ]
        self.completed_levelup_to = 0

    # ── Equipment ─────────────────────────────────────────────────────────────

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 155
        else:
            character.add_item([
                ChainMail(), Flail(), Shield(),
                LightCrossbow(), Bolts(quantity=20), DungeoneersPack(),
            ])
            character.gold += 4
        return character

    # ── Subclass / choice helpers ──────────────────────────────────────────────

    def _set_subclass(self, character: Character, choices, **kwargs):
        self.subclass = choices[0]
        character.special_traits.append(f"Fighter Subclass: {choices[0]}")

    def _apply_fighting_style(self, character: Character, choices, **kwargs):
        character.special_traits.append(f"Fighting Style: {choices[0]}")

    def _apply_weapon_mastery(self, character: Character, choices, **kwargs):
        character.weapon_mastery += choices

    # ── Level feature application ──────────────────────────────────────────────

    def _apply_level_features(self, character: Character, level: int):
        """Apply all Fighter features unlocked at the given level."""

        if level == 1:
            if not isinstance(character.special_abilities, list):
                character.special_abilities = []

            # ── Second Wind ───────────────────────────────────────────────────
            character.special_abilities.append(Spell(
                name="Second Wind",
                casting_time="Bonus Action",
                range_="Self",
                components=[],
                duration="Instantaneous",
                description=(
                    "Regain HP equal to 1d10 + your Fighter level. "
                    "Usable twice per Short Rest."
                ),
                uses_left=2,
                cooldown="Short Rest",
            ))

            # ── Level 1 todos: equipment, skills, fighting style, weapon mastery ──
            character.todo.extend([
                {
                    "Text": (
                        "Select starting equipment or gold: "
                        "(Chain Mail, Flail, Shield, Light Crossbow, 20 Bolts, "
                        "Dungeoneer's Pack, 4 GP) or (155 GP)"
                    ),
                    "Options": ["Starting Equipment", "Gold"],
                    "Function": self.select_starting_equipment,
                },
                {
                    "Text": (
                        "Choose 2 skills: Acrobatics, Animal Handling, Athletics, "
                        "History, Insight, Intimidation, Perception, Survival."
                    ),
                    "Options": list(set(self.proficiencies["Skills"]) - set(character.proficiencies["Skills"])),
                    "Choices": 2,
                    "AllowSame": False,
                    "Function": self.select_skills,
                },
                {
                    "Text": "Choose a Fighting Style.",
                    "Options": _FIGHTING_STYLES,
                    "Function": self._apply_fighting_style,
                },
                {
                    "Text": "Choose 3 weapons to gain Weapon Mastery in.",
                    "Options": _FIGHTER_WEAPON_MASTERY_OPTIONS,
                    "Choices": 3,
                    "AllowSame": False,
                    "Function": self._apply_weapon_mastery,
                },
            ])

        elif level == 2:
            # ── Action Surge ──────────────────────────────────────────────────
            character.special_abilities.append(Spell(
                name="Action Surge",
                casting_time="Free Action",
                range_="Self",
                components=[],
                duration="Instantaneous",
                description=(
                    "On your turn, take one additional action on top of your regular "
                    "action and a possible Bonus Action. You can use this feature twice "
                    "per Short Rest starting at level 17."
                ),
                uses_left=1,
                cooldown="Short Rest",
            ))

        elif level == 3:
            # ── Fighter Subclass ──────────────────────────────────────────────
            character.todo.append({
                "Text": "Choose your Fighter subclass.",
                "Options": self.FIGHTER_SUBCLASSES,
                "Function": self._set_subclass,
            })

        elif level == 5:
            # ── Extra Attack ──────────────────────────────────────────────────
            character.extra_attacks = getattr(character, "extra_attacks", 0) + 1
            character.special_traits.append(
                "Extra Attack: You can attack twice when you take the Attack action."
            )

            # ── Tactical Master ───────────────────────────────────────────────
            character.special_traits.append(
                "Tactical Master: When you attack with a weapon whose Mastery property "
                "you can use, you can replace that property with Push, Sap, or Slow."
            )

        elif level == 6:
            # ── Ability Score Improvement (Fighter-specific extra ASI) ─────────
            character.todo.append({
                "Text": "Choose an Ability Score Improvement or Feat. (Fighter level 6)",
                "Options": ["Ability Score Improvement", "Feat"],
                "Function": self.select_ability_score_improvement_or_feat,
            })

        elif level == 7:
            # ── Studied Attacks ───────────────────────────────────────────────
            character.special_traits.append(
                "Studied Attacks: If you miss an attack roll, you have Advantage on your "
                "next attack roll against that same creature before the end of your next turn."
            )

        elif level == 9:
            # ── Indomitable (1 use) ───────────────────────────────────────────
            character.special_abilities.append(Spell(
                name="Indomitable",
                casting_time="Free Action",
                range_="Self",
                components=[],
                duration="Instantaneous",
                description=(
                    "When you fail a saving throw, you can reroll it using the new result. "
                    "You gain additional uses of this feature at higher levels: "
                    "2 uses at level 13, 3 uses at level 17."
                ),
                uses_left=1,
                cooldown="Long Rest",
            ))

        elif level == 11:
            # ── Extra Attack improvement (3 total) ────────────────────────────
            character.extra_attacks = getattr(character, "extra_attacks", 0) + 1
            character.special_traits.append(
                "Extra Attack (2): You can attack three times when you take the Attack action."
            )

        elif level == 13:
            # ── Indomitable (2 uses) ──────────────────────────────────────────
            for ability in character.special_abilities:
                if ability.name == "Indomitable":
                    ability.uses_left = 2

        elif level == 14:
            # ── Ability Score Improvement (Fighter-specific extra ASI) ─────────
            character.todo.append({
                "Text": "Choose an Ability Score Improvement or Feat. (Fighter level 14)",
                "Options": ["Ability Score Improvement", "Feat"],
                "Function": self.select_ability_score_improvement_or_feat,
            })

        elif level == 15:
            # ── Extra Fighting Style ──────────────────────────────────────────
            character.todo.append({
                "Text": "Choose an additional Fighting Style.",
                "Options": _FIGHTING_STYLES,
                "Function": self._apply_fighting_style,
            })

        elif level == 17:
            # ── Action Surge (2 uses) & Indomitable (3 uses) ──────────────────
            for ability in character.special_abilities:
                if ability.name == "Action Surge":
                    ability.uses_left = 2
                elif ability.name == "Indomitable":
                    ability.uses_left = 3

        elif level == 19:
            # ── Epic Boon ─────────────────────────────────────────────────────
            character.todo.append({
                "Text": (
                    "Choose an Epic Boon feat (e.g. Boon of Combat Prowess, "
                    "Boon of Dimensional Travel, Boon of Energy Resistance, "
                    "Boon of Fate, Boon of Fortitude, Boon of Irresistible Offense, "
                    "Boon of Recovery, Boon of Skill, Boon of Speed, Boon of Spell Recall, "
                    "Boon of the Night Spirit, Boon of Truesight)."
                ),
                "Options": [
                    "Boon of Combat Prowess",
                    "Boon of Dimensional Travel",
                    "Boon of Energy Resistance",
                    "Boon of Fate",
                    "Boon of Fortitude",
                    "Boon of Irresistible Offense",
                    "Boon of Recovery",
                    "Boon of Skill",
                    "Boon of Speed",
                    "Boon of Spell Recall",
                    "Boon of the Night Spirit",
                    "Boon of Truesight",
                ],
                "Function": lambda char, choices, **kw: char.feats.append(choices[0]),
            })

        elif level == 20:
            # ── Extra Attack improvement (4 total) ────────────────────────────
            character.extra_attacks = getattr(character, "extra_attacks", 0) + 1
            character.special_traits.append(
                "Extra Attack (3): You can attack four times when you take the Attack action."
            )

    # ── Class interface ────────────────────────────────────────────────────────

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        # Apply features for every level from 1 up to the Fighter's starting level
        for lvl in range(1, self.level + 1):
            self._apply_level_features(character, lvl)
        self.completed_levelup_to = self.level
        return character

    def level_up(self, character: Character):
        super().level_up(character)  # increments self.level, handles ASI at 4, 8, 12, 16
        self._apply_level_features(character, self.level)
        return character
