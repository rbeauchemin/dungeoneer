from random import choice


def roll_dice(num_dice=1, dice_sides=6):
    rolls = sum(choice(range(1, dice_sides + 1)) for _ in range(num_dice))
    return rolls


def roll_dice_discard_lowest(dice_sides, num_dice=4):
    rolls = [roll_dice(dice_sides=dice_sides) for _ in range(num_dice)]
    print(f"Rolls: {rolls}")
    print(f"Discarding lowest roll: {min(rolls)}")
    rolls.remove(min(rolls))
    return sum(rolls)