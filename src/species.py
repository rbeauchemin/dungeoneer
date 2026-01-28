from src.common import roll_dice
from src.spells import Spell, Light


class Species:
    def __init__(self):
        self.description = ""
        self.spells = {}
        self.special_abilities = {}
        self.resistances = []
        self.todo = []
        self.size = "Medium"
        self.speed = 30
        self.swimming_speed = 15
        self.flying_speed = 0

    def rest(self, long=False):
        print("Resting with no special feats...")
        pass


class Aasimar(Species):
    def __init__(self):
        super().__init__()
        self.description = "Aasimar are beings touched by the divine, often born of celestial heritage. They possess an innate connection to the forces of good and light, which manifests in their radiant appearance and benevolent nature. Aasimar are often driven by a strong sense of justice and a desire to protect the innocent. They are known for their healing abilities and their capacity to inspire hope in others. Aasimar typically have a striking appearance, with features that reflect their celestial lineage, such as glowing eyes or a subtle halo of light."
        self.creature_type = "Humanoid"
        self.target = None
        self.todo = [lambda x: setattr(self, 'size', input("Select your size from the following options: Small, Medium.").strip().title())]
        self.spells = [Light(ability="Charisma", level=0)]
        self.resistances = ["Necrotic", "Radiant"]
        self.vision = "Darkvision"
        self.species = "Aasimar"
        self.shared_celestial_revelation_tracker = 1
        self.full_rest_hours = 8
        self.special_abilities = [
            Spell(
                name="Healing Hands",
                casting_time="Action",
                range_="Touch",
                components=[],
                duration="Instantaneous",
                description="As an action, you can touch a creature and heal it for a number of d4s equal to your proficiency bonus. Once you use this trait, you can't use it again until you finish a long rest.",
                cooldown="Long Rest",
                uses_left=1,
                cast=lambda char, target: self.cast_healing_hands(char, target)
            ),
            Spell(
                name="Celestial Revelation: Heavenly Wings",
                casting_time="Bonus Action",
                range_="Self",
                components=[],
                duration="1 minute",
                description="Two spectral wings sprout from your back temporarily. Until the transformation ends, you have a Fly Speed equal to your speed.",
                cooldown="Long Rest",
                uses_left=self.shared_celestial_revelation_tracker,
                cast=lambda char, target: self.cast_heavenly_wings(char, char)
            ),
            Spell(
                name="Celestial Revelation: Inner Radiance",
                casting_time="Bonus Action",
                range_="Self",
                components=[],
                duration="1 minute",
                description="Searing light temporarily radiates from your eyes and mouth. For the duration, you shed Bright Light in a 10-foot radius and Dim Light for an additional 10 feet, and at the end of each of your turns, each creature of your choice within 10 feet of you takes radiant damage equal to your Proficiency Bonus.",
                cooldown="Long Rest",
                uses_left=self.shared_celestial_revelation_tracker,
                cast=lambda char, target: self.cast_inner_radiance(char, char)
            ),
            Spell(
                name="Celestial Revelation: Necrotic Shroud",
                casting_time="Bonus Action",
                range_="Self",
                components=[],
                duration="1 minute",
                description="Your eyes briefly become pools of darkness, and flightless wings sprout from your back temporarily. Creatures other than your allies within 10 feet of you must succeed on a Charisma saving throw or be frightened of you until the end of your next turn.",
                cooldown="Long Rest",
                uses_left=self.shared_celestial_revelation_tracker,
                cast=lambda char, target: self.cast_necrotic_shroud(char, char)
            )
        ]

    def rest(self, long=False):
        if long:
            print("Resting and restoring celestial features...")
            self.shared_celestial_revelation_tracker = 1
            for ability in self.special_abilities:
                if ability.name.startswith("Celestial Revelation"):
                    ability.uses_left = self.shared_celestial_revelation_tracker
                elif ability.cooldown == "Long Rest":
                    ability.uses_left = 1

    def cast_heavenly_wings(self, char, target):
        if char.level < 3:
            print("You must be at least level 3 to use Celestial Revelation abilities.")
            return
        target.flying_speed = target.speed + 0
        self.shared_celestial_revelation_tracker -= 1
        print(f"{target.name} can now fly with a speed of {target.flying_speed} feet.")

    def cast_inner_radiance(self, char, target):
        if char.level < 3:
            print("You must be at least level 3 to use Celestial Revelation abilities.")
            return
        char.todo.append("Deal radiant damage to creatures within 10 feet at end of turn.")
        self.shared_celestial_revelation_tracker -= 1
        print(f"{target.name} radiates light, dealing radiant damage to nearby creatures.")

    def cast_necrotic_shroud(self, char, target):
        if char.level < 3:
            print("You must be at least level 3 to use Celestial Revelation abilities.")
            return
        char.todo.append("Creatures within 10 feet are frightened if they are not allies.")
        self.shared_celestial_revelation_tracker -= 1
        print(f"{target.name} emanates a necrotic shroud, frightening nearby creatures.")

    def cast_healing_hands(self, char, target):
        healing_amount = roll_dice(self.proficiency_bonus, 4)
        target.current_hp = min(target.max_hp, target.current_hp + healing_amount)
        print(f"{char.name} heals {target.name} for {healing_amount} hit points and is now at {target.current_hp}/{target.max_hp} HP.")


class Dragonborn(Species):
    def __init__(self):
        super().__init__()
        self.description = "Dragonborn are proud, honorable warriors with draconic ancestry. They possess a strong sense of duty and a desire to prove themselves through acts of valor. Dragonborn are known for their physical strength, resilience, and their ability to breathe elemental energy. They often have a strong connection to their clan and value loyalty and camaraderie. Dragonborn typically have scales that reflect their draconic heritage, with colors ranging from metallic hues to vibrant shades associated with different types of dragons."
        self.creature_type = "Humanoid"
        self.size = "Medium"
        self.speed = 30
        self.todo = ["Select your draconic ancestry, which determines the damage type of your breath weapon and your resistance to that damage type."]
        self.species = "Dragonborn"
        self.resistances = []
        self.vision = "Darkvision"
        self.special_abilities = {
            "Draconic Ancestry": "You have a specific type of dragon as your ancestor, which determines the damage type of your breath weapon and your resistance to that damage type.",
            "Breath Weapon": "You can use your action to exhale destructive energy. Your draconic ancestry determines the size, shape, and damage type of the exhalation."
        }


if __name__ == "__main__":
    aasimar = Aasimar()
    print(aasimar.description)
