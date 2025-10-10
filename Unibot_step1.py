# sanity: read CSV and show counts
import pandas as pd
from pathlib import Path

csv = Path("data/unilife.csv")
print("Looking for:", csv.resolve())

df = pd.read_csv(csv)
df.columns = [c.strip().lower() for c in df.columns]
for c in df.columns:
    df[c] = df[c].astype(str).str.strip()

print("✅ CSV loaded | columns:", list(df.columns), "| rows:", len(df))
