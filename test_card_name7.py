import re

def original_clean(raw_name):
    if not raw_name or raw_name == "Unknown": return "Unknown"
    if raw_name.startswith("Some(") and raw_name.endswith(")"):
        raw_name = raw_name[5:-1]

    m = re.match(r"^([A-Za-z0-9]+)?([A-Z][a-z].*)", raw_name)
    if m and m.group(1):
         prefix = m.group(1)
         name_part = m.group(2)
         if len(prefix) <= 6:
             raw_name = name_part

    cleaned = re.sub(r"([a-z])([A-Z])", r"\1 \2", raw_name)

    if cleaned.endswith(" Ex"):
        cleaned = cleaned[:-3] + " ex"
    return cleaned


def new_clean(raw_name):
    if not raw_name or raw_name == "Unknown": return "Unknown"
    if raw_name.startswith("Some(") and raw_name.endswith(")"):
        raw_name = raw_name[5:-1]

    m = re.match(r"^([A-Za-z\-]+?\d+)(.*)", raw_name)
    if m:
        prefix = m.group(1)
        name_part = m.group(2)
        if prefix and len(prefix) <= 7:
            raw_name = name_part
    else:
        m = re.match(r"^([A-Za-z0-9]+)?([A-Z][a-z].*)", raw_name)
        if m and m.group(1):
             prefix = m.group(1)
             name_part = m.group(2)
             if len(prefix) <= 6:
                 raw_name = name_part

    if raw_name == "XSpeed":
        raw_name = "X Speed"

    cleaned = re.sub(r"([a-z])([A-Z])", r"\1 \2", raw_name)

    if cleaned.endswith(" Ex"):
        cleaned = cleaned[:-3] + " ex"
    return cleaned

names = ["P-A005Poké Ball", "PA006RedCard", "A1004VenusaurEx", "A1177Weezing", "P-A007Professor'sResearch"]
for n in names:
    print(f"{n} -> orig: {original_clean(n)}  new: {new_clean(n)}")
