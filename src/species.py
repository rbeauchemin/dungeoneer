from src.common import roll_dice
from src.spells import Spell, Light


class Species:
    def __init__(self):
        self.description = ""
        self.spells = []
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


class Goblin(Species):
    def __init__(self):
        super().__init__()
        self.description = "Goblins are small, green-skinned humanoids known for their cunning and mischievous nature. They are often found in tribes or clans, living in caves or forests. Goblins are quick and agile, making them adept at ambushes and hit-and-run tactics. They have a knack for scavenging and repurposing items they find, often creating makeshift weapons and armor. Despite their small size, goblins can be quite dangerous when encountered in groups. They are known for their sharp teeth and pointed ears, as well as their distinctive, high-pitched voices."
        self.creature_type = "Humanoid"
        self.size = "Small"
        self.speed = 30
        self.species = "Goblin"
        self.special_tags = []
        self.resistances = []
        self.vision = "Darkvision"
        self.full_rest_hours = 8
        self.special_abilities = [
            Spell(
                name="Nimble Escape",
                casting_time="Bonus Action",
                range_="Self",
                components=[],
                duration="Instantaneous",
                description="You can take the Disengage or Hide action as a bonus action on each of your turns.",
                cast=lambda char, targets: print(f"{char.name} uses Nimble Escape to Disengage or Hide as a bonus action.")
            )
        ]


class Aasimar(Species):
    def __init__(self, size="Medium"):
        super().__init__()
        self.description = "Aasimar are beings touched by the divine, often born of celestial heritage. They possess an innate connection to the forces of good and light, which manifests in their radiant appearance and benevolent nature. Aasimar are often driven by a strong sense of justice and a desire to protect the innocent. They are known for their healing abilities and their capacity to inspire hope in others. Aasimar typically have a striking appearance, with features that reflect their celestial lineage, such as glowing eyes or a subtle halo of light."
        self.creature_type = "Humanoid"
        self.target = None
        self.todo = []
        if size in ["Small", "Medium"]:
            self.size = size
        else:
            self.size = "Medium"
        self.spells = [Light(ability="Charisma", level=0)]
        self.resistances = ["Necrotic", "Radiant"]
        self.vision = "Darkvision"
        self.species = "Aasimar"
        self.special_tags = []
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
                cast=lambda char, targets: self.cast_healing_hands(char, targets)
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
                cast=lambda char, targets: self.cast_heavenly_wings(char, [char])
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
                cast=lambda char, targets: self.cast_inner_radiance(char, [char])
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
                cast=lambda char, targets: self.cast_necrotic_shroud(char, [char])
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

    def cast_heavenly_wings(self, char, targets):
        if char.level < 3:
            print("You must be at least level 3 to use Celestial Revelation abilities.")
            return
        targets[0].flying_speed = targets[0].speed + 0
        self.shared_celestial_revelation_tracker -= 1
        print(f"{targets[0].name} can now fly with a speed of {targets[0].flying_speed} feet.")

    def cast_inner_radiance(self, char, targets):
        if char.level < 3:
            print("You must be at least level 3 to use Celestial Revelation abilities.")
            return
        char.todo.append("Deal radiant damage to creatures within 10 feet at end of turn.")
        self.shared_celestial_revelation_tracker -= 1
        print(f"{targets[0].name} radiates light, dealing radiant damage to nearby creatures.")

    def cast_necrotic_shroud(self, char, targets):
        if char.level < 3:
            print("You must be at least level 3 to use Celestial Revelation abilities.")
            return
        char.todo.append("Creatures within 10 feet are frightened if they are not allies.")
        self.shared_celestial_revelation_tracker -= 1
        print(f"{targets[0].name} emanates a necrotic shroud, frightening nearby creatures.")

    def cast_healing_hands(self, char, targets):
        healing_amount = roll_dice(self.proficiency_bonus, 4)
        targets[0].current_hp = min(targets[0].max_hp, targets[0].current_hp + healing_amount)
        print(f"{char.name} heals {targets[0].name} for {healing_amount} hit points and is now at {targets[0].current_hp}/{targets[0].max_hp} HP.")


class Dragonborn(Species):
    def __init__(self, ancestry):
        super().__init__()
        self.todo = ["Select your draconic ancestry, which determines the damage type of your breath weapon and your resistance to that damage type."]
        self.description = "Dragonborn are proud, honorable warriors with draconic ancestry. They possess a strong sense of duty and a desire to prove themselves through acts of valor. Dragonborn are known for their strength, resilience, and their ability to breathe elemental energy. They often have a strong connection to their clan and value loyalty and camaraderie. Dragonborn typically have scales that reflect their draconic heritage, with colors ranging from metallic hues to vibrant shades associated with different types of dragons."
        self.creature_type = "Humanoid"
        self.size = "Medium"
        self.speed = 30
        self.species = "Dragonborn"
        self.special_tags = []
        self.resistances = []
        self.vision = "Darkvision"
        self.full_rest_hours = 8
        self.proficiency_bonus = 2
        self.breaths_left = self.proficiency_bonus + 0
        ancestries = {
            "Black": "Acid",
            "Blue": "Lightning",
            "Brass": "Fire",
            "Bronze": "Lightning",
            "Copper": "Acid",
            "Gold": "Fire",
            "Green": "Poison",
            "Red": "Fire",
            "Silver": "Cold",
            "White": "Cold"
        }
        if ancestry in ancestries.keys():
            self.ancestry = ancestry
            self.breath_weapon_damage_type = ancestries[ancestry]
            self.resistances = [self.breath_weapon_damage_type]
        else:
            print(f"Invalid ancestry provided. Please select a valid draconic ancestry from {list(ancestries.keys())}.")
        self.special_abilities = [
            Spell(
                name="Breath Weapon: Cone",
                casting_time="Attack Action",
                range_="15ft Cone",
                components=[],
                duration="Instantaneous",
                description="You can use your action to exhale destructive energy. Your draconic ancestry determines the size, shape, and damage type of the exhalation. When you use your breath weapon, each creature in the area of the exhalation must make a Dexterity saving throw (DC 8 + your Constitution modifier + your proficiency bonus)",
                ability="Constitution",
                save="Dexterity",
                cooldown="Long Rest",
                uses_left=self.breaths_left,
                cast=lambda char, targets: self.cast_breath_weapon(char, targets)
            ),
            Spell(
                name="Breath Weapon: Line",
                casting_time="Attack Action",
                range_="30ft Line",
                components=[],
                duration="Instantaneous",
                description="You can use your action to exhale destructive energy. Your draconic ancestry determines the size, shape, and damage type of the exhalation. When you use your breath weapon, each creature in the area of the exhalation must make a Dexterity saving throw (DC 8 + your Constitution modifier + your proficiency bonus)",
                ability="Constitution",
                save="Dexterity",
                cooldown="Long Rest",
                uses_left=self.breaths_left,
                cast=lambda char, targets: self.cast_breath_weapon(char, targets)
            ),
            Spell(
                name="Draconic Flight",
                casting_time="Bonus Action",
                range_="Self",
                components=[],
                duration="10 minutes",
                description="At level 5, you can use a bonus action to sprout spectral dragon wings from your back, granting you a flying speed equal to your walking speed for 10 minutes.",
                cooldown="Long Rest",
                uses_left=1,
                cast=lambda char, targets: self.cast_draconic_flight(char, [char])
            )
        ]

    def cast_breath_weapon(self, char, targets, type_="Cone"):
        if char.level < 5:
            number_of_dice = 1
        elif char.level < 11:
            number_of_dice = 2
        elif char.level < 17:
            number_of_dice = 3
        damage_amount = roll_dice(number_of_dice, 10)
        print(f"{char.name} uses Breath Weapon ({type_}) dealing {damage_amount} {self.breath_weapon_damage_type} in the area.")
        for target in targets:
            save, value = target.roll_save("Dexterity", beat=8 + char.get_ability_bonus("Constitution") + char.proficiency_bonus)
            if save:
                specific_damage = damage_amount // 2
                print(f"{target.name} succeeded on the saving throw and takes half damage ({specific_damage} instead of {damage_amount}).")
                target.current_hp = max(0, target.current_hp - (damage_amount // 2))
                if target.current_hp == 0:
                    print(f"{target.name} has been defeated.")
            else:
                print(f"{target.name} failed the saving throw and takes full damage ({damage_amount}).")
                target.current_hp = max(0, target.current_hp - damage_amount)
                if target.current_hp == 0:
                    print(f"{target.name} has been defeated.")

    def cast_draconic_flight(self, char, targets):
        if char.level < 5:
            print("You must be at least level 5 to use Draconic Flight.")
            return
        targets[0].flying_speed = targets[0].speed + 0
        print(f"{targets[0].name} can now fly with a speed of {targets[0].flying_speed} feet.")

    def rest(self, long=False):
        if long:
            print("Resting and restoring breath weapon uses...")
            self.breaths_left = self.proficiency_bonus + 0
            for ability in self.special_abilities:
                if ability.name.startswith("Breath Weapon"):
                    ability.uses_left = self.breaths_left
                elif ability.cooldown == "Long Rest":
                    ability.uses_left = 1


if __name__ == "__main__":
    aasimar = Aasimar()
    print(aasimar.description)
