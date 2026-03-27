from src.creatures import Character
from src.spells import Spell
from src.items import *
from src.classes._base import (
    Class, _HALF_CASTER_SLOTS,
)


# 2024 PHB: Paladin Fighting Style options
_PALADIN_FIGHTING_STYLES = [
    "Blessed Warrior",
    "Blind Fighting",
    "Defense",
    "Dueling",
    "Great Weapon Fighting",
    "Interception",
    "Protection",
]

# 2024 PHB subclasses (Sacred Oaths)
_PALADIN_SUBCLASSES = [
    "Oath of Devotion",
    "Oath of Glory",
    "Oath of the Ancients",
    "Oath of Vengeance",
]

# Weapon mastery options available to Paladins (2024 PHB)
_PALADIN_WEAPON_MASTERY_OPTIONS = [
    "Battleaxe", "Flail", "Glaive", "Greataxe", "Greatsword", "Halberd",
    "Handaxe", "Lance", "Longsword", "Maul", "Morningstar", "Pike",
    "Rapier", "Scimitar", "Shortsword", "Trident", "Warhammer", "War Pick", "Whip",
]


# Prepared spells by level
PREPARABLE_SPELLS = [2, 3, 4, 5, 6, 6, 7, 7, 9, 9, 10, 10, 11, 11, 12, 12, 14, 14, 15, 15]


class Paladin(Class):
    PALADIN_SUBCLASSES = _PALADIN_SUBCLASSES
    PALADIN_FIGHTING_STYLES = _PALADIN_FIGHTING_STYLES

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
        self.proficiencies["Skills"] = [
            "Athletics", "Insight", "Intimidation", "Medicine", "Persuasion", "Religion"
        ]
        self.lay_on_hands_pool = 5 * level
        self.completed_levelup_to = 0

    # ── Equipment ─────────────────────────────────────────────────────────────

    def select_starting_equipment(self, character: Character, choices, **kwargs):
        if "Gold" in choices:
            character.gold += 150
        else:
            character.add_item([ChainMail(), Shield(), Longsword(), HolySymbol(), ScholarsPack()])
            character.gold += 9

    # ── Lay on Hands helpers ───────────────────────────────────────────────────

    def _build_lay_on_hands_ability(self):
        pool = self.lay_on_hands_pool
        return Spell(
            name="Lay on Hands",
            casting_time="Action",
            range_="Touch",
            components=[],
            duration="Instantaneous",
            description=(
                f"You have a pool of {pool} HP (restored on Long Rest). "
                "As an Action, touch a creature to restore any number of HP from the pool, "
                "or spend 5 HP from the pool to remove one disease or neutralize one poison "
                "affecting the creature. Has no effect on Undead or Constructs."
            ),
            uses_left=pool,
            cooldown="Long Rest",
        )

    def _refresh_lay_on_hands(self, character: Character):
        """Replace the Lay on Hands ability with a fresh one reflecting the current level."""
        character.special_abilities = [
            a for a in character.special_abilities if a.name != "Lay on Hands"
        ] + [self._build_lay_on_hands_ability()]

    # ── Subclass / fighting style helpers ─────────────────────────────────────

    def _set_skill_proficiencies(self, character: Character, choices, **kwargs):
        character.proficiencies["Skills"] += choices

    def _set_subclass(self, character: Character, choices, **kwargs):
        self.subclass = choices[0]

    def _apply_fighting_style(self, character: Character, choices, **kwargs):
        character.special_traits.append(f"Fighting Style: {choices[0]}")

    def _apply_weapon_mastery(self, character: Character, choices, **kwargs):
        character.weapon_mastery += choices

    # ── Level feature application ──────────────────────────────────────────────

    def _apply_level_features(self, character: Character, level: int):
        """Apply all Paladin features unlocked at the given level."""

        if level == 1:
            # ── Lay on Hands ──────────────────────────────────────────────────
            if not isinstance(character.special_abilities, list):
                character.special_abilities = []
            character.special_abilities.append(self._build_lay_on_hands_ability())

            # ── Spellcasting ──────────────────────────────────────────────────
            character.special_traits.append(
                "Spellcasting: You can cast Paladin spells using Charisma as your spellcasting ability. "
                "Spell save DC = 8 + proficiency bonus + Charisma modifier."
            )

            # ── Weapon Mastery ────────────────────────────────────────────────
            character.todo.extend([
                {
                    "Text": "Select starting equipment or gold: "
                            "(Chain Mail, Shield, Longsword, Holy Symbol, Scholar's Pack, 9 GP) or (150 GP)",
                    "Options": ["Starting Equipment", "Gold"],
                    "Function": self.select_starting_equipment,
                },
                {
                    "Text": "Choose 2 skills: Athletics, Insight, Intimidation, Medicine, Persuasion, Religion.",
                    "Options": self.proficiencies["Skills"],
                    "Choices": 2,
                    "AllowSame": False,
                    "Function": self._set_skill_proficiencies,
                },
                {
                    "Text": "Choose 2 weapons to gain Weapon Mastery in.",
                    "Options": _PALADIN_WEAPON_MASTERY_OPTIONS,
                    "Choices": 2,
                    "Function": self._apply_weapon_mastery,
                },
            ])

        elif level == 2:
            # ── Paladin's Smite ───────────────────────────────────────────────
            # 2024 PHB: Renamed from Divine Smite. Now requires a Bonus Action to activate
            # (no longer free/automatic). You choose to smite AFTER you know the attack hit.
            character.special_abilities.append(Spell(
                name="Paladin's Smite",
                casting_time="Bonus Action",
                range_="Self",
                components=[],
                duration="Instantaneous",
                description=(
                    "When you hit a target with a melee weapon or Unarmed Strike, you can expend one "
                    "Paladin spell slot as a Bonus Action to deal extra Radiant damage to the target: "
                    "2d8 for a 1st-level slot, +1d8 for each slot level above 1st (max 5d8 for a 5th-level slot). "
                    "The damage increases by 1d8 if the target is a Fiend or Undead. "
                    "You can use Paladin's Smite no more than once per turn."
                ),
                uses_left=None,
                cooldown=None,
            ))

            # ── Fighting Style ────────────────────────────────────────────────
            character.todo.append({
                "Text": "Choose a Paladin Fighting Style.",
                "Options": _PALADIN_FIGHTING_STYLES,
                "Function": self._apply_fighting_style,
            })

        elif level == 3:
            # ── Divine Health ─────────────────────────────────────────────────
            character.special_traits.append(
                "Divine Health: The divine magic flowing through you makes you immune to disease."
            )

            # ── Channel Divinity ──────────────────────────────────────────────
            # 2024 PHB: Channel Divinity gains 2 uses at level 11, 3 uses at level 18.
            # The specific effect depends on the chosen Sacred Oath.
            cd_uses = 1 if self.level < 11 else 2 if self.level < 18 else 3
            character.special_abilities.append(Spell(
                name="Channel Divinity",
                casting_time="Action",
                range_="Self",
                components=[],
                duration="Instantaneous",
                description=(
                    "You channel divine energy through your holy symbol to produce a magical effect. "
                    "The specific effect is determined by your Sacred Oath subclass "
                    "(e.g., Sacred Weapon for Oath of Devotion, Peerless Athlete for Oath of Glory, "
                    "Nature's Wrath for Oath of the Ancients, Vow of Enmity for Oath of Vengeance). "
                    "You regain expended uses when you finish a Short or Long Rest."
                ),
                uses_left=cd_uses,
                cooldown="Short Rest",
            ))

            # ── Sacred Oath (Subclass) ────────────────────────────────────────
            character.todo.append({
                "Text": "Choose your Paladin subclass (Sacred Oath).",
                "Options": _PALADIN_SUBCLASSES,
                "Function": self._set_subclass,
            })

        elif level == 5:
            # ── Extra Attack ──────────────────────────────────────────────────
            character.extra_attacks = getattr(character, "extra_attacks", 0) + 1

            # ── Faithful Steed ────────────────────────────────────────────────
            character.special_traits.append(
                "Faithful Steed: You can call on the aid of an otherworldly steed. You always have "
                "Find Steed prepared and can cast it without expending a spell slot. When you cast it, "
                "the steed becomes a celestial, fey, or fiend (your choice)."
            )

        elif level == 6:
            # ── Aura of Protection ────────────────────────────────────────────
            cha_mod = max(1, (character.ability_scores.get("Charisma", 10) - 10) // 2)
            character.special_traits.append(
                f"Aura of Protection: While you are conscious, you and friendly creatures within 10 feet "
                f"of you add +{cha_mod} (your Charisma modifier, minimum +1) to all saving throws. "
                "The range extends to 30 feet at level 18."
            )

        elif level == 7:
            # ── Aura of Courage ───────────────────────────────────────────────
            character.special_traits.append(
                "Aura of Courage: While you are conscious, you and friendly creatures within 10 feet "
                "of you can't be Frightened. The range extends to 30 feet at level 18."
            )

        elif level == 9:
            # ── Abjure Foes ───────────────────────────────────────────────────
            # 2024 PHB: Uses Channel Divinity; up to Cha mod creatures (min 1); targets Fiends and Undead.
            cha_mod = max(1, (character.ability_scores.get("Charisma", 10) - 10) // 2)
            character.special_traits.append(
                f"Abjure Foes: As an Action, expend one use of Channel Divinity and present your holy symbol. "
                f"Choose up to {cha_mod} (your Charisma modifier, minimum 1) Fiends and/or Undead that you can "
                "see within 60 feet of you. Each target must succeed on a Wisdom saving throw or be Frightened "
                "of you for 1 minute (save DC = your spell save DC). While Frightened, the target's Speed is 0. "
                "A Frightened target repeats the saving throw at the end of each of its turns, ending the effect "
                "on a success. Once you use this feature, you can't use it again until you finish a Short or Long Rest."
            )

        elif level == 10:
            # ── Aura of Courage and Aura of Protection apply to allies with Cha mod ─
            # No new feature at 10 in 2024 PHB for base class (subclass features apply here)
            pass

        elif level == 11:
            # ── Radiant Strikes ───────────────────────────────────────────────
            character.special_traits.append(
                "Radiant Strikes: Your strikes are infused with divine energy. When you hit a target with a "
                "melee weapon or Unarmed Strike, the target takes an extra 1d8 Radiant damage."
            )
            # Channel Divinity gains a second use at level 11; refresh it
            self._refresh_channel_divinity(character)

        elif level == 14:
            # ── Restoring Touch ───────────────────────────────────────────────
            character.special_traits.append(
                "Restoring Touch: When you use Lay on Hands on a creature, you can also remove one of the "
                "following conditions from it at no HP cost: Blinded, Charmed, Deafened, Frightened, "
                "Paralyzed, or Stunned."
            )

        elif level == 18:
            # ── Aura Expansion ────────────────────────────────────────────────
            character.special_traits.append(
                "Aura Expansion: Your Aura of Protection and Aura of Courage now extend to 30 feet "
                "instead of 10 feet."
            )
            # Channel Divinity gains a third use at level 18; refresh it
            self._refresh_channel_divinity(character)

        elif level == 19:
            # ── Epic Boon ─────────────────────────────────────────────────────
            character.todo.append({
                "Text": "Choose an Epic Boon feat.",  # TODO: Choose an Epic Boon feat.
                "Options": ["Epic Boon of Combat Prowess", "Epic Boon of Dimensional Travel",
                            "Epic Boon of Energy Resistance", "Epic Boon of Fortitude",
                            "Epic Boon of Irresistible Offense", "Epic Boon of Luck",
                            "Epic Boon of Night Spirit", "Epic Boon of Peerless Aim",
                            "Epic Boon of Recovery", "Epic Boon of Skill Proficiency",
                            "Epic Boon of Speed", "Epic Boon of Spell Recall",
                            "Epic Boon of the Night Spirit", "Epic Boon of Truesight"],
                "Function": lambda char, choices, **kw: char.feats.append(choices[0]),
            })

        elif level == 20:
            # ── Holy Nimbus ───────────────────────────────────────────────────
            character.special_abilities.append(Spell(
                name="Holy Nimbus",
                casting_time="Bonus Action",
                range_="Self",
                components=[],
                duration="Up to 10 minutes (Concentration)",
                description=(
                    "As a Bonus Action, you can surround yourself with an aura of sunlight. "
                    "For 10 minutes you emit Bright Light in a 30-foot radius and Dim Light for an "
                    "additional 30 feet. At the start of each of your turns, each enemy within the "
                    "Bright Light takes 10 Radiant damage. In addition, for the duration, you have "
                    "Advantage on saving throws against spells cast by Fiends or Undead."
                ),
                uses_left=1,
                cooldown="Long Rest",
            ))

        # ── Refresh spell slots and Lay on Hands pool ─────────────────────────
        self.spell_slots = dict(_HALF_CASTER_SLOTS[level - 1])
        self.spell_slots_remaining = dict(_HALF_CASTER_SLOTS[level - 1])
        self.preparable_spells = PREPARABLE_SPELLS[self.level - 1]
        self.lay_on_hands_pool = 5 * level

    def _refresh_channel_divinity(self, character: Character):
        """Replace the Channel Divinity ability with an updated one for the current use count."""
        cd_uses = 1 if self.level < 11 else 2 if self.level < 18 else 3
        character.special_abilities = [
            a for a in character.special_abilities if a.name != "Channel Divinity"
        ] + [Spell(
            name="Channel Divinity",
            casting_time="Action",
            range_="Self",
            components=[],
            duration="Instantaneous",
            description=(
                "You channel divine energy through your holy symbol to produce a magical effect. "
                "The specific effect is determined by your Sacred Oath subclass "
                "(e.g., Sacred Weapon for Oath of Devotion, Peerless Athlete for Oath of Glory, "
                "Nature's Wrath for Oath of the Ancients, Vow of Enmity for Oath of Vengeance). "
                "You regain expended uses when you finish a Short or Long Rest."
            ),
            uses_left=cd_uses,
            cooldown="Short Rest",
        )]

    # ── Class interface ────────────────────────────────────────────────────────

    def apply_to_character(self, character: Character):
        character = super().apply_to_character(character)
        if not isinstance(character.special_abilities, list):
            character.special_abilities = []
        # Apply features for every level from 1 up to the paladin's starting level
        for lvl in range(1, self.level + 1):
            self._apply_level_features(character, lvl)
        self.completed_levelup_to = self.level
        return character

    def level_up(self, character: Character):
        super().level_up(character)  # increments self.level
        self._apply_level_features(character, self.level)
        # Refresh Lay on Hands to reflect updated pool size
        self._refresh_lay_on_hands(character)
        return character
