from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.common import dnd_skills
from src.classes._base import Class


RAGES_PER_LEVEL = [2, 2, 3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 6, 6, 6, 6]


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

    def _calculate_rage_condition(self):
        from src.conditions import Condition
        rage_condition = Condition(
            name="Rage",
            description="While raging, you gain the following benefits if you aren't wearing heavy armor: You have advantage on Strength checks and Strength saving throws. When you make a melee weapon attack using Strength, you gain a bonus to the damage roll that increases as you gain levels as a barbarian, as shown in the Rage Damage column of the Barbarian table. You have resistance to bludgeoning, piercing, and slashing damage.",
            duration=10  # 1 minute = 10 rounds; also ends early via rage-end check in combat
        )
        rage_condition.bonus_resistances = ["Bludgeoning", "Piercing", "Slashing"]
        rage_condition.bonus_damage = 2 if self.level < 9 else 3 if self.level < 16 else 4
        rage_condition.prevents_casting = True
        rage_condition.adv_abilities = ["Strength"]
        rage_condition.adv_saving_throws = ["Strength"]
        rage_condition.adv_skills = [_ for _ in dnd_skills if dnd_skills[_] == "Strength"]
        return rage_condition

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        # Handle level one additions here, and level up additions in the level up function
        self.completed_levelup_to = 1
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        character.special_abilities += [
            Spell(
                name="Rage",
                casting_time="Bonus Action",
                range_="Self",
                components=[],
                duration="Instantaneous",
                description="In battle, you fight with primal ferocity. On your turn, you can enter a rage as a bonus action. While raging, you gain the following benefits if you aren't wearing heavy armor: You have advantage on Strength checks and Strength saving throws. When you make a melee weapon attack using Strength, you gain a bonus to the damage roll that increases as you gain levels as a barbarian, as shown in the Rage Damage column of the Barbarian table. You have resistance to bludgeoning, piercing, and slashing damage.",
                uses_left=RAGES_PER_LEVEL[self.level - 1],
                cooldown="Long Rest",
                cast=lambda caster, targets: caster.active_effects.append(self._calculate_rage_condition())
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
        super().level_up(character)
        # Level up uses of rage
        character.special_abilities = [
            _ for _ in character.special_abilities if _.name != "Rage"
        ] + [
            Spell(
                name="Rage",
                casting_time="Bonus Action",
                range_="Self",
                components=[],
                duration="Instantaneous",
                description="In battle, you fight with primal ferocity. On your turn, you can enter a rage as a bonus action. While raging, you gain the following benefits if you aren't wearing heavy armor: You have advantage on Strength checks and Strength saving throws. When you make a melee weapon attack using Strength, you gain a bonus to the damage roll that increases as you gain levels as a barbarian, as shown in the Rage Damage column of the Barbarian table. You have resistance to bludgeoning, piercing, and slashing damage.",
                uses_left=RAGES_PER_LEVEL[self.level - 1],
                cooldown="Long Rest",
                cast=lambda caster, targets: caster.active_effects.append(self._calculate_rage_condition())
            )
        ]
        return character
