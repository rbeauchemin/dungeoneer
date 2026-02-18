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
