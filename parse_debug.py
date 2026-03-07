import re
with open('vs_past_deck_battle.html', 'r') as f:
    html = f.read()

# Search for the final log line showing the result
m = re.search(r"New AI did not improve over old AI.*?Failing CI", html)
if m:
    print(m.group(0))
