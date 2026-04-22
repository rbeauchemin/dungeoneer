from src.common import dnd_skills
from src.creatures import Character


class Item():
    def __init__(self, name="Item", description="", **kwargs):
        self.name = name
        self.description = description
        self.type = kwargs.get("type", None)
        self.value = kwargs.get("value", 0)
        self.magical = kwargs.get("magical", False)
        self.rarity = kwargs.get("rarity", "Common")
        self.weight = kwargs.get("weight", 0)
        self.quantity = kwargs.get("quantity", 1)
        # Can be Common, Uncommon, Rare, Legendary

    def purchase(self, character: Character, quantity: int = 1, cost_multiplier: float = 1.0):
        if "Discount" in character.special_traits and not self.magical:
            value = round(self.value * 0.8)
        else:
            value = self.value
        value = value * quantity * cost_multiplier
        if character.gold >= value:
            character.gold -= value
            character.add_item(self, purchasing=False, quantity=quantity)
        else:
            print(f"{character.name} does not have the gold to purchase {self.name}.")

    def sell(self, character: Character, quantity: int = 1):
        if self.type in ["Armor", "Weapon", "Shield"]:
            value = self.value // 2
        else:
            value = self.value
        value = value * quantity
        for item in character.inventory:
            if item.name == self.name:
                if quantity < item.quantity:
                    character.gold += value
                    item.quantity -= quantity
                    return
                elif quantity == item.quantity:
                    character.gold += value
                    character.inventory.remove(item)
                    return
                else:
                    print(f"{character.name} does not have {quantity} {self.name} in their inventory. They have {item.quantity}.")

        print(f"{character.name} does not have {self.name} in their inventory.")


class SpellBook(Item):
    def __init__(self, name="Spellbook", description="A book containing spells that a spellcaster can prepare and cast.", **kwargs):
        super().__init__(name=name, description=description, type="Miscellaneous", **kwargs)
        self.known_spells = kwargs.get("known_spells", [])
        self.prepared_spells = kwargs.get("prepared_spells", [])
        self.weight = 3

    def add_spell(self, spell):
        from src.spells import Spell
        if isinstance(spell, str):
            import importlib
            module = importlib.import_module("src.spells")
            spell = getattr(module, spell, None)()
        if not isinstance(spell, Spell):
            print(f"{spell} is not a valid spell.")
            return
        self.known_spells.append(spell)
