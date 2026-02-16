from src.common import dnd_skills
from src.creatures import Character


class Item():
    def __init__(self, name="Item", description=""):
        self.name = name
        self.description = description
        self.type = None
        self.value = 0
        self.magical = False
        self.rarity = "Common"
        self.weight = 0
        # Can be Common, Uncommon, Rare, Legendary

    def purchase(self, character: Character):
        if "Discount" in character.special_traits and not self.magical:
            value = round(self.value * 0.8)
        else:
            value = self.value
        if character.gold >= value:
            character.gold -= value
            character.add_item(self, purchasing=False)
        else:
            print(f"{character.name} does not have the gold to purchase {self.name}.")

    def sell(self, character: Character):
        if self.type in ["Armor", "Weapon", "Shield"]:
            value = self.value // 2
        else:
            value = self.value
        if self in character.inventory:
            character.gold += value
        else:
            print(f"{character.name} does not have {self.name} in their inventory.")


################################################################################
############################         WEAPONS        ############################
################################################################################


class Weapon(Item):
    def __init__(self, name="Weapon", description=""):
        super().__init__()
        self.type = "Weapon"
        self.name = name
        self.description = description
        # Improvised, Simple, Martial
        self.category = "Improvised"
        self.damage = "1d1"
        self.damage_type = "Bludgeoning"
        # Melee or Ranged
        self.melee_or_ranged = "Melee"
        # Properties include Ammunition, Finesse, Heavy, Light, Loading, Reach, Thrown, Two-Handed, Versatile
        self.properties = []
        # Mastery can be Cleave, Graze, Nick, Push, Sap, Slow, Topple, Vex
        self.mastery = None


class Club(Weapon):
    def __init__(self, name="Club", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Simple"
        self.damage = "1d4"
        self.damage_type = "Bludgeoning"
        self.properties += ["Light"]
        self.mastery = "Slow"
        self.weight = 2
        self.value = 0.1


class Dagger(Weapon):
    def __init__(self, name="Dagger", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Simple"
        self.damage = "1d4"
        self.damage_type = "Piercing"
        self.properties += ["Finesse", "Light", "Thrown"]
        self.normal_range = 20
        self.long_range = 60
        self.mastery = "Nick"
        self.weight = 1
        self.value = 2


class Greatclub(Weapon):
    def __init__(self, name="Greatclub", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Simple"
        # TODO: Finish filling


class Handaxe(Weapon):
    def __init__(self, name="Handaxe", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Simple"
        self.damage = "1d6"
        self.damage_type = "Slashing"
        self.properties += ["Light", "Thrown"]
        self.normal_range = 20
        self.long_range = 60
        self.mastery = "Vex"
        self.weight = 2
        self.value = 5


class Greataxe(Weapon):
    def __init__(self, name="Greataxe", description=""):
        super().__init__()
        self.category = "Martial"
        self.name = name
        self.description = description
        self.damage = "1d12"
        self.damage_type = "Slashing"
        self.properties += ["Heavy", "Two-Handed"]
        self.mastery = "Cleave"
        self.weight = 7
        self.value = 30


################################################################################
############################          ARMOR         ############################
################################################################################


class Armor(Item):
    def __init__(self, name="Armor", description=""):
        super().__init__()
        self.type = "Armor"
        self.name = name
        self.description = description
        # None, Light, Medium, Heavy
        self.category = None
        self.base_ac = 10
        self.add_dex = False
        self.dex_add_max = 10
        self.strength_required = 0
        self.stealth_disadvantage = False
        self.weight = 1
        self.value = 1

    def ac(self, character: Character):
        ac = self.base_ac
        if self.add_dex:
            ac += min([character.get_ability_bonus("Dexterity"), self.dex_add_max])
        return ac

    # TODO: These should add and remove an "active effect" instead, so that it doesn't affect other active effects
    # TODO: active effects should be looked at when measuring ability, skill, speed, etc checks.
    def on_equip(self, character: Character):
        if self.stealth_disadvantage:
            character.disadvantages["Skills"] += ["Stealth"]
        if character.ability_scores["Strength"] < self.strength_required:
            character.speed -= 10
        if self.category is not None and self.category not in character.proficiencies["Armor"]:
            character.disadvantages["Skills"] += [k for k, v in dnd_skills.items() if v in ["Strength", "Dexterity"]]
            character.active_effects += ["Cannot Cast Spells"]
        return character

    def on_unequip(self, character: Character):
        if self.stealth_disadvantage:
            character.disadvantages["Skills"] = [skill for skill in character.disadvantages["Skills"] if skill != "Stealth"]
        if character.ability_scores["Strength"] < self.strength_required:
            character.speed += 10
        if self.category is not None and self.category not in character.proficiencies["Armor"]:
            character.disadvantages["Skills"] = list(set(character.disadvantages["Skills"]) - set([k for k, v in dnd_skills.items() if v in ["Strength", "Dexterity"]]))
            character.active_effects = [_ for _ in character.active_effects if _ != "Cannot Cast Spells"]
        return character


class Clothing(Armor):
    def __init__(self, name="Clothing", description=""):
        super().__init__()
        self.name = name
        self.description = description


class PaddedArmor(Armor):
    def __init__(self, name="Padded Armor", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Light"
        self.stealth_disadvantage = True
        self.base_ac = 11
        self.add_dex = True
        self.weight = 8
        self.value = 5


class LeatherArmor(Armor):
    def __init__(self, name="Leather Armor", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Light"
        self.base_ac = 11
        self.add_dex = True
        self.weight = 10
        self.value = 10


class StuddedLeatherArmor(Armor):
    def __init__(self, name="Studded Leather Armor", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Light"
        self.base_ac = 11
        self.add_dex = True
        self.weight = 13
        self.value = 45


class HideArmor(Armor):
    def __init__(self, name="Hide Armor", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Medium"
        self.base_ac = 12
        self.add_dex = True
        self.dex_add_max = 2
        self.weight = 12
        self.value = 10


class ChainShirt(Armor):
    def __init__(self, name="Chain Shirt", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Medium"
        self.base_ac = 13
        self.add_dex = True
        self.dex_add_max = 2
        self.weight = 20
        self.value = 50


class ScaleMail(Armor):
    def __init__(self, name="Scale Mail", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Medium"
        self.base_ac = 14
        self.add_dex = True
        self.dex_add_max = 2
        self.stealth_disadvantage = True
        self.weight = 45
        self.value = 50


class Breastplate(Armor):
    def __init__(self, name="Breastplate", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Medium"
        self.base_ac = 14
        self.add_dex = True
        self.dex_add_max = 2
        self.weight = 20
        self.value = 400


class HalfPlateArmor(Armor):
    def __init__(self, name="Half Plate Armor", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Medium"
        self.base_ac = 12
        self.add_dex = True
        self.dex_add_max = 2
        self.stealth_disadvantage = True
        self.weight = 40
        self.value = 750


class RingMail(Armor):
    def __init__(self, name="Ring Mail", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Heavy"
        self.base_ac = 14
        self.stealth_disadvantage = True
        self.weight = 40
        self.value = 30


class ChainMail(Armor):
    def __init__(self, name="Chain Mail", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Heavy"
        self.base_ac = 16
        self.stealth_disadvantage = True
        self.strength_required = 13
        self.weight = 55
        self.value = 75


class SplintArmor(Armor):
    def __init__(self, name="Splint Armor", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Heavy"
        self.base_ac = 17
        self.stealth_disadvantage = True
        self.strength_required = 15
        self.weight = 60
        self.value = 200


class PlateArmor(Armor):
    def __init__(self, name="Plate Armor", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Heavy"
        self.base_ac = 18
        self.stealth_disadvantage = True
        self.strength_required = 15
        self.weight = 65
        self.value = 1500


class Shield(Armor):
    def __init__(self, name="Shield", description=""):
        super().__init__()
        self.name = name
        self.description = description
        # Shields are just different enough that I felt it warrants a new type
        self.type = "Shield"
        self.base_ac = 2
        self.weight = 6
        self.value = 10

    def ac(self, character: Character):
        if "Shield" not in character.proficiencies["Armor"]:
            return 0
        else:
            return self.base_ac
