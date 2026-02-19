import os
import re
from typing import Optional, Tuple
from autoexpert.utils.llm_client import client
from autoexpert.prompts.code_generation_prompt import SYSTEM_PROMPT, get_task_prompt
from autoexpert.config import settings

class CodeGenerator:
    def __init__(self, source_name: str):
        self.source_name = source_name

    def generate(self, goal: str, state_text: str, legal_actions_text: str, previous_code: Optional[str] = None, feedback: Optional[str] = None) -> str:
        """Calls Jules to generate a Python play function."""
        task_prompt = get_task_prompt(goal, state_text, legal_actions_text, previous_code, feedback)
        
        full_prompt = f"{SYSTEM_PROMPT}\n\nTASK:\n{task_prompt}\n\nPlease write the function to 'candidate_player.py' in the root directory."

        # Create session
        session = client.create_session(full_prompt, self.source_name, title="Generate TCG Strategy")
        session_id = session["id"]
        
        print(f"Jules session created: {session_id}. Waiting for completion...")
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
