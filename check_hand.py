import deckgym
import random

def test():
    # Need a deck file. I can use one from train_data
    deck_a = "train_data/22336bc3.txt"
    deck_b = "train_data/d4735d04.txt"
    try:
        game = deckgym.PyGameState(deck_a, deck_b, 42)
        state = game.get_state()
        hand = state.get_hand(0)
        if hand:
            c = hand[0]
            print(f"Card: {c.name}")
            print(f"Has hp: {hasattr(c, 'hp')}")
            print(f"Has total_hp: {hasattr(c, 'total_hp')}")
            print(f"Has id: {hasattr(c, 'id')}")
            if hasattr(c, 'id'): print(f"ID: {c.id}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
