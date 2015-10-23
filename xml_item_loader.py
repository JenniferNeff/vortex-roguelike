#!/usr/bin/python

# Thanks to the wolf at Stack Overflow:
# http://stackoverflow.com/questions/5530857/parse-xml-file-into-python-object

import sys
import objects
from lxml import etree

f = open("{0}_list.xml".format(sys.argv[1]), "r")

tree = etree.fromstring(f.read())
f.close()

all_the_items = []

for i in tree.findall('item'):
    traits = []
    for a in i.getchildren():
        if a.tag == "key":
            k = a.text
        if a.text != None:
            traits.append("{0}={1}".format(a.tag,a.text))
        if k == "":
            continue
    all_the_items.append("{1}: objects.{2}({0})".format(",".join(traits), k,
                                                        sys.argv[1]))

output = """#!/usr/bin/python
import objects
all_the_things = {{
{0}
}}
""".format(",\n".join(all_the_items))

g = open("pythoned_{0}_list.py".format(sys.argv[1]), "w")
g.write(output)
g.close
