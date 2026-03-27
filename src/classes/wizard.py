from src.creatures import Character
from src.spells import Spell, get_spells
from src.items import *
from src.classes._base import (
    Class, _FULL_CASTER_SLOTS,
)


class Wizard(Class):
    WIZARD_SUBCLASSES = ["Abjurer", "Diviner", "Evoker", "Illusionist"]
    # Cantrips known per level (1-20)
    CANTRIPS_KNOWN = [3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5]
    PREPARABLE_SPELLS = [4, 5, 6, 7, 9, 10, 11, 12, 14, 15, 16, 16, 17, 18, 19, 21, 22, 23, 24, 25]

    def __init__(self, level):
        super().__init__(name="Wizard", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 6
        self.primary_ability = "Intelligence"
        self.spellcasting_ability = "Intelligence"
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.proficiencies["Weapons"] = ["Simple"]
        self.proficiencies["Saving Throws"] = ["Intelligence", "Wisdom"]
        self.proficiencies["Skills"] = []
        self.completed_levelup_to = 1

    # ── Equipment ─────────────────────────────────────────────────────────────

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 55
        else:
            character.add_item([
                Dagger(quantity=2),
                ArcaneFocus(),  # Quarterstaff used as arcane focus
                Robe(),
                ScholarsPack(),
                SpellBook(),
            ])
            character.gold += 5

    # ── Spells ─────────────────────────────────────────────────────────────

    def _select_spells(self, character: Character, choices, **kwargs):
        spellbook = None
        spells = get_spells(classes=["Wizard"])
        for choice in choices:
            adding_spell = None
            for spell in spells:
                if spell.name == choice:
                    adding_spell = spell
                    break
            if adding_spell is None:
                raise Exception(f"{choice} is not a valid Wizard spell choice.")
            if adding_spell.level == 0:
                if adding_spell.name in character.spells:
                    raise Exception(f"{character.name} already knows the cantrip {adding_spell.name}.")
                # if choices are cantrips, no need to add to spellbook as cantrips are always available to prepare and cast
                character.spells += [adding_spell]
            else:
                spellbook = [_ for _ in character.inventory if isinstance(_, SpellBook)]
                if len(spellbook) == 0:
                    raise Exception(f"{character.name} does not have a spellbook to add spells to.")
                spellbook[0].add_spell(adding_spell)

    # ── Skill / expertise helpers ──────────────────────────────────────────────

    def _set_skill_proficiencies(self, character: Character, choices, **kwargs):
        character.proficiencies["Skills"] += choices

    def _set_subclass(self, character: Character, choices, **kwargs):
        self.subclass = choices[0]

    def _apply_expertise(self, character: Character, choices, **kwargs):
        if not hasattr(character, "expertise"):
            character.expertise = []
        character.expertise += choices

    # ── Level feature application ──────────────────────────────────────────────

    def _apply_level_features(self, character: Character, level: int):
        """Apply all Wizard features unlocked at the given level."""

        if level == 1:
            if not isinstance(character.special_abilities, list):
                character.special_abilities = []

            # ── Arcane Recovery ────────────────────────────────────────────────
            arcane_recovery_slots = (self.level + 1) // 2
            character.special_abilities.append(Spell(
                name="Arcane Recovery",
                casting_time="Special",
                range_="Self",
                components=[],
                duration="Instantaneous",
                description=(
                    f"Once per day during a Short Rest, you can recover expended spell slots "
                    f"with a combined level up to {arcane_recovery_slots} (no slot above 5th level)."
                ),
                uses_left=1,
                cooldown="Long Rest",
            ))

            # ── Ritual Adept ───────────────────────────────────────────────────
            character.special_traits.append(
                "Ritual Adept: You can cast any spell as a Ritual if that spell has the Ritual tag and "
                "the spell is in your spellbook. You need not have the spell prepared."
            )

            # ── Starting todo items ─────────────────────────────────────────────
            character.todo.extend([
                {
                    "Text": "Choose 6 1st-level Wizard spells to add to your spellbook.",
                    "Options": [spell.name for spell in get_spells(classes=["Wizard"], levels=[1])],
                    "Choices": 6,
                    "Function": self._select_spells,
                    "AllowSame": False
                },
                {
                    "Text": "Choose 3 cantrips from the Wizard spell list to add to your repertoire.",
                    "Options": [spell.name for spell in get_spells(classes=["Wizard"], levels=[0])],
                    "Choices": 3,
                    "Function": self._select_spells,
                    "AllowSame": False
                },
                {
                    "Text": "Choose 2 skills: Arcana, History, Insight, Investigation, Medicine, Nature, or Religion.",
                    "Options": ["Arcana", "History", "Insight", "Investigation", "Medicine", "Nature", "Religion"],
                    "Choices": 2,
                    "Function": self._set_skill_proficiencies,
                    "AllowSame": False
                },
                {
                    "Text": (
                        "Select starting equipment or gold: "
                        "(A) 2 Daggers, Arcane Focus, Robe, Spellbook, Scholar's Pack, 5 GP  or  (B) 55 GP"
                    ),
                    "Options": ["Starting Equipment", "Gold"],
                    "Function": self.select_starting_equipment,
                }
            ])

        elif level == 2:
            # ── Scholar ────────────────────────────────────────────────────────
            # Gain proficiency (if not already) and Expertise in Arcana or History.
            character.todo.append({
                "Text": "Scholar: Choose 1 skill to gain Expertise in (Arcana or History).",
                "Options": ["Arcana", "History"],
                "Function": self._apply_expertise,
            })

        elif level == 3:
            # ── Wizard Subclass ────────────────────────────────────────────────
            character.todo.append({
                "Text": "Choose your Wizard subclass.",
                "Options": self.WIZARD_SUBCLASSES,
                "Function": self._set_subclass,
            })

        elif level == 4:
            character.todo.append({
                "Text": "Choose an additional cantrip from the Wizard spell list to add to your repertoire.",
                "Options": list(set([spell.name for spell in get_spells(classes=["Wizard"], levels=[0])]) - set(character.spells)),
                "Choices": 1,
                "Function": self._select_spells,
                "AllowSame": False
            })

        elif level == 5:
            # ── Memorize Spell ─────────────────────────────────────────────────
            character.special_traits.append(
                "Memorize Spell: Whenever you finish a Short Rest, you can study a spell from another "
                "Wizard's spellbook and add it to your own without the usual gold and time cost. "
                "The spell must be of a level you can prepare."
            )

        elif level == 6:
            # ── Subclass feature ───────────────────────────────────────────────
            character.todo.append({
                "Text": f"Subclass feature unlocked (level 6 {getattr(self, 'subclass', 'Wizard subclass')} feature). "
                        "Apply your subclass feature from your chosen Wizard subclass.",
                "Options": ["None"],
                "Function": lambda char, choices, **kw: None,
            })

        elif level == 10:
            # ── Subclass feature ───────────────────────────────────────────────
            character.todo.append({
                "Text": f"Subclass feature unlocked (level 10 {getattr(self, 'subclass', 'Wizard subclass')} feature). "
                        "Apply your subclass feature from your chosen Wizard subclass.",
                "Options": ["None"],
                "Function": lambda char, choices, **kw: None,
            })
            character.todo.append({
                "Text": "Choose an additional cantrip from the Wizard spell list to add to your repertoire.",
                "Options": list(set([spell.name for spell in get_spells(classes=["Wizard"], levels=[0])]) - set(character.spells)),
                "Choices": 1,
                "Function": self._select_spells,
                "AllowSame": False
            })

        elif level == 14:
            # ── Subclass feature ───────────────────────────────────────────────
            character.todo.append({
                "Text": f"Subclass feature unlocked (level 14 {getattr(self, 'subclass', 'Wizard subclass')} feature). "
                        "Apply your subclass feature from your chosen Wizard subclass.",
                "Options": ["None"],
                "Function": lambda char, choices, **kw: None,
            })

        elif level == 18:
            # ── Spell Mastery ──────────────────────────────────────────────────
            character.special_abilities.append(Spell(
                name="Spell Mastery",
                casting_time="Special",
                range_="Self",
                components=[],
                duration="Permanent",
                description=(
                    "Choose one 1st-level and one 2nd-level Wizard spell in your spellbook. "
                    "You can cast each of those spells at their lowest level without expending a spell slot. "
                    "You can change your chosen spells after finishing a Long Rest."
                ),
            ))

        elif level == 19:
            # ── Epic Boon ──────────────────────────────────────────────────────
            character.todo.append({
                "Text": "Choose an Epic Boon feat.",
                "Options": [],
                "Function": lambda char, choices, **kw: None,
            })

        elif level == 20:
            # ── Signature Spells ───────────────────────────────────────────────
            character.special_abilities.append(Spell(
                name="Signature Spells",
                casting_time="Special",
                range_="Self",
                components=[],
                duration="Permanent",
                description=(
                    "Choose two 3rd-level Wizard spells in your spellbook as your signature spells. "
                    "You always have them prepared and can cast each of them once without expending "
                    "a spell slot. You regain both uses when you finish a Long Rest."
                ),
                uses_left=2,
                cooldown="Long Rest",
            ))

        # Update spell slots to reflect current level
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.preparable_spells = self.PREPARABLE_SPELLS[self.level - 1]
        self.completed_levelup_to = level

    # ── Class interface ────────────────────────────────────────────────────────

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        self.completed_levelup_to = 1
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        # Apply features for every level from 1 up to the wizard's starting level
        for lvl in range(1, self.level + 1):
            self._apply_level_features(character, lvl)
        return character

    def level_up(self, character: Character):
        super().level_up(character)  # increments self.level
        self._apply_level_features(character, self.level)
        return character
