from src.creatures import Character
from src.items.items import Item


class Tool(Item):
    def __init__(self, name="Tool", description=""):
        super().__init__()
        self.type = "Tool"
        self.name = name
        self.description = description
        # The ability used with this tool
        self.ability = None
        # What you can do with the tool when you take the Utilize action
        self.utilize = None
        # The ability check DC for utilizing this tool
        self.utilize_dc = 10
        # What you can craft with this tool
        self.craft = []

    def on_equip(self, character: Character):
        return self

    def on_unequip(self, character: Character):
        return self


class AlchemistsSupplies(Tool):
    def __init__(self, name="Alchemist's Supplies", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Intelligence"
        self.utilize = "Identify a substance (DC 15), or start a fire (DC 15)"
        self.utilize_dc = 15
        self.craft = ["Acid", "Alchemist's Fire", "Component Pouch", "Oil", "Paper", "Perfume"]
        self.weight = 8
        self.value = 50


class BrewersSupplies(Tool):
    def __init__(self, name="Brewer's Supplies", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Intelligence"
        self.utilize = "Detect poisoned drink (DC 15), or identify alcohol (DC 10)"
        self.utilize_dc = 15
        self.craft = ["Antitoxin"]
        self.weight = 9
        self.value = 20


class CalligraphersSupplies(Tool):
    def __init__(self, name="Calligrapher's Supplies", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Dexterity"
        self.utilize = "Write text with impressive flourishes that guard against forgery (DC 15)"
        self.utilize_dc = 15
        self.craft = ["Ink", "Spell Scroll"]
        self.weight = 5
        self.value = 10

class CarpentersTools(Tool):
    def __init__(self, name="Carpenter's Tools", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Strength"
        self.utilize = "Open a door or container (DC 15)"
        self.utilize_dc = 15
        self.craft = ["Club", "Greatclub", "Quarterstaff", "Barrel", "Chest", "Ladder", "Pole", "Portable Ram", "Torch"]
        self.weight = 6
        self.value = 8


class CartographersTools(Tool):
    def __init__(self, name="Cartographer's Tools", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Wisdom"
        self.utilize = "Draft a map of a small area (DC 15)"
        self.utilize_dc = 15
        self.craft = ["Map"]
        self.weight = 6
        self.value = 15


class CobblersTools(Tool):
    def __init__(self, name="Cobbler's Tools", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Dexterity"
        self.utilize = "Modify footwear to give Advantage on the wearer's next Dexterity (Acrobatics) check (DC 10)"
        self.utilize_dc = 10
        self.craft = ["Climber's Kit"]
        self.weight = 5
        self.value = 5


class CooksUtensils(Tool):
    def __init__(self, name="Cook's Utensils", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Wisdom"
        self.utilize = "Improve food's flavor (DC 10), or detect spoiled or poisoned food (DC 15)"
        self.utilize_dc = 15
        self.craft = ["Rations"]
        self.weight = 8
        self.value = 1


class GlassblowersTools(Tool):
    def __init__(self, name="Glassblower's Tools", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Intelligence"
        self.utilize = "Discern what a glass object held in the past 24 hours (DC 15)"
        self.utilize_dc = 15
        self.craft = ["Glass Bottle", "Magnifying Glass", "Spyglass", "Vial"]
        self.weight = 5
        self.value = 30


class JewelersTools(Tool):
    def __init__(self, name="Jeweler's Tools", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Intelligence"
        self.utilize = "Discern a gem's value (DC 15)"
        self.utilize_dc = 15
        self.craft = ["Arcane Focus", "Holy Symbol"]
        self.weight = 2
        self.value = 25


class LeatherworkersTools(Tool):
    def __init__(self, name="Leatherworker's Tools", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Dexterity"
        self.utilize = "Add a design to a leather item (DC 10)"
        self.utilize_dc = 10
        self.craft = ["Sling", "Whip", "Hide Armor", "Leather Armor", "Studded Leather Armor", "Backpack", "Crossbow Bolt Case", "Map or Scroll Case", "Parchment", "Pouch", "Quiver", "Waterskin"]
        self.weight = 5
        self.value = 5


class MasonsTools(Tool):
    def __init__(self, name="Mason's Tools", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Strength"
        self.utilize = "Chisel a symbol or hole in a stone block and tackle (DC 10)"
        self.utilize_dc = 10
        self.craft = ["Block", "Tackle"]
        self.weight = 8
        self.value = 10


class PaintersSupplies(Tool):
    def __init__(self, name="Painter's Supplies", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Wisdom"
        self.utilize = "Paint a recognizable image of something you've seen (DC 10)"
        self.utilize_dc = 10
        self.craft = ["Druidic Focus", "Holy Symbol"]
        self.weight = 5
        self.value = 10


class PottersTools(Tool):
    def __init__(self, name="Potter's Tools", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Intelligence"
        self.utilize = "Discern what a ceramic object held in the past 24 hours (DC 15)"
        self.utilize_dc = 15
        self.craft = ["Jug", "Lamp"]
        self.weight = 3
        self.value = 10


class SmithsTools(Tool):
    def __init__(self, name="Smith's Tools", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Strength"
        self.utilize = "Pry open a door or container (DC 20)"
        self.utilize_dc = 20
        self.craft = ["Any Melee weapon (except Club, Greatclub, Quarterstaff, and Whip)", "Medium armor (except Hide)", "Heavy armor", "Ball Bearings", "Bucket", "Caltrop", "Chain", "Crowbar", "Firearm Bullets", "Grappling Hook", "Iron Pot", "Iron Spikes", "Sling Bullets"]
        self.weight = 8
        self.value = 20


class TinkersTools(Tool):
    def __init__(self, name="Tinker's Tools", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Dexterity"
        self.utilize = "Assemble a Tiny item composed of scrap, which falls apart in 1 minute (DC 20)"
        self.utilize_dc = 20
        self.craft = ["Musket", "Pistol", "Bell", "Bullseye Lantern", "Flask", "Hooded Lantern", "Hunting Trap", "Lock", "Manacles", "Mirror", "Shovel", "Signal Whistle", "Tinderbox"]
        self.weight = 10
        self.value = 50


class WeaversTools(Tool):
    def __init__(self, name="Weaver's Tools", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Dexterity"
        self.utilize = "Mend a tear in clothing (DC 10), or sew a Tiny design (DC 10)"
        self.utilize_dc = 10
        self.craft = ["Padded Armor", "Basket", "Bedroll", "Blanket", "Fine Clothes", "Net", "Robe", "Rope", "Sack", "String", "Tent", "Traveler's Clothes"]
        self.weight = 5
        self.value = 1


class WoodcarversTools(Tool):
    def __init__(self, name="Woodcarver's Tools", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Dexterity"
        self.utilize = "Carve a pattern in wood (DC 10)"
        self.utilize_dc = 10
        self.craft = ["Club", "Greatclub", "Quarterstaff", "Ranged weapons (except Pistol, Musket, and Sling)", "Arcane Focus", "Arrows", "Bolts", "Druidic Focus", "Ink Pen", "Needles"]
        self.weight = 5
        self.value = 1


class DisguiseKit(Tool):
    def __init__(self, name="Disguise Kit", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Charisma"
        self.utilize = "Apply makeup (DC 10)"
        self.utilize_dc = 10
        self.craft = ["Costume"]
        self.weight = 3
        self.value = 25


class ForgeryKit(Tool):
    def __init__(self, name="Forgery Kit", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Dexterity"
        self.utilize = "Mimic 10 or fewer words of someone else's handwriting (DC 15), or duplicate a wax seal (DC 20)"
        self.utilize_dc = 20
        self.craft = []
        self.weight = 5
        self.value = 15


class GamingSet(Tool):
    def __init__(self, name="Gaming Set", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Wisdom"
        self.utilize = "Discern whether someone is cheating (DC 10), or win the game (DC 20)"
        self.utilize_dc = 10
        self.craft = []
        self.weight = 0
        self.value = 0


class GamingSetDice(GamingSet):
    def __init__(self, name="Gaming Set (Dice)", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.value = 0.1


class GamingSetDragonchess(GamingSet):
    def __init__(self, name="Gaming Set (Dragonchess)", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.value = 1


class GamingSetPlayingCards(GamingSet):
    def __init__(self, name="Gaming Set (Playing Cards)", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.value = 0.5


class GamingSetThreeDragonAnte(GamingSet):
    def __init__(self, name="Gaming Set (Three-Dragon Ante)", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.value = 1


class HerbalismKit(Tool):
    def __init__(self, name="Herbalism Kit", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Intelligence"
        self.utilize = "Identify a plant (DC 10)"
        self.utilize_dc = 10
        self.craft = ["Antitoxin", "Candle", "Healer's Kit", "Potion of Healing"]
        self.weight = 3
        self.value = 5


class MusicalInstrument(Tool):
    def __init__(self, name="Musical Instrument", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Charisma"
        self.utilize = "Play a known tune (DC 10), or improvise a song (DC 15)"
        self.utilize_dc = 10
        self.craft = []
        self.weight = 0
        self.value = 0


class BagpipesInstrument(MusicalInstrument):
    def __init__(self, name="Bagpipes", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.weight = 6
        self.value = 30


class DrumInstrument(MusicalInstrument):
    def __init__(self, name="Drum", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.weight = 3
        self.value = 6


class DulcimerInstrument(MusicalInstrument):
    def __init__(self, name="Dulcimer", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.weight = 10
        self.value = 25


class FluteInstrument(MusicalInstrument):
    def __init__(self, name="Flute", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.weight = 1
        self.value = 2


class HornInstrument(MusicalInstrument):
    def __init__(self, name="Horn", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.weight = 2
        self.value = 3


class LuteInstrument(MusicalInstrument):
    def __init__(self, name="Lute", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.weight = 2
        self.value = 35


class LyreInstrument(MusicalInstrument):
    def __init__(self, name="Lyre", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.weight = 2
        self.value = 30


class PanFluteInstrument(MusicalInstrument):
    def __init__(self, name="Pan Flute", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.weight = 2
        self.value = 12


class ShawmInstrument(MusicalInstrument):
    def __init__(self, name="Shawm", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.weight = 1
        self.value = 2


class ViolInstrument(MusicalInstrument):
    def __init__(self, name="Viol", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.weight = 1
        self.value = 30


class NavigatorsTools(Tool):
    def __init__(self, name="Navigator's Tools", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Wisdom"
        self.utilize = "Plot a course (DC 10), or determine position by stargazing (DC 15)"
        self.utilize_dc = 10
        self.craft = []
        self.weight = 2
        self.value = 25


class PoisonersKit(Tool):
    def __init__(self, name="Poisoner's Kit", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Intelligence"
        self.utilize = "Detect a poisoned object (DC 10)"
        self.utilize_dc = 10
        self.craft = ["Basic Poison"]
        self.weight = 2
        self.value = 50


class ThievesTools(Tool):
    def __init__(self, name="Thieves' Tools", description=""):
        super().__init__()
        self.name = name
        self.description = description
        self.ability = "Dexterity"
        self.utilize = "Pick a lock (DC 15), or disarm a trap (DC 15)"
        self.utilize_dc = 15
        self.craft = []
        self.weight = 1
        self.value = 25
