import deckgym
from typing import Dict, Any, List

def state_to_text(state: deckgym.State) -> str:
    """Converts deckgym game state to a descriptive text for LLM."""
    lines = []
    lines.append(f"Turn: {state.turn_count}")
    lines.append(f"Current Player: {state.current_player}")
    lines.append(f"Points: Player 0: {state.points[0]}, Player 1: {state.points[1]}")
    
    for p_idx in [0, 1]:
        lines.append(f"\n--- Player {p_idx} ---")
        lines.append(f"Hand Size: {state.get_hand_size(p_idx)}")
        lines.append(f"Deck Size: {state.get_deck_size(p_idx)}")
        lines.append(f"Discard Pile Size: {state.get_discard_pile_size(p_idx)}")
        
        active = state.get_active_pokemon(p_idx)
        if active:
            lines.append(f"Active: {active.name} (HP: {active.remaining_hp}/{active.hp})")
            # You might want to add energy, status, etc. if available in PlayedCard
        else:
            lines.append("Active: None")
            
        bench = state.get_bench_pokemon(p_idx)
        bench_pokemon = [p for p in bench if p is not None] if bench else []
        if bench_pokemon:
            bench_str = ", ".join([f"{p.name} (HP: {p.remaining_hp}/{p.hp})" for p in bench_pokemon])
            lines.append(f"Bench: {bench_str}")
        else:
            lines.append("Bench: None")
            
    return "\n".join(lines)

def get_legal_actions_text(game: deckgym.PyGameState) -> str:
    """Returns a list of legal action names with their IDs."""
    actions = game.legal_actions()
    action_summaries = []
    for aid in actions:
        name = game.action_name(aid)
        action_summaries.append(f"ID {aid}: {name}")
    return "\n".join(action_summaries)

def describe_environment() -> str:
    """Generic description of the deckgym environment and observation/action space."""
    return (
        "Environment: deckgym-core (Pokémon TCG Pocket Simulator)\n"
        "Interface: Python bindings with deckgym module\n"
        "Key Classes:\n"
        "- PyGameState: Main game state manager\n"
        "- PyState: Snapshot of a game state\n"
        "- PyCard / PyPlayedCard: Card information\n"
        "Common Actions: EndTurn (0), AttachEnergy, Attack, PlayPokemon, Evolve, UseItem, UseSupporter, etc.\n"
    )
