import re

def parse_attack(aname):
    m = re.search(r"Attack\((\d+)\)", aname)
    return m

def test():
    cost = ['Lightning', 'Colorless']
    energy_provided = ['Lightning', 'Grass']
    available = list(energy_provided)
    print(available)

test()
