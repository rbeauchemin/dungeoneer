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
        # Unarmed, Improvised, Simple, Martial
        self.category = "Improvised"
        self.damage = "1d1"
        self.damage_type = "Bludgeoning"
        # Melee or Ranged
        self.melee_or_ranged = "Melee"
        # Properties include Ammunition, Finesse, Heavy, Light, Loading, Reach, Thrown, Two-Handed, Versatile
        self.properties = []
        # Mastery can be Cleave, Graze, Nick, Push, Sap, Slow, Topple, Vex
        self.mastery = None
        self.versatile_damage = ""
        self.ammunition_type = ""

    def on_equip(self, character: Character):
        return self

    def on_unequip(self, character: Character):
        return self


class Unarmed(Weapon):
    def __init__(self, name="Unarmed Strike", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Unarmed"
        self.damage = "1d1"

    def on_equip(self, character: Character):
        super().on_equip(character)
        if "Tavern Brawler" in [_.name for _ in character.feats]:
            self.damage = "1d4"
        return self

    def on_unequip(self, character: Character):
        super().on_unequip(character)
        self.damage = "1d1"
        return self


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
        self.damage = "1d8"
        self.damage_type = "Bludgeoning"
        self.properties += ["Two-Handed"]
        self.mastery = "Push"
        self.weight = 10
        self.value = 0.2


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


class Javelin(Weapon):
    def __init__(self, name="Javelin", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Simple"
        self.damage = "1d6"
        self.damage_type = "Piercing"
        self.properties += ["Melee", "Thrown"]
        self.normal_range = 30
        self.long_range = 120
        self.mastery = "Slow"
        self.weight = 2
        self.value = 0.5


class LightHammer(Weapon):
    def __init__(self, name="Light Hammer", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Simple"
        self.damage = "1d4"
        self.damage_type = "Bludgeoning"
        self.properties += ["Light", "Thrown"]
        self.normal_range = 20
        self.long_range = 60
        self.mastery = "Nick"
        self.weight = 2
        self.value = 2


class Mace(Weapon):
    def __init__(self, name="Mace", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Simple"
        self.damage = "1d6"
        self.damage_type = "Bludgeoning"
        self.mastery = "Sap"
        self.weight = 4
        self.value = 5


class Quarterstaff(Weapon):
    def __init__(self, name="Quarterstaff", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Simple"
        self.damage = "1d6"
        self.damage_type = "Bludgeoning"
        self.properties += ["Versatile"]
        self.mastery = "Topple"
        self.weight = 4
        self.value = 0.2
        self.versatile_damage = "1d8"


class Sickle(Weapon):
    def __init__(self, name="Sickle", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Simple"
        self.damage = "1d4"
        self.damage_type = "Slashing"
        self.properties += ["Light"]
        self.mastery = "Nick"
        self.weight = 2
        self.value = 1


class Spear(Weapon):
    def __init__(self, name="Spear", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Simple"
        self.damage = "1d6"
        self.damage_type = "Piercing"
        self.properties += ["Thrown", "Versatile"]
        self.normal_range = 20
        self.long_range = 60
        self.mastery = "Sap"
        self.weight = 3
        self.value = 1
        self.versatile_damage = "1d8"


# Simple Ranged Weapons

class Dart(Weapon):
    def __init__(self, name="Dart", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Simple"
        self.melee_or_ranged = "Ranged"
        self.damage = "1d4"
        self.damage_type = "Piercing"
        self.properties += ["Finesse", "Thrown"]
        self.normal_range = 20
        self.long_range = 60
        self.mastery = "Vex"
        self.weight = 0.25
        self.value = 0.05


class LightCrossbow(Weapon):
    def __init__(self, name="Light Crossbow", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Simple"
        self.melee_or_ranged = "Ranged"
        self.damage = "1d8"
        self.damage_type = "Piercing"
        self.properties += ["Ammunition", "Loading", "Two-Handed"]
        self.normal_range = 80
        self.long_range = 320
        self.mastery = "Slow"
        self.weight = 5
        self.value = 25
        self.ammunition_type = "Bolt"


class Shortbow(Weapon):
    def __init__(self, name="Shortbow", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Simple"
        self.melee_or_ranged = "Ranged"
        self.damage = "1d6"
        self.damage_type = "Piercing"
        self.properties += ["Ammunition", "Two-Handed"]
        self.normal_range = 80
        self.long_range = 320
        self.mastery = "Vex"
        self.weight = 2
        self.value = 25
        self.ammunition_type = "Arrow"


class Sling(Weapon):
    def __init__(self, name="Sling", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Simple"
        self.melee_or_ranged = "Ranged"
        self.damage = "1d4"
        self.damage_type = "Bludgeoning"
        self.properties += ["Ammunition"]
        self.normal_range = 30
        self.long_range = 120
        self.mastery = "Slow"
        self.weight = 0
        self.value = 0.1
        self.ammunition_type = "Bullet"


# Martial Melee Weapons

class Battleaxe(Weapon):
    def __init__(self, name="Battleaxe", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.damage = "1d8"
        self.damage_type = "Slashing"
        self.properties += ["Versatile"]
        self.mastery = "Topple"
        self.weight = 4
        self.value = 10
        self.versatile_damage = "1d10"


class Flail(Weapon):
    def __init__(self, name="Flail", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.damage = "1d8"
        self.damage_type = "Bludgeoning"
        self.mastery = "Sap"
        self.weight = 2
        self.value = 10


class Glaive(Weapon):
    def __init__(self, name="Glaive", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.damage = "1d10"
        self.damage_type = "Slashing"
        self.properties += ["Heavy", "Reach", "Two-Handed"]
        self.mastery = "Graze"
        self.weight = 6
        self.value = 20


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


class Greatsword(Weapon):
    def __init__(self, name="Greatsword", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.damage = "2d6"
        self.damage_type = "Slashing"
        self.properties += ["Heavy", "Two-Handed"]
        self.mastery = "Graze"
        self.weight = 6
        self.value = 50


class Halberd(Weapon):
    def __init__(self, name="Halberd", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.damage = "1d10"
        self.damage_type = "Slashing"
        self.properties += ["Heavy", "Reach", "Two-Handed"]
        self.mastery = "Cleave"
        self.weight = 6
        self.value = 20


class Lance(Weapon):
    def __init__(self, name="Lance", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.damage = "1d10"
        self.damage_type = "Piercing"
        self.properties += ["Heavy", "Reach", "Two-Handed"]
        self.mastery = "Topple"
        self.weight = 6
        self.value = 10

    def on_equip(self, character):
        super().on_equip(character)
        # special property allowing it to be one-handed when mounted.
        if "Mounted" in [_.name for _ in character.active_effects]:
            self.properties.remove("Two-Handed")

    def on_unequip(self, character):
        super().on_unequip(character)
        if "Two-Handed" not in self.properties:
            self.properties += ["Two-Handed"]


class Longsword(Weapon):
    def __init__(self, name="Longsword", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.damage = "1d8"
        self.damage_type = "Slashing"
        self.properties += ["Versatile"]
        self.mastery = "Sap"
        self.weight = 3
        self.value = 15
        self.versatile_damage = "1d10"


class Maul(Weapon):
    def __init__(self, name="Maul", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.damage = "2d6"
        self.damage_type = "Bludgeoning"
        self.properties += ["Heavy", "Two-Handed"]
        self.mastery = "Topple"
        self.weight = 10
        self.value = 10


class Morningstar(Weapon):
    def __init__(self, name="Morningstar", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.damage = "1d8"
        self.damage_type = "Piercing"
        self.mastery = "Sap"
        self.weight = 4
        self.value = 15


class Pike(Weapon):
    def __init__(self, name="Pike", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.damage = "1d10"
        self.damage_type = "Piercing"
        self.properties += ["Heavy", "Reach", "Two-Handed"]
        self.mastery = "Push"
        self.weight = 18
        self.value = 5


class Rapier(Weapon):
    def __init__(self, name="Rapier", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.damage = "1d8"
        self.damage_type = "Piercing"
        self.properties += ["Finesse"]
        self.mastery = "Vex"
        self.weight = 2
        self.value = 25


class Scimitar(Weapon):
    def __init__(self, name="Scimitar", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.damage = "1d6"
        self.damage_type = "Slashing"
        self.properties += ["Finesse", "Light"]
        self.mastery = "Nick"
        self.weight = 3
        self.value = 25


class Shortsword(Weapon):
    def __init__(self, name="Shortsword", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.damage = "1d6"
        self.damage_type = "Piercing"
        self.properties += ["Finesse", "Light"]
        self.mastery = "Vex"
        self.weight = 2
        self.value = 10


class Trident(Weapon):
    def __init__(self, name="Trident", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.damage = "1d8"
        self.damage_type = "Piercing"
        self.properties += ["Thrown", "Versatile"]
        self.normal_range = 20
        self.long_range = 60
        self.mastery = "Topple"
        self.weight = 4
        self.value = 5
        self.versatile_damage = "1d10"


class Warhammer(Weapon):
    def __init__(self, name="Warhammer", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.damage = "1d8"
        self.damage_type = "Bludgeoning"
        self.properties += ["Versatile"]
        self.mastery = "Push"
        self.weight = 5
        self.value = 15
        self.versatile_damage = "1d10"


class WarPick(Weapon):
    def __init__(self, name="War Pick", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.damage = "1d8"
        self.damage_type = "Piercing"
        self.properties += ["Versatile"]
        self.mastery = "Sap"
        self.weight = 2
        self.value = 5
        self.versatile_damage = "1d10"


class Whip(Weapon):
    def __init__(self, name="Whip", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.damage = "1d4"
        self.damage_type = "Slashing"
        self.properties += ["Finesse", "Reach"]
        self.mastery = "Slow"
        self.weight = 3
        self.value = 2


# Martial Ranged Weapons

class Blowgun(Weapon):
    def __init__(self, name="Blowgun", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.melee_or_ranged = "Ranged"
        self.damage = "1"
        self.damage_type = "Piercing"
        self.properties += ["Ammunition", "Loading"]
        self.normal_range = 25
        self.long_range = 100
        self.mastery = "Vex"
        self.weight = 1
        self.value = 10
        self.ammunition_type = "Needle"


class HandCrossbow(Weapon):
    def __init__(self, name="Hand Crossbow", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.melee_or_ranged = "Ranged"
        self.damage = "1d6"
        self.damage_type = "Piercing"
        self.properties += ["Ammunition", "Light", "Loading"]
        self.normal_range = 30
        self.long_range = 120
        self.mastery = "Vex"
        self.weight = 3
        self.value = 75
        self.ammunition_type = "Bolt"


class HeavyCrossbow(Weapon):
    def __init__(self, name="Heavy Crossbow", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.melee_or_ranged = "Ranged"
        self.damage = "1d10"
        self.damage_type = "Piercing"
        self.properties += ["Ammunition", "Heavy", "Loading", "Two-Handed"]
        self.normal_range = 100
        self.long_range = 400
        self.mastery = "Push"
        self.weight = 18
        self.value = 50
        self.ammunition_type = "Bolt"


class Longbow(Weapon):
    def __init__(self, name="Longbow", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.melee_or_ranged = "Ranged"
        self.damage = "1d8"
        self.damage_type = "Piercing"
        self.properties += ["Ammunition", "Heavy", "Two-Handed"]
        self.normal_range = 150
        self.long_range = 600
        self.mastery = "Slow"
        self.weight = 2
        self.value = 50
        self.ammunition_type = "Arrow"


class Musket(Weapon):
    def __init__(self, name="Musket", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.melee_or_ranged = "Ranged"
        self.damage = "1d12"
        self.damage_type = "Piercing"
        self.properties += ["Ammunition", "Loading", "Two-Handed"]
        self.normal_range = 40
        self.long_range = 120
        self.mastery = "Slow"
        self.weight = 10
        self.value = 500
        self.ammunition_type = "Bullet"


class Pistol(Weapon):
    def __init__(self, name="Pistol", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.category = "Martial"
        self.melee_or_ranged = "Ranged"
        self.damage = "1d10"
        self.damage_type = "Piercing"
        self.properties += ["Ammunition", "Loading"]
        self.normal_range = 30
        self.long_range = 90
        self.mastery = "Vex"
        self.weight = 3
        self.value = 250
        self.ammunition_type = "Bullet"


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
        return self

    def on_unequip(self, character: Character):
        if self.stealth_disadvantage:
            character.disadvantages["Skills"] = [skill for skill in character.disadvantages["Skills"] if skill != "Stealth"]
        if character.ability_scores["Strength"] < self.strength_required:
            character.speed += 10
        if self.category is not None and self.category not in character.proficiencies["Armor"]:
            character.disadvantages["Skills"] = list(set(character.disadvantages["Skills"]) - set([k for k, v in dnd_skills.items() if v in ["Strength", "Dexterity"]]))
            character.active_effects = [_ for _ in character.active_effects if _ != "Cannot Cast Spells"]
        return self


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
