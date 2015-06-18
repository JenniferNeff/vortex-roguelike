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

import random, math

# def_article: "the " for most things. "" for uniques with proper names.
# indef_article: "a " or "an " for most things, "the" for uniques

# Not sure if all this "language stuff" will actually get used or not.

def smartcaps(sentence):
    start = sentence[0]
    remainder = sentence[1:]
    return start.capitalize() + remainder
    

def strike_notifs(sub, obj):

    if isinstance(sub, Player):
        sub_name = "you"
    else:
        sub_name = sub.name

    if isinstance(obj, Player):
        obj_name = "you"
    else:
        obj_name = obj.name

    reply = random.choice("{Adef}{Aname} scores a hit against {Bdef}{Bname}.",
                          "{Adef}{Aname} strikes {Bdef}{Bname}.").format(
                          Adef=sub.def_article, Aname=sub_name,
                          Bdef=obj.def_article, Bname=obj_name)

    return smartcaps(reply)

def report(sentence):
    shouts.append(smartcaps(sentence))

class Entity(object):

    def __init__(self, name="Unknown entity", symbol=None, color=7,
                 description="You don't know about this yet",
                 longdesc="You don't know about this yet, longer",
                 def_article="the ", indef_article="a ",
                 xp=0, level=None, alignment=None, opaque=False,
                 traversible=True, can_be_taken=False,
                 hp_max=None, mana_max=None, hp=None, mana=None, defense={},
                 attacks={}, speed=60, accuracy=100,
                 layer=2, floor=None, location=None, hidden=False,
                 inventory=[],
                 **kwargs
                 ):
        self.stats = {"level": level,
                      "XP": xp,
                      "max HP": hp_max,
                      "max mana": mana_max,
                      "speed": speed,
                      "accuracy": accuracy}

        self.adjusted_stats = {"level": level,
                               "XP": xp,
                               "max HP": hp_max,
                               "max mana": mana_max,
                               "speed": speed,
                               "accuracy": accuracy}
        self.name = name
        self.symbol = symbol
        self.color = color
        self.description = description
        self.longdesc = longdesc
        self.def_article = def_article
        self.indef_article = indef_article
        self.xp = xp # deprecating
        self.level = level # deprecating
        self.alignment = alignment
        self.opaque = opaque
        self.traversible = traversible
        self.can_be_taken = can_be_taken
        self.hp = hp
        self.mana = mana
        self.hp_max = hp_max # deprecating
        self.mana_max = mana_max # deprecating
        self.defense = defense
        self.attacks = attacks
        self.speed = speed # deprecating
        self.accuracy = accuracy # deprecating
        self.initiative = 0
        self.layer = layer
        self.floor = floor
        self.location = location
        self.hidden = hidden
        if self.floor and self.location:
            if 2 == self.layer:
                self.floor.layer2[self.location] = self
            elif 3 == self.layer:
                self.floor.layer3[self.location] = self
        self.inventory = inventory

    def __str__(self):
        return self.symbol # there might be some better use for this

    def calc_stats(self):
        self.hp = min(self.hp, self.adjusted_stats["max HP"])
        self.mana = min(self.mana, self.adjusted_stats["max mana"])

    def act(self): # all actions that "take one action" call this
        self.initiative += self.adjusted_stats["speed"]
        self.calc_stats()

    # "Is it possible to step onto the space I want to step on?"
    def traverse_test(self,y,x):
        dest = (self.location[0]+y, self.location[1]+x)
        if dest in self.floor.layer3.keys():
            if not self.floor.layer3[dest].traversible:
                return False
        if dest in self.floor.layer2.keys():
            if not self.floor.layer2[dest].traversible:
                return False
            elif isinstance(self.floor.layer2[dest], Passage):
                return self.floor.layer2[dest].walkon(self)
                # doors can only be walked on from HJKL
                # code assumes that doors are on layer 2
        if not self.floor.layer1[dest[0]][dest[1]].traversible:
            return False
        return True

    def find_open(self, layer):
        '''
        The entity searches for the nearest open space on which to drop an item
        when killed, or other similar purposes.
        '''
        if 2 == layer:
            search_layer = self.floor.layer2
        elif 3 == layer:
            search_layer = self.floor.layer3

        if self.location not in search_layer.keys():
            return self.location

        seek = 1
        while True:
            # http://en.wikipedia.org/wiki/Chebyshev_distance
            cells = [(y,x) for y in range(-seek, seek) \
                           for x in range(-seek, seek) \
                     if max(abs(y), abs(x)) == seek]
            if 0 == len(cells):
                # ran out of contiguous spaces
                return None
            random.shuffle(cells)
            seek += 1
            while 0 < len(cells):
                test = cells.pop()
                target = (self.location[0]+test[0], self.location[1]+test[1])
                if target in search_layer.keys():
                    # that space is already taken
                    continue
                elif not self.floor.layer1[target[0]][target[1]].traversible:
                    # the player can't stand there
                    continue
                elif target in self.floor.layer2.keys() \
                     and not self.floor.layer2[target].traversible:
                    # don't spawn a layer 3 object on an untraversible layer 2
                    continue
                else:
                    return target

    # "If I attempt to step on this object, what happens?"
    # walkon events should generally remove the player's "running" state
    def walkon(self, stomper):
        return None

    def attack(self, aim, implement=None):
        target = self.floor.layer3[aim]
        attack_roll = random.randint(0,self.adjusted_stats["accuracy"])
        defense_roll = random.randint(0,target.defense.setdefault('melee',0))
        if attack_roll > defense_roll:
            if isinstance(target, Player):
                shouts.append(random.choice(
                  ("{Adef}{Aname} scores a hit against you.",
                   "{Adef}{Aname} strikes you.")
                  ).format(Adef=self.def_article.capitalize(), Aname=self.name))
            else:
                shouts.append(random.choice(
                  ("{Adef}{Aname} scores a hit against {Bdef}{Bname}.",
                   "{Adef}{Aname} strikes {Bdef}{Bname}.")
                  ).format(Adef=self.def_article.capitalize(), Aname=self.name,
                           Bdef=target.def_article, Bname=target.name))
            
            if None == implement:
                damage_roll = random.randint(1, self.attacks['unarmed'])
            else:
                report("Attacked with weapon. Fix this!")
                damage_roll = 0
                # seriously, fix it
            target.hp -= damage_roll
            if 0 >= target.hp:
                target.perish(murderer=self)
        else:
            if isinstance(target, Player):
                report(random.choice(
                  ("{Adef}{Aname} misses you.",
                   "{Adef}{Aname} swings and misses you.")
                  ).format(Adef=self.def_article, Aname=self.name))
            else:
                report(random.choice(
                  ("{Adef}{Aname} misses {Bdef}{Bname}.",
                   "{Adef}{Aname} swings and misses {Bdef}{Bname}.")
                  ).format(Adef=self.def_article, Aname=self.name,
                           Bdef=target.def_article, Bname=target.name))

    def level_up(self):
        if isinstance(self.level, int) and isinstance(self.hp_max, int):
            self.stats['level'] += 1
            hp_ratio = float(self.hp) / float(self.adjusted_stats['max HP'])
            # This is the leveling HP curve.
            self.stats['max HP'] += random.randint(10,20)
            self.calc_stats()
            self.hp = int(math.floor(self.adjusted_stats['max HP'] * hp_ratio))
            if isinstance(self, Player):
                report("You have gained a level!")
            else:
                report("{0.def_article}{0.name} has gained a level!".format(self))

class Passage(Entity):

    def __init__(self, **kwargs):
        Entity.__init__(self, symbol="#", traversible=True)
        self.rookspots = [(self.location[0]+1, self.location[1]),
                          (self.location[0]-1, self.location[1]),
                          (self.location[0], self.location[1]+1),
                          (self.location[0], self.location[1]-1)]

    def walkon(self,stomper):
        if self.hidden:
            return False
        elif stomper.location in self.rookspots:
            return True
        else:
            return False

class Player(Entity):

    def __init__(self, **kwargs):
        Entity.__init__(self, symbol="@", level=1, traversible=False,
                        hp_max=50, mana_max=50, hp=50, mana=50, accuracy=80,
                        defense={'melee':80},
                        attacks={'unarmed':5,
                                 'melee':8}
                        )
        self.equipped = {'melee weapon': None,
                         'helm': None,
                         'armor': None,
                         'shoes': None,
                         'right ring': None,
                         'left ring': None,
                         'spellbook': None}

        self.hunger = 0
        self.thirst = 0
        self.fatigue = 0
        self.running = False

        self.skills = {}

    def calc_stats(self):
        for i in self.stats.keys():
            self.adjusted_stats[i] = self.stats[i]
        try:
            for i in self.equipped.values():
                for j in i.stats.keys():
                    self.adjusted_stats[j] += i.stats[j]
        except AttributeError:
            pass
        # Add other temporary inflictions; monsters will do this too.
        # If anything should have a max/min value, that goes here.
        self.hp = min(self.hp, self.adjusted_stats["max HP"])
        self.mana = min(self.mana, self.adjusted_stats["max mana"])

    def move(self, y, x):
        source = self.location
        dest = (self.location[0]+y, self.location[1]+x)
        trav = self.traverse_test(y,x)
        # Possibly handle an exception here, to allow for
        # "are you sure you want to walk on this?" questions.
        if dest in self.floor.layer3.keys():
            self.floor.layer3[dest].walkon(self)
        elif dest in self.floor.layer2.keys():
            self.floor.layer2[dest].walkon(self)
        else:
            self.floor.layer1[dest[0]][dest[1]].walkon(self)

        if trav:
            self.location = dest
            del self.floor.layer3[source]
            self.floor.layer3[dest] = self

            # Healing happens here so it won't in combat
            if self.hp < self.adjusted_stats["max HP"] \
               and random.randint(0,9) == 0:
                self.hp += 1

            self.act()
        else:
            self.running = False #doesn't stop player from attacking

    def attack(self, aim, implement=None):
        if None == implement:
            implement = self.equipped["melee weapon"]

        target = self.floor.layer3[aim]
        attack_roll = random.randint(0,self.adjusted_stats['accuracy'])
        defense_roll = random.randint(0,target.defense.setdefault('melee',0))
        if attack_roll > defense_roll:
            report(random.choice(
              ("You score a hit against {Bdef}{Bname}.",
               "You strike {Bdef}{Bname}.")
              ).format(Bdef=target.def_article, Bname=target.name))
            if None == implement:
                damage_roll = random.randint(1, self.attacks['unarmed'])
            elif self.equipped['melee weapon'] == implement:
                damage_roll = random.randint(1, self.attacks['melee'])
                # add modifier for weapon
            else:
                report("This attack type not defined. Fix this!")
                damage_roll = 0
                # seriously, fix it
            target.hp -= damage_roll
            if 0 >= target.hp:
                target.perish(murderer=self)
        else:
            report(random.choice(
              ("You miss {Bdef}{Bname}.",
               "You swing and miss {Bdef}{Bname}.")
              ).format(Bdef=target.def_article, Bname=target.name))
        self.act()

    def take(self):
        if self.location not in self.floor.layer2.keys():
            report("There's nothing here to take.")
        else:
            report("You pick up a %s." % \
              self.floor.layer2[self.location].name)
            self.floor.layer2[self.location].when_taken()
            self.inventory.append(self.floor.layer2.pop(self.location))
            self.act()

    def drop(self, item):
        if self.location in self.floor.layer2.keys():
            report("There's already something on the floor.")
        else:
            report("You drop the %s." % item.name)
            self.floor.layer2[self.location] = item
            self.inventory.remove(item)
            item.when_dropped()
            self.act()

    def rest(self):
        if self.hp < self.hp_max and random.randint(0,9) == 0:
            self.hp += 1
        self.act()

    def wield_or_wear(self, item):
        if item.when_equipped(self):
            self.equipped[item.equip_slot] = item
            self.act()

    def remove(self, item):
        if item.when_removed(self):
            self.equipped[item.equip_slot] = None
            self.act()
            report(str(self.equipped[item.equip_slot])) # testing

    def perish(self, murderer=None):
        report("Player has died! Resetting HP for ease in testing!")
        self.hp = 50

sampledescription = """
This is a long description of an item. It would be simple enough to pass in
arguments with further details about this item, such as enchantments, etc.
It has infinite charges, so try Invoking it.
"""

class Item(Entity):

    def __init__(self, equip_slot=None, cursed=False, **kwargs):
        Entity.__init__(self, layer=2, # placeholder
          traversible=True, can_be_taken=True,
          description="Short description of a nondescript item.",
          longdesc=sampledescription,
          **kwargs)
          # how to pass in more arguments properly??
        self.equip_slot = equip_slot
        self.cursed = cursed
        try:
            if -1 == self.equip_slot.find("weapon"):
                self.equip_action = "wear"
            else:
                self.equip_action = "wield"
        except AttributeError:
            self.equip_action = "wear"

    def walkon(self, stomper):
        if isinstance(stomper, Player):
            report("You are standing on {obj.indef_article}{obj.name}.".format(obj=self))
            stomper.running = False

    def use(self, user):
        user.level_up()

    # The when_*() functions return False when that action fails, and True
    # when it succeeds. They should also contain all related reports.

    def when_taken(self):
        pass

    def when_dropped(self):
        pass

    def when_equipped(self, user):
        if None == self.equip_slot:
            report("You can't {obj.equip_action} that.".format(obj=self))
            return False
        elif user.equipped[self.equip_slot] != None:
            report("You're already {obj.equip_action}ing a {thing}.".format(obj=self, thing=user.equipped[self.equip_slot].name))
            return False
        else:
            report("You {obj.equip_action} {obj.def_article}{obj.name}.".format(obj=self))
            if self.cursed:
                report("You feel a growing sensation of dread.")
            return True

    def when_removed(self, user):
        if self not in user.equipped.values():
            report("You're not {obj.equip_action}ing {obj.def_article}{obj.name}.".format(obj=self))
            return False
        elif self.cursed:
            report("You can't remove {obj.def_article}{obj.name}. It's cursed.".format(obj=self))
            return False
        else:
            report("You return {obj.def_article}{obj.name} to your inventory.".format(obj=self))
            return True
            

#class Weapon(Item):
#
#    def __init__(self, category=None, **kwargs):
#        Item.__init__(self, **kwargs)
#        self.category = category # sword, hammer, dagger, etc.
#        self.accuracy = 0
#        self.defense = {}
#        self.attack = 0

class Food(Item):
    pass

class Spellbook(Item):
    pass

class Monster(Entity):

    def __init__(self, **kwargs):
        Entity.__init__(self, layer=3, #symbol="Z", #placeholder
          traversible=False, #name="Demo Zombie",
          can_be_taken=False,
          #hp=20, attacks={'unarmed':3},
          #speed=80, accuracy=50,
          #defense={'melee':30},
          #description="Your basic shambling zombie. \"Brains!\"",
          #inventory=[],
          **kwargs)

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

#    def attack(self, aim): # aim is the location to attack
#        shouts.append("The %s performs a useless placeholder attack." % \
#                      self.name)

    def check_adjacency(self, victim):
        cells = [(y,x) for y in (-1,0,1) for x in (-1,0,1) \
                 if not (y == 0 and x == 0)]
        rookcells = [(y,x) for y in (-1,0,1) for x in (-1,0,1) \
                     if not (y == 0 and x == 0) and (y == 0 or x == 0)]

        for i in cells:
            gohere = (self.location[0]+i[0], self.location[1]+i[1])
            if gohere in self.floor.layer2 and \
               (isinstance(self.floor.layer1[gohere[0]][gohere[1]], Passage) and \
               (i in rookcells and self.floor.layer3[gohere] == victim)):
                return gohere
            elif gohere in self.floor.layer3 and \
               self.floor.layer3[gohere] == victim:
                return gohere
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
            adventurer.running = False
            # prevents PC from autoattacking at the end of a run if the monster
            # gets in the first swing.
        elif adventurer.floor == self.floor:
            self.pursue(adventurer.location[0], adventurer.location[1])
        self.initiative += self.adjusted_stats["speed"]

    def walkon(self, stomper):
        if isinstance(stomper, Player):
            try:
                stomper.attack(self.location,
                               implement=stomper.equipped['melee weapon'])
            except KeyError:
                stomper.attack(self.location)
            except AttributeError:
                stomper.attack(self.location)
                # May need to be more clever about this.
                # lack of self.equipped vs. self.attack()

    # Idea: make a monster that moves like a chess knight.
    # ...or is otherwise constrained rook/bishop/pawn style

    def perish(self, murderer=None):
        self.drop_loot()
        del self.floor.layer3[self.location]
        self.location = None
        shouts.append(random.choice(
          ("{Adef}{Aname} dies.",
           "{Adef}{Aname} collapses, lifeless.")
          ).format(Adef=self.def_article.capitalize(), Aname=self.name))
        # Here, add the ability for slain monsters to drop loot.
        murderer.xp += self.xp # Make this more complex later.

    def drop_loot(self):
        for item in self.inventory:
            dropzone = self.find_open(2)
            self.floor.layer2[dropzone] = item
            self.inventory.remove(item)
        
def make_floor():
    return Entity(symbol=".", description="Bare floor.")

def make_passage():
    return Entity(symbol="#", description="A dungeon passage.")

def make_wall(side="-"):
    return Entity(symbol=side, description="A wall.", opaque=True,
                  traversible=False)

def make_void():
    return Entity(symbol=" ", description="There's nothing there.",
                  traversible=False)

shouts = []
