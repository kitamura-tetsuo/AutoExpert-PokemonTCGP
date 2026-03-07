from deckgym import get_all_cards
cards = get_all_cards()
for c in cards:
    if getattr(c, 'name', '') in ['Exeggcute', 'Exeggutor ex']:
        print("Name:", getattr(c, 'name', 'N/A'))
        print("HP:", getattr(c, 'hp', getattr(c, 'total_hp', 'N/A')))
        print("Energy Type:", getattr(c, 'energy_type', 'N/A'))
        for a in getattr(c, 'attacks', []):
            print("  Attack:", getattr(a, 'title', 'N/A'), "Cost:", getattr(a, 'cost', 'N/A'))
        print("========================")
