import json
from src.common import roll_dice_discard_lowest, roll_dice, handle_roll_criticals
from src.species import Goblin, Aasimar, Dragonborn, Dwarf, Elf

species_match = {
    "Goblin": Goblin,
    "Aasimar": Aasimar,
    "Dragonborn": Dragonborn,
    "Dwarf": Dwarf,
    "Elf": Elf,
}


with open('src/rules/json/01 races.json') as f:
    race_data = json.load(f)
# with open('src/rules/json/02 classes.json') as f:
#     class_data = json.load(f)
with open('src/rules/json/04 equipment.json') as f:
    equipment_data = json.load(f)


class Character:
    def __init__(self, name, species, classes, equipment=[], spells=[], description="", ability_score_bonuses={}, **kwargs):
        self.todo = []
        self.name = name
        self.description = description
        self.active_effects = []
        # SET ALL SPECIES ATTRIBUTES
        self.species = species_match.get(species)(**kwargs)
        self.todo += self.species.todo
        self.description += " " if self.description else "" + self.species.description
        self.size = self.species.size
        self.speed = self.species.speed
        self.swimming_speed = self.species.swimming_speed
        self.flying_speed = self.species.flying_speed
        self.spells = self.species.spells
        self.resistances = self.species.resistances
        self.vision = self.species.vision
        self.full_rest_hours = self.species.full_rest_hours
        self.special_abilities = self.species.special_abilities
        # SET ALL BACKGROUND ATTRIBUTES
        # SET ALL CLASS ATTRIBUTES
        self.classes = classes
        self.level = sum(cls["level"] for cls in classes)
        self.species.level = self.level
        if self.level == 1 and equipment == []:
            self.equipment = ["Short Sword", "Leather Armor"]
        else:
            self.equipment = []
        self.equipment += equipment
        self.spells += spells
        self.proficiency_bonus = 2 + (self.level - 1) // 4
        self.species.proficiency_bonus = self.proficiency_bonus
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
        self.max_hp = 10 + self.get_ability_bonus("Constitution")
        if self.species.species == "Dwarf":
            self.max_hp += 1
        self.current_hp = self.max_hp
        if len(ability_score_bonuses) > 0:
            for ability, bonus in ability_score_bonuses.items():
                self.ability_scores[ability] += bonus
        else:
            print("Rolling ability scores...")
            for ability in self.ability_scores.keys():
                score = roll_dice_discard_lowest(6, 4)
                self.ability_scores[ability] = score
                print(f"{ability}: {score}")
        # TODO: Handle traits, resistances, proficiencies, special abilities
        self.description = self.description + " " + description
        self.species.ability_scores = self.ability_scores
        self.species.advantages = self.advantages

    def __str__(self):
        return f"{self.name}, a level {self.level} {self.species} {self.class_} with equipment: {', '.join(self.equipment)}"

    def level_up(self, class_):
        if class_ not in [cls["name"] for cls in self.classes]:
            self.classes.append({"name": class_, "level": 1})
        else:
            for cls in self.classes:
                if cls["name"] == class_:
                    cls["level"] += 1
        if self.species.species == "Dwarf":
            self.max_hp += 1
        # ADD HP BASED ON CLASS HIT DIE
        self.level += 1
        self.proficiency_bonus = 2 + (self.level - 1) // 4
        self.species.proficiency_bonus = self.proficiency_bonus
        self.species.level = self.level
        # TODO: Add class features, spells, and equipment based on new level and which class is being leveled up

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

    def attack(self, target, weapon):
        # TODO: Implement attack logic
        pass

    def cast_spell(self, spell, targets=[]):
        for s in self.spells:
            if s.name == spell:
                if s.uses_left is None or s.uses_left > 0:
                    if s.uses_left is not None:
                        s.uses_left -= 1
                    s.cast(self, targets or [self])
                else:
                    print(f"No uses left for {s.name}.")
                return
        print(f"{self.name} does not know the spell {spell}.")

    def use_special_ability(self, ability, targets=[]):
        for a in self.special_abilities:
            if a.name == ability:
                if a.uses_left is None or a.uses_left > 0:
                    if a.uses_left is not None:
                        a.uses_left -= 1
                    a.cast(self, targets or [self])
                else:
                    print(f"No uses left for {a.name}.")
                return
        print(f"{self.name} does not know the special ability {ability}.")

    def use_ability(self, ability):
        # TODO: Implement ability usage logic
        pass

    def roll_save(self, ability, beat):
        roll = roll_dice(1, 20)
        bonus = self.get_ability_bonus(ability)
        if ability in self.advantages["Saving Throws"]:
            roll2 = roll_dice(1, 20)
            roll = max(roll, roll2)
        if ability in self.proficiencies["Saving Throws"]:
            bonus += self.proficiency_bonus
        total = roll + bonus
        print(f"{self.name} rolls a {ability} saving throw: {roll} + {bonus} = {total}")
        success, total = handle_roll_criticals(roll, total, beat)
        return success, total

    def rest(self, long=False):
        self.species.rest(long=long)
        if long:
            self.current_hp = self.max_hp
        else:
            # TODO: Implement short rest logic with hit die
            pass


# Example usage
if __name__ == "__main__":
    char = Character(
        name="Ysraela",
        species="Aasimar",
        classes=[{"name": "Ranger", "level": 1}],
        description="Ysraela is an angelic ranger, known for her sharp senses and unwavering determination in the face of danger.",
        ability_score_bonuses={
            "Strength": 12,
            "Dexterity": 16,
            "Constitution": 12,
            "Intelligence": 12,
            "Wisdom": 14,
            "Charisma": 16
        }
    )
    char2 = Character(
        name="Thokk",
        species="Aasimar",
        classes=[{"name": "Fighter", "level": 1}],
        description="Thokk is a celestial warrior, wielding his sword with divine purpose and protecting the innocent from evil.",
        ability_score_bonuses={
            "Strength": 16,
            "Dexterity": 12,
            "Constitution": 14,
            "Intelligence": 10,
            "Wisdom": 12,
            "Charisma": 14
        }
    )
    print(char)
