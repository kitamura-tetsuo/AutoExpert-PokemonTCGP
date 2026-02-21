
import re
import random
import sys
import logging

# Setup logging
logging.basicConfig(filename='player.log', level=logging.INFO, filemode='w', format='%(asctime)s - %(message)s')

# --- Card Database (Expanded & Normalized) ---
# All keys lowercase
CARD_DB = {
# --- TARGETED DB UPDATE ---
    "absol": {'hp': 80, 'energy_type': 'Darkness', 'retreat': 1, 'attacks': [{'cost': ['Darkness', 'Colorless'], 'dmg': 20, 'text': "If your opponent's Active Pokémon is affected by a Special Condition, this attack does 60 more damage.", 'scaling': True}]},
    "aerodactyl ex": {'hp': 140, 'energy_type': 'Fighting', 'retreat': 1, 'attacks': [{'cost': ['Fighting', 'Colorless'], 'dmg': 80, 'text': None}]},
    "alolan dugtrio ex": {'hp': 130, 'energy_type': 'Metal', 'retreat': 1, 'attacks': [{'cost': ['Metal', 'Colorless'], 'dmg': 60, 'text': 'Flip 3 coins. This attack does 60 damage for each heads.', 'coin_flips': 3}]},
    "alolan exeggutor": {'hp': 150, 'energy_type': 'Grass', 'retreat': 4, 'attacks': [{'cost': ['Grass', 'Colorless', 'Colorless'], 'dmg': 150, 'text': 'Flip a coin. If tails, this attack does nothing.', 'coin_flips': 1}]},
    "alolan muk ex": {'hp': 160, 'energy_type': 'Darkness', 'retreat': 3, 'attacks': [{'cost': ['Darkness', 'Darkness', 'Colorless'], 'dmg': 80, 'text': "1 Special Condition from among Asleep, Burned, Confused, Paralyzed, and Poisoned is chosen at random, and your opponent's Active Pokémon is now affected by that Special Condition. Any Special Conditions already affecting that Pokémon will not be chosen."}]},
    "alolan ninetales ex": {'hp': 150, 'energy_type': 'Water', 'retreat': 2, 'attacks': [{'cost': ['Water', 'Water'], 'dmg': 80, 'text': "During your opponent's next turn, they can't take any Energy from their Energy Zone to attach to their Active Pokémon."}]},
    "alolan raichu ex": {'hp': 140, 'energy_type': 'Lightning', 'retreat': 1, 'attacks': [{'cost': ['Colorless', 'Colorless', 'Colorless'], 'dmg': 60, 'text': "This attack does 30 more damage for each Energy attached to your opponent's Active Pokémon.", 'scaling': True}]},
    "altaria": {'hp': 120, 'energy_type': 'Dragon', 'retreat': 2, 'attacks': [{'cost': ['Colorless', 'Colorless'], 'dmg': 40, 'text': 'If this Pokémon has 2 or more different types of Energy attached, this attack does 60 more damage.', 'scaling': True}]},
    "arcanine ex": {'hp': 150, 'energy_type': 'Fire', 'retreat': 2, 'attacks': [{'cost': ['Fire', 'Fire', 'Colorless'], 'dmg': 120, 'text': 'This Pokémon also does 20 damage to itself.'}]},
    "arceus ex": {'hp': 140, 'energy_type': 'Colorless', 'retreat': 2, 'attacks': [{'cost': ['Colorless', 'Colorless', 'Colorless'], 'dmg': 70, 'text': 'This attack does 20 more damage for each of your Benched Pokémon.', 'scaling': True}]},
    "articuno ex": {'hp': 140, 'energy_type': 'Water', 'retreat': 2, 'attacks': [{'cost': ['Water', 'Colorless'], 'dmg': 40, 'text': None}, {'cost': ['Water', 'Water', 'Water'], 'dmg': 80, 'text': "This attack also does 10 damage to each of your opponent's Benched Pokémon."}]},
    "banette": {'hp': 90, 'energy_type': 'Psychic', 'retreat': 1, 'attacks': [{'cost': ['Psychic'], 'dmg': 30, 'text': "During your opponent's next turn, they can't take any Energy from their Energy Zone to attach to their Active Pokémon."}]},
    "beedrill ex": {'hp': 170, 'energy_type': 'Grass', 'retreat': 1, 'attacks': [{'cost': ['Grass', 'Grass'], 'dmg': 80, 'text': "Discard a random Energy from your opponent's Active Pokémon.", 'discard': True}]},
    "bibarel ex": {'hp': 160, 'energy_type': 'Colorless', 'retreat': 3, 'attacks': [{'cost': ['Colorless', 'Colorless', 'Colorless', 'Colorless'], 'dmg': 100, 'text': 'Heal 30 damage from this Pokémon.'}]},
    "blacephalon ex": {'hp': 140, 'energy_type': 'Fire', 'retreat': 2, 'attacks': [{'cost': ['Fire'], 'dmg': 0, 'text': "Your opponent's Active Pokémon is now Burned."}, {'cost': ['Fire', 'Fire', 'Fire'], 'dmg': 140, 'text': 'Discard 3 [R] Energy from this Pokémon.', 'discard': True}]},
    "blastoise ex": {'hp': 180, 'energy_type': 'Water', 'retreat': 3, 'attacks': [{'cost': ['Water', 'Colorless'], 'dmg': 40, 'text': None}, {'cost': ['Water', 'Water', 'Colorless'], 'dmg': 100, 'text': 'If this Pokémon has at least 2 extra [W] Energy attached, this attack does 60 more damage.', 'scaling': True}]},
    "blissey ex": {'hp': 180, 'energy_type': 'Colorless', 'retreat': 3, 'attacks': [{'cost': ['Colorless', 'Colorless', 'Colorless', 'Colorless'], 'dmg': 100, 'text': 'Flip a coin. If heads, heal 60 damage from this Pokémon.', 'coin_flips': 1}]},
    "buzzwole ex": {'hp': 140, 'energy_type': 'Grass', 'retreat': 2, 'attacks': [{'cost': ['Colorless', 'Colorless'], 'dmg': 30, 'text': None}, {'cost': ['Grass', 'Grass', 'Colorless'], 'dmg': 120, 'text': "During your next turn, this Pokémon can't use Big Beat."}]},
    "celebi ex": {'hp': 130, 'energy_type': 'Grass', 'retreat': 1, 'attacks': [{'cost': ['Grass', 'Colorless'], 'dmg': 50, 'text': 'Flip a coin for each Energy attached to this Pokémon. This attack does 50 damage for each heads.', 'coin_flips': 1}]},
    "charizard ex": {'hp': 180, 'energy_type': 'Fire', 'retreat': 2, 'attacks': [{'cost': ['Fire', 'Colorless', 'Colorless'], 'dmg': 60, 'text': None}, {'cost': ['Fire', 'Fire', 'Colorless', 'Colorless'], 'dmg': 200, 'text': 'Discard 2 [R] Energy from this Pokémon.', 'discard': True}]},
    "chesnaught": {'hp': 160, 'energy_type': 'Grass', 'retreat': 3, 'attacks': [{'cost': ['Grass', 'Grass', 'Colorless', 'Colorless'], 'dmg': 80, 'text': "During your opponent's next turn, if this Pokémon is damaged by an attack, do 80 damage to the Attacking Pokémon."}]},
    "cinderace": {'hp': 130, 'energy_type': 'Fire', 'retreat': 0, 'attacks': [{'cost': ['Fire', 'Fire'], 'dmg': 120, 'text': "During your next turn, this Pokémon can't attack."}]},
    "cornerstone mask ogerpon": {'hp': 80, 'energy_type': 'Fighting', 'retreat': 1, 'attacks': [{'cost': ['Fighting', 'Colorless'], 'dmg': 40, 'text': "Flip a coin. If heads, during your opponent's next turn, this Pokémon takes -100 damage from attacks.", 'coin_flips': 1}]},
    "crabominable ex": {'hp': 160, 'energy_type': 'Water', 'retreat': 3, 'attacks': [{'cost': ['Water'], 'dmg': 40, 'text': "During your next turn, this Pokémon's Insatiable Striking attack does +40 damage."}]},
    "cresselia ex": {'hp': 140, 'energy_type': 'Psychic', 'retreat': 2, 'attacks': [{'cost': ['Psychic', 'Psychic', 'Colorless'], 'dmg': 80, 'text': None}]},
    "crobat ex": {'hp': 170, 'energy_type': 'Darkness', 'retreat': 1, 'attacks': [{'cost': ['Darkness'], 'dmg': 70, 'text': "Your opponent's Active Pokémon is now Poisoned."}]},
    "darkrai": {'hp': 120, 'energy_type': 'Darkness', 'retreat': 2, 'attacks': [{'cost': ['Darkness', 'Darkness', 'Colorless'], 'dmg': 70, 'text': "During your opponent's next turn, the Defending Pokémon can't retreat."}]},
    "darkrai ex": {'hp': 140, 'energy_type': 'Darkness', 'retreat': 2, 'attacks': [{'cost': ['Darkness', 'Darkness', 'Colorless'], 'dmg': 80, 'text': None}]},
    "decidueye": {'hp': 130, 'energy_type': 'Grass', 'retreat': 2, 'attacks': [{'cost': ['Grass', 'Grass'], 'dmg': 0, 'text': "This attack does 70 damage to 1 of your opponent's Pokémon."}]},
    "decidueye ex": {'hp': 170, 'energy_type': 'Grass', 'retreat': 1, 'attacks': [{'cost': ['Colorless', 'Colorless'], 'dmg': 0, 'text': "This attack does 100 damage to 1 of your opponent's Pokémon that have damage on them."}, {'cost': ['Grass', 'Grass'], 'dmg': 80, 'text': None}]},
    "dhelmise ex": {'hp': 140, 'energy_type': 'Grass', 'retreat': 2, 'attacks': [{'cost': ['Grass', 'Grass', 'Colorless'], 'dmg': 80, 'text': "During your opponent's next turn, the Defending Pokémon can't retreat."}]},
    "dialga ex": {'hp': 150, 'energy_type': 'Metal', 'retreat': 2, 'attacks': [{'cost': ['Metal', 'Metal'], 'dmg': 30, 'text': 'Take 2 [M] Energy from your Energy Zone and attach it to 1 of your Benched Pokémon.'}, {'cost': ['Metal', 'Metal', 'Colorless', 'Colorless'], 'dmg': 100, 'text': None}]},
    "donphan ex": {'hp': 160, 'energy_type': 'Fighting', 'retreat': 3, 'attacks': [{'cost': ['Fighting'], 'dmg': 50, 'text': 'If this Pokémon has at least 2 extra [F] Energy attached, this attack does 60 more damage.', 'scaling': True}]},
    "dragalge ex": {'hp': 150, 'energy_type': 'Darkness', 'retreat': 2, 'attacks': [{'cost': ['Darkness', 'Colorless'], 'dmg': 80, 'text': None}]},
    "dragonite ex": {'hp': 180, 'energy_type': 'Dragon', 'retreat': 2, 'attacks': [{'cost': ['Water', 'Lightning', 'Colorless'], 'dmg': 180, 'text': "During your next turn, this Pokémon can't attack."}]},
    "eevee ex": {'hp': 90, 'energy_type': 'Colorless', 'retreat': 1, 'attacks': [{'cost': ['Colorless'], 'dmg': 30, 'text': None}]},
    "entei": {'hp': 110, 'energy_type': 'Fire', 'retreat': 2, 'attacks': [{'cost': ['Fire', 'Colorless', 'Colorless', 'Colorless'], 'dmg': 110, 'text': 'Flip a coin. If tails, discard 2 random Energy from this Pokémon.', 'coin_flips': 1, 'discard': True}]},
    "entei ex": {'hp': 140, 'energy_type': 'Fire', 'retreat': 2, 'attacks': [{'cost': ['Fire', 'Fire'], 'dmg': 60, 'text': 'If this Pokémon has at least 2 extra [R] Energy attached, this attack does 60 more damage.', 'scaling': True}]},
    "espeon ex": {'hp': 140, 'energy_type': 'Psychic', 'retreat': 1, 'attacks': [{'cost': ['Psychic', 'Psychic'], 'dmg': 80, 'text': None}]},
    "excadrill": {'hp': 120, 'energy_type': 'Metal', 'retreat': 2, 'attacks': [{'cost': ['Metal', 'Metal', 'Colorless'], 'dmg': 80, 'text': None}]},
    "exeggcute": {'hp': 60, 'energy_type': 'Grass', 'retreat': 1, 'attacks': [{'cost': ['Grass', 'Colorless'], 'dmg': 30, 'text': None}]},
    "exeggutor": {'hp': 130, 'energy_type': 'Grass', 'retreat': 3, 'attacks': [{'cost': ['Grass'], 'dmg': 30, 'text': 'Flip a coin. If heads, this attack does 30 more damage.', 'coin_flips': 1, 'scaling': True}]},
    "exeggutor ex": {'hp': 160, 'energy_type': 'Grass', 'retreat': 3, 'attacks': [{'cost': ['Grass'], 'dmg': 40, 'text': 'Flip a coin. If heads, this attack does 40 more damage.', 'coin_flips': 1, 'scaling': True}]},
    "exploud": {'hp': 150, 'energy_type': 'Colorless', 'retreat': 3, 'attacks': [{'cost': ['Colorless', 'Colorless', 'Colorless'], 'dmg': 90, 'text': "During your opponent's next turn, they can't play any Item cards from their hand."}]},
    "flareon ex": {'hp': 150, 'energy_type': 'Fire', 'retreat': 2, 'attacks': [{'cost': ['Fire', 'Fire', 'Colorless'], 'dmg': 130, 'text': 'Discard 2 [R] Energy from this Pokémon.', 'discard': True}]},
    "frosmoth": {'hp': 90, 'energy_type': 'Water', 'retreat': 1, 'attacks': [{'cost': ['Water', 'Colorless'], 'dmg': 40, 'text': "Your opponent's Active Pokémon is now Asleep."}]},
    "galarian linoone": {'hp': 80, 'energy_type': 'Darkness', 'retreat': 1, 'attacks': [{'cost': ['Darkness'], 'dmg': 40, 'text': None}]},
    "galarian obstagoon": {'hp': 150, 'energy_type': 'Darkness', 'retreat': 2, 'attacks': [{'cost': ['Darkness', 'Darkness'], 'dmg': 70, 'text': "If your opponent's Active Pokémon has damage on it, this attack does 50 more damage.", 'scaling': True}]},
    "galarian rapidash": {'hp': 100, 'energy_type': 'Psychic', 'retreat': 2, 'attacks': [{'cost': ['Psychic'], 'dmg': 40, 'text': 'If you have 5 or more [P] Energy in play, this attack does 60 more damage.', 'scaling': True}]},
    "galarian zigzagoon": {'hp': 60, 'energy_type': 'Darkness', 'retreat': 1, 'attacks': [{'cost': ['Darkness'], 'dmg': 20, 'text': None}]},
    "gallade ex": {'hp': 170, 'energy_type': 'Fighting', 'retreat': 1, 'attacks': [{'cost': ['Fighting', 'Fighting'], 'dmg': 70, 'text': "This attack does 20 more damage for each Energy attached to your opponent's Active Pokémon.", 'scaling': True}]},
    "garchomp ex": {'hp': 170, 'energy_type': 'Fighting', 'retreat': 1, 'attacks': [{'cost': ['Fighting'], 'dmg': 0, 'text': "This attack does 50 damage to 1 of your opponent's Pokémon."}, {'cost': ['Fighting', 'Fighting', 'Colorless'], 'dmg': 100, 'text': None}]},
    "gengar ex": {'hp': 170, 'energy_type': 'Psychic', 'retreat': 2, 'attacks': [{'cost': ['Psychic', 'Psychic', 'Psychic'], 'dmg': 100, 'text': None}]},
    "gigalith ex": {'hp': 190, 'energy_type': 'Fighting', 'retreat': 4, 'attacks': [{'cost': ['Fighting', 'Fighting', 'Fighting', 'Fighting'], 'dmg': 0, 'text': "This attack does 140 damage to 1 of your opponent's Pokémon. During your next turn, this Pokémon can't attack."}]},
    "giratina": {'hp': 120, 'energy_type': 'Psychic', 'retreat': 3, 'attacks': [{'cost': ['Psychic', 'Psychic', 'Colorless'], 'dmg': 70, 'text': None}]},
    "giratina ex": {'hp': 150, 'energy_type': 'Psychic', 'retreat': 2, 'attacks': [{'cost': ['Psychic', 'Psychic', 'Psychic', 'Colorless'], 'dmg': 130, 'text': 'This Pokémon also does 20 damage to itself.'}]},
    "glaceon ex": {'hp': 140, 'energy_type': 'Water', 'retreat': 1, 'attacks': [{'cost': ['Water', 'Water', 'Colorless'], 'dmg': 90, 'text': None}]},
    "gourgeist": {'hp': 110, 'energy_type': 'Psychic', 'retreat': 2, 'attacks': [{'cost': ['Psychic'], 'dmg': 70, 'text': "Discard a card from your hand. If you can't, this attack does nothing."}]},
    "greninja": {'hp': 120, 'energy_type': 'Water', 'retreat': 1, 'attacks': [{'cost': ['Water', 'Colorless'], 'dmg': 60, 'text': None}]},
    "greninja ex": {'hp': 170, 'energy_type': 'Water', 'retreat': 2, 'attacks': [{'cost': ['Water', 'Water'], 'dmg': 100, 'text': None}]},
    "guzzlord": {'hp': 150, 'energy_type': 'Darkness', 'retreat': 4, 'attacks': [{'cost': ['Darkness', 'Darkness', 'Darkness', 'Colorless'], 'dmg': 0, 'text': "Flip a coin. If heads, discard your opponent's Active Pokémon.", 'coin_flips': 1}]},
    "guzzlord ex": {'hp': 170, 'energy_type': 'Darkness', 'retreat': 4, 'attacks': [{'cost': ['Colorless', 'Colorless'], 'dmg': 30, 'text': "Flip a coin until you get tails. For each heads, discard a random Energy from your opponent's Active Pokémon.", 'coin_flips': 1, 'discard': True}, {'cost': ['Darkness', 'Darkness', 'Darkness', 'Colorless'], 'dmg': 120, 'text': None}]},
    "gyarados ex": {'hp': 180, 'energy_type': 'Water', 'retreat': 3, 'attacks': [{'cost': ['Water', 'Water', 'Water', 'Colorless'], 'dmg': 140, 'text': "Discard a random Energy from among the Energy attached to all Pokémon (both yours and your opponent's).", 'discard': True}]},
    "hearthflame mask ogerpon": {'hp': 80, 'energy_type': 'Fire', 'retreat': 1, 'attacks': [{'cost': ['Fire', 'Colorless'], 'dmg': 40, 'text': 'Flip a coin. If heads, take 2 [R] Energy from your Energy Zone and attach it to 1 of your Benched Pokémon.', 'coin_flips': 1}]},
    "hitmonchan ex": {'hp': 130, 'energy_type': 'Fighting', 'retreat': 1, 'attacks': [{'cost': ['Fighting'], 'dmg': 50, 'text': "This attack's damage isn't affected by Weakness."}]},
    "ho-oh ex": {'hp': 150, 'energy_type': 'Fire', 'retreat': 2, 'attacks': [{'cost': ['Colorless', 'Colorless', 'Colorless'], 'dmg': 80, 'text': 'Take a [R], [W], and [L] Energy from your Energy Zone and attach them to your Benched Basic Pokémon in any way you like.'}]},
    "hydreigon": {'hp': 150, 'energy_type': 'Darkness', 'retreat': 2, 'attacks': [{'cost': ['Darkness', 'Darkness', 'Darkness'], 'dmg': 130, 'text': 'Discard all Energy from this Pokémon.', 'discard': True}]},
    "incineroar": {'hp': 150, 'energy_type': 'Fire', 'retreat': 3, 'attacks': [{'cost': ['Fire', 'Fire', 'Colorless'], 'dmg': 100, 'text': 'Flip 2 coins. This attack does 100 damage for each heads.', 'coin_flips': 2}]},
    "incineroar ex": {'hp': 180, 'energy_type': 'Fire', 'retreat': 2, 'attacks': [{'cost': ['Fire'], 'dmg': 30, 'text': "Your opponent's Active Pokémon is now Burned."}, {'cost': ['Fire', 'Fire', 'Colorless'], 'dmg': 80, 'text': 'If this Pokémon has damage on it, this attack does 60 more damage.', 'scaling': True}]},
    "indeedee": {'hp': 80, 'energy_type': 'Psychic', 'retreat': 1, 'attacks': [{'cost': ['Psychic', 'Psychic', 'Psychic'], 'dmg': 0, 'text': "This attack does 70 damage to 1 of your opponent's Benched Pokémon."}]},
    "indeedee ex": {'hp': 130, 'energy_type': 'Psychic', 'retreat': 1, 'attacks': [{'cost': ['Psychic', 'Psychic'], 'dmg': 30, 'text': "This attack does 30 more damage for each Energy attached to your opponent's Active Pokémon.", 'scaling': True}]},
    "infernape ex": {'hp': 170, 'energy_type': 'Fire', 'retreat': 0, 'attacks': [{'cost': ['Fire', 'Fire'], 'dmg': 140, 'text': 'Discard all [R] Energy from this Pokémon.', 'discard': True}]},
    "jolteon ex": {'hp': 140, 'energy_type': 'Lightning', 'retreat': 1, 'attacks': [{'cost': ['Lightning', 'Lightning'], 'dmg': 80, 'text': None}]},
    "jumpluff ex": {'hp': 160, 'energy_type': 'Grass', 'retreat': 1, 'attacks': [{'cost': ['Colorless'], 'dmg': 70, 'text': 'You may switch this Pokémon with 1 of your Benched Pokémon.'}]},
    "kingdra ex": {'hp': 170, 'energy_type': 'Water', 'retreat': 1, 'attacks': [{'cost': ['Water', 'Water'], 'dmg': 90, 'text': "During your opponent's next turn, the Defending Pokémon can't retreat."}]},
    "lanturn ex": {'hp': 150, 'energy_type': 'Lightning', 'retreat': 2, 'attacks': [{'cost': ['Lightning', 'Colorless', 'Colorless'], 'dmg': 80, 'text': "Flip a coin. If heads, your opponent's Active Pokémon is now Paralyzed. If tails, your opponent's Active Pokémon is now Confused.", 'coin_flips': 1}]},
    "lapras ex": {'hp': 140, 'energy_type': 'Water', 'retreat': 3, 'attacks': [{'cost': ['Water', 'Water', 'Colorless'], 'dmg': 80, 'text': 'Heal 20 damage from this Pokémon.'}]},
    "larvesta": {'hp': 80, 'energy_type': 'Fire', 'retreat': 2, 'attacks': [{'cost': ['Fire', 'Colorless'], 'dmg': 30, 'text': None}]},
    "leafeon ex": {'hp': 140, 'energy_type': 'Grass', 'retreat': 1, 'attacks': [{'cost': ['Grass', 'Colorless', 'Colorless'], 'dmg': 70, 'text': None}]},
    "lickilicky ex": {'hp': 160, 'energy_type': 'Colorless', 'retreat': 4, 'attacks': [{'cost': ['Colorless', 'Colorless', 'Colorless', 'Colorless'], 'dmg': 100, 'text': 'Flip a coin until you get tails. This attack does 40 more damage for each heads.', 'coin_flips': 1, 'scaling': True}]},
    "linoone": {'hp': 100, 'energy_type': 'Colorless', 'retreat': 1, 'attacks': [{'cost': ['Colorless'], 'dmg': 40, 'text': None}]},
    "lucario ex": {'hp': 150, 'energy_type': 'Fighting', 'retreat': 2, 'attacks': [{'cost': ['Fighting', 'Fighting', 'Fighting'], 'dmg': 100, 'text': "This attack also does 30 damage to 1 of your opponent's Benched Pokémon."}]},
    "lugia ex": {'hp': 150, 'energy_type': 'Colorless', 'retreat': 2, 'attacks': [{'cost': ['Fire', 'Water', 'Lightning'], 'dmg': 180, 'text': 'Discard a [R], [W], and [L] Energy from this Pokémon.', 'discard': True}]},
    "lunala ex": {'hp': 180, 'energy_type': 'Psychic', 'retreat': 1, 'attacks': [{'cost': ['Psychic', 'Colorless', 'Colorless'], 'dmg': 100, 'text': None}]},
    "lycanroc ex": {'hp': 150, 'energy_type': 'Fighting', 'retreat': 2, 'attacks': [{'cost': ['Fighting', 'Fighting', 'Colorless'], 'dmg': 130, 'text': 'Discard a [F] Energy from this Pokémon.', 'discard': True}]},
    "machamp ex": {'hp': 180, 'energy_type': 'Fighting', 'retreat': 3, 'attacks': [{'cost': ['Fighting', 'Fighting', 'Fighting'], 'dmg': 120, 'text': None}]},
    "magnezone": {'hp': 150, 'energy_type': 'Lightning', 'retreat': 2, 'attacks': [{'cost': ['Lightning', 'Colorless', 'Colorless'], 'dmg': 90, 'text': "During your opponent's next turn, if the Defending Pokémon tries to use an attack, your opponent flips a coin. If tails, that attack doesn't happen.", 'coin_flips': 1}]},
    "marowak ex": {'hp': 140, 'energy_type': 'Fighting', 'retreat': 1, 'attacks': [{'cost': ['Fighting', 'Fighting'], 'dmg': 80, 'text': 'Flip 2 coins. This attack does 80 damage for each heads.', 'coin_flips': 2}]},
    "mega absol ex": {'hp': 170, 'energy_type': 'Darkness', 'retreat': 1, 'attacks': [{'cost': ['Darkness', 'Darkness'], 'dmg': 80, 'text': 'Your opponent reveals their hand. Choose a Supporter card you find there and discard it.'}]},
    "mega altaria ex": {'hp': 190, 'energy_type': 'Psychic', 'retreat': 1, 'attacks': [{'cost': ['Psychic', 'Psychic'], 'dmg': 40, 'text': 'This attack does 30 more damage for each of your Benched Pokémon.', 'scaling': True}]},
    "mega ampharos ex": {'hp': 210, 'energy_type': 'Lightning', 'retreat': 2, 'attacks': [{'cost': ['Lightning', 'Lightning', 'Colorless'], 'dmg': 100, 'text': "1 of your opponent's Benched Pokémon is chosen at random 3 times. For each time a Pokémon was chosen, also do 20 damage to it."}]},
    "mega blastoise ex": {'hp': 230, 'energy_type': 'Water', 'retreat': 3, 'attacks': [{'cost': ['Water', 'Water', 'Colorless'], 'dmg': 130, 'text': "If this Pokémon has at least 3 extra [W] Energy attached, this attack also does 50 damage to 2 of your opponent's Benched Pokémon."}]},
    "mega blaziken ex": {'hp': 210, 'energy_type': 'Fire', 'retreat': 1, 'attacks': [{'cost': ['Fire', 'Fire'], 'dmg': 120, 'text': "Discard Fire[R] Energy from this Pokémon. Your opponent's Active Pokémon is now Burned.", 'discard': True}]},
    "mega charizard y ex": {'hp': 220, 'energy_type': 'Fire', 'retreat': 2, 'attacks': [{'cost': ['Fire', 'Fire', 'Fire', 'Colorless'], 'dmg': 250, 'text': 'This Pokémon also does 50 damage to itself.'}]},
    "mega gardevoir ex": {'hp': 210, 'energy_type': 'Psychic', 'retreat': 1, 'attacks': [{'cost': ['Psychic', 'Psychic'], 'dmg': 110, 'text': 'Take 3 [P] Energy from your Energy Zone and attach it to your [P] Pokémon in any way you like.'}]},
    "mega gyarados ex": {'hp': 210, 'energy_type': 'Water', 'retreat': 3, 'attacks': [{'cost': ['Water', 'Water', 'Water', 'Colorless'], 'dmg': 140, 'text': "Discard the top 3 cards of your opponent's deck."}]},
    "mega kangaskhan ex": {'hp': 180, 'energy_type': 'Colorless', 'retreat': 3, 'attacks': [{'cost': ['Colorless', 'Colorless', 'Colorless'], 'dmg': 80, 'text': "This attack is used twice in a row. The second attack does 40 damage.(If the first attack Knocks Out your opponent's Active Pokémon, the second attack is used after your opponent chooses a new Active Pokémon.)"}]},
    "mega latios ex": {'hp': 180, 'energy_type': 'Dragon', 'retreat': 2, 'attacks': [{'cost': ['Water', 'Water', 'Psychic'], 'dmg': 160, 'text': 'Discard all Energy from this Pokémon.', 'discard': True}]},
    "mega lopunny ex": {'hp': 190, 'energy_type': 'Fighting', 'retreat': 1, 'attacks': [{'cost': ['Fighting', 'Fighting'], 'dmg': 90, 'text': "Flip 2 coins. This attack does 90 damage for each heads. Your opponent's Active Pokémon is now Confused.", 'coin_flips': 2}]},
    "mega mawile ex": {'hp': 170, 'energy_type': 'Metal', 'retreat': 1, 'attacks': [{'cost': ['Metal', 'Colorless'], 'dmg': 60, 'text': "Until this Pokémon leaves the Active Spot, this Pokémon's Heat-Up Crunch attack does +30 damage. This effect stacks."}]},
    "mega pidgeot ex": {'hp': 210, 'energy_type': 'Colorless', 'retreat': 2, 'attacks': [{'cost': ['Colorless', 'Colorless', 'Colorless'], 'dmg': 100, 'text': "Flip 3 coins. For each heads, discard a random Energy from your opponent's Active Pokémon. If all of them are tails, this attack does nothing.", 'coin_flips': 3, 'discard': True}]},
    "mega pinsir ex": {'hp': 170, 'energy_type': 'Grass', 'retreat': 2, 'attacks': [{'cost': ['Grass', 'Grass', 'Colorless'], 'dmg': 80, 'text': 'Flip a coin. If heads, this attack does 70 more damage.', 'coin_flips': 1, 'scaling': True}]},
    "mega steelix ex": {'hp': 220, 'energy_type': 'Metal', 'retreat': 4, 'attacks': [{'cost': ['Metal', 'Metal', 'Colorless', 'Colorless'], 'dmg': 120, 'text': "During your opponent's next turn, this Pokémon takes  damage from attacks and has no Weakness."}]},
    "mega swampert ex": {'hp': 230, 'energy_type': 'Water', 'retreat': 3, 'attacks': [{'cost': ['Water', 'Water', 'Water'], 'dmg': 150, 'text': "Discard 2 random Energy from among the Energy attached to all Pokémon (both yours and your opponent's).", 'discard': True}]},
    "mega venusaur ex": {'hp': 240, 'energy_type': 'Grass', 'retreat': 4, 'attacks': [{'cost': ['Grass', 'Grass', 'Colorless', 'Colorless'], 'dmg': 120, 'text': "Your opponent's Active Pokémon is now Poisoned and Asleep."}]},
    "melmetal ex": {'hp': 170, 'energy_type': 'Metal', 'retreat': 3, 'attacks': [{'cost': ['Metal', 'Metal', 'Colorless'], 'dmg': 80, 'text': None}, {'cost': ['Metal', 'Metal', 'Metal', 'Colorless'], 'dmg': 100, 'text': 'If this Pokémon has a Pokémon Tool attached, this attack does 50 more damage.', 'scaling': True}]},
    "meowscarada": {'hp': 140, 'energy_type': 'Grass', 'retreat': 1, 'attacks': [{'cost': ['Grass', 'Grass'], 'dmg': 60, 'text': "If your opponent's Active Pokémon is a Pokémon ex, this attack does 70 more damage.", 'scaling': True}]},
    "mew ex": {'hp': 130, 'energy_type': 'Psychic', 'retreat': 1, 'attacks': [{'cost': ['Psychic'], 'dmg': 20, 'text': None}, {'cost': ['Colorless', 'Colorless', 'Colorless'], 'dmg': 0, 'text': "Choose 1 of your opponent's Active Pokémon's attacks and use it as this attack."}]},
    "mewtwo ex": {'hp': 150, 'energy_type': 'Psychic', 'retreat': 2, 'attacks': [{'cost': ['Psychic', 'Colorless'], 'dmg': 50, 'text': None}, {'cost': ['Psychic', 'Psychic', 'Colorless', 'Colorless'], 'dmg': 150, 'text': 'Discard 2 [P] Energy from this Pokémon.', 'discard': True}]},
    "mimikyu ex": {'hp': 120, 'energy_type': 'Psychic', 'retreat': 2, 'attacks': [{'cost': ['Psychic', 'Psychic'], 'dmg': 70, 'text': None}]},
    "mismagius ex": {'hp': 140, 'energy_type': 'Psychic', 'retreat': 1, 'attacks': [{'cost': ['Psychic', 'Psychic'], 'dmg': 70, 'text': "Your opponent's Active Pokémon is now Confused."}]},
    "moltres ex": {'hp': 140, 'energy_type': 'Fire', 'retreat': 2, 'attacks': [{'cost': ['Fire'], 'dmg': 0, 'text': 'Flip 3 coins. Take an amount of [R] Energy from your Energy Zone equal to the number of heads and attach it to your Benched [R] Pokémon in any way you like.', 'coin_flips': 3}, {'cost': ['Fire', 'Colorless', 'Colorless'], 'dmg': 70, 'text': None}]},
    "naganadel": {'hp': 100, 'energy_type': 'Darkness', 'retreat': 2, 'attacks': [{'cost': ['Darkness'], 'dmg': 40, 'text': "Your opponent's Active Pokémon is now Poisoned."}]},
    "oricorio": {'hp': 70, 'energy_type': 'Fire', 'retreat': 1, 'attacks': [{'cost': ['Fire', 'Fire'], 'dmg': 40, 'text': 'Discard a random Energy from both Active Pokémon.', 'discard': True}]},
    "origin forme dialga": {'hp': 120, 'energy_type': 'Metal', 'retreat': 2, 'attacks': [{'cost': ['Metal', 'Metal', 'Colorless'], 'dmg': 100, 'text': "Flip a coin. If tails, during your next turn, this Pokémon can't attack.", 'coin_flips': 1}]},
    "origin forme palkia": {'hp': 120, 'energy_type': 'Water', 'retreat': 2, 'attacks': [{'cost': ['Water', 'Water', 'Water'], 'dmg': 60, 'text': 'Flip a coin. If heads, this attack does 60 more damage.', 'coin_flips': 1, 'scaling': True}]},
    "pachirisu ex": {'hp': 120, 'energy_type': 'Lightning', 'retreat': 1, 'attacks': [{'cost': ['Lightning', 'Lightning'], 'dmg': 40, 'text': 'If this Pokémon has a Pokémon Tool attached, this attack does 40 more damage.', 'scaling': True}]},
    "paldean clodsire ex": {'hp': 160, 'energy_type': 'Darkness', 'retreat': 3, 'attacks': [{'cost': ['Darkness', 'Darkness'], 'dmg': 60, 'text': "If your opponent's Active Pokémon is Poisoned, this attack does 60 more damage.", 'scaling': True}]},
    "palkia ex": {'hp': 150, 'energy_type': 'Water', 'retreat': 2, 'attacks': [{'cost': ['Water'], 'dmg': 30, 'text': None}, {'cost': ['Water', 'Water', 'Water', 'Colorless'], 'dmg': 150, 'text': "Discard 3 [W] Energy from this Pokémon. This attack also does 20 damage to each of your opponent's Benched Pokémon.", 'discard': True}]},
    "passimian ex": {'hp': 130, 'energy_type': 'Fighting', 'retreat': 2, 'attacks': [{'cost': ['Fighting', 'Colorless'], 'dmg': 60, 'text': None}]},
    "pidgeot ex": {'hp': 170, 'energy_type': 'Colorless', 'retreat': 1, 'attacks': [{'cost': ['Colorless', 'Colorless', 'Colorless'], 'dmg': 80, 'text': "This attack does 20 more damage for each of your opponent's Benched Pokémon.", 'scaling': True}]},
    "pikachu ex": {'hp': 120, 'energy_type': 'Lightning', 'retreat': 1, 'attacks': [{'cost': ['Lightning', 'Lightning'], 'dmg': 30, 'text': 'This attack does 30 damage for each of your Benched [L] Pokémon.'}]},
    "poliwrath ex": {'hp': 180, 'energy_type': 'Fighting', 'retreat': 3, 'attacks': [{'cost': ['Fighting', 'Colorless', 'Colorless'], 'dmg': 100, 'text': 'If this Pokémon has any [W] Energy attached, this attack does 40 more damage.', 'scaling': True}]},
    "primarina": {'hp': 140, 'energy_type': 'Water', 'retreat': 2, 'attacks': [{'cost': ['Water', 'Colorless'], 'dmg': 60, 'text': None}]},
    "primarina ex": {'hp': 180, 'energy_type': 'Water', 'retreat': 2, 'attacks': [{'cost': ['Water'], 'dmg': 40, 'text': 'If this Pokémon has at least 1 extra [W] Energy attached, this attack does 40 more damage.', 'scaling': True}, {'cost': ['Water', 'Water', 'Water'], 'dmg': 100, 'text': 'Heal 20 damage from this Pokémon.'}]},
    "probopass ex": {'hp': 160, 'energy_type': 'Metal', 'retreat': 3, 'attacks': [{'cost': ['Metal', 'Metal', 'Colorless'], 'dmg': 90, 'text': "During your opponent's next turn, this Pokémon takes -20 damage from attacks."}]},
    "raichu ex": {'hp': 140, 'energy_type': 'Lightning', 'retreat': 1, 'attacks': [{'cost': ['Lightning', 'Lightning', 'Lightning'], 'dmg': 130, 'text': 'This Pokémon also does 30 damage to itself.'}]},
    "raikou": {'hp': 90, 'energy_type': 'Lightning', 'retreat': 1, 'attacks': [{'cost': ['Lightning', 'Colorless'], 'dmg': 70, 'text': 'This Pokémon also does 20 damage to itself.'}]},
    "raikou ex": {'hp': 130, 'energy_type': 'Lightning', 'retreat': 2, 'attacks': [{'cost': ['Lightning', 'Lightning'], 'dmg': 60, 'text': "This attack also does 10 damage to 1 of your opponent's Benched Pokémon."}]},
    "rapidash": {'hp': 100, 'energy_type': 'Fire', 'retreat': 1, 'attacks': [{'cost': ['Fire'], 'dmg': 40, 'text': None}]},
    "rapidash ex": {'hp': 150, 'energy_type': 'Fire', 'retreat': 2, 'attacks': [{'cost': ['Fire', 'Fire', 'Fire'], 'dmg': 110, 'text': "This attack also does 20 damage to 1 of your opponent's Benched Pokémon."}]},
    "rayquaza ex": {'hp': 140, 'energy_type': 'Colorless', 'retreat': 2, 'attacks': [{'cost': ['Colorless', 'Colorless', 'Colorless', 'Colorless'], 'dmg': 0, 'text': "1 of your opponent's Pokémon is chosen at random 4 times. For each time a Pokémon was chosen, do 40 damage to it."}]},
    "reshiram": {'hp': 120, 'energy_type': 'Fire', 'retreat': 2, 'attacks': [{'cost': ['Fire', 'Fire', 'Fire'], 'dmg': 110, 'text': 'Discard 2 [R] Energy from this Pokémon.', 'discard': True}]},
    "rillaboom": {'hp': 150, 'energy_type': 'Grass', 'retreat': 3, 'attacks': [{'cost': ['Grass', 'Grass', 'Grass', 'Colorless'], 'dmg': 120, 'text': None}]},
    "shuckle ex": {'hp': 120, 'energy_type': 'Grass', 'retreat': 1, 'attacks': [{'cost': ['Grass'], 'dmg': 20, 'text': 'Flip 3 coins. This attack does 20 damage for each heads.', 'coin_flips': 3}]},
    "skarmory ex": {'hp': 140, 'energy_type': 'Metal', 'retreat': 2, 'attacks': [{'cost': ['Metal', 'Metal'], 'dmg': 70, 'text': "During your opponent's next turn, this Pokémon takes -20 damage from attacks."}]},
    "snom": {'hp': 50, 'energy_type': 'Water', 'retreat': 1, 'attacks': [{'cost': ['Colorless'], 'dmg': 10, 'text': None}]},
    "snorlax ex": {'hp': 160, 'energy_type': 'Colorless', 'retreat': 4, 'attacks': [{'cost': ['Colorless', 'Colorless', 'Colorless', 'Colorless'], 'dmg': 130, 'text': 'This Pokémon is now Asleep.'}]},
    "solgaleo ex": {'hp': 180, 'energy_type': 'Metal', 'retreat': 2, 'attacks': [{'cost': ['Metal', 'Metal'], 'dmg': 120, 'text': 'This Pokémon also does 10 damage to itself.'}]},
    "starmie ex": {'hp': 130, 'energy_type': 'Water', 'retreat': 0, 'attacks': [{'cost': ['Water', 'Water'], 'dmg': 90, 'text': None}]},
    "suicune": {'hp': 100, 'energy_type': 'Water', 'retreat': 1, 'attacks': [{'cost': ['Water', 'Colorless', 'Colorless'], 'dmg': 70, 'text': "During your opponent's next turn, attacks used by the Defending Pokémon do -20 damage."}]},
    "suicune ex": {'hp': 140, 'energy_type': 'Water', 'retreat': 2, 'attacks': [{'cost': ['Water', 'Water'], 'dmg': 20, 'text': "This attack does 20 damage for each Benched Pokémon (both yours and your opponent's)."}]},
    "sylveon ex": {'hp': 140, 'energy_type': 'Psychic', 'retreat': 1, 'attacks': [{'cost': ['Psychic', 'Colorless'], 'dmg': 70, 'text': None}]},
    "tapu bulu": {'hp': 120, 'energy_type': 'Grass', 'retreat': 2, 'attacks': [{'cost': ['Grass', 'Grass', 'Colorless'], 'dmg': 100, 'text': 'Flip a coin. If tails, this Pokémon also does 20 damage to itself.', 'coin_flips': 1}]},
    "tapu fini": {'hp': 100, 'energy_type': 'Water', 'retreat': 1, 'attacks': [{'cost': ['Water', 'Water', 'Colorless'], 'dmg': 60, 'text': 'Heal 20 damage from this Pokémon.'}]},
    "tapu koko": {'hp': 100, 'energy_type': 'Lightning', 'retreat': 1, 'attacks': [{'cost': ['Lightning', 'Lightning', 'Lightning'], 'dmg': 70, 'text': 'Switch this Pokémon with 1 of your Benched [L] Pokémon.'}]},
    "tapu koko ex": {'hp': 130, 'energy_type': 'Lightning', 'retreat': 1, 'attacks': [{'cost': ['Lightning'], 'dmg': 20, 'text': 'Take a [L] Energy from your Energy Zone and attach it to this Pokémon.'}, {'cost': ['Lightning', 'Lightning', 'Colorless'], 'dmg': 90, 'text': None}]},
    "tapu lele": {'hp': 90, 'energy_type': 'Psychic', 'retreat': 1, 'attacks': [{'cost': ['Psychic'], 'dmg': 0, 'text': "This attack does 20 damage to 1 of your opponent's Pokémon for each Energy attached to that Pokémon."}]},
    "tauros ex": {'hp': 140, 'energy_type': 'Colorless', 'retreat': 2, 'attacks': [{'cost': ['Colorless', 'Colorless'], 'dmg': 90, 'text': 'Flip a coin. If tails, this Pokémon also does 30 damage to itself.', 'coin_flips': 1}]},
    "teal mask ogerpon ex": {'hp': 130, 'energy_type': 'Grass', 'retreat': 1, 'attacks': [{'cost': ['Grass', 'Grass'], 'dmg': 60, 'text': 'If the amount of Energy attached to both Active Pokémon is 5 or more, this attack does 60 more damage.', 'scaling': True}]},
    "tinkaton ex": {'hp': 170, 'energy_type': 'Metal', 'retreat': 2, 'attacks': [{'cost': ['Metal', 'Metal', 'Colorless'], 'dmg': 80, 'text': 'Flip a coin. If heads, this attack does 80 more damage.', 'coin_flips': 1, 'scaling': True}]},
    "toxapex": {'hp': 110, 'energy_type': 'Darkness', 'retreat': 2, 'attacks': [{'cost': ['Darkness'], 'dmg': 20, 'text': 'Flip 4 coins. This attack does 20 damage for each heads.', 'coin_flips': 4}]},
    "toxtricity ex": {'hp': 150, 'energy_type': 'Lightning', 'retreat': 2, 'attacks': [{'cost': ['Lightning', 'Lightning', 'Colorless'], 'dmg': 90, 'text': "This attack also does 30 damage to each of your opponent's Benched Pokémon that has damage on it."}]},
    "ultra necrozma ex": {'hp': 150, 'energy_type': 'Dragon', 'retreat': 2, 'attacks': [{'cost': ['Colorless', 'Colorless', 'Colorless'], 'dmg': 60, 'text': None}, {'cost': ['Psychic', 'Psychic', 'Metal', 'Metal'], 'dmg': 120, 'text': "Discard the top 5 cards of each player's deck."}]},
    "umbreon ex": {'hp': 140, 'energy_type': 'Darkness', 'retreat': 2, 'attacks': [{'cost': ['Darkness', 'Darkness'], 'dmg': 80, 'text': None}]},
    "venusaur ex": {'hp': 190, 'energy_type': 'Grass', 'retreat': 3, 'attacks': [{'cost': ['Grass', 'Colorless', 'Colorless'], 'dmg': 60, 'text': None}, {'cost': ['Grass', 'Grass', 'Colorless', 'Colorless'], 'dmg': 100, 'text': 'Heal 30 damage from this Pokémon.'}]},
    "volcarona": {'hp': 120, 'energy_type': 'Fire', 'retreat': 2, 'attacks': [{'cost': ['Fire', 'Fire', 'Colorless'], 'dmg': 0, 'text': "Discard 2 [R] Energy from this Pokémon. This attack does 80 damage to 1 of your opponent's Pokémon.", 'discard': True}]},
    "weavile ex": {'hp': 140, 'energy_type': 'Darkness', 'retreat': 1, 'attacks': [{'cost': ['Darkness'], 'dmg': 30, 'text': "If your opponent's Active Pokémon has damage on it, this attack does 40 more damage.", 'scaling': True}]},
    "weezing": {'hp': 110, 'energy_type': 'Darkness', 'retreat': 3, 'attacks': [{'cost': ['Darkness'], 'dmg': 30, 'text': None}]},
    "wellspring mask ogerpon": {'hp': 80, 'energy_type': 'Water', 'retreat': 1, 'attacks': [{'cost': ['Water', 'Colorless'], 'dmg': 40, 'text': "Flip a coin. If heads, this attack also does 40 damage to 1 of your opponent's Benched Pokémon.", 'coin_flips': 1}]},
    "whimsicott ex": {'hp': 140, 'energy_type': 'Grass', 'retreat': 1, 'attacks': [{'cost': ['Grass', 'Colorless'], 'dmg': 40, 'text': "This attack does 30 more damage for each Energy in your opponent's Active Pokémon's Retreat Cost.", 'scaling': True}]},
    "wigglytuff ex": {'hp': 140, 'energy_type': 'Colorless', 'retreat': 2, 'attacks': [{'cost': ['Colorless', 'Colorless', 'Colorless'], 'dmg': 80, 'text': "Your opponent's Active Pokémon is now Asleep."}]},
    "wishiwashi ex": {'hp': 170, 'energy_type': 'Water', 'retreat': 3, 'attacks': [{'cost': ['Water', 'Water', 'Water'], 'dmg': 30, 'text': 'This attack does 40 more damage for each of your Benched Wishiwashi and Wishiwashi ex.', 'scaling': True}]},
    "wugtrio ex": {'hp': 140, 'energy_type': 'Water', 'retreat': 1, 'attacks': [{'cost': ['Water', 'Water', 'Water'], 'dmg': 0, 'text': "1 of your opponent's Pokémon is chosen at random 3 times. For each time a Pokémon was chosen, do 50 damage to it."}]},
    "yanmega ex": {'hp': 140, 'energy_type': 'Grass', 'retreat': 1, 'attacks': [{'cost': ['Colorless', 'Colorless', 'Colorless'], 'dmg': 120, 'text': 'Discard a random Energy from this Pokémon.', 'discard': True}]},
    "zapdos ex": {'hp': 130, 'energy_type': 'Lightning', 'retreat': 1, 'attacks': [{'cost': ['Lightning'], 'dmg': 20, 'text': None}, {'cost': ['Lightning', 'Lightning', 'Lightning'], 'dmg': 50, 'text': 'Flip 4 coins. This attack does 50 damage for each heads.', 'coin_flips': 4}]},
    "zigzagoon": {'hp': 60, 'energy_type': 'Colorless', 'retreat': 1, 'attacks': [{'cost': ['Colorless'], 'dmg': 20, 'text': None}]},
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

            # Identify guaranteed vs risky lethals
            guaranteed_lethals = [] # (aid, damage)
            risky_lethals = [] # (aid, potential_damage)
            giovanni_guaranteed = []

            for aid, idx in acts["attack"]:
                # Analyze attack for coin flips
                is_risky = False
                base_dmg = 0

                # Check DB for risk
                name = my_active_name.lower() if my_active_name else ""
                if name in CARD_DB and "attacks" in CARD_DB[name] and idx < len(CARD_DB[name]["attacks"]):
                    atk_info = CARD_DB[name]["attacks"][idx]
                    if "coin_flips" in atk_info or "coin_flip_plus" in atk_info:
                        is_risky = True

                dmg = calculate_damage(my_active, idx, len(my_bench), opp_active_hp)

                if dmg >= opp_active_hp:
                    if is_risky:
                        risky_lethals.append((aid, dmg))
                    else:
                        guaranteed_lethals.append((aid, dmg))
                elif giovanni and (dmg + 10) >= opp_active_hp:
                    if not is_risky:
                        giovanni_guaranteed.append((giovanni[0][0], dmg))

            # Prioritize: Guaranteed Low Cost > Guaranteed High Cost > Risky Max Damage > Giovanni
            if guaranteed_lethals:
                # Sort by damage ascending (lowest sufficient damage) to save resources like energy discard
                guaranteed_lethals.sort(key=lambda x: x[1])
                return guaranteed_lethals[0][0]

            if risky_lethals:
                # Sort by damage descending (max potential)
                risky_lethals.sort(key=lambda x: x[1], reverse=True)
                return risky_lethals[0][0]

            if giovanni_guaranteed:
                return giovanni_guaranteed[0][0]

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
             # Prioritize EX/Strong
             best_tool_action = acts["attach_tool"][0][0]
             best_tool_score = -1

             for aid, tool_name, pos in acts["attach_tool"]:
                 target = my_active if pos == 0 else (my_bench[pos-1] if pos-1 < len(my_bench) else None)
                 if not target: continue

                 score = 0
                 tname = get_card_name(target).lower()
                 if "ex" in tname: score += 20
                 if pos == 0: score += 10

                 if score > best_tool_score:
                     best_tool_score = score
                     best_tool_action = aid
             return best_tool_action

        if acts["play_supporter"]:
            misty = [a for a in acts["play_supporter"] if "Misty" in a[1]]
            if misty:
                # Identify best water target (Active EX > Bench EX > Active > Bench)
                best_misty = None
                best_score = -1

                # Check Active
                if my_active and "water" in get_energy_type(my_active_name):
                    score = 100 if "ex" in my_active_name.lower() else 50
                    if not needs_energy(my_active): score -= 40
                    for aid, _, target in misty:
                        if target == 0 and score > best_score:
                            best_score = score
                            best_misty = aid

                # Check Bench
                for i, b in enumerate(my_bench):
                    if b and "water" in get_energy_type(get_card_name(b)):
                        score = 80 if "ex" in get_card_name(b).lower() else 40
                        if not needs_energy(b): score -= 30
                        for aid, _, target in misty:
                            if target == i + 1 and score > best_score:
                                best_score = score
                                best_misty = aid

                if best_misty: return best_misty

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

            x_speed = [a for a in acts["play_item"] if "X Speed" in a[1]]
            if x_speed and my_active_hp <= 70:
                # Use X Speed if we want to retreat (implied by low HP)
                return x_speed[0][0]

            pokeball = [a for a in acts["play_item"] if "Ball" in a[1]]
            if pokeball and len(my_bench) < 3: return pokeball[0][0]

            redcard = [a for a in acts["play_item"] if "Red Card" in a[1]]
            if redcard: return redcard[0][0]

            # Any other item (Pokedex, etc)
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
            best_atk = acts["attack"][0][0]
            max_score = -1

            for aid, idx in acts["attack"]:
                d = calculate_damage(my_active, idx, len(my_bench), opp_active_hp)

                # Check effects
                score = d
                if "Asleep" in str(CARD_DB.get(my_active_name.lower(), {}).get("attacks", [{}])[idx].get("text", "")): score += 10
                if "Paralyzed" in str(CARD_DB.get(my_active_name.lower(), {}).get("attacks", [{}])[idx].get("text", "")): score += 20
                if "Confused" in str(CARD_DB.get(my_active_name.lower(), {}).get("attacks", [{}])[idx].get("text", "")): score += 5

                if score > max_score:
                    max_score = score
                    best_atk = aid
            return best_atk

        if acts["end"]: return acts["end"][0]
        return legal_actions[0]

    except Exception as e:
        logging.error(f"Error in play: {e}")
        return legal_actions[0]
