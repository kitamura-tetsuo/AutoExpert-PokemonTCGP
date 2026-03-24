with open("candidate_player.py", "r") as f:
    content = f.read()

search_str = """            elif "research" in aname_lower or "professor" in aname_lower or "sightseer" in aname_lower:
                action["type"] = "research"
                action["score"] = RESEARCH_SCORE
                if risk_of_donk:
                    action["score"] = DONK_DRAW_SCORE + 1000 # Prefer Research over Copycat"""

replace_str = """            elif "research" in aname_lower or "professor" in aname_lower:
                action["type"] = "research"
                action["score"] = RESEARCH_SCORE
                if risk_of_donk:
                    action["score"] = DONK_DRAW_SCORE + 1000 # Prefer Research over Copycat
            elif "sightseer" in aname_lower:
                action["type"] = "sightseer"
                action["score"] = RESEARCH_SCORE
                if risk_of_donk:
                    action["score"] = DONK_DRAW_SCORE + 1000
                else:
                    needs_evolution = False
                    for p in ([gs.my_active] + gs.my_bench):
                        if p and p.name.lower() in ["greavard", "yamask", "misdreavus"]:
                            needs_evolution = True
                            break
                    if needs_evolution:
                        has_evolution_in_deck = True # Assume we have it
                        if has_evolution_in_deck:
                            action["score"] += 15000
                        else:
                            action["score"] -= 10000
                    else:
                        action["score"] -= 10000"""

content = content.replace(search_str, replace_str)

search_str2 = """        if a["type"] == "research":
            # Smart Research: Discard energy is bad, UNLESS we can accelerate it back (Gardevoir)"""

replace_str2 = """        if a["type"] in ["research", "sightseer"]:
            # Smart Research: Discard energy is bad, UNLESS we can accelerate it back (Gardevoir)"""

content = content.replace(search_str2, replace_str2)

with open("candidate_player.py", "w") as f:
    f.write(content)
