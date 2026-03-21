from src.creatures import Character
from src.items import *
from src.classes._base import (
    Class, _WARLOCK_PACT_SLOTS,
)


class Warlock(Class):
    WARLOCK_SUBCLASSES = ["Archfey Patron", "Celestial Patron", "Fiend Patron", "Great Old One Patron"]
    PACT_BOONS = ["Pact of the Blade", "Pact of the Chain", "Pact of the Tome"]
    ELDRITCH_INVOCATIONS = [
        "Agonizing Blast", "Armor of Shadows", "Ascendant Step", "Beast Speech",
        "Beguiling Influence", "Devil's Sight", "Eldritch Mind", "Eldritch Smite",
        "Eldritch Spear", "Eyes of the Rune Keeper", "Fiendish Vigor",
        "Gaze of Two Minds", "Ghostly Gaze", "Gift of the Depths",
        "Grasp of Hadar", "Investment of the Chain Master", "Lifedrinker",
        "Mask of Many Faces", "Master of Myriad Forms", "Misty Visions",
        "One with Shadows", "Otherworldly Leap", "Repelling Blast",
        "Sculptor of Flesh", "Thirsting Blade", "Undying Servitude",
        "Visions of Distant Realms", "Voice of the Chain Master", "Witch Sight",
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
        self.proficiencies["Skills"] = []
        self.completed_levelup_to = 1

    def _set_skill_proficiencies(self, character: Character, choices):
        character.proficiencies["Skills"] += choices

    def _set_subclass(self, character: Character, choices):
        self.subclass = choices[0]

    def _apply_invocations(self, character: Character, choices):
        if not hasattr(character, "eldritch_invocations"):
            character.eldritch_invocations = []
        character.eldritch_invocations += choices

    def _apply_pact_boon(self, character: Character, choices):
        boon = choices[0]
        character.special_traits.append(
            f"Pact Boon — {boon}: "
            + {
                "Pact of the Blade": "Create a pact weapon (any weapon) that uses your Charisma for attack/damage. Counts as magical.",
                "Pact of the Chain": "Cast Find Familiar as a ritual. Your familiar can be a special form (imp, pseudodragon, quasit, or sprite).",
                "Pact of the Tome": "Your patron gives you a Book of Shadows containing 3 cantrips from any class list and 2 1st-level rituals.",
            }.get(boon, "")
        )

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 100
        else:
            character.add_item([LeatherArmor(), Sickle(), ComponentPouch(), ArcaneFocus(), ScholarsPack()])
            character.gold += 15

    def _apply_level(self, character: Character, level: int):
        if level == 2:
            character.special_traits.append(
                "Magical Cunning: If all your Pact Magic spell slots are expended, you can perform "
                "a 1-minute ritual to regain half your maximum Pact slots (rounded up). "
                "Usable once per Long Rest."
            )
        elif level == 3:
            character.todo.append({
                "Text": "Choose your Warlock subclass (Otherworldly Patron).",
                "Options": self.WARLOCK_SUBCLASSES,
                "Function": self._set_subclass,
            })
            character.todo.append({
                "Text": "Choose your Pact Boon.",
                "Options": self.PACT_BOONS,
                "Function": self._apply_pact_boon,
            })
        elif level == 5:
            character.special_traits.append(
                "Contact Patron: You can cast Commune as a ritual to contact your patron (no spell slot required)."
            )
        elif level == 7:
            character.todo.append({
                "Text": "Choose an additional Eldritch Invocation.",
                "Options": self.ELDRITCH_INVOCATIONS,
                "Function": self._apply_invocations,
            })
        elif level == 11:
            character.special_traits.append(
                "Mystic Arcanum (6th): Choose one 6th-level spell from the Warlock list. "
                "Cast it once without expending a spell slot (regain on Long Rest)."
            )
        elif level == 13:
            character.special_traits.append(
                "Mystic Arcanum (7th): Choose one 7th-level spell. Cast it once per Long Rest for free."
            )
        elif level == 15:
            character.special_traits.append(
                "Mystic Arcanum (8th): Choose one 8th-level spell. Cast it once per Long Rest for free."
            )
        elif level == 17:
            character.special_traits.append(
                "Mystic Arcanum (9th): Choose one 9th-level spell. Cast it once per Long Rest for free."
            )
        elif level == 18:
            character.special_traits.append(
                "Eldritch Master: Spend 1 minute communing with your patron to regain all expended "
                "Pact Magic slots. Usable once per Long Rest."
            )
        elif level == 20:
            character.special_traits.append(
                "Hex Master: You can cast Hex at will without expending a spell slot."
            )
        self.pact_slots = dict(_WARLOCK_PACT_SLOTS[level - 1])
        self.pact_slots_remaining = dict(_WARLOCK_PACT_SLOTS[level - 1])
        self.completed_levelup_to = level

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        self.completed_levelup_to = 1
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        pact_level = list(self.pact_slots.keys())[0]
        pact_count = list(self.pact_slots.values())[0]
        character.special_traits.append(
            f"Pact Magic: You have {pact_count} {pact_level}th-level spell slot(s) that recharge on a Short Rest."
        )
        for lv in range(2, self.level + 1):
            self._apply_level(character, lv)
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
                "Options": ["Arcana", "Deception", "History", "Intimidation", "Investigation", "Nature", "Religion"],
                "Choices": 2,
                "Function": self._set_skill_proficiencies,
            },
            {
                "Text": "Choose 2 Eldritch Invocations.",
                "Options": self.ELDRITCH_INVOCATIONS,
                "Choices": 2,
                "Function": self._apply_invocations,
            },
        ])
        return character

    def level_up(self, character: Character):
        super().level_up(character)
        self._apply_level(character, self.level)
        return character
