from typing import Literal
from src.common import roll_dice
from src.spells import Spell, Light


class Species:
    def __init__(self):
        self.description = ""
        self.spells = []
        self.special_abilities = {}
        self.resistances = []
        self.advantages = {}
        self.vision = "Standard"
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
        self.species = "Goblin"
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
    def __init__(self, size: Literal["Small", "Medium"] = "Medium"):
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
        self.vision = "Darkvision of 60ft"
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
    def __init__(self, ancestry: Literal["Black", "Blue", "Brass", "Bronze", "Copper", "Gold", "Green", "Red", "Silver", "White"]):
        super().__init__()
        self.todo = ["Select your draconic ancestry, which determines the damage type of your breath weapon and your resistance to that damage type."]
        self.description = "Dragonborn are proud, honorable warriors with draconic ancestry. They possess a strong sense of duty and a desire to prove themselves through acts of valor. Dragonborn are known for their strength, resilience, and their ability to breathe elemental energy. They often have a strong connection to their clan and value loyalty and camaraderie. Dragonborn typically have scales that reflect their draconic heritage, with colors ranging from metallic hues to vibrant shades associated with different types of dragons."
        self.creature_type = "Humanoid"
        self.size = "Medium"
        self.speed = 30
        self.species = "Dragonborn"
        self.resistances = []
        self.vision = "Darkvision of 60ft"
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


class Dwarf(Species):
    def __init__(self):
        super().__init__()
        self.description = "Dwarves are stout and sturdy humanoids known for their resilience, craftsmanship, and strong sense of community. They typically stand between 4 and 5 feet tall but are broad-shouldered and muscular. Dwarves have a deep connection to the earth, often dwelling in mountainous regions or underground cities. They are skilled miners and blacksmiths, renowned for their ability to create finely crafted weapons, armor, and jewelry. Dwarves value tradition, honor, and loyalty, often forming tight-knit clans or guilds. They have a reputation for being fierce warriors, especially when defending their homes or allies."
        self.creature_type = "Humanoid"
        self.size = "Medium"
        self.speed = 25
        self.species = "Dwarf"
        self.resistances = ["Poison"]
        self.advantages = {"Saving Throws": ["Poison"]}
        self.vision = "Darkvision of 120ft"
        self.full_rest_hours = 8
        self.special_abilities = [
            Spell(
                name="Stonecunning",
                casting_time="Passive",
                range_="Self",
                components=[],
                duration="Permanent",
                description="Whenever you make an Intelligence (History) check related to the origin of stonework, you are considered proficient in the History skill and add double your proficiency bonus to the check.",
                cast=lambda char, targets: print(f"{char.name} uses Stonecunning to gain expertise in History checks related to stonework.")
            )
        ]


class Elf(Species):
    def __init__(self, lineage: Literal["High", "Wood", "Drow"] = "Wood", extra_proficiency: Literal["Perception", "Insight", "Survival"] = "Perception"):
        super().__init__()
        self.todo = []
        self.description = "Elves are graceful and agile humanoids known for their keen senses, longevity, and deep connection to nature and magic. They typically stand between 5 and 6 feet tall, with slender builds and pointed ears. Elves have a natural affinity for the arcane arts and are often skilled spellcasters. They are known for their exceptional dexterity and keen eyesight, making them adept archers and scouts. Elves value beauty, art, and knowledge, often living in harmony with the natural world. High elves are known for their magical prowess, wood elves for their stealth and connection to the forest, and dark elves (drow) for their subterranean societies and unique abilities."
        self.creature_type = "Humanoid"
        self.size = "Medium"
        if lineage == "Wood":
            self.speed = 35
        else:
            self.speed = 30
        self.species = "Elf"
        self.lineage = lineage
        self.extra_proficiency = extra_proficiency
        self.resistances = []
        self.advantages = {
            "Saving Throws": ["Charm"]
        }
        if lineage == "Drow":
            self.vision = "Darkvision of 120ft"
        else:
            self.vision = "Darkvision of 60ft"
        self.full_rest_hours = 4
        self.vision = "Darkvision of 60ft"
        self.full_rest_hours = 8
        # TODO: Add lineage spells at 1, 3, 5.
        # Drow gets dancing lights, faerie fire, and darkness.
        # High gets Prestidigitation and can replace with different wizard cantrips every long rest, detect magic, misty step.
        # Wood gets druidcraft, longstrider, pass without trace.
        if lineage == "High":
            self.special_abilities = [
                Spell(
                    name="Fey Ancestry",
                    casting_time="Passive",
                    range_="Self",
                    components=[],
                    duration="Permanent",
                    description="You have advantage on saving throws against being charmed, and magic can't put you to sleep.",
                    cast=lambda char, targets: print(f"{char.name} uses Fey Ancestry to resist charm and sleep effects.")
                )
            ]


# TODO: Implement other species below. I used auto-generation for these, so they are not accurate yet
class Gnome(Species):
    def __init__(self):
        super().__init__()
        self.description = "Gnomes are small, intelligent humanoids known for their curiosity, inventiveness, and affinity for magic. They typically stand between 3 and 4 feet tall and have a keen intellect that drives them to explore the world around them. Gnomes are often skilled tinkerers and inventors, creating intricate devices and gadgets. They have a natural talent for illusion magic and are known for their playful and mischievous nature. Gnomes value knowledge, creativity, and community, often forming close-knit societies where they can share their discoveries and inventions."
        self.creature_type = "Humanoid"
        self.size = "Small"
        self.speed = 25
        self.species = "Gnome"
        self.resistances = []
        self.vision = "Darkvision of 60ft"
        self.full_rest_hours = 8
        self.special_abilities = [
            Spell(
                name="Gnome Cunning",
                casting_time="Passive",
                range_="Self",
                components=[],
                duration="Permanent",
                description="You have advantage on all Intelligence, Wisdom, and Charisma saving throws against magic.",
                cast=lambda char, targets: print(f"{char.name} uses Gnome Cunning to resist magical effects.")
            )
        ]


class Goliath(Species):
    def __init__(self):
        super().__init__()
        self.description = "Goliaths are towering humanoids known for their immense strength, endurance, and competitive nature. They typically stand between 7 and 8 feet tall and have muscular builds covered in stone-like skin with distinctive markings. Goliaths hail from mountainous regions, where they have adapted to harsh environments and rugged terrain. They are natural athletes, excelling in physical challenges and feats of strength. Goliaths value self-improvement, honor, and camaraderie, often engaging in friendly competitions to test their abilities. Despite their imposing appearance, goliaths are known for their sense of humor and strong community bonds."
        self.creature_type = "Humanoid"
        self.size = "Medium"
        self.speed = 30
        self.species = "Goliath"
        self.resistances = []
        self.vision = "Darkvision of 60ft"
        self.full_rest_hours = 8
        self.special_abilities = [
            Spell(
                name="Stone's Endurance",
                casting_time="Reaction",
                range_="Self",
                components=[],
                duration="Instantaneous",
                description="You can use your reaction to reduce damage dealt to you by 1d12 + your Constitution modifier. Once you use this trait, you can't use it again until you finish a short or long rest.",
                cast=lambda char, targets: print(f"{char.name} uses Stone's Endurance to reduce incoming damage.")
            )
        ]


class Halfling(Species):
    def __init__(self, subrace: Literal["Lightfoot", "Stout"] = "Lightfoot"):
        super().__init__()
        self.description = "Halflings are small, nimble humanoids known for their cheerful disposition, resourcefulness, and strong sense of community. They typically stand around 3 feet tall and have a slender build. Halflings are known for their luck and ability to avoid danger, often finding themselves in fortunate situations. They value comfort, friendship, and simple pleasures, often living in close-knit villages or communities. Halflings are skilled at stealth and are adept at moving quietly through their surroundings. They have a natural curiosity and love for adventure, often embarking on journeys to explore the wider world."
        self.creature_type = "Humanoid"
        self.size = "Small"
        self.speed = 25
        self.subrace = subrace
        self.species = "Halfling"
        self.resistances = []
        self.advantages = {
            "Saving Throws": ["Fear"]
        }
        self.vision = "Standard"
        self.full_rest_hours = 8
        self.special_abilities = [
            Spell(
                name="Lucky",
                casting_time="Passive",
                range_="Self",
                components=[],
                duration="Permanent",
                description="When you roll a 1 on an attack roll, ability check, or saving throw, you can reroll the die and must use the new roll.",
                cast=lambda char, targets: print(f"{char.name} uses Lucky to reroll a 1 on a d20 roll.")
            )
        ]


class Human(Species):
    def __init__(self):
        super().__init__()
        self.description = "Humans are the most adaptable and ambitious of the common races."
        self.creature_type = "Humanoid"
        self.size = "Medium"
        self.speed = 30
        self.species = "Human"
        self.resistances = []
        self.vision = "Standard"
        self.full_rest_hours = 8


class Orc(Species):
    def __init__(self):
        super().__init__()
        self.description = "Orcs are brutish and aggressive humanoids known for their strength, ferocity, and tribal societies. They typically stand between 6 and 7 feet tall and have muscular builds with greenish or grayish skin tones. Orcs are often depicted as warriors and raiders, valuing strength and combat prowess above all else. They live in harsh environments, such as wastelands or mountains, where they have adapted to survive through sheer toughness and resilience. Orcs have a strong sense of community within their tribes, often engaging in rituals and traditions that celebrate their martial culture."
        self.creature_type = "Humanoid"
        self.size = "Medium"
        self.speed = 30
        self.species = "Orc"
        self.resistances = []
        self.advantages = {
            "Saving Throws": ["Intimidation"]
        }
        self.vision = "Darkvision of 60ft"
        self.full_rest_hours = 8
        self.special_abilities = [
            Spell(
                name="Relentless Endurance",
                casting_time="Passive",
                range_="Self",
                components=[],
                duration="Instantaneous",
                description="When you are reduced to 0 hit points but not killed outright, you can drop to 1 hit point instead. You can't use this feature again until you finish a long rest.",
                cast=lambda char, targets: print(f"{char.name} uses Relentless Endurance to stay standing when reduced to 0 HP.")
            )
        ]


class Tiefling(Species):
    def __init__(self):
        super().__init__()
        self.description = "Tieflings are humanoids with infernal heritage, often characterized by their distinctive horns, tails, and other fiendish features. They typically stand between 5 and 6 feet tall and have a variety of skin tones, ranging from deep reds and purples to more human-like shades. Tieflings are known for their cunning, charisma, and resilience, often navigating the world with a mix of charm and suspicion due to their fiendish ancestry. They possess innate magical abilities, often related to fire and darkness, which they can use to their advantage. Tieflings value individuality and self-reliance, frequently forging their own paths in life despite the prejudices they may face from others."
        self.creature_type = "Humanoid"
        self.size = "Medium"
        self.speed = 30
        self.species = "Tiefling"
        self.resistances = ["Fire"]
        self.vision = "Darkvision of 60ft"
        self.full_rest_hours = 8
        self.special_abilities = [
            Spell(
                name="Hellish Resistance",
                casting_time="Passive",
                range_="Self",
                components=[],
                duration="Permanent",
                description="You have resistance to fire damage.",
                cast=lambda char, targets: print(f"{char.name} uses Hellish Resistance to resist fire damage.")
            ),
            Spell(
                name="Infernal Legacy",
                casting_time="Action",
                range_="30ft",
                components=[],
                duration="Instantaneous",
                description="You can cast the Thaumaturgy cantrip. At 3rd level, you can cast Hellish Rebuke as a 2nd-level spell once per long rest. At 5th level, you can cast Darkness once per long rest.",
                cast=lambda char, targets: print(f"{char.name} uses Infernal Legacy to cast innate spells.")
            )
        ]


if __name__ == "__main__":
    aasimar = Aasimar()
    print(aasimar.description)
