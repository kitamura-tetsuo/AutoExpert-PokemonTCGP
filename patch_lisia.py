import re

with open("candidate_player.py", "r") as f:
    content = f.read()

search_str = """            elif "research" in aname_lower or "professor" in aname_lower or "sightseer" in aname_lower:"""

replace_str = """            elif "lisia" in aname_lower:
                action["type"] = "lisia"
                action["score"] = SEARCH_SCORE
                if risk_of_donk:
                    action["score"] = DONK_SEARCH_SCORE
                else:
                    has_target = True # Assume we have it if we don't know deck contents exactly
                    if not has_target:
                        action["score"] -= 10000

            elif "research" in aname_lower or "professor" in aname_lower or "sightseer" in aname_lower:"""

content = content.replace(search_str, replace_str)

with open("candidate_player.py", "w") as f:
    f.write(content)
