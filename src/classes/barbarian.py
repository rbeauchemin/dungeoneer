from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.common import dnd_skills
from src.classes._base import Class


RAGES_PER_LEVEL = [2, 2, 3, 3, 3, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 6, 6, 6, 6]

# Skills that Primal Knowledge allows a raging barbarian to use as Strength checks
_PRIMAL_KNOWLEDGE_SKILLS = ("Acrobatics", "Intimidation", "Perception", "Stealth", "Survival")


class Barbarian(Class):
    def __init__(self, level):
        super().__init__(name="Barbarian", level=level)
        self.todo = []
        self.level = level
        self.hit_dice = 12
        self.primary_ability = "Strength"
        self.proficiencies["Armor"] = ["Light", "Medium", "Shield"]
        self.proficiencies["Weapons"] = ["Simple", "Martial"]
        self.proficiencies["Saving Throws"] = ["Strength", "Constitution"]
        self.proficiencies["Skills"] = ["Animal Handling", "Athletics", "Intimidation", "Nature", "Perception", "Survival"]
        self.completed_levelup_to = 0
        self._brutal_strike_dice = 1  # increases to 2 at level 17

    # ── Equipment ─────────────────────────────────────────────────────────────

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 75
        else:
            character.add_item([Handaxe(quantity=4), Greataxe(), ExplorersPack()])
            character.gold += 15
        return character

    # ── Rage helpers ──────────────────────────────────────────────────────────

    def _calculate_rage_condition(self):
        from src.conditions import Condition
        rage_damage = 2 if self.level < 9 else 3 if self.level < 16 else 4
        instinctive_pounce = self.level >= 7
        rage_condition = Condition(
            name="Rage",
            description=(
                "While raging, you have Resistance to Bludgeoning, Piercing, and Slashing damage; "
                f"a +{rage_damage} bonus to Strength-based attack damage; Advantage on Strength checks "
                "and Strength saving throws; and you can't Concentrate or cast spells."
                + (" When you enter Rage, you may move up to half your Speed as part of the Bonus Action." if instinctive_pounce else "")
            ),
            duration=10  # 1 minute = 10 rounds; ends early via _check_rage_end in combat
        )
        rage_condition.bonus_resistances = ["Bludgeoning", "Piercing", "Slashing"]
        rage_condition.bonus_damage = rage_damage
        rage_condition.prevents_casting = True
        rage_condition.adv_abilities = ["Strength"]
        rage_condition.adv_saving_throws = ["Strength"]
        rage_condition.adv_skills = [_ for _ in dnd_skills if dnd_skills[_] == "Strength"]
        return rage_condition

    def _build_rage_ability(self):
        return Spell(
            name="Rage",
            casting_time="Bonus Action",
            range_="Self",
            components=[],
            duration="Up to 10 minutes",
            description=(
                "Enter a Rage as a Bonus Action. While raging: Resistance to Bludgeoning/Piercing/Slashing; "
                "bonus to Strength-based attack damage; Advantage on Strength checks and saves; can't cast spells."
            ),
            uses_left=RAGES_PER_LEVEL[self.level - 1],
            cooldown="Long Rest",
            cast=lambda caster, targets: caster.active_effects.append(self._calculate_rage_condition())
        )

    def _refresh_rage(self, character: Character):
        """Replace the Rage special ability with a fresh one reflecting the current level."""
        character.special_abilities = [
            a for a in character.special_abilities if a.name != "Rage"
        ] + [self._build_rage_ability()]

    # ── Level feature application ──────────────────────────────────────────────

    def _apply_level_features(self, character: Character, level: int):
        """Apply all Barbarian features unlocked at the given level."""
        from src.conditions import (
            DangerSense, FeralInstinct, FastMovement, IndomitableMight
        )

        if level == 1:
            
            # ── Rage ──────────────────────────────────────────────────────────
            if not isinstance(character.special_abilities, list):
                character.special_abilities = []
            character.special_abilities.append(self._build_rage_ability())

            # ── Weapon Mastery ─────────────────────────────────────────────────
            character.todo.extend([
                {
                    "Text": "Choose two weapons to gain mastery in.",
                    "Options": ["Greataxe", "Greatsword", "Handaxe", "Javelin", "Light Hammer",
                                "Longsword", "Maul", "Morningstar", "Pike", "Rapier", "Scimitar",
                                "Shortsword", "Trident", "War Pick", "Warhammer"],
                    "Choices": 2,
                    "Function": lambda char, choices: char.weapon_mastery.extend(choices)
                },
                {
                    "Text": "Select starting equipment or gold: (Greataxe, 4 Handaxes, Explorer's Pack) or (75 GP)",
                    "Options": ["Starting Equipment", "Gold"],
                    "Function": self.select_starting_equipment
                },
                {
                    "Text": "Choose two skills to gain proficiency in.",
                    "Options": list(set(self.proficiencies["Skills"]) - set(character.proficiencies["Skills"])),
                    "Function": self.select_skills,
                    "Choices": 2,
                    "AllowSame": False
                }
            ])
            # Unarmored Defense is handled in Character.get_armor_class()

        elif level == 2:
            # ── Danger Sense ───────────────────────────────────────────────────
            DangerSense().apply(character)

            # ── Reckless Attack ────────────────────────────────────────────────
            character.special_abilities.append(Spell(
                name="Reckless Attack",
                casting_time="Free Action",
                range_="Self",
                components=[],
                duration=1,
                description=(
                    "When you make your first attack on your turn, you can attack recklessly. "
                    "You gain Advantage on Strength attack rolls this turn, but attack rolls against you "
                    "have Advantage until the start of your next turn."
                ),
                uses_left=None,
                cooldown=None,
                cast=lambda caster, targets, _self=self: _self._activate_reckless_attack(caster)
            ))

        elif level == 3:
            # ── Primal Knowledge ───────────────────────────────────────────────
            character.todo.append({
                "Text": "Primal Knowledge: Choose one additional skill to become proficient in.",
                "Options": list(set(self.proficiencies["Skills"]) - set(character.proficiencies["Skills"])),
                "Choices": 1,
                "Function": lambda char, choices: char.proficiencies["Skills"].extend(choices)
            })
            # While Raging, you can use Strength for Acrobatics, Intimidation, Perception, Stealth, or Survival.
            # This is tracked as a character flag; roll_check should use Strength for these when Rage is active.
            character.primal_knowledge = True

        elif level == 5:
            # ── Extra Attack ───────────────────────────────────────────────────
            character.extra_attacks = getattr(character, "extra_attacks", 0) + 1

            # ── Fast Movement ──────────────────────────────────────────────────
            FastMovement().apply(character)

        elif level == 7:
            # ── Feral Instinct ─────────────────────────────────────────────────
            FeralInstinct().apply(character)
            # ── Instinctive Pounce ──────────────────────────────────────────────
            # Handled in _calculate_rage_condition via self.level >= 7 check;
            # the move itself must be triggered by the player during their Rage activation.

        elif level == 9:
            # ── Brutal Strike ──────────────────────────────────────────────────
            self._brutal_strike_dice = 1
            character.special_abilities.append(self._build_brutal_strike_ability())

        elif level == 11:
            # ── Relentless Rage ────────────────────────────────────────────────
            character.relentless_rage_dc = 10  # resets to 10 on Short/Long Rest; increases by 5 each use

        elif level == 13:
            # ── Improved Brutal Strike (Staggering Blow, Sundering Blow) ───────
            self._brutal_strike_dice = 1
            self._refresh_brutal_strike(character)

        elif level == 15:
            # ── Persistent Rage ────────────────────────────────────────────────
            character.persistent_rage = True
            # Persistent Rage also lets you regain all Rage uses on Initiative once per Long Rest
            character.special_abilities.append(Spell(
                name="Persistent Rage: Regain Uses",
                casting_time="Free Action",
                range_="Self",
                components=[],
                duration="Instantaneous",
                description=(
                    "When you roll Initiative, you can regain all expended Rage uses. "
                    "You can't use this again until you finish a Long Rest."
                ),
                uses_left=1,
                cooldown="Long Rest",
                cast=lambda caster, targets, _self=self: _self._regain_all_rages(caster)
            ))

        elif level == 17:
            # ── Improved Brutal Strike II (2d10, two effects) ──────────────────
            self._brutal_strike_dice = 2
            self._refresh_brutal_strike(character)

        elif level == 18:
            # ── Indomitable Might ──────────────────────────────────────────────
            IndomitableMight().apply(character)

        elif level == 20:
            # ── Primal Champion ────────────────────────────────────────────────
            character.ability_scores["Strength"] = min(25, character.ability_scores.get("Strength", 10) + 4)
            character.ability_scores["Constitution"] = min(25, character.ability_scores.get("Constitution", 10) + 4)
            # Recompute max_hp for the Con increase (+2 bonus from +4 Con)
            character.max_hp += 2
            character.current_hp = min(character.current_hp + 2, character.max_hp)
        
        # Always refresh Rage to reflect updated uses and damage bonus
        self._refresh_rage(character)

    def _activate_reckless_attack(self, caster):
        from src.conditions import RecklessAttacking
        # duration=2: ticks at end of caster's turn (→1), persists through enemy turns, expires next turn
        caster.remove_condition("Reckless Attacking")
        RecklessAttacking(duration=2).apply(caster)

    def _build_brutal_strike_ability(self):
        dice = self._brutal_strike_dice
        two_effects = self.level >= 17
        effects_list = "Forceful Blow or Hamstring Blow"
        if self.level >= 13:
            effects_list = "Forceful Blow, Hamstring Blow, Staggering Blow, or Sundering Blow"
        if two_effects:
            effects_list = "any two of: Forceful Blow, Hamstring Blow, Staggering Blow, Sundering Blow"
        return Spell(
            name="Brutal Strike",
            casting_time="Free Action",
            range_="Self",
            components=[],
            duration="Next attack",
            description=(
                f"Requires Reckless Attack. Forgo Advantage on one Strength attack this turn. "
                f"On a hit, deal {dice}d10 extra damage and choose {'two effects' if two_effects else 'one effect'}: {effects_list}. "
                "Forceful Blow: push target 15 ft; you may move up to half your Speed toward them. "
                "Hamstring Blow: target Speed −15 ft until your next turn. "
                "Staggering Blow (lvl 13+): target has Disadvantage on its next saving throw and can't make Opportunity Attacks until your next turn. "
                "Sundering Blow (lvl 13+): the next attack against the target before your next turn gains +5 to hit."
            ),
            uses_left=None,
            cooldown=None,
            cast=lambda caster, targets, _self=self: _self._activate_brutal_strike(caster, targets)
        )

    def _activate_brutal_strike(self, caster, targets):
        from src.conditions import BrutalStrike, Hamstrung
        if not any(getattr(e, "name", None) == "Reckless Attacking" for e in caster.active_effects):
            print(f"{caster.name} must be using Reckless Attack to use Brutal Strike.")
            return
        # Mark the barbarian so the next attack deals bonus dice
        caster.remove_condition("Brutal Strike")
        BrutalStrike(dice=self._brutal_strike_dice, duration=1).apply(caster)
        # Apply Hamstring Blow to chosen target (simplest default effect for automation)
        for target in (targets or []):
            Hamstrung(duration=2).apply(target)
            print(f"  {target.name} is Hamstrung (Speed −15 ft until start of next turn).")

    def _refresh_brutal_strike(self, character: Character):
        """Replace the Brutal Strike ability with an updated version for the current level."""
        character.special_abilities = [
            a for a in character.special_abilities if a.name != "Brutal Strike"
        ] + [self._build_brutal_strike_ability()]

    def _regain_all_rages(self, caster):
        for ability in caster.special_abilities:
            if ability.name == "Rage":
                ability.uses_left = RAGES_PER_LEVEL[self.level - 1]
        print(f"  {caster.name} regains all Rage uses from Persistent Rage!")

    # ── Class interface ────────────────────────────────────────────────────────

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        # Apply features for every level from 1 up to the barbarian's starting level
        for lvl in range(1, self.level + 1):
            self._apply_level_features(character, lvl)
        self.completed_levelup_to = self.level
        return character

    def level_up(self, character: Character):
        super().level_up(character)  # increments self.level
        self._apply_level_features(character, self.level)
        return character
