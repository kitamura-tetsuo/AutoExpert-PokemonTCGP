import os
import subprocess
from typing import Optional, List, Dict, Any
from autoexpert.config import settings
from autoexpert.env import PokemonEnv
from autoexpert.skill_library import SkillLibrary
from autoexpert.curriculum import Curriculum
from autoexpert.code_generator import CodeGenerator
from autoexpert.verifier import Verifier
from autoexpert.utils.llm_client import client

class AutoExpert:
    def __init__(self, deck_a: str, deck_b: str, workflow_type: str = "pr_vs_past"):
        self.deck_a = deck_a
        self.deck_b = deck_b
        self.workflow_type = workflow_type
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

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """Returns a list of active or review-pending Jules sessions."""
        try:
            current_branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
            if not current_branch:
                current_branch = "main"
        except Exception:
            current_branch = "main"

        try:
            sessions = client.list_sessions()
            # States that indicate the task is still occupying the repo or needs attention
            active_states = {
                "QUEUED", 
                "PLANNING", 
                "AWAITING_PLAN_APPROVAL", 
                "AWAITING_USER_FEEDBACK", 
                "IN_PROGRESS", 
                "PAUSED"
            }
            
            active = []
            for s in sessions:
                state = s.get("state")
                s_context = s.get("sourceContext", {})
                source = s_context.get("source")
                s_github = s_context.get("githubRepoContext", {})
                starting_branch = s_github.get("startingBranch")
                
                # Filter by source, state, AND starting branch
                if (source == self.source_name and 
                    state in active_states and 
                    starting_branch == current_branch):
                    active.append(s)
            return active
        except Exception as e:
            print(f"Warning: Failed to check for active sessions: {e}")
            return []

    def learn(self, max_iterations: int = settings.MAX_ITERATIONS, wait_completion: bool = True):
        active_tasks = self.get_active_tasks()
        if active_tasks:
            print("\n!!! CONFLICT WARNING !!!")
            print(f"There are {len(active_tasks)} active Jules tasks. To avoid merge conflicts, please wait for them to finish or review them.")
            for s in active_tasks:
                print(f" - [{s.get('state')}] {s.get('title')} (ID: {s.get('id')})")
            print("Aborting learning process.\n")
            return

        print(f"Starting AutoExpert Learning Loop (Max Iterations: {max_iterations}, Wait: {wait_completion})")
        
        for i in range(max_iterations):
            print(f"\n=== Iteration {i+1} ===")
            
            # 1. Decide on a goal
            goal = self.curriculum.get_next_goal(self.source_name)
            print(f"Objective: {goal}")
            
            # 3. Generate/Improve Code (Iterative prompting)
            best_code = None
            best_win_rate = -1.0
            feedback = None
            
            # Load deck contents for context
            deck_a_contents = None
            try:
                with open(self.deck_a, "r") as f:
                    deck_a_contents = f.read()
            except Exception as e:
                print(f"Warning: Failed to read deck file {self.deck_a}: {e}")

            deck_b_contents = None
            try:
                if self.deck_b:
                    with open(self.deck_b, "r") as f:
                        deck_b_contents = f.read()
            except Exception as e:
                print(f"Warning: Failed to read deck file {self.deck_b}: {e}")

            evaluation_log = None
            
            # Baseline evaluation: Run before the first attempt if we have a baseline
            if evaluation_log is None:
                print("Running baseline 100-match evaluation...")
                evaluation_log = self._run_evaluation()

            for retry in range(settings.MAX_RETRIES_PER_GOAL):
                print(f"Generating code (Attempt {retry+1}/{settings.MAX_RETRIES_PER_GOAL})...")
                code = self.code_generator.generate(
                    goal, 
                    feedback, 
                    deck_path=self.deck_a,
                    deck_contents=deck_a_contents,
                    opponent_deck_path=self.deck_b,
                    opponent_deck_contents=deck_b_contents,
                    evaluation_log=evaluation_log,
                    workflow_type=self.workflow_type,
                    wait_completion=wait_completion
                )
                
                if not wait_completion:
                    print("Jules task created successfully. Ending iteration as requested.")
                    return # Exit early as we can't proceed without code

                if not code:
                    print("Failed to generate code.")
                    break
                
                # 4. Verify Code
                print("Verifying code performance...")
                results = self.verifier.verify(code)
                
                # Run vs_past_deck.py to get detailed evaluation log
                evaluation_log = self._run_evaluation()

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

    def _run_evaluation(self) -> str:
        """Runs the 100-match evaluation and returns the log string."""
        print("Running 100-match evaluation against past deck...")
        try:
            # We use the current candidate_player.py which was just written by CodeGenerator or baseline setup
            cmd = [
                "uv", "run", "python3", "vs_past_deck.py",
                "--deck_a", self.deck_a,
                "--deck_b", self.deck_b,
                "--matches", "100",
                "--threshold", "0.01"
            ]
            process = subprocess.run(cmd, capture_output=True, text=True)
            stdout = process.stdout
            
            if "--- Deck-Specialized AI Evaluation Results ---" in stdout:
                log = stdout.split("--- Deck-Specialized AI Evaluation Results ---")[-1]
                return "--- Deck-Specialized AI Evaluation Results ---" + log
            return stdout
        except Exception as e:
            print(f"Warning: Failed to run vs_past_deck.py: {e}")
            return f"Error running vs_past_deck.py: {e}"
