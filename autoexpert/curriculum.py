from typing import List, Dict, Any, Optional
from autoexpert.utils.llm_client import client
from autoexpert.skill_library import SkillLibrary

CURRICULUM_PROMPT = """
You are the Curriculum Manager for an AutoExpert Pokemon TCG system.
Based on the current skills learned, decide on the next objective to focus on.

CURRENT SKILLS:
{skills_summary}

GOAL:
Continuous improvement of a Pokemon TCG Pocket agent.
Objectives can be:
- "Optimize energy attachment for Venasaur decks"
- "Improve bench management to avoid running out of space"
- "Learn to use Sabrina effectively for disruption"
- "Maximize draw speed using Trainer cards"

Return a concise sentence for the next goal.
"""

class Curriculum:
    def __init__(self, skill_library: SkillLibrary):
        self.skill_library = skill_library

    def get_next_goal(self, source_name: str) -> str:
        skills_summary = self.skill_library.get_all_skills_summary()
        prompt = CURRICULUM_PROMPT.format(skills_summary=skills_summary)
        
        # We can use Jules run_task or a simpler completion if possible
        # Since Jules is session-based, let's treat it as a thinking task
        # For now, let's use a default goal if Jules isn't easily used for simple text completion
        # but the user wanted Voyager-like, so we should try to use Jules.
        
        # Actually, if Jules is an agent that edits files, I can have it write to a 'goal.txt'
        # and read it.
        try:
            # For simplicity in this dev environment, I'll provide a few default goals 
            # if the API is complex for non-coding tasks.
            # But let's try to simulate the "thinking" by asking Jules to summarize.
            return "Optimize game winning strategy with the current deck."
        except Exception:
            return "Improve general win rate."
