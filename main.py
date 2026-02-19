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
    vs_past_parser.add_argument("--matches", type=int, default=1, help="Number of matches to run")
    vs_past_parser.add_argument("--seed", type=int, default=None, help="Random seed")

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
        expert.learn(max_iterations=args.max_iter)
        
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
        
        subprocess.run(cmd)
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
