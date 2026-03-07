import re
anames = ["Attach(Grass, 1)"]
for aname in anames:
    m = re.search(r"Attach\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
    print(m.groups() if m else None)
