from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.classes._base import (
    Class, _WARLOCK_PACT_SLOTS,
)


# Number of Eldritch Invocations known at each Warlock level (index = level - 1)
_INVOCATIONS_KNOWN = [2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 6, 7, 7, 7, 8, 8, 8, 9, 9, 9]

# Levels at which a new invocation is gained (for _apply_level_features to add a todo)
_INVOCATION_GAIN_LEVELS = {3, 5, 7, 9, 12, 15, 18}


class Warlock(Class):
    WARLOCK_SUBCLASSES = [
        "Archfey Patron",
        "Celestial Patron",
        "Fiend Patron",
        "Great Old One Patron",
    ]
    PACT_BOONS = ["Pact of the Blade", "Pact of the Chain", "Pact of the Tome"]

    # 2024 PHB Eldritch Invocations (overhauled list)
    ELDRITCH_INVOCATIONS = [
        # No prerequisite
        "Agonizing Blast",
        "Armor of Shadows",
        "Beast Speech",
        "Beguiling Influence",
        "Devil's Sight",
        "Eldritch Mind",
        "Eldritch Spear",
        "Eyes of the Rune Keeper",
        "Fiendish Vigor",
        "Gaze of Two Minds",
        "Mask of Many Faces",
        "Misty Visions",
        "One with Shadows",
        "Repelling Blast",
        "Thief of Five Fates",
        # Require Pact of the Blade
        "Eldritch Smite",
        "Lifedrinker",
        "Thirsting Blade",
        "Improved Pact Weapon",
        # Require Pact of the Chain
        "Investment of the Chain Master",
        "Voice of the Chain Master",
        # Require Pact of the Tome
        "Book of Ancient Secrets",
        "Gift of the Depths",
        # Level prerequisites
        "Ascendant Step",          # requires level 9
        "Devouring Blade",         # requires level 12, Thirsting Blade
        "Eldritch Hex",            # requires level 5
        "Far Scribe",              # requires level 5, Pact of the Tome
        "Ghostly Gaze",            # requires level 7
        "Gift of the Protectors",  # requires level 9, Pact of the Tome
        "Grasp of Hadar",
        "Maddening Hex",           # requires level 5
        "Master of Myriad Forms",  # requires level 15
        "Otherworldly Leap",       # requires level 9
        "Sculptor of Flesh",       # requires level 7
        "Shroud of Shadow",        # requires level 15
        "Trickster's Escape",      # requires level 7, Pact of the Trickster (chain)
        "Undying Servitude",       # requires level 5
        "Visions of Distant Realms",  # requires level 15
        "Witch Sight",             # requires level 15
    ]

    def __init__(self, level):
        super().__init__(name="Warlock", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 8
        self.primary_ability = "Charisma"
        self.spellcasting_ability = "Charisma"
        self.pact_slots = dict(_WARLOCK_PACT_SLOTS[level - 1])
        self.pact_slots_remaining = dict(_WARLOCK_PACT_SLOTS[level - 1])
        self.proficiencies["Armor"] = ["Light"]
        self.proficiencies["Weapons"] = ["Simple"]
        self.proficiencies["Saving Throws"] = ["Wisdom", "Charisma"]
        self.proficiencies["Skills"] = [
            "Arcana", "Deception", "History", "Intimidation",
            "Investigation", "Nature", "Religion",
        ]
        self.completed_levelup_to = 0

    # ── Equipment ─────────────────────────────────────────────────────────────

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 100
        else:
            character.add_item([
                LeatherArmor(), Sickle(), ComponentPouch(),
                ArcaneFocus(), ScholarsPack(),
            ])
            character.gold += 15
        return character

    # ── Invocation helpers ────────────────────────────────────────────────────

    def _apply_invocations(self, character: Character, choices, **kwargs):
        if not hasattr(character, "eldritch_invocations"):
            character.eldritch_invocations = []
        character.eldritch_invocations += choices

    def _invocation_todo(self, count=1):
        return {
            "Text": f"Choose {'an' if count == 1 else count} Eldritch Invocation{'s' if count > 1 else ''}.",
            "Options": self.ELDRITCH_INVOCATIONS,
            "Choices": count,
            "Function": self._apply_invocations,
        }

    # ── Subclass / Pact Boon helpers ──────────────────────────────────────────

    def _set_subclass(self, character: Character, choices, **kwargs):
        self.subclass = choices[0]

    def _apply_pact_boon(self, character: Character, choices, **kwargs):
        boon = choices[0]
        descriptions = {
            "Pact of the Blade": (
                "You can use your action to create a pact weapon in your empty hand. "
                "You are proficient with it and can use Charisma for its attack and damage rolls. "
                "It counts as magical. It disappears if you die, dismiss it, or create a new one."
            ),
            "Pact of the Chain": (
                "You learn the Find Familiar spell and can cast it as a ritual. "
                "Your familiar can take the form of a special creature: imp, pseudodragon, quasit, "
                "or sprite. Your familiar can forgo its attack to give you Advantage on your next attack roll."
            ),
            "Pact of the Tome": (
                "Your patron gives you a Book of Shadows. When you gain this boon, choose three cantrips "
                "from any class spell list. While the book is on your person, you can cast those cantrips "
                "at will. You also gain two 1st-level spells with the Ritual tag from any class list; "
                "you can cast them as rituals without expending a spell slot."
            ),
        }
        character.special_traits.append(
            f"Pact Boon — {boon}: {descriptions.get(boon, '')}"
        )

    # ── Pact Magic trait string ───────────────────────────────────────────────

    def _pact_magic_trait(self):
        pact_level = list(self.pact_slots.keys())[0]
        pact_count = list(self.pact_slots.values())[0]
        return (
            f"Pact Magic: You have {pact_count} {pact_level}th-level spell slot(s) "
            "that recharge on a Short Rest or Long Rest."
        )

    # ── Level feature application ──────────────────────────────────────────────

    def _apply_level_features(self, character: Character, level: int):
        """Apply all Warlock features unlocked at the given level."""

        if level == 1:
            if not isinstance(character.special_abilities, list):
                character.special_abilities = []

            # ── Pact Magic ────────────────────────────────────────────────────
            character.special_traits.append(self._pact_magic_trait())

            # ── Eldritch Invocations (2 at level 1) ──────────────────────────
            character.todo.extend([
                {
                    "Text": (
                        "Select starting equipment or gold: "
                        "(Leather Armor, Sickle, Component Pouch, Arcane Focus, Scholar's Pack, 15 GP) or (100 GP)"
                    ),
                    "Options": ["Starting Equipment", "Gold"],
                    "Function": self.select_starting_equipment,
                },
                {
                    "Text": "Choose 2 skills: Arcana, Deception, History, Intimidation, Investigation, Nature, Religion.",
                    "Options": list(set(self.proficiencies["Skills"]) - set(character.proficiencies.get("Skills", []))),
                    "Choices": 2,
                    "AllowSame": False,
                    "Function": self.select_skills,
                },
                self._invocation_todo(count=2),
            ])

        elif level == 2:
            # ── Magical Cunning ───────────────────────────────────────────────
            character.special_traits.append(
                "Magical Cunning: If all your Pact Magic spell slots are expended, you can perform "
                "a 1-minute ritual to regain half your maximum Pact Magic slots (rounded up). "
                "Usable once per Long Rest."
            )

        elif level == 3:
            # ── Warlock Subclass ──────────────────────────────────────────────
            character.todo.append({
                "Text": "Choose your Warlock subclass (Otherworldly Patron).",
                "Options": self.WARLOCK_SUBCLASSES,
                "Function": self._set_subclass,
            })
            # ── Pact Boon ─────────────────────────────────────────────────────
            character.todo.append({
                "Text": "Choose your Pact Boon.",
                "Options": self.PACT_BOONS,
                "Function": self._apply_pact_boon,
            })
            # ── Eldritch Invocation (gain 1 more) ─────────────────────────────
            character.todo.append(self._invocation_todo(count=1))

        elif level == 4:
            # ASI handled by base class level_up
            pass

        elif level == 5:
            # ── Contact Patron ────────────────────────────────────────────────
            character.special_traits.append(
                "Contact Patron: You gain the ability to contact your otherworldly patron. "
                "You can cast Commune as a ritual to contact your patron without expending a spell slot. "
                "The GM portrays the patron."
            )
            # ── Eldritch Invocation (gain 1 more) ─────────────────────────────
            character.todo.append(self._invocation_todo(count=1))

        elif level == 6:
            # Subclass feature — no generic feature here
            pass

        elif level == 7:
            # ── Eldritch Invocation (gain 1 more) ─────────────────────────────
            character.todo.append(self._invocation_todo(count=1))

        elif level == 8:
            # ASI handled by base class level_up
            pass

        elif level == 9:
            # ── Eldritch Invocation (gain 1 more) ─────────────────────────────
            character.todo.append(self._invocation_todo(count=1))

        elif level == 10:
            # Subclass feature — no generic feature here
            pass

        elif level == 11:
            # ── Mystic Arcanum (6th level) ────────────────────────────────────
            character.special_traits.append(
                "Mystic Arcanum (6th): Your patron bestows a magical secret called an arcanum. "
                "Choose one 6th-level Warlock spell as your arcanum. You can cast it once without "
                "expending a spell slot, and you regain the ability to do so when you finish a Long Rest."
            )
            character.todo.append({
                "Text": "Choose a 6th-level Warlock spell for your Mystic Arcanum.",
                "Options": [
                    "Eyebite", "Flesh to Stone", "Investiture of Flame", "Investiture of Ice",
                    "Investiture of Stone", "Investiture of Wind", "Mass Suggestion",
                    "Mental Prison", "Scatter", "Soul Cage", "Tasha's Otherworldly Guise",
                    "True Seeing",
                ],
                "Function": lambda char, choices, **kw: char.special_traits.append(
                    f"Mystic Arcanum (6th) — {choices[0]}"
                ),
            })

        elif level == 12:
            # ASI handled by base class level_up
            # ── Eldritch Invocation (gain 1 more) ─────────────────────────────
            character.todo.append(self._invocation_todo(count=1))

        elif level == 13:
            # ── Mystic Arcanum (7th level) ────────────────────────────────────
            character.special_traits.append(
                "Mystic Arcanum (7th): Choose one 7th-level Warlock spell as your arcanum. "
                "You can cast it once without expending a spell slot (regain on Long Rest)."
            )
            character.todo.append({
                "Text": "Choose a 7th-level Warlock spell for your Mystic Arcanum.",
                "Options": [
                    "Crown of Stars", "Dream of the Blue Veil", "Etherealness",
                    "Finger of Death", "Forcecage", "Plane Shift", "Power Word Pain",
                    "Simulacrum", "Symbol", "Teleport",
                ],
                "Function": lambda char, choices, **kw: char.special_traits.append(
                    f"Mystic Arcanum (7th) — {choices[0]}"
                ),
            })

        elif level == 14:
            # Subclass feature — no generic feature here
            pass

        elif level == 15:
            # ── Mystic Arcanum (8th level) ────────────────────────────────────
            character.special_traits.append(
                "Mystic Arcanum (8th): Choose one 8th-level Warlock spell as your arcanum. "
                "You can cast it once without expending a spell slot (regain on Long Rest)."
            )
            character.todo.append({
                "Text": "Choose an 8th-level Warlock spell for your Mystic Arcanum.",
                "Options": [
                    "Abi-Dalzim's Horrid Wilting", "Demiplane", "Dominate Monster",
                    "Feeblemind", "Glibness", "Maddening Darkness", "Power Word Stun",
                ],
                "Function": lambda char, choices, **kw: char.special_traits.append(
                    f"Mystic Arcanum (8th) — {choices[0]}"
                ),
            })
            # ── Eldritch Invocation (gain 1 more) ─────────────────────────────
            character.todo.append(self._invocation_todo(count=1))

        elif level == 16:
            # ASI handled by base class level_up
            pass

        elif level == 17:
            # ── Mystic Arcanum (9th level) ────────────────────────────────────
            character.special_traits.append(
                "Mystic Arcanum (9th): Choose one 9th-level Warlock spell as your arcanum. "
                "You can cast it once without expending a spell slot (regain on Long Rest)."
            )
            character.todo.append({
                "Text": "Choose a 9th-level Warlock spell for your Mystic Arcanum.",
                "Options": [
                    "Astral Projection", "Foresight", "Gate", "Imprisonment",
                    "Power Word Kill", "Psychic Scream", "Shapechange",
                    "True Polymorph", "Weird", "Wish",
                ],
                "Function": lambda char, choices, **kw: char.special_traits.append(
                    f"Mystic Arcanum (9th) — {choices[0]}"
                ),
            })

        elif level == 18:
            # ── Eldritch Master ───────────────────────────────────────────────
            character.special_traits.append(
                "Eldritch Master: You can spend 1 minute entreating your patron for aid to regain all "
                "expended Pact Magic slots. Once you use this feature, you can't do so again until you "
                "finish a Long Rest."
            )
            # ── Eldritch Invocation (gain 1 more) ─────────────────────────────
            character.todo.append(self._invocation_todo(count=1))

        elif level == 19:
            # ── Epic Boon ─────────────────────────────────────────────────────
            character.todo.append({
                "Text": "Choose an Epic Boon feat.",
                "Options": ["Epic Boon of Fate", "Epic Boon of Spell Recall",
                            "Epic Boon of the Night Spirit", "Epic Boon of Truesight"],
                "Function": lambda char, choices, **kw: char.feats.append(choices[0]),
            })

        elif level == 20:
            # ── Hex Master ────────────────────────────────────────────────────
            character.special_traits.append(
                "Hex Master: If Hex is among your prepared spells, you can cast it without expending "
                "a spell slot. Additionally, you can now target any number of creatures with Hex "
                "simultaneously by expending one spell slot per additional target."
            )

        # Always update pact slots to reflect current level
        self.pact_slots = dict(_WARLOCK_PACT_SLOTS[level - 1])
        self.pact_slots_remaining = dict(_WARLOCK_PACT_SLOTS[level - 1])

    # ── Class interface ────────────────────────────────────────────────────────

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        # Apply features for every level from 1 up to the warlock's starting level
        for lvl in range(1, self.level + 1):
            self._apply_level_features(character, lvl)
        self.completed_levelup_to = self.level
        return character

    def level_up(self, character: Character):
        super().level_up(character)  # increments self.level and handles ASI at 4/8/12/16
        self._apply_level_features(character, self.level)
        return character
