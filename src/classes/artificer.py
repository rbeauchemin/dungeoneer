from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.common import artisans_tools
from src.classes._base import (
    Class, _HALF_CASTER_SLOTS,
)


# Plans Known by level (index = level - 1); level 1 has none
_PLANS_KNOWN = [0, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8]
# Max magic items created via Replicate Magic Item by level
_MAGIC_ITEMS_MAX = [0, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6]


_TINKERS_MAGIC_ITEMS = [
    "Ball Bearings", "Flask", "Pouch", "Basket", "Grappling Hook", "Rope",
    "Bedroll", "Hunting Trap", "Sack", "Bell", "Jug", "Shovel", "Blanket",
    "Lamp", "Iron Spikes", "Block and Tackle", "Manacles", "String",
    "Glass Bottle", "Net", "Tinderbox", "Bucket", "Oil", "Torch",
    "Candle", "Paper", "Vial", "Parchment", "Crowbar", "Pole",
]


class Artificer(Class):
    def __init__(self, level):
        super().__init__(name="Artificer", level=1)
        self.todo = []
        self.level = level
        self.hit_dice = 8
        self.primary_ability = "Intelligence"
        self.spellcasting_ability = "Intelligence"
        self.spell_slots = dict(_HALF_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_HALF_CASTER_SLOTS[level - 1])
        self.proficiencies["Armor"] = ["Light", "Medium", "Shield"]
        self.proficiencies["Weapons"] = ["Simple"]
        self.proficiencies["Tools"] = ["Thieves' Tools", "Tinker's Tools"]
        self.proficiencies["Saving Throws"] = ["Constitution", "Intelligence"]
        self.proficiencies["Skills"] = ["Arcana", "History", "Investigation", "Medicine", "Nature", "Perception", "Sleight of Hand"]
        self.completed_levelup_to = 1

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 150
        else:
            character.add_item([
                StuddedLeatherArmor(), Dagger(), DungeoneersPack(),
            ])
            character.gold += 16
        return character

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        self.completed_levelup_to = 1
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []

        # Tinker's Magic: create mundane items with Tinker's Tools
        character.special_abilities += [
            Spell(
                name="Tinker's Magic",
                casting_time="Magic Action",
                range_="5 feet",
                components=[],
                duration="Until Long Rest",
                description="While holding Tinker's Tools, you can create one item from the Tinker's Magic list in an unoccupied space within 5 feet. The item lasts until you finish a Long Rest. You can use this feature a number of times equal to your Intelligence modifier (minimum of once), and regain all uses on a Long Rest.",
                uses_left=max(1, character.get_ability_bonus("Intelligence")),
                cooldown="Long Rest",
            )
        ]

        character.todo.extend([
            {
                "Text": "Choose 2 skills to be proficient in.",
                "Options": ["Arcana", "History", "Investigation", "Medicine", "Nature", "Perception", "Sleight of Hand"],
                "Choices": 2,
                "Function": lambda character, choices: character.proficiencies["Skills"].__iadd__(choices)
            },
            {
                "Text": "Choose one type of Artisan's Tools to gain proficiency in.",
                "Options": artisans_tools,
                "Choices": 1,
                "Function": lambda character, choices: character.proficiencies["Tools"].__iadd__(choices)
            },
            {
                "Text": "Select starting equipment or gold: (Studded Leather Armor, Dagger, Thieves' Tools, Tinker's Tools, Dungeoneer's Pack, 16 GP) or (150 GP)",
                "Options": ["Starting Equipment", "Gold"],
                "Function": self.select_starting_equipment
            },
        ])

        # Apply level-up features for levels above 1
        for lv in range(2, self.level + 1):
            self._apply_level(character, lv)

        return character

    def _apply_level(self, character: Character, level: int):
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []

        if level == 2:
            plans = _PLANS_KNOWN[level - 1]
            max_items = _MAGIC_ITEMS_MAX[level - 1]
            character.special_abilities += [
                Spell(
                    name="Replicate Magic Item",
                    casting_time="Long Rest",
                    range_="Self",
                    components=[],
                    duration="Permanent",
                    description=f"You know {plans} arcane plans for replicating magic items. After a Long Rest (with Tinker's Tools in hand), you can create up to {max_items} different magic items based on plans you know. Created items that require Attunement can be attuned to instantly. You can't have more replicated items active than the current maximum.",
                )
            ]
            character.todo.extend([
                {
                    "Text": f"Choose {plans} Magic Item Plans to know (Replicate Magic Item).",
                    "Choices": plans,
                    "Options": [
                        "Bag of Holding", "Cap of Water Breathing", "Sending Stones",
                        "Wand of the War Mage +1", "Alchemy Jug", "Boots of Elvenkind",
                        "Cloak of Elvenkind", "Cloak of Protection", "Eyes of Charming",
                        "Gloves of Thievery", "Lantern of Revealing", "Pipes of Haunting",
                        "Ring of Water Walking", "Winged Boots", "Amulet of Health",
                        "Belt of Giant Strength (Hill)", "Cloak of Displacement",
                        "Headband of Intellect", "Medallion of Thoughts", "Necklace of Adaptation",
                        "Periapt of Wound Closure", "Pipes of the Sewers", "Ring of Jumping",
                        "Ring of Mind Shielding", "Slippers of Spider Climbing",
                        "Wand of the War Mage +2", "Wings of Flying",
                    ],
                    "Function": lambda character, choices: None  # GM/player tracks plans separately
                }
            ])

        elif level == 3:
            character.todo.extend([
                {
                    "Text": "Choose an Artificer Subclass: Alchemist, Armorer, Artillerist, or Battle Smith.",
                    "Options": ["Alchemist", "Armorer", "Artillerist", "Battle Smith"],
                    "Choices": 1,
                    "Function": lambda character, choices: setattr(character, "subclass", choices[0]) if hasattr(character, "subclass") else None
                }
            ])

        elif level == 6:
            character.special_abilities += [
                Spell(
                    name="Magic Item Tinker",
                    casting_time="Bonus Action / Magic Action",
                    range_="5 feet",
                    components=[],
                    duration="Instantaneous",
                    description="You gain three options for your Replicate Magic Item items within 5 feet: Charge Magic Item (Bonus Action, expend a spell slot to recharge charges equal to the slot level), Drain Magic Item (Bonus Action, destroy it to gain a spell slot — 1st for Common, 2nd for Uncommon/Rare; once per Long Rest), or Transmute Magic Item (Magic Action, transform it into another item you have a plan for; once per Long Rest).",
                    uses_left=1,
                    cooldown="Long Rest",
                )
            ]

        elif level == 7:
            character.special_abilities += [
                Spell(
                    name="Flash of Genius",
                    casting_time="Reaction",
                    range_="30 feet",
                    components=[],
                    duration="Instantaneous",
                    description="When you or a creature you can see within 30 feet fails an ability check or saving throw, you can use your Reaction to add a bonus equal to your Intelligence modifier (minimum +1) to the roll, potentially causing it to succeed. Uses = Intelligence modifier (minimum 1). Regain all uses on a Long Rest.",
                    uses_left=max(1, character.get_ability_bonus("Intelligence")),
                    cooldown="Long Rest",
                )
            ]

        elif level == 10:
            character.special_abilities += [
                Spell(
                    name="Magic Item Adept",
                    casting_time="Passive",
                    range_="Self",
                    components=[],
                    duration="Permanent",
                    description="You can now attune to up to four magic items at once.",
                )
            ]

        elif level == 11:
            character.special_abilities += [
                Spell(
                    name="Spell-Storing Item",
                    casting_time="Long Rest",
                    range_="Touch",
                    components=[],
                    duration="Until expended or replaced",
                    description="After a Long Rest, touch a Simple/Martial weapon or Spellcasting Focus to store a level 1–3 Artificer spell (casting time: action, no consumed Material component). A creature holding the item can use a Magic action to produce the spell's effect using your spellcasting modifier. The stored spell can be used a number of times equal to twice your Intelligence modifier (minimum twice) before it fades.",
                )
            ]

        elif level == 14:
            character.special_abilities += [
                Spell(
                    name="Advanced Artifice",
                    casting_time="Passive",
                    range_="Self",
                    components=[],
                    duration="Permanent",
                    description="Magic Item Savant: You can now attune to up to five magic items at once. Refreshed Genius: When you finish a Short Rest, you regain one expended use of Flash of Genius.",
                )
            ]

        elif level == 18:
            character.special_abilities += [
                Spell(
                    name="Magic Item Master",
                    casting_time="Passive",
                    range_="Self",
                    components=[],
                    duration="Permanent",
                    description="You can now attune to up to six magic items at once.",
                )
            ]

        elif level == 20:
            character.special_abilities += [
                Spell(
                    name="Soul of Artifice",
                    casting_time="Passive / Reaction",
                    range_="Self",
                    components=[],
                    duration="Permanent",
                    description="Cheat Death: If reduced to 0 HP but not killed outright, you can disintegrate any number of Uncommon or Rare Replicate Magic Items; your HP instead becomes 20 x the number of items disintegrated. Magical Guidance: When you finish a Short Rest, if you are attuned to at least one magic item, regain all expended uses of Flash of Genius.",
                )
            ]

        self.completed_levelup_to = level
        self.spell_slots = dict(_HALF_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_HALF_CASTER_SLOTS[level - 1])

    def level_up(self, character: Character):
        super().level_up(character)
        self._apply_level(character, self.level)
        return character
