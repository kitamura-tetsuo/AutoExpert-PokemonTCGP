from db_dump import CARD_DB_FULL
import json

v = CARD_DB_FULL.get("oricorio", [])
print(json.dumps(v, indent=2))
