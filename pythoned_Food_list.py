#!/usr/bin/python
import random
import objects
all_the_things = {
"mesa1": objects.Food(key="mesa1",name="Mesa Bar",description="A chewy energy bar.",longdesc="A well-balanced, chewy energy bar, marketed heavily towards adventurers. Its use of whole rolled oats gives it a chunky texture. " + random.choice(("Also contains large amounts of peanut butter.", "Chocolate chunks are visible between the oats.", "Contains a mixture of whole nuts and seeds.", "This one has dried blueberries in it.")))
}
