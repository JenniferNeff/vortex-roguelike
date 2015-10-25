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

import random, math, copy
import new_levelgen

# def_article: "the " for most things. "" for uniques with proper names.
# indef_article: "a " or "an " for most things, "the" for uniques

# Not sure if all this "language stuff" will actually get used or not.

def smartcaps(sentence):
    """Capitalize the first letter of a string, leaving the rest unchanged."""
    start = sentence[0]
    remainder = sentence[1:]
    return start.capitalize() + remainder
    

def strike_notifs(sub, obj):
    """Takes the subject and object of a sentence in which the subject hits
    the object. Returns an appropriate sentence."""

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
    """Add an object-generated message to the message queue"""
    shouts.append(smartcaps(sentence))

class Entity(object):
    """Class handling just about every "thing" in the game."""
    # Goal: make long descriptions Dialogue screens.
    # will probably have to move Dialogue into this file.

    def __init__(self, name="Unknown entity", symbol=None, color=7,
                 description="You don't know about this yet",
                 longdesc="You don't know about this yet, longer",
                 def_article="the ", indef_article="a ",
                 xp=0, level=None, alignment=None, opaque=False,
                 traversable=True, can_be_taken=False,
                 hp_max=None, mana_max=None, hp=None, mana=None, defense={},
                 attacks={}, speed=60, accuracy=100,
                 layer=2, floor=None, location=None, hidden=False,
                 inventory=[], sess=None, gender=None,
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
        self.traversable = traversable
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
        self.session = sess

    def __str__(self):
        return self.symbol # there might be some better use for this

    def calc_stats(self):
        """Caps the entity's HP and mana stats at the maximum values."""
        self.hp = min(self.hp, self.adjusted_stats["max HP"])
        self.mana = min(self.mana, self.adjusted_stats["max mana"])

    def act(self):
        """All actions that "take one action" call this.
        Schedules the entity's next action, and performs any other
        end-of-turn cleanup tasks.
        """
        self.initiative += self.adjusted_stats["speed"]
        self.calc_stats()

    def traverse_test(self,y,x):
        """Is it possible to step onto the space I want to step on?"""
        # wrangling this and the floors counterpart, at the moment
        dest = (self.location[0]+y, self.location[1]+x)
        if y == 0 or x == 0:
            moving_rookwise = True
        else:
            moving_rookwise = False

        result = self.floor.traverse_test(dest, moving_rookwise)
        #report(str(result))
        return result

    def find_open(self, layer):
        """
        The entity searches for the nearest open space on which to drop an item
        when killed, or other similar purposes.
        """
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
                elif not self.floor.layer1[target[0]][target[1]].traversable:
                    # the player can't stand there
                    continue
                elif target in self.floor.layer2.keys() \
                     and not self.floor.layer2[target].traversable:
                    # don't spawn a layer 3 object on an untraversable layer 2
                    continue
                else:
                    return target

    def walkon(self, stomper):
        """Specifies what happens if something tries to walk onto this entity.
        Walkon events should generally remove the player's "running" state.
        Takes the thing stepping on this entity as an argument.
        """
        return None

    def attack(self, aim, implement=None):
        """The basic attack routine.
        Arguments:
        aim -- the entity being attacked
        implement -- an optional weapon being used (default: None)
        """
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
        """Allows this entity to gain a level."""
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

class Door(Entity):

    def __init__(self, **kwargs):
        """Initialize a door with its special traits. Doors are 'rookwise'
        traversable, which means they cannot be traversed diagonally.
        """
        Entity.__init__(self, name='door', traversable='rookwise', symbol="+",
                        **kwargs)

class Player(Entity):

    def __init__(self, **kwargs):
        """Initialize a player with its special traits."""
        Entity.__init__(self, symbol="@", level=1, traversable=False,
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

        self.hungry = "      "
        self.thirsty = False
        self.fatigued = False
        self.hunger_timer = 300

        self.running = False

        self.skills = {}

    def act(self):
        """All actions that "take one action" call this."""
        #if random.randint(1,100) < 30:
        if True: # for testing
            self.hunger += 1

        self.initiative += self.adjusted_stats["speed"]
        self.calc_stats()

    def calc_stats(self):
        for i in self.stats.keys():
            self.adjusted_stats[i] = self.stats[i]
        try:
            for i in self.equipped.values():
                for j in i.stats.keys():
                    self.adjusted_stats[j] += i.stats[j]
        except AttributeError:
            pass

        if self.hunger >= 2400:
            self.hungry = "Weak  "
        elif self.hunger >= 1600:
            self.hungry = "Hungry"
        elif self.hunger >= 800:
            self.hungry = "Pekish"
        else:
            self.hungry = "      "

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
        elif not self.floor.layer2[self.location].can_be_taken:
            report("That's not something you can take.")
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
            #report("Your initiative = %d" % self.initiative)
            self.act()
            #report("Your initiative = %d" % self.initiative)

    def remove(self, item):
        if item.when_removed(self):
            self.equipped[item.equip_slot] = None
            self.act()
            report(str(self.equipped[item.equip_slot])) # testing

    def perish(self, murderer=None):
        report("Player has died! Resetting HP for ease in testing!")
        self.hp = 50

    def descend(self):
        """Move the player down a flight of stairs."""
        try:
            the_stairs = self.floor.layer2[self.location]
            if isinstance(the_stairs, StairsDown):
                report("You walk downstairs.")
                return the_stairs
            else:
                raise KeyError('FLAGRANT ERROR: Standing on something, but not stairs.')
        except KeyError:
            report("You're not standing at a descending stairway.")
            return None

    def ascend(self):
        """Move the player up a flight of stairs."""
        # Could maybe combine these into one
        try:
            the_stairs = self.floor.layer2[self.location]
            if isinstance(the_stairs, StairsUp):
                report("You walk upstairs.")
                return the_stairs
            else:
                raise KeyError('FLAGRANT ERROR: Standing on something, but not stairs.')
        except KeyError:
            report("You're not standing at an ascending stairway.")
            return None

sampledescription = """
This is a long description of an item. It would be simple enough to pass in
arguments with further details about this item, such as enchantments, etc.
It has infinite charges, so try Invoking it.
"""

class Item(Entity):

    def __init__(self, equip_slot=None, cursed=False, **kwargs):
        """Initialize an Item, which encompasses any Entity that can be
        picked up, dropped, and placed in inventories.
        """
        Entity.__init__(self, layer=2, # placeholder
          traversable=True, can_be_taken=True,
          **kwargs)
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
        """Items react to being stepped on by reporting what they are."""
        if isinstance(stomper, Player):
            report("You are standing on {obj.indef_article}{obj.name}.".format(obj=self))
            stomper.running = False

    def use(self, user):
        """Many items can be Invoked to perform some effect."""
        user.level_up()

    # The when_*() functions return False when that action fails, and True
    # when it succeeds. They should also contain all related reports.

    def when_taken(self):
        """An item might do something special when picked up."""
        pass

    def when_dropped(self):
        """An item might do something special when dropped."""
        pass

    def when_equipped(self, user):
        """An item might do something special when equipped.
        The act of wearing the item should trigger the stat update,
        because it takes a turn. So all this needs to do, usually, is 
        report success or failure.
        """
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
        """An item might do something special when equipped.
        The act of wearing the item should trigger the stat update,
        because it takes a turn. So all this needs to do, usually, is 
        report success or failure.
        """
        if self not in user.equipped.values():
            report("You're not {obj.equip_action}ing {obj.def_article}{obj.name}.".format(obj=self))
            return False
        elif self.cursed:
            report("You can't remove {obj.def_article}{obj.name}. It's cursed.".format(obj=self))
            return False
        else:
            report("You return {obj.def_article}{obj.name} to your inventory.".format(obj=self))
            return True

    def self_destruct(self, user):
        user.inventory.remove(self)
            

#class Weapon(Item):
#
#    def __init__(self, category=None, **kwargs):
#        Item.__init__(self, **kwargs)
#        self.category = category # sword, hammer, dagger, etc.
#        self.accuracy = 0
#        self.defense = {}
#        self.attack = 0

class Food(Item):

    def __init__(self,
                 calories=300, caffeine=0, healthy=True, **kwargs):
        Item.__init__(self, #layer=2, # placeholder
          symbol=":", #equip_slot=None, cursed=False,
          **kwargs)
        """Initialize a food item. Game is tuned so that real-world
        calorie counts can be used as a reference.
        calories -- determines how much hunger the food satisfies.
        caffeine -- determines how much mana the food restores.
        healthy -- if true, provides some other benefit
        """

        self.calories = calories
        self.caffeine = caffeine
        self.healthy = healthy

    def use(self, user):
        if user.hunger < self.calories:
            report("You're not hungry enough for {obj.indef_article}{obj.name}.".format(obj=self))
        else:
            report("You eat {obj.indef_article}{obj.name}. Yum!".format(obj=self))
            user.hunger -= self.calories
            user.hunger_timer = 300
            self.self_destruct(user)
            user.act()

class Spellbook(Item):
    """A system for learning skills. Not implemented yet."""
    pass

class StairsDown(Entity):

    def __init__(self, destination=1, **kwargs):
        """Initialize a downward stairway."""
        Entity.__init__(self, layer=2, traversable=True, can_be_taken=False,
                        symbol=">", name="descending stairway", **kwargs)
        self.destination = destination

    def when_taken(self):
        return False

class StairsUp(Entity):

    def __init__(self, destination=1, **kwargs):
        """Initialize an upward stairway."""
        Entity.__init__(self, layer=2, traversable=True, can_be_taken=False,
                        symbol="<", name="ascending stairway",
                        indef_article="an ", **kwargs)
        self.destination = destination

    def when_taken(self):
        return False

class Monster(Entity):

    def __init__(self, scared_at=0, brave_at=90, **kwargs):
        """Initialize a monster.
        scared_at -- at what HP% will it become afraid?
        brave_at -- at what HP% will it lose scared status?
        scared -- is the monster scared (usually means it flees)?
        """
        Entity.__init__(self, layer=3,
          traversable=False,
          can_be_taken=False,
          **kwargs)
        self.scared_at = scared_at
        self.brave_at = brave_at
        self.scared = False

    def move(self, y, x):
        """Movement, for monsters."""
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
        """The creature chases after the given coordinates (y,x)--usually
        the player's location. Pass flee=-1 to this method to make the
        monster run away from that point instead.
        """
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

    def wander(self):
        """A movement behavior for stupid, confused, and blind monsters."""
        moveY = random.choice((-1,0,1))
        moveX = random.choice((-1,0,1))

        if moveY != 0 or moveX != 0:
            self.move(moveY, moveX)

    def check_adjacency(self, victim):
        """The monster checks whether it is close to something it wants
        to attack.
        """
        cells = [(y,x) for y in (-1,0,1) for x in (-1,0,1) \
                 if not (y == 0 and x == 0)]
        rookcells = [(y,x) for y in (-1,0,1) for x in (-1,0,1) \
                     if not (y == 0 and x == 0) and (y == 0 or x == 0)]

        for i in cells:
            gohere = (self.location[0]+i[0], self.location[1]+i[1])
            if gohere in self.floor.layer2 and \
               (isinstance(self.floor.layer1[gohere[0]][gohere[1]], Door) and \
               (i in rookcells and self.floor.layer3[gohere] == victim)):
                return gohere
            elif gohere in self.floor.layer3 and \
               self.floor.layer3[gohere] == victim:
                return gohere
        return None

    def AI_melee_brute(self, adventurer):
        """AI for a monster that uses only melee strikes, and flees at
        low health. The explicit use of self.attack() guarantees that
        monsters stand still and attack when diagonally adjacent to a
        target rather than trying to edge over to a squarely adjacent
        position.
        """
        # do nothing when the player is on a different floor
        if adventurer.floor != self.floor:
            return

        if 100 * self.hp / self.hp_max < self.scared_at:
            self.scared = True
        elif 100 * self.hp / self.hp_max > self.brave_at:
            self.scared = False

        if self.scared:
            self.pursue(adventurer.location[0], adventurer.location[1], flee=-1)
        else:
            strike = self.check_adjacency(adventurer)
            if strike != None:
                self.attack(strike)
                adventurer.running = False
                # prevents PC from autoattacking at the end of a run if the
                # monster gets in the first swing.
            elif adventurer.floor == self.floor:
                self.pursue(adventurer.location[0], adventurer.location[1])

    def act(self, adventurer):
        """This is where the creature decides what to do on its turn:
        a long list of elifs, each of which calls a different other method.
        """
        self.AI_melee_brute(adventurer)
        self.initiative += self.adjusted_stats["speed"]
        #report("DEBUG: %s taking a turn." % self.name)

    def walkon(self, stomper):
        """When the player tries to "walk onto" the monster, they attack
        the monster.
        """
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
        """When the monster dies, it deletes itself from the world,
        reports its death, and grants its killer XP.
        """
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
        """If a monster drops loot when killed, use this."""
        for item in self.inventory:
            dropzone = self.find_open(2)
            self.floor.layer2[dropzone] = item
            self.inventory.remove(item)

class Floor(object):

    def __init__(self, name="Unknown Location", depth=0, sess=None,
                 screen_x=80, screen_y=22, items=[], foods=[], monsters=[]):
        """Initialize a floor, or level, of the dungeon.
        Variables:
        name -- the name given to this level
        depth -- the floor's depth in the dungeon
        sess -- the game session to which the floor belongs

        Other traits:
        self.layer1 -- contains the static floor and walls
        self.layer2 -- contains objects
        self.layer3 -- contains the player and moving monsters
         (thus the player can stand over an object that is on the floor)

        If a file "{name}_{depth}.map" exists in the directory, where
        the name and depth match this floor, then it will be used to
        initialize this floor. If not, the level generator will be
        used. .map files are just text, so you can "draw" handcrafted
        levels in any text editor.
        """
        self.name = name
        self.depth = depth
        self.filename = "{n}_{dep}.map".format(n=self.name, dep=depth)

        self.layer1 = []
        self.layer2 = {} # (i,j) : object
        self.layer3 = {}

        self.maphoriz = 0
        self.mapvert = 2

        self.x_offset = 0
        self.y_offset = 0

        self.session = sess
        self.scr_x = screen_x
        self.scr_y = screen_y

        self.items = items
        self.foods = foods
        self.monsters = monsters

        self.load_map()


    def load_map(self):
        """Build layer 1 of a map from a text file. A border of void
        is added to each side; this prevents errors when fleeing
        monsters reach the edge.
        """
        self.empty_tiles = []
        self.doors = []
        try: # handcrafted map
            getmap = open(self.filename, 'r')
        except IOError: # level generator
            make_map = new_levelgen.Map(depth=self.depth)
            getmap = make_map.export_as_array()
        for line in getmap:
            newline = []
            self.mapvert += 1
            for char in range(len(line)+1):
                if self.maphoriz < char:
                    self.maphoriz = char
                try:
                    if "+" == line[char]:
                        newline.append(make_passage())
                        self.doors.append((self.mapvert-2, char+1))
                    elif "-" == line[char]:
                        newline.append(make_wall(side="-"))
                    elif "|" == line[char]:
                        newline.append(make_wall(side="|"))
                    elif "." == line[char]:
                        newline.append(make_floor())
                        self.empty_tiles.append((self.mapvert-2, char+1))
                    elif "#" == line[char]:
                        newline.append(make_passage())
                    elif " " == line[char]:
                        newline.append(make_void())
                except IndexError:
                    newline.append(make_void())
            self.layer1.append(newline)
        self.layer1.append([make_void()])
        self.layer1.insert(0, [make_void()])
        try:
            getmap.close()
        except AttributeError:
            pass # didn't use a file
        random.shuffle(self.empty_tiles)
        for i in self.doors:
            self.layer2[i] = Door(location=i)

        # Pad the ragged edges with Void
        while len(self.layer1) < self.scr_y:
            self.layer1.append([])
        for line in self.layer1:
            line.insert(0, make_void())
            while len(line) < max(self.maphoriz, self.scr_x):
                line.append(make_void())

        self.session.world[self.name] = self

        # Collapse these into self.populate()
        self.up = self.random_tile()
        self.down = self.random_tile()

        self.populate()

    def random_tile(self):
        """Return a random tile of empty floor. Intended to be used
        only at initialization, as it does not reset.
        Might make this more robust later.
        """
        return self.empty_tiles.pop()

    def populate(self):
        """Put the randomly-generated entities on the map."""
        self.layer2[self.up] = StairsUp(floor=self, location=self.up)
        self.layer2[self.down] = StairsDown(floor=self, location=self.down)
#        for i in range(10):
#            try:
#                self.spawn(random.choice(self.items))
#            except IndexError:
#                pass
        for i in range(10):
            try:
                self.spawn(random.choice(self.monsters))
            except IndexError:
                pass

    def probe(self, coordinates):
        """Return whatever object is visible on the map at that location."""
        if coordinates in self.layer3.keys():
            return self.layer3[coordinates]
        elif coordinates in self.layer2.keys():
            return self.layer2[coordinates]
        else:
            return self.layer1[coordinates[0]][coordinates[1]]

    def traverse_test(self, coordinates, moving_rookwise=False):
        """Is it possible for an entity to walk onto the given tile?"""
        try:
            if not self.layer3[coordinates].traversable:
                return False
        except KeyError:
            pass
        try:
            if not self.layer2[coordinates].traversable:
                return False
            if self.layer2[coordinates].traversable == 'rookwise' \
               and not moving_rookwise:
                return False
        except KeyError:
            pass
        if not self.layer1[coordinates[0]][coordinates[1]].traversable:
            return False
        elif self.layer1[coordinates[0]][coordinates[1]].traversable == 'rookwise' and not moving_rookwise:
            return False
        return True

    def spawn(self, ent, coordinates=None):
        """Places an entity on the map at the specified coordinates."""
        if coordinates == None:
            coordinates = self.random_tile()
        new_ent = copy.deepcopy(ent)
        if isinstance(new_ent, Monster):
            self.layer3[coordinates] = new_ent
        else:
            self.layer2[coordinates] = new_ent
        new_ent.floor = self
        new_ent.location = coordinates


def make_floor():
    """Generate one floor tile."""
    return Entity(name="bare floor", indef_article="", symbol=".",
                  description="Bare floor.")

def make_passage():
    """Generate one passage tile."""
    return Entity(name="passage", symbol="#", traversable='rookwise',
                  description="A dungeon passage.")

def make_wall(side="-"):
    """Generate one wall tile."""
    return Entity(name="wall", symbol=side, description="A wall.", opaque=True,
                  traversable=False)

def make_void():
    """Generate one void tile."""
    return Entity(symbol=" ", description="There's nothing there.",
                  traversable=False)

shouts = []
