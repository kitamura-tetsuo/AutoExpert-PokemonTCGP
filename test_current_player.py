import deckgym
game = deckgym.PyGameState("deckgym-core/example_decks/venusaur-exeggutor.txt", "deckgym-core/example_decks/weezing-arbok.txt", 9)
for i in range(100):
    legal = game.legal_actions()
    if not legal: break
    cp = game.current_player()
    obs = game.encode_observation(cp)
    # just do random
    action = legal[0]
    game.step(action)
