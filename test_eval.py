import re
mode = "ev"
damage = 40
text = "Flip a coin. If heads, this attack does 40 more damage."
num_coins = 1
multiplier = 0.5 if mode == "ev" else 1.0

m_each = re.search(r"(\d+) damage for each heads", text)
if m_each:
    dmg_per_head = int(m_each.group(1))
    damage = num_coins * multiplier * dmg_per_head
else:
    m_more = re.search(r"heads, this attack does (\d+) more damage", text.lower())
    if m_more:
        bonus = int(m_more.group(1))
        damage += (num_coins * multiplier * bonus)
print(damage)
