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
        self.layer = layer
        self.floor = floor
        self.location = location
        if self.floor and self.location:
            if 2 == self.layer:
                self.floor.layer2[self.location] = self
            elif 3 == self.layer:
                self.floor.layer3[self.location] = self

    def __str__(self):
        return self.symbol # there might be some better use for this

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
    def walkon(self):
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

    def act(self): # all actions that "take one action" call this
        pass

    def move(self, y, x):
        source = self.location
        dest = (self.location[0]+y, self.location[1]+x)
        # Possibly handle an exception here, to allow for
        # "are you sure you want to walk on this?" questions.
        if dest in self.floor.layer3.keys():
            self.floor.layer3[dest].walkon()
        if dest in self.floor.layer2.keys():
            self.floor.layer2[dest].walkon()
        self.floor.layer1[dest[0]][dest[1]].walkon()

        if self.traverse_test(y,x):
            self.location = dest
            del self.floor.layer3[source]
            self.floor.layer3[dest] = self

class Item(Entity):

    def __init__(self, **kwargs):
        Entity.__init__(self, layer=2, symbol="$", # placeholder
          traversible=True, name="Nondescript Item",
          can_be_taken=True,
          description="This is an item with no defining qualities.", **kwargs)
          # how to pass in more arguments properly??

    def walkon(self):
        shouts.append("You are standing on a %s" % self.name)
        
def make_floor():
    return Entity(symbol=".", description="Bare floor.")

def make_wall(side="+"):
    return Entity(symbol=side, description="A wall.", opaque=True,
                  traversible=False)

def make_void():
    return Entity(symbol=" ", description="There's nothing there.",
                  traversible=False)

shouts = []
