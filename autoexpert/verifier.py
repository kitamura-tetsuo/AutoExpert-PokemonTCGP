import deckgym
import traceback
import sys
import io
from typing import Dict, Any, Optional, Tuple, Callable
from autoexpert.env import PokemonEnv
from autoexpert.config import settings

class Verifier:
    def __init__(self, deck_a: str, deck_b: str):
        self.deck_a = deck_a
        self.deck_b = deck_b

    def verify(self, code: str, num_simulations: int = settings.NUM_SIMULATIONS) -> Dict[str, Any]:
        """
        Executes the provided code, runs simulations, and returns results.
        Expected code format:
        def play(state, game):
            ...
            return action_id
        """
        results = {
            "success": False,
            "win_rate": 0.0,
            "error": None,
            "total_games": num_simulations,
            "wins": 0
        }

        # Step 1: Parse and execute code
        try:
            local_vars = {}
            exec(code, {"deckgym": deckgym}, local_vars)
            if "play" not in local_vars:
                raise ValueError("Generated code does not contain a 'play' function.")
            play_func = local_vars["play"]
        except Exception:
            results["error"] = traceback.format_exc()
            return results

        # Step 2: Run simulations
        try:
            env = PokemonEnv(self.deck_a, self.deck_b)
            wins = 0
            for i in range(num_simulations):
                # We can use a different seed for each game
                env.seed = i 
                win = env.play_game(play_func)
                if win:
                    wins += 1
            
            results["wins"] = wins
            results["win_rate"] = wins / num_simulations
            results["success"] = True
        except Exception:
            results["error"] = traceback.format_exc()
            results["success"] = False

        return results
