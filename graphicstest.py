#!/usr/bin/python

import objects
import curses, traceback, string
import curses.panel

# These are dummy values.
# standard screen size is 80 x 24.
scr_x = 80
scr_y = 22
x_center = scr_x / 2
y_center = scr_y / 2

# Dummy values. These will be loaded from a file later, to better support
# saving and loading partially-completed games.
PC = objects.Player()
PC_position = (5,5) # 86, 11 to test
HUD_list = []

# Basic movement keys; same as in Rogue
compass = {
"h": (0,-1),
"j": (1,0),
"k": (-1,0),
"l": (0,1),
"y": (-1,-1),
"u": (-1,1),
"b": (1,-1),
"n": (1,1)
}

def tick():
    for i in PC.floor.layer2.values():
        i.initiative -= 1
    for i in PC.floor.layer3.values():
        i.initiative -= 1


def track(limit_y, limit_x): # arguments are the size of the map
    '''
    Figure out a reasonable slice of the map to display such that the PC
    remains in the center of the screen, but the display never slips off
    the edges of the map.
    '''
    upperleft_x = PC.location[1] - x_center
    upperleft_y = PC.location[0] - y_center
    lowerright_x = upperleft_x + (scr_x-1)
    lowerright_y = upperleft_y + (scr_y-1)

    while lowerright_x > limit_x:
        upperleft_x -= 1
        lowerright_x -= 1
    while lowerright_y > limit_y:
        upperleft_y -= 1
        lowerright_y -= 1
    while 0 > upperleft_x:
        upperleft_x += 1
        lowerright_x += 1
    while 0 > upperleft_y:
        upperleft_y += 1
        lowerright_y += 1

    # Printing these things breaks the display but is sometimes needed to test
    #print (limit_y, limit_x)
    #print (upperleft_y, upperleft_x, lowerright_y, lowerright_x)

    return (upperleft_y, upperleft_x, lowerright_y, lowerright_x)

class Floor(object):

    def __init__(self, name="Unknown Location", depth=0):
        self.name = name
        self.depth = depth

        self.layer1 = []
        self.layer2 = {} # object: (i,j) : object
        self.layer3 = {}

        self.window = curses.newwin(scr_y-2, scr_x, 1, 0)
        self.maphoriz = 0
        self.mapvert = 0

    def load_map(self, mapfile):
        '''
        Build layer 1 of a map from a text file. A border of void is added to
        each side; this prevents errors when fleeing monsters reach the edge.
        '''
        getmap = open(mapfile, 'r')
        for line in getmap:
            newline = []
            self.mapvert += 1
            for char in range(len(line)+1):
                if self.maphoriz < char:
                    self.maphoriz = char
                try:
                    if "+" == line[char]:
                        newline.append(objects.make_wall())
                    elif "-" == line[char]:
                        newline.append(objects.make_wall(side="-"))
                    elif "|" == line[char]:
                        newline.append(objects.make_wall(side="|"))
                    elif "." == line[char]:
                        newline.append(objects.make_floor())
                    elif " " == line[char]:
                        newline.append(objects.make_void())
                except IndexError:
                    newline.append(objects.make_void())
            self.layer1.append(newline)
        self.layer1.append([objects.make_void()])
        self.layer1.insert(0, [objects.make_void()])
        getmap.close()

        for line in self.layer1:
            line.insert(0, objects.make_void())
            while len(line) < self.maphoriz:
                line.append(objects.make_void())

    def display(self):
        """
        Updates the content of self.window, which is the map's curses window.
        Updating the actual data in the map happens before this, and drawing
        the level on the screen happens later.
        This is a window instead of a pad because the real processing happens
        in the layerN structures, and windows are easier to pass to panels.
        """
        # Draw Layer 1
        coords = track(self.mapvert, self.maphoriz)
        for y in range(scr_y):
            for x in range(scr_x-1):
                try:
                    self.window.addch(y, x,
                      self.layer1[y+coords[0]][x+coords[1]].symbol)
                except IndexError:
                    pass
#                    self.window.addch(y, x, ord(" "))
                except curses.error:
                    pass
        for item in self.layer2.keys():
            # add an if statement so things don't get drawn off the map
            if (item[0] >= coords[0] and item[0] <= coords[2]) and \
               (item[1] >= coords[1] and item[1] <= coords[3]):
                self.window.addstr(item[0]-coords[0], item[1]-coords[1],
                                  self.layer2[item].symbol)
        for item in self.layer3.keys():
            if (item[0] >= coords[0] and item[0] <= coords[2]) and \
               (item[1] >= coords[1] and item[1] <= coords[3]):
                self.window.addstr(item[0]-coords[0], item[1]-coords[1],
                                  self.layer3[item].symbol)
        self.window.noutrefresh()

class InventoryMenu(object):

    def __init__(self):
        self.window = curses.newwin(scr_y-1, scr_x, 1, 0)
        self.listing = {}

    def display(self, hoard, query=None): # hoard usually = PC.inventory
        hoard.sort()
        self.window.clear()
        self.listing.clear()
        if None == query:
            self.window.addstr(1,1, "You are carrying:")
        else:
            self.window.addstr(1,1, query)

        self.window.move(3,1)
        if 0 == len(hoard):
            self.window.addstr("Nothing!")
        else:
            for i in range(len(hoard)):
                self.window.addstr("%s: %s" % (string.ascii_uppercase[i],
                                               hoard[i].name))
                self.listing[string.ascii_lowercase[i]] = hoard[i]
                if PC.weapon == hoard[i]:
                    self.window.addstr(" (Weapon in hand)")
                elif PC.helm == hoard[i]:
                    self.window.addstr(" (On head)")
                elif PC.armor == hoard[i]:
                    self.window.addstr(" (On body)")
                elif PC.shoes == hoard[i]:
                    self.window.addstr(" (On feet)")
                elif PC.ring_right == hoard[i]:
                    self.window.addstr(" (On right hand)")
                elif PC.ring_left == hoard[i]:
                    self.window.addstr(" (On left hand)")
                elif PC.spellbook == hoard[i]:
                    self.window.addstr(" (Reading)")
                self.window.move(3+i, 1)

        self.window.addstr(20,0, "Press space to exit this screen")
        self.window.noutrefresh()
        curses.doupdate()

class AlertQueue(object):
    # implement as a collection.deque later?

    def __init__(self):
        self.messages = []
        self.window = curses.newwin(1, scr_x, 0, 0)

    def push(self, message):
        self.messages.append(message)

    def shift(self):
        self.messages.extend(objects.shouts)
        objects.shouts = []
        try:
            message_to_show = self.messages.pop(0)
            PC.running = False # kick the player out of running upon news
        except IndexError:
            message_to_show = ""
        if self.messages != []:
            message_to_show = "%s [MORE]" % message_to_show
            if "message" != mode[-1]:
                mode.append("message")
        else:
            while mode[-1] == "message":
                mode.pop()
        self.window.clear()
        self.window.addstr(0,0, message_to_show)
        self.window.noutrefresh()
        curses.doupdate()

    def vent(self):
        while self.messages != []:
            self.shift()

class HUD(object):

    def __init__(self):
        self.window = curses.newwin(1, scr_x, scr_y-1, 0)
        self.frame = "Level: {0.level}   HP: {0.hp}   Mana: {0.mana}"

    def display(self):
        self.window.addstr(0,0, self.frame.format(PC))
        self.window.noutrefresh()

def mapnavigation(command):
    if command in compass.keys():
        PC.move(compass[command][0], compass[command][1])
    elif "t" == command:
        PC.take()
    while 0 < PC.initiative:
        for i in PC.floor.layer3.values():
            if 0 == i.initiative:
                i.act(PC)
        for j in HUD_list:
            j.display()
        tick()
    PC.floor.display()

#def look(command):
#    if command in compass.keys():
        # move the cursor

def inventory(hoard, inv, command, query=None):
    hoard.display(PC.inventory, query)
    curses.panel.update_panels()
    curses.doupdate()
    inv.top()
    inv.show()

    if " " == command:
        mode.pop()
        mode.append("message")
        inv.hide()
        curses.panel.update_panels()
        curses.doupdate()
        return None
    elif None == command:
        pass
    elif command.isalpha():
        mode.pop()
        mode.append("message")
        inv.hide()
        curses.panel.update_panels()
        curses.doupdate()
        return hoard.listing[command]

# Modes are: title, mapnav, maplook, menu...more?

mode = ["title"]

def runit(stdscr):
    stdscr.clear()

    alerts = AlertQueue()
    invent = InventoryMenu()
    heads_up_display = HUD()

    stdscr.refresh()
#    stdscr.getkey()

    test = Floor(name="Testing Map")
    test.load_map("testmap2")

    PC.floor = test
    PC.location = PC_position
    test.layer3[PC.location] = PC

    testitem = objects.Item(floor=test, location=(6,10))
    testmonster = objects.Monster(floor=test, location=(7,11))
    #test.layer2[testitem.location] = testitem

    test.display()

    mode.append("mapnav")

    alerts.push("Hello Vanya, welcome to the Dungeons of Doom")

    # Initialize the stack of panels.
    # May need to do something else to keep them in order.
    map_panel = curses.panel.new_panel(test.window)
    hud_panel = curses.panel.new_panel(heads_up_display.window)
    menu_panel = None
    message_panel = curses.panel.new_panel(alerts.window)
    inventory_panel = curses.panel.new_panel(invent.window)

    command = " "
    curses.curs_set(0)

    while True:

        if "q" == command:
            curses.curs_set(1)
            break
        elif "i" == command:
            mode.append("inventory")
            inventory_question = None
            command = None
        elif "I" == command:
            if [] == PC.inventory:
                alerts.push("You're not carrying anything.")
            else:
                mode.append("inventory")
                inventory_question = "Which item would you like to Invoke?"
                command = None
        elif "." == command:
            PC.rest()

        if "inventory" == mode[-1]:
            alerts.window.clear()
            invoked = inventory(invent, inventory_panel, command,
                      query=inventory_question)
            if None != invoked:
                invoked.use(user=PC)
                curses.doupdate()
                alerts.shift()
                heads_up_display.display()
            curses.doupdate()
        elif "mapnav" == mode[-1]:
            mapnavigation(command)
            alerts.shift()
            heads_up_display.display()
        if "message" == mode[-1]:
            if " " == command:
                alerts.shift()
        curses.doupdate()
        command = stdscr.getkey()


curses.wrapper(runit)
