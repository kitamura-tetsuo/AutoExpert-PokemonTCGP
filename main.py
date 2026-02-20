import argparse
import sys
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
    vs_past_parser.add_argument("--deck-a", type=str, default="mewtwoex.txt", help="Deck file for Player 0")
    vs_past_parser.add_argument("--deck-b", type=str, default="mewtwoex.txt", help="Deck file for Player 1")
    vs_past_parser.add_argument("--output", type=str, default="vs_past.html", help="Path to output HTML file")
    vs_past_parser.add_argument("--matches", type=int, default=1000, help="Number of matches to run")
    vs_past_parser.add_argument("--seed", type=int, default=None, help="Random seed")
    vs_past_parser.add_argument("--league-student", type=str, default=None, help="CSV file for student league decks")
    vs_past_parser.add_argument("--league-teacher", type=str, default=None, help="CSV file for teacher league decks")

    # VS Past Detail command
    vs_past_detail_parser = subparsers.add_parser("vs-past-detail", help="Show step-by-step detailed observation and actions against past expert")
    vs_past_detail_parser.add_argument("--deck-a", type=str, default="mewtwoex.txt", help="Deck file for Player 0")
    vs_past_detail_parser.add_argument("--deck-b", type=str, default="mewtwoex.txt", help="Deck file for Player 1")
    vs_past_detail_parser.add_argument("--seed", type=int, required=True, help="Random seed")
    vs_past_detail_parser.add_argument("--past-dir", type=str, default="past_repo", help="Path to past repository")
    vs_past_detail_parser.add_argument("--repo-url", type=str, default="https://github.com/kitamura-tetsuo/AutoExpert-PokemonTCGP", help="URL of the past repository")

    args = parser.parse_args()
    
    if args.command == "learn":
        deck_a = settings.DECK_DIR / args.deck_a
        deck_b = settings.DECK_DIR / args.deck_b
        
        if not deck_a.exists():
            print(f"Error: Deck file not found at {deck_a}")
            sys.exit(1)
        if not deck_b.exists():
            print(f"Error: Deck file not found at {deck_b}")
            sys.exit(1)
            
        expert = AutoExpert(str(deck_a), str(deck_b))
        expert.learn(max_iterations=args.max_iter, wait_completion=not args.no_wait_completion)
        
    elif args.command == "skills":
        from autoexpert.skill_library import SkillLibrary
        library = SkillLibrary()
        print("Learned Skills Summary:")
        print(library.get_all_skills_summary())
        
    elif args.command == "show-battle":
        import subprocess
        cmd = ["uv", "run", "python3", "show_battle.py", 
               "--deck_a", args.deck_a, 
               "--deck_b", args.deck_b, 
               "--output", args.output]
        if args.seed is not None:
            cmd.extend(["--seed", str(args.seed)])
        
        subprocess.run(cmd)

    elif args.command == "vs-past":
        import subprocess
        cmd = ["uv", "run", "python3", "vs_past.py",
               "--past_dir", args.past_dir,
               "--deck_a", args.deck_a,
               "--deck_b", args.deck_b,
               "--output", args.output,
               "--num_matches", str(args.matches)]
        if args.seed is not None:
            cmd.extend(["--seed", str(args.seed)])
        if args.league_student:
            cmd.extend(["--league_decks_student", args.league_student])
        if args.league_teacher:
            cmd.extend(["--league_decks_teacher", args.league_teacher])
        
        subprocess.run(cmd)

    elif args.command == "vs-past-detail":
        import subprocess
        cmd = ["uv", "run", "python3", "vs_past_detail.py",
               "--deck_a", args.deck_a,
               "--deck_b", args.deck_b,
               "--seed", str(args.seed),
               "--past_dir", args.past_dir,
               "--repo_url", args.repo_url]
        
        subprocess.run(cmd)
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
