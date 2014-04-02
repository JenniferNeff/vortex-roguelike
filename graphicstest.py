#!/usr/bin/python

import objects
import curses, traceback
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

# Figure out a reasonable slice of the map to display
# such that the PC remains in the center of the screen,
# but the display never slips off the edges of the map.

def track(limit_y, limit_x): # arguments are the size of the map
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

        self.window = curses.newwin(scr_y-1, scr_x, 1, 0)
        self.maphoriz = 0
        self.mapvert = 0

    def load_map(self, mapfile):
        getmap = open(mapfile, 'r')
        for line in getmap:
            newline = []
            self.mapvert += 1
            for char in range(len(line)):
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
        getmap.close()

        for line in self.layer1:
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

class AlertQueue(object):
    # implement as a collection.deque later?

    def __init__(self):
        self.messages = []
        self.window = curses.newwin(1, scr_x, 0, 0)

    def push(self, message):
        self.messages.append(message)

    def shift(self):
        self.messages.extend(objects.shouts)
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
            

def mapnavigation(command):
    if command in compass.keys():
        PC.move(compass[command][0], compass[command][1])
        for i in HUD_list:
            i.display()
    PC.floor.display()
    #elif command == "l":
        # Ask player a question...
        # will need a separate window to sit on top and contain messages

# Modes are: title, mapnav, maplook, menu...more?

mode = ["title"]

def runit(stdscr):
    stdscr.clear()

    alerts = AlertQueue()

    #stdscr.addstr("Hello Vanya, welcome to the Dungeons of Doom")
    stdscr.refresh()
    stdscr.getkey()

    test = Floor(name="Testing Map")
    test.load_map("testmap2")

    PC.floor = test
    PC.location = PC_position
    test.layer3[PC.location] = PC

    testitem = objects.Item(floor=test, location=(8,8))
    #test.layer2[testitem.location] = testitem

    test.display()

    mode.append("mapnav")

    alerts.push("Hello Vanya, welcome to the Dungeons of Doom")
    #alerts.push("Second test message")
    #alerts.push("Third test message")

    # Initialize the stack of panels.
    # May need to do something else to keep them in order.
    map_panel = curses.panel.new_panel(test.window)
    hud_panel = None
    menu_panel = None
    message_panel = curses.panel.new_panel(alerts.window)

    while True:
        curses.doupdate()
        command = stdscr.getkey()
        if "q" == command:
            break
        if "mapnav" == mode[-1]:
            alerts.shift()
            alerts.window.clear()
            mapnavigation(command)
        if "message" == mode[-1]:
            if " " == command:
                alerts.shift()

curses.wrapper(runit)
