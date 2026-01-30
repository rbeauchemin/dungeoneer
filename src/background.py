class Background:
    def __init__(self):
        self.todo = []
        self.description = ""
        self.feats = []
        self.ability_scores = []
        self.proficiencies = {
            "Armor": [],
            "Weapons": [],
            "Tools": [],
            "Skills": []
        }
        self.starting_equipment = []

    def select_ability_scores(self, character, choices, **kwargs):
        """You can either add 2 to one ability and one to another, or add 1 to all three.
        """
        if len(choices) == 2:
            character.ability_scores[choices[0]] += 2
            character.ability_scores[choices[1]] += 1
        elif len(choices) == 3:
            for ability in choices:
                if ability in self.ability_scores:
                    character.ability_scores[ability] += 1

        for ability in choices:
            if ability in self.ability_scores:
                character.ability_scores[ability] += 1
        return character


class Acolyte(Background):
    def __init__(self):
        super().__init__()
        self.description = "You have spent your life in the service of a temple to a specific god or pantheon of gods. You act as an intermediary between the realm of the holy and the mortal world, performing sacred rites and offering sacrifices in order to conduct worshipers into the presence of the divine."
        # TODO: Refactor all todos to have the text, options, and function keys, and then also add number of choices allowed.
        self.todo = [
            {
                "Text": "Select either 50 gold or starting equipment (Caligrapher's Supplies, Book (prayers), Holy Symbol, Parchment (10 sheets), Robe, 8 gold).",
                "Options": [
                    "50 gold",
                    "Starting Equipment"
                ],
                "Function": self.grant_starting_equipment
            },
            {
                "Text": "Choose two-three abilities to increase. One ability increases by 2, the other by 1. Or, three abilities increase by 1 each.",
                "Options": self.ability_scores,
                "Function": self.select_ability_scores
            }
        ]
        self.ability_scores = ["Intelligence", "Wisdom", "Charisma"]
        self.proficiencies["Skills"] = ["Insight", "Religion"]
        self.proficiencies["Tools"] = ["Caligrapher's Supplies"]
        # TODO Add feats!

    def grant_starting_equipment(self, character, choice, **kwargs):
        if choice == "50 gold":
            character.gold += 50
        else:
            character.equipment += [
                "Caligrapher's Supplies",
                "Book (prayers)",
                "Holy Symbol",
                "Parchment (10 sheets)",
                "Robe"
            ]
            character.gold += 8
        return character


class Artisan(Background):
    def __init__(self):
        super().__init__()
        self.todo = [
            {
                "Text": "Choose a type of artisan's tools to be proficient with.",
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
                "Function": self.set_tool_proficiency
            },
        ]
        self.description = "You learned your trade from a master and are proficient with the use of a set of artisan's tools. You are part of a guild, which provides you with certain benefits and obligations."
        self.proficiencies["Tools"] = [tool_proficiency]
        self.proficiencies["Skills"] = ["Insight", "Persuasion"]
        self.starting_equipment = [
            f"{tool_proficiency} set",
            "Letter from guild",
            "Traveler's Clothes",
            "15 gold"
        ]
        self.ability_scores = ["Strength", "Dexterity", "Intelligence"]