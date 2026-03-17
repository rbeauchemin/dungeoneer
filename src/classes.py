from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.common import dnd_skills, artisans_tools


class Class:
    def __init__(self, name, level, subclass=None):
        self.name = name
        self.level = level
        self.hit_dice = 8
        self.subclass = subclass
        self.spellcasting_ability = "None"
        self.proficiencies = {
            "Armor": [],
            "Weapons": [],
            "Tools": [],
            "Saving Throws": [],
            "Skills": []
        }

    def apply_to_character(self, character):
        character.proficiencies["Armor"] += self.proficiencies["Armor"]
        character.proficiencies["Weapons"] += self.proficiencies["Weapons"]
        character.proficiencies["Tools"] += self.proficiencies["Tools"]
        character.proficiencies["Saving Throws"] += self.proficiencies["Saving Throws"]
        character.proficiencies["Skills"] += self.proficiencies["Skills"]
        return character

    def level_up(self, character):
        # These are handled in the specific class level up functions, but this is where you would put any general level up logic that applies to all classes, such as increasing hit points or granting ability score improvements.
        return character


class Barbarian(Class):
    def __init__(self, level):
        super().__init__(name="Barbarian", level=1)
        self.todo = []
        self.level = level
        self.hit_dice = 12
        self.primary_ability = "Strength"
        self.proficiencies["Armor"] = ["Light", "Medium", "Shield"]
        self.proficiencies["Weapons"] = ["Simple", "Martial"]
        self.proficiencies["Saving Throws"] = ["Strength", "Constitution"]
        self.proficiencies["Skills"] = ["Animal Handling", "Athletics", "Intimidation", "Nature", "Perception", "Survival"]
        self.completed_levelup_to = 1

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 75
        else:
            character.add_item([Handaxe(quantity=4), Greataxe(), ExplorersPack()])
            character.gold += 15
        return character

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        # Handle level one additions here, and level up additions in the level up function
        self.completed_levelup_to = 1
        rages_per_level = [2, 2, 3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 6, 6, 6, 6]
        character.special_abilities += [
            Spell(
                name="Rage",
                casting_time="Bonus Action",
                range_="Self",
                components=[],
                duration="1 Turn",
                description="In battle, you fight with primal ferocity. On your turn, you can enter a rage as a bonus action. While raging, you gain the following benefits if you aren't wearing heavy armor: You have advantage on Strength checks and Strength saving throws. When you make a melee weapon attack using Strength, you gain a bonus to the damage roll that increases as you gain levels as a barbarian, as shown in the Rage Damage column of the Barbarian table. You have resistance to bludgeoning, piercing, and slashing damage.",
                uses_left=rages_per_level[self.level - 1],
                cooldown="Long Rest",
                cast=lambda caster, targets: caster.active_effects.append("Rage")
            )
        ]
        character.todo.extend([
            {
                "Text": "Choose two weapons to gain mastery in.",
                "Options": ["Greataxe", "Greatsword", "Handaxe", "Javelin", "Light Hammer", "Longsword", "Maul", "Morningstar", "Pike", "Rapier", "Scimitar", "Shortsword", "Trident", "War Pick", "Warhammer"],
                "Choices": 2,
                "Function": lambda character, choices: character.weapon_mastery.extend(choices)
            },
            {
                "Text": "Select starting equipment or gold: (Greataxe, Two Handaxes, Explorer's Pack) or (4 Javelins and 2 Handaxes and 10 gold)",
                "Options": ["Starting Equipment", "Gold"],
                "Function": self.select_starting_equipment
            }
        ])
        return character

    def level_up(self, character: Character):
        self.level += 1
        # TODO: Handle levelup logic such as increasing hit points, granting new abilities, and updating the number of rages per day.
        character.classes = [cls for cls in character.classes if cls.name != self.name] + [self]
        return character


class Bard(Class):
    # Full caster spell slot table (levels 1–20)
    SPELL_SLOTS = [
        {1: 2},                                                         # Level 1
        {1: 3},                                                         # Level 2
        {1: 4, 2: 2},                                                   # Level 3
        {1: 4, 2: 3},                                                   # Level 4
        {1: 4, 2: 3, 3: 2},                                            # Level 5
        {1: 4, 2: 3, 3: 3},                                            # Level 6
        {1: 4, 2: 3, 3: 3, 4: 1},                                      # Level 7
        {1: 4, 2: 3, 3: 3, 4: 2},                                      # Level 8
        {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},                               # Level 9
        {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},                               # Level 10
        {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},                        # Level 11
        {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},                        # Level 12
        {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},                  # Level 13
        {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},                  # Level 14
        {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},            # Level 15
        {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},            # Level 16
        {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1},     # Level 17
        {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1},     # Level 18
        {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1},     # Level 19
        {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1},     # Level 20
    ]

    # Bardic Inspiration die by level
    BARDIC_INSPIRATION_DIE = {
        **{lv: "d6" for lv in range(1, 5)},
        **{lv: "d8" for lv in range(5, 10)},
        **{lv: "d10" for lv in range(10, 15)},
        **{lv: "d12" for lv in range(15, 21)},
    }

    # Cantrips known by level (index 0 = level 1)
    CANTRIPS_KNOWN = [2, 2, 2, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4]

    MUSICAL_INSTRUMENTS = [
        "Bagpipes", "Drum", "Dulcimer", "Flute", "Horn",
        "Lute", "Lyre", "Pan Flute", "Shawm", "Viol",
    ]

    BARD_SUBCLASSES = [
        "College of Dance",
        "College of Glamour",
        "College of Lore",
        "College of Valor",
    ]

    def __init__(self, level):
        super().__init__(name="Bard", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 8
        self.primary_ability = "Charisma"
        self.spellcasting_ability = "Charisma"
        self.spell_slots = dict(self.SPELL_SLOTS[level - 1])
        self.spell_slots_remaining = dict(self.SPELL_SLOTS[level - 1])
        self.proficiencies["Armor"] = ["Light"]
        self.proficiencies["Weapons"] = ["Simple"]
        self.proficiencies["Saving Throws"] = ["Dexterity", "Charisma"]
        self.proficiencies["Skills"] = []  # Chosen via todo
        self.completed_levelup_to = 1

    # ── helpers ──────────────────────────────────────────────────────────────

    def _set_skill_proficiencies(self, character: Character, choices):
        character.proficiencies["Skills"] += choices

    def _set_instrument_proficiencies(self, character: Character, choices):
        character.proficiencies["Tools"] += choices

    def _apply_expertise(self, character: Character, choices):
        if not hasattr(character, "expertise"):
            character.expertise = []
        character.expertise += choices

    def _apply_magical_secrets(self, character: Character, choices):
        # TODO: resolve spell names to Spell objects from the full spell list
        if not hasattr(character, "magical_secrets"):
            character.magical_secrets = []
        character.magical_secrets += choices

    def _set_subclass(self, character: Character, choices):
        self.subclass = choices[0]

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 90
        else:
            character.add_item([LeatherArmor(), Dagger(quantity=2), EntertainersPack()])
            # Add the instrument the player chose as proficient
            if character.proficiencies["Tools"]:
                character.add_item(character.proficiencies["Tools"][-1])
            character.gold += 19
        return character

    # ── feature application ───────────────────────────────────────────────────

    def _apply_level(self, character: Character, level: int):
        """Apply all features gained at the given level."""

        if level == 2:
            # Expertise: choose 2 proficient skills or tools to double proficiency bonus on
            character.todo.append({
                "Text": (
                    "Expertise (Level 2): Choose 2 skills or tools you are proficient in "
                    "to gain Expertise (double proficiency bonus on checks with them)."
                ),
                "Options": list(dnd_skills.keys()),
                "Choices": 2,
                "Function": self._apply_expertise,
            })
            # Jack of All Trades: add half proficiency to checks not using proficiency
            character.special_traits.append("Jack of All Trades")

        elif level == 3:
            character.todo.append({
                "Text": "Choose a Bard College (subclass).",
                "Options": self.BARD_SUBCLASSES,
                "Function": self._set_subclass,
            })
            # TODO: Apply subclass level 3 features based on chosen college

        elif level == 5:
            # Font of Inspiration: Bardic Inspiration recharges on Short Rest
            for ability in character.special_abilities:
                if ability.name == "Bardic Inspiration":
                    ability.cooldown = "Short Rest"
            character.special_traits.append("Font of Inspiration")

        elif level == 7:
            character.special_abilities.append(
                Spell(
                    name="Countercharm",
                    casting_time="Action",
                    range_="Self (30-foot emanation)",
                    components=[],
                    duration="Until the start of your next turn",
                    description=(
                        "You launch a magical performance to distract an enemy. "
                        "Until the start of your next turn, you and any ally within "
                        "30 feet of you who can hear you have Advantage on saving "
                        "throws to avoid or end the Charmed or Frightened condition."
                    ),
                )
            )

        elif level == 9:
            # Second Expertise selection
            character.todo.append({
                "Text": (
                    "Expertise (Level 9): Choose 2 more skills or tools you are "
                    "proficient in to gain Expertise."
                ),
                "Options": list(dnd_skills.keys()),
                "Choices": 2,
                "Function": self._apply_expertise,
            })

        elif level == 10:
            # Magical Secrets: learn 2 spells from any class list
            character.todo.append({
                "Text": (
                    "Magical Secrets (Level 10): Choose 2 spells from any class's "
                    "spell list. They count as Bard spells for you and are always "
                    "prepared. Enter the spell names."
                ),
                # TODO: Replace with a real cross-class spell list when available
                "Options": ["(Enter spell name — see full spell list)"],
                "Choices": 1,
                "Function": self._apply_magical_secrets,
            })

        elif level == 14:
            # TODO: Subclass level-14 feature
            pass

        elif level == 18:
            character.special_traits.append("Superior Bardic Inspiration")
            # Superior Bardic Inspiration: regain one use on initiative roll if at 0

        elif level == 20:
            character.special_abilities.append(
                Spell(
                    name="Words of Creation",
                    casting_time="Action",
                    range_="Touch",
                    components=[],
                    duration="Instantaneous",
                    description=(
                        "You have mastered two words of power.\n"
                        "Power Word Fortify: You touch up to 5 willing creatures. "
                        "Distribute up to 5 x (2d12 + Charisma modifier) Hit Points "
                        "among them in any way you choose. This doesn't require "
                        "Concentration and can't be undone.\n"
                        "Power Word Heal: You touch a creature and restore all its "
                        "Hit Points. All conditions afflicting it also end."
                    ),
                    cooldown="Long Rest",
                )
            )

        # Update Bardic Inspiration die if it increases at this level
        prev_die = self.BARDIC_INSPIRATION_DIE.get(level - 1, "d6")
        new_die = self.BARDIC_INSPIRATION_DIE[level]
        if new_die != prev_die:
            for ability in character.special_abilities:
                if ability.name == "Bardic Inspiration":
                    ability.description = ability.description.replace(
                        f"({prev_die})", f"({new_die})"
                    )

        # Update spell slots
        self.spell_slots = dict(self.SPELL_SLOTS[level - 1])
        self.spell_slots_remaining = dict(self.SPELL_SLOTS[level - 1])
        self.completed_levelup_to = level

    # ── apply_to_character ────────────────────────────────────────────────────

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        self.completed_levelup_to = 1

        # Normalize special_abilities to a list (base Species uses a dict)
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []

        insp_die = self.BARDIC_INSPIRATION_DIE[self.level]

        # ── Level 1 ability: Bardic Inspiration ──────────────────────────────
        character.special_abilities += [
            Spell(
                name="Bardic Inspiration",
                casting_time="Bonus Action",
                range_="60 feet",
                components=[],
                duration="1 minute",
                description=(
                    f"You inspire a creature within 60 feet that can hear you. "
                    f"Once in the next minute, that creature can roll a Bardic "
                    f"Inspiration die ({insp_die}) and add it to one ability check, "
                    f"attack roll, or saving throw it makes. A creature can have "
                    f"only one Bardic Inspiration die at a time. You can use this "
                    f"feature a number of times equal to your Charisma modifier "
                    f"(minimum once)."
                ),
                uses_left=max(1, (character.ability_scores.get("Charisma", 10) - 10) // 2),
                cooldown="Long Rest",
            )
        ]

        # ── Apply features for levels 2–N first (they stack at bottom of todo)
        for lv in range(2, self.level + 1):
            self._apply_level(character, lv)

        # ── Level 1 todos (appended last → resolved first, LIFO) ─────────────
        # Resolution order: instruments → skills → equipment
        character.todo.extend([
            {
                "Text": (
                    "Select starting equipment or gold: "
                    "(Leather Armor, 2 Daggers, Musical Instrument you're proficient in, "
                    "Entertainer's Pack, 19 GP) or (105 GP)"
                ),
                "Options": ["Starting Equipment", "Gold"],
                "Function": self.select_starting_equipment,
            },
            {
                "Text": (
                    "Choose 3 skills to gain proficiency in "
                    "(Bards may choose from any skill)."
                ),
                "Options": list(dnd_skills.keys()),
                "Choices": 3,
                "Function": self._set_skill_proficiencies,
            },
            {
                "Text": "Choose 3 musical instruments to gain proficiency with.",
                "Options": self.MUSICAL_INSTRUMENTS,
                "Choices": 3,
                "Function": self._set_instrument_proficiencies,
            },
        ])
        return character

    # ── level_up ──────────────────────────────────────────────────────────────

    def level_up(self, character: Character):
        self.level += 1
        self._apply_level(character, self.level)
        character.classes = [cls for cls in character.classes if cls.name != self.name] + [self]
        return character


# ── Shared spell-slot tables ───────────────────────────────────────────────

_FULL_CASTER_SLOTS = [
    {1: 2},                                                          # Level 1
    {1: 3},                                                          # Level 2
    {1: 4, 2: 2},                                                    # Level 3
    {1: 4, 2: 3},                                                    # Level 4
    {1: 4, 2: 3, 3: 2},                                             # Level 5
    {1: 4, 2: 3, 3: 3},                                             # Level 6
    {1: 4, 2: 3, 3: 3, 4: 1},                                       # Level 7
    {1: 4, 2: 3, 3: 3, 4: 2},                                       # Level 8
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},                                # Level 9
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},                                # Level 10
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},                         # Level 11
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},                         # Level 12
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},                   # Level 13
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},                   # Level 14
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},             # Level 15
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},             # Level 16
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1},      # Level 17
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1},      # Level 18
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1},      # Level 19
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1},      # Level 20
]

_HALF_CASTER_SLOTS = [
    {1: 2},                          # Level 1
    {1: 2},                          # Level 2
    {1: 3},                          # Level 3
    {1: 3},                          # Level 4
    {1: 4, 2: 2},                    # Level 5
    {1: 4, 2: 2},                    # Level 6
    {1: 4, 2: 3},                    # Level 7
    {1: 4, 2: 3},                    # Level 8
    {1: 4, 2: 3, 3: 2},             # Level 9
    {1: 4, 2: 3, 3: 2},             # Level 10
    {1: 4, 2: 3, 3: 3},             # Level 11
    {1: 4, 2: 3, 3: 3},             # Level 12
    {1: 4, 2: 3, 3: 3, 4: 1},       # Level 13
    {1: 4, 2: 3, 3: 3, 4: 1},       # Level 14
    {1: 4, 2: 3, 3: 3, 4: 2},       # Level 15
    {1: 4, 2: 3, 3: 3, 4: 2},       # Level 16
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 1}, # Level 17
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 1}, # Level 18
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2}, # Level 19
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2}, # Level 20
]

_WARLOCK_PACT_SLOTS = [
    {1: 1}, {1: 2}, {2: 2}, {2: 2},  # Levels 1-4
    {3: 2}, {3: 2}, {4: 2}, {4: 2},  # Levels 5-8
    {5: 2}, {5: 2},                   # Levels 9-10
    {5: 3}, {5: 3}, {5: 3}, {5: 3},  # Levels 11-14
    {5: 3}, {5: 3},                   # Levels 15-16
    {5: 4}, {5: 4}, {5: 4}, {5: 4},  # Levels 17-20
]

_FIGHTING_STYLES = [
    "Archery", "Blind Fighting", "Defense", "Dueling",
    "Great Weapon Fighting", "Interception", "Protection",
    "Thrown Weapon Fighting", "Two-Weapon Fighting", "Unarmed Fighting",
]


# ── Cleric ─────────────────────────────────────────────────────────────────

class Cleric(Class):
    CLERIC_SUBCLASSES = ["Life Domain", "Light Domain", "Trickery Domain", "War Domain"]

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

    def _set_skill_proficiencies(self, character: Character, choices):
        character.proficiencies["Skills"] += choices

    def _set_subclass(self, character: Character, choices):
        self.subclass = choices[0]

    def _apply_divine_order(self, character: Character, choices):
        if "Protector" in choices:
            character.proficiencies["Armor"] += ["Heavy"]
            character.proficiencies["Weapons"] += ["Martial"]
        else:
            character.proficiencies["Skills"] += choices[1:]

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 110
        else:
            character.add_item([ChainShirt(), Shield(), Mace(), HolySymbol(), ScholarsPack()])
            character.gold += 7

    def _apply_level(self, character: Character, level: int):
        if level == 2:
            channel_uses = [2,2,2,2,2,3,3,3,3,3,4,4,4,4,4,4,4,5,5,5]
            character.special_abilities.append(Spell(
                name="Channel Divinity",
                casting_time="Action", range_="Self", components=[],
                duration="Instantaneous",
                description=(
                    "You channel divine energy to fuel magical effects. "
                    "You have Turn Undead and one effect from your subclass. "
                    "Turn Undead: each undead that can see or hear you must make a Wisdom save "
                    "or be Turned for 1 minute."
                ),
                uses_left=channel_uses[self.level - 1],
                cooldown="Short Rest",
            ))
        elif level == 3:
            character.todo.append({
                "Text": "Choose your Divine Domain (Cleric subclass).",
                "Options": self.CLERIC_SUBCLASSES,
                "Function": self._set_subclass,
            })
        elif level == 5:
            character.special_traits.append(
                "Sear Undead: When you use Turn Undead, undead that aren't turned "
                "take Radiant damage equal to your Wisdom modifier (minimum 1)."
            )
        elif level == 7:
            character.special_traits.append(
                "Blessed Strikes: When a cantrip damages a creature or you hit with a weapon "
                "attack, you can deal an extra 1d8 Radiant or Necrotic damage once per turn."
            )
        elif level == 10:
            character.special_abilities.append(Spell(
                name="Divine Intervention",
                casting_time="Action", range_="Self", components=[],
                duration="Instantaneous",
                description=(
                    "You call on your deity to intervene. You can cast any Cleric spell "
                    "without expending a spell slot or requiring material components."
                ),
                uses_left=1, cooldown="Long Rest",
            ))
        elif level == 14:
            character.special_traits.append("Improved Blessed Strikes: Blessed Strikes damage increases to 2d8.")
        elif level == 20:
            character.special_abilities.append(Spell(
                name="Greater Divine Intervention",
                casting_time="Action", range_="Self", components=[],
                duration="Instantaneous",
                description=(
                    "You can cast any spell from the Divine Magic spell list without "
                    "expending a spell slot or requiring material components."
                ),
                uses_left=1, cooldown="Long Rest",
            ))
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.completed_levelup_to = level

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
                "Text": "Choose 2 skills: History, Insight, Medicine, Persuasion, Religion.",
                "Options": ["History", "Insight", "Medicine", "Persuasion", "Religion"],
                "Choices": 2,
                "Function": self._set_skill_proficiencies,
            },
            {
                "Text": (
                    "Choose Divine Order: Protector (Heavy Armor + Martial Weapon proficiency) "
                    "or Thaumaturge (choose 2 skills from Arcana, History, Nature, Religion)."
                ),
                "Options": ["Protector", "Thaumaturge", "Arcana", "History", "Nature", "Religion"],
                "Function": self._apply_divine_order,
            },
        ])
        return character

    def level_up(self, character: Character):
        self.level += 1
        self._apply_level(character, self.level)
        character.classes = [cls for cls in character.classes if cls.name != self.name] + [self]
        return character


# ── Druid ──────────────────────────────────────────────────────────────────

class Druid(Class):
    DRUID_SUBCLASSES = ["Circle of the Land", "Circle of the Moon", "Circle of the Sea", "Circle of the Stars"]

    def __init__(self, level):
        super().__init__(name="Druid", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 8
        self.primary_ability = "Wisdom"
        self.spellcasting_ability = "Wisdom"
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.proficiencies["Armor"] = ["Light", "Medium", "Shield"]
        self.proficiencies["Weapons"] = ["Simple"]
        self.proficiencies["Tools"] = ["Herbalism Kit"]
        self.proficiencies["Saving Throws"] = ["Intelligence", "Wisdom"]
        self.proficiencies["Skills"] = []
        self.wild_shape_uses = 2
        self.completed_levelup_to = 1

    def _set_skill_proficiencies(self, character: Character, choices):
        character.proficiencies["Skills"] += choices

    def _set_subclass(self, character: Character, choices):
        self.subclass = choices[0]

    def _apply_primal_order(self, character: Character, choices):
        if "Warden" in choices:
            character.proficiencies["Armor"] += ["Heavy"]
            character.proficiencies["Weapons"] += ["Martial"]
        else:
            character.proficiencies["Skills"] += choices[1:]

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 50
        else:
            character.add_item([LeatherArmor(), Shield(), Sickle(), DruidicFocus(), HerbalismKit(), ExplorersPack()])

    def _apply_level(self, character: Character, level: int):
        if level == 2:
            character.special_abilities.append(Spell(
                name="Wild Shape",
                casting_time="Bonus Action", range_="Self", components=[],
                duration="Concentration, up to 1 hour",
                description=(
                    "You magically assume the shape of a Beast with a Challenge Rating "
                    "equal to or less than your allowed CR (1/4 at level 2, 1/2 at level 4, "
                    "1 at level 8). You retain your mental ability scores and can't cast "
                    "spells while transformed."
                ),
                uses_left=2, cooldown="Short Rest",
            ))
            character.todo.append({
                "Text": "Choose your Druid subclass (Druid Circle).",
                "Options": self.DRUID_SUBCLASSES,
                "Function": self._set_subclass,
            })
        elif level == 3:
            character.special_traits.append(
                "Wild Resurgence: Once per turn, if you have no Wild Shape uses, you can expend "
                "a spell slot to regain one use. If you have no spell slots, you can expend a "
                "Wild Shape use to regain one 1st-level spell slot."
            )
        elif level == 7:
            character.special_traits.append(
                "Elemental Fury: Choose Cold, Fire, Lightning, or Thunder. "
                "Once per turn your cantrip or melee attack deals an extra 1d6 damage of that type."
            )
        elif level == 18:
            character.special_traits.append(
                "Beast Spells: You can cast Druid spells while in Wild Shape form, "
                "using verbal and somatic components but not material ones."
            )
        elif level == 20:
            character.special_traits.append(
                "Archdruid: Unlimited Wild Shape uses per day. "
                "You can ignore Concentration for one Wild Shape spell at a time."
            )
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.completed_levelup_to = level

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
                    "(Leather Armor, Shield, Sickle, Druidic Focus, Herbalism Kit, Explorer's Pack) or (50 GP)"
                ),
                "Options": ["Starting Equipment", "Gold"],
                "Function": self.select_starting_equipment,
            },
            {
                "Text": "Choose 2 skills: Arcana, Animal Handling, Insight, Medicine, Nature, Perception, Religion, Survival.",
                "Options": ["Arcana", "Animal Handling", "Insight", "Medicine", "Nature", "Perception", "Religion", "Survival"],
                "Choices": 2,
                "Function": self._set_skill_proficiencies,
            },
            {
                "Text": (
                    "Choose Primal Order: Warden (Heavy Armor + Martial Weapon proficiency) "
                    "or Magician (choose 2 skills from Arcana, History, Nature, Religion)."
                ),
                "Options": ["Warden", "Magician", "Arcana", "History", "Nature", "Religion"],
                "Function": self._apply_primal_order,
            },
        ])
        return character

    def level_up(self, character: Character):
        self.level += 1
        self._apply_level(character, self.level)
        character.classes = [cls for cls in character.classes if cls.name != self.name] + [self]
        return character

# ── Fighter ────────────────────────────────────────────────────────────────

class Fighter(Class):
    FIGHTER_SUBCLASSES = ["Battle Master", "Champion", "Eldritch Knight", "Psi Warrior"]

    def __init__(self, level):
        super().__init__(name="Fighter", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 10
        self.primary_ability = "Strength or Dexterity"
        self.proficiencies["Armor"] = ["Light", "Medium", "Heavy", "Shield"]
        self.proficiencies["Weapons"] = ["Simple", "Martial"]
        self.proficiencies["Saving Throws"] = ["Strength", "Constitution"]
        self.proficiencies["Skills"] = []
        self.completed_levelup_to = 1

    def _set_skill_proficiencies(self, character: Character, choices):
        character.proficiencies["Skills"] += choices

    def _set_subclass(self, character: Character, choices):
        self.subclass = choices[0]

    def _apply_fighting_style(self, character: Character, choices):
        character.special_traits.append(f"Fighting Style: {choices[0]}")

    def _apply_weapon_mastery(self, character: Character, choices):
        character.weapon_mastery += choices

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 155
        else:
            character.add_item([ChainMail(), Flail(), Shield(), LightCrossbow(), Bolts(quantity=20), DungeoneersPack()])
            character.gold += 4

    def _apply_level(self, character: Character, level: int):
        if level == 2:
            character.special_abilities.append(Spell(
                name="Action Surge",
                casting_time="Bonus Action", range_="Self", components=[],
                duration="Instantaneous",
                description="On your turn, take one additional action on top of your regular action and possible bonus action.",
                uses_left=1, cooldown="Short Rest",
            ))
        elif level == 3:
            character.todo.append({
                "Text": "Choose your Fighter subclass (Martial Archetype).",
                "Options": self.FIGHTER_SUBCLASSES,
                "Function": self._set_subclass,
            })
        elif level == 5:
            character.special_traits.append("Extra Attack: You can attack twice when you take the Attack action.")
        elif level == 9:
            character.special_abilities.append(Spell(
                name="Indomitable",
                casting_time="Free Action", range_="Self", components=[],
                duration="Instantaneous",
                description="When you fail a saving throw, you can reroll it using the new result.",
                uses_left=1, cooldown="Long Rest",
            ))
            character.special_traits.append(
                "Tactical Master: When you use Weapon Mastery, you can swap one mastery property for Push, Sap, or Slow."
            )
        elif level == 11:
            character.special_traits.append("Extra Attack (2): You can attack three times when you take the Attack action.")
        elif level == 13:
            character.special_traits.append(
                "Studied Attacks: If you miss an attack, you have Advantage on your next attack "
                "roll against that same creature before the end of your next turn."
            )
        elif level == 17:
            for ability in character.special_abilities:
                if ability.name in ("Action Surge", "Indomitable"):
                    ability.uses_left = 2
        elif level == 20:
            character.special_traits.append("Extra Attack (3): You can attack four times when you take the Attack action.")
            for ability in character.special_abilities:
                if ability.name == "Indomitable":
                    ability.uses_left = 3
        self.completed_levelup_to = level

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        self.completed_levelup_to = 1
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        character.special_abilities.append(Spell(
            name="Second Wind",
            casting_time="Bonus Action", range_="Self", components=[],
            duration="Instantaneous",
            description="Regain HP equal to 1d10 + your Fighter level. Usable twice per Short Rest.",
            uses_left=2, cooldown="Short Rest",
        ))
        for lv in range(2, self.level + 1):
            self._apply_level(character, lv)
        character.todo.extend([
            {
                "Text": (
                    "Select starting equipment or gold: "
                    "(Chain Mail, Flail, Shield, Light Crossbow, 20 Bolts, Dungeoneer's Pack, 4 GP) or (155 GP)"
                ),
                "Options": ["Starting Equipment", "Gold"],
                "Function": self.select_starting_equipment,
            },
            {
                "Text": "Choose 2 skills: Acrobatics, Animal Handling, Athletics, History, Insight, Intimidation, Perception, Survival.",
                "Options": ["Acrobatics", "Animal Handling", "Athletics", "History", "Insight", "Intimidation", "Perception", "Survival"],
                "Choices": 2,
                "Function": self._set_skill_proficiencies,
            },
            {
                "Text": "Choose a Fighting Style.",
                "Options": _FIGHTING_STYLES,
                "Function": self._apply_fighting_style,
            },
            {
                "Text": "Choose 3 weapons to gain Weapon Mastery in.",
                "Options": ["Battleaxe", "Flail", "Glaive", "Greataxe", "Greatsword", "Halberd", "Handaxe", "Javelin", "Lance", "Light Hammer", "Longsword", "Maul", "Morningstar", "Pike", "Rapier", "Scimitar", "Shortsword", "Trident", "Warhammer", "War Pick", "Whip", "Light Crossbow", "Hand Crossbow", "Heavy Crossbow", "Longbow", "Shortbow"],
                "Choices": 3,
                "Function": self._apply_weapon_mastery,
            },
        ])
        return character

    def level_up(self, character: Character):
        self.level += 1
        self._apply_level(character, self.level)
        character.classes = [cls for cls in character.classes if cls.name != self.name] + [self]
        return character


# ── Monk ───────────────────────────────────────────────────────────────────

class Monk(Class):
    MONK_SUBCLASSES = [
        "Warrior of the Elements", "Warrior of Mercy",
        "Warrior of Shadow", "Warrior of the Open Hand",
    ]
    MARTIAL_ARTS_DIE = {
        **{lv: "1d6"  for lv in range(1,  5)},
        **{lv: "1d8"  for lv in range(5,  11)},
        **{lv: "1d10" for lv in range(11, 17)},
        **{lv: "1d12" for lv in range(17, 21)},
    }

    def __init__(self, level):
        super().__init__(name="Monk", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 8
        self.primary_ability = "Dexterity and Wisdom"
        self.proficiencies["Weapons"] = ["Simple", "Martial"]
        self.proficiencies["Saving Throws"] = ["Strength", "Dexterity"]
        self.proficiencies["Skills"] = []
        self.focus_points = level
        self.completed_levelup_to = 1

    def _set_skill_proficiencies(self, character: Character, choices):
        character.proficiencies["Skills"] += choices

    def _set_subclass(self, character: Character, choices):
        self.subclass = choices[0]

    def _apply_tool_proficiency(self, character: Character, choices):
        character.proficiencies["Tools"] += choices

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 50
        else:
            character.add_item([Shortsword(), DungeoneersPack()])
            character.gold += 11

    def _apply_level(self, character: Character, level: int):
        if level == 2:
            character.special_abilities.append(Spell(
                name="Flurry of Blows",
                casting_time="Bonus Action", range_="Self", components=[],
                duration="Instantaneous",
                description="Immediately after the Attack action, make two Unarmed Strikes as a Bonus Action.",
            ))
            character.special_traits.append(
                f"Monk's Focus: You have {level} Focus Points (regain on Short Rest). "
                "Patient Defense (1 FP: Dodge as Bonus Action). "
                "Step of the Wind (1 FP: Dash or Disengage as Bonus Action, jump doubled)."
            )
        elif level == 3:
            character.special_abilities.append(Spell(
                name="Deflect Attacks",
                casting_time="Reaction", range_="Self", components=[],
                duration="Instantaneous",
                description=(
                    "When you take Bludgeoning, Piercing, or Slashing damage, reduce it by "
                    "1d10 + Dex modifier + Monk level. If reduced to 0, spend 1 FP to redirect "
                    "it as a ranged attack (20/60 ft)."
                ),
            ))
            character.todo.append({
                "Text": "Choose your Monk subclass (Monastic Tradition).",
                "Options": self.MONK_SUBCLASSES,
                "Function": self._set_subclass,
            })
        elif level == 4:
            character.special_traits.append("Slow Fall: Reduce fall damage by 5 x your Monk level.")
        elif level == 5:
            character.special_traits.append("Extra Attack: You can attack twice when you take the Attack action.")
            character.special_traits.append(
                "Stunning Strike: When you hit with a Monk weapon or Unarmed Strike, spend 1 FP "
                "to force a Con save or the target is Stunned until the start of your next turn."
            )
        elif level == 6:
            character.special_traits.append("Empowered Strikes: Your Unarmed Strikes count as magical for overcoming resistance.")
        elif level == 7:
            character.special_traits.append("Evasion: On a Dex save for half damage, take none on success and half on failure.")
            character.special_traits.append("Self-Restoration: At the start of your turn, end one Frightened, Poisoned, or Prone condition on yourself.")
        elif level == 9:
            character.special_traits.append("Acrobatic Movement: You can move along vertical surfaces and across liquids during your movement.")
        elif level == 13:
            character.special_traits.append("Deflect Energy: Deflect Attacks works against any damage type.")
        elif level == 14:
            character.proficiencies["Saving Throws"] = list(set(
                character.proficiencies["Saving Throws"] +
                ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
            ))
            character.special_traits.append("Disciplined Survivor: You gain proficiency in all saving throws.")
        elif level == 15:
            character.special_traits.append(
                "Perfect Focus: When you roll Initiative with fewer than 4 Focus Points, "
                "you regain FP until you have 4."
            )
        elif level == 18:
            character.special_abilities.append(Spell(
                name="Superior Defense",
                casting_time="Bonus Action", range_="Self", components=[],
                duration="1 minute",
                description="Gain resistance to all damage except Psychic for 1 minute.",
                uses_left=1, cooldown="Short Rest",
            ))
        elif level == 20:
            character.special_traits.append(
                "Body and Mind: Dexterity and Wisdom each increase by 4 (maximum 25). "
                "Focus Point maximum increases by 4."
            )
        self.focus_points = level
        self.completed_levelup_to = level

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        self.completed_levelup_to = 1
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        ma_die = self.MARTIAL_ARTS_DIE[self.level]
        character.special_traits.append(
            f"Martial Arts: Unarmed Strikes and Monk weapons deal {ma_die} damage. "
            "Use Dexterity for attack/damage. After the Attack action, make one Unarmed Strike as a Bonus Action."
        )
        character.special_traits.append(
            "Unarmored Defense: AC = 10 + Dexterity modifier + Wisdom modifier (no armor or shield)."
        )
        character.special_traits.append("Unarmored Movement: Your speed increases by 10 feet while unarmored and unshielded.")
        for lv in range(2, self.level + 1):
            self._apply_level(character, lv)
        character.todo.extend([
            {
                "Text": "Select starting equipment or gold: (Shortsword, Dungeoneer's Pack, 11 GP) or (50 GP)",
                "Options": ["Starting Equipment", "Gold"],
                "Function": self.select_starting_equipment,
            },
            {
                "Text": "Choose 2 skills: Acrobatics, Athletics, History, Insight, Religion, Stealth.",
                "Options": ["Acrobatics", "Athletics", "History", "Insight", "Religion", "Stealth"],
                "Choices": 2,
                "Function": self._set_skill_proficiencies,
            },
            {
                "Text": "Choose 1 tool proficiency: an Artisan's Tool or Musical Instrument.",
                "Options": artisans_tools + ["Bagpipes", "Drum", "Dulcimer", "Flute", "Horn", "Lute", "Lyre", "Pan Flute", "Shawm", "Viol"],
                "Function": self._apply_tool_proficiency,
            },
        ])
        return character

    def level_up(self, character: Character):
        self.level += 1
        self._apply_level(character, self.level)
        character.classes = [cls for cls in character.classes if cls.name != self.name] + [self]
        return character


# ── Paladin ────────────────────────────────────────────────────────────────

class Paladin(Class):
    PALADIN_SUBCLASSES = ["Oath of Devotion", "Oath of Glory", "Oath of the Ancients", "Oath of Vengeance"]
    PALADIN_FIGHTING_STYLES = [
        "Blessed Warrior", "Blind Fighting", "Defense",
        "Dueling", "Great Weapon Fighting", "Interception", "Protection",
    ]

    def __init__(self, level):
        super().__init__(name="Paladin", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 10
        self.primary_ability = "Strength and Charisma"
        self.spellcasting_ability = "Charisma"
        self.spell_slots = dict(_HALF_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_HALF_CASTER_SLOTS[level - 1])
        self.proficiencies["Armor"] = ["Light", "Medium", "Heavy", "Shield"]
        self.proficiencies["Weapons"] = ["Simple", "Martial"]
        self.proficiencies["Saving Throws"] = ["Wisdom", "Charisma"]
        self.proficiencies["Skills"] = []
        self.lay_on_hands_pool = 5 * level
        self.completed_levelup_to = 1

    def _set_skill_proficiencies(self, character: Character, choices):
        character.proficiencies["Skills"] += choices

    def _set_subclass(self, character: Character, choices):
        self.subclass = choices[0]

    def _apply_fighting_style(self, character: Character, choices):
        character.special_traits.append(f"Fighting Style: {choices[0]}")

    def _apply_weapon_mastery(self, character: Character, choices):
        character.weapon_mastery += choices

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 150
        else:
            character.add_item([ChainMail(), Shield(), Longsword(), HolySymbol(), ScholarsPack()])
            character.gold += 9

    def _apply_level(self, character: Character, level: int):
        if level == 2:
            character.special_traits.append(
                "Paladin's Smite: When you hit with a melee weapon or Unarmed Strike, expend a spell slot "
                "(Bonus Action) for extra Radiant damage: 2d8 for a 1st-level slot, +1d8 per slot level above 1st."
            )
            character.todo.append({
                "Text": "Choose a Paladin Fighting Style.",
                "Options": self.PALADIN_FIGHTING_STYLES,
                "Function": self._apply_fighting_style,
            })
        elif level == 3:
            character.special_traits.append("Divine Health: You are immune to disease.")
            character.special_abilities.append(Spell(
                name="Channel Divinity",
                casting_time="Action", range_="Self", components=[],
                duration="Instantaneous",
                description=(
                    "Channel divine energy for an effect from your Sacred Oath. "
                    "Sacred Weapon (Devotion): Imbue a weapon with +Cha modifier to attack rolls "
                    "and bright light (20 ft) for 10 minutes."
                ),
                uses_left=2, cooldown="Short Rest",
            ))
            character.todo.append({
                "Text": "Choose your Paladin subclass (Sacred Oath).",
                "Options": self.PALADIN_SUBCLASSES,
                "Function": self._set_subclass,
            })
        elif level == 5:
            character.special_traits.append("Extra Attack: You can attack twice when you take the Attack action.")
            character.special_traits.append("Faithful Steed: Cast Find Steed without expending a spell slot.")
        elif level == 6:
            cha_mod = max(1, (character.ability_scores.get("Charisma", 10) - 10) // 2)
            character.special_traits.append(
                f"Aura of Protection: You and friendly creatures within 10 feet add +{cha_mod} "
                "(your Charisma modifier) to all saving throws while you are conscious."
            )
        elif level == 7:
            character.special_traits.append(
                "Aura of Courage: You and friendly creatures within 10 feet are immune to the "
                "Frightened condition while you are conscious."
            )
        elif level == 9:
            character.special_traits.append(
                "Abjure Foes: Use Channel Divinity to frighten Fiends and Undead within 60 feet "
                "(Wisdom save or Frightened for 1 minute with speed 0)."
            )
        elif level == 11:
            character.special_traits.append(
                "Radiant Strikes: Melee weapon attacks and Unarmed Strikes deal an extra 1d8 Radiant damage."
            )
        elif level == 14:
            character.special_traits.append(
                "Restoring Touch: When you use Lay on Hands, also remove one of: "
                "Blinded, Charmed, Deafened, Frightened, Paralyzed, or Stunned."
            )
        elif level == 18:
            character.special_traits.append("Aura Expansion: Aura of Protection and Aura of Courage extend to 30 feet.")
        self.spell_slots = dict(_HALF_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_HALF_CASTER_SLOTS[level - 1])
        self.lay_on_hands_pool = 5 * level
        self.completed_levelup_to = level

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        self.completed_levelup_to = 1
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        character.special_abilities.append(Spell(
            name="Lay on Hands",
            casting_time="Action", range_="Touch", components=[],
            duration="Instantaneous",
            description=(
                f"You have a pool of {self.lay_on_hands_pool} HP (restored on Long Rest). "
                "Restore HP to a creature you touch, or spend 5 HP to cure one disease or "
                "neutralize one poison."
            ),
            uses_left=self.lay_on_hands_pool, cooldown="Long Rest",
        ))
        for lv in range(2, self.level + 1):
            self._apply_level(character, lv)
        character.todo.extend([
            {
                "Text": (
                    "Select starting equipment or gold: "
                    "(Chain Mail, Shield, Longsword, Holy Symbol, Scholar's Pack, 9 GP) or (150 GP)"
                ),
                "Options": ["Starting Equipment", "Gold"],
                "Function": self.select_starting_equipment,
            },
            {
                "Text": "Choose 2 skills: Athletics, Insight, Intimidation, Medicine, Persuasion, Religion.",
                "Options": ["Athletics", "Insight", "Intimidation", "Medicine", "Persuasion", "Religion"],
                "Choices": 2,
                "Function": self._set_skill_proficiencies,
            },
            {
                "Text": "Choose 2 weapons to gain Weapon Mastery in.",
                "Options": ["Battleaxe", "Flail", "Glaive", "Greataxe", "Greatsword", "Halberd", "Handaxe", "Lance", "Longsword", "Maul", "Morningstar", "Pike", "Rapier", "Scimitar", "Shortsword", "Trident", "Warhammer", "War Pick", "Whip"],
                "Choices": 2,
                "Function": self._apply_weapon_mastery,
            },
        ])
        return character

    def level_up(self, character: Character):
        self.level += 1
        self._apply_level(character, self.level)
        character.classes = [cls for cls in character.classes if cls.name != self.name] + [self]
        return character

# ── Ranger ─────────────────────────────────────────────────────────────────

class Ranger(Class):
    RANGER_SUBCLASSES = ["Beast Master", "Fey Wanderer", "Gloom Stalker", "Hunter"]
    RANGER_FIGHTING_STYLES = [
        "Archery", "Blind Fighting", "Defense", "Druidic Warrior",
        "Thrown Weapon Fighting", "Two-Weapon Fighting",
    ]
    FAVORED_ENEMY_TYPES = [
        "Aberrations", "Beasts", "Celestials", "Constructs", "Dragons",
        "Elementals", "Fey", "Fiends", "Giants", "Monstrosities",
        "Oozes", "Plants", "Undead",
    ]

    def __init__(self, level):
        super().__init__(name="Ranger", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 10
        self.primary_ability = "Dexterity or Wisdom"
        self.spellcasting_ability = "Wisdom"
        self.spell_slots = dict(_HALF_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_HALF_CASTER_SLOTS[level - 1])
        self.proficiencies["Armor"] = ["Light", "Medium", "Shield"]
        self.proficiencies["Weapons"] = ["Simple", "Martial"]
        self.proficiencies["Saving Throws"] = ["Strength", "Dexterity"]
        self.proficiencies["Skills"] = []
        self.completed_levelup_to = 1

    def _set_skill_proficiencies(self, character: Character, choices):
        character.proficiencies["Skills"] += choices

    def _set_subclass(self, character: Character, choices):
        self.subclass = choices[0]

    def _apply_fighting_style(self, character: Character, choices):
        character.special_traits.append(f"Fighting Style: {choices[0]}")

    def _apply_weapon_mastery(self, character: Character, choices):
        character.weapon_mastery += choices

    def _apply_favored_enemy(self, character: Character, choices):
        character.special_traits.append(
            f"Favored Enemy: {choices[0]}. You have Advantage on Wisdom saving throws against "
            f"{choices[0]} and can always get a Hunter's Mark against them (no slot expended, 1/long rest)."
        )

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 150
        else:
            character.add_item([StuddedLeatherArmor(), Shortsword(quantity=2), Longbow(), Quiver(), Arrows(quantity=20), ExplorersPack()])
            character.gold += 7

    def _apply_level(self, character: Character, level: int):
        if level == 2:
            character.todo.append({
                "Text": "Choose a Ranger Fighting Style.",
                "Options": self.RANGER_FIGHTING_STYLES,
                "Function": self._apply_fighting_style,
            })
            character.special_traits.append(
                "Deft Explorer: Gain Expertise in one skill you are proficient in. "
                "Also gain one of: Climb speed equals movement, Swim speed equals movement, "
                "or difficult terrain in natural environments doesn't cost extra movement."
            )
        elif level == 3:
            character.todo.append({
                "Text": "Choose your Ranger subclass (Ranger Archetype).",
                "Options": self.RANGER_SUBCLASSES,
                "Function": self._set_subclass,
            })
            character.special_traits.append(
                "Tireless: As a Bonus Action, gain 1d8 + Wisdom modifier Temporary HP. "
                "Usable a number of times equal to your Proficiency Bonus per Short Rest."
            )
        elif level == 5:
            character.special_traits.append("Extra Attack: You can attack twice when you take the Attack action.")
        elif level == 6:
            character.special_traits.append("Roving: Your speed increases by 10 feet. You gain Climb and Swim speeds equal to your movement speed.")
        elif level == 9:
            character.special_traits.append("Conjure Barrage: You can cast Conjure Barrage without expending a spell slot (once per Short Rest).")
        elif level == 14:
            character.special_abilities.append(Spell(
                name="Nature's Veil",
                casting_time="Bonus Action", range_="Self", components=[],
                duration="Until the start of your next turn",
                description="You become Invisible until the start of your next turn.",
                uses_left=None, cooldown=None,
            ))
            character.special_traits.append("Nature's Veil: Become Invisible as a Bonus Action (uses = Proficiency Bonus per Long Rest).")
        elif level == 17:
            character.special_traits.append(
                "Precise Hunter: You have Advantage on attack rolls against creatures marked "
                "by your Hunter's Mark."
            )
        elif level == 18:
            character.special_traits.append(
                "Feral Senses: You don't have Disadvantage on attack rolls against creatures you "
                "can't see. You are also aware of invisible creatures within 30 feet."
            )
        elif level == 20:
            character.special_traits.append(
                "Foe Slayer: Once per turn, add your Wisdom modifier to the attack roll or damage "
                "roll of an attack against your Favored Enemy."
            )
        self.spell_slots = dict(_HALF_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_HALF_CASTER_SLOTS[level - 1])
        self.completed_levelup_to = level

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
                    "(Studded Leather Armor, 2 Shortswords, Longbow, Quiver, 20 Arrows, Explorer's Pack, 7 GP) or (150 GP)"
                ),
                "Options": ["Starting Equipment", "Gold"],
                "Function": self.select_starting_equipment,
            },
            {
                "Text": "Choose 3 skills: Animal Handling, Athletics, Insight, Investigation, Nature, Perception, Stealth, Survival.",
                "Options": ["Animal Handling", "Athletics", "Insight", "Investigation", "Nature", "Perception", "Stealth", "Survival"],
                "Choices": 3,
                "Function": self._set_skill_proficiencies,
            },
            {
                "Text": "Choose 2 weapons to gain Weapon Mastery in.",
                "Options": ["Battleaxe", "Flail", "Glaive", "Greataxe", "Greatsword", "Halberd", "Handaxe", "Javelin", "Lance", "Light Hammer", "Longsword", "Maul", "Morningstar", "Pike", "Rapier", "Scimitar", "Shortsword", "Trident", "Warhammer", "War Pick", "Whip", "Light Crossbow", "Hand Crossbow", "Heavy Crossbow", "Longbow", "Shortbow"],
                "Choices": 2,
                "Function": self._apply_weapon_mastery,
            },
            {
                "Text": "Choose a Favored Enemy type.",
                "Options": self.FAVORED_ENEMY_TYPES,
                "Function": self._apply_favored_enemy,
            },
        ])
        return character

    def level_up(self, character: Character):
        self.level += 1
        self._apply_level(character, self.level)
        character.classes = [cls for cls in character.classes if cls.name != self.name] + [self]
        return character


# ── Rogue ──────────────────────────────────────────────────────────────────

class Rogue(Class):
    ROGUE_SUBCLASSES = ["Arcane Trickster", "Assassin", "Soulknife", "Thief"]
    SNEAK_ATTACK_DICE = [
        "1d6",  "1d6",  "2d6",  "2d6",  "3d6",  "3d6",
        "4d6",  "4d6",  "5d6",  "5d6",  "6d6",  "6d6",
        "7d6",  "7d6",  "8d6",  "8d6",  "9d6",  "9d6",
        "10d6", "10d6",
    ]

    def __init__(self, level):
        super().__init__(name="Rogue", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 8
        self.primary_ability = "Dexterity"
        self.proficiencies["Armor"] = ["Light"]
        self.proficiencies["Weapons"] = ["Simple", "Martial"]
        self.proficiencies["Tools"] = ["Thieves' Tools"]
        self.proficiencies["Saving Throws"] = ["Dexterity", "Intelligence"]
        self.proficiencies["Skills"] = []
        self.completed_levelup_to = 1

    def _set_skill_proficiencies(self, character: Character, choices):
        character.proficiencies["Skills"] += choices

    def _set_subclass(self, character: Character, choices):
        self.subclass = choices[0]

    def _apply_expertise(self, character: Character, choices):
        if not hasattr(character, "expertise"):
            character.expertise = []
        character.expertise += choices

    def _apply_weapon_mastery(self, character: Character, choices):
        character.weapon_mastery += choices

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 100
        else:
            character.add_item([Dagger(quantity=2), ThievesTools(), LeatherArmor(), BurglarsPack()])
            character.gold += 8

    def _apply_level(self, character: Character, level: int):
        sneak_dice = self.SNEAK_ATTACK_DICE[level - 1]
        for trait in character.special_traits:
            if "Sneak Attack" in trait:
                character.special_traits.remove(trait)
                break
        character.special_traits.append(
            f"Sneak Attack ({sneak_dice}): Once per turn, deal extra {sneak_dice} damage when "
            "you hit with a Finesse or Ranged weapon and have Advantage, or an ally is adjacent to the target."
        )
        if level == 2:
            character.special_traits.append(
                "Cunning Action: Dash, Disengage, or Hide as a Bonus Action on each of your turns."
            )
        elif level == 3:
            character.todo.append({
                "Text": "Choose your Rogue subclass (Roguish Archetype).",
                "Options": self.ROGUE_SUBCLASSES,
                "Function": self._set_subclass,
            })
            character.special_traits.append(
                "Steady Aim: As a Bonus Action, gain Advantage on your next attack roll this turn "
                "(your speed becomes 0 until the end of the turn)."
            )
        elif level == 5:
            character.special_traits.append(
                "Cunning Strike: When you deal Sneak Attack damage, you can forgo one Sneak Attack die "
                "for an effect: Disarm, Poison (Con save or Poisoned), Trip (Str save or Prone), "
                "or Withdraw (move up to half your speed without provoking opportunity attacks)."
            )
            character.special_abilities.append(Spell(
                name="Uncanny Dodge",
                casting_time="Reaction", range_="Self", components=[],
                duration="Instantaneous",
                description="When an attacker hits you with an attack roll, halve the attack's damage against you.",
            ))
        elif level == 6:
            character.todo.append({
                "Text": "Expertise (Level 6): Choose 2 more skills or tools to gain Expertise in.",
                "Options": list(dnd_skills.keys()) + ["Thieves' Tools"],
                "Choices": 2,
                "Function": self._apply_expertise,
            })
        elif level == 7:
            character.special_traits.append("Evasion: On a Dex save for half damage, take none on success and half on failure.")
            character.special_traits.append(
                "Reliable Talent: When you make an ability check using a skill or tool you are "
                "proficient in, treat any roll of 9 or lower as a 10."
            )
        elif level == 11:
            character.special_traits.append(
                "Improved Cunning Strike: You can use Cunning Strike without losing a Sneak Attack die."
            )
        elif level == 14:
            character.special_traits.append(
                "Devious Strikes: New Cunning Strike options — Daze (Con save or Incapacitated until "
                "end of their next turn), Knock Out (Con save or Unconscious for 1 minute), "
                "Obscure (Dex save or Blinded until end of their next turn)."
            )
        elif level == 15:
            if "Wisdom" not in character.proficiencies["Saving Throws"]:
                character.proficiencies["Saving Throws"].append("Wisdom")
            character.special_traits.append("Slippery Mind: You gain proficiency in Wisdom saving throws.")
        elif level == 18:
            character.special_traits.append(
                "Elusive: No attack roll has Advantage against you while you aren't Incapacitated."
            )
        elif level == 20:
            character.special_abilities.append(Spell(
                name="Stroke of Luck",
                casting_time="Free Action", range_="Self", components=[],
                duration="Instantaneous",
                description=(
                    "If you fail an ability check, turn it into a 20. "
                    "If you miss an attack roll, turn it into a hit."
                ),
                uses_left=1, cooldown="Long Rest",
            ))
        self.completed_levelup_to = level

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        self.completed_levelup_to = 1
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        character.special_traits.append(
            f"Sneak Attack ({self.SNEAK_ATTACK_DICE[0]}): Once per turn, deal extra "
            f"{self.SNEAK_ATTACK_DICE[0]} damage when you have Advantage or an ally is adjacent."
        )
        character.special_traits.append(
            "Thieves' Cant: You know Thieves' Cant — a secret mix of dialect, jargon, and code "
            "that lets you hide messages in seemingly normal conversation."
        )
        for lv in range(2, self.level + 1):
            self._apply_level(character, lv)
        character.todo.extend([
            {
                "Text": (
                    "Select starting equipment or gold: "
                    "(2 Daggers, Thieves' Tools, Leather Armor, Burglar's Pack, 8 GP) or (100 GP)"
                ),
                "Options": ["Starting Equipment", "Gold"],
                "Function": self.select_starting_equipment,
            },
            {
                "Text": "Choose 4 skills: Acrobatics, Athletics, Deception, Insight, Intimidation, Investigation, Perception, Persuasion, Sleight of Hand, Stealth.",
                "Options": ["Acrobatics", "Athletics", "Deception", "Insight", "Intimidation", "Investigation", "Perception", "Persuasion", "Sleight of Hand", "Stealth"],
                "Choices": 4,
                "Function": self._set_skill_proficiencies,
            },
            {
                "Text": "Expertise (Level 1): Choose 2 skills or Thieves' Tools to gain Expertise in (double proficiency bonus).",
                "Options": ["Acrobatics", "Athletics", "Deception", "Insight", "Intimidation", "Investigation", "Perception", "Persuasion", "Sleight of Hand", "Stealth", "Thieves' Tools"],
                "Choices": 2,
                "Function": self._apply_expertise,
            },
            {
                "Text": "Choose 2 weapons to gain Weapon Mastery in.",
                "Options": ["Dagger", "Dart", "Handaxe", "Javelin", "Light Hammer", "Mace", "Quarterstaff", "Sickle", "Spear", "Light Crossbow", "Shortbow", "Sling", "Hand Crossbow", "Rapier", "Scimitar", "Shortsword", "Whip"],
                "Choices": 2,
                "Function": self._apply_weapon_mastery,
            },
        ])
        return character

    def level_up(self, character: Character):
        self.level += 1
        self._apply_level(character, self.level)
        character.classes = [cls for cls in character.classes if cls.name != self.name] + [self]
        return character

# ── Sorcerer ───────────────────────────────────────────────────────────────

class Sorcerer(Class):
    SORCERER_SUBCLASSES = ["Aberrant Mind", "Clockwork Soul", "Draconic Sorcery", "Wild Magic"]
    METAMAGIC_OPTIONS = [
        "Careful Spell", "Distant Spell", "Empowered Spell", "Extended Spell",
        "Heightened Spell", "Quickened Spell", "Seeking Spell", "Subtle Spell",
        "Transmuted Spell", "Twinned Spell",
    ]
    CANTRIPS_KNOWN = [4, 4, 4, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6]

    def __init__(self, level):
        super().__init__(name="Sorcerer", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 6
        self.primary_ability = "Charisma"
        self.spellcasting_ability = "Charisma"
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.proficiencies["Weapons"] = ["Simple"]
        self.proficiencies["Saving Throws"] = ["Constitution", "Charisma"]
        self.proficiencies["Skills"] = []
        self.sorcery_points = level
        self.completed_levelup_to = 1

    def _set_skill_proficiencies(self, character: Character, choices):
        character.proficiencies["Skills"] += choices

    def _set_subclass(self, character: Character, choices):
        self.subclass = choices[0]

    def _apply_metamagic(self, character: Character, choices):
        if not hasattr(character, "metamagic"):
            character.metamagic = []
        character.metamagic += choices

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 50
        else:
            character.add_item([Dagger(quantity=2), ComponentPouch(), ArcaneFocus(), BurglarsPack()])
            character.gold += 28

    def _apply_level(self, character: Character, level: int):
        self.sorcery_points = level
        if level == 2:
            character.special_traits.append(
                f"Font of Magic: You have {level} Sorcery Points (regain on Long Rest). "
                "Convert spell slots to Sorcery Points (1 point per slot level) or vice versa "
                "(spend points equal to the slot level to create a slot, max 5th level)."
            )
            character.todo.append({
                "Text": "Choose 2 Metamagic options.",
                "Options": self.METAMAGIC_OPTIONS,
                "Choices": 2,
                "Function": self._apply_metamagic,
            })
        elif level == 3:
            character.todo.append({
                "Text": "Choose your Sorcerer subclass (Sorcerous Origin).",
                "Options": self.SORCERER_SUBCLASSES,
                "Function": self._set_subclass,
            })
            character.special_traits.append(
                "Sorcery Incarnate: While Innate Sorcery is active, you can apply two Metamagic "
                "options to a single spell instead of one."
            )
        elif level == 5:
            character.special_traits.append(
                "Sorcerous Restoration: When you finish a Short Rest, you regain 4 expended Sorcery Points."
            )
        elif level == 7:
            character.special_traits.append(
                "Arcane Apotheosis: While Innate Sorcery is active, once per turn you can apply "
                "one Metamagic option to a spell without spending Sorcery Points."
            )
        elif level == 10:
            character.todo.append({
                "Text": "Choose a 3rd Metamagic option.",
                "Options": self.METAMAGIC_OPTIONS,
                "Function": self._apply_metamagic,
            })
        elif level == 17:
            character.todo.append({
                "Text": "Choose a 4th Metamagic option.",
                "Options": self.METAMAGIC_OPTIONS,
                "Function": self._apply_metamagic,
            })
        elif level == 20:
            character.special_traits.append(
                "Arcane Apotheosis (Improved): While Innate Sorcery is active, you can apply any "
                "number of Metamagic options for free each turn."
            )
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.completed_levelup_to = level

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        self.completed_levelup_to = 1
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        character.special_abilities.append(Spell(
            name="Innate Sorcery",
            casting_time="Bonus Action", range_="Self", components=[],
            duration="1 minute",
            description=(
                "You emanate an aura of magical power. For 1 minute: you have Advantage on "
                "spell attack rolls, and creatures have Disadvantage on saving throws against "
                "your spells that deal damage."
            ),
            uses_left=1, cooldown="Long Rest",
        ))
        for lv in range(2, self.level + 1):
            self._apply_level(character, lv)
        character.todo.extend([
            {
                "Text": (
                    "Select starting equipment or gold: "
                    "(2 Daggers, Component Pouch, Arcane Focus, Burglar's Pack, 28 GP) or (50 GP)"
                ),
                "Options": ["Starting Equipment", "Gold"],
                "Function": self.select_starting_equipment,
            },
            {
                "Text": "Choose 2 skills: Arcana, Deception, Insight, Intimidation, Persuasion, Religion.",
                "Options": ["Arcana", "Deception", "Insight", "Intimidation", "Persuasion", "Religion"],
                "Choices": 2,
                "Function": self._set_skill_proficiencies,
            },
        ])
        return character

    def level_up(self, character: Character):
        self.level += 1
        self._apply_level(character, self.level)
        character.classes = [cls for cls in character.classes if cls.name != self.name] + [self]
        return character


# ── Warlock ────────────────────────────────────────────────────────────────

class Warlock(Class):
    WARLOCK_SUBCLASSES = ["Archfey Patron", "Celestial Patron", "Fiend Patron", "Great Old One Patron"]
    PACT_BOONS = ["Pact of the Blade", "Pact of the Chain", "Pact of the Tome"]
    ELDRITCH_INVOCATIONS = [
        "Agonizing Blast", "Armor of Shadows", "Ascendant Step", "Beast Speech",
        "Beguiling Influence", "Devil's Sight", "Eldritch Mind", "Eldritch Smite",
        "Eldritch Spear", "Eyes of the Rune Keeper", "Fiendish Vigor",
        "Gaze of Two Minds", "Ghostly Gaze", "Gift of the Depths",
        "Grasp of Hadar", "Investment of the Chain Master", "Lifedrinker",
        "Mask of Many Faces", "Master of Myriad Forms", "Misty Visions",
        "One with Shadows", "Otherworldly Leap", "Repelling Blast",
        "Sculptor of Flesh", "Thirsting Blade", "Undying Servitude",
        "Visions of Distant Realms", "Voice of the Chain Master", "Witch Sight",
    ]

    def __init__(self, level):
        super().__init__(name="Warlock", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 8
        self.primary_ability = "Charisma"
        self.spellcasting_ability = "Charisma"
        self.pact_slots = dict(_WARLOCK_PACT_SLOTS[level - 1])
        self.pact_slots_remaining = dict(_WARLOCK_PACT_SLOTS[level - 1])
        self.proficiencies["Armor"] = ["Light"]
        self.proficiencies["Weapons"] = ["Simple"]
        self.proficiencies["Saving Throws"] = ["Wisdom", "Charisma"]
        self.proficiencies["Skills"] = []
        self.completed_levelup_to = 1

    def _set_skill_proficiencies(self, character: Character, choices):
        character.proficiencies["Skills"] += choices

    def _set_subclass(self, character: Character, choices):
        self.subclass = choices[0]

    def _apply_invocations(self, character: Character, choices):
        if not hasattr(character, "eldritch_invocations"):
            character.eldritch_invocations = []
        character.eldritch_invocations += choices

    def _apply_pact_boon(self, character: Character, choices):
        boon = choices[0]
        character.special_traits.append(
            f"Pact Boon — {boon}: "
            + {
                "Pact of the Blade": "Create a pact weapon (any weapon) that uses your Charisma for attack/damage. Counts as magical.",
                "Pact of the Chain": "Cast Find Familiar as a ritual. Your familiar can be a special form (imp, pseudodragon, quasit, or sprite).",
                "Pact of the Tome": "Your patron gives you a Book of Shadows containing 3 cantrips from any class list and 2 1st-level rituals.",
            }.get(boon, "")
        )

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 100
        else:
            character.add_item([LeatherArmor(), Sickle(), ComponentPouch(), ArcaneFocus(), ScholarsPack()])
            character.gold += 15

    def _apply_level(self, character: Character, level: int):
        if level == 2:
            character.special_traits.append(
                "Magical Cunning: If all your Pact Magic spell slots are expended, you can perform "
                "a 1-minute ritual to regain half your maximum Pact slots (rounded up). "
                "Usable once per Long Rest."
            )
        elif level == 3:
            character.todo.append({
                "Text": "Choose your Warlock subclass (Otherworldly Patron).",
                "Options": self.WARLOCK_SUBCLASSES,
                "Function": self._set_subclass,
            })
            character.todo.append({
                "Text": "Choose your Pact Boon.",
                "Options": self.PACT_BOONS,
                "Function": self._apply_pact_boon,
            })
        elif level == 5:
            character.special_traits.append(
                "Contact Patron: You can cast Commune as a ritual to contact your patron (no spell slot required)."
            )
        elif level == 7:
            character.todo.append({
                "Text": "Choose an additional Eldritch Invocation.",
                "Options": self.ELDRITCH_INVOCATIONS,
                "Function": self._apply_invocations,
            })
        elif level == 11:
            character.special_traits.append(
                "Mystic Arcanum (6th): Choose one 6th-level spell from the Warlock list. "
                "Cast it once without expending a spell slot (regain on Long Rest)."
            )
        elif level == 13:
            character.special_traits.append(
                "Mystic Arcanum (7th): Choose one 7th-level spell. Cast it once per Long Rest for free."
            )
        elif level == 15:
            character.special_traits.append(
                "Mystic Arcanum (8th): Choose one 8th-level spell. Cast it once per Long Rest for free."
            )
        elif level == 17:
            character.special_traits.append(
                "Mystic Arcanum (9th): Choose one 9th-level spell. Cast it once per Long Rest for free."
            )
        elif level == 18:
            character.special_traits.append(
                "Eldritch Master: Spend 1 minute communing with your patron to regain all expended "
                "Pact Magic slots. Usable once per Long Rest."
            )
        elif level == 20:
            character.special_traits.append(
                "Hex Master: You can cast Hex at will without expending a spell slot."
            )
        self.pact_slots = dict(_WARLOCK_PACT_SLOTS[level - 1])
        self.pact_slots_remaining = dict(_WARLOCK_PACT_SLOTS[level - 1])
        self.completed_levelup_to = level

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        self.completed_levelup_to = 1
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        pact_level = list(self.pact_slots.keys())[0]
        pact_count = list(self.pact_slots.values())[0]
        character.special_traits.append(
            f"Pact Magic: You have {pact_count} {pact_level}th-level spell slot(s) that recharge on a Short Rest."
        )
        for lv in range(2, self.level + 1):
            self._apply_level(character, lv)
        character.todo.extend([
            {
                "Text": (
                    "Select starting equipment or gold: "
                    "(Leather Armor, Sickle, Component Pouch, Arcane Focus, Scholar's Pack, 15 GP) or (100 GP)"
                ),
                "Options": ["Starting Equipment", "Gold"],
                "Function": self.select_starting_equipment,
            },
            {
                "Text": "Choose 2 skills: Arcana, Deception, History, Intimidation, Investigation, Nature, Religion.",
                "Options": ["Arcana", "Deception", "History", "Intimidation", "Investigation", "Nature", "Religion"],
                "Choices": 2,
                "Function": self._set_skill_proficiencies,
            },
            {
                "Text": "Choose 2 Eldritch Invocations.",
                "Options": self.ELDRITCH_INVOCATIONS,
                "Choices": 2,
                "Function": self._apply_invocations,
            },
        ])
        return character

    def level_up(self, character: Character):
        self.level += 1
        self._apply_level(character, self.level)
        character.classes = [cls for cls in character.classes if cls.name != self.name] + [self]
        return character


# ── Wizard ─────────────────────────────────────────────────────────────────

class Wizard(Class):
    WIZARD_SUBCLASSES = ["Abjurer", "Diviner", "Evoker", "Illusionist"]
    CANTRIPS_KNOWN = [3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5]

    def __init__(self, level):
        super().__init__(name="Wizard", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 6
        self.primary_ability = "Intelligence"
        self.spellcasting_ability = "Intelligence"
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.proficiencies["Weapons"] = ["Simple"]
        self.proficiencies["Saving Throws"] = ["Intelligence", "Wisdom"]
        self.proficiencies["Skills"] = []
        self.completed_levelup_to = 1

    def _set_skill_proficiencies(self, character: Character, choices):
        character.proficiencies["Skills"] += choices

    def _set_subclass(self, character: Character, choices):
        self.subclass = choices[0]

    def _apply_expertise(self, character: Character, choices):
        if not hasattr(character, "expertise"):
            character.expertise = []
        character.expertise += choices

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 110
        else:
            character.add_item([Quarterstaff(), ArcaneFocus(), ComponentPouch(), ScholarsPack()])
            character.gold += 5
            character.special_traits.append(
                "Spellbook: You have a spellbook containing 6 1st-level Wizard spells of your choice."
            )

    def _apply_level(self, character: Character, level: int):
        if level == 2:
            character.todo.append({
                "Text": "Choose your Wizard subclass (Arcane Tradition).",
                "Options": self.WIZARD_SUBCLASSES,
                "Function": self._set_subclass,
            })
            character.todo.append({
                "Text": "Scholar: Choose 1 skill to gain Expertise in (Arcana or History).",
                "Options": ["Arcana", "History"],
                "Function": self._apply_expertise,
            })
            character.special_traits.append(
                "Memorize Spell: Once per day you can study a spell from another Wizard's spellbook "
                "and add it to your own without the usual gold cost."
            )
        elif level == 3:
            character.special_traits.append(
                "Cantrip Formulas: During a Short Rest, you can replace one Wizard cantrip you know "
                "with another Wizard cantrip."
            )
        elif level == 18:
            character.special_abilities.append(Spell(
                name="Spell Mastery",
                casting_time="Special", range_="Self", components=[],
                duration="Permanent",
                description=(
                    "Choose one 1st-level and one 2nd-level Wizard spell in your spellbook. "
                    "You can cast each of those spells at their lowest level without expending a spell slot. "
                    "You can change your chosen spells after a Long Rest."
                ),
            ))
        elif level == 20:
            character.special_abilities.append(Spell(
                name="Signature Spells",
                casting_time="Special", range_="Self", components=[],
                duration="Permanent",
                description=(
                    "Choose two 3rd-level Wizard spells in your spellbook as your signature spells. "
                    "You always have them prepared and can cast each of them once without expending "
                    "a spell slot (regain uses on Long Rest)."
                ),
                uses_left=2, cooldown="Long Rest",
            ))
        self.spell_slots = dict(_FULL_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_FULL_CASTER_SLOTS[level - 1])
        self.completed_levelup_to = level

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        self.completed_levelup_to = 1
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        arcane_recovery_slots = (self.level + 1) // 2
        character.special_abilities.append(Spell(
            name="Arcane Recovery",
            casting_time="Special", range_="Self", components=[],
            duration="Instantaneous",
            description=(
                f"Once per day during a Short Rest, you can recover expended spell slots "
                f"with a combined level up to {arcane_recovery_slots} (max 5th level each)."
            ),
            uses_left=1, cooldown="Long Rest",
        ))
        character.special_traits.append(
            "Spellbook: You possess a spellbook containing your prepared Wizard spells. "
            "You can prepare a number of spells equal to your Intelligence modifier + your Wizard level."
        )
        for lv in range(2, self.level + 1):
            self._apply_level(character, lv)
        character.todo.extend([
            {
                "Text": (
                    "Select starting equipment or gold: "
                    "(Quarterstaff, Arcane Focus, Component Pouch, Scholar's Pack, Spellbook, 5 GP) or (110 GP)"
                ),
                "Options": ["Starting Equipment", "Gold"],
                "Function": self.select_starting_equipment,
            },
            {
                "Text": "Choose 2 skills: Arcana, History, Insight, Investigation, Medicine, Religion.",
                "Options": ["Arcana", "History", "Insight", "Investigation", "Medicine", "Religion"],
                "Choices": 2,
                "Function": self._set_skill_proficiencies,
            },
        ])
        return character

    def level_up(self, character: Character):
        self.level += 1
        self._apply_level(character, self.level)
        character.classes = [cls for cls in character.classes if cls.name != self.name] + [self]
        return character
