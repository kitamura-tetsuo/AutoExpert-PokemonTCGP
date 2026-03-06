import argparse
import sys
import subprocess
from pathlib import Path
from autoexpert.autoexpert import AutoExpert
from autoexpert.config import settings

def main():
    parser = argparse.ArgumentParser(description="AutoExpert-PokemonTCGP: Voyager-like LLM Agent for TCG Pocket")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Learn command
    learn_parser = subparsers.add_parser("learn", help="Start the automatic learning process")
    learn_parser.add_argument("--deck-a", type=str, default="venusaur-exeggutor.txt", help="Deck file for Player 0")
    learn_parser.add_argument("--deck-b", type=str, default="weezing-arbok.txt", help="Deck file for Player 1 (opponent)")
    learn_parser.add_argument("--max-iter", type=int, default=settings.MAX_ITERATIONS, help="Max iterations")
    learn_parser.add_argument("--no-wait-completion", action="store_true", help="Don't wait for Jules session to complete")
    
    # List skills command
    subparsers.add_parser("skills", help="List all learned skills")
    
    # Show battle command
    battle_parser = subparsers.add_parser("show-battle", help="Visualize a self-match battle using the best expert")
    battle_parser.add_argument("--deck-a", type=str, default="mewtwoex.txt", help="Deck file for Player 0")
    battle_parser.add_argument("--deck-b", type=str, default="mewtwoex.txt", help="Deck file for Player 1")
    battle_parser.add_argument("--output", type=str, default="battle.html", help="Path to output HTML file")
    battle_parser.add_argument("--seed", type=int, default=None, help="Random seed")
    
    # VS Past command
    vs_past_parser = subparsers.add_parser("vs-past", help="Match current expert against past code expert")
    vs_past_parser.add_argument("--past-dir", type=str, default="past_repo", help="Path to past repository")
    vs_past_parser.add_argument("--deck-a", type=str, default=None, help="Deck file for Player 0")
    vs_past_parser.add_argument("--deck-b", type=str, default=None, help="Deck file for Player 1")
    vs_past_parser.add_argument("--output", type=str, default="vs_past.html", help="Path to output HTML file")
    vs_past_parser.add_argument("--matches", type=int, default=1000, help="Number of matches to run")
    vs_past_parser.add_argument("--threshold", type=float, default=0.51, help="Win rate threshold to pass")
    vs_past_parser.add_argument("--seed", type=int, default=None, help="Random seed")
    vs_past_parser.add_argument("--league-student", type=str, default=None, help="CSV file for student league decks")
    vs_past_parser.add_argument("--league-teacher", type=str, default=None, help="CSV file for teacher league decks")

    # VS Past Detail command
    vs_past_detail_parser = subparsers.add_parser("vs-past-detail", help="Show step-by-step detailed observation and actions against past expert")
    vs_past_detail_parser.add_argument("--deck-a", type=str, default=None, help="Deck file for Player 0")
    vs_past_detail_parser.add_argument("--deck-b", type=str, default=None, help="Deck file for Player 1")
    vs_past_detail_parser.add_argument("--seed", type=int, required=True, help="Random seed")
    vs_past_detail_parser.add_argument("--past-dir", type=str, default="past_repo", help="Path to past repository")
    vs_past_detail_parser.add_argument("--repo-url", type=str, default="https://github.com/kitamura-tetsuo/AutoExpert-PokemonTCGP", help="URL of the past repository")

    args = parser.parse_args()
    
    if args.command == "learn":
        # Auto-detect deck based on branch name
        current_branch = ""
        try:
            current_branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
        except Exception:
            pass

        deck_a_str = args.deck_a
        deck_b_str = args.deck_b

        if current_branch.startswith("student_vs_teacher/"):
            # Format: student_vs_teacher/DeckA_vs_DeckB
            decks_part = current_branch[len("student_vs_teacher/"):]
            if "_vs_" in decks_part:
                student, teacher = decks_part.split("_vs_", 1)
                
                # Ensure .txt suffix
                if not student.endswith(".txt"): student += ".txt"
                if not teacher.endswith(".txt") and not teacher.endswith(".csv"): teacher += ".txt"
                
                deck_a_str = f"train_data/{student}"
                deck_b_str = f"train_data/{teacher}"
                print(f"Specialized matchup detected from branch '{current_branch}':")
                print(f"  Student: {deck_a_str}")
                print(f"  Teacher: {deck_b_str}")
            else:
                # Fallback: use the branch name for student, and default teacher
                student = decks_part
                if not student.endswith(".txt"): student += ".txt"
                deck_a_str = f"train_data/{student}"
                print(f"Branch '{current_branch}' detected. Using student deck: {deck_a_str}")
        elif deck_a_str == "venusaur-exeggutor.txt":
            # Original auto-detection for simple branch decks
            if current_branch and current_branch != "main":
                branch_deck = Path(f"train_data/{current_branch}.txt")
                if branch_deck.exists():
                    print(f"Detected deck for branch '{current_branch}': {branch_deck}")
                    deck_a_str = str(branch_deck)

        deck_a = Path(deck_a_str)
        if not deck_a.exists():
            deck_a = settings.DECK_DIR / deck_a_str
            
        deck_b = Path(deck_b_str)
        if not deck_b.exists():
            deck_b = settings.DECK_DIR / deck_b_str
        
        if not deck_a.exists():
            print(f"Error: Deck file not found: {deck_a_str}")
            sys.exit(1)
        if not deck_b.exists():
            print(f"Error: Deck file not found: {deck_b_str}")
            sys.exit(1)
            
        # Detect workflow type
        workflow_type = "pr_vs_past"
        if current_branch.startswith("student_vs_teacher/"):
            workflow_type = "student_deck_vs_teacher_deck"
        elif current_branch and current_branch != "main":
            workflow_type = "pr_vs_past_deck"
            
        print(f"Workflow Pattern Detected: {workflow_type}")
            
        expert = AutoExpert(str(deck_a), str(deck_b), workflow_type=workflow_type)
        expert.learn(max_iterations=args.max_iter, wait_completion=not args.no_wait_completion)
        
    elif args.command == "skills":
        from autoexpert.skill_library import SkillLibrary
        library = SkillLibrary()
        print("Learned Skills Summary:")
        print(library.get_all_skills_summary())
        
    elif args.command == "show-battle":
        cmd = ["uv", "run", "python3", "show_battle.py", 
               "--deck_a", args.deck_a, 
               "--deck_b", args.deck_b, 
               "--output", args.output]
        if args.seed is not None:
            cmd.extend(["--seed", str(args.seed)])
        
        subprocess.run(cmd, check=True)

    elif args.command == "vs-past":
        cmd = ["uv", "run", "python3", "vs_past.py",
               "--past_dir", args.past_dir,
                "--threshold", str(args.threshold)]
        if args.deck_a:
            cmd.extend(["--deck_a", args.deck_a])
        if args.deck_b:
            cmd.extend(["--deck_b", args.deck_b])
        if args.matches:
            cmd.extend(["--matches", str(args.matches)])
        if args.league_student:
            cmd.extend(["--league_decks_student", args.league_student])
        if args.league_teacher:
            cmd.extend(["--league_decks_teacher", args.league_teacher])
        
        subprocess.run(cmd, check=True)

    elif args.command == "vs-past-detail":
        cmd = ["uv", "run", "python3", "vs_past_detail.py",
               "--seed", str(args.seed),
               "--past_dir", args.past_dir,
               "--repo_url", args.repo_url]
        if args.deck_a:
            cmd.extend(["--deck_a", args.deck_a])
        if args.deck_b:
            cmd.extend(["--deck_b", args.deck_b])
        
        subprocess.run(cmd, check=True)
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
