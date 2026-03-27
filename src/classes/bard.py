from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.common import dnd_skills
from src.classes._base import (
    Class, _FULL_CASTER_SLOTS,
)


# Bardic Inspiration die by level
BARDIC_INSPIRATION_DIE = {
    **{lv: "1d6" for lv in range(1, 5)},
    **{lv: "1d8" for lv in range(5, 10)},
    **{lv: "1d10" for lv in range(10, 15)},
    **{lv: "1d12" for lv in range(15, 21)},
}

# Cantrips known by level (index 0 = level 1)
CANTRIPS_KNOWN = [2, 2, 2, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4]

# Prepared spells by level
PREPARABLE_SPELLS = [4, 5, 6, 7, 9, 10, 11, 12, 14, 15, 16, 16, 17, 17, 18, 18, 19, 20, 21, 22]

MUSICAL_INSTRUMENTS = [
    "Bagpipes", "Drum", "Dulcimer", "Flute", "Horn",
    "Lute", "Lyre", "Pan Flute", "Shawm", "Viol",
]

BARD_SUBCLASSES = [
    "College of Dance",
    "College of Glamour",
    "College of Lore",
    "College of Valor",
]


class Bard(Class):
    def __init__(self, level):
        super().__init__(name="Bard", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 8
        self.primary_ability = "Charisma"
        self.spellcasting_ability = "Charisma"
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.proficiencies["Armor"] = ["Light"]
        self.proficiencies["Weapons"] = ["Simple"]
        self.proficiencies["Saving Throws"] = ["Dexterity", "Charisma"]
        self.proficiencies["Skills"] = list(dnd_skills.keys())  # may choose from any skill
        self.completed_levelup_to = 0

    # ── helpers ───────────────────────────────────────────────────────────────

    def _set_skill_proficiencies(self, character: Character, choices, **kwargs):
        character.proficiencies["Skills"] += choices

    def _set_instrument_proficiencies(self, character: Character, choices, **kwargs):
        character.proficiencies["Tools"] += choices

    def _apply_expertise(self, character: Character, choices, **kwargs):
        if not hasattr(character, "expertise"):
            character.expertise = []
        character.expertise += choices

    def _apply_magical_secrets(self, character: Character, choices, **kwargs):
        # TODO: resolve spell names to Spell objects from the full spell list
        if not hasattr(character, "magical_secrets"):
            character.magical_secrets = []
        character.magical_secrets += choices

    def _set_subclass(self, character: Character, choices, **kwargs):
        self.subclass = choices[0]

    # ── Equipment ─────────────────────────────────────────────────────────────

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 90
        else:
            character.add_item([LeatherArmor(), Dagger(quantity=2), EntertainersPack()])
            # Add the instrument the player chose as proficient
            if character.proficiencies["Tools"]:
                character.add_item(character.proficiencies["Tools"][-1])
            character.gold += 19
        return character

    # ── Bardic Inspiration helpers ─────────────────────────────────────────────

    def _build_bardic_inspiration(self, character: Character):
        insp_die = BARDIC_INSPIRATION_DIE[self.level]
        return Spell(
            name="Bardic Inspiration",
            casting_time="Bonus Action",
            range_="60 feet",
            components=[],
            duration="1 minute",
            description=(
                f"You inspire a creature within 60 feet that can hear you. "
                f"Once in the next minute, that creature can roll a Bardic "
                f"Inspiration die ({insp_die}) and add it to one ability check, "
                f"attack roll, or saving throw it makes. A creature can have "
                f"only one Bardic Inspiration die at a time. You can use this "
                f"feature a number of times equal to your Charisma modifier "
                f"(minimum once)."
            ),
            uses_left=max(1, (character.ability_scores.get("Charisma", 10) - 10) // 2),
            cooldown="Long Rest",
        )

    def _refresh_bardic_inspiration(self, character: Character):
        """Replace Bardic Inspiration with an updated version for the current level."""
        character.special_abilities = [
            a for a in character.special_abilities if a.name != "Bardic Inspiration"
        ] + [self._build_bardic_inspiration(character)]

    # ── Level feature application ──────────────────────────────────────────────

    def _apply_level_features(self, character: Character, level: int):
        """Apply all Bard features unlocked at the given level."""

        if level == 1:
            # ── Bardic Inspiration ─────────────────────────────────────────────
            if not isinstance(character.special_abilities, list):
                character.special_abilities = []
            character.special_abilities.append(self._build_bardic_inspiration(character))

            # ── Spellcasting ───────────────────────────────────────────────────
            # Spell slots are tracked on self.spell_slots / self.spell_slots_remaining
            character.special_traits.append("Spellcasting (Charisma)")

            # ── Level 1 todos: resolved LIFO so order here is instruments → skills → equipment
            character.todo.extend([
                {
                    "Text": (
                        "Select starting equipment or gold: "
                        "(Leather Armor, 2 Daggers, Musical Instrument you're proficient in, "
                        "Entertainer's Pack, 19 GP) or (90 GP)"
                    ),
                    "Options": ["Starting Equipment", "Gold"],
                    "Function": self.select_starting_equipment,
                },
                {
                    "Text": (
                        "Choose 3 skills to gain proficiency in "
                        "(Bards may choose from any skill)."
                    ),
                    "Options": list(dnd_skills.keys()),
                    "Choices": 3,
                    "Function": self._set_skill_proficiencies,
                },
                {
                    "Text": "Choose 3 musical instruments to gain proficiency with.",
                    "Options": MUSICAL_INSTRUMENTS,
                    "Choices": 3,
                    "Function": self._set_instrument_proficiencies,
                },
            ])

        elif level == 2:
            # ── Expertise ──────────────────────────────────────────────────────
            character.todo.append({
                "Text": (
                    "Expertise (Level 2): Choose 2 skills or tools you are proficient in "
                    "to gain Expertise (double proficiency bonus on checks with them)."
                ),
                "Options": list(dnd_skills.keys()),
                "Choices": 2,
                "Function": self._apply_expertise,
            })
            # ── Jack of All Trades ─────────────────────────────────────────────
            # Add half proficiency bonus to ability checks not using your proficiency bonus.
            character.special_traits.append("Jack of All Trades")

        elif level == 3:
            # ── Bard College (subclass) ────────────────────────────────────────
            character.todo.append({
                "Text": "Choose a Bard College (subclass).",
                "Options": BARD_SUBCLASSES,
                "Choices": 1,
                "Function": self._set_subclass,
            })
            # TODO: Apply subclass level 3 features based on chosen college

        elif level == 4:
            # ASI handled by base Class.level_up; nothing extra for Bard at level 4
            pass

        elif level == 5:
            # ── Font of Inspiration ────────────────────────────────────────────
            # Bardic Inspiration now recharges on a Short Rest
            for ability in character.special_abilities:
                if ability.name == "Bardic Inspiration":
                    ability.cooldown = "Short Rest"
            character.special_traits.append("Font of Inspiration")

        elif level == 6:
            # TODO: Apply subclass level 6 features based on chosen college
            pass

        elif level == 7:
            # ── Countercharm ───────────────────────────────────────────────────
            character.special_abilities.append(
                Spell(
                    name="Countercharm",
                    casting_time="Action",
                    range_="Self (30-foot emanation)",
                    components=[],
                    duration="Until the start of your next turn",
                    description=(
                        "You launch a magical performance to distract an enemy. "
                        "Until the start of your next turn, you and any ally within "
                        "30 feet of you who can hear you have Advantage on saving "
                        "throws to avoid or end the Charmed or Frightened condition."
                    ),
                )
            )

        elif level == 8:
            # ASI handled by base Class.level_up
            pass

        elif level == 9:
            # ── Expertise (second selection) ───────────────────────────────────
            character.todo.append({
                "Text": (
                    "Expertise (Level 9): Choose 2 more skills or tools you are "
                    "proficient in to gain Expertise."
                ),
                "Options": list(dnd_skills.keys()),
                "Choices": 2,
                "Function": self._apply_expertise,
            })

        elif level == 10:
            # ── Magical Secrets ────────────────────────────────────────────────
            character.todo.append({
                "Text": (
                    "Magical Secrets (Level 10): Choose 2 spells from any class's "
                    "spell list. They count as Bard spells for you and are always "
                    "prepared. Enter the spell names."
                ),
                # TODO: Replace with a real cross-class spell list when available
                "Options": ["(Enter spell name — see full spell list)"],
                "Choices": 2,
                "Function": self._apply_magical_secrets,
            })

        elif level == 11:
            pass

        elif level == 12:
            # ASI handled by base Class.level_up
            pass

        elif level == 13:
            pass

        elif level == 14:
            # TODO: Apply subclass level 14 features based on chosen college
            pass

        elif level == 15:
            pass

        elif level == 16:
            # ASI handled by base Class.level_up
            pass

        elif level == 17:
            pass

        elif level == 18:
            # ── Superior Inspiration ──────────────────────────────────────────
            character.special_traits.append("Superior Inspiration")
            # When you roll Initiative and have no uses of Bardic Inspiration left,
            # you regain one use.

        elif level == 19:
            # ── Epic Boon ─────────────────────────────────────────────────────
            character.todo.append({
                "Text": "Choose an Epic Boon feat.",
                "Options": ["Epic Boon"],
                "Choices": 1,
                "Function": self.select_feat,
            })

        elif level == 20:
            # ── Words of Creation ─────────────────────────────────────────────
            character.special_abilities.append(
                Spell(
                    name="Words of Creation",
                    casting_time="Action",
                    range_="Touch",
                    components=[],
                    duration="Instantaneous",
                    description=(
                        "You have mastered two words of power.\n"
                        "Power Word Fortify: You touch up to 5 willing creatures. "
                        "Distribute up to 5 x (2d12 + Charisma modifier) Hit Points "
                        "among them in any way you choose. This doesn't require "
                        "Concentration and can't be undone.\n"
                        "Power Word Heal: You touch a creature and restore all its "
                        "Hit Points. All conditions afflicting it also end."
                    ),
                    cooldown="Long Rest",
                )
            )

        # ── Bardic Inspiration die update ─────────────────────────────────────
        if level > 1:
            prev_die = BARDIC_INSPIRATION_DIE.get(level - 1, "1d6")
            new_die = BARDIC_INSPIRATION_DIE[level]
            if new_die != prev_die:
                for ability in character.special_abilities:
                    if ability.name == "Bardic Inspiration":
                        ability.description = ability.description.replace(
                            f"({prev_die})", f"({new_die})"
                        )

        # ── Spell slots update ────────────────────────────────────────────────
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.preparable_spells = PREPARABLE_SPELLS[self.level - 1]
        self.completed_levelup_to = level

    # ── Class interface ────────────────────────────────────────────────────────

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        # Apply features for every level from 1 up to the bard's starting level
        for lvl in range(1, self.level + 1):
            self._apply_level_features(character, lvl)
        self.completed_levelup_to = self.level
        return character

    def level_up(self, character: Character):
        super().level_up(character)  # increments self.level, handles ASI at 4/8/12/16
        self._apply_level_features(character, self.level)
        # Always refresh Bardic Inspiration to reflect updated die size
        self._refresh_bardic_inspiration(character)
        return character
