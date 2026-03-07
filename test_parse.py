import re

aname = "AttachEnergy(0, Grass)"
m = re.search(r"AttachEnergy\((\d+), (.*?)\)", aname)
if m:
    print(f"Match 1: '{m.group(1)}', '{m.group(2)}'")

aname2 = "Attach(Some(Grass), 0)"
m2 = re.search(r"Attach\((?:Some\()?(.*?)\)?, (\d+)\)", aname2)
if m2:
    print(f"Match 2: '{m2.group(1)}', '{m2.group(2)}'")

aname3 = "Attach(Grass, 0)"
m3 = re.search(r"Attach\((?:Some\()?(.*?)\)?, (\d+)\)", aname3)
if m3:
    print(f"Match 3: '{m3.group(1)}', '{m3.group(2)}'")
