
import re
import random
import sys
import logging

# Setup logging
logging.basicConfig(filename='player.log', level=logging.INFO, filemode='w', format='%(asctime)s - %(message)s')

# --- Card Database (Expanded & Normalized) ---
# All keys lowercase
CARD_DB = {
    # Lightning
    "pikachu ex": {"hp": 120, "energy_type": "lightning", "retreat": 1, "attacks": [{"name": "Circle Circuit", "cost": ["Lightning", "Lightning"], "dmg": 30, "bench_scale": True}]},
    "zapdos ex": {"hp": 130, "energy_type": "lightning", "retreat": 1, "attacks": [{"name": "Peck", "cost": ["Lightning"], "dmg": 20}, {"name": "Thundering Hurricane", "cost": ["Lightning", "Lightning", "Lightning"], "dmg": 50, "coin_flips": 4}]},
    "pikachu": {"hp": 60, "energy_type": "lightning", "retreat": 1, "attacks": [{"name": "Gnaw", "cost": ["Lightning"], "dmg": 20}]},
    "raichu": {"hp": 100, "energy_type": "lightning", "retreat": 1, "attacks": [{"name": "Thunderbolt", "cost": ["Lightning", "Lightning", "Colorless"], "dmg": 140, "discard_all": True}]},
    "magneton": {"hp": 80, "energy_type": "lightning", "retreat": 1, "attacks": [{"name": "Volt Charge", "cost": ["Lightning", "Colorless"], "dmg": 40}]},
    "electrode": {"hp": 90, "energy_type": "lightning", "retreat": 1, "attacks": [{"name": "Electro Ball", "cost": ["Lightning", "Colorless"], "dmg": 70}]},
    "blitzle": {"hp": 60, "energy_type": "lightning", "retreat": 1, "attacks": [{"name": "Quick Attack", "cost": ["Lightning"], "dmg": 10, "coin_flip_plus": 10}]},
    "zebstrika": {"hp": 100, "energy_type": "lightning", "retreat": 1, "attacks": [{"name": "Thunder", "cost": ["Lightning", "Colorless"], "dmg": 30}]},
    "pincurchin": {"hp": 70, "energy_type": "lightning", "retreat": 2, "attacks": [{"name": "Peck", "cost": ["Lightning"], "dmg": 10}]},
    "electabuzz": {"hp": 70, "energy_type": "lightning", "retreat": 2, "attacks": [{"name": "Thunder Punch", "cost": ["Lightning", "Colorless"], "dmg": 30}]},

    # Psychic
    "mewtwo ex": {"hp": 150, "energy_type": "psychic", "retreat": 2, "attacks": [{"name": "Psychic Sphere", "cost": ["Psychic", "Colorless"], "dmg": 50}, {"name": "Psydrive", "cost": ["Psychic", "Psychic", "Colorless", "Colorless"], "dmg": 150, "discard": 2}]},
    "gardevoir": {"hp": 110, "energy_type": "psychic", "retreat": 2, "attacks": [{"name": "Psyshot", "cost": ["Psychic", "Psychic", "Colorless"], "dmg": 60}], "ability": "Psy Shadow"},
    "kirlia": {"hp": 80, "energy_type": "psychic", "retreat": 1, "attacks": [{"name": "Smack", "cost": ["Psychic", "Colorless"], "dmg": 30}]},
    "ralts": {"hp": 60, "energy_type": "psychic", "retreat": 1, "attacks": [{"name": "Smack", "cost": ["Psychic"], "dmg": 10}]},
    "gengar ex": {"hp": 170, "energy_type": "psychic", "retreat": 2, "attacks": [{"name": "Spooky Shot", "cost": ["Psychic", "Psychic", "Psychic"], "dmg": 100}]},
    "gastly": {"hp": 60, "energy_type": "psychic", "retreat": 1, "attacks": [{"name": "Gas", "cost": ["Psychic"], "dmg": 10}]},
    "haunter": {"hp": 80, "energy_type": "psychic", "retreat": 1, "attacks": [{"name": "Spooky Shot", "cost": ["Psychic", "Colorless"], "dmg": 30}]},
    "gengar": {"hp": 130, "energy_type": "psychic", "retreat": 1, "attacks": [{"name": "Poltergeist", "cost": ["Psychic", "Psychic"], "dmg": 50}]},
    "abra": {"hp": 60, "energy_type": "psychic", "retreat": 1, "attacks": [{"name": "Psyshot", "cost": ["Psychic"], "dmg": 10}]},
    "kadabra": {"hp": 80, "energy_type": "psychic", "retreat": 1, "attacks": [{"name": "Psyshot", "cost": ["Psychic", "Colorless"], "dmg": 30}]},
    "alakazam": {"hp": 130, "energy_type": "psychic", "retreat": 2, "attacks": [{"name": "Psychic", "cost": ["Psychic", "Psychic", "Colorless"], "dmg": 60, "plus_opp_energy": 30}]},
    "jynx": {"hp": 70, "energy_type": "psychic", "retreat": 2, "attacks": [{"name": "Psychic", "cost": ["Psychic", "Colorless"], "dmg": 30}]},
    "mr. mime": {"hp": 80, "energy_type": "psychic", "retreat": 2, "attacks": [{"name": "Psychic", "cost": ["Psychic", "Colorless"], "dmg": 30}]},
    "mew ex": {"hp": 130, "energy_type": "psychic", "retreat": 0, "attacks": [{"name": "Genome Hacking", "cost": ["Colorless", "Colorless", "Colorless"], "dmg": 0}]},

    # Water
    "starmie ex": {"hp": 130, "energy_type": "water", "retreat": 0, "attacks": [{"name": "Hydro Splash", "cost": ["Water", "Water"], "dmg": 90}]},
    "staryu": {"hp": 50, "energy_type": "water", "retreat": 1, "attacks": [{"name": "Water Gun", "cost": ["Water"], "dmg": 20}]},
    "articuno ex": {"hp": 140, "energy_type": "water", "retreat": 2, "attacks": [{"name": "Ice Wing", "cost": ["Water", "Colorless"], "dmg": 40}, {"name": "Blizzard", "cost": ["Water", "Water", "Water"], "dmg": 80, "bench_dmg": 10}]},
    "articuno": {"hp": 100, "energy_type": "water", "retreat": 1, "attacks": [{"name": "Gust", "cost": ["Water"], "dmg": 20}, {"name": "Blizzard", "cost": ["Water", "Water", "Water"], "dmg": 80, "coin_flip_paralyze": True}]},
    "blastoise ex": {"hp": 180, "energy_type": "water", "retreat": 3, "attacks": [{"name": "Surf", "cost": ["Water", "Colorless"], "dmg": 40}, {"name": "Hydro Bazooka", "cost": ["Water", "Water", "Colorless"], "dmg": 100, "extra_energy_dmg": 60}]},
    "squirtle": {"hp": 60, "energy_type": "water", "retreat": 1, "attacks": [{"name": "Bubble", "cost": ["Water"], "dmg": 10}]},
    "wartortle": {"hp": 90, "energy_type": "water", "retreat": 2, "attacks": [{"name": "Water Gun", "cost": ["Water", "Colorless"], "dmg": 30}]},
    "greninja": {"hp": 120, "energy_type": "water", "retreat": 1, "attacks": [{"name": "Mist Slash", "cost": ["Water", "Colorless"], "dmg": 60}], "ability": "Water Shuriken"},
    "frogadier": {"hp": 80, "energy_type": "water", "retreat": 1, "attacks": [{"name": "Water Pulse", "cost": ["Water"], "dmg": 20}]},
    "froakie": {"hp": 60, "energy_type": "water", "retreat": 1, "attacks": [{"name": "Bubble", "cost": ["Water"], "dmg": 10}]},
    "psyduck": {"hp": 70, "energy_type": "water", "retreat": 1, "attacks": [{"name": "Headache", "cost": ["Water"], "dmg": 20, "disable_trainers": True}]},
    "golduck": {"hp": 100, "energy_type": "water", "retreat": 1, "attacks": [{"name": "Scratch", "cost": ["Water", "Colorless"], "dmg": 40}]},
    "poliwag": {"hp": 60, "energy_type": "water", "retreat": 1, "attacks": [{"name": "Bubble", "cost": ["Water"], "dmg": 10}]},
    "suicune ex": {"hp": 140, "energy_type": "water", "retreat": 2, "attacks": [{"name": "Aurora Beam", "cost": ["Water", "Colorless", "Colorless"], "dmg": 100}]},

    # Fire
    "charizard ex": {"hp": 180, "energy_type": "fire", "retreat": 2, "attacks": [{"name": "Slash", "cost": ["Fire", "Colorless"], "dmg": 60}, {"name": "Crimson Storm", "cost": ["Fire", "Fire", "Colorless", "Colorless"], "dmg": 200, "discard": 2}]},
    "charmander": {"hp": 60, "energy_type": "fire", "retreat": 1, "attacks": [{"name": "Scratch", "cost": ["Fire"], "dmg": 10}]},
    "charmeleon": {"hp": 90, "energy_type": "fire", "retreat": 2, "attacks": [{"name": "Flame Tail", "cost": ["Fire", "Colorless"], "dmg": 30}]},
    "moltres ex": {"hp": 140, "energy_type": "fire", "retreat": 2, "attacks": [{"name": "Inferno Dance", "cost": ["Fire"], "dmg": 0, "effect": "accelerate"}, {"name": "Heat Blast", "cost": ["Fire", "Colorless", "Colorless"], "dmg": 70}]},
    "moltres": {"hp": 100, "energy_type": "fire", "retreat": 1, "attacks": [{"name": "Assisted Heater", "cost": ["Fire"], "dmg": 20}]},
    "arcanine ex": {"hp": 190, "energy_type": "fire", "retreat": 3, "attacks": [{"name": "Flamethrower", "cost": ["Fire", "Fire", "Colorless"], "dmg": 120}]},
    "growlithe": {"hp": 70, "energy_type": "fire", "retreat": 2, "attacks": [{"name": "Roar", "cost": ["Colorless"], "dmg": 0}]},
    "ponyta": {"hp": 60, "energy_type": "fire", "retreat": 1, "attacks": [{"name": "Ember", "cost": ["Fire"], "dmg": 20}]},
    "rapidash": {"hp": 90, "energy_type": "fire", "retreat": 0, "attacks": [{"name": "Fire Spin", "cost": ["Fire", "Colorless"], "dmg": 40}]},
    "vulpix": {"hp": 60, "energy_type": "fire", "retreat": 1, "attacks": [{"name": "Ember", "cost": ["Fire"], "dmg": 20}]},
    "ninetales": {"hp": 90, "energy_type": "fire", "retreat": 1, "attacks": [{"name": "Flamethrower", "cost": ["Fire", "Colorless", "Colorless"], "dmg": 90, "discard": 1}]},
    "magmar": {"hp": 80, "energy_type": "fire", "retreat": 2, "attacks": [{"name": "Fire Punch", "cost": ["Fire", "Colorless"], "dmg": 30}]},

    # Grass
    "venusaur ex": {"hp": 190, "energy_type": "grass", "retreat": 3, "attacks": [{"name": "Razor Leaf", "cost": ["Grass", "Colorless", "Colorless"], "dmg": 60}, {"name": "Giant Bloom", "cost": ["Grass", "Grass", "Colorless", "Colorless"], "dmg": 100, "heal": 30}]},
    "bulbasaur": {"hp": 70, "energy_type": "grass", "retreat": 2, "attacks": [{"name": "Vine Whip", "cost": ["Grass", "Colorless"], "dmg": 30}]},
    "ivysaur": {"hp": 100, "energy_type": "grass", "retreat": 3, "attacks": [{"name": "Vine Whip", "cost": ["Grass", "Colorless", "Colorless"], "dmg": 50}]},
    "exeggutor ex": {"hp": 160, "energy_type": "grass", "retreat": 3, "attacks": [{"name": "Tropical Swing", "cost": ["Grass", "Colorless"], "dmg": 40, "coin_flip_plus": 40}]},
    "exeggcute": {"hp": 50, "energy_type": "grass", "retreat": 1, "attacks": [{"name": "Hypnosis", "cost": ["Grass"], "dmg": 10}]},
    "caterpie": {"hp": 50, "energy_type": "grass", "retreat": 1, "attacks": [{"name": "Bug Bite", "cost": ["Grass"], "dmg": 10}]},
    "metapod": {"hp": 70, "energy_type": "grass", "retreat": 2, "attacks": [{"name": "Harden", "cost": ["Grass"], "dmg": 0}]},
    "butterfree": {"hp": 100, "energy_type": "grass", "retreat": 1, "attacks": [{"name": "Gust", "cost": ["Grass", "Colorless"], "dmg": 40}]},
    "weedle": {"hp": 50, "energy_type": "grass", "retreat": 1, "attacks": [{"name": "Poison Sting", "cost": ["Grass"], "dmg": 10}]},
    "kakuna": {"hp": 70, "energy_type": "grass", "retreat": 2, "attacks": [{"name": "Stiffen", "cost": ["Grass"], "dmg": 0}]},
    "beedrill": {"hp": 100, "energy_type": "grass", "retreat": 1, "attacks": [{"name": "Pin Missile", "cost": ["Grass", "Colorless"], "dmg": 30, "coin_flips": 3}]},
    "scyther": {"hp": 70, "energy_type": "grass", "retreat": 0, "attacks": [{"name": "Slash", "cost": ["Colorless"], "dmg": 10}]},
    "pinsir": {"hp": 80, "energy_type": "grass", "retreat": 2, "attacks": [{"name": "Vice Grip", "cost": ["Grass", "Colorless"], "dmg": 40}]},

    # Fighting
    "machamp ex": {"hp": 180, "energy_type": "fighting", "retreat": 3, "attacks": [{"name": "Mega Punch", "cost": ["Fighting", "Fighting", "Fighting"], "dmg": 120}]},
    "machop": {"hp": 70, "energy_type": "fighting", "retreat": 2, "attacks": [{"name": "Low Kick", "cost": ["Fighting"], "dmg": 20}]},
    "machoke": {"hp": 100, "energy_type": "fighting", "retreat": 3, "attacks": [{"name": "Karate Chop", "cost": ["Fighting", "Fighting"], "dmg": 40}]},
    "marowak ex": {"hp": 140, "energy_type": "fighting", "retreat": 1, "attacks": [{"name": "Bonemerang", "cost": ["Fighting", "Fighting"], "dmg": 80, "coin_flips": 2}]},
    "cubone": {"hp": 60, "energy_type": "fighting", "retreat": 1, "attacks": [{"name": "Bone Club", "cost": ["Fighting"], "dmg": 20}]},
    "hitmonlee": {"hp": 80, "energy_type": "fighting", "retreat": 1, "attacks": [{"name": "Rolling Kick", "cost": ["Fighting"], "dmg": 30}]},
    "hitmonchan": {"hp": 90, "energy_type": "fighting", "retreat": 2, "attacks": [{"name": "Jab", "cost": ["Fighting"], "dmg": 20}]},
    "kabutops": {"hp": 140, "energy_type": "fighting", "retreat": 1, "attacks": [{"name": "Slash", "cost": ["Fighting"], "dmg": 50}]},
    "kabuto": {"hp": 80, "energy_type": "fighting", "retreat": 1, "attacks": [{"name": "Scratch", "cost": ["Fighting"], "dmg": 20}]},
    "geodude": {"hp": 70, "energy_type": "fighting", "retreat": 2, "attacks": [{"name": "Rock Throw", "cost": ["Fighting"], "dmg": 20}]},
    "graveler": {"hp": 100, "energy_type": "fighting", "retreat": 3, "attacks": [{"name": "Rock Slide", "cost": ["Fighting", "Fighting"], "dmg": 40}]},
    "golem": {"hp": 160, "energy_type": "fighting", "retreat": 4, "attacks": [{"name": "Rock Blast", "cost": ["Fighting", "Fighting", "Fighting", "Colorless"], "dmg": 100}]},
    "onix": {"hp": 110, "energy_type": "fighting", "retreat": 4, "attacks": [{"name": "Bind", "cost": ["Fighting", "Colorless"], "dmg": 30}]},
    "rhyhorn": {"hp": 80, "energy_type": "fighting", "retreat": 3, "attacks": [{"name": "Horn Attack", "cost": ["Fighting", "Colorless"], "dmg": 30}]},
    "rhydon": {"hp": 110, "energy_type": "fighting", "retreat": 4, "attacks": [{"name": "Horn Drill", "cost": ["Fighting", "Fighting", "Colorless"], "dmg": 60}]},

    # Darkness
    "weavile": {"hp": 90, "energy_type": "darkness", "retreat": 1, "attacks": [{"name": "Slash", "cost": ["Darkness"], "dmg": 30}]},
    "sneasel": {"hp": 60, "energy_type": "darkness", "retreat": 1, "attacks": [{"name": "Scratch", "cost": ["Darkness"], "dmg": 10}]},
    "muk": {"hp": 120, "energy_type": "darkness", "retreat": 3, "attacks": [{"name": "Sludge Bomb", "cost": ["Darkness", "Colorless", "Colorless"], "dmg": 70}]},
    "grimer": {"hp": 70, "energy_type": "darkness", "retreat": 2, "attacks": [{"name": "Pound", "cost": ["Darkness"], "dmg": 20}]},
    "koffing": {"hp": 60, "energy_type": "darkness", "retreat": 1, "attacks": [{"name": "Smog", "cost": ["Darkness"], "dmg": 10}]},
    "weezing": {"hp": 100, "energy_type": "darkness", "retreat": 2, "attacks": [{"name": "Sludge", "cost": ["Darkness", "Colorless"], "dmg": 30}]},
    "arbok": {"hp": 100, "energy_type": "darkness", "retreat": 2, "attacks": [{"name": "Corner", "cost": ["Darkness", "Colorless"], "dmg": 60}]},
    "ekans": {"hp": 60, "energy_type": "darkness", "retreat": 1, "attacks": [{"name": "Spit Poison", "cost": ["Darkness"], "dmg": 10}]},
    "nidoran": {"hp": 60, "energy_type": "darkness", "retreat": 1, "attacks": [{"name": "Horn Hazard", "cost": ["Darkness"], "dmg": 20}]},
    "nidorina": {"hp": 90, "energy_type": "darkness", "retreat": 2, "attacks": [{"name": "Bite", "cost": ["Darkness", "Colorless"], "dmg": 30}]},
    "nidoqueen": {"hp": 150, "energy_type": "darkness", "retreat": 3, "attacks": [{"name": "Queen Press", "cost": ["Darkness", "Colorless", "Colorless"], "dmg": 90}]},
    "nidorino": {"hp": 90, "energy_type": "darkness", "retreat": 2, "attacks": [{"name": "Horn Drill", "cost": ["Darkness", "Colorless"], "dmg": 30}]},
    "nidoking": {"hp": 150, "energy_type": "darkness", "retreat": 3, "attacks": [{"name": "Venomous Horn", "cost": ["Darkness", "Colorless", "Colorless"], "dmg": 90}]},
    "zubat": {"hp": 50, "energy_type": "darkness", "retreat": 1, "attacks": [{"name": "Supersonic", "cost": ["Darkness"], "dmg": 10}]},
    "golbat": {"hp": 80, "energy_type": "darkness", "retreat": 1, "attacks": [{"name": "Leech Life", "cost": ["Darkness"], "dmg": 20}]},

    # Metal
    "melmetal": {"hp": 130, "energy_type": "metal", "retreat": 3, "attacks": [{"name": "Heavy Impact", "cost": ["Metal", "Colorless", "Colorless"], "dmg": 80}]},
    "meltan": {"hp": 60, "energy_type": "metal", "retreat": 1, "attacks": [{"name": "Headbutt", "cost": ["Metal"], "dmg": 20}]},
    "mawile": {"hp": 70, "energy_type": "metal", "retreat": 1, "attacks": [{"name": "Crunch", "cost": ["Metal", "Colorless"], "dmg": 30}]},

    # Dragon
    "dragonite": {"hp": 160, "energy_type": "dragon", "retreat": 3, "attacks": [{"name": "Draco Meteor", "cost": ["Water", "Lightning", "Colorless", "Colorless"], "dmg": 50, "random_target": 4}]},
    "dragonair": {"hp": 100, "energy_type": "dragon", "retreat": 2, "attacks": [{"name": "Twister", "cost": ["Water", "Lightning"], "dmg": 40}]},
    "dratini": {"hp": 60, "energy_type": "dragon", "retreat": 1, "attacks": [{"name": "Wrap", "cost": ["Water"], "dmg": 10}]},

    # Colorless
    "wigglytuff ex": {"hp": 140, "energy_type": "colorless", "retreat": 2, "attacks": [{"name": "Sleepy Song", "cost": ["Colorless", "Colorless", "Colorless"], "dmg": 80, "status": "Sleep"}]},
    "jigglypuff": {"hp": 60, "energy_type": "colorless", "retreat": 1, "attacks": [{"name": "Pound", "cost": ["Colorless"], "dmg": 20}]},
    "kangaskhan": {"hp": 100, "retreat": 3, "energy_type": "colorless", "attacks": [{"name": "Comet Punch", "cost": ["Colorless"], "dmg": 20, "coin_flip_plus": 20}]},
    "farfetch'd": {"hp": 60, "retreat": 1, "energy_type": "colorless", "attacks": [{"name": "Leek Slap", "cost": ["Colorless"], "dmg": 30}]},
    "tauros": {"hp": 100, "retreat": 2, "energy_type": "colorless", "attacks": [{"name": "Horn Attack", "cost": ["Colorless", "Colorless"], "dmg": 30}]},
    "snorlax": {"hp": 150, "retreat": 4, "energy_type": "colorless", "attacks": [{"name": "Body Slam", "cost": ["Colorless", "Colorless", "Colorless", "Colorless"], "dmg": 80}]},
    "eevee": {"hp": 50, "retreat": 1, "energy_type": "colorless", "attacks": [{"name": "Tackle", "cost": ["Colorless"], "dmg": 10}]},
    "pidgey": {"hp": 50, "retreat": 1, "energy_type": "colorless", "attacks": [{"name": "Gust", "cost": ["Colorless"], "dmg": 10}]},
    "pidgeotto": {"hp": 70, "retreat": 1, "energy_type": "colorless", "attacks": [{"name": "Wing Attack", "cost": ["Colorless", "Colorless"], "dmg": 30}]},
    "pidgeot": {"hp": 130, "retreat": 0, "energy_type": "colorless", "attacks": [{"name": "Hurricane", "cost": ["Colorless", "Colorless", "Colorless"], "dmg": 70}]},
    "rattata": {"hp": 40, "retreat": 1, "energy_type": "colorless", "attacks": [{"name": "Bite", "cost": ["Colorless"], "dmg": 20}]},
    "raticate": {"hp": 80, "retreat": 0, "energy_type": "colorless", "attacks": [{"name": "Hyper Fang", "cost": ["Colorless"], "dmg": 50}]},
    "spearow": {"hp": 50, "retreat": 1, "energy_type": "colorless", "attacks": [{"name": "Peck", "cost": ["Colorless"], "dmg": 10}]},
    "fearow": {"hp": 80, "retreat": 0, "energy_type": "colorless", "attacks": [{"name": "Drill Peck", "cost": ["Colorless", "Colorless"], "dmg": 40}]},
    "meowth": {"hp": 60, "retreat": 1, "energy_type": "colorless", "attacks": [{"name": "Pay Day", "cost": ["Colorless"], "dmg": 10}]},
    "persian": {"hp": 80, "retreat": 1, "energy_type": "colorless", "attacks": [{"name": "Slash", "cost": ["Colorless", "Colorless"], "dmg": 30}]},
    "lickitung": {"hp": 90, "retreat": 3, "energy_type": "colorless", "attacks": [{"name": "Tongue Slap", "cost": ["Colorless", "Colorless"], "dmg": 30}]},
    "chansey": {"hp": 120, "retreat": 2, "energy_type": "colorless", "attacks": [{"name": "Double-Edge", "cost": ["Colorless", "Colorless", "Colorless"], "dmg": 60}]},
    "ditto": {"hp": 60, "retreat": 1, "energy_type": "colorless", "attacks": [{"name": "Transform", "cost": ["Colorless"], "dmg": 0}]},
    "porygon": {"hp": 60, "retreat": 1, "energy_type": "colorless", "attacks": [{"name": "Sharpen", "cost": ["Colorless"], "dmg": 20}]},
    "aerodactyl": {"hp": 100, "retreat": 1, "energy_type": "colorless", "attacks": [{"name": "Wing Attack", "cost": ["Colorless", "Colorless"], "dmg": 30}]},
}

def play(state, game):
    """
    Advanced Pokemon TCG Pocket Player (v8 - Max Lethal & Improvements)
    """
    legal_actions = game.legal_actions()
    if not legal_actions:
        return 0

    try:
        # --- 1. Helper Functions ---
        def get_card_name(card_obj):
            if not card_obj: return None
            return getattr(card_obj, "name", "Unknown")

        def get_card_hp(card_obj):
            if not card_obj: return 0
            return getattr(card_obj, "remaining_hp", 0)

        def get_card_max_hp(card_obj):
            if not card_obj: return 0
            return getattr(card_obj, "total_hp", 0)

        def get_card_energy(card_obj):
            if not card_obj: return []
            return [str(e) for e in getattr(card_obj, "attached_energy", [])]

        def get_energy_type(card_name):
            if not card_name: return "colorless"
            n = card_name.lower()
            if n in CARD_DB:
                return CARD_DB[n].get("energy_type", "colorless").lower()

            # Heuristic fallback
            if any(x in n for x in ["pikachu", "zapdos", "raichu", "magneton", "electrode", "blitzle", "electabuzz"]): return "lightning"
            if any(x in n for x in ["mewtwo", "ralts", "kirlia", "gardevoir", "gengar", "abra", "gastly", "mew"]): return "psychic"
            if any(x in n for x in ["starmie", "articuno", "blastoise", "greninja", "squirtle", "poliwag", "suicune"]): return "water"
            if any(x in n for x in ["charizard", "moltres", "arcanine", "charmander", "vulpix", "ponyta", "magmar"]): return "fire"
            if any(x in n for x in ["venusaur", "exeggutor", "bulbasaur", "caterpie", "weedle", "scyther", "pinsir"]): return "grass"
            if any(x in n for x in ["machamp", "marowak", "golem", "geodude", "onix", "rhyhorn", "hitmon", "kabuto"]): return "fighting"
            if any(x in n for x in ["dragonite", "dratini"]): return "dragon"
            if any(x in n for x in ["melmetal", "meltan", "mawile"]): return "metal"
            if any(x in n for x in ["weavile", "muk", "koffing", "ekans", "nidoran", "zubat"]): return "darkness"
            return "colorless"

        def calculate_damage(attacker_card, attack_idx, my_bench_len, opp_active_hp):
            name = get_card_name(attacker_card)
            if not name: return 0
            n_lower = name.lower()

            # 1. Check DB first
            if n_lower in CARD_DB and "attacks" in CARD_DB[n_lower]:
                attacks_db = CARD_DB[n_lower]["attacks"]
                if attack_idx < len(attacks_db):
                    atk = attacks_db[attack_idx]
                    base = atk.get("dmg", 0)
                    if atk.get("bench_scale"): return 30 * my_bench_len
                    if "coin_flips" in atk: return base * 0.5 * atk["coin_flips"]
                    if "coin_flip_plus" in atk: return base + (atk["coin_flip_plus"] * 0.5)
                    if "extra_energy_dmg" in atk:
                        energies = get_card_energy(attacker_card)
                        cost_len = len(atk.get("cost", []))
                        if len(energies) >= cost_len + 1: return base + atk["extra_energy_dmg"]
                        return base
                    if base > 0: return base

            # 2. Check Object Attributes
            attacks_obj = getattr(attacker_card, "attacks", [])
            if attack_idx < len(attacks_obj):
                atk_obj = attacks_obj[attack_idx]
                fixed = getattr(atk_obj, "fixed_damage", 0)
                if fixed > 0: return fixed
                dmg = getattr(atk_obj, "damage", 0)
                if dmg > 0: return dmg
            return 0

        def get_best_attack(card_obj):
            name = get_card_name(card_obj)
            if not name: return (0, 0, -1)
            n_lower = name.lower()
            best_dmg = 0; best_cost = 0; best_idx = -1

            if n_lower in CARD_DB and "attacks" in CARD_DB[n_lower]:
                attacks = CARD_DB[n_lower]["attacks"]
                for i, atk in enumerate(attacks):
                    dmg = atk.get("dmg", 0)
                    cost = len(atk.get("cost", []))
                    if atk.get("bench_scale"): dmg = 90
                    if "coin_flips" in atk: dmg = dmg * 0.5 * atk["coin_flips"]
                    if "extra_energy_dmg" in atk: dmg += atk["extra_energy_dmg"]
                    if dmg > best_dmg: best_dmg = dmg; best_cost = cost; best_idx = i
            else:
                 attacks_obj = getattr(card_obj, "attacks", [])
                 for i, atk in enumerate(attacks_obj):
                     d = getattr(atk, "fixed_damage", 0)
                     if d == 0: d = getattr(atk, "damage", 0)
                     if d > best_dmg: best_dmg = d; best_cost = 2; best_idx = i
            return (best_dmg, best_cost, best_idx)

        def needs_energy(card_obj):
            name = get_card_name(card_obj)
            if not name: return False
            current_energy = len(get_card_energy(card_obj))
            _, cost, _ = get_best_attack(card_obj)
            if cost > 0: return current_energy < cost
            if "ex" in name.lower(): return current_energy < 3
            return current_energy < 2

        # --- 2. Parse State ---
        me = state.current_player
        opp = 1 - me
        my_active = state.get_active_pokemon(me)
        my_bench = [b for b in state.get_bench_pokemon(me) if b is not None]
        my_hand = state.get_hand(me)
        opp_active = state.get_active_pokemon(opp)
        opp_bench = [b for b in state.get_bench_pokemon(opp) if b is not None]
        my_active_name = get_card_name(my_active)
        my_active_hp = get_card_hp(my_active)
        my_active_max_hp = get_card_max_hp(my_active)
        opp_active_hp = get_card_hp(opp_active) if opp_active else 0

        # Categorize Actions
        acts = {
            "attack": [], "attach_energy": [], "attach_tool": [],
            "evolve": [], "place_basic": [], "place_active": [], "play_supporter": [],
            "play_item": [], "ability": [], "retreat": [],
            "activate": [], "end": [], "draw": [], "stadium": []
        }

        for aid in legal_actions:
            aname = game.action_name(aid)

            if aname == "EndTurn": acts["end"].append(aid)
            elif aname == "DrawCard": acts["draw"].append(aid)
            elif aname.startswith("Attack("):
                m = re.search(r"Attack\((\d+)\)", aname)
                if m: acts["attack"].append((aid, int(m.group(1))))
            elif aname.startswith("AttachTool"):
                m = re.search(r"AttachTool\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
                if m: acts["attach_tool"].append((aid, m.group(1).replace(")", ""), int(m.group(2))))
            elif aname.startswith("Attach"):
                if "Tool" in aname: continue
                m = re.search(r"Attach\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
                if m: acts["attach_energy"].append((aid, m.group(1).replace(")", ""), int(m.group(2))))
                else:
                    m = re.search(r"AttachEnergy\((\d+), (.*?)\)", aname)
                    if m: acts["attach_energy"].append((aid, m.group(2), int(m.group(1))))
            elif aname.startswith("Evolve"):
                m = re.search(r"Evolve\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
                if m: acts["evolve"].append((aid, m.group(1).replace(")", ""), int(m.group(2))))
            elif aname.startswith("Place") or aname.startswith("PlayPokemon"):
                 m = re.search(r"Place\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
                 if m:
                     if int(m.group(2)) == 0: acts["place_active"].append((aid, m.group(1).replace(")", "")))
                     else: acts["place_basic"].append((aid, m.group(1).replace(")", ""), int(m.group(2))))
                 elif "PlayPokemon" in aname:
                     if ", 0)" in aname: acts["place_active"].append((aid, "Unknown"))
                     else: acts["place_basic"].append((aid, "Unknown", -1))
            elif aname.startswith("Play") or aname.startswith("UseItem") or aname.startswith("UseSupporter"):
                target = -1
                m_t = re.search(r", (\d+)\)", aname)
                if m_t: target = int(m_t.group(1))
                m_n = re.search(r"Some\((.*?)\)", aname)
                if m_n: card_name = m_n.group(1).replace(")", "")
                else: card_name = aname

                supporters = ["Research", "Sabrina", "Giovanni", "Erika", "Misty", "Blaine", "Koga", "Lt. Surge", "Brock", "Copycat", "Lisia", "Cyrus", "Mars", "Red", "Guzma", "Judge", "Acerola", "Hau", "Bill"]
                if any(s in card_name for s in supporters): acts["play_supporter"].append((aid, card_name, target))
                else: acts["play_item"].append((aid, card_name, target))
            elif aname.startswith("UseAbility"):
                m = re.search(r"UseAbility\((\d+)\)", aname)
                if m: acts["ability"].append((aid, int(m.group(1))))
            elif aname.startswith("Retreat"): acts["retreat"].append(aid)
            elif aname.startswith("Activate"):
                m = re.search(r"Activate\((\d+)\)", aname)
                if m: acts["activate"].append((aid, int(m.group(1))))
            elif "Stadium" in aname: acts["stadium"].append(aid)

        # --- 3. Strategy Execution ---

        # 0. Draw Card
        if acts["draw"]: return acts["draw"][0]

        # A. Win Condition (Lethal)
        if acts["attack"] and opp_active_hp > 0:
            giovanni = [a for a in acts["play_supporter"] if "Giovanni" in a[1]]

            # Direct Lethals
            direct_lethals = []
            giovanni_lethals = []

            for aid, idx in acts["attack"]:
                dmg = calculate_damage(my_active, idx, len(my_bench), opp_active_hp)
                if dmg >= opp_active_hp:
                    direct_lethals.append((aid, dmg))
                elif giovanni and (dmg + 10) >= opp_active_hp:
                    giovanni_lethals.append((aid, dmg))

            if direct_lethals:
                # Pick MAX damage to be safe against coin flips/variance
                direct_lethals.sort(key=lambda x: x[1], reverse=True)
                return direct_lethals[0][0]

            if giovanni_lethals:
                return giovanni[0][0]

        # B. Forced Switch (Activate)
        if acts["activate"]:
            if not my_active or my_active_hp == 0:
                best_cand = acts["activate"][0][0]
                max_score = -2000
                for aid, idx in acts["activate"]:
                    if idx >= len(my_bench): continue
                    c = my_bench[idx]
                    if not c: continue
                    name = get_card_name(c); score = 0
                    is_ex = "ex" in name.lower()
                    energy_count = len(get_card_energy(c))
                    hp = get_card_hp(c)
                    if not needs_energy(c): score += 500
                    elif energy_count > 0: score += 100 * energy_count
                    if is_ex: score += 50
                    score += hp
                    if score > max_score: max_score = score; best_cand = aid
                return best_cand
            else: return acts["activate"][0][0]

        # C. Place Active
        if acts["place_active"]:
            best_active = acts["place_active"][0][0]; max_score = -1000
            for aid, name in acts["place_active"]:
                score = 0; n = name.lower()
                if n in CARD_DB: score += CARD_DB[n].get("hp", 60) - (CARD_DB[n].get("retreat", 1) * 10)
                if "ex" in n: score += 50
                if "kangaskhan" in n: score += 60
                if "tauros" in n: score += 50
                if "articuno" in n and "ex" not in n: score += 40
                if "zapdos" in n and "ex" not in n: score += 40
                if "moltres" in n and "ex" not in n: score += 40
                if score > max_score: max_score = score; best_active = aid
            return best_active

        # D. Main Phase
        if acts["evolve"]:
            for aid, name, pos in acts["evolve"]:
                if pos == 0: return aid
            return acts["evolve"][0][0]

        if acts["place_basic"]:
            if len(my_bench) < 3:
                best_bp = None; best_score = -100
                for aid, name, _ in acts["place_basic"]:
                    score = 0; n = name.lower()
                    if "ex" in n: score += 100
                    if "pikachu" in n: score += 80
                    if "ralts" in n: score += 60
                    if "froakie" in n: score += 60
                    if "articuno" in n: score += 70
                    if "moltres" in n: score += 70
                    if "charmander" in n or "squirtle" in n or "bulbasaur" in n: score += 50
                    if score > best_score: best_score = score; best_bp = aid
                if best_bp and best_score > 0: return best_bp

        if acts["ability"]:
            for aid, idx in acts["ability"]:
                user = my_active if idx == 0 else (my_bench[idx-1] if idx-1 < len(my_bench) else None)
                if user:
                    n = get_card_name(user).lower()
                    if "greninja" in n: return aid
                    if "gardevoir" in n:
                        if needs_energy(my_active) or any(needs_energy(b) for b in my_bench): return aid
                    if "pidgeot" in n: return aid
            return acts["ability"][0][0]

        # Attach Tool (Improved)
        if acts["attach_tool"]:
             # Active EX/Strong
             for aid, tool_name, pos in acts["attach_tool"]:
                 if pos == 0:
                     target = my_active
                     if target and "ex" in get_card_name(target).lower(): return aid
             # Bench EX/Strong
             for aid, tool_name, pos in acts["attach_tool"]:
                 if pos != 0:
                     target = my_bench[pos-1] if pos-1 < len(my_bench) else None
                     if target and "ex" in get_card_name(target).lower(): return aid
             return acts["attach_tool"][0][0]

        if acts["play_supporter"]:
            misty = [a for a in acts["play_supporter"] if "Misty" in a[1]]
            if misty:
                if "water" in get_energy_type(my_active_name) and needs_energy(my_active):
                     for aid, _, target in misty:
                        if target == 0: return aid
                for i, b in enumerate(my_bench):
                    if b and "water" in get_energy_type(get_card_name(b)) and needs_energy(b):
                         for aid, _, target in misty:
                             if target == i + 1: return aid

            research = [a for a in acts["play_supporter"] if "Research" in a[1]]
            if research and len(my_hand) <= 5: return research[0][0]

            sabrina = [a for a in acts["play_supporter"] if "Sabrina" in a[1]]
            if sabrina and opp_bench:
                can_kill_active = False
                if acts["attack"]:
                     for _, idx in acts["attack"]:
                         if calculate_damage(my_active, idx, len(my_bench), opp_active_hp) >= opp_active_hp: can_kill_active = True
                if not can_kill_active and opp_active_hp > 50: return sabrina[0][0]

        if acts["play_item"]:
            potion = [a for a in acts["play_item"] if "Potion" in a[1]]
            if potion:
                 if my_active_hp > 0 and my_active_hp <= my_active_max_hp - 20: return potion[0][0]
            pokeball = [a for a in acts["play_item"] if "Ball" in a[1]]
            if pokeball and len(my_bench) < 3: return pokeball[0][0]
            redcard = [a for a in acts["play_item"] if "Red Card" in a[1]]
            if redcard: return redcard[0][0]
            return acts["play_item"][0][0]

        if acts["stadium"]: return acts["stadium"][0]

        if acts["attach_energy"]:
            best_attach = None; max_score = -1000
            for aid, type_str, pos in acts["attach_energy"]:
                score = 0
                target = my_active if pos == 0 else (my_bench[pos-1] if pos-1 < len(my_bench) else None)
                if not target: continue
                t_name = get_card_name(target); t_type = get_energy_type(t_name); type_str_lower = type_str.lower()
                match = (type_str_lower == t_type) or (t_type == "colorless")
                if needs_energy(target):
                    score += 100
                    if pos == 0: score += 50
                    if match: score += 60
                    if "ex" in t_name.lower(): score += 30
                    if "mewtwo" in t_name.lower() and "psychic" in type_str_lower: score += 50
                    if "pikachu" in t_name.lower() and "lightning" in type_str_lower: score += 50
                    if "charizard" in t_name.lower() and "fire" in type_str_lower: score += 50
                    if "blastoise" in t_name.lower() and "water" in type_str_lower: score += 50
                    if "venusaur" in t_name.lower() and "grass" in type_str_lower: score += 50
                else: score -= 50
                if score > max_score: max_score = score; best_attach = aid
            if best_attach and max_score > 0: return best_attach

        if acts["retreat"] and my_active:
            danger_hp = 70
            if my_active_hp <= danger_hp:
                 can_replace = False
                 for b in my_bench:
                     if b and not needs_energy(b) and get_card_hp(b) > 50: can_replace = True; break
                 if can_replace: return acts["retreat"][0]

        if acts["attack"]:
            best_atk = acts["attack"][0][0]; max_dmg = -1
            for aid, idx in acts["attack"]:
                d = calculate_damage(my_active, idx, len(my_bench), opp_active_hp)
                if d > max_dmg: max_dmg = d; best_atk = aid
            return best_atk

        if acts["end"]: return acts["end"][0]
        return legal_actions[0]

    except Exception as e:
        logging.error(f"Error in play: {e}")
        return legal_actions[0]
