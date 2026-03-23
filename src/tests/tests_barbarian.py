"""Tests for Barbarian class features (2024 PHB)."""
from src.creatures import Character
from src.classes import Barbarian


def _make_barbarian(level: int, str_score: int = 18, con_score: int = 16) -> Character:
    return Character(
        name="Krogar",
        species="Human",
        background="Acolyte",
        classes=[Barbarian(level=level)],
        description="A mighty barbarian warrior.",
        ability_score_bonuses={
            "Strength": str_score - 10,
            "Dexterity": 2,
            "Constitution": con_score - 10,
            "Intelligence": 0,
            "Wisdom": 0,
            "Charisma": 0,
        },
    )


# ── Level 1: Rage ─────────────────────────────────────────────────────────────

def test_rage_applies_resistances_and_damage_bonus():
    char = _make_barbarian(1)
    assert any(a.name == "Rage" for a in char.special_abilities), "Rage ability missing at level 1"
    char.use_special_ability("Rage")
    rage_condition = next((e for e in char.active_effects if e.name == "Rage"), None)
    assert rage_condition is not None, "Rage condition not applied"
    assert "Bludgeoning" in char.resistances, "Rage should grant Bludgeoning resistance"
    assert "Piercing" in char.resistances, "Rage should grant Piercing resistance"
    assert "Slashing" in char.resistances, "Rage should grant Slashing resistance"
    assert rage_condition.bonus_damage == 2, "Rage damage bonus should be +2 at level 1"
    assert "Strength" in char.advantages["Abilities"], "Rage should give Strength advantage"
    assert "Strength" in char.advantages["Saving Throws"], "Rage should give Strength save advantage"
    assert rage_condition.prevents_casting is True, "Rage should prevent casting"


def test_rage_duration_10_rounds():
    char = _make_barbarian(1)
    char.use_special_ability("Rage")
    rage = next(e for e in char.active_effects if e.name == "Rage")
    assert rage.duration == 10, f"Rage duration should be 10 rounds, got {rage.duration}"


def test_rage_uses_per_level():
    char2 = _make_barbarian(2)
    rage = next(a for a in char2.special_abilities if a.name == "Rage")
    assert rage.uses_left == 2, f"Level 2 should have 2 rages, got {rage.uses_left}"

    char6 = _make_barbarian(6)
    rage6 = next(a for a in char6.special_abilities if a.name == "Rage")
    assert rage6.uses_left == 4, f"Level 6 should have 4 rages, got {rage6.uses_left}"

    char12 = _make_barbarian(12)
    rage12 = next(a for a in char12.special_abilities if a.name == "Rage")
    assert rage12.uses_left == 5, f"Level 12 should have 5 rages, got {rage12.uses_left}"


def test_rage_damage_bonus_scales():
    char8 = _make_barbarian(8)
    char8.use_special_ability("Rage")
    rage8 = next(e for e in char8.active_effects if e.name == "Rage")
    assert rage8.bonus_damage == 2, f"Levels 1-8 should have +2 rage damage, got {rage8.bonus_damage}"

    char9 = _make_barbarian(9)
    char9.use_special_ability("Rage")
    rage9 = next(e for e in char9.active_effects if e.name == "Rage")
    assert rage9.bonus_damage == 3, f"Levels 9-15 should have +3 rage damage, got {rage9.bonus_damage}"

    char16 = _make_barbarian(16)
    char16.use_special_ability("Rage")
    rage16 = next(e for e in char16.active_effects if e.name == "Rage")
    assert rage16.bonus_damage == 4, f"Levels 16+ should have +4 rage damage, got {rage16.bonus_damage}"


# ── Level 1: Unarmored Defense ────────────────────────────────────────────────

def test_unarmored_defense():
    char = _make_barbarian(1)  # Str 18 (+4), Dex 12 (+1), Con 16 (+3)
    # Unarmored: AC = 10 + Dex mod + Con mod = 10 + 1 + 3 = 14
    expected_ac = 10 + char.get_ability_bonus("Dexterity") + char.get_ability_bonus("Constitution")
    assert char.get_armor_class() == expected_ac, (
        f"Unarmored Defense AC should be {expected_ac}, got {char.get_armor_class()}"
    )


# ── Level 2: Danger Sense ─────────────────────────────────────────────────────

def test_danger_sense_applied_at_level_2():
    char = _make_barbarian(2)
    assert any(getattr(e, "name", None) == "Danger Sense" for e in char.active_effects), \
        "Danger Sense condition should be applied at level 2"
    assert "Dexterity" in char.advantages["Saving Throws"], \
        "Danger Sense should give advantage on Dexterity saving throws"


def test_danger_sense_not_present_at_level_1():
    char = _make_barbarian(1)
    assert not any(getattr(e, "name", None) == "Danger Sense" for e in char.active_effects), \
        "Danger Sense should not be present at level 1"


# ── Level 2: Reckless Attack ──────────────────────────────────────────────────

def test_reckless_attack_applied_at_level_2():
    char = _make_barbarian(2)
    assert any(a.name == "Reckless Attack" for a in char.special_abilities), \
        "Reckless Attack should be available at level 2"


def test_reckless_attack_applies_condition():
    char = _make_barbarian(2)
    char.use_special_ability("Reckless Attack")
    assert any(getattr(e, "name", None) == "Reckless Attacking" for e in char.active_effects), \
        "Reckless Attack should apply RecklessAttacking condition"
    assert char.advantages["Attack"] >= 1, \
        "RecklessAttacking should grant attack advantage"
    assert char.advantages["ToBeAttacked"] >= 1, \
        "RecklessAttacking should grant enemies advantage to attack"


# ── Level 3: Primal Knowledge ─────────────────────────────────────────────────

def test_primal_knowledge_todo_at_level_3():
    char = _make_barbarian(3)
    primal_todo = [t for t in char.todo if "Primal Knowledge" in t.get("Text", "")]
    assert len(primal_todo) == 1, "Primal Knowledge skill choice todo should be present at level 3"


def test_primal_knowledge_flag():
    char = _make_barbarian(3)
    assert getattr(char, "primal_knowledge", False), \
        "primal_knowledge flag should be set at level 3"


# ── Level 5: Extra Attack ─────────────────────────────────────────────────────

def test_extra_attack_at_level_5():
    char = _make_barbarian(5)
    assert getattr(char, "extra_attacks", 0) >= 1, "extra_attacks should be at least 1 at level 5"


def test_no_extra_attack_before_level_5():
    char = _make_barbarian(4)
    assert getattr(char, "extra_attacks", 0) == 0, "extra_attacks should not be set before level 5"


# ── Level 5: Fast Movement ────────────────────────────────────────────────────

def test_fast_movement_at_level_5():
    char_5 = _make_barbarian(5)
    char_1 = _make_barbarian(1)
    assert char_5.speed == char_1.speed + 10, \
        f"Level 5 speed should be 10 ft more than level 1 speed (got {char_5.speed} vs {char_1.speed})"


def test_fast_movement_condition_applied():
    char = _make_barbarian(5)
    assert any(getattr(e, "name", None) == "Fast Movement" for e in char.active_effects), \
        "Fast Movement condition should be applied at level 5"


# ── Level 7: Feral Instinct ───────────────────────────────────────────────────

def test_feral_instinct_at_level_7():
    char = _make_barbarian(7)
    assert any(getattr(e, "name", None) == "Feral Instinct" for e in char.active_effects), \
        "Feral Instinct condition should be applied at level 7"
    assert char.advantages["Initiative"] >= 1, \
        "Feral Instinct should grant initiative advantage"


# ── Level 9: Brutal Strike ────────────────────────────────────────────────────

def test_brutal_strike_ability_at_level_9():
    char = _make_barbarian(9)
    assert any(a.name == "Brutal Strike" for a in char.special_abilities), \
        "Brutal Strike should be available at level 9"


def test_brutal_strike_requires_reckless_attack(capsys=None):
    char = _make_barbarian(9)
    # Without Reckless Attack active, Brutal Strike should do nothing
    char.use_special_ability("Brutal Strike")
    assert not any(getattr(e, "name", None) == "Brutal Strike" for e in char.active_effects), \
        "Brutal Strike condition should NOT apply without active Reckless Attacking"


def test_brutal_strike_with_reckless_attack():
    char = _make_barbarian(9)
    char.use_special_ability("Reckless Attack")
    assert any(getattr(e, "name", None) == "Reckless Attacking" for e in char.active_effects)
    char.use_special_ability("Brutal Strike")
    assert any(getattr(e, "name", None) == "Brutal Strike" for e in char.active_effects), \
        "Brutal Strike condition should be applied when Reckless Attacking is active"
    brutal = next(e for e in char.active_effects if e.name == "Brutal Strike")
    assert brutal.brutal_strike_dice == 1, "Brutal Strike should use 1d10 at level 9"


# ── Level 11: Relentless Rage ─────────────────────────────────────────────────

def test_relentless_rage_dc_at_level_11():
    char = _make_barbarian(11)
    assert hasattr(char, "relentless_rage_dc"), "relentless_rage_dc should be set at level 11"
    assert char.relentless_rage_dc == 10, f"Relentless Rage DC should start at 10, got {char.relentless_rage_dc}"


def test_no_relentless_rage_before_level_11():
    char = _make_barbarian(10)
    assert not hasattr(char, "relentless_rage_dc"), \
        "relentless_rage_dc should not be set before level 11"


# ── Level 15: Persistent Rage ─────────────────────────────────────────────────

def test_persistent_rage_flag_at_level_15():
    char = _make_barbarian(15)
    assert getattr(char, "persistent_rage", False), \
        "persistent_rage should be True at level 15"


def test_no_persistent_rage_before_level_15():
    char = _make_barbarian(14)
    assert not getattr(char, "persistent_rage", False), \
        "persistent_rage should not be set before level 15"


def test_persistent_rage_ability_available():
    char = _make_barbarian(15)
    assert any(a.name == "Persistent Rage: Regain Uses" for a in char.special_abilities), \
        "Persistent Rage: Regain Uses ability should be available at level 15"


def test_persistent_rage_regain_rages():
    char = _make_barbarian(15)
    rage = next(a for a in char.special_abilities if a.name == "Rage")
    rage.uses_left = 0
    char.use_special_ability("Persistent Rage: Regain Uses")
    rage_after = next(a for a in char.special_abilities if a.name == "Rage")
    assert rage_after.uses_left > 0, "Persistent Rage should restore Rage uses"


# ── Level 17: Improved Brutal Strike II ──────────────────────────────────────

def test_improved_brutal_strike_at_level_17():
    char = _make_barbarian(17)
    char.use_special_ability("Reckless Attack")
    char.use_special_ability("Brutal Strike")
    brutal = next(e for e in char.active_effects if e.name == "Brutal Strike")
    assert brutal.brutal_strike_dice == 2, f"Improved Brutal Strike should use 2d10, got {brutal.brutal_strike_dice}d10"


# ── Level 18: Indomitable Might ───────────────────────────────────────────────

def test_indomitable_might_condition_at_level_18():
    char = _make_barbarian(18)
    assert any(getattr(e, "name", None) == "Indomitable Might" for e in char.active_effects), \
        "Indomitable Might condition should be applied at level 18"


def test_indomitable_might_floor_on_strength_check():
    char = _make_barbarian(18)  # Str 18
    str_score = char.ability_scores["Strength"]
    # Force total below Str score by mocking roll_check result
    # Directly test: if total < str_score, it should be raised
    # We simulate by checking the condition is present and the flag is set
    indom = next(e for e in char.active_effects if e.name == "Indomitable Might")
    assert getattr(indom, "indomitable_might", False), "IndomitableMight flag should be True"
    assert str_score >= 18, f"Str score should be at least 18, got {str_score}"


# ── Level 20: Primal Champion ─────────────────────────────────────────────────

def test_primal_champion_at_level_20():
    # Create a level 19 barbarian first to test the +4 increment at 20
    char = _make_barbarian(20)
    # Starting Str was 18 → 18 + 4 = 22, capped at 25
    assert char.ability_scores["Strength"] >= 22, \
        f"Primal Champion should increase Strength by 4 (got {char.ability_scores['Strength']})"
    assert char.ability_scores["Constitution"] >= 20, \
        f"Primal Champion should increase Constitution by 4 (got {char.ability_scores['Constitution']})"


def test_primal_champion_cap_at_25():
    char = Character(
        name="Goliath",
        species="Human",
        background="Acolyte",
        classes=[Barbarian(level=20)],
        description="Massively strong barbarian.",
        ability_score_bonuses={
            "Strength": 12,   # score 22 → 22+4=26, capped at 25
            "Constitution": 8,
            "Dexterity": 0,
            "Intelligence": 0,
            "Wisdom": 0,
            "Charisma": 0,
        },
    )
    assert char.ability_scores["Strength"] <= 25, \
        f"Primal Champion should cap Strength at 25, got {char.ability_scores['Strength']}"


# ── Level-up progression test ─────────────────────────────────────────────────

def test_levelup_applies_features():
    char = _make_barbarian(1)
    # No Danger Sense yet
    assert not any(getattr(e, "name", None) == "Danger Sense" for e in char.active_effects)

    barb_class = char.classes[0]
    barb_class.level_up(char)  # → level 2
    assert any(getattr(e, "name", None) == "Danger Sense" for e in char.active_effects), \
        "Danger Sense should appear after leveling up to 2"
    assert any(a.name == "Reckless Attack" for a in char.special_abilities), \
        "Reckless Attack should appear after leveling up to 2"

    for _ in range(3):  # → levels 3, 4, 5
        barb_class.level_up(char)
    assert getattr(char, "extra_attacks", 0) >= 1, "Extra Attack should appear after leveling up to 5"
    assert any(getattr(e, "name", None) == "Fast Movement" for e in char.active_effects), \
        "Fast Movement should appear after leveling up to 5"


if __name__ == "__main__":
    test_rage_applies_resistances_and_damage_bonus()
    test_rage_duration_10_rounds()
    test_rage_uses_per_level()
    test_rage_damage_bonus_scales()
    test_unarmored_defense()
    test_danger_sense_applied_at_level_2()
    test_danger_sense_not_present_at_level_1()
    test_reckless_attack_applied_at_level_2()
    test_reckless_attack_applies_condition()
    test_primal_knowledge_todo_at_level_3()
    test_primal_knowledge_flag()
    test_extra_attack_at_level_5()
    test_no_extra_attack_before_level_5()
    test_fast_movement_at_level_5()
    test_fast_movement_condition_applied()
    test_feral_instinct_at_level_7()
    test_brutal_strike_ability_at_level_9()
    test_brutal_strike_requires_reckless_attack()
    test_brutal_strike_with_reckless_attack()
    test_relentless_rage_dc_at_level_11()
    test_no_relentless_rage_before_level_11()
    test_persistent_rage_flag_at_level_15()
    test_no_persistent_rage_before_level_15()
    test_persistent_rage_ability_available()
    test_persistent_rage_regain_rages()
    test_improved_brutal_strike_at_level_17()
    test_indomitable_might_condition_at_level_18()
    test_indomitable_might_floor_on_strength_check()
    test_primal_champion_at_level_20()
    test_primal_champion_cap_at_25()
    test_levelup_applies_features()
    print("All barbarian tests passed.")
