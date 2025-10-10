# parse event dates and print the 3 soonest
import re
import pandas as pd
from pathlib import Path

csv = Path("data/unilife.csv")
df = pd.read_csv(csv)
df.columns = [c.strip().lower() for c in df.columns]
events = df["events"].astype(str).str.strip().tolist()

month = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

parsed = []
for label in events:
    m = re.search(r"\((\d{1,2})\s*([A-Za-z]+)\)", label) or re.search(
        r"(\d{1,2})\s*([A-Za-z]+)", label
    )
    if m:
        day = int(m.group(1))
        mon = month.get(m.group(2).lower(), 13)
        parsed.append((label, mon, day))
    else:
        parsed.append((label, 13, 99))  # push unknowns to end

parsed.sort(key=lambda x: (x[1], x[2], x[0]))

print("🎉 Three Nearest events:")
for label, _, _ in parsed[:3]:
    print(" •", label)
