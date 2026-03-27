from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.classes._base import (
    Class, _FULL_CASTER_SLOTS,
)

# Channel Divinity uses by Cleric level (index 0 = level 1).
# Levels 1 has no Channel Divinity; 2-5 → 2 uses; 6-17 → 3 uses; 18-20 → 4 uses.
_CHANNEL_DIVINITY_USES = [
    0,  # 1  — not yet gained
    2,  # 2
    2,  # 3
    2,  # 4
    2,  # 5
    3,  # 6
    3,  # 7
    3,  # 8
    3,  # 9
    3,  # 10
    3,  # 11
    3,  # 12
    3,  # 13
    3,  # 14
    3,  # 15
    3,  # 16
    3,  # 17
    4,  # 18
    4,  # 19
    4,  # 20
]

# Prepared spells by level
PREPARABLE_SPELLS = [4, 5, 6, 7, 9, 10, 11, 12, 14, 15, 16, 16, 17, 17, 18, 18, 19, 20, 21, 22]


class Cleric(Class):
    # 2024 PHB subclasses (Knowledge Domain added alongside the original four).
    CLERIC_SUBCLASSES = [
        "Knowledge Domain",
        "Life Domain",
        "Light Domain",
        "Trickery Domain",
        "War Domain",
    ]

    def __init__(self, level):
        super().__init__(name="Cleric", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 8
        self.primary_ability = "Wisdom"
        self.spellcasting_ability = "Wisdom"
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.proficiencies["Armor"] = ["Light", "Medium", "Shield"]
        self.proficiencies["Weapons"] = ["Simple"]
        self.proficiencies["Saving Throws"] = ["Wisdom", "Charisma"]
        self.proficiencies["Skills"] = []
        self.completed_levelup_to = 1

    # ── Skill / subclass selection helpers ────────────────────────────────────

    def _set_skill_proficiencies(self, character: Character, choices, **kwargs):
        character.proficiencies["Skills"] += choices

    def _set_subclass(self, character: Character, choices, **kwargs):
        self.subclass = choices[0]

    # ── Starting equipment ────────────────────────────────────────────────────

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 110
        else:
            character.add_item([ChainShirt(), Shield(), Mace(), HolySymbol(), ScholarsPack()])
            character.gold += 7
        return character

    # ── Divine Order (level 1) ────────────────────────────────────────────────

    def _apply_divine_order(self, character: Character, choices, **kwargs):
        """
        Protector: Heavy armor + Martial weapon proficiency.
        Thaumaturge: one extra cantrip + Wisdom modifier bonus to Int (Arcana or Religion) checks.
        """
        if "Protector" in choices:
            character.proficiencies["Armor"] += ["Heavy"]
            character.proficiencies["Weapons"] += ["Martial"]
        else:
            # Thaumaturge — extra cantrip is tracked as a todo; the Intelligence bonus
            # is a passive trait noted on the character sheet.
            character.todo.append({
                "Text": (
                    "Thaumaturge: Choose one extra cantrip from the Cleric spell list. "
                    "You also add your Wisdom modifier (min +1) to Intelligence (Arcana or Religion) checks."
                ),
                "Options": ["Cantrip"],  # placeholder — real cantrip picker should be wired up here
                "Function": lambda char, ch, **kw: char.special_traits.append(
                    "Thaumaturge: +Wisdom modifier to Intelligence (Arcana or Religion) checks."
                ),
            })

    # ── Level-by-level feature application ───────────────────────────────────

    def _build_channel_divinity(self):
        """Return a Channel Divinity Spell object scaled to the current level."""
        uses = _CHANNEL_DIVINITY_USES[self.level - 1]
        return Spell(
            name="Channel Divinity",
            casting_time="Magic Action",
            range_="Self",
            components=[],
            duration="Instantaneous",
            description=(
                "You channel divine energy to fuel one of the following magical effects:\n"
                "Divine Spark: Point your Holy Symbol at a creature within 30 ft. Roll Wisdom-modifier "
                "d8s (min 1d8). Either restore that many HP to the creature, or force a Constitution save: "
                "on a failure the creature takes Necrotic or Radiant damage equal to the roll; "
                "half on a success. (Scales to 2d8 at level 7, 3d8 at level 13, 4d8 at level 18.)\n"
                "Turn Undead: Each Undead of your choice within 30 ft must make a Wisdom save. "
                "On a failure it has the Frightened and Incapacitated conditions for 1 minute, "
                "moving as far from you as possible on its turns. "
                "Ends early if the creature takes damage, you become Incapacitated, or you die.\n"
                "Your subclass may grant additional Channel Divinity options."
            ),
            uses_left=uses,
            cooldown="Short Rest",
        )

    def _refresh_channel_divinity(self, character: Character):
        """Replace the Channel Divinity ability with a fresh one for the current level."""
        character.special_abilities = [
            a for a in character.special_abilities if a.name != "Channel Divinity"
        ] + [self._build_channel_divinity()]

    def _apply_level(self, character: Character, level: int):
        if level == 2:
            if not isinstance(character.special_abilities, list):
                character.special_abilities = []
            character.special_abilities.append(self._build_channel_divinity())

        elif level == 3:
            character.todo.append({
                "Text": "Choose your Cleric Subclass (Divine Domain).",
                "Options": self.CLERIC_SUBCLASSES,
                "Function": self._set_subclass,
            })

        elif level == 5:
            character.special_traits.append(
                "Sear Undead: Whenever you use Turn Undead, roll a number of d8s equal to your "
                "Wisdom modifier (minimum 1d8) and add the results together. Each Undead that fails "
                "its saving throw against that use of Turn Undead takes Radiant damage equal to the "
                "total. This damage doesn't end the turn effect."
            )

        elif level == 6:
            # Subclass feature — prompt handled by the subclass itself in a full implementation.
            character.todo.append({
                "Text": "You gain your Cleric subclass feature at level 6. Apply your Domain feature.",
                "Options": [],
                "Function": lambda char, ch, **kw: None,
            })

        elif level == 7:
            character.todo.append({
                "Text": (
                    "Blessed Strikes: Choose one option —\n"
                    "Divine Strike: Once per turn on a weapon hit, deal an extra 1d8 Necrotic or "
                    "Radiant damage (your choice).\n"
                    "Potent Spellcasting: Add your Wisdom modifier to damage dealt by Cleric cantrips."
                ),
                "Options": ["Divine Strike", "Potent Spellcasting"],
                "Function": lambda char, ch, **kw: char.special_traits.append(
                    f"Blessed Strikes ({ch[0]}): "
                    + ("Once per turn on a weapon hit, deal an extra 1d8 Necrotic or Radiant damage."
                       if ch[0] == "Divine Strike"
                       else "Add Wisdom modifier to Cleric cantrip damage.")
                ),
            })

        elif level == 10:
            character.special_abilities.append(Spell(
                name="Divine Intervention",
                casting_time="Magic Action",
                range_="Self",
                components=[],
                duration="Instantaneous",
                description=(
                    "Call on your deity to intervene. Choose any Cleric spell of level 5 or lower "
                    "that doesn't require a Reaction to cast and cast it without expending a spell "
                    "slot or needing Material components."
                ),
                uses_left=1,
                cooldown="Long Rest",
            ))

        elif level == 14:
            character.special_traits.append(
                "Improved Blessed Strikes: Your Blessed Strikes option grows more powerful. "
                "Divine Strike: the extra damage increases to 2d8. "
                "Potent Spellcasting: when you deal cantrip damage to a creature, you can grant "
                "yourself or a creature within 60 ft a number of Temporary Hit Points equal to "
                "twice your Wisdom modifier."
            )

        elif level == 17:
            # Subclass feature — prompt handled by the subclass itself in a full implementation.
            character.todo.append({
                "Text": "You gain your Cleric subclass feature at level 17. Apply your Domain feature.",
                "Options": [],
                "Function": lambda char, ch, **kw: None,
            })

        elif level == 19:
            # Epic Boon — base class handles ASI at [4, 8, 12, 16]; level 19 is explicit here.
            character.todo.append({
                "Text": "Choose an Epic Boon feat.",
                "Options": ["Epic Boon"],  # placeholder — full Epic Boon feat list goes here
                "Function": lambda char, ch, **kw: char.feats.append(ch[0]),
            })

        elif level == 20:
            # Greater Divine Intervention upgrades the existing Divine Intervention ability.
            character.special_abilities = [
                a for a in character.special_abilities if a.name != "Divine Intervention"
            ]
            character.special_abilities.append(Spell(
                name="Greater Divine Intervention",
                casting_time="Magic Action",
                range_="Self",
                components=[],
                duration="Instantaneous",
                description=(
                    "When you use Divine Intervention, you may choose the Wish spell. "
                    "If you do, you can't use Divine Intervention again until you finish 2d4 Long Rests. "
                    "Otherwise, Divine Intervention functions as normal (any Cleric spell level 5 or lower, "
                    "no slot or Material components required)."
                ),
                uses_left=1,
                cooldown="Long Rest",
            ))

        # Refresh spell slots and Channel Divinity uses for every level-up.
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.preparable_spells = PREPARABLE_SPELLS[self.level - 1]
        if level >= 2:
            self._refresh_channel_divinity(character)
        self.completed_levelup_to = level

    # ── Class interface ───────────────────────────────────────────────────────

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        self.completed_levelup_to = 1
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        for lv in range(2, self.level + 1):
            self._apply_level(character, lv)
        character.todo.extend([
            {
                "Text": (
                    "Select starting equipment or gold: "
                    "(Chain Shirt, Shield, Mace, Holy Symbol, Scholar's Pack, 7 GP) or (110 GP)"
                ),
                "Options": ["Starting Equipment", "Gold"],
                "Function": self.select_starting_equipment,
            },
            {
                "Text": "Choose 2 skills from: History, Insight, Medicine, Persuasion, Religion.",
                "Options": ["History", "Insight", "Medicine", "Persuasion", "Religion"],
                "Choices": 2,
                "Function": self._set_skill_proficiencies,
            },
            {
                "Text": (
                    "Choose Divine Order: "
                    "Protector (Heavy Armor + Martial Weapon proficiency) or "
                    "Thaumaturge (one extra Cleric cantrip + Wisdom modifier bonus to "
                    "Intelligence (Arcana or Religion) checks)."
                ),
                "Options": ["Protector", "Thaumaturge"],
                "Function": self._apply_divine_order,
            },
        ])
        return character

    def level_up(self, character: Character):
        super().level_up(character)  # increments self.level; adds ASI todo at levels 4/8/12/16
        self._apply_level(character, self.level)
        return character
