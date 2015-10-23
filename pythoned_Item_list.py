#!/usr/bin/python
import objects
all_the_things = {
"item1": objects.Item(key="item1",name="Unknown entity",symbol="$",color=7,description="You don't know about this, yet",longdesc="You don't know about this yet, longer",def_article="the ",indef_article="a ",xp=0,defense={},attacks={},speed=60,accuracy=100,hidden=False,inventory=[]),
"item2": objects.Item(key="item2",name="Testing Sword",symbol="/",color=7,description="A sword that should be wielded",longdesc="You don't know about this yet, longer",def_article="the ",indef_article="a ",xp=0,defense={},attacks={},speed=60,accuracy=100,hidden=False,inventory=[],equip_slot="melee weapon"),
"testitem": objects.Item(key="testitem",name="Nondescript Item",symbol="$",longdesc="This looks like nothing special, but maybe you can Invoke it."),
"testweapon": objects.Item(key="testweapon",name="Basic Sword",symbol="/",description="A basic steel sword.",longdesc="There's absolutely nothing special about this sword. Probably the last idiot who came in here dropped it when they got killed.",equip_slot="melee weapon")
}
