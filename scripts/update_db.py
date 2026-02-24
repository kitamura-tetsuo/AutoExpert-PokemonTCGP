import json
import os

def main():
    try:
        with open("deckgym-core/database.json", "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print("deckgym-core/database.json not found.")
        return

    db = {}
    for entry in data:
        if "Pokemon" in entry:
            p = entry["Pokemon"]
            name = p["name"]
            key = name.lower()

            retreat_cost = len(p.get("retreat_cost", []))

            attacks = []
            for atk in p.get("attacks", []):
                attacks.append({
                    "cost": atk["energy_required"],
                    "dmg": atk.get("fixed_damage", 0),
                    "text": atk.get("effect", ""),
                    "name": atk.get("title", "")
                })

            ability = p.get("ability")

            entry_data = {
                "name": name,
                "hp": p["hp"],
                "energy_type": p["energy_type"],
                "retreat": retreat_cost,
                "attacks": attacks,
                "ability": ability
            }

            # Use the first occurrence (usually base set A1)
            if key not in db:
                db[key] = entry_data

    content = "CARD_DB = " + json.dumps(db, indent=4)
    content = content.replace("null", "None").replace("true", "True").replace("false", "False")

    with open("db_dump.py", "w") as f:
        f.write(content)

    print(f"db_dump.py regenerated with {len(db)} entries.")

if __name__ == "__main__":
    main()
