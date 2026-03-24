import re

with open("candidate_player.py", "r") as f:
    content = f.read()

search_str = """            # Specific Item Parsing
            if "catcher" in aname_lower or "sabrina" in aname_lower or "boss" in aname_lower:
                action["type"] = "gust"
                action["score"] = ITEM_SCORE"""

replace_str = """            # Specific Item Parsing
            if "catcher" in aname_lower or "sabrina" in aname_lower or "boss" in aname_lower:
                action["type"] = "gust"
                action["score"] = ITEM_SCORE
            elif "cyrus" in aname_lower:
                action["type"] = "cyrus"
                action["score"] = ITEM_SCORE"""

content = content.replace(search_str, replace_str)

search_str3 = """            elif gs.opp_active and gs.opp_active.hp > 80:
                a["score"] += 2000
            else:
                a["score"] = ITEM_SCORE - 10000"""

replace_str3 = """            elif gs.opp_active and gs.opp_active.hp > 80:
                a["score"] += 2000
            else:
                a["score"] = ITEM_SCORE - 10000
        elif a["type"] == "cyrus":
            has_damaged_bench = False
            can_ko_damaged_bench = False
            for b in gs.opp_bench:
                if b.hp < b.max_hp:
                    has_damaged_bench = True
                    if gs.my_active:
                         for idx in range(len(gs.my_active.attacks)):
                             atk = gs.my_active.attacks[idx]
                             if can_use_attack(atk.get("cost", []), gs.my_active.energy):
                                 dmg = calculate_damage(gs.my_active, idx, gs, target_override=b)
                                 if dmg >= b.hp:
                                     can_ko_damaged_bench = True
                                     break

            if can_ko_damaged_bench:
                a["score"] = GUST_LETHAL_SCORE
            elif has_damaged_bench:
                a["score"] = ITEM_SCORE + 2000
            else:
                a["score"] -= 50000"""

content = content.replace(search_str3, replace_str3)

with open("candidate_player.py", "w") as f:
    f.write(content)
