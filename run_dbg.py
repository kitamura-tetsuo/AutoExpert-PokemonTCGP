import deckgym
import candidate_player

def test():
    game = deckgym.PyGameState("train_data/b7162a87.txt", "train_data/4ff0d50e.txt", 1234)
    step = 0
    while not game.get_state().is_game_over() and step < 50:
        state = game.get_state()
        if state.current_player == 0:
            act = candidate_player.play(state, game)
        else:
            act = game.legal_actions()[0]
        game.step_with_id(act)
        step += 1
    print("Execution completed successfully without errors!")
test()
