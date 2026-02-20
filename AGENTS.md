# AGENTS.md: Algorithm Improvement Guide

This document defines the workflow for AI agents to improve the Pokemon TCG Pocket gameplay algorithms and the AutoExpert system itself.

## 🚀 System Overview
AutoExpert is a Voyager-like system that iteratively generates, verifies, and stores gameplay strategies (Skills). It uses the Google Jules API to translate game observations into Python logic that interacts with the `deckgym-core` simulator.

## 🔄 Algorithm Improvement Workflow
To improve the agent's performance, follow this PDCA (Plan-Do-Check-Act) cycle:

### 1. Plan: Identify Weaknesses
Run a large-scale benchmark against a baseline (e.g., a past version of the repository) to find statistical weaknesses.
```bash
python main.py vs-past --past-dir past_repo --matches 1000 --league-student train_data/student.csv --league-teacher train_data/teacher.csv
```
*   **Action**: Look at the "Loss Analysis" output. Note the `Seed` and `Decks` of the longest and shortest losses.

### 2. Do: Deep Dive Analysis
Use the identified failure seeds to analyze the agent's internal state perception and decision-making step-by-step.
```bash
python main.py vs-past-detail --deck-a [FAILING_DECK] --deck-b [OPPONENT_DECK] --seed [FAIL_SEED]
```
*   **Action**: Analyze the JSON output. Compare the `decoded_observation` with the `Selected Action`.
*   **Check**: Does the agent see the relevant cards? Is its priority ranking correct? Why did it pick a sub-optimal action ID?

### 3. Check: Hypothesize & Refine
Based on the deep dive, update the prompt engineering or the core logic.
*   **Prompt Improvement**: Modify `autoexpert/prompts/code_generation_prompt.py` to add specific heuristics or clarify observation meanings.
*   **Skill Refinement**: If a specific skill is failing, use its code as a base for the next `learn` iteration with specific feedback.

### 4. Act: Verify and Commit
Run a learning loop or a new benchmark to verify the fix.
```bash
python main.py learn --max-iter 10
```
*   **Action**: If win rates improve, save the new skills and update the `skill_library`.

---

## 🛠 Toolset Reference

| Command | Purpose | When to use |
| :--- | :--- | :--- |
| `main.py learn` | Self-improvement loop | To generate new skills using LLM. |
| `main.py vs-past` | Benchmarking | To measure progress against previous versions. |
| `main.py vs-past-detail` | Debugging/Analysis | To see exactly what the DL model and LLM "see" in a match against the baseline. |
| `main.py show-battle` | Visualization | To watch a match and gain intuition for strategy. |
| `main.py skills` | Inventory | To see the current library of learned strategies. |

---

## 🤖 Recommendations for AI Agents

As an AI agent collaborating on this project, you are granted high-level autonomy. You are strongly encouraged to:

1.  **Improve AGENTS.md**: If you discover a more effective workflow or a common pitfall, update this document immediately to help future agents.
2.  **Enhance Diagnostic Tools**: If `vs_detail.py` or `vs_past.py` lacks a piece of information you need, modify them. Adding better telemetry or data visualization is a key part of "Algorithm Improvement."
3.  **Refine Encoding**: If the Deep Learning model is failing to learn certain patterns, investigate `deckgym-core/src/encoding.rs` and propose changes to how the game state is vectorized.
4.  **Improve the Prompt**: If you find that the `code_generation_prompt.py` is not eliciting the best strategies, update it. Be specific about what information or constraints are missing.
5.  **Read the Database**: `deckgym-core/database.json` contains the list of all cards in the game. Use it to understand the game mechanics and card interactions.

*Self-improvement is not limited to the gameplay logic; it extends to the tools and documentation we use to build that logic.*

---

## 📚 Technical Context
*   **Observation Vector**: Decoded in `vs_detail.py`. It represents the "eyes" of the Deep Learning model.
*   **Action Space**: Defined in `encoding.rs`. Every action has a unique ID used by both the DL model and the LLM Skill code.
*   **League Decks**: Found in `train_data/`. These represent the "Meta" environment the agent must master.
