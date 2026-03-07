import deckgym

def main():
    game = deckgym.PyGameState("deckgym-core/example_decks/venusaur-exeggutor.txt", "deckgym-core/example_decks/weezing-arbok.txt", 42)

    actions = []

    # We want to see if `legal_actions` actually includes Attack(1) and what it does.
    # It's hard to force Venusaur into the active slot with 4 energy without a custom setup.
    # Let's inspect Rust code instead of trying to run a full game trace.
    print("Script ran.")

if __name__ == "__main__":
    main()
