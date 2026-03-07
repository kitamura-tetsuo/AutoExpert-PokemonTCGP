import os
import re
from typing import Optional, Tuple
from autoexpert.utils.llm_client import client
from autoexpert.prompts.code_generation_prompt import get_system_prompt, get_task_prompt
from autoexpert.config import settings

class CodeGenerator:
    def __init__(self, source_name: str):
        self.source_name = source_name

    def generate(self, goal: str, feedback: Optional[str] = None, deck_path: Optional[str] = None, deck_contents: Optional[str] = None, opponent_deck_path: Optional[str] = None, opponent_deck_contents: Optional[str] = None, evaluation_log: Optional[str] = None, workflow_type: str = "pr_vs_past") -> str:
        """Calls Jules to generate a Python play function."""
        task_prompt = get_task_prompt(goal, feedback, deck_path, deck_contents, opponent_deck_path, opponent_deck_contents, evaluation_log)
        
        system_prompt = get_system_prompt(deck_path, opponent_deck_path, workflow_type=workflow_type)
        full_prompt = f"{system_prompt}\n\nTASK:\n{task_prompt}\n\nPlease write the function to 'candidate_player.py' in the root directory. Also You can edit all files in the repository."

        # Create session
        session = client.create_session(full_prompt, self.source_name, title="Generate TCG Strategy")
        session_id = session["id"]
        
        print(f"Jules session created: {session_id}.")
        
        if not wait_completion:
            return "SESSION_CREATED_ASYNC"

        print(f"Waiting for completion...")
        completed_session = client.wait_for_session(session_id)
        
        # In a real Voyager system, we'd extract the code from the response.
        # Since Jules edits files, let's assume it wrote to 'candidate_player.py'
        # if it detected the request to write to a file.
        
        # Alternatively, we can check the 'outputs' file changes if the API provides it.
        # For this implementation, I will attempt to read 'candidate_player.py' after session completion.
        
        try:
            with open("candidate_player.py", "r") as f:
                code = f.read()
            return code
        except FileNotFoundError:
            # Fallback: Extract from session outputs if Jules just chatted back
            outputs = completed_session.get("outputs", [])
            for output in outputs:
                if "content" in output:
                    # Look for python code blocks
                    match = re.search(r"```python\n(.*?)\n```", output["content"], re.DOTALL)
                    if match:
                        return match.group(1)
            return ""

    def clean_up(self):
        if os.path.exists("candidate_player.py"):
            os.remove("candidate_player.py")
