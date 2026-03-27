from copy import deepcopy
import importlib
from typing import Optional
from src.common import roll_dice_discard_lowest, roll_dice, handle_roll_criticals, dnd_skills, clean_text


def _fresh_adv_dict():
    """Return a fresh per-instance advantages/disadvantages/auto_fail dict."""
    return {
        "Saving Throws": [],
        "Skills": [],
        "Abilities": [],
        "Attack": 0,
        "ToBeAttacked": 0,
        "Initiative": 0,
    }


class Character:
    def __init__(self, name, species, background, classes=[], equipment=[], spells=[], description="", ability_score_bonuses={}, **kwargs):
        # Set base traits and abilities
        self.todo = []
        self.name = name
        self.description = description
        self.gold = 0
        self.active_effects = []
        self.position = None   # set by Map.place_creature / Map.move_creature
        self._map = None       # set by Map.place_creature
        self.inventory = []
        self.inventory += equipment
        self.death_saves = {
            "Failed": 0,
            "Succeeded": 0
        }
        self.equipped_items = []
        self.ability_scores = kwargs['ability_scores'] if "ability_scores" in kwargs else {
            "Strength": 10,
            "Dexterity": 10,
            "Constitution": 10,
            "Intelligence": 10,
            "Wisdom": 10,
            "Charisma": 10
        }
        self.proficiencies = kwargs['proficiencies'] if "proficiencies" in kwargs else {
            "Armor": [],
            "Weapons": ["Unarmed"],
            "Tools": [],
            "Saving Throws": [],
            "Skills": [],
            "Special": []
        }
        self._base_advantages = dict(kwargs["advantages"]) if "advantages" in kwargs else _fresh_adv_dict()
        self._base_disadvantages = dict(kwargs["disadvantages"]) if "disadvantages" in kwargs else _fresh_adv_dict()
        self._base_auto_fail = dict(kwargs["auto_fail"]) if "auto_fail" in kwargs else _fresh_adv_dict()
        # SET ALL SPECIES ATTRIBUTES
        if isinstance(species, str):
            try:
                self.species = getattr(importlib.import_module("src.species"), species)(**kwargs)
            except AttributeError:
                raise Exception(f"Species {species} could not be found")
        else:
            self.species = species
        self.todo += self.species.todo
        self.description += " " if self.description else "" + self.species.description
        self.size = self.species.size
        self._base_weight = self.species.weight
        self._base_speed = self.species.speed
        self.swimming_speed = self.species.swimming_speed
        self.flying_speed = self.species.flying_speed
        self.climbing_speed = self.species.climbing_speed
        self.spells = self.species.spells
        self.spells += spells
        self.prepared_spells = []
        self._base_resistances = list(self.species.resistances)
        self._base_immunities = list(self.species.immunities)
        self.vision = self.species.vision
        self.full_rest_hours = self.species.full_rest_hours
        self.special_abilities = self.species.special_abilities
        self.special_traits = self.species.special_traits
        if "feats" in kwargs:
            self.feats = kwargs['feats']
        else:
            self.feats = []
        # SET ALL BACKGROUND ATTRIBUTES
        if isinstance(background, str):
            try:
                self.background = getattr(importlib.import_module("src.backgrounds"), background)(**kwargs)
            except AttributeError:
                raise Exception(f"Background {background} could not be found")
        else:
            self.background = background
        self.background.apply_to_character(self)
        # SET ALL CLASS ATTRIBUTES
        self.classes = classes
        for cls in classes:
            cls.apply_to_character(self)
        self.level = sum(cls.level for cls in classes)
        self.species.level = self.level
        self.proficiency_bonus = 2 + (self.level - 1) // 4
        self.species.proficiency_bonus = self.proficiency_bonus

        self.max_hp = 10 + self.get_ability_bonus("Constitution")
        if self.species.species == "Dwarf":
            self.max_hp += 1
        self.current_hp = self.max_hp
        if len(ability_score_bonuses) > 0:
            for ability, bonus in ability_score_bonuses.items():
                self.ability_scores[ability] += bonus
        else:
            print("Rolling ability scores...")
            for ability in self.ability_scores.keys():
                score = roll_dice_discard_lowest(6, 4)
                self.ability_scores[ability] = score
                print(f"{ability}: {score}")
        # TODO: Handle traits, resistances, proficiencies, special abilities
        self.description = self.description + " " + description
        self.species.ability_scores = self.ability_scores
        self.species.advantages = self._base_advantages
        self.spellcasting_ability = self.classes[0].spellcasting_ability if self.classes else "None"
        self.weapon_mastery = []
        self.actions_left = 1
        self.bonus_actions_left = 1
        # TODO: create a better actions handling system that accounts for multiattack, legendary actions, reactions, bonus actions, and action types (e.g. some abilities can only be used as a reaction, some can only be used on the turn you take the Attack action, etc.)

    def __str__(self):
        return f"{self.name}, a level {self.level} {self.species} {self.class_} with equipment: {', '.join(self.inventory)}"

    # ── Computed stat properties ─────────────────────────────────────────────

    @property
    def speed(self) -> int:
        """Effective walking speed in feet, derived from base speed and active conditions.

        Any condition with speed_override set forces the result to that value (0
        for all standard conditions like Grappled, Paralyzed, etc.).  Speed
        bonuses from Dash (bonus_speed) are included here so that zero-override
        conditions correctly suppress them.
        """
        for e in self.active_effects:
            if getattr(e, "speed_override", None) is not None:
                return 0
        s = self._base_speed + getattr(self, "bonus_speed", 0)
        for e in self.active_effects:
            s += getattr(e, "speed_delta", 0)
        return max(0, s)

    @property
    def d20_modifier(self) -> int:
        """Flat modifier applied to every d20 roll, derived from active conditions."""
        mod = 0
        for e in self.active_effects:
            mod += getattr(e, "d20_delta", 0)
        return mod

    @property
    def advantages(self) -> dict:
        """Effective advantages dict merged from base values and active conditions."""
        result = {
            "Saving Throws": list(self._base_advantages.get("Saving Throws", [])),
            "Skills": list(self._base_advantages.get("Skills", [])),
            "Abilities": list(self._base_advantages.get("Abilities", [])),
            "Attack": self._base_advantages.get("Attack", 0),
            "ToBeAttacked": self._base_advantages.get("ToBeAttacked", 0),
            "Initiative": self._base_advantages.get("Initiative", 0),
        }
        for e in self.active_effects:
            result["Attack"] += getattr(e, "adv_attack", 0)
            result["ToBeAttacked"] += getattr(e, "adv_to_be_attacked", 0)
            result["Initiative"] += getattr(e, "adv_initiative", 0)
            for item in getattr(e, "adv_saving_throws", ()):
                if item not in result["Saving Throws"]:
                    result["Saving Throws"].append(item)
            for item in getattr(e, "adv_skills", ()):
                if item not in result["Skills"]:
                    result["Skills"].append(item)
            for item in getattr(e, "adv_abilities", ()):
                if item not in result["Abilities"]:
                    result["Abilities"].append(item)
        return result

    @property
    def disadvantages(self) -> dict:
        """Effective disadvantages dict merged from base values and active conditions."""
        result = {
            "Saving Throws": list(self._base_disadvantages.get("Saving Throws", [])),
            "Skills": list(self._base_disadvantages.get("Skills", [])),
            "Abilities": list(self._base_disadvantages.get("Abilities", [])),
            "Attack": self._base_disadvantages.get("Attack", 0),
            "ToBeAttacked": self._base_disadvantages.get("ToBeAttacked", 0),
            "Initiative": self._base_disadvantages.get("Initiative", 0),
        }
        for e in self.active_effects:
            result["Attack"] += getattr(e, "disadv_attack", 0)
            result["ToBeAttacked"] += getattr(e, "disadv_to_be_attacked", 0)
            result["Initiative"] += getattr(e, "disadv_initiative", 0)
            for item in getattr(e, "disadv_saving_throws", ()):
                if item not in result["Saving Throws"]:
                    result["Saving Throws"].append(item)
            for item in getattr(e, "disadv_skills", ()):
                if item not in result["Skills"]:
                    result["Skills"].append(item)
            for item in getattr(e, "disadv_abilities", ()):
                if item not in result["Abilities"]:
                    result["Abilities"].append(item)
        return result

    @property
    def auto_fail(self) -> dict:
        """Effective auto-fail dict merged from base values and active conditions."""
        result = {
            "Saving Throws": list(self._base_auto_fail.get("Saving Throws", [])),
            "Skills": list(self._base_auto_fail.get("Skills", [])),
            "Abilities": list(self._base_auto_fail.get("Abilities", [])),
            "Attack": self._base_auto_fail.get("Attack", 0),
            "ToBeAttacked": self._base_auto_fail.get("ToBeAttacked", 0),
            "Initiative": self._base_auto_fail.get("Initiative", 0),
        }
        for e in self.active_effects:
            for ability in getattr(e, "auto_fail_saving_throws", ()):
                if ability not in result["Saving Throws"]:
                    result["Saving Throws"].append(ability)
        return result

    @property
    def resistances(self) -> list:
        """Effective damage resistances merged from base and active conditions."""
        result = list(self._base_resistances)
        for e in self.active_effects:
            for dtype in getattr(e, "bonus_resistances", ()):
                if dtype not in result:
                    result.append(dtype)
        return result

    @property
    def immunities(self) -> list:
        """Effective damage immunities merged from base and active conditions."""
        result = list(self._base_immunities)
        for e in self.active_effects:
            for dtype in getattr(e, "bonus_immunities", ()):
                if dtype not in result:
                    result.append(dtype)
        return result

    @property
    def weight(self) -> float:
        """Effective weight, multiplied by any active condition weight_multipliers."""
        w = self._base_weight
        for e in self.active_effects:
            w *= getattr(e, "weight_multiplier", 1)
        return w

    def level_up(self, class_, roll_for_health=False):
        from src.classes import Class
        idx = -1
        if class_ not in [cls.name for cls in self.classes]:
            self.classes.append(Class(name=class_, level=1))
        else:
            for idx, cls in enumerate(self.classes):
                if cls.name == class_:
                    cls.level_up(self)
                    break
        class_leveling = self.classes[idx]
        if self.species.species == "Dwarf":
            self.max_hp += 1
            self.current_hp += 1
        if self.feats and "Tough" in [feat.name for feat in self.feats]:
            self.max_hp += 2
            self.current_hp += 2
        if roll_for_health:
            hp = roll_dice(1, class_leveling.hit_dice) + self.get_ability_bonus("Constitution")
            self.max_hp += hp
            self.current_hp += hp
        else:
            hp = (class_leveling.hit_dice // 2) + 1 + self.get_ability_bonus("Constitution")
            self.max_hp += hp
            self.current_hp += hp
        self.level += 1
        self.proficiency_bonus = 2 + (self.level - 1) // 4
        self.species.proficiency_bonus = self.proficiency_bonus
        self.species.level = self.level

    def add_condition(self, condition):
        if isinstance(condition, list):
            for c in condition:
                self.add_condition(c)
            return
        elif isinstance(condition, str):
            try:
                condition = getattr(importlib.import_module("src.conditions"), condition)()
            except AttributeError:
                raise Exception("Could not find the requested item")
        try:
            condition.apply(self)
        except Exception:
            condition().apply(self)

    def remove_condition(self, condition):
        if isinstance(condition, list):
            for c in condition:
                self.remove_condition(c)
            return
        name = condition if isinstance(condition, str) else condition.name
        for active_effect in list(self.active_effects):
            if clean_text(getattr(active_effect, "name", "")).lower() == clean_text(name).lower():
                active_effect.remove(self)
                break

    def add_item(self, item, purchasing=False, quantity: int = 1):
        if isinstance(item, list):
            for i in item:
                self.add_item(i)
            return
        elif isinstance(item, str):
            try:
                item_object = getattr(importlib.import_module("src.items"), clean_text(item))(quantity=quantity)
            except AttributeError:
                raise Exception("Could not find the requested item")
        else:
            item_object = item
        if purchasing:
            item_object.purchase(self, quantity=quantity)
        else:
            # check existing items
            for i in self.inventory:
                if item_object.name == i.name:
                    i.quantity += quantity
                    return
            # if none matched, add a new one
            self.inventory.append(item_object)

    def remove_item(self, item, selling=False, quantity: int = 1):
        if isinstance(item, list):
            for i in item:
                self.remove_item(i)
            return
        elif isinstance(item, str):
            try:
                item_object = getattr(importlib.import_module("src.items"), clean_text(item))()
            except AttributeError:
                print("Could not find the requested item")
        else:
            item_object = item
        if selling:
            item_object.sell(self, quantity=quantity)
        else:
            for i in self.inventory:
                if i.name == item_object.name:
                    if quantity < i.quantity:
                        i.quantity -= quantity
                    else:
                        self.inventory.remove(item)

    def equip_item(self, item_name: str):
        item = None
        for i in self.inventory:
            if clean_text(item_name).lower() == clean_text(i.name).lower():
                item = i
                break
        if item is None:
            print(f"{self.name} does not have {item_name} in their inventory.")
            return
        hands_left = 2
        for equipped_item in self.equipped_items:
            if equipped_item.type == "Weapon":
                if "Two-Handed" in equipped_item.properties:
                    hands_left -= 2
                else:
                    hands_left -= 1
            if equipped_item.type == "Shield":
                hands_left -= 1
        if item.type == "Weapon":
            if "Two-Handed" in item.properties and hands_left < 2:
                print(f"Not enough hands to equip {item.name}. Unequip some items first.")
                return
            elif hands_left < 1:
                print(f"Not enough hands to equip {item.name}. Unequip some items first.")
                return
        elif item.type == "Shield":
            # can't have two shields
            for equipped_item in self.equipped_items:
                if equipped_item.type == "Shield":
                    self.unequip_item(equipped_item.name)
        elif item.type in ["Armor", "Clothing"]:
            # can't have two armors/clothing
            for equipped_item in self.equipped_items:
                if equipped_item.type in ["Armor", "Clothing"]:
                    self.unequip_item(equipped_item.name)
        if hasattr(item, "on_equip"):
            item.on_equip(self)
        equippable_item = deepcopy(item)
        equippable_item.quantity = 1
        self.remove_item(item, quantity=1)
        self.equipped_items.append(equippable_item)

    def unequip_item(self, item_name):
        item = None
        for i in self.equipped_items:
            if clean_text(item_name).lower() == clean_text(i.name).lower():
                item = i
                break
        if item is None:
            print(f"{self.name} does not have {item_name} equipped.")
            return
        self.equipped_items.remove(item)
        self.add_item(item)
        if hasattr(item, "on_unequip"):
            item.on_unequip(self)
        print(f"{self.name} has unequipped {item.name}.")

    def get_ability_bonus(self, ability):
        return (self.ability_scores[ability] - 10) // 2

    def get_armor_class(self):
        # Base AC
        ac = 10 + self.get_ability_bonus("Dexterity")
        unarmored = True
        for item in self.equipped_items:
            if item.type == "Armor":
                ac = item.ac(self)
                unarmored = False
        # Unarmored defense for barbarians
        if self.classes and self.classes[0].name == "Barbarian" and unarmored:
            ac = 10 + self.get_ability_bonus("Dexterity") + self.get_ability_bonus("Constitution")
        # Unarmored defense for monks
        if self.classes and self.classes[0].name == "Monk" and unarmored:
            ac = 10 + self.get_ability_bonus("Dexterity") + self.get_ability_bonus("Wisdom")
        for item in self.equipped_items:
            if item.type == "Shield" and self.classes[0].name != "Monk" and self.proficiencies["Armor"] and "Shield" in self.proficiencies["Armor"]:
                ac += item.ac(self)
        return ac
    get_ac = get_armor_class
    ac = get_armor_class

    def get_skill_bonus(self, skill):
        return self.get_ability_bonus(dnd_skills[skill]) + (self.proficiency_bonus if skill in self.proficiencies["Skills"] else 0)

    def attack(self, target, weapon_name: Optional[str] = None, action_type: str = "Action", lethal: bool = True):
        advantage_counter = 0
        charmed_by = [_.by for _ in self.active_effects if _.name == "Charmed"]
        for charmer in charmed_by:
            if charmer == target:
                print(f"{target} cannot be targeted due to charm.")
                return
        grappled_by = [_.by for _ in self.active_effects if _.name == "Grappled"]
        if len(grappled_by) > 0 and target not in grappled_by:
            print("Getting disadvantage for not attacking grappler")
            advantage_counter -= 1
        from src.items import Unarmed
        weapons = [Unarmed().on_equip(self)]
        weapon = None
        for item in self.equipped_items:
            if item.type == "Weapon":
                weapons.append(item)
        # Take the only equipped weapon or unarmed as default
        if len(weapons) < 3 and weapon_name is None:
            weapon = weapons[-1]
        else:
            for item in weapons:
                if item.name == weapon_name:
                    weapon = item
        if weapon is None:
            raise Exception(f"Weapon not found: {weapon_name}. Options are {[w.name for w in weapons]}")
        ability_bonus = self.get_ability_bonus("Strength")
        if "Finesse" in weapon.properties:
            ability_bonus = max([self.get_ability_bonus("Dexterity"), ability_bonus])
        proficiency_bonus = self.proficiency_bonus if weapon.category in self.proficiencies["Weapons"] else 0
        # give extra bonus to attack advantage if target marked with advantage to be attacked
        advantage_counter += target.advantages["ToBeAttacked"]
        advantage_counter -= target.disadvantages["ToBeAttacked"]
        print(f"{self.name} attacks {target.name} with {weapon.name}.")
        success, total, crit_fail, crit_success = self.roll_check(None, beat=target.ac(), bonus=ability_bonus + proficiency_bonus, check_type="Attack", advantage_counter=advantage_counter)
        dice_split = [int(_) for _ in weapon.damage.split("d")]
        if "Paralyzed" in [_.name for _ in target.active_effects] and success:
            print("It's a critical hit due to Paralysis.")
            crit_success = True
        if "Unconscious" in [_.name for _ in target.active_effects] and success:
            print("It's a critical hit due to Unconsciousness.")
            crit_success = True
        # HOUSE RULE: Critical success - double dice. Could also double the total below.
        if crit_success:
            dice_split[0] = dice_split[0] * 2
        # HOUSE RULE: Critical failure
        # TODO: Add some fun table of slip-ups for crit fails
        if crit_fail:
            pass
        if success:
            total = roll_dice(dice_split[0], dice_split[1]) + ability_bonus
            # Brutal Strike bonus damage
            brutal = next(
                (e for e in self.active_effects if getattr(e, "name", None) == "Brutal Strike"), None
            )
            if brutal is not None:
                extra = roll_dice(brutal.brutal_strike_dice, 10)
                print(f"  Brutal Strike adds {extra} damage ({brutal.brutal_strike_dice}d10)!")
                total += extra
                brutal.remove(self)
            print(f"The total damage done is {total}")
            if weapon.damage_type in target.resistances:
                print("The attack doesn't seem very effective.")
                total = total // 2
            elif weapon.damage_type in target.immunities:
                print("The attack did nothing at all!")
                total = 0
            target.current_hp -= total
        else:
            print("The attack missed!")
        if target.current_hp < 0 and lethal:
            target.current_hp = 0
            target.add_condition("Dead")
        elif target.current_hp < 0 and not lethal:
            target.current_hp = 1
            target.add_condition("Unconscious")

    def prepare_spell(self, spell):
        from src.spells import get_spells
        preparable_spells = sum([_.preparable_spells for _ in self.classes if hasattr(_, "preparable_spells")]) - len(self.prepared_spells)
        if preparable_spells <= 0:
            print("You cannot prepare any more spells.")
            return
        spellbook = None
        for item in self.inventory:
            if item.name.lower() == "spellbook":
                spellbook = item
                break
        if spellbook is None:
            print("You don't have a spellbook to prepare spells from.")
            return
        if isinstance(spell, str):
            spells = get_spells(classes=[_.name for _ in self.classes])
            for s in spells:
                if s.name == spell:
                    spell = s
                    break
        if isinstance(spell, str):
            print(f"{spell} is not a valid spell choice.")
            return
        for s in spellbook.known_spells:
            if s.name == spell.name:
                self.prepared_spells.append(s)
                print(f"{self.name} has prepared the spell {s.name}. You have {preparable_spells - 1} spell preparations left.")
                return
        print(f"You don't know the spell {spell.name} or it's not in your spellbook.")

    def cast_spell(self, spell, targets=[]):
        if any(getattr(e, "prevents_casting", False) for e in self.active_effects):
            print(f"{self.name} cannot cast spells right now.")
            return
        charmed_by = [_.by for _ in self.active_effects if getattr(_, "name", None) == "Charmed"]
        for charmer in charmed_by:
            if charmer in targets:
                print(f"{charmer.name} cannot be targeted due to charm.")
                return
        for s in self.spells:
            if s.name == spell:
                if s.uses_left is None or s.uses_left > 0:
                    if s.uses_left is not None:
                        s.uses_left -= 1
                    s.cast(self, targets or [self])
                else:
                    print(f"No uses left for {s.name}.")
                return
        print(f"{self.name} does not know the spell {spell}.")

    def use_special_ability(self, ability, targets=[]):
        charmed_by = [_.by for _ in self.active_effects if _.name == "Charmed"]
        for charmer in charmed_by:
            if charmer in targets:
                print(f"{charmed_by.name} cannot be targeted due to charm.")
                return
        for a in self.special_abilities:
            if a.name == ability:
                if a.uses_left is None or a.uses_left > 0:
                    if a.uses_left is not None:
                        a.uses_left -= 1
                    a.cast(self, targets or [self])
                else:
                    print(f"No uses left for {a.name}.")
                return
        print(f"{self.name} does not know the special ability {ability}.")

    def grapple(self, target):
        from src.conditions import Grappled
        Grappled(by=self).apply(target)

    def dash(self, as_bonus_action=False):
        if as_bonus_action:
            if self.bonus_actions_left <= 0:
                print("No bonus actions left to dash.")
                return
            self.bonus_actions_left -= 1
        else:
            if self.actions_left <= 0:
                print("No actions left to dash.")
                return
            self.actions_left -= 1
        self.bonus_speed = max([self._base_speed, self.swimming_speed, self.flying_speed, self.climbing_speed])

    def roll_check(self, ability, beat=None, bonus=0, check_type=None, advantage_counter=0, critical_threshold: int = 20, failure_threshold: int = 1, tie_succeeds: bool = True):
        # check type can be ["Abilities", "Saving Throws", "Skills", "Attack", "Initiative"]
        auto_fail = False
        if isinstance(self.auto_fail[check_type], list):
            auto_fail = ability in self.auto_fail[check_type]
        else:
            auto_fail = bool(self.auto_fail[check_type])
        if auto_fail:
            return False, 0, False, False
        roll = roll_dice(1, 20)
        bonus += self.d20_modifier
        if check_type in ["Abilities", "Saving Throws"]:
            bonus += self.get_ability_bonus(ability)
        elif check_type == "Skills":
            bonus += self.get_skill_bonus(ability)
        elif check_type == "Initiative":
            bonus += self.get_ability_bonus("Dexterity")
        if isinstance(self.advantages[check_type], list):
            for adv in self.advantages[check_type]:
                if adv == ability:
                    advantage_counter += 1
            for dadv in self.disadvantages[check_type]:
                if dadv == ability:
                    advantage_counter -= 1
        elif isinstance(self.advantages[check_type], int):
            advantage_counter += self.advantages[check_type]
            advantage_counter -= self.disadvantages[check_type]
        if advantage_counter > 0:
            roll2 = roll_dice(1, 20)
            print(f"Rolling with advantage: {roll} and {roll2}")
            roll = max(roll, roll2)
        elif advantage_counter < 0:
            roll2 = roll_dice(1, 20)
            print(f"Rolling with disadvantage: {roll} and {roll2}")
            roll = min(roll, roll2)
        if check_type in self.proficiencies and ability in self.proficiencies[check_type]:
            bonus += self.proficiency_bonus
        total = roll + bonus
        print(f"{self.name} rolls {roll} + {bonus} = {total}")
        success, total, crit_fail, crit_success = handle_roll_criticals(
            roll, total, beat, critical_threshold=critical_threshold,
            failure_threshold=failure_threshold,
            halfling_luck="Halfling Luck" in self.special_traits,
            tie_succeeds=tie_succeeds
        )
        # Indomitable Might: Strength checks/saves use Strength score as floor
        if check_type in ("Abilities", "Saving Throws") and ability == "Strength":
            if any(getattr(e, "indomitable_might", False) for e in self.active_effects):
                str_score = self.ability_scores.get("Strength", 10)
                if total < str_score:
                    print(f"  Indomitable Might raises total from {total} to {str_score}.")
                    total = str_score
                    success = beat is None or total >= beat
        return success, total, crit_fail, crit_success

    def rest(self, long=False):
        self.species.rest(long=long)
        if long:
            from src.conditions import Exhaustion
            self.current_hp = self.max_hp
            self.remove_condition("Exhaustion")
            self.prepared_spells = []
        else:
            # TODO: Implement short rest logic with hit die
            pass

    def move(self, map_, x: int, y: int, z: int = 0, budget: float = None,
             blocked_creatures=None) -> dict:
        """Move toward (x, y, z) using A* from map_.find_path().

        Step costs follow the Pythagorean theorem — moving through d axes costs
        sqrt(d) feet per cell_size (cardinal = 1x, diagonal = √2x, 3-D = √3x).
        Difficult terrain doubles each step's cost.

        Speed pool chosen from the path's z-range:
          - any step with z > 0  → flying_speed
          - any step with z < 0  → swimming_speed
          - otherwise            → speed (walking, includes bonus_speed)

        Args:
          budget            — optional cap on feet available for this call (used
                              by combat to support split movement).
          blocked_creatures — iterable of enemy creatures whose cells cannot be
                              entered. Ally cells can be passed through but the
                              creature cannot land on any occupied cell.

        Returns a dict:
          path               — full planned path as list of (x, y, z) cells
          reached            — final position after consuming available movement
          movement_used      — feet spent (rounded to nearest foot)
          movement_remaining — feet remaining within this call's budget
          blocked            — True if no path to the target exists
        """
        import math as _math
        if self.position is None:
            raise RuntimeError(f"{self.name} is not placed on a map.")

        path = map_.find_path(self, x, y, z, blocked_creatures=blocked_creatures)
        avail = budget if budget is not None else self.speed
        if path is None:
            return {
                "path": [], "reached": self.position,
                "movement_used": 0, "movement_remaining": round(avail),
                "blocked": True,
            }
        if not path:
            return {
                "path": [], "reached": self.position,
                "movement_used": 0, "movement_remaining": round(avail),
                "blocked": False,
            }

        needs_fly  = any(pz > 0 for _, _, pz in path)
        needs_swim = any(pz < 0 for _, _, pz in path)
        if needs_fly:
            speed_ft = self.flying_speed
        elif needs_swim:
            speed_ft = self.swimming_speed
        else:
            # self.speed already incorporates bonus_speed and condition overrides
            speed_ft = self.speed
        if budget is not None:
            speed_ft = min(speed_ft, budget)

        cost_ft = 0.0
        # Track the last cell that has no other creature on it — that is where
        # the creature will land if it runs out of movement on an occupied cell.
        last_free_pos = self.position
        last_free_cost = 0.0
        prev = self.position
        final_pos = self.position
        for cell in path:
            dims = sum(1 for a, b in zip(prev, cell) if a != b)
            step_ft = _math.sqrt(dims) * map_.cell_size
            if cell in map_.difficult_terrain:
                step_ft *= 2
            if cost_ft + step_ft > speed_ft:
                break
            cost_ft += step_ft
            final_pos = cell
            prev = cell
            # Is this cell free of other creatures?
            if not any(c is not self for c in map_.get_creatures_at(*cell)):
                last_free_pos = cell
                last_free_cost = cost_ft

        # Cannot land on an occupied cell — back up to the last free cell.
        if any(c is not self for c in map_.get_creatures_at(*final_pos)):
            final_pos = last_free_pos
            cost_ft = last_free_cost

        fx, fy, fz = final_pos
        map_.move_creature(self, fx, fy, fz)
        return {
            "path": path,
            "reached": final_pos,
            "movement_used": round(cost_ft),
            "movement_remaining": round(speed_ft - cost_ft),
            "blocked": False,
        }
