from typing import List, Optional
from src.creatures import Character
from src.common import damage_types, dnd_skills


class Condition:
    """Base condition class.

    Subclasses should override `apply` and `remove` to change a Character's
    traits. Each Condition instance stores any previous state it changes in
    `_prev_state` so `remove` can restore it.
    """

    def __init__(self, name: str, description: str = "", duration: Optional[int] = None):
        self.name = name
        self.description = description
        # duration in rounds; None means indefinite
        self.duration = duration
        # store previous values here for restoration
        self._prev_state = {}

    def apply(self, character: Character):
        """Apply the condition to `character`.

        This method should be idempotent: applying twice should not stack
        duplicate effects.
        """
        if self.name in character.active_effects:
            return
        character.active_effects.append(self)

    def remove(self, character: Character):
        """Remove the condition and restore prior character state."""
        if self.name in character.active_effects:
            character.active_effects = [e for e in character.active_effects if e.name != self.name]
        # subclasses should restore additional state using `_prev_state`


# Helper functions

def _add_unique(lst: List, val):
    if val not in lst:
        lst.append(val)


def _remove_safe(lst: List, val):
    if val in lst:
        lst.remove(val)


# Concrete conditions

class Blinded(Condition):
    def __init__(self, duration: Optional[int] = None):
        super().__init__("Blinded", "Can't see. Attack rolls have disadvantage; attacks against you have advantage; automatically fail checks that require sight.", duration)

    def apply(self, character: Character):
        # Attack rolls have disadvantage
        character.disadvantages["Attack"] = character.disadvantages.get("Attack", 0) + 1
        # Attacks against this character have advantage
        character.advantages["ToBeAttacked"] = character.advantages.get("ToBeAttacked", 0) + 1
        # record what we changed
        self._prev_state["disadv_attack_added"] = 1
        self._prev_state["adv_to_be_attacked_added"] = 1
        super().apply(character)

    def remove(self, character: Character):
        if self._prev_state.get("disadv_attack_added"):
            character.disadvantages["Attack"] = max(0, character.disadvantages.get("Attack", 0) - 1)
        if self._prev_state.get("adv_to_be_attacked_added"):
            character.advantages["ToBeAttacked"] = max(0, character.advantages.get("ToBeAttacked", 0) - 1)
        super().remove(character)


class Charmed(Condition):
    def __init__(self, duration: Optional[int] = None, by: Optional[Character] = None):
        super().__init__("Charmed", "Can't attack the charmer with damaging abilities or magical effects. The charmer has advantage on any ability check to interact with the affected character socially.")
        self.by = by

    def apply(self, character: Character):
        super().apply(character)
        # TODO: Add character-specific interaction effect in the dice roll if the roll is social

    def remove(self, character: Character):
        super().remove(character)


class Charming(Condition):
    def __init__(self, duration: Optional[int] = None, who: Optional[Character] = None):
        super().__init__("Charming", "The character that this character is charming cannot attack them. This character has advantage on social rolls against the target character.")
        self.who = who

    def apply(self, character: Character):
        super().apply(character)

    def remove(self, character: Character):
        super().remove(character)


class Dead(Condition):
    def __init__(self, duration: Optional[int] = None):
        super().__init__("Dead", "This character is dead. Only magic such as Revivify can bring them back.")

    def apply(self, character: Character):
        character.current_hp = 0
        super().apply(character)

    def remove(self, character: Character):
        # Returning to life removes one exhaustion level
        character.remove_condition("Exhaustion")
        character.current_hp = 1
        super().remove(character)


class Deafened(Condition):
    def __init__(self, duration: Optional[int] = None):
        super().__init__("Deafened", "Can't hear. Automatically fail checks that require hearing.", duration)
        # TODO Add side benefit: Automatically succeed against Vicious Mockery, Suggestion, Dissonant Whispers, Command, Compulsion, Enthrall, and Divine Word

    def apply(self, character: Character):
        # TODO: This is just a placeholder for now. Need to make these all checks that require hearing and for instant fail instead of disadvantage
        _add_unique(character.disadvantages.setdefault("Skills", []), "Perception")
        self._prev_state["added_perception_disadv"] = True
        super().apply(character)

    def remove(self, character: Character):
        if self._prev_state.get("added_perception_disadv"):
            _remove_safe(character.disadvantages.setdefault("Skills", []), "Perception")
        super().remove(character)


class Exhaustion(Condition):
    def __init__(self, duration: Optional[int] = None):
        super().__init__("Exhaustion", "This condition is cumulative. Each time you receive it, you gain 1 Exhaustion level. You die if your Exhaustion level is 6. Finishing long rests reduces the amount", duration)
        self.level = 0

    def apply(self, character: Character):
        # Each application should increment by 1
        existing_effect = [_ for _ in character.active_effects if _.name == "Exhaustion"]
        if len(existing_effect) == 1:
            self.level = existing_effect[0].level
            character.active_effects = [e for e in character.active_effects if e.name != "Exhaustion"]
        else:
            self.level = 0
        self.increment(character)

    def remove(self, character: Character):
        # Each removal should decrement by 1
        existing_effect = [_ for _ in character.active_effects if _.name == "Exhaustion"]
        if len(existing_effect) == 1:
            self.level = existing_effect[0].level
            character.active_effects = [e for e in character.active_effects if e.name != "Exhaustion"]
        else:
            # Nothing to remove
            return
        self.decrement(character)

    def increment(self, character: Character):
        self.level += 1
        character.speed -= 5
        character.d20_modifier -= 2
        if self.level == 6:
            character.speed += 30
            character.d20_modifier += 12
            character.current_hp = 0
            character.death_saves['Failed'] = 3
            Dead().apply(character)
        super().apply(character)

    def decrement(self, character: Character):
        self.level -= 1
        character.speed += 5
        character.d20_modifier += 2
        if self.level == 0:
            super().remove(character)
        else:
            super().apply(character)


class Frightened(Condition):
    def __init__(self, duration: Optional[int] = None, by: Optional[Character] = None):
        super().__init__("Frightened", "Disadvantage on ability checks and attack rolls while the source is in line of sight; can't willingly move closer to the source.", duration)

    def apply(self, character: Character):
        # Disadvantage on attack rolls
        character.disadvantages["Attack"] = character.disadvantages.get("Attack", 0) + 1
        # Disadvantage on all ability checks
        abilities = ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
        for a in abilities:
            _add_unique(character.disadvantages.setdefault("Abilities", []), a)
        _add_unique(character.active_effects, "Frightened_CannotApproachSource")
        self._prev_state["disadv_attack_added"] = 1
        self._prev_state["abilities_added"] = abilities
        self._prev_state["added_flag"] = True
        super().apply(character)

    def remove(self, character: Character):
        if self._prev_state.get("disadv_attack_added"):
            character.disadvantages["Attack"] = max(0, character.disadvantages.get("Attack", 0) - 1)
        for a in self._prev_state.get("abilities_added", []):
            _remove_safe(character.disadvantages.setdefault("Abilities", []), a)
        if self._prev_state.get("added_flag"):
            _remove_safe(character.active_effects, "Frightened_CannotApproachSource")
        super().remove(character)


class Grappled(Condition):
    def __init__(self, duration: Optional[int] = None, by: Optional[Character] = None):
        super().__init__("Grappled", "Speed becomes 0 while grappled.", duration)
        self.by = by

    def apply(self, character: Character):
        # store previous speed and set to 0
        self._prev_state["speed"] = getattr(character, "speed", None)
        character.speed = 0
        super().apply(character)

    def remove(self, character: Character):
        if "speed" in self._prev_state and self._prev_state["speed"] is not None:
            character.speed = self._prev_state["speed"]
        super().remove(character)


class Incapacitated(Condition):
    def __init__(self, duration: Optional[int] = None):
        super().__init__("Incapacitated", "Can't take actions or reactions.", duration)

    def apply(self, character: Character, speed_handled=False):
        if not speed_handled:
            # store previous speed and set to 0
            self._prev_state["speed"] = getattr(character, "speed", None)
            character.speed = 0
        character.disadvantages["Initiative"] += 1
        super().apply(character)

    def remove(self, character: Character):
        if "speed" in self._prev_state and self._prev_state["speed"] is not None:
            character.speed = self._prev_state["speed"]
        super().remove(character)


class Invisible(Condition):
    def __init__(self, duration: Optional[int] = None):
        super().__init__("Invisible", "You are invisible: attack rolls against you have disadvantage; you have advantage on attack rolls.", duration)

    def apply(self, character: Character):
        # Attacks against have disadvantage: decrement ToBeAttacked advantage
        character.advantages["ToBeAttacked"] = max(0, character.advantages.get("ToBeAttacked", 0) - 1)
        # You have advantage on attack rolls
        character.advantages["Attack"] = character.advantages.get("Attack", 0) + 1
        self._prev_state["adv_to_be_attacked_decremented"] = 1
        self._prev_state["adv_attack_added"] = 1
        super().apply(character)

    def remove(self, character: Character):
        if self._prev_state.get("adv_to_be_attacked_decremented"):
            # reversing the earlier decrement: add back one
            character.advantages["ToBeAttacked"] = character.advantages.get("ToBeAttacked", 0) + 1
        if self._prev_state.get("adv_attack_added"):
            character.advantages["Attack"] = max(0, character.advantages.get("Attack", 0) - 1)
        super().remove(character)


class Paralyzed(Condition):
    def __init__(self, duration: Optional[int] = None):
        super().__init__("Paralyzed", "Incapacitated, can't move or speak, automatically fail Strength and Dexterity saving throws. Attacks within 5 feet have advantage and any attack that hits is a critical if attacker is within 5 feet.", duration)

    def apply(self, character: Character):
        Incapacitated().apply(character, speed_handled=True)
        # store speed
        self._prev_state["speed"] = getattr(character, "speed", None)
        character.speed = 0
        for a in ["Strength, Dexterity"]:
            _add_unique(character.auto_fail.setdefault("Saving Throws", []), a)
        # Attacks against have advantage
        character.advantages["ToBeAttacked"] += 1
        super().apply(character)

    def remove(self, character: Character):
        character.remove_condition("Incapacitated")
        if "speed" in self._prev_state and self._prev_state["speed"] is not None:
            character.speed = self._prev_state["speed"]
        for a in ["Strength, Dexterity"]:
            _remove_safe(character.auto_fail.setdefault("Saving Throws", []), a)
        character.advantages["ToBeAttacked"] -= 1
        super().remove(character)


class Petrified(Condition):
    def __init__(self, duration: int = None):
        super().__init__("Petrified", "Incapacitated. Speed is 0 and can't increase. Attack rolls against you have advantage. You automatically fail Strength and Dexterity saving throws. You have resistance to all damage. You have immunity to the Poisoned condition.", duration)

    def apply(self, character: Character):
        Incapacitated().apply(character, speed_handled=True)
        character.weight *= 10
        for item in character.inventory:
            if hasattr(item, "weight"):
                item.weight *= 10
        for item in character.equipped_items:
            if hasattr(item, "weight"):
                item.weight *= 10

        # Speed 0 and can't increase
        self._prev_state["speed"] = getattr(character, "speed", None)
        character.speed = 0

        # Attack rolls against you have Advantage
        character.advantages["ToBeAttacked"] = character.advantages.get("ToBeAttacked", 0) + 1
        self._prev_state["adv_to_be_attacked_added"] = 1

        # Automatically fail Strength and Dexterity saving throws
        for a in ["Strength, Dexterity"]:
            _add_unique(character.auto_fail.setdefault("Saving Throws", []), a)

        # Resistance to all damage (add all damage types)
        prev_resistances = []
        for dtype in damage_types:
            if dtype not in character.resistances:
                character.resistances.append(dtype)
                prev_resistances.append(dtype)
        self._prev_state["resistances_added"] = prev_resistances

        if "Poison" not in character.immunities:
            character.immunities.append("Poison")
            self._prev_state["immunities_added"] = prev_resistances
        super().apply(character)

    def remove(self, character: Character):
        character.remove_condition("Incapacitated")
        character.weight /= 10
        for item in character.inventory:
            if hasattr(item, "weight"):
                item.weight /= 10
        for item in character.equipped_items:
            if hasattr(item, "weight"):
                item.weight /= 10

        # Restore speed
        if "speed" in self._prev_state and self._prev_state["speed"] is not None:
            character.speed = self._prev_state["speed"]

        # Remove advantage to be attacked
        if self._prev_state.get("adv_to_be_attacked_added"):
            character.advantages["ToBeAttacked"] = max(0, character.advantages.get("ToBeAttacked", 0) - 1)

        # Remove saving throw disadvantages
        for a in ["Strength, Dexterity"]:
            _remove_safe(character.auto_fail.setdefault("Saving Throws", []), a)

        # Remove damage resistances
        for dtype in self._prev_state.get("resistances_added", []):
            _remove_safe(character.resistances, dtype)

        # Remove poison immunity marker
        for dtype in self._prev_state.get("immunities_added", []):
            _remove_safe(character.immunities, dtype)
        super().remove(character)


class Poisoned(Condition):
    def __init__(self, duration: Optional[int] = None):
        super().__init__("Poisoned", "Disadvantage on attack rolls and ability checks.", duration)

    def apply(self, character: Character):
        # Disadvantage on attack rolls
        character.disadvantages["Attack"] = character.disadvantages.get("Attack", 0) + 1
        # Disadvantage on all ability checks
        abilities = [
            _ for _ in ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]
            if _ not in character.disadvantages["Abilities"]
        ]
        for a in abilities:
            _add_unique(character.disadvantages.setdefault("Abilities", []), a)
        self._prev_state["disadv_attack_added"] = 1
        self._prev_state["abilities_added"] = abilities
        super().apply(character)

    def remove(self, character: Character):
        if self._prev_state.get("disadv_attack_added"):
            character.disadvantages["Attack"] = max(0, character.disadvantages.get("Attack", 0) - 1)
        for a in self._prev_state.get("abilities_added", []):
            _remove_safe(character.disadvantages.setdefault("Abilities", []), a)
        super().remove(character)


class Prone(Condition):
    def __init__(self, duration: Optional[int] = None):
        super().__init__("Prone", "You are prone: movement options are limited; attack rolls have disadvantage; melee attacks against you have advantage.", duration)

    def apply(self, character: Character):
        # Attack rolls disadvantage
        character.disadvantages["Attack"] = character.disadvantages.get("Attack", 0) + 1
        # Attacks against this character have advantage
        # TODO: This is supposed to be only for melee, so we need to refactor ToBeAttacked into range and melee
        character.advantages["ToBeAttacked"] = character.advantages.get("ToBeAttacked", 0) + 1
        self._prev_state["disadv_attack_added"] = 1
        self._prev_state["adv_to_be_attacked_added"] = 1
        super().apply(character)

    def remove(self, character: Character):
        if self._prev_state.get("disadv_attack_added"):
            character.disadvantages["Attack"] = max(0, character.disadvantages.get("Attack", 0) - 1)
        if self._prev_state.get("adv_to_be_attacked_added"):
            character.advantages["ToBeAttacked"] = max(0, character.advantages.get("ToBeAttacked", 0) - 1)
        super().remove(character)


class Restrained(Condition):
    def __init__(self, duration: Optional[int] = None):
        super().__init__("Restrained", "Speed is 0, cannot benefit from bonuses to speed, attack rolls have disadvantage, attacks against you have advantage; Dexterity saving throws have disadvantage.", duration)

    def apply(self, character: Character):
        self._prev_state["speed"] = getattr(character, "speed", None)
        character.speed = 0
        # Attack rolls disadvantage
        character.disadvantages["Attack"] = character.disadvantages.get("Attack", 0) + 1
        # Attacks against this character have advantage
        character.advantages["ToBeAttacked"] = character.advantages.get("ToBeAttacked", 0) + 1
        # Dex saves disadvantage: track in Abilities
        if "Dexterity" not in character.disadvantages["Abilities"]:
            _add_unique(character.disadvantages.setdefault("Abilities", []), "Dexterity")
            self._prev_state["dex_added"] = True
        self._prev_state["disadv_attack_added"] = 1
        self._prev_state["adv_to_be_attacked_added"] = 1
        super().apply(character)

    def remove(self, character: Character):
        if "speed" in self._prev_state and self._prev_state["speed"] is not None:
            character.speed = self._prev_state["speed"]
        if self._prev_state.get("disadv_attack_added"):
            character.disadvantages["Attack"] = max(0, character.disadvantages.get("Attack", 0) - 1)
        if self._prev_state.get("adv_to_be_attacked_added"):
            character.advantages["ToBeAttacked"] = max(0, character.advantages.get("ToBeAttacked", 0) - 1)
        if self._prev_state.get("dex_added"):
            _remove_safe(character.disadvantages.setdefault("Abilities", []), "Dexterity")
        super().remove(character)


class Stunned(Condition):
    def __init__(self, duration: Optional[int] = None):
        super().__init__("Stunned", "Incapacitated, can't move, can speak, automatically fail Strength and Dexterity saving throws.", duration)

    def apply(self, character: Character):
        Incapacitated().apply(character, speed_handled=True)
        self._prev_state["speed"] = getattr(character, "speed", None)
        character.speed = 0
        # Disadvantage on attacks
        character.disadvantages["Attack"] = character.disadvantages.get("Attack", 0) + 1
        self._prev_state["disadv_attack_added"] = 1
        # Automatically fail Strength and Dexterity saving throws
        for a in ["Strength, Dexterity"]:
            _add_unique(character.auto_fail.setdefault("Saving Throws", []), a)
        super().apply(character)

    def remove(self, character: Character):
        character.remove_condition("Incapacitated")
        if "speed" in self._prev_state and self._prev_state["speed"] is not None:
            character.speed = self._prev_state["speed"]
        if self._prev_state.get("disadv_attack_added"):
            character.disadvantages["Attack"] = max(0, character.disadvantages.get("Attack", 0) - 1)
        for a in ["Strength, Dexterity"]:
            _remove_safe(character.auto_fail.setdefault("Saving Throws", []), a)
        super().remove(character)


class Unconscious(Condition):
    def __init__(self, duration: Optional[int] = None):
        super().__init__("Unconscious", "Incapacitated, can't move or speak, drop to 0 hit points, you fall prone.", duration)

    def apply(self, character: Character):
        Incapacitated().apply(character, speed_handled=True)
        Prone().apply(character)
        # drop speed to 0
        self._prev_state["speed"] = getattr(character, "speed", None)
        character.speed = 0
        # Automatically fail Strength and Dexterity saving throws
        for a in ["Strength, Dexterity"]:
            _add_unique(character.auto_fail.setdefault("Saving Throws", []), a)
        super().apply(character)

    def remove(self, character: Character):
        character.remove_condition("Incapacitated")
        # Note: Prone does not get resolved after
        if "speed" in self._prev_state and self._prev_state["speed"] is not None:
            character.speed = self._prev_state["speed"]
        for a in ["Strength, Dexterity"]:
            _remove_safe(character.auto_fail.setdefault("Saving Throws", []), a)
        super().remove(character)


# EXTRA EFFECTS
class CannotCast(Condition):
    def __init__(self, duration: Optional[int] = None):
        super().__init__("Cannot Cast", "Something is causing casting to be impossible at this time.", duration)


class ClunkyArmor(Condition):
    def __init__(self, duration: Optional[int] = None):
        super().__init__("Clunky Armor", "Your armor is too loud and is making it hard to sneak around.", duration)

    def apply(self, character):
        if "Stealth" not in character.disadvantages["Skills"]:
            character.disadvantages["Skills"] += ["Stealth"]
            self._prev_state["disadv_stealth_added"] = True
        super().apply(character)

    def remove(self, character):
        if self._prev_state.get("disadv_stealth_added"):
            _remove_safe(character.disadvantages.setdefault("Skills", []), "Stealth")
        super().remove(character)


class ArmorTooHeavy(Condition):
    def __init__(self, duration: Optional[int] = None):
        super().__init__("Armor Too Heavy", "You lack the strength to move effectively in your armor.", duration)

    def apply(self, character):
        # drop speed to 0
        self._prev_state["speed"] = getattr(character, "speed", None)
        character.speed -= 10
        if character.speed < 0:
            character.speed = 0
        super().apply(character)

    def remove(self, character):
        if "speed" in self._prev_state and self._prev_state["speed"] is not None:
            character.speed = self._prev_state["speed"]
        super().remove(character)


class ProficiencyGappedArmor(Condition):
    def __init__(self, duration: Optional[int] = None):
        super().__init__("Proficiency Gapped Armor", "You don't know how to navigate in the armor you are wearing.", duration)

    def apply(self, character):
        CannotCast().apply(character)
        sts_to_disadv = [
            _ for _ in ["Strength", "Dexterity"]
            if _ not in character.disadvantages["Saving Throws"]
        ]
        abilities_to_disadv = [
            _ for _ in ["Strength", "Dexterity"]
            if _ not in character.disadvantages["Abilities"]
        ]
        skills_to_disadv = [
            _ for _ in [k for k, v in dnd_skills.items() if v in ["Strength", "Dexterity"]]
            if _ not in character.disadvantages["Skills"]
        ]
        character.disadvantages.setdefault("Saving Throws", []).extend(sts_to_disadv)
        character.disadvantages.setdefault("Abilities", []).extend(abilities_to_disadv)
        character.disadvantages.setdefault("Skills", []).extend(skills_to_disadv)
        self._prev_state["sts_to_disadv"] = sts_to_disadv
        self._prev_state["abilities_to_disadv"] = abilities_to_disadv
        self._prev_state["skills_to_disadv"] = skills_to_disadv
        super().apply(character)

    def remove(self, character):
        character.remove_condition("CannotCast")
        for sts in self._prev_state["sts_to_disadv"]:
            _remove_safe(character.disadvantages.setdefault("Saving Throws", []), sts)
        for a in self._prev_state["abilities_to_disadv"]:
            _remove_safe(character.disadvantages.setdefault("Abilities", []), a)
        for s in self._prev_state["skills_to_disadv"]:
            _remove_safe(character.disadvantages.setdefault("Skills", []), s)
        super().remove(character)
