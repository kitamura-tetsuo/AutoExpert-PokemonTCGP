import deckgym

def main():
    game = deckgym.PyGameState("deckgym-core/example_decks/venusaur-exeggutor.txt", "deckgym-core/example_decks/weezing-arbok.txt", 42)

    # We want to artificially setup Venusaur ex vs something and test Attack(1).
    # Since we can't easily script a specific state, let's just inspect the Rust code if possible,
    # or let's use the DB dump to see if Giant Bloom is implemented.
    print("Test ready.")

if __name__ == "__main__":
    main()
