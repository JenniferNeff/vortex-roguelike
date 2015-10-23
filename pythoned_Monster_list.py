#!/usr/bin/python
import random
import objects
all_the_things = {
"zombie1": objects.Monster(key="zombie1",name="Zombie",symbol="Z",description="Your basic shambling zombie. \"Brains!\"",longdesc="This decaying corpse shuffles along slowly. Despite its constant hunger for brains, it shows a distinct lack of enthusiasm.",defense={'melee':30},attacks={'unarmed':objects.roll(1,4)},speed=80,inventory=[],scared_at=0,brave_at=90),
"snake1": objects.Monster(key="snake1",name="Snake",symbol="s",description="A snake. Not poisonous, yet.",longdesc="Why did it have to be snakes? Luckily, this one is a little green one that looks pretty harmless.",defense={'melee':30},attacks={'unarmed':objects.roll(1,4)},speed=60,accuracy=80,inventory=[],scared_at=50,brave_at=90)
}
