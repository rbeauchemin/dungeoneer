from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.common import dnd_skills, artisans_tools
from src.classes._base import (
    Class, _FULL_CASTER_SLOTS, _HALF_CASTER_SLOTS,
    _WARLOCK_PACT_SLOTS, _FIGHTING_STYLES,
)


class Barbarian(Class):
    def __init__(self, level):
        super().__init__(name="Barbarian", level=1)
        self.todo = []
        self.level = level
        self.hit_dice = 12
        self.primary_ability = "Strength"
        self.proficiencies["Armor"] = ["Light", "Medium", "Shield"]
        self.proficiencies["Weapons"] = ["Simple", "Martial"]
        self.proficiencies["Saving Throws"] = ["Strength", "Constitution"]
        self.proficiencies["Skills"] = ["Animal Handling", "Athletics", "Intimidation", "Nature", "Perception", "Survival"]
        self.completed_levelup_to = 1

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 75
        else:
            character.add_item([Handaxe(quantity=4), Greataxe(), ExplorersPack()])
            character.gold += 15
        return character

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        # Handle level one additions here, and level up additions in the level up function
        self.completed_levelup_to = 1
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        rages_per_level = [2, 2, 3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 6, 6, 6, 6]
        character.special_abilities += [
            Spell(
                name="Rage",
                casting_time="Bonus Action",
                range_="Self",
                components=[],
                duration="1 Turn",
                description="In battle, you fight with primal ferocity. On your turn, you can enter a rage as a bonus action. While raging, you gain the following benefits if you aren't wearing heavy armor: You have advantage on Strength checks and Strength saving throws. When you make a melee weapon attack using Strength, you gain a bonus to the damage roll that increases as you gain levels as a barbarian, as shown in the Rage Damage column of the Barbarian table. You have resistance to bludgeoning, piercing, and slashing damage.",
                uses_left=rages_per_level[self.level - 1],
                cooldown="Long Rest",
                cast=lambda caster, targets: caster.active_effects.append("Rage")
            )
        ]
        character.todo.extend([
            {
                "Text": "Choose two weapons to gain mastery in.",
                "Options": ["Greataxe", "Greatsword", "Handaxe", "Javelin", "Light Hammer", "Longsword", "Maul", "Morningstar", "Pike", "Rapier", "Scimitar", "Shortsword", "Trident", "War Pick", "Warhammer"],
                "Choices": 2,
                "Function": lambda character, choices: character.weapon_mastery.extend(choices)
            },
            {
                "Text": "Select starting equipment or gold: (Greataxe, Two Handaxes, Explorer's Pack) or (4 Javelins and 2 Handaxes and 10 gold)",
                "Options": ["Starting Equipment", "Gold"],
                "Function": self.select_starting_equipment
            }
        ])
        return character

    def level_up(self, character: Character):
        self.level += 1
        # TODO: Handle levelup logic such as increasing hit points, granting new abilities, and updating the number of rages per day.
        character.classes = [cls for cls in character.classes if cls.name != self.name] + [self]
        return character

