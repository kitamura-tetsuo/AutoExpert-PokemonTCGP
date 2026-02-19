import time
from typing import Optional
from autoexpert.config import settings
from autoexpert.env import PokemonEnv
from autoexpert.skill_library import SkillLibrary
from autoexpert.curriculum import Curriculum
from autoexpert.code_generator import CodeGenerator
from autoexpert.verifier import Verifier
from autoexpert.utils.llm_client import client

class AutoExpert:
    def __init__(self, deck_a: str, deck_b: str):
        self.deck_a = deck_a
        self.deck_b = deck_b
        self.skill_library = SkillLibrary()
        self.curriculum = Curriculum(self.skill_library)
        
        # We need to find the source name for this repo to use Jules
        print("Locating repository source for Jules...")
        sources = client.list_sources()
        if not sources:
            raise RuntimeError("No sources found for Jules. Please connect this repository.")
        
        # Heuristic to find the right source
        self.source_name = sources[0]["name"]
        print(f"Using source: {self.source_name}")
        
        self.code_generator = CodeGenerator(self.source_name)
        self.verifier = Verifier(deck_a, deck_b)

    def learn(self, max_iterations: int = settings.MAX_ITERATIONS, wait_completion: bool = True):
        print(f"Starting AutoExpert Learning Loop (Max Iterations: {max_iterations}, Wait: {wait_completion})")
        
        for i in range(max_iterations):
            print(f"\n=== Iteration {i+1} ===")
            
            # 1. Decide on a goal
            goal = self.curriculum.get_next_goal(self.source_name)
            print(f"Objective: {goal}")
            
            # 2. Get current game context for prompting
            env = PokemonEnv(self.deck_a, self.deck_b)
            state_text, legal_actions = env.get_observation()
            legal_actions_text = "\n".join([f"{aid}: {env.game.action_name(aid)}" for aid in legal_actions])
            
            # 3. Generate/Improve Code (Iterative prompting)
            best_code = None
            best_win_rate = -1.0
            feedback = None
            previous_code = None
            
            # Use current best skill as baseline if applicable
            best_skill = self.skill_library.get_best_skill()
            if best_skill:
                previous_code = best_skill["code"]
            
            for retry in range(settings.MAX_RETRIES_PER_GOAL):
                print(f"Generating code (Attempt {retry+1}/{settings.MAX_RETRIES_PER_GOAL})...")
                code = self.code_generator.generate(goal, state_text, legal_actions_text, previous_code, feedback, wait_completion=wait_completion)
                
                if not wait_completion:
                    print("Jules task created successfully. Ending iteration as requested.")
                    return # Exit early as we can't proceed without code

                if not code:
                    print("Failed to generate code.")
                    break
                
                # 4. Verify Code
                print("Verifying code performance...")
                results = self.verifier.verify(code)
                
                if results["success"]:
                    win_rate = results["win_rate"]
                    print(f"Success! Win rate: {win_rate:.2%}")
                    
                    if win_rate > best_win_rate:
                        best_win_rate = win_rate
                        best_code = code
                    
                    if win_rate >= 0.6: # Satisfactory threshold
                        print("Performance threshold met.")
                        break
                    else:
                        feedback = f"Win rate was too low ({win_rate:.2%}). Try to be more aggressive or optimize energy usage."
                else:
                    print("Verification failed with error.")
                    feedback = f"Error during execution:\n{results['error']}"
                
                previous_code = code

            # 5. Save successfully improved skill
            if best_code and best_win_rate > (best_skill["win_rate"] if best_skill else 0.0):
                skill_name = f"Skill_{int(time.time())}"
                self.skill_library.save_skill(skill_name, best_code, goal, best_win_rate)
                print(f"New skill saved: {skill_name}")
            else:
                print("No improvement found in this iteration.")

            # Clean up temporary files
            self.code_generator.clean_up()
            
        print("\nLearning process completed.")
