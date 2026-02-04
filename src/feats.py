class Feat:
    def __init__(self):
        self.todo = []
        self.name = ""
        self.description = ""
        self.prerequisites = {}

    def apply_to_character(self, character):
        pass


# TODO: At least complete the origin feats


class Tough(Feat):
    def __init__(self):
        super().__init__()
        self.name = "Tough"
        self.description = "Your hit point maximum increases by an amount equal to twice your level when you gain this feat. Whenever you gain a level thereafter, your hit point maximum increases by an additional 2 hit points."

    def apply_to_character(self, character):
        character.max_hp += 2 * character.level
        character.feats.append(self)