from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.common import dnd_skills, artisans_tools


class Class:
    def __init__(self, name, level, subclass=None):
        self.name = name
        self.level = level
        self.hit_dice = 8
        self.subclass = subclass
        self.spellcasting_ability = "None"
        self.proficiencies = {
            "Armor": [],
            "Weapons": [],
            "Tools": [],
            "Saving Throws": [],
            "Skills": []
        }

    def apply_to_character(self, character):
        character.proficiencies["Armor"] += self.proficiencies["Armor"]
        character.proficiencies["Weapons"] += self.proficiencies["Weapons"]
        character.proficiencies["Tools"] += self.proficiencies["Tools"]
        character.proficiencies["Saving Throws"] += self.proficiencies["Saving Throws"]
        character.proficiencies["Skills"] += self.proficiencies["Skills"]
        return character

    def level_up(self, character):
        # These are handled in the specific class level up functions, but this is where you would put any general level up logic that applies to all classes, such as increasing hit points or granting ability score improvements.
        return character



# ── Shared spell-slot tables ───────────────────────────────────────────────

_FULL_CASTER_SLOTS = [
    {1: 2},                                                          # Level 1
    {1: 3},                                                          # Level 2
    {1: 4, 2: 2},                                                    # Level 3
    {1: 4, 2: 3},                                                    # Level 4
    {1: 4, 2: 3, 3: 2},                                             # Level 5
    {1: 4, 2: 3, 3: 3},                                             # Level 6
    {1: 4, 2: 3, 3: 3, 4: 1},                                       # Level 7
    {1: 4, 2: 3, 3: 3, 4: 2},                                       # Level 8
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},                                # Level 9
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},                                # Level 10
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},                         # Level 11
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},                         # Level 12
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},                   # Level 13
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},                   # Level 14
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},             # Level 15
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},             # Level 16
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1},      # Level 17
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1},      # Level 18
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1},      # Level 19
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1},      # Level 20
]

_HALF_CASTER_SLOTS = [
    {1: 2},                          # Level 1
    {1: 2},                          # Level 2
    {1: 3},                          # Level 3
    {1: 3},                          # Level 4
    {1: 4, 2: 2},                    # Level 5
    {1: 4, 2: 2},                    # Level 6
    {1: 4, 2: 3},                    # Level 7
    {1: 4, 2: 3},                    # Level 8
    {1: 4, 2: 3, 3: 2},             # Level 9
    {1: 4, 2: 3, 3: 2},             # Level 10
    {1: 4, 2: 3, 3: 3},             # Level 11
    {1: 4, 2: 3, 3: 3},             # Level 12
    {1: 4, 2: 3, 3: 3, 4: 1},       # Level 13
    {1: 4, 2: 3, 3: 3, 4: 1},       # Level 14
    {1: 4, 2: 3, 3: 3, 4: 2},       # Level 15
    {1: 4, 2: 3, 3: 3, 4: 2},       # Level 16
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 1}, # Level 17
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 1}, # Level 18
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2}, # Level 19
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2}, # Level 20
]

_WARLOCK_PACT_SLOTS = [
    {1: 1}, {1: 2}, {2: 2}, {2: 2},  # Levels 1-4
    {3: 2}, {3: 2}, {4: 2}, {4: 2},  # Levels 5-8
    {5: 2}, {5: 2},                   # Levels 9-10
    {5: 3}, {5: 3}, {5: 3}, {5: 3},  # Levels 11-14
    {5: 3}, {5: 3},                   # Levels 15-16
    {5: 4}, {5: 4}, {5: 4}, {5: 4},  # Levels 17-20
]

_FIGHTING_STYLES = [
    "Archery", "Blind Fighting", "Defense", "Dueling",
    "Great Weapon Fighting", "Interception", "Protection",
    "Thrown Weapon Fighting", "Two-Weapon Fighting", "Unarmed Fighting",
]


# ── Cleric ─────────────────────────────────────────────────────────────────

