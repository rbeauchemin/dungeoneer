import importlib
from src.common import roll_dice_discard_lowest, roll_dice, handle_roll_criticals, dnd_skills


class Character:
    def __init__(self, name, species, classes=[], equipment=[], spells=[], description="", ability_score_bonuses={}, **kwargs):
        # Set base traits and abilities
        self.todo = []
        self.name = name
        self.description = description
        self.gold = 0
        self.active_effects = []
        self.inventory = []
        self.inventory += equipment
        self.equipped_items = []
        if "ability_scores" in kwargs:
            self.ability_scores = kwargs['ability_scores']
        else:
            self.ability_scores = {
                "Strength": 10,
                "Dexterity": 10,
                "Constitution": 10,
                "Intelligence": 10,
                "Wisdom": 10,
                "Charisma": 10
            }
        if "proficiencies" in kwargs:
            self.proficiencies = kwargs['proficiencies']
        else:
            self.proficiencies = {
                "Armor": [],
                "Weapons": ["Unarmed"],
                "Tools": [],
                "Saving Throws": [],
                "Skills": [],
                "Special": []
            }
        if "advantages" in kwargs:
            self.advantages = kwargs['advantages']
        else:
            self.advantages = {
                "Saving Throws": [],
                "Skills": [],
                "Abilities": [],
                "Attack": 0,
                "ToBeAttacked": 0
            }
        if "disadvantages" in kwargs:
            self.disadvantages = kwargs['disadvantages']
        else:
            self.disadvantages = {
                "Saving Throws": [],
                "Skills": [],
                "Abilities": [],
                "Attack": 0,
                "ToBeAttacked": 0
            }
        # SET ALL SPECIES ATTRIBUTES
        if isinstance(species, str):
            try:
                self.species = getattr(importlib.import_module("src.species"), species)(**kwargs)
            except AttributeError:
                raise Exception(f"Species {species} could not be found")
        else:
            self.species = species
        self.todo += self.species.todo
        self.description += " " if self.description else "" + self.species.description
        self.size = self.species.size
        self.speed = self.species.speed
        self.swimming_speed = self.species.swimming_speed
        self.flying_speed = self.species.flying_speed
        self.spells = self.species.spells
        self.spells += spells
        self.resistances = self.species.resistances
        self.vision = self.species.vision
        self.full_rest_hours = self.species.full_rest_hours
        self.special_abilities = self.species.special_abilities
        self.special_traits = self.species.special_traits
        # SET ALL BACKGROUND ATTRIBUTES
        # TODO: ADD background setup

        # SET ALL CLASS ATTRIBUTES
        self.classes = classes
        for cls in classes:
            cls.apply_to_character(self)
        self.level = sum(cls.level for cls in classes)
        self.species.level = self.level
        self.proficiency_bonus = 2 + (self.level - 1) // 4
        self.species.proficiency_bonus = self.proficiency_bonus

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
        if "feats" in kwargs:
            self.feats = kwargs['feats']
        else:
            self.feats = []
        # TODO: Handle traits, resistances, proficiencies, special abilities
        self.description = self.description + " " + description
        self.species.ability_scores = self.ability_scores
        self.species.advantages = self.advantages
        self.spellcasting_ability = self.classes[0].spellcasting_ability if self.classes else "None"
        self.weapon_mastery = []

    def __str__(self):
        return f"{self.name}, a level {self.level} {self.species} {self.class_} with equipment: {', '.join(self.inventory)}"

    def level_up(self, class_):
        from src.classes import Class
        if class_ not in [cls.name for cls in self.classes]:
            self.classes.append(Class(name=class_, level=1))
        else:
            for cls in self.classes:
                if cls.name == class_:
                    cls.level_up(self)
        if self.species.species == "Dwarf":
            self.max_hp += 1
        if self.feats and "Tough" in [feat.name for feat in self.feats]:
            self.max_hp += 2
        # ADD HP BASED ON CLASS HIT DIE
        self.level += 1
        self.proficiency_bonus = 2 + (self.level - 1) // 4
        self.species.proficiency_bonus = self.proficiency_bonus
        self.species.level = self.level
        # TODO: Add class features, spells, and equipment based on new level and which class is being leveled up

    def add_item(self, item, purchasing=False):
        if isinstance(item, str):
            try:
                item_object = getattr(importlib.import_module("src.items"), item)()
            except AttributeError:
                print("Could not find the requested item")
        else:
            item_object = item
        if purchasing:
            item_object.purchase(self)
        else:
            self.inventory.append(item_object)

    def remove_item(self, item, selling=False):
        if isinstance(item, str):
            try:
                item_object = getattr(importlib.import_module("src.items"), item)()
            except AttributeError:
                print("Could not find the requested item")
        else:
            item_object = item
        if selling:
            item_object.sell(self)
        else:
            self.inventory.remove(item_object)

    def equip_item(self, item_name: str):
        item_object = None
        for item in self.inventory:
            if item_name == item.name:
                item_object = item
                break
        if item_object is None:
            print(f"{self.name} does not have {item_name} in their inventory.")
            return
        hands_left = 2
        for equipped_item in self.equipped_items:
            if equipped_item.type == "Weapon":
                if "Two-Handed" in equipped_item.properties:
                    hands_left -= 2
                else:
                    hands_left -= 1
            if equipped_item.type == "Shield":
                hands_left -= 1
        if item_object.type == "Weapon":
            if "Two-Handed" in item_object.properties and hands_left < 2:
                print(f"Not enough hands to equip {item_object.name}. Unequip some items first.")
                return
            elif hands_left < 1:
                print(f"Not enough hands to equip {item_object.name}. Unequip some items first.")
                return
        elif item_object.type == "Shield":
            # can't have two shields
            for equipped_item in self.equipped_items:
                if equipped_item.type == "Shield":
                    self.unequip_item(equipped_item.name)
        elif item.type == "Armor":
            # can't have two armors
            for equipped_item in self.equipped_items:
                if equipped_item.type == "Armor":
                    self.unequip_item(equipped_item.name)
        self.equipped_items.append(item)
        self.inventory.remove(item)

    def unequip_item(self, item_name):
        item_object = None
        for item in self.equipped_items:
            if item_name == item.name:
                item_object = item
                break
        if item_object is None:
            print(f"{self.name} does not have {item_name} equipped.")
            return
        self.equipped_items.remove(item)
        self.inventory.append(item)
        print(f"{self.name} has unequipped {item_object.name}.")

    def get_ability_bonus(self, ability):
        return (self.ability_scores[ability] - 10) // 2

    def get_armor_class(self):
        # Base AC
        ac = 10 + self.get_ability_bonus("Dexterity")
        unarmored = True
        for item in self.equipped_items:
            if item.type == "Armor":
                ac = item.ac(self)
                unarmored = False
        # Unarmored defense for barbarians
        if self.classes and self.classes[0].name == "Barbarian" and unarmored:
            ac = 10 + self.get_ability_bonus("Dexterity") + self.get_ability_bonus("Constitution")
        # Unarmored defense for monks
        if self.classes and self.classes[0].name == "Monk" and unarmored:
            ac = 10 + self.get_ability_bonus("Dexterity") + self.get_ability_bonus("Wisdom")
        for item in self.equipped_items:
            if item.type == "Shield" and self.classes[0].name != "Monk" and self.proficiencies["Armor"] and "Shield" in self.proficiencies["Armor"]:
                ac += item.ac(self)
        return ac
    get_ac = get_armor_class
    ac = get_armor_class

    def get_skill_bonus(self, skill):
        return self.get_ability_bonus(dnd_skills[skill]) + (self.proficiency_bonus if skill in self.proficiencies["Skills"] else 0)

    def attack(self, target, weapon_name=None, action_type="Action"):
        from src.items import Unarmed
        weapons = [Unarmed().on_equip(self)]
        weapon = None
        for item in self.equipped_items:
            if item.type == "Weapon":
                weapons.append(item)
        # Take the only equipped weapon or unarmed as default
        if len(weapons) < 3 and weapon_name is None:
            weapon = weapons[-1]
        else:
            for item in weapons:
                if item.name == weapon_name:
                    weapon = item
        if weapon is None:
            raise Exception(f"Weapon not found: {weapon_name}. Options are {[w.name for w in weapons]}")
        ability_bonus = self.get_ability_bonus("Strength")
        if "Finesse" in weapon.properties:
            ability_bonus = max([self.get_ability_bonus("Dexterity"), ability_bonus])
        proficiency_bonus = self.proficiency_bonus if weapon.category in self.proficiencies["Weapons"] else 0
        # give extra bonus to attack advantage if target marked with advantage to be attacked
        advantage_counter = 0
        advantage_counter += target.advantages["ToBeAttacked"]
        advantage_counter -= target.disadvantages["ToBeAttacked"]
        print(f"{self.name} attacks {target.name} with {weapon.name}.")
        success, total, crit_fail, crit_success = self.roll_check(None, beat=target.ac(), bonus=ability_bonus + proficiency_bonus, check_type="Attack", advantage_counter=advantage_counter)
        dice_split = [int(_) for _ in weapon.damage.split("d")]
        # HOUSE RULE: Critical success - double dice. Could also double the total below.
        if crit_success:
            dice_split[0] = dice_split[0] * 2
        # HOUSE RULE: Critical failure
        # TODO: Add some fun table of slip-ups for crit fails
        if crit_fail:
            pass
        if success:
            total = roll_dice(dice_split[0], dice_split[1]) + ability_bonus
            print(f"The total damage done is {total}")
            if weapon.damage_type in target.resistances:
                print("The attack doesn't seem very effective")
                total = total // 2
            target.current_hp -= total
        else:
            print("The attack missed!")

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

    def roll_check(self, ability, beat=None, bonus=0, check_type=None, advantage_counter=0, critical_threshold: int = 20, failure_threshold: int = 1, tie_succeeds: bool = True):
        # check type can be ["Abilities", "Saving Throws", "Skills", "Attack", "Initiative"]
        roll = roll_dice(1, 20)
        if check_type in ["Abilities", "Saving Throws"]:
            bonus = self.get_ability_bonus(ability)
        if check_type in ["Skills"]:
            bonus = self.get_skill_bonus(ability)
        if isinstance(self.advantages[check_type], list):
            for adv in self.advantages[check_type]:
                if adv == ability:
                    advantage_counter += 1
            for dadv in self.disadvantages[check_type]:
                if dadv == ability:
                    advantage_counter -= 1
        elif isinstance(self.advantages[check_type], int):
            advantage_counter += self.advantages[check_type]
            advantage_counter -= self.disadvantages[check_type]
        if advantage_counter > 0:
            roll2 = roll_dice(1, 20)
            roll = max(roll, roll2)
        elif advantage_counter < 0:
            roll2 = roll_dice(1, 20)
            roll = min(roll, roll2)
        if check_type in self.proficiencies and ability in self.proficiencies[check_type]:
            bonus += self.proficiency_bonus
        total = roll + bonus
        print(f"{self.name} rolls {roll} + {bonus} = {total}")
        success, total, crit_fail, crit_success = handle_roll_criticals(roll, total, beat, critical_threshold=critical_threshold, failure_threshold=failure_threshold, halfling_luck="Halfling Luck" in self.special_traits, tie_succeeds=tie_succeeds)
        return success, total, crit_fail, crit_success

    def rest(self, long=False):
        self.species.rest(long=long)
        if long:
            self.current_hp = self.max_hp
        else:
            # TODO: Implement short rest logic with hit die
            pass


# Example usage
if __name__ == "__main__":
    from src.classes import Barbarian
    char = Character(
        name="Ylera",
        species="Aasimar",
        classes=[Barbarian(level=1)],
        description="Ylera is an angelic barbarian, known for her sharp senses and unwavering determination in the face of danger.",
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
        classes=[Barbarian(level=1)],
        description="Thokk is a celestial barbarian, wielding his sword with divine purpose and protecting the innocent from evil.",
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
