# Unibot v2 — fun, open-ended, slightly smarter (terminal-run)
# Features:
# - Session "profile" from open-ended questions (vibe, energy, solo/group, budget)
# - Topic classification with a (very) simple confidence signal + why-explanation
# - Sports recommender considers type + time commitment + indoor/outdoor + partner
# - Social recommender maps vibe→associations and filters events by vibe/energy
# - Clear fallbacks and explain-why messages

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import pandas as pd

CSV = Path("data/unilife.csv")


# ---------- Utilities ----------
def ask(msg: str) -> str:
    return input(msg).strip()


def load_csv():
    if not CSV.exists():
        raise FileNotFoundError(
            f"Missing {CSV.resolve()}. Create data/unilife.csv first."
        )
    df = pd.read_csv(CSV)
    df.columns = [c.strip().lower() for c in df.columns]
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
    if not {"sports", "associations", "events"}.issubset(set(df.columns)):
        raise ValueError("CSV must have columns: sports, associations, events")
    return df


# ---------- Classifier with (tiny) confidence + explanation ----------
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
        },
        "weight": 1.0,
    },
}


def classify_with_conf(text: str) -> Tuple[Optional[str], float, Dict[str, int]]:
    t = (text or "").lower()
    scores = {}
    hits = {}
    for topic, cfg in KEYS.items():
        score = 0
        topic_hits = 0
        for w in cfg["keywords"]:
            if w in t:
                score += 1
                topic_hits += 1
        scores[topic] = score * cfg["weight"]
        hits[topic] = topic_hits
    # pick best unique
    best_topic = max(scores, key=lambda k: scores[k])
    best_score = scores[best_topic]
    if best_score == 0 or list(scores.values()).count(best_score) > 1:
        return None, 0.0, hits
    # scale a tiny confidence (0..1) by number of hits vs 3 as a soft cap
    conf = min(1.0, best_score / 3.0)
    return best_topic, conf, hits


# ---------- Events ----------
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


def parse_events(events: List[str]) -> List[Tuple[str, int, int]]:
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
    return parsed


def filter_events_by_vibe(
    sorted_events: List[Tuple[str, int, int]], vibe: str, energy: str
) -> List[str]:
    vibe = (vibe or "").lower()
    energy = (energy or "").lower()
    fun_words = {
        "chill": {"picnic", "dinner", "thanksgiving", "language", "poetry"},
        "hype": {"party", "carnival", "karaoke", "halloween"},
        "creative": {"painting", "film", "music", "poetry"},
    }
    liked = fun_words.get(
        "chill" if "low" in energy else "hype" if "high" in energy else "creative",
        set(),
    )
    # also bias by vibe words if matched
    liked |= fun_words.get(vibe, set())
    out = []
    for label, _, _ in sorted_events:
        low = label.lower()
        if any(k in low for k in liked) or not liked:
            out.append(label)
    return out[:3] if out else [x[0] for x in sorted_events[:3]]


# ---------- Associations ----------
ASSOC_PREFS = {
    "international": "Language Club",
    "debate": "Debate Club",
    "science": "Science Society",
    "art": "Painting and Pottery",
    "poetry": "Poetry Pals",
    "music": "Music Band",
    "film": "Film Appreciation",
    "entrepreneur": "Entrepreneur Society",
    "yoga": "Yoga Circle",
    "language": "Language Club",
    "creative": "Painting and Pottery",
    "tech": "Science Society",
    "startup": "Entrepreneur Society",
}


def assoc_by_vibe(associations: List[str], vibe: str) -> str:
    vibe = (vibe or "").lower()
    # map vibe to a keyword; then pick matching assoc if present
    vibe_to_kw = {
        "chill": "yoga",
        "hype": "music",
        "creative": "art",
        "debate": "debate",
        "tech": "science",
        "international": "language",
        "startup": "entrepreneur",
    }
    kw = vibe_to_kw.get(vibe, None)
    if kw and kw in ASSOC_PREFS:
        preferred = ASSOC_PREFS[kw]
        for a in associations:
            if preferred.lower() == a.lower():
                return a
    # fallback: first
    return associations[0] if associations else "Debate Club"


# ---------- Sports advanced ----------
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
    sports_avail: set[str],
    pref: str,
    time_commit: str,
    indoor_outdoor: str,
    partner: str,
) -> str:
    pref = (pref or "").lower()
    time_commit = (time_commit or "").lower()
    indoor_outdoor = (indoor_outdoor or "").lower()
    partner = (partner or "").lower()

    # collate preference lists
    candidates = []

    def add_list(keys: List[str]):
        for k in keys:
            for s in TYPE_MAP.get(k, []):
                if s in sports_avail and s not in candidates:
                    candidates.append(s)

    # seed by pref word
    for key in TYPE_MAP:
        if key in pref:
            add_list([key])

    # indoor/outdoor bias
    if "indoor" in indoor_outdoor:
        add_list(["indoor"])
    elif "outdoor" in indoor_outdoor:
        add_list(["outdoor"])

    # partner requirement bias
    if "solo" in partner:
        # prefer solo-friendly
        soloish = ["running", "aikido", "tennis", "table tennis", "swimming"]
        for s in soloish:
            if s in sports_avail and s not in candidates:
                candidates.append(s)
    elif "partner" in partner or "friends" in partner:
        socialish = ["basketball", "football", "badminton"]
        for s in socialish:
            if s in sports_avail and s not in candidates:
                candidates.append(s)

    # time commitment heuristic
    if "low" in time_commit:
        low = ["running", "yoga", "table tennis", "badminton"]
        for s in low:
            if s in sports_avail and s not in candidates:
                candidates.append(s)
    elif "high" in time_commit:
        hi = ["basketball", "football", "aikido", "swimming", "tennis"]
        for s in hi:
            if s in sports_avail and s not in candidates:
                candidates.append(s)

    # fallback: anything available
    for s in sports_avail:
        if s not in candidates:
            candidates.append(s)

    return candidates[0].title() if candidates else "Basketball"


# ---------- Studying flow ----------
def studying_flow():
    print(
        "Are you struggling with something, or just want practical info? (type 'struggling' or 'practical')"
    )
    mode = ask("> ").lower()
    if "strug" in mode:
        print("Would you like to share this with other students? (yes/no)")
        share = ask("> ").lower()
        if share.startswith("y"):
            print(
                "➡️ Suggestion: join a study group. Reason: peer support, shared notes, accountability."
            )
        else:
            print(
                "➡️ Suggestion: contact the student advisor. Reason: confidential, tailored guidance."
            )
    else:
        print(
            "➡️ Suggestion: use the Student Desk contact form for enrolment, timetables, and practical matters."
        )


# ---------- Social flow ----------
def social_flow(profile: Dict[str, str], df: pd.DataFrame):
    print(
        "Are you looking for upcoming events or to join an association? (events/association)"
    )
    kind = ask("> ").lower()
    if kind.startswith("event"):
        ev_sorted = parse_events(df["events"].tolist())
        picks = filter_events_by_vibe(
            ev_sorted, profile.get("vibe", ""), profile.get("energy", "")
        )
        print("🎉 Handpicked events for your vibe/energy:")
        for e in picks:
            print(" •", e)
        print(
            "(Why: matched keywords from your vibe/energy to event types; fallback = chronological earliest.)"
        )
    else:
        assoc = df["associations"].tolist()
        pick = assoc_by_vibe(assoc, profile.get("vibe", ""))
        print(f"➡️ Try the association: {pick}")
        print(
            "(Why: mapped your vibe to association theme; fallback = first available.)"
        )


# ---------- Sports flow ----------
def sports_flow(df: pd.DataFrame):
    sports = set(df["sports"].astype(str).str.lower().tolist())

    print("Do you have a specific sport in mind? (yes/no)")
    yn = ask("> ").lower()

    if yn.startswith("y"):
        print("Which sport?")
        name = ask("> ").lower()
        if name in sports:
            print(
                "✅ Available on campus. → Check the University Sports Centre to register."
            )
            print("(Why: exact match found in the CSV list.)")
            return
        else:
            print("❌ Not in the list. Let's personalize a rec with 3 quick questions.")
    else:
        print("Cool, let's find your match with 3 quick questions.")

    pref = ask(
        "What kind of sport are you feeling? (team/ball/cardio/strength/martial/racket): "
    )
    time_commit = ask("How much time commitment do you prefer? (low/medium/high): ")
    io = ask("Indoor or outdoor vibes? (indoor/outdoor/any): ")
    partner = ask("Going solo or with friends? (solo/partner/friends): ")

    rec = recommend_sport(sports, pref, time_commit, io, partner)
    print(f"➡️ Recommendation: {rec}")
    print(
        "(Why: combined preference keywords + indoor/outdoor + partner need + time commitment; fallback = first available.)"
    )


# ---------- Profile building (open-ended) ----------
def build_profile() -> Dict[str, str]:
    print("First, tell me about you. No right answers—just vibes.")
    vibe = ask(
        "Q1) What vibe are you craving this week? (chill / hype / creative / debate / tech / startup / international): "
    )
    energy = ask("Q2) Energy level today? (low / medium / high): ")
    solo = ask("Q3) Social mode? (solo / with friends / either): ")
    budget = ask("Q4) Budget feeling? (tight / normal / splurge): ")
    return {"vibe": vibe, "energy": energy, "social_mode": solo, "budget": budget}


# ---------- Main ----------
def main():
    df = load_csv()
    profile = build_profile()

    print("\n👋 What can I help you with today? (free text)")
    user = ask("> ")
    topic, conf, hits = classify_with_conf(user)

    if topic is None or conf < 0.34:  # low confidence → clarify
        print(
            "That could be a few things. Is it mainly Studying, Sports, or Social activities?"
        )
        user2 = ask("> ")
        topic, conf2, hits2 = classify_with_conf(user2)
        if topic is None:
            print("Pick one: [1] Studying  [2] Sports  [3] Social")
            topic = {"1": "studying", "2": "sports", "3": "social"}.get(ask("> "), None)

    if topic is None:
        print("I couldn't determine the topic. Let's try again later.")
        return

    # Explain why (simple hits-based reason)
    reason = ", ".join([f"{k}:{v}" for k, v in hits.items()])
    print(f"\n✅ Topic: {topic}  (confidence≈{int((conf or 0) * 100)}%)")
    print(f"(Why: keyword hits → {reason})\n")

    if topic == "studying":
        studying_flow()
    elif topic == "sports":
        sports_flow(df)
    else:
        social_flow(profile, df)


if __name__ == "__main__":
    main()
