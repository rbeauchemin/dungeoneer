from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.classes._base import (
    Class, _FULL_CASTER_SLOTS,
)


# Metamagic options available per the 2024 PHB
_METAMAGIC_OPTIONS = [
    "Careful Spell",
    "Distant Spell",
    "Empowered Spell",
    "Extended Spell",
    "Heightened Spell",
    "Quickened Spell",
    "Seeking Spell",
    "Subtle Spell",
    "Transmuted Spell",
    "Twinned Spell",
]

# Sorcery Points = Sorcerer level (gained at level 2)
_SORCERY_POINTS_PER_LEVEL = [
    0,   # Level 1 (not yet unlocked)
    2, 3, 4, 5, 6, 7, 8, 9, 10,   # Levels 2-10
    11, 12, 13, 14, 15, 16, 17, 18, 19, 20,  # Levels 11-20
]

PREPARABLE_SPELLS = [2, 4, 6, 7, 9, 10, 11, 12, 14, 15, 16, 16, 17, 17, 18, 18, 19, 20, 21, 22]


class Sorcerer(Class):
    SORCERER_SUBCLASSES = [
        "Draconic Sorcery",
        "Wild Magic Sorcery",
        "Clockwork Sorcery",
        "Aberrant Sorcery",
    ]
    CANTRIPS_KNOWN = [4, 4, 4, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6]

    def __init__(self, level):
        super().__init__(name="Sorcerer", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 6
        self.primary_ability = "Charisma"
        self.spellcasting_ability = "Charisma"
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.proficiencies["Weapons"] = ["Simple"]
        self.proficiencies["Saving Throws"] = ["Constitution", "Charisma"]
        self.proficiencies["Skills"] = [
            "Arcana", "Deception", "Insight", "Intimidation", "Persuasion", "Religion"
        ]
        self.completed_levelup_to = 0

    # ── Equipment ─────────────────────────────────────────────────────────────

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 50
        else:
            character.add_item([Dagger(quantity=2), ComponentPouch(), ArcaneFocus(), BurglarsPack()])
            character.gold += 28
        return character

    # ── Innate Sorcery helpers ─────────────────────────────────────────────────

    def _build_innate_sorcery_ability(self):
        uses = 2 if self.level >= 5 else 1
        return Spell(
            name="Innate Sorcery",
            casting_time="Bonus Action",
            range_="Self",
            components=[],
            duration="1 minute",
            description=(
                "You emanate an aura of magical power. For 1 minute: you have Advantage on "
                "spell attack rolls, and the spell save DC of your Sorcerer spells increases by 1."
            ),
            uses_left=uses,
            cooldown="Long Rest",
        )

    def _refresh_innate_sorcery(self, character: Character):
        """Replace Innate Sorcery with an updated version reflecting the current level."""
        character.special_abilities = [
            a for a in character.special_abilities if a.name != "Innate Sorcery"
        ] + [self._build_innate_sorcery_ability()]

    # ── Metamagic helpers ──────────────────────────────────────────────────────

    def _apply_metamagic(self, character: Character, choices, **kwargs):
        if not hasattr(character, "metamagic"):
            character.metamagic = []
        character.metamagic += choices

    # ── Subclass helper ────────────────────────────────────────────────────────

    def _set_subclass(self, character: Character, choices, **kwargs):
        self.subclass = choices[0]

    # ── Level feature application ──────────────────────────────────────────────

    def _apply_level_features(self, character: Character, level: int):
        """Apply all Sorcerer features unlocked at the given level."""

        if level == 1:
            # ── Innate Sorcery ─────────────────────────────────────────────────
            if not isinstance(character.special_abilities, list):
                character.special_abilities = []
            character.special_abilities.append(self._build_innate_sorcery_ability())

            # ── Weapon Mastery ─────────────────────────────────────────────────
            character.todo.extend([
                {
                    "Text": "Weapon Mastery: Choose one Simple weapon to gain mastery in.",
                    "Options": [
                        "Club", "Dagger", "Greatclub", "Handaxe", "Javelin",
                        "Light Hammer", "Mace", "Quarterstaff", "Sickle", "Spear",
                        "Light Crossbow", "Dart", "Shortbow", "Sling",
                    ],
                    "Choices": 1,
                    "Function": lambda char, choices: char.weapon_mastery.extend(choices)
                },
                {
                    "Text": (
                        "Select starting equipment or gold: "
                        "(2 Daggers, Component Pouch, Arcane Focus, Burglar's Pack, 28 GP) or (50 GP)"
                    ),
                    "Options": ["Starting Equipment", "Gold"],
                    "Function": self.select_starting_equipment,
                },
                {
                    "Text": "Choose 2 skills: Arcana, Deception, Insight, Intimidation, Persuasion, Religion.",
                    "Options": list(set(self.proficiencies["Skills"]) - set(character.proficiencies["Skills"])),
                    "Function": self.select_skills,
                    "Choices": 2,
                    "AllowSame": False,
                },
            ])

        elif level == 2:
            # ── Font of Magic ──────────────────────────────────────────────────
            sorcery_points = _SORCERY_POINTS_PER_LEVEL[level - 1]
            character.special_traits = getattr(character, "special_traits", [])
            character.special_traits.append(
                f"Font of Magic: You have {sorcery_points} Sorcery Points (regain all on Long Rest). "
                "You can convert spell slots to Sorcery Points (1 point per slot level) or spend "
                "Sorcery Points to create spell slots (cost equals the slot level, max 5th level)."
            )
            # ── Metamagic ──────────────────────────────────────────────────────
            character.todo.append({
                "Text": "Metamagic: Choose 2 Metamagic options.",
                "Options": _METAMAGIC_OPTIONS,
                "Choices": 2,
                "Function": self._apply_metamagic,
            })

        elif level == 3:
            # ── Sorcerer Subclass ──────────────────────────────────────────────
            character.todo.append({
                "Text": "Choose your Sorcerer subclass.",
                "Options": self.SORCERER_SUBCLASSES,
                "Choices": 1,
                "Function": self._set_subclass,
            })
            # ── Sorcery Incarnate ──────────────────────────────────────────────
            character.special_traits.append(
                "Sorcery Incarnate: While your Innate Sorcery feature is active, you can use up to "
                "two of your Metamagic options on each spell you cast."
            )

        elif level == 5:
            # ── Sorcerous Restoration ──────────────────────────────────────────
            character.special_traits.append(
                "Sorcerous Restoration: When you finish a Short Rest, you regain 2 expended Sorcery Points."
            )
            # ── Innate Sorcery gains a second use at level 5 ───────────────────
            self._refresh_innate_sorcery(character)

        elif level == 7:
            # ── Arcane Apotheosis ──────────────────────────────────────────────
            character.special_traits.append(
                "Arcane Apotheosis: While your Innate Sorcery feature is active, once per turn when "
                "you cast a Sorcerer spell, you can apply one of your Metamagic options to it without "
                "spending Sorcery Points."
            )

        elif level == 10:
            # ── Metamagic (3rd option) ─────────────────────────────────────────
            character.todo.append({
                "Text": "Metamagic: Choose a 3rd Metamagic option.",
                "Options": _METAMAGIC_OPTIONS,
                "Choices": 1,
                "Function": self._apply_metamagic,
            })

        elif level == 17:
            # ── Metamagic (4th option) ─────────────────────────────────────────
            character.todo.append({
                "Text": "Metamagic: Choose a 4th Metamagic option.",
                "Options": _METAMAGIC_OPTIONS,
                "Choices": 1,
                "Function": self._apply_metamagic,
            })

        elif level == 19:
            # ── Epic Boon ──────────────────────────────────────────────────────
            character.todo.append({
                "Text": "Choose an Epic Boon feat.",
                "Options": ["Epic Boon"],
                "Function": self.select_feat,
            })

        elif level == 20:
            # ── Arcane Apotheosis (capstone) ───────────────────────────────────
            character.special_traits.append(
                "Arcane Apotheosis (Improved): While your Innate Sorcery feature is active, you can "
                "apply any number of your Metamagic options to each spell you cast without spending "
                "Sorcery Points."
            )

        # Update spell slots for every level
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.preparable_spells = PREPARABLE_SPELLS[level - 1]

    # ── Class interface ────────────────────────────────────────────────────────

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        character.special_traits = getattr(character, "special_traits", [])
        # Apply features for every level from 1 up to the sorcerer's starting level
        for lvl in range(1, self.level + 1):
            self._apply_level_features(character, lvl)
        self.completed_levelup_to = self.level
        return character

    def level_up(self, character: Character):
        super().level_up(character)  # increments self.level
        self._apply_level_features(character, self.level)
        return character
