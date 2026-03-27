from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.classes._base import (
    Class, _FULL_CASTER_SLOTS,
)


# Prepared spells by level
PREPARABLE_SPELLS = [4, 5, 6, 7, 9, 10, 11, 12, 14, 15, 16, 16, 17, 17, 18, 18, 19, 20, 21, 22]


# CR cap for Wild Shape by druid level (2024 PHB)
# Lv 1: no Wild Shape; Lv 2-3: CR 1/4; Lv 4-7: CR 1/2; Lv 8+: CR 1
def _wild_shape_cr(level: int) -> str:
    if level >= 8:
        return "1"
    elif level >= 4:
        return "1/2"
    else:
        return "1/4"


class Druid(Class):
    DRUID_SUBCLASSES = [
        "Circle of the Land",
        "Circle of the Moon",
        "Circle of the Sea",
        "Circle of the Stars",
    ]

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
        self.proficiencies["Skills"] = [
            "Arcana", "Animal Handling", "Insight", "Medicine",
            "Nature", "Perception", "Religion", "Survival",
        ]
        self.completed_levelup_to = 0

    # ── Equipment ─────────────────────────────────────────────────────────────

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 50
        else:
            character.add_item([
                LeatherArmor(), Shield(), Sickle(),
                DruidicFocus(), HerbalismKit(), ExplorersPack(),
            ])
        return character

    # ── Primal Order ──────────────────────────────────────────────────────────

    def _apply_primal_order(self, character: Character, choices, **kwargs):
        """
        Warden: gain Heavy Armor and Martial Weapon proficiency.
        Magician: learn one extra cantrip and gain proficiency in Arcana or Nature.
        """
        if "Warden" in choices:
            character.proficiencies["Armor"].append("Heavy")
            character.proficiencies["Weapons"].append("Martial")
        else:
            # Magician: +1 cantrip (tracked as todo) and one skill from Arcana/Nature
            character.todo.append({
                "Text": (
                    "Primal Order (Magician): Choose one additional skill proficiency "
                    "from Arcana or Nature."
                ),
                "Options": ["Arcana", "Nature"],
                "Choices": 1,
                "Function": lambda char, ch: char.proficiencies["Skills"].extend(ch),
            })
            character.todo.append({
                "Text": (
                    "Primal Order (Magician): Choose one additional Druid cantrip to learn."
                ),
                "Options": [],  # TODO: populate with full druid cantrip list
                "Function": lambda char, ch: None,
            })

    # ── Subclass ──────────────────────────────────────────────────────────────

    def _set_subclass(self, character: Character, choices, **kwargs):
        self.subclass = choices[0]

    # ── Skill proficiencies ───────────────────────────────────────────────────

    def _set_skill_proficiencies(self, character: Character, choices, **kwargs):
        character.proficiencies["Skills"] += choices

    # ── Wild Shape helpers ────────────────────────────────────────────────────

    def _build_wild_shape_ability(self):
        cr = _wild_shape_cr(self.level)
        return Spell(
            name="Wild Shape",
            casting_time="Bonus Action",
            range_="Self",
            components=[],
            duration="Concentration, up to 1 hour",
            description=(
                f"You magically assume the shape of a Beast with a Challenge Rating "
                f"of {cr} or lower. You retain your mental ability scores, alignment, "
                f"and personality. You can't cast spells while transformed (until you "
                f"gain Beast Spells at level 18), but you can maintain Concentration "
                f"on a spell. You revert if you drop to 0 HP, fall unconscious, or "
                f"choose to as a Bonus Action. Wild Shape uses recharge on a Short or "
                f"Long Rest."
            ),
            uses_left=2,
            cooldown="Short Rest",
        )

    def _refresh_wild_shape(self, character: Character):
        """Replace Wild Shape ability with a version reflecting the current CR cap."""
        character.special_abilities = [
            a for a in character.special_abilities if a.name != "Wild Shape"
        ] + [self._build_wild_shape_ability()]

    # ── Level feature application ─────────────────────────────────────────────

    def _apply_level_features(self, character: Character, level: int):
        """Apply all Druid features unlocked at the given level."""

        if level == 1:
            if not isinstance(character.special_abilities, list):
                character.special_abilities = []

            # ── Druidic ────────────────────────────────────────────────────────
            character.special_traits.append(
                "Druidic: You know Druidic, the secret language of druids. You can "
                "speak it, use it to leave hidden messages, and automatically spot "
                "such messages. Others spot them only on a successful DC 15 Perception "
                "check."
            )

            # ── Spellcasting ───────────────────────────────────────────────────
            character.special_traits.append(
                "Spellcasting (Wisdom): You prepare Druid spells from the full Druid "
                "spell list after each Long Rest. Your spell save DC and attack bonus "
                "are based on Wisdom."
            )

            # ── Level-1 todos ──────────────────────────────────────────────────
            character.todo.extend([
                {
                    "Text": (
                        "Select starting equipment or gold: "
                        "(Leather Armor, Shield, Sickle, Druidic Focus, Herbalism Kit, "
                        "Explorer's Pack) or (50 GP)"
                    ),
                    "Options": ["Starting Equipment", "Gold"],
                    "Function": self.select_starting_equipment,
                },
                {
                    "Text": (
                        "Choose 2 skills: Arcana, Animal Handling, Insight, Medicine, "
                        "Nature, Perception, Religion, Survival."
                    ),
                    "Options": self.proficiencies["Skills"],
                    "Choices": 2,
                    "AllowSame": False,
                    "Function": self._set_skill_proficiencies,
                },
                {
                    "Text": (
                        "Choose Primal Order: Warden (Heavy Armor + Martial Weapon proficiency) "
                        "or Magician (extra cantrip + Arcana or Nature proficiency)."
                    ),
                    "Options": ["Warden", "Magician"],
                    "Choices": 1,
                    "Function": self._apply_primal_order,
                },
            ])

        elif level == 2:
            # ── Wild Shape ─────────────────────────────────────────────────────
            character.special_abilities.append(self._build_wild_shape_ability())

            # ── Wild Companion ─────────────────────────────────────────────────
            character.special_traits.append(
                "Wild Companion: You can expend a use of Wild Shape to cast Find Familiar "
                "without material components. The familiar always takes the form of a Fey "
                "creature, and it disappears when you finish a Long Rest."
            )

        elif level == 3:
            # ── Druid Subclass ─────────────────────────────────────────────────
            character.todo.append({
                "Text": "Choose your Druid Circle (subclass).",
                "Options": self.DRUID_SUBCLASSES,
                "Choices": 1,
                "Function": self._set_subclass,
            })

        elif level == 4:
            # ── Wild Shape CR improves to 1/2 ──────────────────────────────────
            self._refresh_wild_shape(character)

        elif level == 7:
            # ── Elemental Fury ─────────────────────────────────────────────────
            character.todo.append({
                "Text": (
                    "Elemental Fury: Choose one damage type — Cold, Fire, Lightning, or Thunder. "
                    "Once per turn when you deal damage with a cantrip or a melee attack, you "
                    "deal an extra 1d6 damage of the chosen type."
                ),
                "Options": ["Cold", "Fire", "Lightning", "Thunder"],
                "Choices": 1,
                "Function": lambda char, ch, _self=self: setattr(
                    _self, "elemental_fury_type", ch[0]
                ),
            })
            character.special_traits.append(
                "Elemental Fury: Once per turn, one of your cantrip hits or melee attack "
                "hits deals an extra 1d6 damage of your chosen element (Cold, Fire, "
                "Lightning, or Thunder)."
            )

        elif level == 8:
            # ── Wild Shape CR improves to 1 ────────────────────────────────────
            self._refresh_wild_shape(character)

        elif level == 9:
            # ── Wild Resurgence ────────────────────────────────────────────────
            character.special_traits.append(
                "Wild Resurgence: Once per turn, if you have no Wild Shape uses remaining, "
                "you can expend one spell slot (of any level) to regain one Wild Shape use. "
                "Additionally, if you have no spell slots remaining, you can expend one "
                "Wild Shape use to regain one expended 1st-level spell slot."
            )

        elif level == 15:
            # ── Improved Elemental Fury ────────────────────────────────────────
            character.special_traits.append(
                "Improved Elemental Fury: Your Elemental Fury extra damage increases to 2d6."
            )

        elif level == 18:
            # ── Beast Spells ───────────────────────────────────────────────────
            character.special_traits.append(
                "Beast Spells: While in Wild Shape form you can cast Druid spells, provided "
                "those spells don't require material components. You can perform the somatic "
                "and verbal components of such spells using your beast form."
            )

        elif level == 19:
            # ── Epic Boon ──────────────────────────────────────────────────────
            character.todo.append({
                "Text": "Choose an Epic Boon feat.",
                "Options": [],  # TODO: Choose an Epic Boon feat.
                "Function": lambda char, ch: char.feats.append(ch[0]) if ch else None,
            })

        elif level == 20:
            # ── Archdruid ──────────────────────────────────────────────────────
            character.special_traits.append(
                "Archdruid: Your maximum number of Wild Shape uses increases to 3, and you "
                "regain all uses whenever you finish a Short or Long Rest. Additionally, the "
                "maximum CR for your Wild Shape increases to 5 (or to your druid level ÷ 3, "
                "whichever is lower; minimum 5 at this level). You can also ignore the "
                "Concentration requirement for one ongoing spell you maintain while in "
                "Wild Shape form."
            )
            # Refresh Wild Shape to represent the CR-5 cap
            self._refresh_wild_shape(character)

        # ── Spell slot update (every level) ───────────────────────────────────
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.preparable_spells = PREPARABLE_SPELLS[self.level - 1]
        self.completed_levelup_to = level

    # ── Class interface ────────────────────────────────────────────────────────

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        # Apply features for every level from 1 up to the druid's starting level
        for lvl in range(1, self.level + 1):
            self._apply_level_features(character, lvl)
        self.completed_levelup_to = self.level
        return character

    def level_up(self, character: Character):
        super().level_up(character)  # increments self.level
        self._apply_level_features(character, self.level)
        return character
