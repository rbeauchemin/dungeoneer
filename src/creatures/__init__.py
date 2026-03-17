from src.creatures.character import Character
from src.creatures.monsters import (
    Monster,
    NPC,
    # CR 0
    Commoner,
    Rat,
    Bat,
    Cat,
    # CR 1/8
    Bandit,
    Guard,
    Kobold,
    PoisonousSnake,
    Stirge,
    # CR 1/4
    Goblin,
    Skeleton,
    Zombie,
    Wolf,
    # CR 1/2
    Hobgoblin,
    Orc,
    Scout,
    # CR 1
    Bugbear,
    DireWolf,
    Ghoul,
    GiantSpider,
    Harpy,
    # CR 2
    Ogre,
    SeaHag,
    # CR 3
    Manticore,
    Mummy,
    Wight,
    # CR 4
    Banshee,
    Ettin,
    # CR 5
    HillGiant,
    Troll,
    VampireSpawn,
    # CR 8
    Assassin,
    # CR 9
    CloudGiant,
    # CR 13
    Vampire,
    # CR 17
    AdultRedDragon,
    # CR 21
    Lich,
    # CR 24
    AncientRedDragon,
)
from src.creatures.npc import NPC  # noqa: F811 — re-export for convenience
