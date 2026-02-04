class Feat:
    def __init__(self):
        self.todo = []
        self.name = ""
        self.description = ""
        self.prerequisites = {}

    def apply_to_character(self, character):
        pass


# TODO: At least complete the origin feats


class Alert(Feat):
    def __init__(self):
        super().__init__()
        self.name = "Alert"
        self.description = "Always on the lookout for danger, you gain the following benefits: You gain a +5 bonus to initiative. You can't be surprised while you are conscious. Other creatures don't gain advantage on attack rolls against you as a result of being unseen by you."


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

    def apply_to_character(self, character):
        pass


class Tough(Feat):
    def __init__(self):
        super().__init__()
        self.name = "Tough"
        self.description = "Your hit point maximum increases by an amount equal to twice your level when you gain this feat. Whenever you gain a level thereafter, your hit point maximum increases by an additional 2 hit points."

    def apply_to_character(self, character):
        character.max_hp += 2 * character.level
