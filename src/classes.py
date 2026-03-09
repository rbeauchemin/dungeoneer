from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.common import dnd_skills


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
