#!/usr/bin/python

import objects
import curses, traceback, string, pickle, sys
import curses.panel

# These are dummy values.
# standard screen size is 80 x 24.
scr_x = 80
scr_y = 22
x_center = scr_x / 2
y_center = scr_y / 2

# Dummy values. These will be loaded from a file later, to better support
# saving and loading partially-completed games.
#PC = objects.Player()
PC_position = (5,5) # 86, 11 to test - this is the player's starting position
#all_levels = []


class Session(object):

    def __init__(self, name):
        self.name = "%s.vor" % name
        self.PC = objects.Player()
        self.world = []

    def save_game(self):
        output = open(self.name, 'w')
        pickle.dump(self, output)
        output.close()

#    def load_game(load):
#        input_file = pickle.load(open(load, 'r'))
#        self.PC = input_file.PC
#        self.world = input_file.world

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

def tick(session):
    for i in session.PC.floor.layer2.values():
        i.initiative -= 1
    for i in session.PC.floor.layer3.values():
        i.initiative -= 1


def track(target):
    '''
    Figure out a reasonable slice of the map to display such that the PC
    remains in the center of the screen, but the display never slips off
    the edges of the map.
    '''
    upperleft_x = target.location[1] - x_center
    upperleft_y = target.location[0] - y_center
    lowerright_x = upperleft_x + (scr_x-1)
    lowerright_y = upperleft_y + (scr_y-1)

    while lowerright_x > target.floor.maphoriz:
        upperleft_x -= 1
        lowerright_x -= 1
    while lowerright_y > target.floor.mapvert:
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

    target.floor.x_offset = upperleft_x
    target.floor.y_offset = upperleft_y

    return (upperleft_y, upperleft_x, lowerright_y, lowerright_x)

class Floor(object):

    def __init__(self, name="Unknown Location", depth=0):
        self.name = name
        self.depth = depth

        self.layer1 = []
        self.layer2 = {} # (i,j) : object
        self.layer3 = {}

        self.window = curses.newwin(scr_y-2, scr_x, 1, 0)
        self.maphoriz = 0
        self.mapvert = 2

        self.x_offset = 0
        self.y_offset = 0

    def load_map(self, mapfile, session):
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

        session.world.append(self)
        self.session = session

    def display(self):
        """
        Updates the content of self.window, which is the map's curses window.
        Updating the actual data in the map happens before this, and drawing
        the level on the screen happens later.
        This is a window instead of a pad because the real processing happens
        in the layerN structures, and windows are easier to pass to panels.
        """
        # Draw Layer 1
        coords = track(self.session.PC)
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

    def probe(self, coordinates):
        """
        Return whatever object is visible on the map at that location.
        """
        if coordinates in self.layer3.keys():
            return self.layer3[coordinates]
        elif coordinates in self.layer2.keys():
            return self.layer2[coordinates]
        else:
            return self.layer1[coordinates[0]][coordinates[1]]

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

class Dialogue(object):
    '''
    Display a full screen with a title (like an item's name, or the name of
    an NPC you are talking to) and some content, and then a set of choices
    (dialogue options, choices for how to interact with an object, etc.)
    '''

    def __init__(self, title, content, options):
        self.window = curses.newwin(scr_y-1, scr_x, 1, 0)
        self.title = title
        self.content = content
        self.options = options

    def display(self):
        if None == self.options:
            self.options = ["Continue"]
        self.window.clear()
        self.window.addstr(1,1, self.title)
        self.window.addstr(3,1, self.content)

        self.window.move(20-len(self.options),1)
        for i in range(len(self.options)):
            self.window.addstr("%s: %s" % (i+1, self.options[i]))
        self.window.noutrefresh()
        curses.doupdate()
        dialogueoption = "0"
        while not int(dialogueoption)-1 in range(len(self.options)):
            dialogueoption = self.window.getkey()
            if not dialogueoption.isdigit():
                dialogueoption = "0"

class AlertQueue(object):
    # implement as a collection.deque later?

    def __init__(self, session):
        self.messages = []
        self.window = curses.newwin(1, scr_x, 0, 0)
        self.session = session

    def push(self, message):
        self.messages.append(message)

    def shift(self):
        self.messages.extend(objects.shouts)
        objects.shouts = []
        try:
            message_to_show = self.messages.pop(0)
            self.session.PC.running = False # kick the player out of running upon news
        except IndexError:
            message_to_show = ""
        if self.messages != []:
            message_to_show = "%s [MORE]" % message_to_show
        self.window.clear()
        self.window.addstr(0,0, message_to_show)
        self.window.noutrefresh()
        curses.doupdate()
        while len(self.messages) > 0:
            scroll = self.window.getkey()
            if " " == scroll:
                self.shift()

    def vent(self):
        while self.messages != []:
            self.shift()

class HUD(object):

    def __init__(self, session):
        self.window = curses.newwin(1, scr_x, scr_y-1, 0)
        self.frame = "Level: {0.level}   HP: {0.hp}   Mana: {0.mana}"
        self.session = session

    def display(self):
        self.window.addstr(0,0, self.frame.format(self.session.PC))
        self.window.noutrefresh()

class Titlescreen(object):

    def __init__(self):
        self.window = curses.newwin(scr_y, scr_x, 0, 0)

    def display(self):
        splash = open("titlescreen.vortex", 'r')
        try:
            self.window.addstr(0,0, splash.read())
        except curses.error:
            pass
        splash.close()

def check_command(win,c):
    if None == c:
        return win.getkey()
    else:
        return c

def new_map_loop(session, command=None):
    '''
    Move the player around on the map, and perform simple actions (anything
    that can be accomplished by calling PC.foo(bar) and won't kick the game out
    of map mode). More complex actions are returned back to the main loop.
    '''
    command = check_command(session.PC.floor.window, command)
    if command in compass.keys():
        session.PC.move(compass[command][0], compass[command][1])
    elif command.lower() in compass.keys():
        session.PC.move(compass[command.lower()][0], compass[command.lower()][1])
        session.PC.running = True
    elif "t" == command:
        session.PC.take()
    elif "." == command:
        session.PC.rest()
    else:
        return command
    while 0 < session.PC.initiative:
        for i in session.PC.floor.layer3.values():
            if 0 == i.initiative:
                i.act(session.PC)
        tick(session)
    while session.PC.running:
        new_map_loop(session, command.lower())
    session.PC.floor.display()
    curses.doupdate
    mode = 'mapnav'

def view_loop(session, command=None):
    curses.curs_set(2)
    crosshairs = [y_center, x_center]
    session.PC.floor.window.move(crosshairs[0], crosshairs[1])
    command = check_command(session.PC.floor.window, command)
    while "\n" != command and " " != command:
        if command in compass.keys():
            crosshairs = [crosshairs[0]+compass[command][0],
                          crosshairs[1]+compass[command][1]]
        elif command.lower() in compass.keys():
            crosshairs = [crosshairs[0]+compass[command.lower()][0]*5,
                          crosshairs[1]+compass[command.lower()][1]*5]
        crosshairs[0] = max(crosshairs[0], 0)
        crosshairs[0] = min(crosshairs[0], scr_y-3)
        crosshairs[1] = max(crosshairs[1], 0)
        crosshairs[1] = min(crosshairs[1], scr_x-1)
      
        session.PC.floor.window.move(crosshairs[0], crosshairs[1])
        command = session.PC.floor.window.getkey()

    if "\n" == command:
        mode = 'mapnav' # exit view mode
        curses.curs_set(0)
        session.PC.floor.display()
        curses.doupdate
        return (crosshairs[0]+session.PC.floor.y_offset,
                crosshairs[1]+session.PC.floor.x_offset)
    elif " " == command:
        mode = 'mapnav' # exit view mode
        curses.curs_set(0)
        session.PC.floor.display()
        curses.doupdate
        return None

def new_inventory_loop(session, hoard, inv, command):
    if 'i' == command:
        query = "You are carrying:"
    elif 'I' == command:
        query = "Which item would you like to Invoke?"
    elif 'd' == command:
        query = "Which item would you like to drop?"
    elif 'e' == command:
        query = "Which item would you like to examine?"
    elif 'E' == command:
        query = "Which item would you like to Examine Closely?"
    hoard.display(session.PC.inventory, query)
    inv.top()
    inv.show()
    curses.panel.update_panels()
    curses.doupdate()
    command = None

    while None == command:
        command = hoard.window.getkey()
        if " " == command:
            mode = 'mapnav'
            curses.panel.update_panels()
            curses.doupdate()
            inv.hide()
            return None
        elif command.isalpha() and command.lower() in hoard.listing.keys():
            mode = 'mapnav'
            curses.panel.update_panels()
            curses.doupdate()
            inv.hide()
            return hoard.listing[command.lower()]
        command = None

def cutscene(title, content, options, command=None):
    cut = Dialogue(title, content, options)
    cutscene_panel = curses.panel.new_panel(cut.window)
    cut.display()
    curses.panel.update_panels()
    #curses.doupdate()
    cutscene_panel.top()
    cutscene_panel.show()

def title_screen_startup(title):
    title.display()
    curses.panel.update_panels()
    #curses.doupdate()
    command = None
    while True:
        curses.doupdate()
        if "1" == command: # new game
            session = Session("awesome")
            test = Floor(name="Testing Map")
            test.load_map("testmap2", session)

            session.PC.floor = test
            session.PC.location = PC_position
            test.layer3[session.PC.location] = session.PC
            testitem = objects.Item(floor=session.PC.floor, location=(6,10))
            testmonster = objects.Monster(floor=session.PC.floor,
                                          location=(7,11))
            return session
        if "2" == command: # load game
            session = pickle.load(open("awesome.vor", 'r'))
            return session
        if "3" == command: # help
            break
        if "4" == command: # quit
            sys.exit()
        command = title.window.getkey()

# The wisdom you need is here:
# http://python.about.com/od/pythonstandardlibrary/a/pickle_intro.htm

# Modes are:
# title : title screen? Maybe just make this a cutscene
# mapnav : map navigation
# inventory : viewing an inventory menu
# cutscene : view a screen with title, text, and a few options
# view : move a cursor around the map


def runit(stdscr):

    # Initialize title screen.
    titlescreen = Titlescreen()
    title_panel = curses.panel.new_panel(titlescreen.window)

    thisgame = title_screen_startup(titlescreen)
    mode = 'mapnav'
    stdscr.clear()

    alerts = AlertQueue(thisgame)
    invent = InventoryMenu()
    heads_up_display = HUD(thisgame)

    stdscr.refresh()

    alerts.push("Hello Vanya, welcome to the Dungeons of Doom")

    # Initialize the stack of panels.
    # May need to do something else to keep them in order.
    map_panel = curses.panel.new_panel(thisgame.PC.floor.window)
    hud_panel = curses.panel.new_panel(heads_up_display.window)
    menu_panel = None
    message_panel = curses.panel.new_panel(alerts.window)
    inventory_panel = curses.panel.new_panel(invent.window)

#    command = " "
    curses.curs_set(0)
    menu_flag = None

    # do these when first displaying the map
    heads_up_display.display()
    thisgame.PC.floor.display()
    alerts.shift()
    curses.doupdate()

    while True:

        if 'mapnav' == mode:
            leave_map = new_map_loop(thisgame)
            if None == leave_map:
                pass
            elif leave_map in 'EIdei':
                if [] == thisgame.PC.inventory:
                    alerts.push("You're not carrying anything.")
                else:
                    mode = 'inventory'
                    menu_flag = leave_map
            elif leave_map in 'v':
                mode = 'view'
            elif 'q' == leave_map:
                sys.exit()
            elif 's' == leave_map:
                thisgame.save_game()
                alerts.push("Game saved.")
            alerts.shift()
            heads_up_display.display()

        if 'view' == mode:
            alerts.push("Use movement keys to select a cell on the map. (Shift-move to go 5 squares.)")
            alerts.shift()
            # move cursor to its current position
            leave_map = view_loop(thisgame)
            if None == leave_map:
                pass
            else:
                alerts.push("You see %s%s at position %s." % \
                  (thisgame.PC.floor.probe(leave_map).indef_article,
                   thisgame.PC.floor.probe(leave_map).name,
                   str(leave_map)))
            mode = 'mapnav'
            alerts.shift()
            heads_up_display.display()

        elif 'inventory' == mode:
            alerts.window.clear()
            returned_item = new_inventory_loop(thisgame, invent,
                                               inventory_panel, menu_flag)
            if None != returned_item: # Move this into inventory function
                if "I" == menu_flag:
                    returned_item.use(user=thisgame.PC)
                elif "d" == menu_flag:
                    PC.drop(returned_item)
                elif 'e' == menu_flag:
                    alerts.push(returned_item.description)
                elif 'E' == menu_flag:
                    if None != returned_item.longdesc:
                        cutscene(returned_item.name, returned_item.longdesc,
                                 None)
                    else:
                        cutscene(returned_item.name, returned_item.description,
                                 None)
            mode = 'mapnav'
            heads_up_display.display()
            alerts.shift()
            curses.doupdate

        elif 'title' == mode:
            title_panel.top()
            title_panel.show()
            title_screen_startup(titlescreen, thisgame)

            title_panel.hide()
            mode = 'mapnav'
            heads_up_display.display()
            alerts.shift()
            curses.doupdate


curses.wrapper(runit)