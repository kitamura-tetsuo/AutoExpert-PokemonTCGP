import deckgym
def main():
    game = deckgym.PyGameState("deckgym-core/example_decks/venusaur-exeggutor.txt", "deckgym-core/example_decks/weezing-arbok.txt", 42)
    s = game.get_state()
    h = s.get_hand(0)
    for c in h:
        if hasattr(c, "energy_type"):
            print("energy_type:", c.energy_type)
            print("str:", str(c.energy_type))
            print("repr:", repr(c.energy_type))
            break
if __name__ == "__main__":
    main()
