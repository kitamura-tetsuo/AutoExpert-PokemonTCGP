import sys

def update_candidate_player8():
    with open("candidate_player.py", "r") as f:
        content = f.read()

    # Modify the Bench Setup Priority for Venusaur/Exeggutor in attach_energy
    bench_setup_logic_before = """
            # Bench Setup Priority
            if gs.my_active and "exeggutor ex" in gs.my_active.name.lower():
                active_can_attack = False
                for atk in gs.my_active.attacks:
                    if can_use_attack(atk.get("cost", []), gs.my_active.energy):
                        active_can_attack = True
                        break

                if active_can_attack:
                    allows_retreat = a["pos"] == 0 and target.energy_count < target.retreat_cost and (target.energy_count + 1) >= target.retreat_cost
                    if a["pos"] == 0 and not allows_retreat:
                        a["score"] -= 50000
                    elif target and any(n in target.name.lower() for n in ["bulbasaur", "ivysaur", "venusaur ex"]):
                        a["score"] += 15000
                    elif target and any(n in target.name.lower() for n in ["exeggcute"]):
                        if not target.needs_energy():
                            a["score"] -= 50000"""

    bench_setup_logic_after = """
            # Bench Setup Priority
            if gs.my_active and "exeggutor ex" in gs.my_active.name.lower():
                active_can_attack = False
                for atk in gs.my_active.attacks:
                    if can_use_attack(atk.get("cost", []), gs.my_active.energy):
                        active_can_attack = True
                        break

                if active_can_attack:
                    allows_retreat = a["pos"] == 0 and target.energy_count < target.retreat_cost and (target.energy_count + 1) >= target.retreat_cost
                    if a["pos"] == 0 and not allows_retreat:
                        a["score"] -= 50000
                    elif target and any(n in target.name.lower() for n in ["bulbasaur", "ivysaur", "venusaur ex"]):
                        if target.needs_energy():
                             a["score"] += 15000
                    elif target and any(n in target.name.lower() for n in ["exeggcute"]):
                        if not target.needs_energy():
                            a["score"] -= 50000"""

    content = content.replace(bench_setup_logic_before, bench_setup_logic_after)

    with open("candidate_player.py", "w") as f:
        f.write(content)

update_candidate_player8()
