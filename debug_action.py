import deckgym
from deckgym import get_all_cards

game = deckgym.PyGameState("deckgym-core/example_decks/venusaur-exeggutor.txt", "deckgym-core/example_decks/weezing-arbok.txt")
game.reset()

state = game.get_state()
for _ in range(10):
    if game.legal_actions():
        game.step(game.legal_actions()[0])

state = game.get_state()
c = state.get_active_pokemon(0)
if c:
    e = getattr(c, "energy_type", None)
    print("energy_type enum type is:", type(e))
    print("energy_type repr is:", repr(e))
    energies = getattr(c, "attached_energy", [])
    print("energies enum type:", [type(e) for e in energies])
