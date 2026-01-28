from src.creature import Character


def test_aasimar_abilities():
    char = Character(
        name="Ysraela",
        species="Aasimar",
        classes=[{"name": "Ranger", "level": 1}],
        description="Ysraela is an angelic ranger, known for her sharp senses and unwavering determination in the face of danger.",
        ability_score_bonuses={
            "Strength": 12,
            "Dexterity": 16,
            "Constitution": 12,
            "Intelligence": 12,
            "Wisdom": 14,
            "Charisma": 16
        }
    )
    char2 = Character(
        name="Thokk",
        species="Aasimar",
        classes=[{"name": "Fighter", "level": 3}],
        description="Thokk is a celestial warrior, wielding his sword with divine purpose and protecting the innocent from evil.",
        ability_score_bonuses={
            "Strength": 16,
            "Dexterity": 12,
            "Constitution": 14,
            "Intelligence": 10,
            "Wisdom": 12,
            "Charisma": 14
        }
    )
    print(f"{char2.name} is on death's door!")
    char2.current_hp = 1
    char.use_special_ability("Healing Hands", targets=[char2])
    assert char2.current_hp > 1, "Healing Hands did not heal the target properly"
    char.use_special_ability("Celestial Revelation: Heavenly Wings")
    assert char.flying_speed == 0, "Heavenly Wings shouldn't work at level 1"
    char2.use_special_ability("Celestial Revelation: Heavenly Wings")
    assert char2.flying_speed == char2.speed, "Heavenly Wings did not set flying speed correctly"
    char2.use_special_ability("Celestial Revelation: Inner Radiance")
    assert "Celestial Revelation: Inner Radiance" not in char2.active_effects, "Inner Radiance was allowed to be set even though no uses were left due to shared cooldown"
    print(f"{char2.name} is on death's door!")
    char2.current_hp = 1
    char.use_special_ability("Healing Hands", targets=[char2])
    assert char2.current_hp == 1, "Healing Hands was allowed to be used twice when only one use was allowed"
    print(f"{char.name} is on death's door!")
    char.current_hp = 1
    char.rest(long=True)
    assert char.current_hp == char.max_hp, "Long rest did not restore character to full health"
    char.use_special_ability("Healing Hands", targets=[char2])
    assert char2.current_hp > 1, "Healing Hands did not heal the target properly after long rest"


def test_dragonborn_abilities():
    char = Character(
        name="Drake",
        species="Dragonborn",
        classes=[{"name": "Fighter", "level": 5}],
        description="Drake is a fierce dragonborn warrior, known for his strength and fiery breath.",
        ability_score_bonuses={
            "Strength": 16,
            "Dexterity": 12,
            "Constitution": 14,
            "Intelligence": 10,
            "Wisdom": 12,
            "Charisma": 14
        },
        ancestry="Red"
    )
    char2 = Character(
        name="Gobby",
        species="Goblin",
        classes=[{"name": "Rogue", "level": 2}],
        description="A sneaky goblin, always looking for trouble.",
        ability_score_bonuses={
            "Strength": 8,
            "Dexterity": 14,
            "Constitution": 10,
            "Intelligence": 10,
            "Wisdom": 8,
            "Charisma": 8
        }
    )
    char2.current_hp = 20
    char.use_special_ability("Breath Weapon: Cone", targets=[char2])
    assert char2.current_hp < 20, "Breath Weapon did not deal damage properly"


if __name__ == "__main__":
    test_aasimar_abilities()
    test_dragonborn_abilities()
    print("All tests passed.")
