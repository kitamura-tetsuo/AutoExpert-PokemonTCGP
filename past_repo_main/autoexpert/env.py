import deckgym
from pathlib import Path
from typing import List, Union, Optional, Tuple, Callable
from autoexpert.utils.game_utils import state_to_text, get_legal_actions_text

class PokemonEnv:
    def __init__(self, deck_a_path: Union[str, Path], deck_b_path: Union[str, Path], seed: Optional[int] = None):
        self.deck_a_path = str(deck_a_path)
        self.deck_b_path = str(deck_b_path)
        self.seed = seed
        self.game = deckgym.PyGameState(self.deck_a_path, self.deck_b_path, self.seed)
        self.reset()

    def reset(self):
        self.game.reset()
        return self.get_observation()

    def get_observation(self) -> Tuple[str, List[int]]:
        state = self.game.get_state()
        state_text = state_to_text(state)
        legal_actions = self.game.legal_actions()
        return state_text, legal_actions

    def step(self, action_id: int) -> Tuple[bool, bool]:
        """Returns (done, won_flag)"""
        done, won = self.game.step_with_id(action_id)
        return done, won

    def play_game(self, player_func: Callable[[deckgym.State, deckgym.PyGameState], int]) -> bool:
        """Plays a full game using the provided player function. Returns True if Player 0 wins."""
        self.reset()
        done = False
        won = False
        while not done:
            state = self.game.get_state()
            # Player 0 uses our expert function
            if state.current_player == 0:
                try:
                    action = player_func(state, self.game)
                    done, won = self.step(action)
                except Exception as e:
                    # If expert fails, we might want to record the error
                    raise e
            else:
                # Player 1 uses random action (or another strategy) for now
                # We can extend this to play against different player types
                actions = self.game.legal_actions()
                import random
                action = random.choice(actions)
                done, _ = self.step(action)

        return won
