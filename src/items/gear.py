from src.items.items import Item


class Book(Item):
    def __init__(self, name="Book", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Gear"
        self.weight = 5
        self.value = 25


class HolySymbol(Item):
    def __init__(self, name="Holy Symbol", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Gear"
        self.weight = 1
        self.value = 5


class Parchment(Item):
    def __init__(self, name="Parchment", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Gear"
        self.weight = 0
        self.value = 0.1


class Pouch(Item):
    def __init__(self, name="Pouch", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Gear"
        self.weight = 1
        self.value = 0.5


class Mirror(Item):
    def __init__(self, name="Mirror", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Gear"
        self.weight = 0.5
        self.value = 5


class Perfume(Item):
    def __init__(self, name="Perfume", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Gear"
        self.weight = 0
        self.value = 5


class IronPot(Item):
    def __init__(self, name="Iron Pot", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Gear"
        self.weight = 10
        self.value = 2


class HoodedLantern(Item):
    def __init__(self, name="Hooded Lantern", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Gear"
        self.weight = 2
        self.value = 5


class Manacles(Item):
    def __init__(self, name="Manacles", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Gear"
        self.weight = 6
        self.value = 2


class Quiver(Item):
    def __init__(self, name="Quiver", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Gear"
        self.weight = 1
        self.value = 1


class Bedroll(Item):
    def __init__(self, name="Bedroll", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Gear"
        self.weight = 7
        self.value = 1


class Lamp(Item):
    def __init__(self, name="Lamp", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Gear"
        self.weight = 1
        self.value = 0.5


class OilFlask(Item):
    def __init__(self, name="Oil Flask", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Gear"
        self.weight = 1
        self.value = 0.1


class Tent(Item):
    def __init__(self, name="Tent", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Gear"
        self.weight = 20
        self.value = 2


class Rope(Item):
    def __init__(self, name="Rope", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Gear"
        self.weight = 10
        self.value = 1


class Arrows(Item):
    def __init__(self, name="Arrows", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Ammunition"
        self.weight = 0.05
        self.value = 0.05


class Bolts(Item):
    def __init__(self, name="Bolts", description="", **kwargs):
        super().__init__(name, description, **kwargs)
        self.type = "Ammunition"
        self.weight = 0.075
        self.value = 0.05
