from random import choice


def roll_dice(num_dice=1, dice_sides=6):
    rolls = sum(choice(range(1, dice_sides + 1)) for _ in range(num_dice))
    return rolls


def handle_roll_criticals(roll, total, beat, critical_threshold=20, failure_threshold=1, halfling_luck=False):
    if roll >= critical_threshold:
        print("Critical success!")
        return True, total
    elif roll <= failure_threshold and not halfling_luck:
        print("Critical failure!")
        return False, total
    elif halfling_luck and roll <= failure_threshold:
        new_roll = roll_dice(1, 20)
        total = total - roll + new_roll
        print("Lucky halfling! Rerolled 1 to {total}.")
    success = total >= beat
    print(f"Rolled total of {total} against {beat}.")
    return success, total


def roll_dice_discard_lowest(dice_sides, num_dice=4):
    rolls = [roll_dice(dice_sides=dice_sides) for _ in range(num_dice)]
    print(f"Rolls: {rolls}")
    print(f"Discarding lowest roll: {min(rolls)}")
    rolls.remove(min(rolls))
    return sum(rolls)
