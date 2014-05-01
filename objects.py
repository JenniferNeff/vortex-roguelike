#!/usr/bin/python

# Available colors:
# 0: black
# 1: red
# 2: green
# 3: yellow
# 4: blue
# 5: magenta
# 6: cyan
# 7: white

import random

class Entity(object):

    def __init__(self, name="Unknown entity", symbol=None, color=7,
                 description="You don't know about this yet",
                 xp=0, level=None, alignment=None, opaque=False,
                 traversible=True, can_be_taken=False,
                 hp=None, mana=None, defense={}, attacks={}, speed=60,
                 layer=2, floor=None, location=None,
                 ):
        self.name = name
        self.symbol = symbol
        self.color = color
        self.description = description
        self.xp = xp
        self.level = level
        self.alignment = alignment
        self.opaque = opaque
        self.traversible = traversible
        self.can_be_taken = can_be_taken
        self.hp = hp
        self.mana = mana
        self.defense = defense
        self.attacks = attacks
        self.speed = speed
        self.initiative = 0
        self.layer = layer
        self.floor = floor
        self.location = location
        if self.floor and self.location:
            if 2 == self.layer:
                self.floor.layer2[self.location] = self
            elif 3 == self.layer:
                self.floor.layer3[self.location] = self
        self.inventory = []

    def __str__(self):
        return self.symbol # there might be some better use for this

    def act(self): # all actions that "take one action" call this
        self.initiative += self.speed

    # "Is it possible to step onto the space I want to step on?"
    def traverse_test(self,y,x):
        dest = (self.location[0]+y, self.location[1]+x)
        if dest in self.floor.layer3.keys():
            if not self.floor.layer3[dest].traversible:
                return False
        if dest in self.floor.layer2.keys():
            if not self.floor.layer2[dest].traversible:
                return False
        if not self.floor.layer1[dest[0]][dest[1]].traversible:
            return False
        return True

    # "If I attempt to step on this object, what happens?"
    # walkon events should generally remove the player's "running" state
    def walkon(self, stomper):
        return None

class Player(Entity):

    def __init__(self,
                 **kwargs):
        Entity.__init__(self, symbol="@", level=1, traversible=False,
                        hp=50, mana=50,
                        )
        self.weapon = None
        self.helm = None
        self.armor = None
        self.shoes = None
        self.ring_right = None
        self.ring_left = None
        self.spellbook = None

        self.hunger = 0
        self.thirst = 0
        self.fatigue = 0
        self.running = False

        self.skills = {}

    def move(self, y, x):
        source = self.location
        dest = (self.location[0]+y, self.location[1]+x)
        # Possibly handle an exception here, to allow for
        # "are you sure you want to walk on this?" questions.
        if dest in self.floor.layer3.keys():
            self.floor.layer3[dest].walkon(self)
        if dest in self.floor.layer2.keys():
            self.floor.layer2[dest].walkon(self)
        self.floor.layer1[dest[0]][dest[1]].walkon(self)

        if self.traverse_test(y,x):
            self.location = dest
            del self.floor.layer3[source]
            self.floor.layer3[dest] = self
            self.act()

    def attack(self, aim):
        shouts.append("You hit the %s with an ineffective placeholder attack." % \
                      self.floor.layer3[aim].name)
        self.act()

    def take(self):
        if self.location not in self.floor.layer2.keys():
            shouts.append("There's nothing here to take.")
        else:
            shouts.append("You pick up a %s." % \
              self.floor.layer2[self.location].name)
            self.inventory.append(self.floor.layer2.pop(self.location))
            self.act()

class Item(Entity):

    def __init__(self, **kwargs):
        Entity.__init__(self, layer=2, symbol="$", # placeholder
          traversible=True, name="Nondescript Item",
          can_be_taken=True,
          description="This is an item with no defining qualities.", **kwargs)
          # how to pass in more arguments properly??

    def walkon(self, stomper):
        if isinstance(stomper, Player):
            shouts.append("You are standing on a %s" % self.name)

class Weapon(Item):
    pass

class Food(Item):
    pass

class Spellbook(Item):
    pass

class Monster(Entity):

    def __init__(self, **kwargs):
        Entity.__init__(self, layer=3, symbol="Z", #placeholder
          traversible=False, name="Basic Zombie",
          can_be_taken=False,
          speed=80,
          description="Your basic shambling zombie. \"Brains!\"", **kwargs)

    def move(self, y, x):
        source = self.location
        dest = (self.location[0]+y, self.location[1]+x)
        # These lines still here to allow monsters to set off traps.
        # To Do: add a filter so objects know what is walking on them.
        if dest in self.floor.layer3.keys():
            self.floor.layer3[dest].walkon(self)
        if dest in self.floor.layer2.keys():
            self.floor.layer2[dest].walkon(self)
        self.floor.layer1[dest[0]][dest[1]].walkon(self)

        if self.traverse_test(y,x):
            self.location = dest
            del self.floor.layer3[source]
            self.floor.layer3[dest] = self

    def pursue(self, y, x, flee=1): # y, x are the coordinates to chase
        '''
        The creature chases after the given coordinates (y,x)--usually the
        player's location. Pass flee=-1 to this method to make the monster
        run away instead.
        '''
        moveY = 0
        moveX = 0
        if y < self.location[0]:
            moveY = -1 * flee
        elif y > self.location[0]:
            moveY = 1 * flee
        if x < self.location[1]:
            moveX = -1 * flee
        elif x > self.location[1]:
            moveX = 1 * flee

        edgeflee = random.choice((1,-1))

        if self.traverse_test(moveY, moveX):
            self.move(moveY, moveX)
        # If the diagonal route is blocked, move rookwise.
        elif self.traverse_test(0, moveX):
            self.move(0, moveX)
        elif self.traverse_test(moveY, 0):
            self.move(moveY, 0)
        # If fleeing and against a wall, edge sideways.
        elif -1 == flee and self.traverse_test(0, moveX+edgeflee):
            self.move(0, moveX+edgeflee)
        elif -1 == flee and self.traverse_test(0, moveX-edgeflee):
            self.move(0, moveX-edgeflee)
        elif -1 == flee and self.traverse_test(moveY+edgeflee,0):
            self.move(moveY+edgeflee, 0)
        elif -1 == flee and self.traverse_test(moveY-edgeflee,0):
            self.move(moveY-edgeflee, 0)

    def wander(self): # use for stupid, confused, and blind monsters
        moveY = random.choice((-1,0,1))
        moveX = random.choice((-1,0,1))

        if moveY != 0 or moveX != 0:
            self.move(moveY, moveX)

    def attack(self, aim): # aim is the location to attack
        shouts.append("The %s performs a useless placeholder attack." % \
                      self.name)

    def check_adjacency(self, victim):
        cells = [(y,x) for y in (-1,0,1) for x in (-1,0,1) \
                 if not (y == 0 and x == 0)]

        for i in cells:
            gohere = (self.location[0]+i[0], self.location[1]+i[1])
            if gohere in self.floor.layer3 and \
               self.floor.layer3[gohere] == victim:
                return i
        return None

    def act(self, adventurer):
        '''
        This is where the creature decides what to do on its turn:
        a long list of elifs, each of which calls a different other method.
        The explicit use of self.attack() guarantees that monsters stand still
        and attack when diagonally adjacent to a target rather than trying to
        edge over to a squarely adjacent position.
        '''
        strike = self.check_adjacency(adventurer)
        if strike != None:
            self.attack(strike)
        elif adventurer.floor == self.floor:
            self.pursue(adventurer.location[0], adventurer.location[1])
        self.initiative += self.speed

    def walkon(self, stomper):
        if isinstance(stomper, Player):
            stomper.attack(self.location)

    # Idea: make a monster that moves like a chess knight.
    # ...or is otherwise constrained rook/bishop/pawn style
        
def make_floor():
    return Entity(symbol=".", description="Bare floor.")

def make_wall(side="+"):
    return Entity(symbol=side, description="A wall.", opaque=True,
                  traversible=False)

def make_void():
    return Entity(symbol=" ", description="There's nothing there.",
                  traversible=False)

shouts = []
