#!/usr/bin/python
import random
import objects
all_the_things = {
"mesa1": objects.Food(key="mesa1",name="Mesa Bar",description="A chewy energy bar.",longdesc="A well-balanced, chewy energy bar, marketed heavily towards adventurers. Its use of whole rolled oats gives it a chunky texture. " + random.choice(("Also contains large amounts of peanut butter.", "Chocolate chunks are visible between the oats.", "Contains a mixture of whole nuts and seeds.", "This one has dried blueberries in it.", "It's a dark chocoloate brown, possibly trying a little too hard to be a brownie.")),calories=300,caffeine=0,healthy=True),
"mesa2": objects.Food(key="mesa2",name="Black Mesa Bar",description="A chewy energy bar with caffeine in it.",longdesc="A well-balanced, chewy energy bar, marketed heavily towards adventurers. It's just like a normal Mesa Bar, but this flavor is caffeinated. " + random.choice(("You think you can see bits of espresso bean in it.", "It's chocolate, and white mint icing is drizzled over the top.")),calories=300,caffeine=100,healthy=True),
"tea1": objects.Food(key="tea1",name="cup of green tea",description="A hot covered cup of green tea.",longdesc="This hot cup of green tea steams slightly when the lid is opened. It smells a little bitter.",calories=0,caffeine=100,healthy=True),
"tea2": objects.Food(key="tea2",name="cup of black tea",description="A hot covered cup of black tea.",longdesc="This hot cup of black tea steams slightly when the lid is opened. A cursory taste confirms it has a bit of sugar in it.",calories=0,caffeine=100,healthy=True),
"tea3": objects.Food(key="tea3",name="bottle of iced tea",description="A cold bottle of iced tea.",longdesc="The label on this bottle of tea proclaims its environmental friendliness and lack of any artifical ingredients. The ingredients list reveals that it contains a rather ridiculous amount of sugar.",calories=20,caffeine=100,healthy=False),
"coffee1": objects.Food(key="coffee1",name="cup of black coffee",description="A hot covered cup of black coffee.",longdesc="This hot cup of black coffee steams slightly when the lid is opened. Its aroma permeates the air.",calories=0,caffeine=150,healthy=False),
"coffee2": objects.Food(key="coffee2",name="Latteccino",description="A hot covered cup of coffee with milk and syrup.",longdesc="A hot cup of coffee, mixed with milk and sweeteners and covered with a layer of whipped cream. It smells faintly of " + random.choice(("vanilla.", "hazelnuts.", "caramel.", "pumpkin pie spices.", "chocolate.")),calories=200,caffeine=150,healthy=False),
"coffee2": objects.Food(key="coffee2",name="Iced Latteccino",description="A cold covered cup of coffee with milk and syrup.",longdesc="A cold cup of coffee, mixed with milk and sweeteners and covered with a layer of whipped cream. It smells faintly of " + random.choice(("vanilla.", "hazelnuts.", "caramel.", "pumpkin pie spices.", "chocolate.")),indef_article="an ",calories=200,caffeine=150,healthy=False),
"pizza1": objects.Food(key="pizza1",name="slice of cold pizza",description="A slice of cold pizza.",longdesc="A slice of pizza from last night, or perhaps earlier, topped with " + random.choice(("pepperoni.", "a variety of vegetables.", "chicken and barbeque sauce.", "ham and pineapple.", "curried chicken and vegetables.")),calories=260,caffeine=0,healthy=False),
"candy1": objects.Food(key="candy1",name="chocolate covered espresso beans",description="A handful of chocolate-covered coffee beans.",longdesc="A strong scent of coffee emanates from these chocolate-covered candies. Some of them are in stuck-together pairs.",indef_article="some ",calories=200,caffeine=250,healthy=False),
"sandwich1": objects.Food(key="sandwich1",name="sub sandwich",description="A footlong sandwich on a roll.",longdesc="This sandwich is conveniently wrapped in waxed paper, and the inside is layered with a few kinds of thinly-sliced meat and vegetables.",calories=700,caffeine=0,healthy=True),
"mix1": objects.Food(key="mix1",name="bottle of soylent",description="A bottle of thick protein slush.",longdesc="It's not green, but it is sort of baffling. This thick white liquid is about as bland as plain tofu, but it's pretty filling.",calories=666,caffeine=0,healthy=True),
"water1": objects.Food(key="water1",name="bottle of water",description="A bottle of plain water.",longdesc="The label has a picture of some Hawaiian waterfall on it, but it was probably bottled from a tap in New York. You could drink this, but it's not caffeinated or anything. It's just cold water.",calories=0,caffeine=0,healthy=True),
"water2": objects.Food(key="water2",name="cup of hot water",description="A cup of plain hot water.",longdesc="It's a covered cup of plain hot water, nearly boiling. You could drink it, carefully, but it wouldn't taste like much of anything.",calories=0,caffeine=0,healthy=True)
}
