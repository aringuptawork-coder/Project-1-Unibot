# Social -> Events: show 3 soonest from data/unilife.csv
import re
from pathlib import Path
import pandas as pd
from typing import Optional

CSV = Path("data/unilife.csv")


# --- tiny classifier (same as before) ---
def classify(text: str) -> Optional[str]:
    t = (text or "").lower()
    study_kw = {
        "study",
        "studying",
        "library",
        "exam",
        "course",
        "advisor",
        "assignment",
        "deadline",
        "timetable",
        "schedule",
        "grades",
    }
    sports_kw = {
        "sport",
        "sports",
        "gym",
        "basketball",
        "football",
        "tennis",
        "swim",
        "training",
        "team",
        "aikido",
        "yoga",
        "run",
        "workout",
    }
    social_kw = {
        "event",
        "party",
        "association",
        "club",
        "society",
        "friends",
        "social",
        "festival",
        "concert",
        "meetup",
    }
    scores = {"studying": 0, "sports": 0, "social": 0}
    for w in study_kw:
        if w in t:
            scores["studying"] += 1
    for w in sports_kw:
        if w in t:
            scores["sports"] += 1
    for w in social_kw:
        if w in t:
            scores["social"] += 1
    best_topic, best_score = max(scores.items(), key=lambda kv: kv[1])
    if best_score == 0 or list(scores.values()).count(best_score) > 1:
        return None
    return best_topic


# --- helpers for events ---
MONTH = {
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


def load_events():
    df = pd.read_csv(CSV)
    df.columns = [c.strip().lower() for c in df.columns]
    return [str(x).strip() for x in df["events"].tolist()]


def three_soonest(events):
    parsed = []
    for label in events:
        m = re.search(r"\((\d{1,2})\s*([A-Za-z]+)\)", label) or re.search(
            r"(\d{1,2})\s*([A-Za-z]+)", label
        )
        if m:
            day = int(m.group(1))
            mon = MONTH.get(m.group(2).lower(), 13)
            parsed.append((label, mon, day))
        else:
            parsed.append((label, 13, 99))
    parsed.sort(key=lambda x: (x[1], x[2], x[0]))
    return [label for (label, _, _) in parsed[:3]]


# --- tiny CLI ---
def ask(msg: str) -> str:
    return input(msg).strip()


def main():
    print("👋 Hi, I'm Unibot. What can I help you with today?")
    topic = classify(ask("> "))

    if topic is None:
        print("Is it mainly Studying, Sports, or Social activities?")
        topic = classify(ask("> "))

    if topic is None:
        print("Pick one: [1] Studying  [2] Sports  [3] Social")
        topic = {"1": "studying", "2": "sports", "3": "social"}.get(ask("> "))

    if topic != "social":
        print(f"✅ Topic selected: {topic} (we’ll handle this branch next)")
        return

    # Social branch
    print(
        "Are you looking for upcoming events or to join an association? (events/association)"
    )
    kind = ask("> ").lower()
    if kind.startswith("event"):
        ev = load_events()
        top3 = three_soonest(ev)
        print("🎉 The three soonest campus events:")
        for e in top3:
            print(" •", e)
    else:
        print("✅ Association flow coming next. For now, try typing 'events'.")


if __name__ == "__main__":
    main()
