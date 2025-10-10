# Unibot — Step 7 (open-ended + brief-compliant, fun + explainable)
# - Starts with open-ended profile questions (vibe, energy, social mode, budget)
# - Open question → classify (studying/sports/social) with confidence & "why"
# - Clarifying question if low confidence → MC fallback [1/2/3]
# - Studying: struggling vs practical → share? → advisor/study group/Student Desk
# - Sports: exact check or personalized rec (type + time + indoor/outdoor + partner)
# - Social: events (3 soonest, vibe/energy-aware) or association (vibe-mapped)
# Requirements: pandas installed; CSV at data/unilife.csv

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import pandas as pd

CSV = Path("data/unilife.csv")


# -------------------- Utilities --------------------
def ask(msg: str) -> str:
    return input(msg).strip()


def load_csv() -> pd.DataFrame:
    if not CSV.exists():
        raise FileNotFoundError(
            f"Missing {CSV.resolve()} — create data/unilife.csv first."
        )
    df = pd.read_csv(CSV)
    df.columns = [c.strip().lower() for c in df.columns]
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
    need = {"sports", "associations", "events"}
    missing = need - set(df.columns)
    if missing:
        raise ValueError(f"CSV must include columns: {need} (missing: {missing})")
    return df


# -------------------- Classifier (+confidence + why) --------------------
KEYS = {
    "studying": {
        "keywords": {
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
            "syllabus",
            "enrol",
            "enroll",
        },
        "weight": 1.0,
    },
    "sports": {
        "keywords": {
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
            "badminton",
            "table tennis",
        },
        "weight": 1.0,
    },
    "social": {
        "keywords": {
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
            "picnic",
            "dinner",
            "karaoke",
            "valentine",
            "halloween",
        },
        "weight": 1.0,
    },
}


def classify_with_conf(text: str) -> Tuple[Optional[str], float, Dict[str, int]]:
    t = (text or "").lower()
    scores, hits = {}, {}
    for topic, cfg in KEYS.items():
        h = sum(1 for w in cfg["keywords"] if w in t)
        hits[topic] = h
        scores[topic] = h * cfg["weight"]
    best = max(scores, key=lambda k: scores[k])
    top = scores[best]
    if top == 0 or list(scores.values()).count(top) > 1:
        return None, 0.0, hits
    conf = min(1.0, top / 3.0)  # soft cap
    return best, conf, hits


# -------------------- Events --------------------
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


def parse_events(ev: List[str]) -> List[Tuple[str, int, int]]:
    out = []
    for label in ev:
        m = re.search(r"\((\d{1,2})\s*([A-Za-z]+)\)", label) or re.search(
            r"(\d{1,2})\s*([A-Za-z]+)", label
        )
        if m:
            day = int(m.group(1))
            mon = MONTH.get(m.group(2).lower(), 13)
            out.append((label, mon, day))
        else:
            out.append((label, 13, 99))
    out.sort(key=lambda x: (x[1], x[2], x[0]))
    return out


def filter_events_by_profile(
    sorted_events: List[Tuple[str, int, int]], vibe: str, energy: str
) -> List[str]:
    vibe = (vibe or "").lower()
    energy = (energy or "").lower()
    buckets = {
        "chill": {"picnic", "dinner", "thanksgiving", "language", "poetry"},
        "hype": {"party", "carnival", "karaoke", "halloween"},
        "creative": {"painting", "film", "music", "poetry"},
        "debate": {"debate"},
        "tech": {"science"},
    }
    liked = set()
    if "low" in energy:
        liked |= buckets["chill"]
    elif "high" in energy:
        liked |= buckets["hype"]
    else:
        liked |= buckets["creative"]
    liked |= buckets.get(vibe, set())
    picks = [
        lbl for (lbl, _, _) in sorted_events if any(k in lbl.lower() for k in liked)
    ]
    return picks[:3] or [x[0] for x in sorted_events[:3]]


# -------------------- Associations --------------------
ASSOC_PREFS = {
    "international": "Language Club",
    "debate": "Debate Club",
    "science": "Science Society",
    "art": "Painting and Pottery",
    "poetry": "Poetry Pals",
    "music": "Music Band",
    "film": "Film Appreciation",
    "startup": "Entrepreneur Society",
    "yoga": "Yoga Circle",
    "language": "Language Club",
    "creative": "Painting and Pottery",
    "tech": "Science Society",
}


def association_for_vibe(associations: List[str], vibe: str) -> str:
    vibe = (vibe or "").lower()
    vibe_map = {
        "chill": "yoga",
        "hype": "music",
        "creative": "art",
        "debate": "debate",
        "tech": "science",
        "startup": "startup",
        "international": "language",
    }
    kw = vibe_map.get(vibe)
    if kw and kw in ASSOC_PREFS:
        prefer = ASSOC_PREFS[kw]
        for a in associations:
            if a.lower() == prefer.lower():
                return a
    return associations[0] if associations else "Debate Club"


# -------------------- Sports --------------------
TYPE_MAP = {
    "team": ["football", "basketball"],
    "ball": ["football", "basketball", "tennis", "table tennis"],
    "cardio": ["running", "swimming", "badminton"],
    "strength": ["aikido"],
    "martial": ["aikido"],
    "racket": ["tennis", "badminton", "table tennis"],
    "indoor": ["table tennis", "aikido", "badminton", "basketball"],
    "outdoor": ["football", "running", "tennis"],
}


def recommend_sport(
    avail: set[str], pref: str, time_commit: str, place: str, partner: str
) -> str:
    pref = (pref or "").lower()
    time_commit = (time_commit or "").lower()
    place = (place or "").lower()
    partner = (partner or "").lower()

    candidates: List[str] = []

    def add_list(keys: List[str]):
        for k in keys:
            for s in TYPE_MAP.get(k, []):
                if s in avail and s not in candidates:
                    candidates.append(s)

    for key in TYPE_MAP:
        if key in pref:
            add_list([key])

    if "indoor" in place:
        add_list(["indoor"])
    elif "outdoor" in place:
        add_list(["outdoor"])

    if "solo" in partner:
        for s in ["running", "aikido", "tennis", "table tennis", "swimming"]:
            if s in avail and s not in candidates:
                candidates.append(s)
    elif "partner" in partner or "friends" in partner:
        for s in ["basketball", "football", "badminton"]:
            if s in avail and s not in candidates:
                candidates.append(s)

    if "low" in time_commit:
        for s in ["running", "yoga", "table tennis", "badminton"]:
            if s in avail and s not in candidates:
                candidates.append(s)
    elif "high" in time_commit:
        for s in ["basketball", "football", "aikido", "swimming", "tennis"]:
            if s in avail and s not in candidates:
                candidates.append(s)

    for s in avail:
        if s not in candidates:
            candidates.append(s)

    return candidates[0].title() if candidates else "Basketball"


# -------------------- Branch flows (per brief) --------------------
def studying_flow():
    print(
        "Are you struggling with something, or do you want practical info? (free text)"
    )
    mode = ask("> ").lower()
    if "strug" in mode:
        print("Would you like to share this with other students? (yes/no)")
        share = ask("> ").lower()
        if share.startswith("y"):
            print(
                "➡️ Suggestion: join a study group. (Reason: peer support, shared notes, accountability.)"
            )
        else:
            print(
                "➡️ Suggestion: contact the student advisor. (Reason: confidential, tailored guidance.)"
            )
    else:
        print(
            "➡️ Suggestion: use the Student Desk contact form for enrolment/timetables/practical issues."
        )


def sports_flow(df: pd.DataFrame):
    sports = set(df["sports"].astype(str).str.lower())
    print("Do you have a specific sport in mind? (yes/no)")
    if ask("> ").lower().startswith("y"):
        print("Which sport?")
        name = ask("> ").lower()
        if name in sports:
            print(
                "✅ Available on campus → Check the University Sports Centre to register. (Why: exact match in CSV.)"
            )
            return
        else:
            print("❌ Not listed. Let’s personalize a rec with 3 quick questions.")
    else:
        print("Cool—let’s find your match with 3 quick questions.")

    pref = ask(
        "Q1) What kind of sport are you feeling? (team/ball/cardio/strength/martial/racket): "
    )
    time_commit = ask("Q2) Time commitment? (low/medium/high): ")
    place = ask("Q3) Indoor or outdoor? (indoor/outdoor/any): ")
    partner = ask("Q4) Solo or with friends? (solo/partner/friends): ")
    rec = recommend_sport(sports, pref, time_commit, place, partner)
    print(f"➡️ Recommendation: {rec}")
    print(
        "(Why: combined type + place + partner + time; fallback = first available in CSV.)"
    )


def social_flow(profile: Dict[str, str], df: pd.DataFrame):
    print(
        "Are you looking for upcoming events or to join an association? (events/association)"
    )
    kind = ask("> ").lower()
    if kind.startswith("event"):
        ev_sorted = parse_events(df["events"].tolist())
        picks = filter_events_by_profile(
            ev_sorted, profile.get("vibe", ""), profile.get("energy", "")
        )
        print("🎉 Handpicked events (considering your vibe/energy):")
        for e in picks:
            print(" •", e)
        print(
            "(Why: matched vibe/energy keywords; fallback = earliest chronologically.)"
        )
    else:
        assoc = df["associations"].tolist()
        pick = association_for_vibe(assoc, profile.get("vibe", ""))
        print(f"➡️ Try the association: {pick}")
        print("(Why: mapped your vibe to association theme; fallback = first in CSV.)")


# -------------------- Profile (open-ended first) --------------------
def build_profile() -> Dict[str, str]:
    print("Before we start, tell me about you (open-ended).")
    vibe = ask(
        "Q1) What vibe are you craving this week? (e.g., chill / hype / creative / debate / tech / startup / international): "
    )
    energy = ask("Q2) Energy level today? (low / medium / high): ")
    social = ask("Q3) Social mode? (solo / with friends / either): ")
    budget = ask("Q4) Budget? (tight / normal / splurge): ")
    return {"vibe": vibe, "energy": energy, "social": social, "budget": budget}


# -------------------- Main --------------------
def main():
    df = load_csv()
    profile = build_profile()

    print("\n👋 What can I help you with today? (free text)")
    topic, conf, hits = classify_with_conf(ask("> "))

    if topic is None or conf < 0.34:
        print(
            "That could be a few things. Is it mainly Studying, Sports, or Social activities?"
        )
        topic, conf, hits = classify_with_conf(ask("> "))

    if topic is None:
        print("Pick one: [1] Studying  [2] Sports  [3] Social")
        topic = {"1": "studying", "2": "sports", "3": "social"}.get(ask("> "), None)

    if topic is None:
        print("I couldn’t determine the topic. Let’s try again later.")
        return

    why = ", ".join([f"{k}:{v}" for k, v in hits.items()])
    print(f"\n✅ Topic: {topic} (confidence≈{int(conf * 100)}%)")
    print(f"(Why: keyword hits → {why})\n")

    if topic == "studying":
        studying_flow()
    elif topic == "sports":
        sports_flow(df)
    else:
        social_flow(profile, df)


if __name__ == "__main__":
    main()
