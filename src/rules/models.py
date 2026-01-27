import json
from random import choice


with open('src/rules/json/01 races.json') as f:
    race_data = json.load(f)
# with open('src/rules/json/02 classes.json') as f:
#     klass_data = json.load(f)
with open('src/rules/json/04 equipment.json') as f:
    equipment_data = json.load(f)


def roll_dice(dice_sides, num_dice=1):
    rolls = sum(choice(range(1, dice_sides + 1)) for _ in range(num_dice))
    return rolls


def roll_dice_discard_lowest(dice_sides, num_dice=4):
    rolls = [roll_dice(dice_sides) for _ in range(num_dice)]
    print(f"Rolls: {rolls}")
    print(f"Discarding lowest roll: {min(rolls)}")
    rolls.remove(min(rolls))
    return sum(rolls)


class Character:
    def __init__(self, name, race, klass, level=1, equipment=[], spells=[], description="", ability_score_bonuses = {}):
        self.todo = []
        self.name = name
        self.race = race
        self.klass = klass
        self.level = level
        if level == 1 and equipment == []:
            self.equipment = ["Short Sword", "Leather Armor"]
        self.equipment = equipment
        self.spells = spells
        self.proficiency_bonus = 2 + (level - 1) // 4
        self.ability_scores = {
            "Strength": 0,
            "Dexterity": 0,
            "Constitution": 0,
            "Intelligence": 0,
            "Wisdom": 0,
            "Charisma": 0
        }
        self.proficiencies = {
            "Armor": [],
            "Weapons": [],
            "Tools": [],
            "Saving Throws": [],
            "Skills": []
        }
        self.advantages = {
            "Saving Throws": [],
            "Skills": []
        }
        if len(ability_score_bonuses) > 0:
            for ability, bonus in ability_score_bonuses.items():
                self.ability_scores[ability] += bonus
        else:
            print("Rolling ability scores...")
            for ability in self.ability_scores.keys():
                score = roll_dice_discard_lowest(6, 4)
                self.ability_scores[ability] = score
                print(f"{ability}: {score}")
        # RACE FEATURES
        this_race_data = race_data.get(race)
        self.size = this_race_data.get("Size", "medium")
        self.speed = this_race_data.get("Speed", 30)
        self.languages = this_race_data.get("Languages", [])
        self.resistances = this_race_data.get("Resistances", [])
        self.full_rest_hours = this_race_data.get("Full Rest Hours", 8)
        for element in self.proficiencies.keys():
            self.proficiencies[element] += this_race_data.get("Proficiencies", {}).get(element, [])
        for element in self.advantages.keys():
            self.advantages[element] += this_race_data.get("Advantages", {}).get(element, [])
        for element in self.ability_scores.keys():
            self.ability_scores[element] += this_race_data.get("Ability Scores", {}).get(element, 0)
        # TODO: Handle traits, resistances, proficiencies, special abilities
        # CLASS FEATURES
        # this_klass_data = klass_data.get(klass)
        # TODO: Add class features, spells, and equipment based on class and level
        # TODO: Add class description to character description
        self.description = description + " " + this_race_data.get("Description", "")

    def level_up(self):
        self.level += 1
        # TODO: Add class features, spells, and equipment based on new level

    def add_equipment(self, item):
        self.equipment.append(item)

    def get_ability_bonus(self, ability):
        return (self.ability_scores[ability] - 10) // 2

    def get_skill_bonus(self, skill):
        dnd_skills = {
            "Acrobatics": "Dexterity",
            "Animal Handling": "Wisdom",
            "Arcana": "Intelligence",
            "Athletics": "Strength",
            "Deception": "Charisma",
            "History": "Intelligence",
            "Insight": "Wisdom",
            "Intimidation": "Charisma",
            "Investigation": "Intelligence",
            "Medicine": "Wisdom",
            "Nature": "Intelligence",
            "Perception": "Wisdom",
            "Performance": "Charisma",
            "Persuasion": "Charisma",
            "Religion": "Intelligence",
            "Sleight of Hand": "Dexterity",
            "Stealth": "Dexterity",
            "Survival": "Wisdom"
        }
        return self.get_ability_bonus(dnd_skills[skill]) + (self.proficiency_bonus if skill in self.proficiencies["Skills"] else 0)

    def __str__(self):
        return f"{self.name}, a level {self.level} {self.race} {self.klass} with equipment: {', '.join(self.equipment)}"


# Example usage
if __name__ == "__main__":
    char = Character(name="Aragorn", race="Human", klass="Ranger", description="He is the king of Gondor.")
    print(char)
