#!/usr/bin/python

import objects, monsters, new_levelgen
import curses, traceback, string, pickle, sys, random, collections, textwrap
import curses.panel
import unittest
import startup_cutscene
import pythoned_Item_list, pythoned_Food_list, pythoned_Monster_list

# These are dummy values.
# Standard screen size is 80 x 24; work default screen is a little smaller
# Maybe put these in an option file later
scr_x = 80
scr_y = 22
x_center = scr_x / 2
y_center = scr_y / 2

# Grand dictionaries of all the Entities in the game.
item_dict = pythoned_Item_list.all_the_things
food_dict = pythoned_Food_list.all_the_things
mons_dict = pythoned_Monster_list.all_the_things

class Session(object):
    """Contains the objects of a particular play-through of the game,
    kept together in a single "session" so the game can be saved and loaded.
    """

    def __init__(self, name):
        """Initialize the session.

        Arguments:
        name -- the name of the session as a string

        Also initializes:
        self.PC -- the Player object for this play-through
        self.world -- a dictionary of all the floors in this play-through.
                      These in turn contain the other objects
                      (monsters, NPCs, items)
        """
        self.name = name
        self.PC = objects.Player(sess=self.name)
        self.world = {}

    def save_game(self, savename=""):
        """Pickles the session."""
        if "" != savename:
            self.name = savename
            output = open(self.name, 'w')
            pickle.dump(self, output, 2)
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
    """Advance the game clock by one tick."""
    # Maybe this should be a Session method.
    for i in session.PC.floor.layer2.values():
        i.initiative -= 1
    for i in session.PC.floor.layer3.values():
        i.initiative -= 1


def track(target):
    """Figures out a reasonable slice of the map to display such that the PC
    remains in the center of the screen, but the display never slips off
    the edges of the map.
    Returns the corners of the slice to display as a tuple.
    """
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

    # Printing these things breaks the display but was used for testing
    # early on.
    #print (limit_y, limit_x)
    #print (upperleft_y, upperleft_x, lowerright_y, lowerright_x)

    target.floor.x_offset = upperleft_x
    target.floor.y_offset = upperleft_y

    return (upperleft_y, upperleft_x, lowerright_y, lowerright_x)

def level_filter(ents, lev):
    return [x for x in ents.values() if x.level <= lev and x.level < lev + 10]


class MapScreen(object):
    """Handles the curses window for the game map."""

    def __init__(self, session):
        """Initialize the curses window for the game map.
        This takes up the whole screen except for two lines:
        the message line at the top and the HUD line at the bottom.
        session -- the session this MapScreen belongs to
        """
        self.window = curses.newwin((scr_y-2), scr_x, 1, 0)
        self.session = session

    def display(self, floor):
        """Updates the content of self.window, which is the map's curses
        window. Data comes from the floor that is passed in.
        This is a window instead of a pad because the real processing happens
        in the layerN structures, and windows are easier to pass to panels.
        """
        # Draw Layer 1
        coords = track(self.session.PC)
        for y in range(scr_y):
            for x in range(scr_x):
                try:
                    draw1 = floor.layer1[y+coords[0]][x+coords[1]]
                    self.window.addch(y, x, draw1.symbol)
                except IndexError:
                    pass
                except curses.error:
                    pass
        for item in floor.layer2.keys():
            # add an if statement so things don't get drawn off the map
            if (item[0] >= coords[0] and item[0] < coords[2]-1) and \
               (item[1] > coords[1] and item[1] <= coords[3]):
                # Remove ^ the equals and you will see a strange thing happen.
                try:
                    self.window.addstr(item[0]-coords[0], item[1]-coords[1],
                                      floor.layer2[item].symbol)
                except curses.error:
                    pass
        for item in floor.layer3.keys():
            if (item[0] >= coords[0] and item[0] < coords[2]-1) and \
               (item[1] > coords[1] and item[1] <= coords[3]):
                self.window.addstr(item[0]-coords[0], item[1]-coords[1],
                                  floor.layer3[item].symbol)

        self.window.noutrefresh()

class InventoryMenu(object):
    """Handles the curses window for the player's inventory."""

    def __init__(self, session):
        """Initializes the inventory display.
        session -- the session this menu belongs to
        self.window -- covers whole screen except the message row
        self.listing -- dictionary that will contain the items to show
        """
        self.window = curses.newwin(scr_y-1, scr_x, 1, 0)
        self.listing = {}
        self.session = session

    def display(self, hoard, query="You are carrying:"):
        """Updates the inventory menu display.
        hoard -- the list of stuff in the inventory
                 (this is usually the PC's inventory)
        query -- a prompt for when it's not just a list of the player's stuff
                 (ex: "Which item would you like to Invoke?")
        """
        hoard.sort()
        self.window.clear()
        self.listing.clear()
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
    """Displays a full screen with a title (like an item's name, or
    the name of an NPC you are talking to) and some content, and then
    a set of choices (dialogue options, choices for how to interact
    with an object, etc.)
    """

    def __init__(self, title, content, options, branches=None):
        """Initializes a single page of dialogue.
        Arguments:
        title -- a string
        content -- can be a string, which will be converted to textwrapped
                   lines when initialized, or a pre-made list of strings.
        options -- a list of options that the player can respond with
        branches -- a list of functions that the corresponding options
                    will trigger. Can be Invocations, commands to
                    display other Dialogue pages, etc.
        """
        self.window = curses.newwin(scr_y, scr_x, 0, 0)
        self.title = title
        if isinstance(content, str):
            content = textwrap.wrap(content)
        self.content = content
        if None == options:
            options = ["Continue"]
        self.options = options
        self.branches = branches

    def display(self):
        """Updates the display for a page of dialogue."""
        self.window.clear()
        self.window.addstr(1,1, objects.smartcaps(self.title))
        for c in range(len(self.content)):
            self.window.addstr(3+c,1, self.content[c])

        self.window.move(20-len(self.options),1)
        for i in range(len(self.options)):
            self.window.addstr("%s: %s" % (i+1, self.options[i]))
        self.window.noutrefresh()
        curses.doupdate()
        

class AlertQueue(object):
    """Handles the message line at the top of the screen."""

    def __init__(self, session):
        """Initialize the message queue for a particular session."""
        self.messages = collections.deque()
        self.window = curses.newwin(1, scr_x, 0, 0)
        self.session = session

    def push(self, message):
        """Push a message onto the queue."""
        self.messages.append(message)

    def shift(self):
        """Shift a message off the queue and show the player.
        Adds a "[MORE]" tag if more messages are in the queue,
        and waits for the player to respond before showing the next.
        """
        self.messages.extend(objects.shouts)
        objects.shouts = []
        try:
            message_to_show = self.messages.popleft()
            # kick the player out of running mode upon news
            self.session.PC.running = False
        except IndexError:
            message_to_show = ""
        if len(self.messages) > 0:
            message_to_show = "%s [MORE]" % message_to_show
        self.window.clear()
        self.window.addstr(0,0, message_to_show)
        self.window.noutrefresh()
        curses.doupdate() # This one is critical
        while len(self.messages) > 0:
            scroll = self.window.getkey()
            if " " == scroll:
                self.shift()

    def ask_player(self, query):
        """Ask the player for input via the message line."""
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
        """Shift all messages off the queue for perusal."""
        while len(self.messages) > 0:
            self.shift()

class HUD(object):
    """Handles the status bar at the bottom of the screen."""

    def __init__(self, session):
        """Initialize the HUD for a particular session."""
        self.window = curses.newwin(1, scr_x, scr_y-1, 0)
        self.frame = "Level: {0.stats[level]}   HP: {0.hp}   Mana: {0.mana} {0.hungry} | Depth: {0.floor.depth}"
        self.session = session

    def display(self):
        """Update the HUD display."""
        self.window.addstr(0,0, self.frame.format(self.session.PC))
        self.window.noutrefresh()

class Titlescreen(object):
    """Handles the title screen at the beginning of the game."""

    def __init__(self):
        """Initialize the title screen as a window taking the whole screen."""
        self.window = curses.newwin(scr_y, scr_x, 0, 0)

    def display(self):
        """Update the title screen display."""
        splash = open("titlescreen.vortex", 'r')
        try:
            self.window.addstr(0,0, splash.read())
        except curses.error:
            pass
        splash.close()

def check_command(win,c):
    """Get a single-stroke command from the player.
    c -- an optional override
    """
    if None == c:
        return win.getkey()
    else:
        return c

def new_map_loop(session, map_screen, command=None):
    """Move the player around on the map, and perform simple actions
    (anything that can be accomplished by calling PC.foo(bar) and won't
    kick the game out of map mode).
    """
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
    # The stairs code is redundant; fix later
    elif ">" == command:
        send_player_to = session.PC.descend()
        try:
            if isinstance(send_player_to.destination, objects.StairsUp):
                session.PC.floor = send_player_to.destination.floor
                session.PC.location = send_player_to.destination.location
                session.PC.floor.layer3[session.PC.location] = session.PC
            elif isinstance(send_player_to.destination, int):
                target = session.PC.floor.depth+send_player_to.destination
                session.PC.floor = objects.Floor(name="Basement level {d}".format(d=target), sess=session, depth=target, screen_x=scr_x, screen_y=scr_y, items=level_filter(item_dict, target), foods=food_dict.values(), monsters=level_filter(mons_dict, target))
                session.PC.location = session.PC.floor.up
                session.PC.floor.layer3[session.PC.location] = session.PC
                send_player_to.destination = session.PC.floor.layer2[session.PC.location]
                session.PC.floor.layer2[session.PC.location].destination = send_player_to
        except IOError:
            pass
    elif "<" == command:
        send_player_to = session.PC.ascend()
        try:
            if isinstance(send_player_to.destination, objects.StairsDown):
                session.PC.floor = send_player_to.destination.floor
                session.PC.location = send_player_to.destination.location
                session.PC.floor.layer3[session.PC.location] = session.PC
            elif isinstance(send_player_to.destination, int):
                target = session.PC.floor.depth-send_player_to.destination
                session.PC.floor = objects.Floor(name="Basement level {d}".format(d=target), sess=session, depth=target, screen_x=scr_x, screen_y=scr_y, items=level_filter(item_dict, target), foods=food_dict.values(), monsters=level_filter(mons_dict, target))
                session.PC.location = session.PC.floor.down
                session.PC.floor.layer3[session.PC.location] = session.PC
                send_player_to.destination = session.PC.floor.layer2[session.PC.location]
                session.PC.floor.layer2[session.PC.location].destination = send_player_to
        except IOError:
            pass
    else:
        return command
    while 0 < session.PC.initiative:
        for i in session.PC.floor.layer3.values():
            if 0 == i.initiative:
                i.act(session.PC)
        tick(session)
    while session.PC.running:
        new_map_loop(session, map_screen, command.lower())
    mode = 'mapnav'

def view_loop(session, map_screen, command=None):
    """Allows the player to select a space on the map for information.
    Arguments:
    map_screen -- the MapScreen object to be examined
    command -- player-entered command to select or cancel
    """
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

    mode = 'mapnav'
    curses.curs_set(0)

    if "\n" == command:
        return (crosshairs[0]+session.PC.floor.y_offset,
                crosshairs[1]+session.PC.floor.x_offset)
    elif " " == command:
        return None

def new_inventory_loop(session, hoard, inv, command):
    """Handles viewing of the inventory.
    Arguments:
    session -- this session
    hoard -- the list of items to be displayed
    inv -- 
    command -- player-entered command to select an item or cancel
    """
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
            return None
        elif command.isalpha() and command.lower() in hoard.listing.keys():
            mode = 'mapnav'
            inv.hide()
            curses.panel.update_panels()
            return hoard.listing[command.lower()]
        command = None

def cutscene(page, command=None):
    """Creates and displays a new Dialogue object.
    Arguments:
    page -- a Dialogue object
    title -- the title of the dialogue page
    content -- a string or list of strings
    options -- a list of options for the player to select
    command -- the player's selection
    """
    cutscene_panel = curses.panel.new_panel(page.window)
    dialogueoption = 0
    while not int(dialogueoption)-1 in range(len(page.options)):
        page.display()
        dialogueoption = page.window.getkey()
        if not dialogueoption.isdigit():
            dialogueoption = -1
        else:
            dialogueoption = int(dialogueoption)
            if page.branches != None:
                try:
                    if isinstance(page.branches[dialogueoption - 1], Dialogue):
                        page = page.branches[dialogueoption - 1]
                        dialogueoption = 0
                except IndexError:
                    continue
    

def title_screen_startup(title):
    """Handles the title screen at the beginning of the game."""
    command = None
    while True:
        title.display()
        curses.panel.update_panels()
        curses.doupdate()
        if "1" == command: # new game
            page_two = Dialogue(title="And you are?...",
                                content=startup_cutscene.content_two,
                                options=None)
            page_one = Dialogue(title="Silicon Valley Times, 10/31/2015",
                                content=startup_cutscene.content_one,
                                options=["Read more..."],
                                branches=[page_two])

            cutscene(page_one, None) # comment out if borked
            session = Session("awesome")
            test = objects.Floor(name="testmap", sess=session,
                                 screen_x=scr_x, screen_y=scr_y,
                                 items=[], foods=[], monsters=[])
            session.world[test.name] = test
            #test.load_map(session) # map gets loaded here
            #test.populate() # this is in the Floor.__init__ function now

            session.PC.floor = test
            session.PC.location = (5,5)
            test.layer3[session.PC.location] = session.PC
            session.PC.floor.spawn(item_dict["testitem"], (6,10))
            session.PC.floor.spawn(item_dict["testweapon"], (4,16))
            session.PC.floor.spawn(food_dict["mesa1"], (5,20))
            session.PC.floor.spawn(mons_dict["zombie1"], (7,11))
            session.PC.floor.spawn(mons_dict["snake1"], (12,46))
            return session
        if "2" == command: # load game
            title.window.addstr(18,29, "File to load: ")
            curses.echo()
            curses.curs_set(1)
            response = title.window.getstr()
            try:
                return pickle.load(open(response, 'r'))
            except:
                title.display()
                curses.panel.update_panels()
                title.window.addstr(18,29, "Couldn't load requested file.")
                title.window.addstr(scr_y-1, 0, "")
        if "3" == command: # help
            help_file = open('front_help.txt', 'r')
            help_screen = Dialogue("Welcome to Vortex!", list(help_file), None)
            help_file.close()
            cutscene(help_screen, None)
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
    """Runs the game, establishing all required windows and loops for the
    different modes of the game.
    """

    # Initialize title screen.
    titlescreen = Titlescreen()
    title_panel = curses.panel.new_panel(titlescreen.window)

    thisgame = title_screen_startup(titlescreen)
    mode = 'mapnav'

    alerts = AlertQueue(thisgame)
    invent = InventoryMenu(thisgame)
    heads_up_display = HUD(thisgame)
    map_display = MapScreen(thisgame)

    alerts.push("Welcome to the demo level!")

    # Initialize the stack of panels.
    # May need to do something else to keep them in order.
    map_panel = curses.panel.new_panel(map_display.window)
    hud_panel = curses.panel.new_panel(heads_up_display.window)
    menu_panel = None
    message_panel = curses.panel.new_panel(alerts.window)
    inventory_panel = curses.panel.new_panel(invent.window)

    curses.curs_set(0)
    menu_flag = None

    # do these when first displaying the map
    map_panel.top()

    while True:

        if 'mapnav' == mode:
            # These four lines should be all that's needed to draw the map.
            map_display.display(thisgame.PC.floor)
            heads_up_display.display()
            alerts.shift()
            #curses.doupdate # the one in alerts.shift() covers it.

            leave_map = new_map_loop(thisgame, map_display)
            if None == leave_map:
                pass
            elif leave_map in 'EIdeirw':
                if [] == thisgame.PC.inventory:
                    alerts.push("You're not carrying anything.")
                else:
                    mode = 'inventory'
                    menu_flag = leave_map
            elif leave_map in 'Vv':
                mode = 'view'
            elif 'q' == leave_map:
                sys.exit()
            elif 's' == leave_map:
                newname = alerts.ask_player("Save game as (leave blank to overwrite):")
                thisgame.save_game(savename=newname)
                alerts.push("Game saved as %s." % thisgame.name)

        if 'view' == mode:
            alerts.push("Use movement keys to select a cell on the map. (Shift-move to go 5 squares.)")
            alerts.shift()
            if leave_map == 'V':
                view_closely = True
            else:
                view_closely = False
            # move cursor to its current position
            leave_map = view_loop(thisgame, map_display)
            if None == leave_map:
                pass
            elif not view_closely:
                look_at = thisgame.PC.floor.probe(leave_map)
                alerts.push("You see %s%s at position %s." % \
                  (look_at.indef_article, look_at.name, str(leave_map)))
            else:
                look_at = thisgame.PC.floor.probe(leave_map)
                cutscene(Dialogue(title=look_at.name,
                                  content=look_at.longdesc,
                                  options=None))
            mode = 'mapnav'

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
                        cutscene(Dialogue(title=returned_item.name,
                                          content=returned_item.longdesc,
                                          options=None))
                    else:
                        cutscene(Dialogue(title=returned_item.name,
                                          content=returned_item.description,
                                          options=None))
                elif 'w' == menu_flag:
                    thisgame.PC.wield_or_wear(returned_item)
                elif 'r' == menu_flag:
                    thisgame.PC.remove(returned_item)
            mode = 'mapnav' # moved up there for message chains
                            # but exiting i with space stopped working
            heads_up_display.display()
            ## start added block -- Patched!
            ## make initiative work with a heap or something
            #alerts.push("DEBUG: Maybe this is where it needs to happen.")
            while 0 < thisgame.PC.initiative:
                for i in thisgame.PC.floor.layer3.values():
                    if 0 == i.initiative:
                        i.act(thisgame.PC)
                        map_display.display(thisgame.PC.floor)
                tick(thisgame)
            ## end of added block

        elif 'title' == mode:
            title_panel.top()
            title_panel.show()
            title_screen_startup(titlescreen, thisgame)

            title_panel.hide()
            mode = 'mapnav'


if __name__ == '__main__':
    curses.wrapper(runit)
