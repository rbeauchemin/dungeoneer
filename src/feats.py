from typing import Literal
from creatures import Character


class Feat:
    def __init__(self):
        self.todo = []
        self.name = ""
        self.description = ""
        self.prerequisites = {}

    def apply_to_character(self, character: Character):
        return character


# TODO: At least complete the origin feats


class Alert(Feat):
    def __init__(self):
        super().__init__()
        self.name = "Alert"
        self.description = "Always on the lookout for danger, you gain the following benefits: You gain a +5 bonus to initiative. You can't be surprised while you are conscious. Other creatures don't gain advantage on attack rolls against you as a result of being unseen by you."

    def apply_to_character(self, character: Character):
        character.proficiencies["Special"] += ["Initiative"]
        character.special_traits += ["Initiative Swap"]
        return character


class Crafter(Feat):
    def __init__(self, tool_type=None):
        super().__init__()
        self.name = "Crafter"
        self.tool_type = tool_type
        if tool_type is None:
            self.todo = [{
                "Text": "Choose three artisan's tools to gain proficiency with.",
                "Options": [
                    "Alchemist's Supplies",
                    "Brewer's Supplies",
                    "Calligrapher's Supplies",
                    "Carpenter's Tools",
                    "Cartographer's Tools",
                    "Cobbler's Tools",
                    "Cook's Utensils",
                    "Glassblower's Tools",
                    "Jeweler's Tools",
                    "Leatherworker's Tools",
                    "Mason's Tools",
                    "Painter's Supplies",
                    "Potter's Tools",
                    "Smith's Tools",
                    "Tinker's Tools",
                    "Weaver's Tools",
                    "Woodcarver's Tools"
                ],
                "Function": self.set_tool_proficiency,
                "Choices": 3
            }]
        self.description = "You gain proficiency with artisan's tools of your choice. You can use your tools to create items during a long rest, provided you have the necessary materials. The time and cost to create an item depend on its complexity and value."

    def set_tool_proficiency(self, character: Character, choices):
        character.proficiencies["Tools"] += choices
        return character

    def apply_to_character(self, character: Character):
        character.special_traits += ["Discount", "Fast Crafting"]
        # TODO: Add handling for crafting items during long rest and discount on nonmagical items
        return character


class Healer(Feat):
    def __init__(self):
        super().__init__()
        self.name = "Healer"
        self.description = "You have always cared for others, whether after battle or after illness befell your community, and gain bonuses to healing"

    def apply_to_character(self, character: Character):
        character.special_traits += ["Battle Medic", "Healing Rerolls"]
        return character


class MagicInitiate(Feat):
    def __init__(self, spell_list=Literal["Cleric", "Druid", "Wizard"]):
        super().__init__()
        self.name = "Magic Initiate (" + spell_list + ")"
        self.spell_list = spell_list
        self.description = "Choose a class from the following list: Cleric, Druid, Wizard. You learn two cantrips of your choice from that class's spell list. In addition, choose one 1st-level spell from that same list. You learn that spell and can cast it at its lowest level. Once you cast it, you must finish a long rest before you can cast it again using this feat."

    def apply_to_character(self, character: Character):
        character.todo.append(
            {
                "Text": f"Choose two cantrips and one 1st-level spell from the {self.spell_list} spell list.",
                "Options": [],  # TODO: Fill in options based on spell list
                "Function": self.select_spells,
                "Choices": 3
            }
        )

    def select_spells(self, character: Character, choices):
        for choice in choices:
            character.spells.append(choice)


MagicInitiateCleric = MagicInitiate(spell_list="Cleric")
MagicInitiateDruid = MagicInitiate(spell_list="Druid")
MagicInitiateWizard = MagicInitiate(spell_list="Wizard")


class Tough(Feat):
    def __init__(self):
        super().__init__()
        self.name = "Tough"
        self.description = "Your hit point maximum increases by an amount equal to twice your level when you gain this feat. Whenever you gain a level thereafter, your hit point maximum increases by an additional 2 hit points."

    def apply_to_character(self, character):
        character.max_hp += 2 * character.level
