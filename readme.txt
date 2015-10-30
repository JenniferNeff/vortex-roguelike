Hello Rodney/Sailor/AFGNCAAP:

Welcome to Vortex! You can start this roguelike by running vortex.py on the
command line. It's a work in progress and I'm always adding little features one
at a time, but you can walk around and interact with what's there. If you go
up or down the stairs, you can admire the work of my level generator and the
scrolling display.

The load_and_run.sh script will reload the definitions of items and monsters
before starting the game. If you change the XML files, then you'll need to
start the game with this script once (or duplicate its effects by running the
commands listed therein by hand).

Make sure your command line window is at least 80 x 24.

Here are the commands currently supported:

yku
h l - These are your movement commands. Use Shift-[direction] to run.
bjn

> - Go downstairs
< - Go upstairs

i - Display the [inventory].
I - [Invoke] (that is, use) an item from your inventory.
    (This action is also used to eat food.)
. - Rest for one turn.
t - [take] an item you are standing on.
d - [drop] an item from your inventory.
e - [examine] an item from your inventory.
E - [Examine closely] to see a longer description of inventory items.
    (Not all items have a longer description yet.)
v - [view] an object visible on the map.
V - [View closely] to see a longer description of things on the map.
w - [wield or wear] an item in your inventory.
r - [remove] an item that you are wearing.
Space - Scroll through messages when prompted with "[MORE]"; Exit menus.

s - [save] the game by pickling it. You can load it at the title screen.
q - [quit] the game. You won't be prompted to save!

Attack monsters by walking onto them. More complex ways of attacking with
ranged weapons, etc. will be added later.

Objects and items:

@     That's you!
.     The floor
#     A passage between rooms
$     An item you can Invoke
/     A sword
:     Food
-|    Walls
+     Door
>     Downward staircase
<     Upward staircase
A-Z   Monsters

Planned symbols:
~   liquid on the floor
!   potion
*   gold
]   armor
