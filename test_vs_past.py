import sys
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add current directory to path
sys.path.append(os.getcwd())

# Mock deckgym and other dependencies
sys.modules["deckgym"] = MagicMock()
sys.modules["autoexpert"] = MagicMock()
sys.modules["autoexpert.skill_library"] = MagicMock()
sys.modules["autoexpert.config"] = MagicMock()
sys.modules["show_battle"] = MagicMock()

import vs_past

def test_majority_vote():
    print("Testing MajorityVotePlayer...")
    
    # Mocking play functions
    func1 = lambda s, g: 1
    func2 = lambda s, g: 1
    func3 = lambda s, g: 2
    
    mvp = vs_past.MajorityVotePlayer([func1, func2, func3], ["b1", "b2", "b3"])
    
    # Simple state/game mocks
    state = MagicMock()
    game = MagicMock()
    
    # Should select 1 (majority)
    result = mvp(state, game)
    print(f"Majority vote result (expected 1): {result}")
    assert result == 1

    # Tie case (1 vs 2)
    func4 = lambda s, g: 2
    mvp_tie = vs_past.MajorityVotePlayer([func1, func4], ["b1", "b4"])
    # Should be one of [1, 2]
    result_tie = mvp_tie(state, game)
    print(f"Tie vote result (expected 1 or 2): {result_tie}")
    assert result_tie in [1, 2]
    print("MajorityVotePlayer test passed!")

def test_prioritized_branch_selection():
    print("\nTesting prioritized branch selection...")
    repo_url = "https://github.com/test/repo"
    student_deck = "train_data/mewtwo.txt"
    
    # Case 1: Priority 1 exists
    remote_branches_p1 = [
        "student_vs_teacher/pikachu_vs_mewtwo",
        "student",
        "main"
    ]
    with patch("vs_past.list_remote_branches", return_value=remote_branches_p1):
        with patch("vs_past.get_past_func_for_branch", return_value=lambda s, g: 0):
            result = vs_past.get_prioritized_past_func("base", repo_url, student_deck)
            print(f"P1 selection: {type(result)}")
            assert isinstance(result, vs_past.MajorityVotePlayer)
            assert result.branch_names == ["student_vs_teacher/pikachu_vs_mewtwo"]

    # Case 2: Priority 2 exists
    remote_branches_p2 = [
        "student_vs_teacher/mewtwo_vs_starmie",
        "student_vs_teacher/mewtwo",
        "student",
        "main"
    ]
    with patch("vs_past.list_remote_branches", return_value=remote_branches_p2):
        with patch("vs_past.get_past_func_for_branch", return_value=lambda s, g: 0):
            result = vs_past.get_prioritized_past_func("base", repo_url, student_deck)
            print(f"P2 selection: {type(result)}")
            assert isinstance(result, vs_past.MajorityVotePlayer)
            assert set(result.branch_names) == {"student_vs_teacher/mewtwo_vs_starmie", "student_vs_teacher/mewtwo"}

    # Case 3: Priority 3 exists (student)
    remote_branches_p3 = [
        "student",
        "main"
    ]
    with patch("vs_past.list_remote_branches", return_value=remote_branches_p3):
        with patch("vs_past.get_past_func_for_branch", return_value=lambda s, g: 0):
            result = vs_past.get_prioritized_past_func("base", repo_url, student_deck)
            print(f"P3 selection: {type(result)}")
            assert not isinstance(result, vs_past.MajorityVotePlayer)

    # Case 4: Only main exists
    remote_branches_p4 = [
        "main"
    ]
    with patch("vs_past.list_remote_branches", return_value=remote_branches_p4):
        with patch("vs_past.get_past_func_for_branch", return_value=lambda s, g: 0):
            result = vs_past.get_prioritized_past_func("base", repo_url, student_deck)
            print(f"P4 selection: {type(result)}")
            assert not isinstance(result, vs_past.MajorityVotePlayer)

    print("Prioritized branch selection tests passed!")

if __name__ == "__main__":
    test_majority_vote()
    test_prioritized_branch_selection()
