import re

with open("candidate_player.py", "r") as f:
    content = f.read()

# Fix EX checks
content = content.replace('"ex" in self.name.lower()', 'self.name.lower().endswith(" ex")')
content = content.replace('"ex" in evolved', 'evolved.endswith(" ex")')
content = content.replace('"ex" in stage2', 'stage2.endswith(" ex")')
content = content.replace('"mega" in n_lower and "ex" in n_lower', '"mega" in n_lower and n_lower.endswith(" ex")')
content = content.replace('elif "ex" in n_lower:', 'elif n_lower.endswith(" ex"):')
content = content.replace('"ex" in attacker.name.lower()', 'attacker.name.lower().endswith(" ex")')
content = content.replace('"ex" in b.name.lower()', 'b.name.lower().endswith(" ex")')
content = content.replace('"ex" in gs.opp_active.name.lower()', 'gs.opp_active.name.lower().endswith(" ex")')
content = content.replace('"ex" in gs.my_active.name.lower()', 'gs.my_active.name.lower().endswith(" ex")')
content = content.replace('"ex" in target.name.lower()', 'target.name.lower().endswith(" ex")')
content = content.replace('"ex" in n_lower', 'n_lower.endswith(" ex")')
content = content.replace('"ex" in card.name.lower()', 'card.name.lower().endswith(" ex")')

with open("candidate_player.py", "w") as f:
    f.write(content)