#!/usr/bin/python

import objects, monsters
import curses, traceback, string, pickle, sys
import curses.panel
import unittest

# These are dummy values.
# standard screen size is 80 x 24.
scr_x = 80
scr_y = 22
x_center = scr_x / 2
y_center = scr_y / 2

# Dummy values. These will be loaded from a file later, to better support
# saving and loading partially-completed games.
PC_position = (5,5) # 86, 11 to test - this is the player's starting position

class Session(object):

    def __init__(self, name):
        self.name = name
        self.PC = objects.Player()
        self.world = {}

    def save_game(self, savename=""):
        if "" != savename:
            self.name = savename
            output = open(self.name, 'w')
            pickle.dump(self, output)
            output.close()

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
        self.filename = "{n}_{dep}.txt".format(n=self.name, dep=depth)

        self.layer1 = []
        self.layer2 = {} # (i,j) : object
        self.layer3 = {}

        self.maphoriz = 0
        self.mapvert = 2

        self.x_offset = 0
        self.y_offset = 0

    def load_map(self, session):
        '''
        Build layer 1 of a map from a text file. A border of void is added to
        each side; this prevents errors when fleeing monsters reach the edge.
        '''
        getmap = open(self.filename, 'r')
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
                    elif "#" == line[char]:
                        newline.append(objects.make_passage())
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

        session.world[self.name] = self
        self.session = session

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

class MapScreen(object):

    def __init__(self, session):
        self.window = curses.newwin((scr_y-2), scr_x, 1, 0)
        self.session = session

    def display(self, floor):
        """
        Updates the content of self.window, which is the map's curses window.
        Data comes from the floor that is passed in.
        This is a window instead of a pad because the real processing happens
        in the layerN structures, and windows are easier to pass to panels.
        """
        # Draw Layer 1
        coords = track(self.session.PC)
        for y in range(scr_y):
            for x in range(scr_x-1):
                try:
                    draw1 = floor.layer1[y+coords[0]][x+coords[1]]
                    self.window.addch(y, x, draw1.symbol)
                except IndexError:
                    pass
                except curses.error:
                    pass
        for item in floor.layer2.keys():
            # add an if statement so things don't get drawn off the map
            if (item[0] >= coords[0] and item[0] <= coords[2]) and \
               (item[1] >= coords[1] and item[1] <= coords[3]):
                self.window.addstr(item[0]-coords[0], item[1]-coords[1],
                                  floor.layer2[item].symbol)
        for item in floor.layer3.keys():
            if (item[0] >= coords[0] and item[0] <= coords[2]) and \
               (item[1] >= coords[1] and item[1] <= coords[3]):
                self.window.addstr(item[0]-coords[0], item[1]-coords[1],
                                  floor.layer3[item].symbol)
        self.window.noutrefresh()

class InventoryMenu(object):

    def __init__(self, session):
        self.window = curses.newwin(scr_y-1, scr_x, 1, 0)
        self.listing = {}
        self.session = session

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
                for j in self.session.PC.equipped.keys():
                    if self.session.PC.equipped[j] == hoard[i]:
                        self.window.addstr(" ({0})".format(j))

                self.window.move(4+i, 1)

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

    def ask_player(self, query):
        self.window.clear()
        self.window.addstr(0,0, query)
        self.window.addstr(" ")
        curses.echo()
        curses.curs_set(1)
        response = self.window.getstr()
        curses.curs_set(0)
        curses.noecho()
        return response

    def vent(self):
        while self.messages != []:
            self.shift()

class HUD(object):

    def __init__(self, session):
        self.window = curses.newwin(1, scr_x, scr_y-1, 0)
        self.frame = "Level: {0.stats[level]}   HP: {0.hp}   Mana: {0.mana}"
        self.session = session

    def display(self):
        self.window.addstr(0,0, self.frame.format(self.session.PC))
        self.window.noutrefresh()
        curses.doupdate() # lest HP counters update too late

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

def new_map_loop(session, map_screen, command=None):
    '''
    Move the player around on the map, and perform simple actions (anything
    that can be accomplished by calling PC.foo(bar) and won't kick the game out
    of map mode). More complex actions are returned back to the main loop.
    '''
    command = check_command(map_screen.window, command)
    if command in compass.keys():
        session.PC.move(compass[command][0], compass[command][1])
    elif command.lower() in compass.keys():
        session.PC.move(compass[command.lower()][0], compass[command.lower()][1])
        session.PC.running = True
    elif "t" == command:
        session.PC.take()
    elif "." == command:
        session.PC.rest()
    elif ">" == command:
        session.PC.descend()
    elif "<" == command:
        session.PC.ascend()
    else:
        return command
    while 0 < session.PC.initiative:
        for i in session.PC.floor.layer3.values():
            if 0 == i.initiative:
                i.act(session.PC)
        tick(session)
    while session.PC.running:
        new_map_loop(session, map_screen, command.lower())
    map_screen.display(session.PC.floor)
    mode = 'mapnav'

def view_loop(session, map_screen, command=None):
    curses.curs_set(2)
    crosshairs = [y_center, x_center]
    map_screen.window.move(crosshairs[0], crosshairs[1])
    command = check_command(map_screen.window, command)
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
      
        map_screen.window.move(crosshairs[0], crosshairs[1])
        command = map_screen.window.getkey()

    if "\n" == command:
        mode = 'mapnav'
        curses.curs_set(0)
        map_screen.display(session.PC.floor)
        curses.doupdate
        return (crosshairs[0]+session.PC.floor.y_offset,
                crosshairs[1]+session.PC.floor.x_offset)
    elif " " == command:
        mode = 'mapnav'
        curses.curs_set(0)
        map_screen.window.display(session.PC.floor)
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
    elif 'w' == command:
        query = "Which item would you like to wield or wear?"
    elif 'r' == command:
        query = "Which item would you like to remove?"
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
            inv.hide()
            curses.panel.update_panels()
            curses.doupdate()
            return None
        elif command.isalpha() and command.lower() in hoard.listing.keys():
            mode = 'mapnav'
            inv.hide()
            curses.panel.update_panels()
            curses.doupdate()
            return hoard.listing[command.lower()]
        command = None

def cutscene(title, content, options, command=None):
    cut = Dialogue(title, content, options)
    cutscene_panel = curses.panel.new_panel(cut.window)
    cut.display()
    curses.panel.update_panels()
    cutscene_panel.top()
    cutscene_panel.show()

def title_screen_startup(title):
    command = None
    while True:
        title.display()
        curses.panel.update_panels()
        curses.doupdate()
        if "1" == command: # new game
            session = Session("awesome")
            test = Floor(name="testmap")
            test.load_map(session) # map gets loaded here

            session.PC.floor = test
            session.PC.location = PC_position
            test.layer3[session.PC.location] = session.PC
            testitem = objects.Item(floor=session.PC.floor, location=(6,10),
                                    name="Nondescript item", symbol='$')
            testweapon = objects.Item(floor=session.PC.floor, location=(4,16),
                                      equip_slot='melee weapon',
                                      name="Basic Sword", symbol='/')
            testmonster = monsters.Zombie(flr=session.PC.floor, loc=(7,11))
            teststairs = objects.StairsDown(floor=session.PC.floor, location=(12,35))
            return session
        if "2" == command: # load game
            title.window.addstr(18,29, "File to load: ")
            curses.echo()
            curses.curs_set(1)
            response = title.window.getstr()
            curses.curs_set(0)
            curses.noecho()
            try:
                session = pickle.load(open(response, 'r'))
                return session
            except:
                title.display()
                curses.panel.update_panels()
                title.window.addstr(18,29, "Couldn't load requested file.")
        if "3" == command: # help
            break
        if "4" == command: # quit
            sys.exit()
        command = title.window.getkey()

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
#    stdscr.clear()

    alerts = AlertQueue(thisgame)
    invent = InventoryMenu(thisgame)
    heads_up_display = HUD(thisgame)
    map_display = MapScreen(thisgame)
#    curses.doupdate()

#    stdscr.refresh()

    alerts.push("Hello Vanya, welcome to the Dungeons of Doom")

    # Initialize the stack of panels.
    # May need to do something else to keep them in order.
    map_panel = curses.panel.new_panel(map_display.window)
    hud_panel = curses.panel.new_panel(heads_up_display.window)
    menu_panel = None
    message_panel = curses.panel.new_panel(alerts.window)
    inventory_panel = curses.panel.new_panel(invent.window)

#    command = " "
    curses.curs_set(0)
    menu_flag = None

    # do these when first displaying the map
    map_display.display(thisgame.PC.floor) # why is it blank at this point?
    map_panel.top()
    heads_up_display.display()
    alerts.shift()
    # adding more map loops here just delays drawing

#    curses.doupdate()

    while True:

        if 'mapnav' == mode:
            leave_map = new_map_loop(thisgame, map_display)
            if None == leave_map:
                pass
            elif leave_map in 'EIdeirw':
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
                newname = alerts.ask_player("Save game as (leave blank to overwrite):")
                thisgame.save_game(savename=newname)
                alerts.push("Game saved as %s." % thisgame.name)
            alerts.shift()
            heads_up_display.display()

        if 'view' == mode:
            alerts.push("Use movement keys to select a cell on the map. (Shift-move to go 5 squares.)")
            alerts.shift()
            # move cursor to its current position
            leave_map = view_loop(thisgame, map_display)
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
                mode = 'mapnav' # "up here"
                curses.doupdate # "up here"
                if "I" == menu_flag:
                    returned_item.use(user=thisgame.PC)
                elif "d" == menu_flag:
                    thisgame.PC.drop(returned_item)
                elif 'e' == menu_flag:
                    alerts.push(returned_item.description)
                elif 'E' == menu_flag:
                    if None != returned_item.longdesc:
                        cutscene(returned_item.name, returned_item.longdesc,
                                 None)
                    else:
                        cutscene(returned_item.name, returned_item.description,
                                 None)
                elif 'w' == menu_flag:
                    thisgame.PC.wield_or_wear(returned_item)
                elif 'r' == menu_flag:
                    thisgame.PC.remove(returned_item)
            mode = 'mapnav' # moved up there for message chains
                            # but exiting i with space stopped working
            heads_up_display.display()
            ## start added block -- Patched!
            ## make initiative work with a heap or something
            alerts.push("Maybe this is where it needs to happen.")
            while 0 < thisgame.PC.initiative:
                for i in thisgame.PC.floor.layer3.values():
                    if 0 == i.initiative:
                        i.act(thisgame.PC)
                        map_display.display(thisgame.PC.floor)
                tick(thisgame)
            ## end of added block
            alerts.shift()
            map_display.display(thisgame.PC.floor)
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


#curses.wrapper(runit)

if __name__ == '__main__':
    curses.wrapper(runit)
