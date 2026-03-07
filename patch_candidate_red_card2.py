import re

content = open("candidate_player.py").read()

m = re.search(r"elif a\[\"type\"\] == \"red_card\":\s*if gs\.opp_hand_count >= 5:\s*a\[\"score\"\] = 85000(.*?)elif a\[\"type\"\] == \"potion\":", content, re.DOTALL)
if m:
    print(m.group(1))
