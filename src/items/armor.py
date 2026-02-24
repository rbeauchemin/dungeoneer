from src.common import dnd_skills
from src.creatures import Character
from src.items.items import Item


class Armor(Item):
    def __init__(self, name="Armor", description="", **kwargs):
        super().__init__(name, description, **kwargs)
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

    def on_equip(self, character: Character):
        if self.stealth_disadvantage:
            character.add_condition("ClunkyArmor")
        if character.ability_scores["Strength"] < self.strength_required:
            character.add_condition("ArmorTooHeavy")
        if self.category is not None and self.category not in character.proficiencies["Armor"]:
            character.add_condition("ProficiencyGappedArmor")
        return self

    def on_unequip(self, character: Character):
        character.remove_condition(["ClunkyArmor", "ArmorTooHeavy", "ProficiencyGappedArmor"])
        return self


class Clothing(Armor):
    def __init__(self, name="Clothing", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.name = name
        self.description = description


class PaddedArmor(Armor):
    def __init__(self, name="Padded Armor", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.name = name
        self.description = description
        self.category = "Light"
        self.stealth_disadvantage = True
        self.base_ac = 11
        self.add_dex = True
        self.weight = 8
        self.value = 5


class LeatherArmor(Armor):
    def __init__(self, name="Leather Armor", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.name = name
        self.description = description
        self.category = "Light"
        self.base_ac = 11
        self.add_dex = True
        self.weight = 10
        self.value = 10


class StuddedLeatherArmor(Armor):
    def __init__(self, name="Studded Leather Armor", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.name = name
        self.description = description
        self.category = "Light"
        self.base_ac = 11
        self.add_dex = True
        self.weight = 13
        self.value = 45


class HideArmor(Armor):
    def __init__(self, name="Hide Armor", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.name = name
        self.description = description
        self.category = "Medium"
        self.base_ac = 12
        self.add_dex = True
        self.dex_add_max = 2
        self.weight = 12
        self.value = 10


class ChainShirt(Armor):
    def __init__(self, name="Chain Shirt", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.name = name
        self.description = description
        self.category = "Medium"
        self.base_ac = 13
        self.add_dex = True
        self.dex_add_max = 2
        self.weight = 20
        self.value = 50


class ScaleMail(Armor):
    def __init__(self, name="Scale Mail", description="", **kwargs):
        super().__init__(name, description, **kwargs)
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
    def __init__(self, name="Breastplate", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.name = name
        self.description = description
        self.category = "Medium"
        self.base_ac = 14
        self.add_dex = True
        self.dex_add_max = 2
        self.weight = 20
        self.value = 400


class HalfPlateArmor(Armor):
    def __init__(self, name="Half Plate Armor", description="", **kwargs):
        super().__init__(name, description, **kwargs)
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
    def __init__(self, name="Ring Mail", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.name = name
        self.description = description
        self.category = "Heavy"
        self.base_ac = 14
        self.stealth_disadvantage = True
        self.weight = 40
        self.value = 30


class ChainMail(Armor):
    def __init__(self, name="Chain Mail", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.name = name
        self.description = description
        self.category = "Heavy"
        self.base_ac = 16
        self.stealth_disadvantage = True
        self.strength_required = 13
        self.weight = 55
        self.value = 75


class SplintArmor(Armor):
    def __init__(self, name="Splint Armor", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.name = name
        self.description = description
        self.category = "Heavy"
        self.base_ac = 17
        self.stealth_disadvantage = True
        self.strength_required = 15
        self.weight = 60
        self.value = 200


class PlateArmor(Armor):
    def __init__(self, name="Plate Armor", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.name = name
        self.description = description
        self.category = "Heavy"
        self.base_ac = 18
        self.stealth_disadvantage = True
        self.strength_required = 15
        self.weight = 65
        self.value = 1500


class Shield(Armor):
    def __init__(self, name="Shield", description="", **kwargs):
        super().__init__(name, description, **kwargs)
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
