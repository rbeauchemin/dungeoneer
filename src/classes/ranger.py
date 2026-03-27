from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.classes._base import (
    Class, _HALF_CASTER_SLOTS,
)


# Prepared spells by level
PREPARABLE_SPELLS = [2, 3, 4, 5, 6, 6, 7, 7, 9, 9, 10, 10, 11, 11, 12, 12, 14, 14, 15, 15]


class Ranger(Class):
    RANGER_SUBCLASSES = ["Beast Master", "Fey Wanderer", "Gloom Stalker", "Hunter"]
    RANGER_FIGHTING_STYLES = [
        "Archery", "Blind Fighting", "Defense", "Druidic Warrior",
        "Thrown Weapon Fighting", "Two-Weapon Fighting",
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
        self.proficiencies["Skills"] = [
            "Animal Handling", "Athletics", "Insight", "Investigation",
            "Nature", "Perception", "Stealth", "Survival",
        ]
        self.completed_levelup_to = 0

    # ── Equipment ─────────────────────────────────────────────────────────────

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 150
        else:
            character.add_item([
                StuddedLeatherArmor(), Shortsword(quantity=2),
                Longbow(), Quiver(), Arrows(quantity=20), ExplorersPack(),
            ])
            character.gold += 7
        return character

    # ── Hunter's Mark helpers ──────────────────────────────────────────────────

    def _hunters_mark_uses(self):
        """Uses per Long Rest = Wisdom modifier (minimum 1), refreshed on Long Rest."""
        # Actual Wisdom modifier is not known at class-construction time; we store
        # a sentinel and let the Spell description convey the rule.
        return None  # unlimited tracking deferred to runtime

    def _build_hunters_mark_ability(self):
        wis_uses = "Wisdom modifier (minimum 1)"
        return Spell(
            name="Hunter's Mark",
            casting_time="Bonus Action",
            range_="90 feet",
            components=[],
            duration="Up to 1 hour (Concentration)",
            description=(
                "Mark one creature you can see within 90 feet as your quarry. "
                "Until the spell ends, you deal an extra 1d6 Force damage to the target "
                "whenever you hit it with an attack roll, and you have Advantage on any "
                "Wisdom (Perception or Survival) check you make to find it. "
                "If the target drops to 0 HP before the spell ends, you can use a Bonus "
                "Action to move the mark to a new creature. "
                f"You can cast this feature a number of times equal to your {wis_uses} "
                "per Long Rest without expending a spell slot. You can also cast it using "
                "a spell slot of 1st level or higher."
            ),
            uses_left=None,
            cooldown="Long Rest",
        )

    # ── Skill / subclass helpers ───────────────────────────────────────────────

    def _set_skill_proficiencies(self, character: Character, choices):
        character.proficiencies["Skills"] += choices

    def _set_subclass(self, character: Character, choices):
        self.subclass = choices[0]

    def _apply_fighting_style(self, character: Character, choices):
        character.special_traits.append(f"Fighting Style: {choices[0]}")

    def _apply_weapon_mastery(self, character: Character, choices):
        character.weapon_mastery += choices

    def _apply_expertise(self, character: Character, choices):
        """Grant Expertise (double proficiency bonus) in the chosen skill(s)."""
        if not hasattr(character, "expertise"):
            character.expertise = []
        character.expertise += choices

    # ── Level feature application ──────────────────────────────────────────────

    def _apply_level_features(self, character: Character, level: int):
        """Apply all Ranger features unlocked at the given level."""

        if level == 1:
            if not isinstance(character.special_abilities, list):
                character.special_abilities = []

            # ── Hunter's Mark ──────────────────────────────────────────────────
            character.special_abilities.append(self._build_hunters_mark_ability())

            # ── Weapon Mastery ─────────────────────────────────────────────────
            character.todo.extend([
                {
                    "Text": "Choose 2 weapons to gain Weapon Mastery in.",
                    "Options": [
                        "Battleaxe", "Flail", "Glaive", "Greataxe", "Greatsword", "Halberd",
                        "Handaxe", "Javelin", "Lance", "Light Hammer", "Longsword", "Maul",
                        "Morningstar", "Pike", "Rapier", "Scimitar", "Shortsword", "Trident",
                        "Warhammer", "War Pick", "Whip", "Light Crossbow", "Hand Crossbow",
                        "Heavy Crossbow", "Longbow", "Shortbow",
                    ],
                    "Choices": 2,
                    "Function": self._apply_weapon_mastery,
                },
                {
                    "Text": (
                        "Select starting equipment or gold: "
                        "(Studded Leather Armor, 2 Shortswords, Longbow, Quiver, 20 Arrows, "
                        "Explorer's Pack, 7 GP) or (150 GP)"
                    ),
                    "Options": ["Starting Equipment", "Gold"],
                    "Function": self.select_starting_equipment,
                },
                {
                    "Text": "Choose 3 skills: Animal Handling, Athletics, Insight, Investigation, Nature, Perception, Stealth, Survival.",
                    "Options": [
                        "Animal Handling", "Athletics", "Insight", "Investigation",
                        "Nature", "Perception", "Stealth", "Survival",
                    ],
                    "Choices": 3,
                    "Function": self._set_skill_proficiencies,
                },
            ])

        elif level == 2:
            # ── Deft Explorer ──────────────────────────────────────────────────
            # Gain Expertise in one skill you're proficient in, plus a Natural Explorer option.
            character.todo.append({
                "Text": (
                    "Deft Explorer: Choose one skill you're proficient in to gain Expertise "
                    "(double proficiency bonus)."
                ),
                "Options": [
                    "Animal Handling", "Athletics", "Insight", "Investigation",
                    "Nature", "Perception", "Stealth", "Survival",
                ],
                "Choices": 1,
                "Function": self._apply_expertise,
            })
            character.special_traits.append(
                "Deft Explorer (Natural Explorer): Choose one of the following benefits: "
                "(1) Climb speed equals your Speed, "
                "(2) Swim speed equals your Speed, or "
                "(3) Difficult terrain in natural environments doesn't cost you extra movement."
            )

            # ── Fighting Style ─────────────────────────────────────────────────
            character.todo.append({
                "Text": "Choose a Ranger Fighting Style.",
                "Options": self.RANGER_FIGHTING_STYLES,
                "Function": self._apply_fighting_style,
            })

        elif level == 3:
            # ── Subclass ───────────────────────────────────────────────────────
            character.todo.append({
                "Text": "Choose your Ranger subclass (Ranger Conclave).",
                "Options": self.RANGER_SUBCLASSES,
                "Function": self._set_subclass,
            })

            # ── Tireless ───────────────────────────────────────────────────────
            character.special_abilities.append(Spell(
                name="Tireless",
                casting_time="Bonus Action",
                range_="Self",
                components=[],
                duration="Until removed",
                description=(
                    "As a Bonus Action, give yourself Temporary HP equal to 1d8 plus your "
                    "Wisdom modifier. You can use this feature a number of times equal to your "
                    "Proficiency Bonus, and you regain all expended uses when you finish a Short "
                    "or Long Rest. In addition, whenever you finish a Short Rest, your Exhaustion "
                    "level, if any, decreases by 1."
                ),
                uses_left=None,  # = Proficiency Bonus; tracked at runtime
                cooldown="Short Rest",
            ))

        elif level == 5:
            # ── Extra Attack ───────────────────────────────────────────────────
            character.extra_attacks = getattr(character, "extra_attacks", 0) + 1

        elif level == 6:
            # ── Roving ────────────────────────────────────────────────────────
            character.special_traits.append(
                "Roving: Your Speed increases by 10 feet. You also gain a Climb speed "
                "and a Swim speed equal to your Speed."
            )

        elif level == 7:
            # ── Expertise (second skill) ───────────────────────────────────────
            character.todo.append({
                "Text": (
                    "Deft Explorer (level 7): Choose a second skill you're proficient in "
                    "to gain Expertise (double proficiency bonus)."
                ),
                "Options": [
                    "Animal Handling", "Athletics", "Insight", "Investigation",
                    "Nature", "Perception", "Stealth", "Survival",
                ],
                "Choices": 1,
                "Function": self._apply_expertise,
            })

        elif level == 9:
            # ── Nature's Veil ─────────────────────────────────────────────────
            character.special_abilities.append(Spell(
                name="Nature's Veil",
                casting_time="Bonus Action",
                range_="Self",
                components=[],
                duration="Until the start of your next turn",
                description=(
                    "Draw on the power of nature to hide yourself from view. Using a Bonus "
                    "Action, you become Invisible until the start of your next turn. "
                    "You can use this feature a number of times equal to your Proficiency "
                    "Bonus per Long Rest."
                ),
                uses_left=None,  # = Proficiency Bonus; tracked at runtime
                cooldown="Long Rest",
            ))

        elif level == 11:
            # ── Conjure Barrage ────────────────────────────────────────────────
            character.special_traits.append(
                "Conjure Barrage: You can cast Conjure Barrage without expending a spell slot. "
                "You can do so once per Short Rest."
            )

        elif level == 13:
            # ── Precise Hunter ─────────────────────────────────────────────────
            character.special_traits.append(
                "Precise Hunter: You have Advantage on attack rolls against the creature "
                "currently marked by your Hunter's Mark."
            )

        elif level == 14:
            # ── Feral Senses ───────────────────────────────────────────────────
            character.special_traits.append(
                "Feral Senses: Your connection to nature is so strong that your senses are "
                "supernaturally keen. You don't have Disadvantage on attack rolls against "
                "creatures you can't see, provided the creature isn't hidden from you and "
                "you aren't Blinded. You are also aware of the location of any creature "
                "within 30 feet of you, even if it has the Invisible condition."
            )

        elif level == 15:
            # ── Conjure Volley ────────────────────────────────────────────────
            character.special_traits.append(
                "Conjure Volley: You can cast Conjure Volley without expending a spell slot. "
                "You can do so once per Short Rest."
            )

        elif level == 18:
            # ── Feral Senses: Blindsight ───────────────────────────────────────
            character.special_traits.append(
                "Feral Senses (level 18): You gain Blindsight with a range of 30 feet."
            )

        elif level == 19:
            # ── Epic Boon ──────────────────────────────────────────────────────
            character.todo.append({
                "Text": "Choose an Epic Boon feat.",
                "Options": ["Epic Boon"],
                "Function": lambda char, choices, **kw: char.feats.append(choices[0]),
            })

        elif level == 20:
            # ── Foe Slayer ─────────────────────────────────────────────────────
            character.special_traits.append(
                "Foe Slayer: Your Hunter's Mark gains power. Once per turn when you hit a "
                "creature with a weapon attack, you can roll a d10 and add it to the "
                "attack roll or the damage roll (your choice). You can use this benefit "
                "regardless of whether your Hunter's Mark is active."
            )

        # ── Spell slots scale at every level ──────────────────────────────────
        self.spell_slots = dict(_HALF_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_HALF_CASTER_SLOTS[level - 1])
        self.preparable_spells = PREPARABLE_SPELLS[self.level - 1]
        self.completed_levelup_to = level

    # ── Class interface ────────────────────────────────────────────────────────

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        # Apply features for every level from 1 up to the ranger's starting level
        for lvl in range(1, self.level + 1):
            self._apply_level_features(character, lvl)
        self.completed_levelup_to = self.level
        return character

    def level_up(self, character: Character):
        super().level_up(character)  # increments self.level; handles ASI at 4, 8, 12, 16
        self._apply_level_features(character, self.level)
        return character
