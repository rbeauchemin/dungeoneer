from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.common import dnd_skills, artisans_tools
from src.classes._base import (
    Class, _FULL_CASTER_SLOTS, _HALF_CASTER_SLOTS,
    _WARLOCK_PACT_SLOTS, _FIGHTING_STYLES,
)


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
            character.special_traits.append("Slow Fall: Reduce fall damage by 5 × your Monk level.")
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

