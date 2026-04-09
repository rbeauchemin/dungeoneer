from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.common import artisans_tools
from src.classes._base import (
    Class, _HALF_CASTER_SLOTS,
)


# Plans Known by level (index = level - 1)
# Artificer gains Replicate Magic Item at level 2; level 1 has none.
_PLANS_KNOWN = [0, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8]

# Max replicated magic items active at once by level
_MAGIC_ITEMS_MAX = [0, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6]

# Prepared spells by level
PREPARABLE_SPELLS = [2, 3, 4, 5, 6, 6, 7, 7, 9, 9, 10, 10, 11, 11, 12, 12, 14, 14, 15, 15]

_TINKERS_MAGIC_ITEMS = [
    "Ball Bearings", "Flask", "Pouch", "Basket", "Grappling Hook", "Rope",
    "Bedroll", "Hunting Trap", "Sack", "Bell", "Jug", "Shovel", "Blanket",
    "Lamp", "Iron Spikes", "Block and Tackle", "Manacles", "String",
    "Glass Bottle", "Net", "Tinderbox", "Bucket", "Oil", "Torch",
    "Candle", "Paper", "Vial", "Parchment", "Crowbar", "Pole",
]

_REPLICATE_MAGIC_ITEM_PLANS = [
    # Common / no rarity restriction
    "Bag of Holding", "Cap of Water Breathing", "Goggles of Night",
    "Rope of Climbing", "Sending Stones", "Wand of the War Mage +1",
    # Uncommon
    "Alchemy Jug", "Boots of Elvenkind", "Cloak of Elvenkind",
    "Cloak of Protection", "Eyes of Charming", "Gloves of Thievery",
    "Lantern of Revealing", "Pipes of Haunting", "Ring of Water Walking",
    "Winged Boots",
    # Rare (require Artificer level 10+)
    "Amulet of Health", "Belt of Giant Strength (Hill)", "Cloak of Displacement",
    "Cloak of the Bat", "Eyes of the Eagle", "Gauntlets of Ogre Power",
    "Headband of Intellect", "Medallion of Thoughts", "Necklace of Adaptation",
    "Periapt of Wound Closure", "Pipes of the Sewers", "Ring of Jumping",
    "Ring of Mind Shielding", "Slippers of Spider Climbing",
    "Wand of the War Mage +2", "Wings of Flying",
    # Very Rare (require Artificer level 14+)
    "Amulet of the Planes", "Belt of Giant Strength (Stone/Frost)",
    "Boots of Speed", "Bracers of Defense", "Cloak of Invisibility",
    "Crystal Ball", "Helm of Teleportation", "Ring of Regeneration",
    "Ring of Shooting Stars", "Ring of Telekinesis",
    "Wand of the War Mage +3",
]


class Artificer(Class):
    def __init__(self, level):
        super().__init__(name="Artificer", level=level)
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
        self.proficiencies["Skills"] = [
            "Arcana", "History", "Investigation", "Medicine",
            "Nature", "Perception", "Sleight of Hand",
        ]
        self.completed_levelup_to = 0

    # ── Equipment ─────────────────────────────────────────────────────────────

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 150
        else:
            character.add_item([
                StuddedLeatherArmor(), Dagger(), DungeoneersPack(),
            ])
            character.gold += 16
        return character

    # ── Level feature application ──────────────────────────────────────────────

    def _apply_level_features(self, character: Character, level: int):
        """Apply all Artificer features unlocked at the given level."""
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []

        if level == 1:
            # ── Spellcasting ───────────────────────────────────────────────────
            # Intelligence-based; prepared spells = INT modifier + half Artificer level (min 1).
            # Requires Tinker's Tools or Arcane Focus as spellcasting focus.
            # Spell slots from _HALF_CASTER_SLOTS; spells known from Artificer spell list.
            character.todo.extend([
                {
                    "Text": (
                        "Spellcasting (Artificer): Prepare Artificer spells equal to your Intelligence "
                        "modifier + half your Artificer level (minimum 1). You can change your prepared "
                        "list on a Long Rest. Spellcasting ability: Intelligence. Requires Tinker's Tools "
                        "or an Arcane Focus as your spellcasting focus."
                    ),
                    "Options": [],  # Full spell list managed separately
                    "Choices": 0,
                    "Function": lambda character, choices: None
                },
            ])

            # ── Tinker's Magic ─────────────────────────────────────────────────
            character.special_abilities.append(
                Spell(
                    name="Tinker's Magic",
                    casting_time="Magic Action",
                    range_="5 feet",
                    components=[],
                    duration="Until Long Rest",
                    description=(
                        "While holding Tinker's Tools, you can use a Magic action to create one Tiny object "
                        "from the Tinker's Magic list in an unoccupied space within 5 feet of you. The object "
                        "is a magic item that lasts until you finish a Long Rest, at which point it crumbles "
                        "to dust. You can have a number of these objects equal to your Intelligence modifier "
                        "(minimum 1). When you finish a Long Rest, you can replace any number of them. "
                        f"Available items: {', '.join(_TINKERS_MAGIC_ITEMS)}."
                    ),
                    uses_left=None,  # tracked per object count via INT modifier
                    cooldown=None,
                )
            )

            # ── Starting todo items ────────────────────────────────────────────
            character.todo.extend([
                {
                    "Text": "Choose 2 skills to be proficient in.",
                    "Options": self.proficiencies["Skills"],
                    "Choices": 2,
                    "Function": self.select_skills,
                    "AllowSame": False,
                },
                {
                    "Text": "Choose one type of Artisan's Tools to gain proficiency in.",
                    "Options": artisans_tools,
                    "Choices": 1,
                    "Function": lambda character, choices: character.proficiencies["Tools"].__iadd__(choices)
                },
                {
                    "Text": (
                        "Select starting equipment or gold: "
                        "(Studded Leather Armor, Dagger, Thieves' Tools, Tinker's Tools, Dungeoneer's Pack, 16 GP) "
                        "or (150 GP)"
                    ),
                    "Options": ["Starting Equipment", "Gold"],
                    "Function": self.select_starting_equipment
                },
            ])

        elif level == 2:
            # ── Replicate Magic Item ───────────────────────────────────────────
            plans = _PLANS_KNOWN[level - 1]
            max_items = _MAGIC_ITEMS_MAX[level - 1]
            character.special_abilities.append(
                Spell(
                    name="Replicate Magic Item",
                    casting_time="Long Rest",
                    range_="Self",
                    components=[],
                    duration="Permanent",
                    description=(
                        f"You know {plans} arcane Plans for replicating magic items. After a Long Rest "
                        f"(with Tinker's Tools in hand), you can create up to {max_items} different magic "
                        "items based on Plans you know. Created items that require Attunement can be attuned "
                        "to instantly. You can't have more replicated items active than the current maximum. "
                        "You gain additional Plans as you level up."
                    ),
                )
            )
            character.todo.append({
                "Text": f"Choose {plans} Magic Item Plans to know (Replicate Magic Item).",
                "Choices": plans,
                "Options": _REPLICATE_MAGIC_ITEM_PLANS,
                "Function": lambda character, choices: None  # GM/player tracks plans separately
            })

        elif level == 3:
            # ── Artificer Subclass ─────────────────────────────────────────────
            character.todo.append({
                "Text": "Choose an Artificer Subclass: Alchemist, Armorer, Artillerist, or Battle Smith.",
                "Options": ["Alchemist", "Armorer", "Artillerist", "Battle Smith"],
                "Choices": 1,
                "Function": lambda character, choices: setattr(character, "subclass", choices[0])
            })

        elif level == 4:
            # ── Ability Score Improvement ──────────────────────────────────────
            character.todo.append({
                "Text": "Choose an Ability Score Improvement or Feat.",
                "Options": ["Ability Score Improvement", "Feat"],
                "Function": self.select_ability_score_improvement_or_feat,
            })

        elif level == 6:
            # ── Magic Item Tinker (replaces Tool Expertise from older rules) ───
            # Update Plans Known and max items
            plans = _PLANS_KNOWN[level - 1]
            max_items = _MAGIC_ITEMS_MAX[level - 1]
            self._refresh_replicate_magic_item(character, plans, max_items)

            character.special_abilities.append(
                Spell(
                    name="Magic Item Tinker",
                    casting_time="Bonus Action or Magic Action",
                    range_="5 feet",
                    components=[],
                    duration="Instantaneous",
                    description=(
                        "You gain three options for interacting with Replicate Magic Items within 5 feet of you: "
                        "Charge Magic Item (Bonus Action): Expend a spell slot to restore a number of charges "
                        "equal to the slot's level. "
                        "Drain Magic Item (Bonus Action): Destroy a replicated item to regain a spell slot — "
                        "1st-level for Common rarity, 2nd-level for Uncommon or Rare. Once per Long Rest. "
                        "Transmute Magic Item (Magic Action): Transform a replicated item into another item "
                        "you have a Plan for, of the same or lower rarity. Once per Long Rest."
                    ),
                    uses_left=1,
                    cooldown="Long Rest",
                )
            )

        elif level == 7:
            # ── Flash of Genius ────────────────────────────────────────────────
            character.special_abilities.append(
                Spell(
                    name="Flash of Genius",
                    casting_time="Reaction",
                    range_="30 feet",
                    components=[],
                    duration="Instantaneous",
                    description=(
                        "When you or a creature you can see within 30 feet of you fails an ability check "
                        "or a saving throw, you can use your Reaction to add your Intelligence modifier "
                        "(minimum +1) to the roll, potentially turning a failure into a success. "
                        "You can use this feature a number of times equal to your Intelligence modifier "
                        "(minimum once), and you regain all expended uses when you finish a Long Rest."
                    ),
                    uses_left=max(1, character.get_ability_modifier("Intelligence")),
                    cooldown="Long Rest",
                )
            )

        elif level == 8:
            # ── Ability Score Improvement ──────────────────────────────────────
            character.todo.append({
                "Text": "Choose an Ability Score Improvement or Feat.",
                "Options": ["Ability Score Improvement", "Feat"],
                "Function": self.select_ability_score_improvement_or_feat,
            })

        elif level == 10:
            # ── Magic Item Adept ───────────────────────────────────────────────
            # Update Plans Known and max items
            plans = _PLANS_KNOWN[level - 1]
            max_items = _MAGIC_ITEMS_MAX[level - 1]
            self._refresh_replicate_magic_item(character, plans, max_items)

            character.special_abilities.append(
                Spell(
                    name="Magic Item Adept",
                    casting_time="Passive",
                    range_="Self",
                    components=[],
                    duration="Permanent",
                    description=(
                        "You can attune to up to four magic items at once (rather than the normal limit of three). "
                        "Additionally, you can craft magic items of Common and Uncommon rarity in half the normal "
                        "time and for half the normal cost."
                    ),
                )
            )

        elif level == 11:
            # ── Spell-Storing Item ─────────────────────────────────────────────
            character.special_abilities.append(
                Spell(
                    name="Spell-Storing Item",
                    casting_time="Long Rest",
                    range_="Touch",
                    components=[],
                    duration="Until expended or replaced",
                    description=(
                        "When you finish a Long Rest, you can touch a Simple or Martial weapon or a "
                        "Spellcasting Focus and store a 1st- or 2nd-level Artificer spell inside it "
                        "(the spell must have a casting time of an action and must not consume a costly "
                        "Material component). A creature holding the item can use a Magic action to produce "
                        "the spell's effect, using your spell attack bonus and save DC. The stored spell can "
                        "be activated a number of times equal to twice your Intelligence modifier (minimum "
                        "twice) before it fades. You can store a different spell each Long Rest."
                    ),
                )
            )

        elif level == 12:
            # ── Ability Score Improvement ──────────────────────────────────────
            character.todo.append({
                "Text": "Choose an Ability Score Improvement or Feat.",
                "Options": ["Ability Score Improvement", "Feat"],
                "Function": self.select_ability_score_improvement_or_feat,
            })

        elif level == 14:
            # ── Advanced Artifice ──────────────────────────────────────────────
            # Update Plans Known and max items
            plans = _PLANS_KNOWN[level - 1]
            max_items = _MAGIC_ITEMS_MAX[level - 1]
            self._refresh_replicate_magic_item(character, plans, max_items)

            character.special_abilities.append(
                Spell(
                    name="Advanced Artifice",
                    casting_time="Passive",
                    range_="Self",
                    components=[],
                    duration="Permanent",
                    description=(
                        "Magic Item Savant: You can now attune to up to five magic items at once. "
                        "You ignore all class, race, spell, and level requirements on attuning to or using "
                        "a magic item. "
                        "Refreshed Genius: When you finish a Short Rest, you regain one expended use of "
                        "Flash of Genius."
                    ),
                )
            )

        elif level == 16:
            # ── Ability Score Improvement ──────────────────────────────────────
            character.todo.append({
                "Text": "Choose an Ability Score Improvement or Feat.",
                "Options": ["Ability Score Improvement", "Feat"],
                "Function": self.select_ability_score_improvement_or_feat,
            })

        elif level == 18:
            # ── Magic Item Master ──────────────────────────────────────────────
            # Update Plans Known and max items
            plans = _PLANS_KNOWN[level - 1]
            max_items = _MAGIC_ITEMS_MAX[level - 1]
            self._refresh_replicate_magic_item(character, plans, max_items)

            character.special_abilities.append(
                Spell(
                    name="Magic Item Master",
                    casting_time="Passive",
                    range_="Self",
                    components=[],
                    duration="Permanent",
                    description="You can now attune to up to six magic items at once.",
                )
            )

        elif level == 19:
            # ── Epic Boon ──────────────────────────────────────────────────────
            character.todo.append({
                "Text": "Choose an Epic Boon feat.",  # TODO: Choose an Epic Boon feat.
                "Options": [
                    "Epic Boon of Combat Prowess", "Epic Boon of Dimensional Travel",
                    "Epic Boon of Energy Resistance", "Epic Boon of Fate",
                    "Epic Boon of Fortitude", "Epic Boon of Irresistible Offense",
                    "Epic Boon of Luck", "Epic Boon of the Night Spirit",
                    "Epic Boon of Peerless Aim", "Epic Boon of Recovery",
                    "Epic Boon of Skill Proficiency", "Epic Boon of Speed",
                    "Epic Boon of Spell Recall", "Epic Boon of Truesight",
                    "Epic Boon of Undetectability",
                ],
                "Choices": 1,
                "Function": self.select_feat,
            })

        elif level == 20:
            # ── Soul of Artifice ───────────────────────────────────────────────
            character.special_abilities.append(
                Spell(
                    name="Soul of Artifice",
                    casting_time="Passive / Reaction",
                    range_="Self",
                    components=[],
                    duration="Permanent",
                    description=(
                        "You have developed a mystical connection to your magic items. "
                        "Cheat Death: If you are reduced to 0 Hit Points but not killed outright, you can "
                        "disintegrate any number of your Replicate Magic Items that are Uncommon rarity or "
                        "higher; you are instead reduced to 1 Hit Point for each item destroyed this way. "
                        "Magical Guidance: When you make an ability check that fails, you can expend a spell "
                        "slot to reroll the check, and you must use the new roll."
                    ),
                )
            )

        # ── Update spell slots for every level ────────────────────────────────
        self.spell_slots = dict(_HALF_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_HALF_CASTER_SLOTS[level - 1])
        self.preparable_spells = PREPARABLE_SPELLS[self.level - 1]
        self.completed_levelup_to = level

    def _refresh_replicate_magic_item(self, character: Character, plans: int, max_items: int):
        """Replace the Replicate Magic Item ability with an updated version reflecting current Plans/max."""
        character.special_abilities = [
            a for a in character.special_abilities if a.name != "Replicate Magic Item"
        ]
        character.special_abilities.append(
            Spell(
                name="Replicate Magic Item",
                casting_time="Long Rest",
                range_="Self",
                components=[],
                duration="Permanent",
                description=(
                    f"You know {plans} arcane Plans for replicating magic items. After a Long Rest "
                    f"(with Tinker's Tools in hand), you can have up to {max_items} different replicated "
                    "magic items active at once. Created items that require Attunement can be attuned to "
                    "instantly."
                ),
            )
        )

    # ── Class interface ────────────────────────────────────────────────────────

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        # Apply features for every level from 1 up to the artificer's starting level
        for lvl in range(1, self.level + 1):
            self._apply_level_features(character, lvl)
        self.completed_levelup_to = self.level
        return character

    def level_up(self, character: Character):
        super().level_up(character)  # increments self.level; handles ASI at 4/8/12/16 via base
        self._apply_level_features(character, self.level)
        return character
