import deckgym

def main():
    game = deckgym.PyGameState("deckgym-core/example_decks/venusaur-exeggutor.txt", "deckgym-core/example_decks/weezing-arbok.txt", 42)
    b = game.get_bench_pokemon(0)
    print("Length:", len(b))
    for x in b:
        print("Item:", x, type(x))
        if x:
            print("  Name:", getattr(x, 'name', 'NO_NAME'))

if __name__ == "__main__":
    main()
