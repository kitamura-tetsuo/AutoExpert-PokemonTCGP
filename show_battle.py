import argparse
import sys
import os
import json
import re
import random
import datetime
import logging
import traceback
import deckgym
from pathlib import Path
from typing import Dict, Any, List, Optional

# Set up paths for imports if necessary
sys.path.append(os.getcwd())

from autoexpert.skill_library import SkillLibrary
from autoexpert.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_args():
    parser = argparse.ArgumentParser(description="Run a battle between two agents (Self-match using latest expert).")
    parser.add_argument("--deck_a", type=str, default="mewtwoex.txt", help="Path to deck 1 file.")
    parser.add_argument("--deck_b", type=str, default="mewtwoex.txt", help="Path to deck 2 file.")
    parser.add_argument("--output", type=str, default="battle.html", help="Path to output HTML file.")
    parser.add_argument("--seed", type=int, default=int(datetime.datetime.now().timestamp()), help="Random seed.")
    return parser.parse_args()

def get_card_image_url(card_id: str) -> str:
    """
    Constructs the Limitless TCG image URL from the card ID.
    Example ID: "A1 129" -> "https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/pocket/A1/A1_129_EN_SM.webp"
    """
    if not card_id:
        return ""
    parts = card_id.split()
    if len(parts) != 2:
        return ""

    set_id = parts[0]
    card_num = parts[1]

    url = f"https://limitlesstcg.nyc3.cdn.digitaloceanspaces.com/pocket/{set_id}/{set_id}_{card_num}_EN_SM.webp"
    return url

def extract_state_info(state: deckgym.State):
    """
    Extracts structured information from the deckgym Game State object.
    """
    info = {
        "turn": state.turn_count,
        "current_player": state.current_player,
        "points": list(state.points),
        "winner": None,
        "players": []
    }

    if state.is_game_over():
        outcome = state.winner
        # PyGameOutcome might have a .winner property or we can use str()
        winner_val = -1
        if hasattr(outcome, "winner"):
            winner_val = outcome.winner
        else:
            # Fallback parsing from string if necessary, e.g. "GameOutcome::Win(0)"
            match = re.search(r"Win\((\d+)\)", str(outcome))
            if match:
                winner_val = int(match.group(1))
        
        info["winner"] = {
            "winner": winner_val,
            "is_tie": "Tie" in str(outcome)
        }

    for p in [0, 1]:
        p_info = {
            "hand": [],
            "active": None,
            "bench": [],
            "discard_pile_size": state.get_discard_pile_size(p),
            "deck_size": state.get_deck_size(p),
        }

        # Hand
        hand = state.get_hand(p)
        for card in hand:
            p_info["hand"].append({
                "id": card.id,
                "name": card.name,
                "url": get_card_image_url(card.id)
            })

        # Active
        active = state.get_active_pokemon(p)
        if active:
            tool_info = None
            if hasattr(active, "attached_tool") and active.attached_tool:
                tool = active.attached_tool
                tool_info = {
                    "id": tool.id,
                    "name": tool.name,
                    "url": get_card_image_url(tool.id)
                }

            p_info["active"] = {
                "id": active.card.id,
                "name": active.name,
                "url": get_card_image_url(active.card.id),
                "hp": active.remaining_hp,
                "max_hp": active.total_hp,
                "energy": [e if isinstance(e, str) else str(e) for e in active.attached_energy],
                "tool": tool_info,
                "status": []
            }
            if active.poisoned: p_info["active"]["status"].append("Poisoned")
            if active.asleep: p_info["active"]["status"].append("Asleep")
            if active.paralyzed: p_info["active"]["status"].append("Paralyzed")

        # Bench
        bench = state.get_bench_pokemon(p)
        for mon in bench:
            if not mon:
                continue

            tool_info = None
            if hasattr(mon, "attached_tool") and mon.attached_tool:
                tool = mon.attached_tool
                tool_info = {
                    "id": tool.id,
                    "name": tool.name,
                    "url": get_card_image_url(tool.id)
                }

            p_info["bench"].append({
                "id": mon.card.id,
                "name": mon.name,
                "url": get_card_image_url(mon.card.id),
                "hp": mon.remaining_hp,
                "max_hp": mon.total_hp,
                "energy": [e if isinstance(e, str) else str(e) for e in mon.attached_energy],
                "tool": tool_info,
                "status": []
            })

        info["players"].append(p_info)

    return info

def generate_html(history, output_path):
    """
    Generates an interactive HTML file to visualize the battle history.
    Based on the reference battle.py.
    """
    history_json = json.dumps(history)

    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pokemon TCGP Expert Battle Visualization</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1a1a1a; color: #e0e0e0; margin: 0; padding: 20px; }}
        .ptcg-symbol {{
            display: inline-block;
            width: 1.2em;
            text-align: center;
            border-radius: 50%;
            font-weight: bold;
            color: white;
            text-shadow: 1px 1px 1px black;
            margin-right: 2px;
            font-size: 0.8em;
        }}
        .type-grass {{ background-color: #78C850; }}
        .type-fire {{ background-color: #F08030; }}
        .type-water {{ background-color: #6890F0; }}
        .type-lightning {{ background-color: #F8D030; color: black; text-shadow: none; }}
        .type-psychic {{ background-color: #F85888; }}
        .type-fighting {{ background-color: #C03028; }}
        .type-darkness {{ background-color: #705848; }}
        .type-metal {{ background-color: #B8B8D0; color: black; text-shadow: none; }}
        .type-colorless {{ background-color: #A8A878; color: black; text-shadow: none; }}

        .container {{ max-width: 1200px; margin: 0 auto; background: #2d2d2d; padding: 20px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }}
        .header {{ text-align: center; margin-bottom: 20px; }}
        .controls {{ text-align: center; margin-bottom: 20px; background: #3d3d3d; padding: 15px; border-radius: 8px; }}
        button {{ padding: 10px 20px; font-size: 16px; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 5px; transition: background 0.2s; }}
        button:hover {{ background: #0056b3; }}
        .status-bar {{ display: flex; justify-content: space-between; margin-bottom: 10px; font-weight: bold; color: #aaa; }}

        .board {{ display: flex; flex-direction: column; gap: 20px; }}
        .player-area {{ border: 2px solid #444; padding: 15px; border-radius: 10px; flex: 1; transition: transform 0.2s; }}
        .player-area.current {{ border-color: #007bff; background-color: #333; transform: scale(1.01); }}

        .area-title {{ font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid #444; padding-bottom: 5px; color: #007bff; }}

        .zone {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px; align-items: flex-start; min-height: 100px; }}
        .zone-title {{ width: 60px; font-size: 12px; color: #888; font-weight: bold; text-transform: uppercase; }}

        .card-container {{ position: relative; width: 80px; }}
        .card-img {{ width: 100%; border-radius: 6px; box-shadow: 0 4px 8px rgba(0,0,0,0.4); }}
        .card-stats {{ position: absolute; bottom: 0; left: 0; right: 0; background: rgba(0,0,0,0.8); color: white; font-size: 10px; padding: 3px; text-align: center; border-radius: 0 0 6px 6px; }}
        .status-icon {{ position: absolute; top: 0; right: 0; background: #ff4d4d; color: white; border-radius: 50%; width: 20px; height: 20px; font-size: 12px; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 2px solid white; }}
        .tool-icon {{ position: absolute; top: 25px; right: -15px; width: 35px; height: 45px; z-index: 10; }}
        .tool-img {{ width: 100%; height: 100%; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.5); border: 2px solid #ffd700; }}

        .log {{ margin-top: 20px; max-height: 200px; overflow-y: auto; background: #111; padding: 15px; font-family: 'Consolas', monospace; font-size: 13px; border-radius: 8px; border: 1px solid #444; }}
        .action-highlight {{ color: #00ff00; font-weight: bold; }}
        
        .winner-display {{ position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: rgba(0,123,255,0.9); color: white; padding: 40px; border-radius: 20px; font-size: 32px; font-weight: bold; z-index: 100; display: none; text-shadow: 2px 2px 4px black; box-shadow: 0 0 50px rgba(0,0,0,0.8); }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Expert Battle Simulation</h1>
            <p id="expert-info">Current Expert Self-Match</p>
        </div>

        <div class="controls">
            <button onclick="changeStep(-10)">&lt;&lt; -10</button>
            <button onclick="changeStep(-1)">Prev</button>
            <span id="turn-display" style="margin: 0 20px; font-weight: bold; font-size: 18px;">Step: 0</span>
            <button onclick="changeStep(1)">Next</button>
            <button onclick="changeStep(10)">+10 &gt;&gt;</button>
        </div>

        <div id="board" class="board">
            <!-- Board content rendered here -->
        </div>

        <div class="log" id="action-log"></div>
    </div>

    <div id="winner-banner" class="winner-display"></div>

    <script>
        const history = {history_json};
        let currentStep = 0;

        function getEnergyChar(type) {{
            const map = {{
                'Grass': 'G', 'Fire': 'R', 'Water': 'W', 'Lightning': 'L',
                'Psychic': 'P', 'Fighting': 'F', 'Darkness': 'D',
                'Metal': 'M', 'Colorless': 'C'
            }};
            return map[type] || type.substring(0, 1);
        }}

        function renderCard(card, type="hand") {{
            if (!card) return '<div class="card-container" style="border: 1px dashed #444; height: 110px; border-radius: 6px;"></div>';

            let statsHtml = '';
            if (type === 'active' || type === 'bench') {{
                let energyHtml = '';
                if (card.energy && card.energy.length > 0) {{
                    energyHtml = card.energy.map(e => {{
                        const char = getEnergyChar(e);
                        const cls = e.toLowerCase();
                        return `<span class="ptcg-symbol type-${{cls}}" title="${{e}}">${{char}}</span>`;
                    }}).join('');
                }}
                statsHtml = `<div class="card-stats">HP: ${{card.hp}}/${{card.max_hp}}<br>${{energyHtml}}</div>`;
            }}

            let statusHtml = '';
            if (card.status && card.status.length > 0) {{
                statusHtml = `<div class="status-icon" title="${{card.status.join(', ')}}">!</div>`;
            }}

            let toolHtml = '';
            if (card.tool) {{
                toolHtml = `<div class="tool-icon" title="${{card.tool.name}}"><img src="${{card.tool.url}}" class="tool-img"></div>`;
            }}

            return `
                <div class="card-container">
                    <img src="${{card.url}}" alt="${{card.name}}" class="card-img" onerror="this.src='https://via.placeholder.com/80x110?text=${{encodeURIComponent(card.name)}}'">
                    ${{toolHtml}}
                    ${{statsHtml}}
                    ${{statusHtml}}
                </div>
            `;
        }}

        function renderPlayerArea(pIndex, state) {{
            const p = state.players[pIndex];
            const isCurrent = state.acting_player === pIndex;

            let activeHtml = renderCard(p.active, 'active');
            let benchHtml = p.bench.map(c => renderCard(c, 'bench')).join('');
            let handHtml = p.hand.map(c => renderCard(c, 'hand')).join('');

            return `
                <div class="player-area ${{isCurrent ? 'current' : ''}}">
                    <div class="area-title">Player ${{pIndex}} (Points: ${{state.points[pIndex]}} / 3) | Deck: ${{p.deck_size}} | Discard: ${{p.discard_pile_size}}</div>

                    <div class="zone">
                        <div class="zone-title">Active</div>
                        ${{activeHtml}}
                    </div>

                    <div class="zone">
                        <div class="zone-title">Bench</div>
                        ${{benchHtml}}
                    </div>

                    <div class="zone">
                        <div class="zone-title">Hand (${{p.hand.length}})</div>
                        ${{handHtml}}
                    </div>
                </div>
            `;
        }}

        function render() {{
            const state = history[currentStep];
            if (!state) return;

            document.getElementById('turn-display').innerText = `Step: ${{currentStep}} / ${{history.length - 1}} (Turn: ${{state.turn}})`;

            // Display players
            // For a better view, we show opponent (P1) on top and us (P0) on bottom
            const p0Html = renderPlayerArea(0, state);
            const p1Html = renderPlayerArea(1, state);

            document.getElementById('board').innerHTML = p1Html + p0Html;

            // Log entry
            const logDiv = document.getElementById('action-log');
            let logHtml = '';
            // Show last 5 actions
            for (let i = Math.max(0, currentStep - 5); i <= currentStep; i++) {{
                const s = history[i];
                const prefix = i === currentStep ? '<span class="action-highlight">>> </span>' : '   ';
                logHtml += `<div>${{prefix}}Step ${{i}} (Player ${{s.acting_player}}): ${{s.action_name}}</div>`;
            }}
            logDiv.innerHTML = logHtml;
            logDiv.scrollTop = logDiv.scrollHeight;

            // Winner banner
            const banner = document.getElementById('winner-banner');
            if (state.winner) {{
                banner.innerText = `WINNER: PLAYER ${{state.winner.winner}}!`;
                banner.style.display = 'block';
            }} else {{
                banner.style.display = 'none';
            }}
        }}

        function changeStep(delta) {{
            currentStep = Math.max(0, Math.min(history.length - 1, currentStep + delta));
            render();
        }}

        document.addEventListener('keydown', (e) => {{
            if (e.key === "ArrowLeft") changeStep(-1);
            if (e.key === "ArrowRight") changeStep(1);
        }});

        render();
    </script>
</body>
</html>
    """

    with open(output_path, "w") as f:
        f.write(html_template)
    logging.info(f"HTML visualization saved to {output_path}")

def main():
    args = parse_args()
    random.seed(args.seed)
    
    # Initialize Skill Library
    library = SkillLibrary()
    best_skill = library.get_best_skill()
    
    play_func = None
    if best_skill:
        logging.info(f"Using best skill: {best_skill['name']} (Win Rate: {best_skill['win_rate']:.2%})")
        code = best_skill["code"]
        local_vars = {}
        try:
            exec(code, {"deckgym": deckgym}, local_vars)
            play_func = local_vars.get("play")
            if not play_func:
                raise ValueError("No 'play' function found in skill code.")
        except Exception as e:
            logging.error(f"Error executing skill code: {e}")
            play_func = None
            
    if not play_func:
        # Fallback to candidate_player.py
        try:
            import candidate_player
            import importlib
            importlib.reload(candidate_player)
            play_func = candidate_player.play
            logging.info("Using candidate_player.play as expert skill.")
        except ImportError:
            logging.warning("No expert skill found in library or candidate_player.py. Using random strategy.")
            def play_func(state, game):
                import random
                actions = game.legal_actions()
                return random.choice(actions)

    # Initialize Game
    deck_a_path = str(settings.DECK_DIR / args.deck_a)
    deck_b_path = str(settings.DECK_DIR / args.deck_b)
    
    logging.info(f"Initializing Game with deck_a={args.deck_a}, deck_b={args.deck_b}, seed={args.seed}")
    game = deckgym.PyGameState(deck_a_path, deck_b_path, args.seed)
    
    history = []
    max_steps = 300
    step_count = 0
    
    while not game.get_state().is_game_over() and step_count < max_steps:
        state = game.get_state()
        current_player = state.current_player
        
        # Record state BEFORE action
        info = extract_state_info(state)
        info["acting_player"] = current_player
        
        # Get action
        try:
            # We use the same expert for both players (Self-match)
            action_id = play_func(state, game)
            action_name = game.action_name(action_id)
        except Exception as e:
            logging.error(f"Error during play_func: {e}")
            logging.error(traceback.format_exc())
            # Fallback to random
            action_id = random.choice(game.legal_actions())
            action_name = f"ERROR_FALLBACK: {game.action_name(action_id)}"
            
        info["action_name"] = action_name
        history.append(info)
        
        # Apply action
        game.step_with_id(action_id)
        step_count += 1
        
    # Record final state
    final_state = game.get_state()
    final_info = extract_state_info(final_state)
    final_info["acting_player"] = final_state.current_player
    final_info["action_name"] = "Game Over"
    history.append(final_info)
    
    winner_str = str(final_state.winner)
    logging.info(f"Game finished in {step_count} steps. Winner: {winner_str}")

    # Generate HTML
    generate_html(history, args.output)
    print(f"\nBattle completed! Visualization saved to: {args.output}")

if __name__ == "__main__":
    main()
