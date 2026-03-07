from candidate_player import *

class DummyObj:
    def __init__(self):
        pass

state = GameStateWrapper.__new__(GameStateWrapper)
state.my_active = Card("Venusaur ex", DummyObj())

# Wait, the error is argument of type builtins.PyEnergyType is not iterable.
# PyEnergyType is the rust object! Where does python see a PyEnergyType?
# `getattr(obj, "attached_energy", [])` returns a list of PyEnergyType!
# But `Card.energy` is initialized as:
# self.energy = [str(e) for e in getattr(obj, "attached_energy", [])] if obj else []
# So `Card.energy` is always strings!
# Wait, what if the error is when `can_use_attack` receives `energy_provided`?
# In get_opponent_max_damage, there's `available_base = list(current_energy) + list(extra_energy)`
# current_energy is attacker_card.energy (list of strings).
# extra_energy is list of strings.

# Wait, look at `AttachEnergy` action!
# `AttachEnergy(pos, energy_type)`
# The regex parses `energy_type` as string!
# But wait, could there be a place where I call can_use_attack with `gs.my_active.energy` directly?
# Yes, `gs.my_active.energy` is list of strings.
