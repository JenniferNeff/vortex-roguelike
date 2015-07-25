#!/usr/bin/python

import objects

def Zombie(flr=None, loc=None):
    return objects.Monster(
     name="Zombie",
     symbol="Z",
     description="Your basic shambling zombie. \"Brains!\"",
     hp=20, hp_max=20,
     mana=0, mana_max=0,
     speed=80,
     accuracy=50,
     attacks={'unarmed':3},
     defense={'melee':30},
     inventory=[],
     scared_at=0, # flees at this % of HP
     brave_at=90,
     floor=flr, location=loc
     )

def Snake(flr=None, loc=None):
    return objects.Monster(
     name="Snake",
     symbol="s",
     description="A snake. Not poisonous, yet.",
     hp=10, hp_max=10,
     mana=0, mana_max=0,
     speed=60,
     accuracy=80,
     attacks={'unarmed':3},
     defense={'melee':30},
     inventory=[],
     scared_at=50,
     brave_at=90,
     floor=flr, location=loc
     )
