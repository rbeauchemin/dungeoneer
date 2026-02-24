from src.items.items import Item


class Gear(Item):
    def __init__(self, name="Gear", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Gear"
        self.weight = 0
        self.value = 0


class Acid(Gear):
    def __init__(self, name="Acid", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 1
        self.value = 25


class AlchemistsFire(Gear):
    def __init__(self, name="Alchemist's Fire", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 1
        self.value = 50


class Antitoxin(Gear):
    def __init__(self, name="Antitoxin", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 0
        self.value = 50


class ArcaneFocus(Gear):
    def __init__(self, name="Arcane Focus", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        # NOTE: This will vary based on the type of focus and material. This is styled after a crystal.
        self.weight = 2
        self.value = 10


class Arrows(Gear):
    def __init__(self, name="Arrows", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Ammunition"
        self.weight = 0.05
        self.value = 0.05


class Backpack(Gear):
    def __init__(self, name="Backpack", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 5
        self.value = 2


class BallBearings(Gear):
    def __init__(self, name="Ball Bearings", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 2
        self.value = 1


class Barrel(Gear):
    def __init__(self, name="Barrel", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 70
        self.value = 2


class Basket(Gear):
    def __init__(self, name="Basket", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 2
        self.value = 0.4


class Bedroll(Gear):
    def __init__(self, name="Bedroll", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 7
        self.value = 1


class Bell(Gear):
    def __init__(self, name="Bell", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 0
        self.value = 1


class Blanket(Gear):
    def __init__(self, name="Blanket", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 3
        self.value = 0.5


class BlockandTackle(Gear):
    def __init__(self, name="Block and Tackle", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 5
        self.value = 1


class Bolts(Gear):
    def __init__(self, name="Bolts", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Ammunition"
        self.weight = 0.075
        self.value = 0.05


class Book(Gear):
    def __init__(self, name="Book", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 5
        self.value = 25


class GlassBottle(Gear):
    def __init__(self, name="Glass Bottle", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 2
        self.value = 2


class Bucket(Gear):
    def __init__(self, name="Bucket", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 2
        self.value = 0.05


class BullseyeLantern(Gear):
    def __init__(self, name="Bullseye Lantern", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 2
        self.value = 10


class BurglarsPack(Gear):
    def __init__(self, name="Burglar's Pack", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 42
        self.value = 16


class Candle(Gear):
    def __init__(self, name="Candle", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 0
        self.value = 0.01


class CrossbowBoltCase(Gear):
    def __init__(self, name="Crossbow Bolt Case", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 1
        self.value = 1


class MaporScrollCase(Gear):
    def __init__(self, name="Map or Scroll Case", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 1
        self.value = 1


class Chain(Gear):
    def __init__(self, name="Chain", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 10
        self.value = 5


class Chest(Gear):
    def __init__(self, name="Chest", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 25
        self.value = 5


class ClimbersKit(Gear):
    def __init__(self, name="Climber's Kit", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 12
        self.value = 25


class ComponentPouch(Gear):
    def __init__(self, name="Component Pouch", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 2
        self.value = 25


# NOTE: Costume in armor.py and Crowbar in tools.py currently. Maybe move back to here?


class DiplomatsPack(Gear):
    def __init__(self, name="Diplomat's Pack", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 39
        self.value = 39


class DruidicFocus(Gear):
    def __init__(self, name="Druidic Focus", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 4
        self.value = 5


class DungeoneersPack(Gear):
    def __init__(self, name="Dungeoneer's Pack", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 55
        self.value = 12


class EntertainersPack(Gear):
    def __init__(self, name="Entertainer's Pack", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 58.5
        self.value = 40


class ExplorersPack(Gear):
    def __init__(self, name="Explorer's Pack", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 55
        self.value = 10


class FirearmBullets(Gear):
    def __init__(self, name="Firearm Bullets", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Ammunition"
        self.weight = 0.2
        self.value = 0.3


class Flask(Gear):
    def __init__(self, name="Flask", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 1
        self.value = 0.02


class GrapplingHook(Gear):
    def __init__(self, name="Grappling Hook", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 4
        self.value = 2


class HolySymbol(Gear):
    def __init__(self, name="Holy Symbol", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 1
        self.value = 5


class HolyWater(Gear):
    def __init__(self, name="Holy Water", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 1
        self.value = 25


class HoodedLantern(Gear):
    def __init__(self, name="Hooded Lantern", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 2
        self.value = 5


class HuntingTrap(Gear):
    def __init__(self, name="Hunting Trap", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 25
        self.value = 5


class Ink(Gear):
    def __init__(self, name="Ink", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 0
        self.value = 10


class InkPen(Gear):
    def __init__(self, name="Ink Pen", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 0
        self.value = 0.02


class IronPot(Gear):
    def __init__(self, name="Iron Pot", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 10
        self.value = 2


class IronSpikes(Gear):
    def __init__(self, name="Iron Spikes", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 5
        self.value = 1


class Jug(Gear):
    def __init__(self, name="Jug", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 4
        self.value = 0.02


class Ladder(Gear):
    def __init__(self, name="Ladder", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 25
        self.value = 0.1


class Lamp(Gear):
    def __init__(self, name="Lamp", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 1
        self.value = 0.5


class Lock(Gear):
    def __init__(self, name="Lock", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 1
        self.value = 10


class MagnifyingGlass(Gear):
    def __init__(self, name="Magnifying Glass", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 0
        self.value = 100


class Manacles(Gear):
    def __init__(self, name="Manacles", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 6
        self.value = 2


class Map(Gear):
    def __init__(self, name="Map", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 0
        self.value = 1


class Mirror(Gear):
    def __init__(self, name="Mirror", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 0.5
        self.value = 5


class Needles(Gear):
    def __init__(self, name="Needles", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Ammunition"
        self.weight = 0.02
        self.value = 0.02


class Net(Gear):
    def __init__(self, name="Net", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 3
        self.value = 1


class Oil(Gear):
    def __init__(self, name="Oil", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 1
        self.value = 0.1


class OilFlask(Gear):
    def __init__(self, name="Oil Flask", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        # TODO: This should be refactored to allow flask to be filled with different things
        self.weight = 2
        self.value = 0.12


class Paper(Gear):
    def __init__(self, name="Paper", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 0
        self.value = 0.2


class Parchment(Gear):
    def __init__(self, name="Parchment", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 0
        self.value = 0.1


class Perfume(Gear):
    def __init__(self, name="Perfume", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 0
        self.value = 5


class BasicPoison(Gear):
    def __init__(self, name="Basic Poison", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 0
        self.value = 100


class Pole(Gear):
    def __init__(self, name="Pole", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 7
        self.value = 0.05


class PortableRam(Gear):
    def __init__(self, name="Portable Ram", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 35
        self.value = 4


class PotionOfHealing(Gear):
    def __init__(self, name="Potion of Healing", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 0.5
        self.value = 50


class Pouch(Gear):
    def __init__(self, name="Pouch", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 1
        self.value = 0.5


class Quiver(Gear):
    def __init__(self, name="Quiver", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 1
        self.value = 1


class Rations(Gear):
    def __init__(self, name="Quiver", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 2
        self.value = 0.5


class Rope(Gear):
    def __init__(self, name="Rope", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 5
        self.value = 1


class Sack(Gear):
    def __init__(self, name="Sack", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 0.5
        self.value = 0.01


class ScholarsPack(Gear):
    def __init__(self, name="Scholar's Pack", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 22
        self.value = 40


class SignalWhistle(Gear):
    def __init__(self, name="Signal Whistle", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 0
        self.value = 0.05


class SlingBullets(Gear):
    def __init__(self, name="Sling Bullets", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Ammunition"
        self.weight = 0.075
        self.value = 0.002


class SpellScroll(Gear):
    def __init__(self, name="Signal Whistle", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        level = kwargs.get("level", 0)
        self.weight = 0
        self.value = 30 + 20 * level


class Spyglass(Gear):
    def __init__(self, name="Spyglass", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 1
        self.value = 1000


class String(Gear):
    def __init__(self, name="String", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 0
        self.value = 0.1


class Tent(Gear):
    def __init__(self, name="Tent", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 20
        self.value = 2


class Tinderbox(Gear):
    def __init__(self, name="Tinderbox", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 1
        self.value = 0.5


class Torch(Gear):
    def __init__(self, name="Torch", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 1
        self.value = 0.01


class Vial(Gear):
    def __init__(self, name="Vial", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 0
        self.value = 1


class Waterskin(Gear):
    def __init__(self, name="Waterskin", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.weight = 5
        self.value = 0.2
