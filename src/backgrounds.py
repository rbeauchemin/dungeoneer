from src.feats import (
    Alert, Crafter, Healer, Lucky, Musician,
    MagicInitiateCleric, MagicInitiateDruid, MagicInitiateWizard,
    SavageAttacker, Skilled, TavernBrawler, Tough
)


# TODO: All equipment below should have classes added instead of text, allowing use of quantity fields as well
class Background:
    def __init__(self, **kwargs):
        self.description = ""
        self.feats = []
        self.ability_scores = kwargs.get("ability_scores", [])
        self.starting_equipment_details = kwargs.get("starting_equipment_details", [])
        self.todo = [
            {
                "Text": "Choose two-three abilities to increase. One ability increases by 2, the other by 1. Or, three abilities increase by 1 each.",
                "Options": self.ability_scores,
                "Function": self.select_ability_scores
            },
            {
                "Text": f"Select either 50 gold or starting equipment ({self.starting_equipment_details}).",
                "Options": [
                    "50 gold",
                    "Starting Equipment"
                ],
                "Function": self.grant_starting_equipment
            }
        ]
        self.proficiencies = {
            "Armor": [],
            "Weapons": [],
            "Tools": [],
            "Skills": [],
            "Saving Throws": []
        }
        self.starting_equipment = []

    def select_ability_scores(self, character, choices, **kwargs):
        """You can either add 2 to one ability and 1 to another, or add 1 to all three.
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

    def grant_starting_equipment(self, character, choices, **kwargs):
        # Implemented by subclasses
        return

    def apply_to_character(self, character):
        character.proficiencies["Armor"] += self.proficiencies["Armor"]
        character.proficiencies["Weapons"] += self.proficiencies["Weapons"]
        character.proficiencies["Tools"] += self.proficiencies["Tools"]
        character.proficiencies["Saving Throws"] += self.proficiencies["Saving Throws"]
        character.proficiencies["Skills"] += self.proficiencies["Skills"]
        character.feats += self.feats
        for feat in self.feats:
            feat.apply_to_character(character)
        character.todo += self.todo
        return character


class Acolyte(Background):
    def __init__(self):
        self.ability_scores = ["Intelligence", "Wisdom", "Charisma"]
        super().__init__(ability_scores=self.ability_scores, starting_equipment_details="Calligrapher's Supplies, Book (prayers), Holy Symbol, Parchment (10 sheets), Robe, 8 gold")
        self.description = "You have spent your life in the service of a temple to a specific god or pantheon of gods. You act as an intermediary between the realm of the holy and the mortal world, performing sacred rites and offering sacrifices in order to conduct worshipers into the presence of the divine."
        self.proficiencies["Skills"] = ["Insight", "Religion"]
        self.proficiencies["Tools"] = ["Calligrapher's Supplies"]
        self.feats += [MagicInitiateCleric]

    def grant_starting_equipment(self, character, choices, **kwargs):
        if "50 gold" in choices:
            character.gold += 50
        else:
            character.inventory += [
                "Calligrapher's Supplies",
                "Book (prayers)",
                "Holy Symbol",
                "Robe"
            ] + ["Parchment"] * 10
            character.gold += 8
        return character


class Artisan(Background):
    def __init__(self):
        self.ability_scores = ["Strength", "Dexterity", "Intelligence"]
        super().__init__(ability_scores=self.ability_scores, starting_equipment_details="Artisan's tools you are proficient in, 2 pouches, Traveler's Clothes, and 32 gold")
        self.todo += [
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
            }
        ]
        self.description = "You learned your trade from a master and are proficient with the use of a set of artisan's tools. You are part of a guild, which provides you with certain benefits and obligations."
        self.proficiencies["Skills"] = ["Investigation", "Persuasion"]
        self.feats += [Crafter()]

    def set_tool_proficiency(self, character, choices, **kwargs):
        self.proficiencies["Tools"] = choices
        character.proficiencies["Tools"].extend(choices)
        return character

    def grant_starting_equipment(self, character, choices, **kwargs):
        if "50 gold" in choices:
            character.gold += 50
        else:
            character.inventory += [self.proficiencies["Tools"], "Pouch", "Pouch", "Traveler's Clothes"]
            character.gold += 32
        return character


class Charlatan(Background):
    def __init__(self):
        self.ability_scores = ["Dexterity", "Constitution", "Charisma"]
        super().__init__(ability_scores=self.ability_scores, starting_equipment_details="Forgery Kit, Costume, Fine Clothes, 15 gold")
        self.description = "Once you were old enough to order an ale, you soon had a favorite stool in every tavern within ten miles of where you were born. As you traveled the circuit from public house to watering hole, you learned to prey on unfortunates who were in the market for a comforting lie or two - perhaps a sham potion or forged ancestry records."
        self.proficiencies["Skills"] = ["Deception", "Sleight of Hand"]
        self.proficiencies["Tools"] = ["Forgery Kit"]
        self.feats += [Skilled()]

    def grant_starting_equipment(self, character, choices, **kwargs):
        if "50 gold" in choices:
            character.gold += 50
        else:
            character.inventory += ["Forgery Kit", "Costume", "Fine Clothes"]
            character.gold += 15
        return character


class Criminal(Background):
    def __init__(self):
        self.ability_scores = ["Dexterity", "Constitution", "Intelligence"]
        super().__init__(ability_scores=self.ability_scores, starting_equipment_details="2 Daggers, Thieves' Tools, Crowbar, 2 Pouches, Traveler's Clothes, 16 gold")
        self.description = "You eked out a living in dark alleyways, cutting purses or burgling shops. Perhaps you were part of a small gang of like-minded wrongdoers who looked out for each other. Or maybe you were a lone wolf, fending for yourself against the local thieves' guild and more fearsome lawbreakers."
        self.proficiencies["Skills"] = ["Sleight of Hand", "Stealth"]
        self.proficiencies["Tools"] = ["Thieves' Tools"]
        self.feats += [Alert()]

    def grant_starting_equipment(self, character, choices, **kwargs):
        if "50 gold" in choices:
            character.gold += 50
        else:
            character.inventory += ["Dagger", "Dagger", "Thieves' Tools", "Crowbar", "Pouch", "Pouch", "Traveler's Clothes"]
            character.gold += 16
        return character


class Entertainer(Background):
    def __init__(self):
        self.ability_scores = ["Strength", "Dexterity", "Charisma"]
        super().__init__(ability_scores=self.ability_scores, starting_equipment_details="Musical Instrument you are proficient in, 2 Costumes, Mirror, Perfume, Traveler's Clothes, 11 gold")
        self.description = "You spent much of your youth following roving fairs and carnivals, performing odd jobs for musicians and acrobats in exchange for lessons. You may have learned how to walk a tightrope, how to play a lute in a distinct style, or how to recite poetry with impeccable diction. To this day, you thrive on applause and long for the stage."
        self.proficiencies["Skills"] = ["Acrobatics", "Performance"]
        self.proficiencies["Tools"] = []
        self.feats += [Musician()]
        self.todo += [
            {
                "Text": "Choose an instrument to be proficient in.",
                "Options": ["Bagpipes", "Drum", "Dulcimer", "Flute", "Horn", "Lute", "Lyre", "Pan Flute", "Shawm", "Viol"],
                "Function": self.set_tool_proficiency
            }
        ]

    def set_tool_proficiency(self, character, choices, **kwargs):
        self.proficiencies["Tools"] = choices
        character.proficiencies["Tools"].extend(choices)
        return character

    def grant_starting_equipment(self, character, choices, **kwargs):
        if "50 gold" in choices:
            character.gold += 50
        else:
            character.inventory += ["Costume", "Costume", "Mirror", "Perfume", "Traveler's Clothes"] + self.proficiencies["Tools"]
            character.gold += 11
        return character


class Farmer(Background):
    def __init__(self):
        self.ability_scores = ["Strength", "Constitution", "Wisdom"]
        super().__init__(ability_scores=self.ability_scores, starting_equipment_details="Sickle, Carpenter's Tools, Healer's Kit, Iron Pot, Shovel, Traveler's Clothes, 30 gold")
        self.description = "You grew up close to the land. Years tending animals and cultivating the earth rewarded you with patience and good health. You have a keen appreciation for nature's bounty alongside a healthy respect for nature's wrath."
        self.proficiencies["Skills"] = ["Animal Handling", "Nature"]
        self.proficiencies["Tools"] = ["Carpenter's Tools"]
        self.feats += [Tough()]
        self.todo += [
            {
                "Text": "Select either 50 gold or starting equipment ().",
                "Options": ["Starting Equipment", "50 gold"],
                "Function": self.grant_starting_equipment
            }
        ]

    def grant_starting_equipment(self, character, choices, **kwargs):
        if "50 gold" in choices:
            character.gold += 50
        else:
            character.inventory += ["Sickle", "Carpenter's Tools", "Healer's Kit", "Iron Pot", "Shovel", "Traveler's Clothes"]
            character.gold += 30
        return character


class Guard(Background):
    def __init__(self):
        self.ability_scores = ["Strength", "Intelligence", "Wisdom"]
        super().__init__(ability_scores=self.ability_scores, starting_equipment_details="Spear, Light Crossbow, 20 Bolts, Gaming Set (same as above), Hooded Lan-tern, Manacles, Quiver, Traveler's Clothes, 12 gold")
        self.description = "Your feet ache when you remember the countless hours you spent at your post in the tower. You were trained to keep one eye looking outside the wall, watching for marauders sweeping from the nearby forest, and your other eye looking inside the wall, searching for cutpurses and troublemakers."
        self.proficiencies["Skills"] = ["Athletics", "Perception"]
        self.feats += [Alert()]
        self.todo += [
            {
                "Text": "Choose a gaming set to be proficient in.",
                "Options": ["Dice", "Dragonchess", "Playing Cards", "Three-Dragon Ante"],
                "Function": self.set_tool_proficiency
            }
        ]

    def set_tool_proficiency(self, character, choices, **kwargs):
        self.proficiencies["Tools"] = choices
        character.proficiencies["Tools"].extend(choices)
        return character

    def grant_starting_equipment(self, character, choices, **kwargs):
        if "50 gold" in choices:
            character.gold += 50
        else:
            character.inventory += ["Spear", "Light Crossbow", "Hooded Lantern", "Manacles", "Quiver", "Traveler's Clothes"] + self.proficiencies["Tools"] + ["Bolts"] * 20
            character.gold += 12
        return character


class Hermit(Background):
    def __init__(self):
        self.ability_scores = ["Constitution", "Wisdom", "Charisma"]
        super().__init__(ability_scores=self.ability_scores, starting_equipment_details="Quarterstaff, Herbalism Kit, Bedroll, Book (philosophy), Lamp, Oil (3 flasks), Traveler's Clothes, 16 gold")
        self.description = "You spent your early years secluded in a hut or monastery located well beyond the outskirts of the nearest settlement. In those days, your only companions were the creatures of the forest and those who would occasionally visit to bring news of the outside world and supplies. The solitude allowed you to spend many hours pondering the mysteries of creation."
        self.proficiencies["Skills"] = ["Medicine", "Religion"]
        self.proficiencies["Tools"] = ["Herbalism Kit"]
        self.feats += [Healer()]

    def grant_starting_equipment(self, character, choices, **kwargs):
        if "50 gold" in choices:
            character.gold += 50
        else:
            character.inventory += ["Quarterstaff", "Herbalism Kit", "Bedroll", "Book (philosophy)", "Lamp", "Traveler's Clothes"] + ["Oil Flask"] * 3
            character.gold += 16
        return character


class Guide(Background):
    def __init__(self):
        self.ability_scores = ["Dexterity", "Constitution", "Wisdom"]
        super().__init__(ability_scores=self.ability_scores, starting_equipment_details="Shortbow, 20 Arrows, Cartographer's Tools, Bedroll, Quiver, Tent, Traveler's Clothes, 3 gold")
        self.description = "You came of age outdoors, far from settled lands. Your home was anywhere you chose to spread your bedroll. There are wonders in the wilderness — strange monsters, pristine forests and streams, overgrown ruins of great halls once trod by giants - and you learned to fend for yourself as you explored them. From time to time, you guided friendly nature priests who instructed you in the fundamentals of channeling the magic of the wild."
        self.proficiencies["Skills"] = ["Stealth", "Survival"]
        self.proficiencies["Tools"] = ["Cartographer's Tools"]
        self.feats += [MagicInitiateDruid]

    def grant_starting_equipment(self, character, choices, **kwargs):
        if "50 gold" in choices:
            character.gold += 50
        else:
            character.inventory += ["Shortbow", "Cartographer's Tools", "Bedroll", "Quiver", "Tent", "Traveler's Clothes"] + ["Arrows"] * 20
            character.gold += 3
        return character


class Merchant(Background):
    def __init__(self):
        self.ability_scores = ["Constitution", "Intelligence", "Charisma"]
        super().__init__(ability_scores=self.ability_scores, starting_equipment_details="Navigator's Tools, 2 Pouches, Traveler's Clothes, 22 gold")
        self.description = "You were apprenticed to a trader, caravan master, or shopkeeper, learning the fundamentals of commerce. You traveled broadly, and you earned a living by buying and selling the raw materials artisans need to practice their craft or finished works from such crafters. You might have transported goods from one place to another (by ship, wagon, or cara-van) or bought them from traveling traders and sold them in your own shop."
        self.proficiencies["Skills"] = ["Animal Handling", "Persuasion"]
        self.proficiencies["Tools"] = ["Navigator's Tools"]
        self.feats += [Lucky()]

    def grant_starting_equipment(self, character, choices, **kwargs):
        if "50 gold" in choices:
            character.gold += 50
        else:
            character.inventory += ["Navigator's Tools", "Pouch", "Pouch", "Traveler's Clothes"]
            character.gold += 22
        return character


class Noble(Background):
    def __init__(self):
        self.ability_scores = ["Strength", "Intelligence", "Charisma"]
        super().__init__(ability_scores=self.ability_scores, starting_equipment_details="Gaming Set, Fine Clothes, Perfume, 29 gold")
        self.description = "You were raised in a castle, surrounded by wealth, power, and privilege. Your family of minor aristocrats ensured that you received a first-class education, some of which you appreciated and some of which you resented. Your time in the castle, especially the many hours you spent observing your family at court, also taught you a great deal about leadership."
        self.proficiencies["Skills"] = ["History", "Persuasion"]
        self.feats += [Skilled()]
        self.todo += [
            {
                "Text": "Choose a gaming set to be proficient in.",
                "Options": ["Dice", "Dragonchess", "Playing Cards", "Three-Dragon Ante"],
                "Function": self.set_tool_proficiency
            }
        ]

    def set_tool_proficiency(self, character, choices, **kwargs):
        self.proficiencies["Tools"] = choices
        character.proficiencies["Tools"].extend(choices)
        return character

    def grant_starting_equipment(self, character, choices, **kwargs):
        if "50 gold" in choices:
            character.gold += 50
        else:
            character.inventory += ["Fine Clothes", "Perfume"] + self.proficiencies["Tools"]
            character.gold += 29
        return character


class Sage(Background):
    def __init__(self):
        self.ability_scores = ["Constitution", "Intelligence", "Wisdom"]
        super().__init__(ability_scores=self.ability_scores, starting_equipment_details="Quarterstaff, Calligrapher's Supplies, Book (history), Parchment (8 sheets), Robe, 8 gold")
        self.description = "You spent your formative years traveling between manors and monasteries, performing various odd jobs and services in exchange for access to their libraries. You whiled away many a long evening studying books and scrolls, learning the lore of the multiverse - even the rudiments of magic - and your mind yearns for more."
        self.proficiencies["Skills"] = ["Arcana", "History"]
        self.proficiencies["Tools"] = ["Calligrapher's Supplies"]
        self.feats += [MagicInitiateWizard]

    def grant_starting_equipment(self, character, choices, **kwargs):
        if "50 gold" in choices:
            character.gold += 50
        else:
            character.inventory += ["Quarterstaff", "Calligrapher's Supplies", "Book (history)", "Robe"] + ["Parchment"] * 8
            character.gold += 8
        return character


class Sailor(Background):
    def __init__(self):
        self.ability_scores = ["Strength", "Dexterity", "Wisdom"]
        super().__init__(ability_scores=self.ability_scores, starting_equipment_details="Dagger, Navigator's Tools, Rope, Traveler's Clothes, 20 gold")
        self.description = "You lived as a seafarer, wind at your back and decks swaying beneath your feet. You've perched on barstools in more ports of call than you can remember, faced mighty storms, and swapped stories with folk who live beneath the waves."
        self.proficiencies["Skills"] = ["Acrobatics", "Perception"]
        self.proficiencies["Tools"] = ["Navigator's Tools"]
        self.feats += [TavernBrawler()]

    def grant_starting_equipment(self, character, choices, **kwargs):
        if "50 gold" in choices:
            character.gold += 50
        else:
            character.inventory += ["Dagger", "Navigator's Tools", "Rope", "Traveler's Clothes"]
            character.gold += 20
        return character


class Scribe(Background):
    def __init__(self):
        self.ability_scores = ["Dexterity", "Intelligence", "Wisdom"]
        super().__init__(ability_scores=self.ability_scores, starting_equipment_details="Calligrapher's Supplies, Fine Clothes, Lamp, Oil (3 flasks), Parchment (12 sheets), 23 gold")
        self.description = "You spent formative years in a scriptorium, a monastery dedicated to the preservation of knowledge, or a government agency, where you learned to write with a clear hand and produce finely written texts. Perhaps you scribed government documents or copied tomes of literature. You might have some skill as a writer of poetry, narrative, or scholarly research. Above all, you have a careful attention to detail, helping you avoid introducing mistakes to the documents you copy and create."
        self.proficiencies["Skills"] = ["Investigation", "Perception"]
        self.proficiencies["Tools"] = ["Calligrapher's Supplies"]
        self.feats += [Skilled()]

    def grant_starting_equipment(self, character, choices, **kwargs):
        if "50 gold" in choices:
            character.gold += 50
        else:
            character.inventory += ["Calligrapher's Supplies", "Fine Clothes", "Lamp"] + ["Oil Flask"] * 3 + ["Parchment"] * 12
            character.gold += 23
        return character


class Soldier(Background):
    def __init__(self):
        self.ability_scores = ["Strength", "Dexterity", "Constitution"]
        super().__init__(ability_scores=self.ability_scores, starting_equipment_details="Spear, Shortbow, 20 Arrows, Gaming Set , Healer's Kit, Quiver, Traveler's Clothes, 14 gold")
        self.description = "You began training for war as soon as you reached adulthood and carry precious few memories of life before you took up arms. Battle is in your blood. Sometimes you catch yourself reflexively performing the basic fighting exercises you learned first. Eventually, you put that training to use on the battlefield, protecting the realm by waging war."
        self.proficiencies["Skills"] = ["Athletics", "Intimidation"]
        self.feats += [SavageAttacker()]
        self.todo += [
            {
                "Text": "Choose a gaming set to be proficient in.",
                "Options": ["Dice", "Dragonchess", "Playing Cards", "Three-Dragon Ante"],
                "Function": self.set_tool_proficiency
            }
        ]

    def set_tool_proficiency(self, character, choices, **kwargs):
        self.proficiencies["Tools"] = choices
        character.proficiencies["Tools"].extend(choices)
        return character

    def grant_starting_equipment(self, character, choices, **kwargs):
        if "50 gold" in choices:
            character.gold += 50
        else:
            character.inventory += ["Spear", "Shortbow", "Healer's Kit", "Quiver", "Traveler's Clothes"] + self.proficiencies["Tools"] + ["Arrows"] * 20
            character.gold += 14
        return character


class Wayfarer(Background):
    def __init__(self):
        self.ability_scores = ["Dexterity", "Wisdom", "Charisma"]
        super().__init__(ability_scores=self.ability_scores, starting_equipment_details="2 Daggers, Thieves' Tools, Gaming Set of choice, Bedroll, 2 Pouches, Traveler's Clothes, 16 gold")
        self.description = "You grew up on the streets surrounded by similarly ill-fated castoffs, a few of them friends and a few of them rivals. You slept where you could and did odd jobs for food. At times, when the hunger became unbearable, you resorted to theft. Still, you never lost your pride and never abandoned hope. Fate is not yet finished with you."
        self.proficiencies["Skills"] = ["Insight", "Stealth"]
        self.proficiencies["Tools"] = ["Thieves' Supplies"]
        self.tool_preference = []
        self.feats += [Lucky()]
        self.todo += [
            {
                "Text": "Choose a gaming set you may have picked up on your journey.",
                "Options": ["Dice", "Dragonchess", "Playing Cards", "Three-Dragon Ante"],
                "Function": self.set_tool_preference
            }
        ]

    def set_tool_preference(self, character, choices, **kwargs):
        self.tool_preference = choices
        return character

    def grant_starting_equipment(self, character, choices, **kwargs):
        if "50 gold" in choices:
            character.gold += 50
        else:
            character.inventory += ["Dagger", "Dagger", "Thieves' Tools", "Bedroll", "Pouch", "Pouch", "Traveler's Clothes"] + self.tool_preference
            character.gold += 16
        return character
