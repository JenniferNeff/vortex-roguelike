#!/usr/bin/python

import curses # Will this work??

import objects
import sys

# Getch input by Danny Yoo
# code.activestate.com/recipes/134892
# (Download and use the getch module maybe later)

class _Getch:
    """Gets a single character from standard input.  Does not echo to the
screen."""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()


getch = _Getch()

# standard screen size is 80 x 24.
scr_x = 80
scr_y = 24

class Floor(object):

    def __init__(self, name="Unknown Location", depth=0):
        self.name = name
        self.depth = depth

        self.level1 = []
        self.level2 = {} # (i,j) : object
        self.level3 = {}

    def load_map(self, mapfile):
        getmap = open(mapfile, 'r')
        for line in getmap:
            newline = []
            for char in range(scr_x):
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
            self.level1.append(newline)

    def display(self):
        for j in range(scr_y):
            try:
                for i in range(scr_x):
                    if (i,j) in self.level3.keys():
                        sys.stdout.write(self.level3[(i,j)].symbol)
                    elif (i,j) in self.level2.keys():
                        sys.stdout.write(self.level2[(i,j)].symbol)
                    else:
                        sys.stdout.write(self.level1[j][i].symbol)
                sys.stdout.write("\n")
            except IndexError:
                sys.stdout.write("\n")

test = Floor(name="Testing Map")
test.load_map("testmap")
test.display()
