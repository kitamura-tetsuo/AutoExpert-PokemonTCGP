import json
from deckgym import PyGameState
from candidate_player import play, GameStateWrapper

def main():
    gs = PyGameState("deckgym-core/example_decks/venusaur-exeggutor.txt", "deckgym-core/example_decks/weezing-arbok.txt")

    try:
        print(f"Action 37753 is: {gs.action_name(37753)}")
    except Exception as e:
        print(e)

    try:
        print(f"Action 713 is: {gs.action_name(713)}")
    except Exception as e:
        pass

if __name__ == "__main__":
    main()
