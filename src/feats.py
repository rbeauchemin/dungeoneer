from typing import Literal
from creatures import Character
from common import artisans_tools, other_tools, dnd_skills


class Feat:
    def __init__(self):
        self.todo = []
        self.name = ""
        self.description = ""
        self.prerequisites = {}
        self.repeatable = False

    def apply_to_character(self, character: Character):
        return character


class Alert(Feat):
    def __init__(self):
        super().__init__()
        self.name = "Alert"
        self.description = "Always on the lookout for danger, you gain the following benefits: You gain a +5 bonus to initiative. You can't be surprised while you are conscious. Other creatures don't gain advantage on attack rolls against you as a result of being unseen by you."

    def apply_to_character(self, character: Character):
        # TODO: Add handling for both of these when combat code is created
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
                "Options": artisans_tools,
                "Function": self.set_tool_proficiency,
                "Choices": 3
            }]
        self.description = "You gain proficiency with artisan's tools of your choice. You can use your tools to create items during a long rest, provided you have the necessary materials. The time and cost to create an item depend on its complexity and value."

    def set_tool_proficiency(self, character: Character, choices):
        character.proficiencies["Tools"] += choices
        return character

    def apply_to_character(self, character: Character):
        # NOTE: Discount is handled in the buying part of the code
        # TODO: Add handling for crafting items during long rest and discount on nonmagical items
        character.special_traits += ["Discount", "Fast Crafting"]
        return character


class Healer(Feat):
    def __init__(self):
        super().__init__()
        self.name = "Healer"
        self.description = "You have always cared for others, whether after battle or after illness befell your community, and gain bonuses to healing"

    def apply_to_character(self, character: Character):
        # TODO: Handle both of these
        character.special_traits += ["Battle Medic", "Healing Rerolls"]
        return character


class Lucky(Feat):
    def __init__(self):
        super().__init__()
        self.name = "Lucky"
        self.description = "You're lucky!"

    def apply_to_character(self, character: Character):
        # TODO: Handle Lucky as a special ability (spell) that applies to next roll.
        character.special_traits += ["Lucky"]
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


class Musician(Feat):
    def __init__(self):
        super().__init__()
        self.name = "Musician"
        self.description = "You know how to play instruments for a crowd."

    def apply_to_character(self, character: Character):
        # TODO: Add special ability to add Heroic Inspiration to allies using the below note
        # As you finish a Short or Long Rest, you can play a song on a Musical Instrument with which you have proficiency and give Heroic Inspiration to allies who hear the song. The number of allies you can affect in this way equals your Prof
        character.todo += [
            {
                "Text": "Select an instrument to gain proficiency in.",
                "Options": ["Bagpipes", "Drum", "Dulcimer", "Flute", "Horn", "Lute", "Lyre", "Pan Flute", "Shawm", "Viol"],
                "Function": self.add_proficiencies,
                "Choices": 3
            }
        ]
        return character

    def add_proficiencies(self, character, choices, **kwargs):
        character.proficiencies["Tools"].extend(choices)
        return character


class SavageAttacker(Feat):
    def __init__(self):
        super().__init__()
        self.name = "Savage Attacker"
        self.description = "Once per turn when you hit a target with an attack, you may roll damage dice twice and sue either roll."

    def apply_to_character(self, character: Character):
        # TODO: Implement this in creatures.py with a once/turn check and a `savage`` kwarg
        return character


class Skilled(Feat):
    def __init__(self):
        super().__init__()
        self.name = "Skilled"
        self.description = "You're skilled!"

    def apply_to_character(self, character: Character):
        character.todo += [
            {
                "Text": "Select three tools/skills to gain proficiency in",
                "Options": [
                    "Tool - " + tool for tool in artisans_tools + other_tools
                ] + [
                    "Skill - " + skill for skill in dnd_skills
                ],
                "Function": self.add_proficiencies,
                "Choices": 3
            }
        ]
        return character

    def add_proficiencies(self, character, choices, **kwargs):
        for choice in choices:
            if choice.startswith("Tool"):
                character.proficiencies["Tools"].extend([choice.lstrip("Tool - ")])
            else:
                character.proficiencies["Skills"].extend([choice.lstrip("Skill - ")])


class TavernBrawler(Feat):
    def __init__(self):
        super().__init__()
        self.name = "Tavern Brawler"
        self.description = "You know how to fight with your bare hands."

    def apply_to_character(self, character: Character):
        # NOTE: Increased unarmed damage is handled in weapons.py
        # TODO: Implement Damage Rerolls and Push
        character.proficiencies["Weapons"] += "Improvised"
        return character


class Tough(Feat):
    def __init__(self):
        super().__init__()
        self.name = "Tough"
        self.description = "Your hit point maximum increases by an amount equal to twice your level when you gain this feat. Whenever you gain a level thereafter, your hit point maximum increases by an additional 2 hit points."

    def apply_to_character(self, character):
        character.max_hp += 2 * character.level


# TODO: Complete the rest of the feats!
