import re

with open("candidate_player.py", "r") as f:
    content = f.read()

search_str = """                if has_houndstone_threat and is_psychic_pokemon and not is_useful:
                    action["score"] = 60000 # Prioritize discarding psychic pokemon for Houndstone"""

replace_str = """                if has_houndstone_threat and is_psychic_pokemon and not is_useful:
                    action["score"] = 85000 # Prioritize discarding psychic pokemon for Houndstone"""

content = content.replace(search_str, replace_str)


search_str2 = """        for d in state.my_discard:
            d_name = d.name.lower()
            if any(x in d_name for x in ["greavard", "houndstone", "yamask", "cofagrigus", "misdreavus", "mismagius", "ralts", "kirlia", "gardevoir", "mewtwo", "gengar", "gastly", "haunter", "comfey", "klefki"]):
                psychic_in_discard += 1"""

replace_str2 = """        for d in state.my_discard:
            d_name = d.name.lower()
            if any(x in d_name for x in ["greavard", "houndstone", "yamask", "cofagrigus", "misdreavus", "mismagius", "ralts", "kirlia", "gardevoir", "mewtwo", "gengar", "gastly", "haunter", "comfey", "klefki", "jynx", "abra", "kadabra", "alakazam"]):
                psychic_in_discard += 1"""
content = content.replace(search_str2, replace_str2)

search_str3 = """        elif "Place" in aname or "PlayPokemon" in aname:
            m = re.search(r"(?:Place|PlayPokemon)\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
            if m:
                card_name_raw = m.group(1)
                pos = int(m.group(2))
                action["type"] = "place"
                action["pos"] = pos
                action["score"] = PLACE_BASIC_SCORE
                action["card_name"] = Card._clean_name(card_name_raw)"""

replace_str3 = """        elif "Place" in aname or "PlayPokemon" in aname:
            m = re.search(r"(?:Place|PlayPokemon)\\((?:Some\\()?(.*?)\\)?, (\\d+)\\)", aname)
            if m:
                card_name_raw = m.group(1)
                pos = int(m.group(2))
                action["type"] = "place"
                action["pos"] = pos
                action["score"] = PLACE_BASIC_SCORE
                clean_name = Card._clean_name(card_name_raw)
                action["card_name"] = clean_name
                if "greavard" in clean_name.lower():
                    action["score"] += 5000"""

content = content.replace(search_str3, replace_str3)


search_str4 = """        elif "Evolve" in aname:
            action["type"] = "evolve"
            action["score"] = EVOLVE_SCORE"""

replace_str4 = """        elif "Evolve" in aname:
            action["type"] = "evolve"
            action["score"] = EVOLVE_SCORE
            m = re.search(r"Evolve\\((?:Some\\()?(.*?)\\)?, (\\d+)\\)", aname)
            if m:
                evo_name = Card._clean_name(m.group(1)).lower()
                if "houndstone" in evo_name:
                    action["score"] += 5000"""

content = content.replace(search_str4, replace_str4)

with open("candidate_player.py", "w") as f:
    f.write(content)
