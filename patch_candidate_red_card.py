import candidate_player

def check_file():
    with open('candidate_player.py', 'r') as f:
        content = f.read()
        print("has_lethal_on_board count:", content.count("has_lethal_on_board"))

check_file()
