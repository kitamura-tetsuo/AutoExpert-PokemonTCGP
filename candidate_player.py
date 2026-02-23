import re
import random
import logging
from db_dump import CARD_DB

# Setup logging
logger = logging.getLogger("player")
if not logger.handlers:
    fh = logging.FileHandler('player.log', mode='w')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logger.addHandler(fh)
    logger.setLevel(logging.INFO)

def play(state, game):
    """
    Advanced Pokemon TCG Pocket Player Strategy
    Implements optimized heuristics, proper name parsing, and strict priority sequences.
    """
    legal_actions = game.legal_actions()
    if not legal_actions:
        return 0

    try:
        # --- 1. Helper Functions ---
        def clean_name(raw_name):
            if not raw_name: return "Unknown"
            if raw_name.startswith("Some(") and raw_name.endswith(")"):
                raw_name = raw_name[5:-1]

            m = re.match(r"^[A-Z0-9]+([A-Z].*)", raw_name)
            if m:
                name_part = m.group(1)
            else:
                name_part = raw_name

            cleaned = re.sub(r"([a-z])([A-Z])", r"\1 \2", name_part)

            key = cleaned.lower()
            if key in CARD_DB:
                return CARD_DB[key].get("name", key.title())

            if key.endswith(" ex"):
                base_key = key[:-3] + "ex"
                if base_key in CARD_DB:
                     return CARD_DB[base_key].get("name", key.title())

            if key + " ex" in CARD_DB:
                return CARD_DB[key + " ex"].get("name", key.title())

            return cleaned

        def get_card_name(card_obj):
            if not card_obj: return "Unknown"
            val = getattr(card_obj, "name", "Unknown")
            return clean_name(str(val)) if val is not None else "Unknown"

        def get_card_hp(card_obj):
            if not card_obj: return 0
            return getattr(card_obj, "remaining_hp", 0)

        def get_card_max_hp(card_obj):
            if not card_obj: return 0
            return getattr(card_obj, "total_hp", 0)

        def get_card_energy(card_obj):
            if not card_obj: return []
            return [str(e) for e in getattr(card_obj, "attached_energy", [])]

        def get_db_card(card_name):
            if not card_name: return None
            key = card_name.lower()
            if key in CARD_DB: return CARD_DB[key]
            for k in CARD_DB:
                if k in key: return CARD_DB[k]
            return None

        def get_energy_type(card_name):
            db_card = get_db_card(card_name)
            if db_card:
                return db_card.get("energy_type", "Colorless")
            n = card_name.lower()
            if "pikachu" in n or "zapdos" in n or "magneton" in n or "voltorb" in n or "electrode" in n or "raichu" in n or "electabuzz" in n or "mareep" in n or "flaaffy" in n or "ampharos" in n or "blitzle" in n or "zebstrika" in n or "joltik" in n or "galvantula" in n or "tynamo" in n or "eelektrik" in n or "eelektross" in n or "stunfisk" in n or "helioptile" in n or "heliolisk" in n or "dedenne" in n or "togedemaru" in n or "zeraora" in n or "yamper" in n or "boltund" in n or "pincurchin" in n or "morpeko" in n or "dracozolt" in n or "regieleki" in n or "pawmi" in n or "pawmo" in n or "pawmot" in n or "bellibolt" in n or "wattrel" in n or "kilowattrel" in n or "tadbulb" in n or "miraidon" in n: return "Lightning"
            if "mewtwo" in n or "gardevoir" in n or "ralts" in n or "kirlia" in n or "abra" in n or "kadabra" in n or "alakazam" in n or "gastly" in n or "haunter" in n or "gengar" in n or "jynx" in n or "mr. mime" in n or "drowzee" in n or "hypno" in n or "exeggcute" in n or "exeggutor" in n or "starmie" in n or "mew" in n or "natu" in n or "xatu" in n or "espeon" in n or "slowpoke" in n or "slowbro" in n or "slowking" in n or "unown" in n or "wobbuffet" in n or "girafarig" in n or "spoink" in n or "grumpig" in n or "lunatone" in n or "solrock" in n or "baltoy" in n or "claydol" in n or "chimecho" in n or "chingling" in n or "bronzor" in n or "bronzong" in n or "mime jr." in n or "gallade" in n or "uxie" in n or "mesprit" in n or "azelf" in n or "cresselia" in n or "woobat" in n or "swoobat" in n or "sigilyph" in n or "gothita" in n or "gothorita" in n or "gothitelle" in n or "solosis" in n or "duosion" in n or "reuniclus" in n or "elgyem" in n or "beheeyem" in n or "litwick" in n or "lampent" in n or "chandelure" in n or "espurr" in n or "meowstic" in n or "honedge" in n or "doublade" in n or "aegislash" in n or "inkay" in n or "malamar" in n or "pumpkaboo" in n or "gourgeist" in n or "sandygast" in n or "palossand" in n or "mimikyu" in n or "dhelmise" in n or "cosmog" in n or "cosmoem" in n or "solgaleo" in n or "lunala" in n or "necrozma" in n or "blacephalon" in n or "indeedee" in n or "dreepy" in n or "drakloak" in n or "dragapult" in n or "calyrex" in n or "wyrdeer" in n or "kleavor" in n or "rabsca" in n or "flittle" in n or "espathra" in n or "greavard" in n or "houndstone" in n: return "Psychic"
            if "charizard" in n or "moltres" in n or "charmander" in n or "charmeleon" in n or "growlithe" in n or "arcanine" in n or "ponyta" in n or "rapidash" in n or "magmar" in n or "vulpix" in n or "ninetales" in n or "flareon" in n or "cyndaquil" in n or "quilava" in n or "typhlosion" in n or "slugma" in n or "magcargo" in n or "houndour" in n or "houndoom" in n or "entei" in n or "ho-oh" in n or "torchic" in n or "combusken" in n or "blaziken" in n or "numel" in n or "camerupt" in n or "torkoal" in n or "chimchar" in n or "monferno" in n or "infernape" in n or "magmortar" in n or "tepig" in n or "pignite" in n or "emboar" in n or "pansear" in n or "simisear" in n or "darumaka" in n or "darmanitan" in n or "litwick" in n or "lampent" in n or "chandelure" in n or "heatmor" in n or "larvesta" in n or "volcarona" in n or "reshiram" in n or "fennekin" in n or "braixen" in n or "delphox" in n or "fletchling" in n or "fletchinder" in n or "talonflame" in n or "litleo" in n or "pyroar" in n or "volcanion" in n or "litten" in n or "torracat" in n or "incineroar" in n or "oricorio" in n or "turtonator" in n or "scorbunny" in n or "raboot" in n or "cinderace" in n or "sizzlipede" in n or "centiskorch" in n or "fuecoco" in n or "crocalor" in n or "skeledirge" in n or "charcadet" in n or "armarouge" in n or "ceruledge" in n or "scovillain" in n or "iron moth" in n or "chi-yu" in n: return "Fire"
            if "blastoise" in n or "starmie" in n or "articuno" in n or "squirtle" in n or "wartortle" in n or "psyduck" in n or "golduck" in n or "poliwag" in n or "poliwhirl" in n or "poliwrath" in n or "tentacool" in n or "tentacruel" in n or "seel" in n or "dewgong" in n or "shellder" in n or "cloyster" in n or "krabby" in n or "kingler" in n or "horsea" in n or "seadra" in n or "goldeen" in n or "seaking" in n or "staryu" in n or "magikarp" in n or "gyarados" in n or "lapras" in n or "vaporeon" in n or "omanyte" in n or "omastar" in n or "kabuto" in n or "kabutops" in n or "totodile" in n or "croconaw" in n or "feraligatr" in n or "chinchou" in n or "lanturn" in n or "marill" in n or "azumarill" in n or "politoed" in n or "wooper" in n or "quagsire" in n or "slowking" in n or "corsola" in n or "remoraid" in n or "octillery" in n or "mantine" in n or "kingdra" in n or "suicune" in n or "mudkip" in n or "marshtomp" in n or "swampert" in n or "lotad" in n or "lombre" in n or "ludicolo" in n or "wingull" in n or "pelipper" in n or "surskit" in n or "masquerain" in n or "carvanha" in n or "sharpedo" in n or "wailmer" in n or "wailord" in n or "barboach" in n or "whiscash" in n or "corphish" in n or "crawdaunt" in n or "feebas" in n or "milotic" in n or "spheal" in n or "sealeo" in n or "walrein" in n or "clamperl" in n or "huntail" in n or "gorebyss" in n or "relicanth" in n or "luvdisc" in n or "kyogre" in n or "piplup" in n or "prinplup" in n or "empoleon" in n or "bibarel" in n or "buizel" in n or "floatzel" in n or "shellos" in n or "gastrodon" in n or "finneon" in n or "lumineon" in n or "mantyke" in n or "snover" in n or "abomasnow" in n or "phione" in n or "manaphy" in n or "oshawott" in n or "dewott" in n or "samurott" in n or "panpour" in n or "simipour" in n or "tympole" in n or "palpitoad" in n or "seismitoad" in n or "basculin" in n or "tirtouga" in n or "carracosta" in n or "ducklett" in n or "swanna" in n or "vanillite" in n or "vanillish" in n or "vanilluxe" in n or "frillish" in n or "jellicent" in n or "alomomola" in n or "cubchoo" in n or "beartic" in n or "cryogonal" in n or "keldeo" in n or "froakie" in n or "frogadier" in n or "greninja" in n or "binacle" in n or "barbaracle" in n or "clauncher" in n or "clawitzer" in n or "bergmite" in n or "avalugg" in n or "volcanion" in n or "popplio" in n or "brionne" in n or "primarina" in n or "wishiwashi" in n or "mareanie" in n or "toxapex" in n or "dewpider" in n or "araquanid" in n or "pyukumuku" in n or "bruxish" in n or "tapu fini" in n or "sobble" in n or "drizzile" in n or "inteleon" in n or "chewtle" in n or "drednaw" in n or "cramorant" in n or "arrokuda" in n or "barraskewda" in n or "snom" in n or "frosmoth" in n or "eiscue" in n or "arctovish" in n or "quaxly" in n or "quaxwell" in n or "quaquaval" in n or "wiglett" in n or "wugtrio" in n or "finizen" in n or "palafin" in n or "veluza" in n or "dondozo" in n or "tatsugiri" in n or "iron bundle" in n or "walking wake" in n or "ogrepon" in n: return "Water"
            if "venusaur" in n or "bulbasaur" in n or "ivysaur" in n or "caterpie" in n or "metapod" in n or "butterfree" in n or "weedle" in n or "kakuna" in n or "beedrill" in n or "ekans" in n or "arbok" in n or "nidoran" in n or "nidorina" in n or "nidoqueen" in n or "nidorino" in n or "nidoking" in n or "zubat" in n or "golbat" in n or "oddish" in n or "gloom" in n or "vileplume" in n or "paras" in n or "parasect" in n or "venonat" in n or "venomoth" in n or "bellsprout" in n or "weepinbell" in n or "victreebel" in n or "exeggcute" in n or "exeggutor" in n or "tangela" in n or "scyther" in n or "pinsir" in n or "chikorita" in n or "bayleef" in n or "meganium" in n or "sentret" in n or "furret" in n or "spinarak" in n or "ariados" in n or "crobat" in n or "hoppip" in n or "skiploom" in n or "jumpluff" in n or "sunkern" in n or "sunflora" in n or "yanma" in n or "pineco" in n or "forretress" in n or "shuckle" in n or "celebi" in n or "treecko" in n or "grovyle" in n or "sceptile" in n or "wurmple" in n or "silcoon" in n or "beautifly" in n or "cascoon" in n or "dustox" in n or "lotad" in n or "lombre" in n or "ludicolo" in n or "seedot" in n or "nuzleaf" in n or "shiftry" in n or "surskit" in n or "masquerain" in n or "shroomish" in n or "breloom" in n or "nincada" in n or "ninjask" in n or "shedinja" in n or "roselia" in n or "cacnea" in n or "cacturne" in n or "tropius" in n or "turtwig" in n or "grotle" in n or "torterra" in n or "kricketot" in n or "kricketune" in n or "budew" in n or "roserade" in n or "burmy" in n or "wormadam" in n or "mothim" in n or "combee" in n or "vespiquen" in n or "cherubi" in n or "cherrim" in n or "carnivine" in n or "snover" in n or "abomasnow" in n or "tangrowth" in n or "leafeon" in n or "shaymin" in n or "snivy" in n or "servine" in n or "serperior" in n or "pansage" in n or "simisage" in n or "sewaddle" in n or "swadloon" in n or "leavanny" in n or "venipede" in n or "whirlipede" in n or "scolipede" in n or "cottonee" in n or "whimsicott" in n or "petilil" in n or "lilligant" in n or "maractus" in n or "dwebble" in n or "crustle" in n or "karrablast" in n or "escavalier" in n or "foongus" in n or "amoonguss" in n or "ferroseed" in n or "ferrothorn" in n or "shelmet" in n or "accelgor" in n or "durant" in n or "virizion" in n or "chespin" in n or "quilladin" in n or "chesnaught" in n or "scatterbug" in n or "spewpa" in n or "vivillon" in n or "skiddo" in n or "gogoat" in n or "phantump" in n or "trevenant" in n or "pumpkaboo" in n or "gourgeist" in n or "rowlet" in n or "dartrix" in n or "decidueye" in n or "grubbin" in n or "charjabug" in n or "vikavolt" in n or "fomantis" in n or "lurantis" in n or "morelull" in n or "shiinotic" in n or "bounsweet" in n or "steenee" in n or "tsareena" in n or "dhelmise" in n or "tapu bulu" in n or "kartana" in n or "grookey" in n or "thwackey" in n or "rillaboom" in n or "gossifleur" in n or "eldegoss" in n or "applin" in n or "flapple" in n or "appletun" in n or "zarude" in n or "calyrex" in n or "kleavor" in n or "sprigatito" in n or "floragato" in n or "meowscarada" in n or "tarountula" in n or "spidops" in n or "nymble" in n or "lokix" in n or "smoliv" in n or "dolliv" in n or "arboliva" in n or "brambleghast" in n or "toedscool" in n or "toedscruel" in n or "capsakid" in n or "scovillain" in n or "rellor" in n or "rabsca" in n or "brute bonnet" in n or "wo-chien" in n or "hydrapple" in n: return "Grass"
            if "machamp" in n or "marowak" in n or "machop" in n or "machoke" in n or "geodude" in n or "graveler" in n or "golem" in n or "onix" in n or "cubone" in n or "hitmonlee" in n or "hitmonchan" in n or "rhyhorn" in n or "rhydon" in n or "sudowoodo" in n or "gligar" in n or "steelix" in n or "shuckle" in n or "heracross" in n or "corsola" in n or "phanpy" in n or "donphan" in n or "tyrogue" in n or "hitmontop" in n or "larvitar" in n or "pupitar" in n or "tyranitar" in n or "nosepass" in n or "meditite" in n or "medicham" in n or "lunatone" in n or "solrock" in n or "barboach" in n or "whiscash" in n or "baltoy" in n or "claydol" in n or "anorith" in n or "armaldo" in n or "regirock" in n or "groudon" in n or "cranidos" in n or "rampardos" in n or "shieldon" in n or "bastiodon" in n or "bonsly" in n or "riolu" in n or "lucario" in n or "hippopotas" in n or "hippowdon" in n or "rhyperior" in n or "gliscor" in n or "probopass" in n or "gallade" in n or "roggenrola" in n or "boldore" in n or "gigalith" in n or "drilbur" in n or "excadrill" in n or "timburr" in n or "gurdurr" in n or "conkeldurr" in n or "tympole" in n or "palpitoad" in n or "seismitoad" in n or "throh" in n or "sawk" in n or "sandile" in n or "krokorok" in n or "krookodile" in n or "dwebble" in n or "crustle" in n or "scraggy" in n or "scrafty" in n or "archen" in n or "archeops" in n or "stunfisk" in n or "mienfoo" in n or "mienshao" in n or "golett" in n or "golurk" in n or "terrakion" in n or "landorus" in n or "bunnelby" in n or "diggersby" in n or "pancham" in n or "pangoro" in n or "binacle" in n or "barbaracle" in n or "hawlucha" in n or "carbink" in n or "zygarde" in n or "rockruff" in n or "lycanroc" in n or "mudbray" in n or "mudsdale" in n or "minior" in n or "passimian" in n or "sandygast" in n or "palossand" in n or "crabrawler" in n or "crabominable" in n or "stakataka" in n or "clobbopus" in n or "grapploct" in n or "falinks" in n or "stonjourner" in n or "kubfu" in n or "urshifu" in n or "kleavor" in n or "ursaluna" in n or "sneasler" in n or "great tusk" in n or "scream tail" in n or "sandy shocks" in n or "iron hands" in n or "iron treads" in n or "iron valiant" in n or "koraidon" in n or "ting-lu" in n or "okidogi" in n: return "Fighting"
            if "weezing" in n or "muk" in n or "grimer" in n or "koffing" in n or "ekans" in n or "arbok" in n or "nidoran" in n or "nidorina" in n or "nidoqueen" in n or "nidorino" in n or "nidoking" in n or "zubat" in n or "golbat" in n or "gastly" in n or "haunter" in n or "gengar" in n or "spinarak" in n or "ariados" in n or "crobat" in n or "umbreon" in n or "murkrow" in n or "misdreavus" in n or "sneasel" in n or "houndour" in n or "houndoom" in n or "tyranitar" in n or "poochyena" in n or "mightyena" in n or "sableye" in n or "carvanha" in n or "sharpedo" in n or "cacnea" in n or "cacturne" in n or "seviper" in n or "corphish" in n or "crawdaunt" in n or "shuppet" in n or "banette" in n or "duskull" in n or "dusclops" in n or "absol" in n or "drifloon" in n or "drifblim" in n or "mismagius" in n or "honchkrow" in n or "stunky" in n or "skuntank" in n or "spiritomb" in n or "skorupi" in n or "drapion" in n or "croagunk" in n or "toxicroak" in n or "weavile" in n or "darkrai" in n or "purrloin" in n or "liepard" in n or "venipede" in n or "whirlipede" in n or "scolipede" in n or "sandile" in n or "krokorok" in n or "krookodile" in n or "scraggy" in n or "scrafty" in n or "yamask" in n or "cofagrigus" in n or "trubbish" in n or "garbodor" in n or "zorua" in n or "zoroark" in n or "pawniard" in n or "bisharp" in n or "vullaby" in n or "mandibuzz" in n or "deino" in n or "zweilous" in n or "hydreigon" in n or "greninja" in n or "pangoro" in n or "inkay" in n or "malamar" in n or "yveltal" in n or "incineroar" in n or "grimer" in n or "muk" in n or "rattata" in n or "raticate" in n or "meowth" in n or "persian" in n or "sandshrew" in n or "sandslash" in n or "vulpix" in n or "ninetales" in n or "diglett" in n or "dugtrio" in n or "geodude" in n or "graveler" in n or "golem" in n or "marowak" in n or "raichu" in n or "exeggutor" in n or "marowak" in n or "silvally" in n or "guzzlord" in n or "poipole" in n or "naganadel" in n or "stakataka" in n or "blacephalon" in n or "nickit" in n or "thievul" in n or "impidimp" in n or "morgrem" in n or "grimmsnarl" in n or "obstagoon" in n or "perrserker" in n or "cursola" in n or "sirfetch'd" in n or "mr. rime" in n or "runerigus" in n or "morpeko" in n or "zarude" in n or "regidrago" in n or "urshifu" in n or "calyrex" in n or "wyrdeer" in n or "kleavor" in n or "ursaluna" in n or "basculegion" in n or "sneasler" in n or "overqwil" in n or "enamorus" in n or "lokix" in n or "brambleghast" in n or "toedscool" in n or "toedscruel" in n or "kingambit" in n or "brute bonnet" in n or "flutter mane" in n or "slither wing" in n or "sandy shocks" in n or "iron treads" in n or "iron bundle" in n or "iron hands" in n or "iron jugulis" in n or "iron moth" in n or "iron thorns" in n or "wo-chien" in n or "chien-pao" in n or "ting-lu" in n or "chi-yu" in n or "roaring moon" in n or "iron valiant" in n or "walking wake" in n or "iron leaves" in n or "dipplin" in n or "poltchageist" in n or "sinistcha" in n or "okidogi" in n or "munkidori" in n or "fezandipiti" in n or "ogrepon" in n: return "Darkness"
            if "melmetal" in n or "meltan" in n or "magnemite" in n or "magneton" in n or "forretress" in n or "steelix" in n or "scizor" in n or "skarmory" in n or "mawile" in n or "aron" in n or "lairon" in n or "aggron" in n or "beldum" in n or "metang" in n or "metagross" in n or "registeel" in n or "jirachi" in n or "empoleon" in n or "shieldon" in n or "bastiodon" in n or "bronzor" in n or "bronzong" in n or "lucario" in n or "magnezone" in n or "probopass" in n or "dialga" in n or "heatran" in n or "excadrill" in n or "escavalier" in n or "ferroseed" in n or "ferrothorn" in n or "klink" in n or "klang" in n or "klinklang" in n or "pawniard" in n or "bisharp" in n or "durant" in n or "cobalion" in n or "genesect" in n or "honedge" in n or "doublade" in n or "aegislash" in n or "klefki" in n or "solgaleo" in n or "celesteela" in n or "kartana" in n or "magearna" in n or "stakataka" in n or "meltan" in n or "melmetal" in n or "corviknight" in n or "perrserker" in n or "cufant" in n or "copperajah" in n or "duraludon" in n or "zacian" in n or "zamazenta" in n or "eternatus" in n or "regieleki" in n or "regidrago" in n or "glastrier" in n or "spectrier" in n or "calyrex" in n or "wyrdeer" in n or "kleavor" in n or "ursaluna" in n or "basculegion" in n or "sneasler" in n or "overqwil" in n or "enamorus" in n or "tinkatink" in n or "tinkatuff" in n or "tinkaton" in n or "varoom" in n or "revavroom" in n or "orthworm" in n or "gholdengo" in n or "kingambit" in n or "great tusk" in n or "scream tail" in n or "brute bonnet" in n or "flutter mane" in n or "slither wing" in n or "sandy shocks" in n or "iron treads" in n or "iron bundle" in n or "iron hands" in n or "iron jugulis" in n or "iron moth" in n or "iron thorns" in n or "roaring moon" in n or "iron valiant" in n or "walking wake" in n or "iron leaves" in n or "dipplin" in n or "poltchageist" in n or "sinistcha" in n or "okidogi" in n or "munkidori" in n or "fezandipiti" in n or "ogrepon" in n: return "Metal"
            return "Colorless"

        def get_attacks(card_name):
            db_card = get_db_card(card_name)
            if db_card:
                return db_card.get("attacks", [])
            return []

        # --- 2. Parse State ---
        me = state.current_player
        opp = 1 - me

        my_active = state.get_active_pokemon(me)
        my_bench_raw = state.get_bench_pokemon(me)
        my_bench = [b for b in my_bench_raw if b is not None]
        my_hand = state.get_hand(me)

        opp_active = state.get_active_pokemon(opp)
        opp_bench_raw = state.get_bench_pokemon(opp)
        opp_bench = [b for b in opp_bench_raw if b is not None]
        opp_bench_count = len(opp_bench)
        opp_hand = state.get_hand(opp)
        opp_hand_count = len(opp_hand)

        opp_active_hp = get_card_hp(opp_active) if opp_active else 0
        opp_energy_count = len(get_card_energy(opp_active)) if opp_active else 0

        my_active_name = get_card_name(my_active)
        my_active_energy = len(get_card_energy(my_active))

        # --- 3. Damage Calculation Logic ---
        def calculate_damage(attacker_card, attack_idx, my_bench_list, opp_active_c, opp_b_count, opp_e_count):
            name = get_card_name(attacker_card)
            n_lower = name.lower()
            my_bench_len = len([b for b in my_bench_list if b])

            # Special Hardcoded Logic for scaling attacks
            if "pikachu ex" in n_lower and attack_idx == 0:
                lightning_bench = 0
                for b in my_bench_list:
                    if b:
                        b_name = get_card_name(b)
                        if "lightning" in get_energy_type(b_name).lower(): lightning_bench += 1
                return 30 * lightning_bench

            if "mewtwo ex" in n_lower:
                if attack_idx == 0: return 50
                if attack_idx == 1: return 150

            if "starmie ex" in n_lower and attack_idx == 0: return 90

            if "articuno ex" in n_lower:
                if attack_idx == 0: return 40
                if attack_idx == 1: return 80

            if "moltres ex" in n_lower and attack_idx == 1: return 70

            if "zapdos ex" in n_lower and attack_idx == 1:
                return 100

            if "marowak ex" in n_lower and attack_idx == 0:
                return 80

            if "greninja" in n_lower and "ex" not in n_lower and attack_idx == 0: return 60

            if "cinccino" in n_lower and attack_idx == 0: return 30 * my_bench_len

            if "indeedee ex" in n_lower and attack_idx == 0: return 30 + (30 * opp_e_count)

            if "gardevoir" in n_lower and "ex" not in n_lower and attack_idx == 0: return 60

            # DB Logic Fallback
            attacks = get_attacks(name)
            damage = 0
            if attack_idx < len(attacks):
                atk = attacks[attack_idx]
                damage = atk.get("dmg", 0)
                text_val = atk.get("text")
                text = text_val.lower() if text_val else ""

                if "damage for each" in text:
                    multiplier = 0
                    m = re.search(r"(\d+) damage for each", text)
                    if m: multiplier = int(m.group(1))
                    else: multiplier = 20

                    if "benched" in text:
                        if "opponent" in text: damage += (multiplier * opp_b_count)
                        else: damage += (multiplier * my_bench_len)
                    elif "energy" in text: damage += (multiplier * opp_e_count)
                elif "more damage" in text:
                    m = re.search(r"(\d+) more damage", text)
                    if m: damage += int(m.group(1))
                    else: damage += 40
                elif "coin" in text and "heads" in text:
                     m = re.search(r"(\d+) damage for each heads", text)
                     if m:
                         num_coins = atk.get("coin_flips", 1)
                         damage = int(num_coins * int(m.group(1)) * 0.5)

            return damage

        # --- 4. Needs Energy Logic ---
        def needs_energy(card_obj):
            if not card_obj: return False
            name = get_card_name(card_obj).lower()
            current_energy = len(get_card_energy(card_obj))

            if "mewtwo ex" in name: return current_energy < 4
            if "charizard ex" in name: return current_energy < 4
            if "venusaur ex" in name: return current_energy < 4
            if "blastoise ex" in name: return current_energy < 3
            if "pikachu ex" in name: return current_energy < 2
            if "starmie ex" in name: return current_energy < 2
            if "marowak ex" in name: return current_energy < 2
            if "articuno ex" in name: return current_energy < 3
            if "moltres ex" in name: return current_energy < 3
            if "zapdos ex" in name: return current_energy < 3
            if "greninja" in name and "ex" not in name: return current_energy < 2
            if "gardevoir" in name: return current_energy < 3

            attacks = get_attacks(name)
            max_cost = 0
            for atk in attacks:
                c = len(atk.get("cost", []))
                if c > max_cost: max_cost = c

            if max_cost == 0: return False
            return current_energy < max_cost

        # --- 5. Action Parsing & Categorization ---
        parsed_actions = []

        # STRICT PRIORITY SYSTEM
        LETHAL_WIN_SCORE = 1000000

        SETUP_EVOLVE_SCORE = 22000
        SETUP_PLACE_SCORE = 21000 # Restored to Standard
        SETUP_PLACE_URGENT_SCORE = 100000 # Donk prevention
        SETUP_ITEM_SCORE = 20000
        SETUP_ABILITY_SCORE = 19000
        SETUP_ATTACH_SCORE = 18000
        SETUP_SUPPORTER_SCORE = 14000

        LETHAL_KO_SCORE = 10000
        ATTACK_BASE_SCORE = 1000

        RETREAT_SCORE = -5000
        END_TURN_SCORE = -10000

        for aid in legal_actions:
            aname = game.action_name(aid)
            details = {"id": aid, "name": aname, "type": "unknown", "score": 0}

            m_attack = re.match(r"Attack\((\d+)\)", aname)
            m_attach_energy = re.match(r"AttachEnergy\((\d+), (.*?)\)", aname)
            m_attach_simple = re.match(r"Attach\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
            m_attach_tool = re.match(r"AttachTool\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
            m_place = re.match(r"Place\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
            m_play_pokemon = re.match(r"PlayPokemon\((\d+), (\d+)\)", aname)
            m_evolve = re.match(r"Evolve\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
            m_retreat = re.match(r"Retreat\((\d+)\)", aname)
            m_activate = re.match(r"Activate\((\d+)\)", aname)
            m_discard = re.match(r"DiscardOwnCard\((?:Some\()?(.*?)\)?\)", aname)

            if aname == "EndTurn":
                details["type"] = "end"
                details["score"] = END_TURN_SCORE

            elif m_attack:
                idx = int(m_attack.group(1))
                details["type"] = "attack"
                details["idx"] = idx
                dmg = 0
                if my_active:
                     dmg = calculate_damage(my_active, idx, my_bench, opp_active, opp_bench_count, opp_energy_count)
                details["damage"] = dmg
                details["score"] = ATTACK_BASE_SCORE + (dmg * 10)

                if opp_active_hp > 0 and dmg >= opp_active_hp:
                    details["score"] = LETHAL_KO_SCORE + 5000 - dmg
                    details["can_ko"] = True
                    if opp_bench_count == 0:
                        details["score"] = LETHAL_WIN_SCORE
                        details["is_lethal"] = True
                    elif state.points[me] + 1 >= 3:
                         details["score"] = LETHAL_WIN_SCORE
                         details["is_lethal"] = True

            elif m_attach_tool:
                details["type"] = "tool"
                details["card_name"] = clean_name(m_attach_tool.group(1))
                details["pos"] = int(m_attach_tool.group(2))
                details["score"] = SETUP_ITEM_SCORE

            elif m_attach_energy:
                 pos = int(m_attach_energy.group(1))
                 etype = m_attach_energy.group(2)
                 details["type"] = "attach_energy"
                 details["pos"] = pos
                 details["energy_type"] = etype
                 details["score"] = SETUP_ATTACH_SCORE

            elif m_attach_simple and "Energy" in aname:
                 obj = m_attach_simple.group(1)
                 pos = int(m_attach_simple.group(2))
                 details["type"] = "attach_energy"
                 details["pos"] = pos
                 details["energy_type"] = clean_name(obj)
                 details["score"] = SETUP_ATTACH_SCORE

            elif m_place:
                 card_name = clean_name(m_place.group(1))
                 pos = int(m_place.group(2))
                 details["type"] = "place"
                 details["card_name"] = card_name
                 details["pos"] = pos
                 details["score"] = SETUP_PLACE_SCORE

            elif m_play_pokemon:
                 details["type"] = "place"
                 details["pos"] = int(m_play_pokemon.group(2))
                 details["score"] = SETUP_PLACE_SCORE
                 h_idx = int(m_play_pokemon.group(1))
                 if h_idx < len(my_hand):
                     details["card_name"] = get_card_name(my_hand[h_idx])

            elif m_evolve:
                card_name = clean_name(m_evolve.group(1))
                pos = int(m_evolve.group(2))
                details["type"] = "evolve"
                details["card_name"] = card_name
                details["pos"] = pos
                details["score"] = SETUP_EVOLVE_SCORE
                if pos == 0: details["score"] += 500

            elif "UseSupporter" in aname or ("Play" in aname and not "Pokemon" in aname):
                is_supporter = False
                supporters = ["Research", "Professor", "Sabrina", "Giovanni", "Erika", "Misty", "Blaine", "Koga", "Lt. Surge", "Brock", "Copycat", "Lisia", "Cyrus", "Mars", "Red", "Guzma", "Judge", "Acerola", "Hau", "Bill", "Pokemon Center Lady", "Pokémon Center Lady", "Ilima"]
                sname = ""
                for s in supporters:
                    if s in aname:
                        sname = s
                        is_supporter = True
                        break

                if is_supporter:
                    details["type"] = "supporter"
                    details["supporter_name"] = sname
                    details["score"] = SETUP_SUPPORTER_SCORE
                else:
                    details["type"] = "item"
                    details["score"] = SETUP_ITEM_SCORE
                    m_play_item = re.match(r"Play\((?:Some\()?(.*?)\)?\)", aname)
                    if m_play_item:
                        details["item_name"] = clean_name(m_play_item.group(1))

            elif m_retreat:
                details["type"] = "retreat"
                details["target_pos"] = int(m_retreat.group(1))
                details["score"] = RETREAT_SCORE

            elif m_activate:
                details["type"] = "activate"
                details["target_pos"] = int(m_activate.group(1))
                details["score"] = SETUP_ABILITY_SCORE
                if details["target_pos"] == 0:
                    details["ability_card"] = my_active_name
                elif details["target_pos"] > 0 and details["target_pos"] <= len(my_bench_raw):
                    details["ability_card"] = get_card_name(my_bench_raw[details["target_pos"]-1])

            elif "ApplyDamage" in aname:
                 details["type"] = "damage_resolution"
                 details["score"] = LETHAL_WIN_SCORE

            elif "UseAbility" in aname:
                details["type"] = "ability"
                details["score"] = SETUP_ABILITY_SCORE
                m_use = re.match(r"UseAbility\((?:Some\()?(.*?)\)?\)", aname)
                if m_use:
                    details["ability_card"] = clean_name(m_use.group(1))

            elif m_discard:
                details["type"] = "discard"
                details["card_name"] = clean_name(m_discard.group(1))
                details["score"] = 0

            parsed_actions.append(details)

        # --- 6. Refined Scoring Logic ---

        # Pre-calc context
        has_lethal_attack = any(a.get("is_lethal") for a in parsed_actions if a["type"] == "attack")
        has_ko_attack = any(a.get("can_ko") for a in parsed_actions if a["type"] == "attack")

        # Donk Prevention
        if len(my_bench) == 0:
            for a in parsed_actions:
                if a["type"] == "place":
                    a["score"] = SETUP_PLACE_URGENT_SCORE

        # Determine lethal bencher exists for coordinated switch
        best_bench_damage = 0
        lethal_bencher_exists = False
        lethal_bencher_idx = -1
        active_damage = 0
        if my_active:
             a_attacks = get_attacks(my_active_name)
             for i in range(len(a_attacks)):
                  if my_active_energy >= len(a_attacks[i].get("cost", [])):
                       d = calculate_damage(my_active, i, my_bench, opp_active, opp_bench_count, opp_energy_count)
                       if d > active_damage: active_damage = d

        for b_idx, b_card in enumerate(my_bench_raw):
            if b_card:
                b_name = get_card_name(b_card)
                b_attacks = get_attacks(b_name)
                b_energy = len(get_card_energy(b_card))
                b_max_dmg = 0
                for i in range(len(b_attacks)):
                    cost = len(b_attacks[i].get("cost", []))
                    if b_energy >= cost:
                        d = calculate_damage(b_card, i, my_bench, opp_active, opp_bench_count, opp_energy_count)
                        if d > b_max_dmg: b_max_dmg = d

                if b_max_dmg > best_bench_damage:
                    best_bench_damage = b_max_dmg
                    if opp_active_hp > 0 and best_bench_damage >= opp_active_hp:
                         lethal_bencher_exists = True
                         lethal_bencher_idx = b_idx + 1

        # Check if we have a Switch Item available
        has_switch_action = any(a.get("is_switch_item") for a in parsed_actions)

        # Giovanni Logic Check
        has_giovanni = False
        gio_action = None
        for a in parsed_actions:
             if a["type"] == "supporter" and "Giovanni" in a.get("supporter_name", ""):
                  has_giovanni = True
                  gio_action = a
                  break

        if has_giovanni:
             # Check if Giovanni makes any attack lethal
             for a in parsed_actions:
                  if a["type"] == "attack":
                       dmg = a.get("damage", 0)
                       if opp_active_hp > 0 and dmg < opp_active_hp and (dmg + 10) >= opp_active_hp:
                            # Giovanni creates lethal!
                            gio_action["score"] = 22500 # Very high priority
                            if opp_bench_count == 0 or state.points[me] + 1 >= 3:
                                gio_action["score"] = LETHAL_WIN_SCORE

        for a in parsed_actions:
            if a["type"] == "attach_energy":
                pos = a.get("pos", -1)
                target_card = None
                if pos == 0: target_card = my_active
                elif pos > 0 and pos <= len(my_bench_raw): target_card = my_bench_raw[pos-1]

                if target_card:
                    cname = get_card_name(target_card)
                    ctype = get_energy_type(cname)
                    etype = a.get("energy_type", "")

                    if needs_energy(target_card):
                         if pos == 0: a["score"] += 800
                         else: a["score"] += 500

                    if ctype in etype or etype in ctype:
                         a["score"] += 200

                    if not needs_energy(target_card):
                         a["score"] -= 500

                    # Coordinated Switch Logic: Only if we HAVE a switch card and a lethal bencher
                    if lethal_bencher_exists and has_switch_action:
                         if pos == 0:
                             a["score"] -= 2000
                         elif pos == lethal_bencher_idx:
                             a["score"] += 2000
                else:
                    a["score"] -= 1000

            if a["type"] == "supporter":
                sname = a.get("supporter_name", "")
                if "Research" in sname or "Professor" in sname:
                    if len(my_hand) < 8: a["score"] = 18800
                    else: a["score"] -= 1000
                elif "Sabrina" in sname:
                    if opp_active and opp_energy_count >= 2: a["score"] += 500
                    if opp_active_hp > 0 and opp_active_hp <= 60: a["score"] -= 8000
                elif "Misty" in sname:
                    needs_water = False
                    if "Water" in get_energy_type(my_active_name) and needs_energy(my_active): needs_water = True
                    for b in my_bench:
                         if "Water" in get_energy_type(get_card_name(b)) and needs_energy(b): needs_water = True

                    if needs_water:
                        a["score"] = 19500
                    else:
                        a["score"] -= 500

            if a["type"] == "item":
                iname = a.get("item_name", a["name"])
                if "Potion" in iname or "Heal" in iname:
                     if my_active and get_card_hp(my_active) <= get_card_max_hp(my_active) - 20:
                         a["score"] += 500
                     else:
                         a["score"] = -500
                elif "Red Card" in iname:
                     if opp_hand_count >= 3: a["score"] += 500
                     else: a["score"] -= 10000
                elif "Switch" in iname or "Escape" in iname or "Speed" in iname:
                     a["score"] = -1000
                     a["is_switch_item"] = True

            if a["type"] == "activate" or a["type"] == "ability":
                card = a.get("ability_card", "")
                if "Gardevoir" in card:
                    a["score"] = -1000
                else:
                    a["score"] = SETUP_ABILITY_SCORE

            if a["type"] == "discard":
                cname = a.get("card_name", "Unknown").lower()
                if "ex" in cname: a["score"] -= 1000
                elif "research" in cname or "gio" in cname or "sabrina" in cname: a["score"] -= 500
                elif "energy" in cname: a["score"] += 100
                else: a["score"] += 200

            if a["type"] == "place":
                card_name = a.get("card_name", "")
                if card_name:
                     if my_active:
                         aname = get_card_name(my_active)
                         atype = get_energy_type(aname)
                         ctype = get_energy_type(card_name)
                         if atype == ctype: a["score"] += 1000

                     if "ex" in card_name.lower(): a["score"] += 200

        for action in parsed_actions:
            # Smart Switch Item
            if action.get("is_switch_item"):
                if lethal_bencher_exists:
                    if opp_bench_count == 0 or state.points[me] + 1 >= 3:
                        action["score"] = LETHAL_WIN_SCORE
                    else:
                        action["score"] = 15000
                elif active_damage == 0 and best_bench_damage >= 40:
                    action["score"] = 14500
                elif my_active and get_card_hp(my_active) <= 40 and best_bench_damage > 0:
                    action["score"] = 14500

            # Retreat Logic
            if action["type"] == "retreat":
                if my_active and get_card_hp(my_active) <= 40 and len(my_bench) > 0:
                     if action["score"] < 14500: action["score"] = 14500

                target_pos = action.get("target_pos", -1)
                if target_pos >= 0 and target_pos < len(my_bench_raw):
                    target_mon = my_bench_raw[target_pos]
                    if target_mon:
                        t_name = get_card_name(target_mon)
                        t_attacks = get_attacks(t_name)
                        t_energy = len(get_card_energy(target_mon))
                        max_dmg = 0
                        for i in range(len(t_attacks)):
                            cost = len(t_attacks[i].get("cost", []))
                            if t_energy >= cost:
                                d = calculate_damage(target_mon, i, my_bench, opp_active, opp_bench_count, opp_energy_count)
                                if d > max_dmg: max_dmg = d

                        if opp_active_hp > 0 and max_dmg >= opp_active_hp:
                             if opp_bench_count == 0:
                                 action["score"] = LETHAL_WIN_SCORE
                             elif not has_ko_attack:
                                 action["score"] = 14500
                        elif active_damage < 40 and max_dmg >= (active_damage + 40):
                             if action["score"] < 14000: action["score"] = 14000

        # Mewtwo ex penalty
        mewtwo_attacks = [a for a in parsed_actions if a["type"] == "attack" and "mewtwo ex" in my_active_name.lower()]
        psydrive = next((a for a in mewtwo_attacks if a["idx"] == 1), None)
        standard = next((a for a in mewtwo_attacks if a["idx"] == 0), None)

        if psydrive and standard and standard.get("is_lethal"):
             psydrive["score"] = -2000

        # --- 7. Selection ---
        best_score = -float('inf')
        best_action_id = legal_actions[0]

        for action in parsed_actions:
            if action["score"] > best_score:
                best_score = action["score"]
                best_action_id = action["id"]

        logger.debug(f"Turn: {state.turn if hasattr(state, 'turn') else '?'} | Player: {me}")
        for a in parsed_actions:
            if a["score"] > -5000:
                 logger.debug(f"Action: {a['name']} | Type: {a['type']} | Score: {a['score']}")
        logger.debug(f"Selected: {game.action_name(best_action_id)}")

        return best_action_id

    except Exception as e:
        logger.error(f"Error in play: {e}")
        # traceback.print_exc()
        return legal_actions[0]
