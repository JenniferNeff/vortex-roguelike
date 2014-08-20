#!/usr/bin/python

import objects

def zombie():
    return objects.Monster(
     name="Zombie",
     symbol="Z",
     description="Your basic shambling zombie. \"Brains!\"",
     hp=20, hp_max=20,
     mana=0, mana_max=0,
     speed=80,
     accuracy=50,
     attacks={'unarmed':3}
     defense={'melee':30},
     inventory=[])
