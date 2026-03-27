from src.creatures import Character


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

    def select_skills(self, character, choices, **kwargs):
        counter = {}
        for skill in choices:
            counter[skill] = counter.get(skill, 0) + 1
        if len(counter) == 1:
            print("You may not select the same skill twice. Please select again.")
            character.todo += [
                {
                    "Text": "Choose two skills to gain proficiency in.",
                    "Options": list(set(self.proficiencies["Skills"]) - set(character.proficiencies["Skills"])),
                    "Function": self.select_skills,
                    "Choices": 2,
                    "AllowSame": False
                }
            ]
            return
        else:
            for skill in counter:
                character.proficiencies["Skills"].append(skill)
        return character

    def apply_to_character(self, character: Character):
        character.proficiencies["Armor"] += self.proficiencies["Armor"]
        character.proficiencies["Weapons"] += self.proficiencies["Weapons"]
        character.proficiencies["Tools"] += self.proficiencies["Tools"]
        character.proficiencies["Saving Throws"] += self.proficiencies["Saving Throws"]
        return character

    def level_up(self, character: Character):
        self.level += 1
        # Insert class back where it was in the list of classes to preserve ordering (important for spellcasting progression)
        for i, cls in enumerate(character.classes):
            if cls.name == self.name:
                character.classes[i] = self
                break
        if self.level in [4, 8, 12, 16]:
            character.todo.append({
                "Text": "Choose an Ability Score Improvement or Feat.",
                "Options": ["Ability Score Improvement", "Feat"],
                "Function": self.select_ability_score_improvement_or_feat,
            })
            
        return character

    def select_ability_score_improvement_or_feat(self, character, choices, **kwargs):
        if choices[0] == "Ability Score Improvement":
            character.todo.append({
                "Text": "Choose two ability scores to increase by 1 (or one ability score to increase by 2).",
                "Options": ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"],
                "Function": self.select_ability_score_improvement,
                "Choices": 2,
                "AllowSame": True,
            })
        else:
            # TODO: Add correct feats based on character traits and whether they meet feat requirements
            character.todo.append({
                "Text": "Choose a feat.",
                "Options": ["Feat 1", "Feat 2", "Feat 3"],  # Placeholder, should be list of feats
                "Function": self.select_feat,
            })

    def select_ability_score_improvement(self, character, choices, **kwargs):
        counter = {}
        current_con = None
        if "Constitution" in choices:
            current_con = character.get_ability_score("Constitution")
        for ability in choices:
            counter[ability] = counter.get(ability, 0) + 1
        if len(counter) == 1:
            ability = choices[0]
            character.ability_scores[ability] += 2
        else:
            for ability in counter:
                character.ability_scores[ability] += 1
        if current_con and character.get_ability_score("Constitution") > current_con:
            # If Constitution increased, also increase max HP and current HP by 1 per character level
            hp_increase = character.level
            character.max_hp += hp_increase
            character.current_hp += hp_increase
        return character

    def select_feat(self, character, choices, **kwargs):
        feat = choices[0]
        character.feats.append(feat)
        return character


# ── Shared spell-slot tables ───────────────────────────────────────────────

_FULL_CASTER_SLOTS = [
    {1: 2},                                                      # Level 1
    {1: 3},                                                      # Level 2
    {1: 4, 2: 2},                                                # Level 3
    {1: 4, 2: 3},                                                # Level 4
    {1: 4, 2: 3, 3: 2},                                          # Level 5
    {1: 4, 2: 3, 3: 3},                                          # Level 6
    {1: 4, 2: 3, 3: 3, 4: 1},                                    # Level 7
    {1: 4, 2: 3, 3: 3, 4: 2},                                    # Level 8
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},                              # Level 9
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},                              # Level 10
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},                        # Level 11
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},                        # Level 12
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},                  # Level 13
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},                  # Level 14
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},            # Level 15
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},            # Level 16
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
    {1: 4, 2: 3, 3: 2},              # Level 9
    {1: 4, 2: 3, 3: 2},              # Level 10
    {1: 4, 2: 3, 3: 3},              # Level 11
    {1: 4, 2: 3, 3: 3},              # Level 12
    {1: 4, 2: 3, 3: 3, 4: 1},        # Level 13
    {1: 4, 2: 3, 3: 3, 4: 1},        # Level 14
    {1: 4, 2: 3, 3: 3, 4: 2},        # Level 15
    {1: 4, 2: 3, 3: 3, 4: 2},        # Level 16
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},  # Level 17
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},  # Level 18
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},  # Level 19
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},  # Level 20
]

_WARLOCK_PACT_SLOTS = [
    {1: 1}, {1: 2}, {2: 2}, {2: 2},  # Levels 1-4
    {3: 2}, {3: 2}, {4: 2}, {4: 2},  # Levels 5-8
    {5: 2}, {5: 2},                  # Levels 9-10
    {5: 3}, {5: 3}, {5: 3}, {5: 3},  # Levels 11-14
    {5: 3}, {5: 3},                  # Levels 15-16
    {5: 4}, {5: 4}, {5: 4}, {5: 4},  # Levels 17-20
]

_FIGHTING_STYLES = [
    "Archery", "Blind Fighting", "Defense", "Dueling",
    "Great Weapon Fighting", "Interception", "Protection",
    "Thrown Weapon Fighting", "Two-Weapon Fighting", "Unarmed Fighting",
]
