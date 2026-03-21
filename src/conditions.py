from typing import List, Optional
from src.creatures import Character


class Condition:
    """Base condition class.

    Subclasses declare their stat contributions as class or instance attributes.
    Creature computed properties (speed, advantages, etc.) read these to derive
    effective values — conditions no longer mutate stats directly.

    Stat descriptor defaults (override in subclasses):
      speed_override          — if not None, forces effective speed to this value
      speed_delta             — feet added to speed (negative = penalty)
      d20_delta               — modifier added to all d20 rolls
      adv_attack              — advantage stacks on this creature's attack rolls
      disadv_attack           — disadvantage stacks on attack rolls
      adv_to_be_attacked      — advantage stacks on rolls made against this creature
      disadv_to_be_attacked   — disadvantage stacks on rolls made against this creature
      adv_initiative          — advantage stacks on initiative
      disadv_initiative       — disadvantage stacks on initiative
      adv_abilities           — tuple of ability names granted advantage
      disadv_abilities        — tuple of ability names given disadvantage
      adv_skills              — tuple of skill names granted advantage
      disadv_skills           — tuple of skill names given disadvantage
      adv_saving_throws       — tuple of ability names granted saving throw advantage
      disadv_saving_throws    — tuple of ability names given saving throw disadvantage
      auto_fail_saving_throws — tuple of ability names that auto-fail saving throws
      bonus_resistances       — tuple of damage types added as resistances
      bonus_immunities        — tuple of damage types added as immunities
      weight_multiplier       — multiplied onto the creature's base weight
      prevents_casting        — True blocks cast_spell()
    """

    speed_override = None
    speed_delta = 0
    d20_delta = 0
    adv_attack = 0
    disadv_attack = 0
    adv_to_be_attacked = 0
    disadv_to_be_attacked = 0
    adv_initiative = 0
    disadv_initiative = 0
    adv_abilities = ()
    disadv_abilities = ()
    adv_skills = ()
    disadv_skills = ()
    adv_saving_throws = ()
    disadv_saving_throws = ()
    auto_fail_saving_throws = ()
    bonus_resistances = ()
    bonus_immunities = ()
    weight_multiplier = 1
    prevents_casting = False

    def __init__(self, name: str, description: str = "", duration: Optional[int] = None):
        self.name = name
        self.description = description
        # duration in rounds; None means indefinite
        self.duration = duration

    def apply(self, character: Character):
        """Add this condition to the creature's active_effects (idempotent)."""
        if any(getattr(e, "name", None) == self.name for e in character.active_effects):
            return
        character.active_effects.append(self)

    def remove(self, character: Character):
        """Remove this condition from the creature's active_effects."""
        character.active_effects = [
            e for e in character.active_effects
            if getattr(e, "name", None) != self.name
        ]


# ── Concrete conditions ─────────────────────────────────────────────────────

class Blinded(Condition):
    """Can't see. Attacks have disadvantage; attacks against you have advantage."""
    disadv_attack = 1
    adv_to_be_attacked = 1

    def __init__(self, duration: Optional[int] = None):
        super().__init__(
            "Blinded",
            "Can't see. Attack rolls have disadvantage; attacks against you have advantage; "
            "automatically fail checks that require sight.",
            duration,
        )


class Charmed(Condition):
    """Can't attack the charmer; charmer has advantage on social checks."""

    def __init__(self, duration: Optional[int] = None, by: Optional[Character] = None):
        super().__init__(
            "Charmed",
            "Can't attack the charmer with damaging abilities or magical effects. "
            "The charmer has advantage on any ability check to interact socially.",
            duration,
        )
        self.by = by


class Charming(Condition):
    """Paired condition placed on the creature doing the charming."""

    def __init__(self, duration: Optional[int] = None, who: Optional[Character] = None):
        super().__init__(
            "Charming",
            "The character this creature is charming cannot attack them. "
            "This creature has advantage on social rolls against the target.",
            duration,
        )
        self.who = who


class Dead(Condition):
    """This character is dead."""

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
    """Can't hear; automatically fail checks requiring hearing."""
    disadv_skills = ("Perception",)

    def __init__(self, duration: Optional[int] = None):
        super().__init__(
            "Deafened",
            "Can't hear. Automatically fail checks that require hearing.",
            duration,
        )


class Exhaustion(Condition):
    """Cumulative condition. Each application adds one level (max 6 = death)."""

    def __init__(self, duration: Optional[int] = None):
        super().__init__(
            "Exhaustion",
            "Cumulative: each level reduces speed by 5 ft and applies -2 to all d20 rolls. "
            "Level 6 is fatal.",
            duration,
        )
        self.level = 0
        # Instance attributes override the class-level defaults of 0
        self.speed_delta = 0
        self.d20_delta = 0

    def _update_deltas(self):
        self.speed_delta = -5 * self.level
        self.d20_delta = -2 * self.level

    def apply(self, character: Character):
        # Merge with any existing Exhaustion in active_effects
        existing = next(
            (e for e in character.active_effects if getattr(e, "name", None) == "Exhaustion"),
            None,
        )
        if existing is not None:
            character.active_effects.remove(existing)
            self.level = existing.level
        self.level += 1
        self._update_deltas()
        if self.level >= 6:
            character.current_hp = 0
            character.death_saves["Failed"] = 3
            Dead().apply(character)
        character.active_effects.append(self)

    def remove(self, character: Character):
        # Called on the actual Exhaustion object already in active_effects
        if self not in character.active_effects:
            return
        character.active_effects.remove(self)
        self.level -= 1
        self._update_deltas()
        if self.level > 0:
            character.active_effects.append(self)


class Frightened(Condition):
    """Disadvantage on attacks and ability checks; can't approach the source."""
    disadv_attack = 1
    disadv_abilities = (
        "Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma",
    )

    def __init__(self, duration: Optional[int] = None, by: Optional[Character] = None):
        super().__init__(
            "Frightened",
            "Disadvantage on ability checks and attack rolls while source is in sight; "
            "can't willingly move closer to the source.",
            duration,
        )
        self.by = by  # the creature causing the fear (checked for line-of-sight logic)


class Grappled(Condition):
    """Speed becomes 0."""
    speed_override = 0

    def __init__(self, duration: Optional[int] = None, by: Optional[Character] = None):
        super().__init__("Grappled", "Speed becomes 0 while grappled.", duration)
        self.by = by


class Incapacitated(Condition):
    """Can't take actions or reactions; speed 0; disadvantage on initiative."""
    speed_override = 0
    disadv_initiative = 1
    prevents_casting = True

    def __init__(self, duration: Optional[int] = None):
        super().__init__(
            "Incapacitated",
            "Can't take actions or reactions.",
            duration,
        )


class Invisible(Condition):
    """Advantage on attacks; disadvantage on rolls against you."""
    adv_attack = 1
    disadv_to_be_attacked = 1

    def __init__(self, duration: Optional[int] = None):
        super().__init__(
            "Invisible",
            "You are invisible: attack rolls against you have disadvantage; "
            "you have advantage on attack rolls.",
            duration,
        )


class Paralyzed(Condition):
    """Incapacitated; speed 0; auto-fail Str/Dex saves; attacks against have advantage and crit within 5 ft."""
    speed_override = 0
    disadv_initiative = 1
    prevents_casting = True
    auto_fail_saving_throws = ("Strength", "Dexterity")
    adv_to_be_attacked = 1

    def __init__(self, duration: Optional[int] = None):
        super().__init__(
            "Paralyzed",
            "Incapacitated, can't move or speak, automatically fail Strength and Dexterity "
            "saving throws. Attacks within 5 feet have advantage and are critical hits.",
            duration,
        )


class Petrified(Condition):
    """Incapacitated; speed 0; auto-fail Str/Dex saves; resistance to all damage; immune to Poison."""
    speed_override = 0
    disadv_initiative = 1
    prevents_casting = True
    auto_fail_saving_throws = ("Strength", "Dexterity")
    adv_to_be_attacked = 1
    bonus_resistances = (
        "Acid", "Bludgeoning", "Cold", "Fire", "Force", "Lightning",
        "Necrotic", "Piercing", "Poison", "Psychic", "Radiant", "Slashing", "Thunder",
    )
    bonus_immunities = ("Poison",)
    weight_multiplier = 10

    def __init__(self, duration: Optional[int] = None):
        super().__init__(
            "Petrified",
            "Incapacitated. Speed is 0 and can't increase. Attack rolls against you have "
            "advantage. You automatically fail Strength and Dexterity saving throws. "
            "Resistance to all damage. Immunity to the Poisoned condition. Weight ×10.",
            duration,
        )


class Poisoned(Condition):
    """Disadvantage on attack rolls and all ability checks."""
    disadv_attack = 1
    disadv_abilities = (
        "Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma",
    )

    def __init__(self, duration: Optional[int] = None):
        super().__init__(
            "Poisoned",
            "Disadvantage on attack rolls and ability checks.",
            duration,
        )


class Prone(Condition):
    """Attack rolls have disadvantage; melee attacks against you have advantage."""
    disadv_attack = 1
    adv_to_be_attacked = 1

    def __init__(self, duration: Optional[int] = None):
        super().__init__(
            "Prone",
            "You are prone: attack rolls have disadvantage; melee attacks against you have advantage.",
            duration,
        )


class Restrained(Condition):
    """Speed 0; attack rolls have disadvantage; attacks against have advantage; Dex saves disadvantage."""
    speed_override = 0
    disadv_attack = 1
    adv_to_be_attacked = 1
    disadv_saving_throws = ("Dexterity",)

    def __init__(self, duration: Optional[int] = None):
        super().__init__(
            "Restrained",
            "Speed is 0, cannot benefit from bonuses to speed, attack rolls have disadvantage, "
            "attacks against you have advantage; Dexterity saving throws have disadvantage.",
            duration,
        )


class Stunned(Condition):
    """Incapacitated; speed 0; auto-fail Str/Dex saves; attacks against have advantage."""
    speed_override = 0
    disadv_initiative = 1
    prevents_casting = True
    disadv_attack = 1
    auto_fail_saving_throws = ("Strength", "Dexterity")
    adv_to_be_attacked = 1

    def __init__(self, duration: Optional[int] = None):
        super().__init__(
            "Stunned",
            "Incapacitated, can't move, can speak, automatically fail Strength and Dexterity saving throws.",
            duration,
        )


class Unconscious(Condition):
    """Incapacitated + Prone; speed 0; auto-fail Str/Dex saves; attacks against have advantage."""
    speed_override = 0
    disadv_initiative = 1
    prevents_casting = True
    disadv_attack = 1           # from Prone
    adv_to_be_attacked = 1      # from Prone
    auto_fail_saving_throws = ("Strength", "Dexterity")

    def __init__(self, duration: Optional[int] = None):
        super().__init__(
            "Unconscious",
            "Incapacitated, can't move or speak, fall prone.",
            duration,
        )


# ── Equipment-derived conditions ────────────────────────────────────────────

class CannotCast(Condition):
    """Something is preventing spellcasting."""
    prevents_casting = True

    def __init__(self, duration: Optional[int] = None):
        super().__init__(
            "Cannot Cast",
            "Something is causing casting to be impossible at this time.",
            duration,
        )


class ClunkyArmor(Condition):
    """Armor is too loud — disadvantage on Stealth."""
    disadv_skills = ("Stealth",)

    def __init__(self, duration: Optional[int] = None):
        super().__init__(
            "Clunky Armor",
            "Your armor is too loud and is making it hard to sneak around.",
            duration,
        )


class ArmorTooHeavy(Condition):
    """Lacking the strength for this armor — speed –10 ft."""
    speed_delta = -10

    def __init__(self, duration: Optional[int] = None):
        super().__init__(
            "Armor Too Heavy",
            "You lack the strength to move effectively in your armor.",
            duration,
        )


class ProficiencyGappedArmor(Condition):
    """Wearing armor without proficiency — can't cast, Str/Dex saves and checks have disadvantage."""
    prevents_casting = True
    disadv_saving_throws = ("Strength", "Dexterity")
    disadv_abilities = ("Strength", "Dexterity")
    # Strength skill: Athletics. Dexterity skills: Acrobatics, Sleight of Hand, Stealth.
    disadv_skills = ("Athletics", "Acrobatics", "Sleight of Hand", "Stealth")

    def __init__(self, duration: Optional[int] = None):
        super().__init__(
            "Proficiency Gapped Armor",
            "You don't know how to navigate in the armor you are wearing.",
            duration,
        )
