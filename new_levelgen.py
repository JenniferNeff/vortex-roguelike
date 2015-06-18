#!/usr/bin/python
import random, math, sys
#####################################################################
#
# Level generator for Vortex.
#
#
#
#
#
#
#
#####################################################################

# Map places rooms in random "sectors" of the map.
# Tunnelers generate passages between adjacent rooms.

try:
    depth = sys.argv[1]
except:
    depth = 1

mapwidth = random.randint(3,5)
mapheight = random.randint(3,5)

x_scale = 20
y_scale = 10

mapscheme = [[None for x in range(mapwidth)] for y in range(mapheight)]
mapcanvas = [[" " for x in range(mapwidth * x_scale)] \
             for y in range(mapheight * y_scale)]

flat_sector_list = []

#print mapscheme

room_density = random.uniform(0.4, 1)
list_of_starts = []

def check_sector(place):
    """
    Given a location on the canvas, check which sector it's in.
    """
    check_y = place[0]
    check_x = place[1]
    return (check_y // y_scale, check_x // x_scale)

def fuzzycenter():
    """
    Choose a cell "near the center" of a map sector.
    """
    x_wiggle = random.randint(-x_scale/5, x_scale/5)
    y_wiggle = random.randint(-y_scale/5, y_scale/5)

    y_center = y_scale / 2
    x_center = x_scale / 2

    return (y_center + y_wiggle, x_center + x_wiggle)

def approach(a,b):
    """
    What change, applied to a, will make it approach b?
    """
    if a == b:
        return 0
    elif a > b:
        return -1
    else:
        return 1

def two_D_approach(A,B):
    ways = []
    if approach(A[0],B[0]) != 0:
        ways.append((approach(A[0],B[0]), 0))
    if approach(A[1],B[1]) != 0:
        ways.append((0, (approach(A[1],B[1]))))
    try:
        return random.choice(ways)
    except IndexError:
        return (0,0)

class MapSector(object):

    def __init__(self, y, x):
        # perhaps implement a flag for special kinds of rooms
        self.y_scheme = y
        self.x_scheme = x
        self.real_y_center = y * y_scale + y_scale / 2
        self.real_x_center = x * x_scale + x_scale / 2
        self.contains_room = random.random() <= room_density
        self.blueprint = [[" " for x in range(x_scale)] \
                          for y in range(y_scale)]
        self.room_height = None
        self.room_width = None
        self.floor_cells = []
        self.neighbors = []

        if self.contains_room:
            self.build_room()

        # Passages lead to and from anchors, intersecing walls as fate wills.
        self.anchor = self.find_anchor()
        self.carve_room()

        self.connected = False # set to true when a tunneler reaches it
        if self.y_scheme != 0:
            self.neighbors.append((self.y_scheme - 1, self.x_scheme))
        if self.y_scheme != mapheight - 1:
            self.neighbors.append((self.y_scheme + 1, self.x_scheme))
        if self.x_scheme != 0:
            self.neighbors.append((self.y_scheme, self.x_scheme - 1))
        if self.x_scheme != mapwidth - 1:
            self.neighbors.append((self.y_scheme, self.x_scheme + 1))

    def build_room(self):
        # Note: when color displays are implemented, that will not matter here.
        # This map is read into the game, then turned into entities to be
        # displayed. Color is added when the entities are generated.

        # W---X     W = (A,C)  X = (B,C)
        # |...|     Y = (A,D)  Z = (B,D)
        # Y---Z

        self.A = random.randint(1, math.floor(x_scale * 0.4))
        self.B = random.randint(math.ceil(x_scale * 0.6), x_scale - 1)
        self.C = random.randint(1, math.floor(y_scale * 0.6))
        self.D = random.randint(math.ceil(y_scale * 0.6), y_scale - 1)

        self.B = min(self.B, x_scale - 2)
        self.D = min(self.B, y_scale - 2) # Would like to s/2/1/
        # But it can cause the generator to get stuck in a loop

        self.width = (self.B - self.A) - 1
        self.height = (self.D - self.C) - 1

        # need some way to eliminate rooms with any dimension 0

        # These are for debugging!
        #print "A = %d" % self.A
        #print "B = %d" % self.B
        #print "C = %d" % self.C
        #print "D = %d" % self.D
        #print "Room (%d, %d) has dimensions (%d, %d)." % (self.y_scheme,
        #                                                  self.x_scheme,
        #                                                  self.height,
        #                                                  self.width)

        for i in range(y_scale):
            for j in range(x_scale):
                pen = " "

                if (i == self.C or i == self.D) and \
                   (j == self.A or j == self.B):
                    pen = "X" # corner case is special for the moment
                elif i > self.C and i < self.D:
                    if j == self.A or j == self.B:
                        pen = "|"
                    elif j > self.A and j < self.B:
                        pen = "."
                        self.floor_cells.append((i,j))
                elif i == self.C or i == self.D:
                    if j >= self.A and j <= self.B:
                        pen = "-"
                else:
                    pen = " "

                self.blueprint[i][j] = pen

#        self.anchor = self.find_anchor()
#        self.blueprint[self.anchor[0]][self.anchor[1]] = "o"
#        list_of_starts.append((self.y_scheme * y_scale + self.anchor[0],
#                               self.x_scheme * x_scale + self.anchor[1]))

    def carve_room(self):
        """
        The room transfers its image to the mapcanvas in the proper place.
        """
        for i in range(y_scale):
            for j in range(x_scale):
                mapcanvas[i + (self.y_scheme * y_scale)] \
                         [j + (self.x_scheme * x_scale)] = self.blueprint[i][j]

    def find_anchor(self):
        try:
            anchor = random.choice(self.floor_cells)
            self.blueprint[anchor[0]][anchor[1]] = "o"
        except IndexError:
            anchor = fuzzycenter()
            self.blueprint[anchor[0]][anchor[1]] = "O"

        final_anchor = (self.y_scheme * y_scale + anchor[0],
                        self.x_scheme * x_scale + anchor[1])

        list_of_starts.append(final_anchor)
        return final_anchor

class Room(object):

    def __init__(self, floor_plan):
        # import the floor plan in some interesting way
        # floor plan also includes a defined center and other stats?
        self.plan = floor_plan
        self.population = random.randint(0,3)
        self.treasure = random.randint(0,3)

class Tunneler(object):

    def __init__(self, s, f):
        self.s = s
        self.f = f


        self.start = s.anchor
        self.finish = f.anchor
        #self.direction = two_D_approach(start, finish)
        self.direction = (finish.y_scheme - start.y_scheme, finish.x_scheme - start.x_scheme)
        #print self.direction

        self.position = self.start
        self.exited = False
        self.entered = False
        self.navigate(self.direction)

    def drill(self, direction):
        '''
        THIS IS A DRILL!
        Kick reason to the curb and do the impossible!
        '''
        destination = (self.position[0] + direction[0],
                       self.position[1] + direction[1])
        #if mapcanvas[destination[0]][destination[1]] == "-" or \
        #     mapcanvas[destination[0]][destination[1]] == "|":
        if mapcanvas[destination[0]][destination[1]] in "-|+":
            if (self.exited and \
                check_sector(destination) == check_sector(self.start)) or \
               (self.entered and \
                check_sector(destination) == check_sector(self.finish)):
                return 'blocked'
            else:
                self.position = destination
                mapcanvas[destination[0]][destination[1]] = "+"
                if check_sector(destination) == check_sector(self.start):
                    self.exited = True
                elif check_sector(destination) == check_sector(self.finish):
                    self.entered = True
                return 'door'
        elif mapcanvas[destination[0]][destination[1]] == " ":
            self.position = destination
            mapcanvas[destination[0]][destination[1]] = "#"
            return 'rock'
        elif mapcanvas[destination[0]][destination[1]] == ".":
            self.position = destination
            return 'floor'
        elif mapcanvas[destination[0]][destination[1]] == "X":
            return 'corner'
        else:
            self.position = destination
            return 'done'

    def navigate(self, go):
        #print "Stuck drilling!"
        counter = 0
        this_way = go
        while self.position != self.finish:
#            self.drill(two_D_approach(self.position, self.finish))
            step = self.drill(this_way)
            if step != 'door':
                this_way = two_D_approach(self.position, self.finish)
                #print "Navigating " + str(this_way)
            #print self.position
            counter += 1
            if counter == 30:
                print "Breaking on path from {s} to {f}.".format(s=check_sector(self.start),f=check_sector(self.finish))
                break

for i in range(mapheight):
    for j in range(mapwidth):
        # This is where sectors get their contents.
        mapscheme[i][j] = MapSector(i, j)
        flat_sector_list.append(mapscheme[i][j])

#print mapscheme # testin'

# Set one seed sector as "connected"
unconnected_list = flat_sector_list[:]
connected_list = []
random.shuffle(unconnected_list)
connected_list.append(unconnected_list.pop())
connected_list[0].connected = True
list_of_paths = []
connected_sectors = 1
total_sectors = mapwidth * mapheight

# Then start connecting sectors at random to create a spanning tree.
# The decision of which doors are secret happens when the map is loaded.

while connected_sectors < total_sectors:
    #print "Stuck in path generation!"
    start = random.choice(connected_list)
    start_coordinates = (start.y_scheme, start.x_scheme)
    finish_coordinates = random.choice(start.neighbors)
    finish = mapscheme[finish_coordinates[0]][finish_coordinates[1]]
    if not finish.connected:
        #go = Tunneler(start.anchor, finish.anchor)
        #print "Pathing from {s} to {f}.".format(s=start.anchor, f=finish.anchor)
        go = Tunneler(start, finish)
        connected_list.append(finish)
        unconnected_list.remove(finish)
        finish.connected = True
        connected_sectors += 1
        list_of_paths.append(set((start,finish)))

# At this point, the map is a spanning tree, except where paths collide.
# Sometimes, more loops should be added to keep things interesting.

loop_paths = [0,1,2,3] # tweak numbers to change how "loopy" the graph is
loops_this_level = random.choice(loop_paths)
loops_done = 0
while loops_done < loops_this_level:
    start = random.choice(connected_list)
    start_coordinates = (start.y_scheme, start.x_scheme)
    finish_coordinates = random.choice(start.neighbors)
    finish = mapscheme[finish_coordinates[0]][finish_coordinates[1]]
    if not set((start,finish)) in list_of_paths:
        #print "Pathing loop from {s} to {f}.".format(s=start.anchor, f=finish.anchor)
        go = Tunneler(start, finish)
        list_of_paths.append(set((start,finish)))
        loops_done += 1

# Remove the center and corner markings.

for i in mapcanvas:
    for j in range(len(i)):
        if i[j] == "X":
            i[j] = "-"
        elif i[j] == "o":
            i[j] = "."
        elif i[j] == "O":
            i[j] = "#"

         
# Display the map.

collapsed_canvas = []

for i in mapcanvas:
    collapsed_canvas.append("".join(i))

# Silence this for production
#for i in collapsed_canvas:
#    print i

# Output the map as a .txt.

filename = "vortex_map{d}.txt".format(d=depth)
f = open(filename, 'w')
for i in collapsed_canvas:
    f.write(i)
    f.write("\n")
f.close()

#print list_of_starts

#for i in list_of_starts:
#    print i, check_sector(i)
