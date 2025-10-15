# Unibot — combined steps (open-ended + policy-compliant + loop)
from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, List, Tuple, Dict
import pandas as pd
import sys, os


def runtime_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path.cwd()))  # _MEIPASS exists only in the EXE
    return base / relative


CSV = Path("data/unilife.csv")


# ---------- I/O ----------
def ask(msg: str) -> str:
    return input(msg).strip()


def load_df() -> pd.DataFrame:
    if not CSV.exists():
        raise FileNotFoundError(
            f"CSV missing at {CSV.resolve()}. Put your data at data/unilife.csv"
        )
    df = pd.read_csv(CSV)
    df.columns = [c.strip().lower() for c in df.columns]
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
    need = {"sports", "associations", "events"}
    miss = need - set(df.columns)
    if miss:
        raise ValueError(f"CSV must include columns {need}; missing: {miss}")
    return df


# ---------- Topic inferencer (free-text only) ----------
def classify_free(text: str) -> Optional[str]:
    t = (text or "").lower()
    st = any(
        w in t
        for w in [
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
            "enrol",
            "enroll",
        ]
    )
    sp = any(
        w in t
        for w in [
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
        ]
    )
    so = any(
        w in t
        for w in [
            "event",
            "party",
            "association",
            "club",
            "society",
            "friends",
            "friend",
            "friendshipsocial",
            "festival",
            "activity",
            "fun",
            "concert",
            "show",
            "meetup",
            "meet-up",
            "karaoke",
            "sing",
            "dinner",
            "picnic",
            "valentine",
            "halloween",
        ]
    )
    hits = {"studying": int(st), "sports": int(sp), "social": int(so)}
    if sum(hits.values()) == 0 or list(hits.values()).count(1) > 1:
        return None
    return max(hits, key=hits.get)


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


def parse_events(ev: List[str]) -> List[Tuple[str, int, int]]:
    out = []
    for label in ev:
        m = re.search(r"\((\d{1,2})\s*([A-Za-z]+)\)", label) or re.search(
            r"(\d{1,2})\s*([A-Za-z]+)", label
        )
        if m:
            out.append((label, MONTH.get(m.group(2).lower(), 13), int(m.group(1))))
        else:
            out.append((label, 13, 99))
    return sorted(out, key=lambda x: (x[1], x[2], x[0]))


# ---------- Associations ----------
ASSOC_PREFS = {
    "international": "Language Club",
    "art": "Painting and Pottery",
    "creative": "Painting and Pottery",
    "debate": "Debate Club",
    "science": "Science Society",
    "tech": "Science Society",
    "poetry": "Poetry Pals",
    "music": "Music Band",
    "film": "Film Appreciation",
    "startup": "Entrepreneur Society",
    "yoga": "Yoga Circle",
    "language": "Language Club",
}


def map_assoc(associations: List[str], free_text: str) -> str:
    t = free_text.lower()
    for k, v in ASSOC_PREFS.items():
        if k in t:
            for a in associations:
                if a.lower() == v.lower():
                    return a
    return associations[0] if associations else "Debate Club"


# ---------- Sports ----------
TYPE_MAP = {
    "team": ["football", "basketball"],
    "ball": ["football", "basketball", "tennis", "table tennis"],
    "cardio": ["running", "swimming", "badminton"],
    "strength": ["aikido"],
    "martial": ["aikido"],
    "racket": ["tennis", "badminton", "table tennis"],
}


def rec_sport(avail: set[str], desc: str) -> str:
    t = (desc or "").lower()
    order = [
        k for k in ["team", "ball", "cardio", "strength", "martial", "racket"] if k in t
    ] or ["team", "cardio", "racket"]
    for key in order:
        for s in TYPE_MAP[key]:
            if s in avail:
                return s.title()
    return next(iter(avail), "Basketball").title()


# ---------- Branch flows (policy-compliant, open-ended) ----------
def studying_flow():
    q1 = ask(
        "Tell me what you need around studies right now—are you struggling with something, or just after practical info? "
    )
    if any(
        k in q1.lower()
        for k in ["strug", "problem", "issue", "stuck", "anxious", "stress", "fail"]
    ):
        q2 = ask(
            "Would you be comfortable sharing this with other students, or would you prefer to keep it private? "
        )
        if any(
            k in q2.lower() for k in ["share", "students", "group", "public", "others"]
        ):
            print(
                "➡️ Suggestion: join a study group. (brief: struggling + willing to share → study group)"
            )
        else:
            print(
                "➡️ Suggestion: contact the student advisor. (brief: struggling + not sharing → advisor)"
            )
    else:
        print(
            "➡️ Suggestion: use the Student Desk contact form for practical info. (brief: practical → Student Desk)"
        )


def sports_flow(df: pd.DataFrame):
    sports = set(df["sports"].astype(str).str.lower())

    q1 = ask(
        "Tell me about the sport situation—do you already have a specific sport in mind, or are you exploring? "
    )

    t1 = q1.lower()

    # 1) If a sport name is already mentioned in q1, handle it right away.
    for s in sports:
        if s in t1:
            print(
                "✅ That sport is available. → Check the University Sports Centre website. (brief: specific + available)"
            )
            return

    # 2) If the user said "yes" (or similar) but didn't name the sport, ask for it.
    yes_words = ("yes", "yep", "yeah", "y", "sure", "ok", "okay", "affirmative")
    if any(t1.startswith(w) or f" {w} " in f" {t1} " for w in yes_words):
        name = ask("Which sport do you have in mind? ").strip().lower()
        if any(s in name for s in sports):
            print(
                "✅ That sport is available. → Check the University Sports Centre website. (brief: specific + available)"
            )
            return
        else:
            print("❌ I couldn’t find that exact sport on the campus list.")
            # fall through to preference-based recommendation

    # 3) Exploring (or unknown sport) → follow-up then recommend.
    q2 = ask(
        "Describe what you want from a sport (e.g., team vibes, ball games, cardio, strength): "
    )
    suggestion = rec_sport(sports, q2)
    print(
        f"➡️ Recommendation: {suggestion} (brief: exploring → follow-up → recommend from available list)"
    )

    sports = set(df["sports"].str.lower())
    q1 = ask(
        "Tell me about the sport situation—do you already have a specific sport in mind, or are you exploring? "
    )
    # exact sport check
    for s in sports:
        if s in q1.lower():
            print(
                "✅ That sport is available. → Check the University Sports Centre website. (brief: specific + available)"
            )
            return
    # otherwise follow-up → recommend
    q2 = ask(
        "Describe what you want from a sport (e.g., team vibes, ball games, cardio, strength): "
    )
    print(
        f"➡️ Recommendation: {rec_sport(sports, q2)} (brief: exploring → follow-up → recommend from available list)"
    )


def social_flow(df: pd.DataFrame):
    q1 = ask(
        "What are you looking for socially—upcoming events to attend or joining an association? Say it in your own words. "
    )
    t = q1.lower()
    if any(
        k in t
        for k in [
            "event",
            "party",
            "show",
            "concert",
            "karaoke",
            "dinner",
            "picnic",
            "festival",
        ]
    ):
        top3 = [lbl for (lbl, _, _) in parse_events(df["events"].tolist())[:3]]
        print("🎉 The three soonest campus events:")
        [print(" •", e) for e in top3]
        print("(brief: events path → 3 soonest)")
    else:
        pref = ask(
            "Describe what kind of association fits you (e.g., international, artistic, debate, business, wellness, music, film, science, language): "
        )
        assoc = df["associations"].tolist()
        print(
            f"➡️ Try joining: {map_assoc(assoc, pref)} (brief: association path → follow-up → recommend)"
        )


# ---------- Loop control (continue/close + remainder) ----------
import re


def wants_more_and_remainder(text: str):
    """
    Return:
      (True, remainder)  -> user wants more; 'remainder' is what's after the yes/intent cue
      (False, "")        -> user is done
      (None, "")         -> unclear
    Handles: 'yes, ...', 'more ...', 'also ...', 'next ...', 'i want ...', 'need ...', 'help ...'
    """
    t = (text or "").strip()
    low = t.lower()

    # explicit NO wins
    no_words = (
        "no",
        "nope",
        "nah",
        "n",
        "all good",
        "im good",
        "i'm good",
        "that’s all",
        "thats all",
        "thanks",
        "thank you",
        "done",
        "finish",
        "exit",
        "quit",
        "nothing else",
        "i'm fine",
        "im fine",
    )
    if any(w in low for w in no_words):
        return False, ""

    # strong YES cues (start or anywhere)
    yes_heads = (
        r"(?:yes|yep|yeah|y|sure|ok(?:ay)?|please|continue|more|another|also|next)"
    )
    need_heads = r"(?:i\s+want|i\s+need|need|want|help|tell\s+me|info|information)"
    m = re.match(rf"^\s*(?:{yes_heads}|{need_heads})[\s,.:;-]*(.*)$", low, flags=re.I)
    if m:
        remainder = (m.group(1) or "").strip()
        return True, remainder

    # soft intent: contains topic keywords → likely wants more
    soft_yes_terms = (
        "sport",
        "study",
        "exam",
        "advisor",
        "event",
        "association",
        "club",
        "social",
    )
    if any(w in low for w in soft_yes_terms):
        return True, low  # treat whole line as next query

    return None, ""

    """
    Returns: (True, remainder) if wants more; (False, "") if done; (None, "") if unclear.
    If 'yes, also X' → True with remainder 'also X'.
    """
    t = (text or "").strip()
    low = t.lower()
    no_words = (
        "no",
        "nope",
        "nah",
        "n",
        "all good",
        "im good",
        "i'm good",
        "that’s all",
        "thats all",
        "thanks",
        "thank you",
        "done",
        "finish",
        "exit",
        "quit",
    )
    if any(w in low for w in no_words):
        return False, ""
    if any(
        low.startswith(w)
        for w in (
            "yes",
            "yep",
            "yeah",
            "y",
            "sure",
            "ok",
            "okay",
            "please",
            "continue",
            "more",
            "help",
            "go on",
        )
    ) or any(
        f" {w} " in f" {low} "
        for w in (
            "yes",
            "yep",
            "yeah",
            "y",
            "sure",
            "ok",
            "okay",
            "please",
            "continue",
            "more",
            "help",
            "go on",
        )
    ):
        m = re.match(
            r"^\s*(?:yes|yep|yeah|y|sure|ok(?:ay)?|please|continue|more|help|go on)[\s,.:;-]*(.*)$",
            t,
            flags=re.I,
        )
        remainder = (m.group(1) if m else "").strip()
        return True, remainder
    return None, ""


def run_once(df: pd.DataFrame, seed_text: str | None = None):
    if seed_text:
        user_text = seed_text
    else:
        print("Hello student,What can I help you with today? (free text, no options)")
        user_text = ask("> ")
    topic = classify_free(user_text)
    if topic is None:
        topic = classify_free(
            ask(
                "I didn’t quite catch that—tell me more: are we talking studies, sports, or social life? "
            )
        )
    if topic == "studying":
        studying_flow()
    elif topic == "sports":
        sports_flow(df)
    elif topic == "social":
        social_flow(df)
    else:
        print("I couldn’t confidently infer the topic from free text this time.")


def main():
    df = load_df()
    while True:
        run_once(df)
        ans = ask("\nDo you need anything else? (free text) ")
        more, remainder = wants_more_and_remainder(ans)
        if more is True:
            if remainder:
                print("Cool — continuing with that.")
                run_once(df, seed_text=remainder)
            else:
                print("Cool — tell me what you need next.")
                run_once(df)
            continue
        if more is False:
            print("Got you. Closing the chat — have a solid day! 👋")
            break
        ans2 = ask("Got it — do you want to continue or end it here? ")
        more2, rem2 = wants_more_and_remainder(ans2)
        if more2 is True:
            if rem2:
                print("Alright, continuing with that.")
                run_once(df, seed_text=rem2)
            else:
                run_once(df)
            continue
        print("All good. Ending here — take care! 👋")
        break


if __name__ == "__main__":
    main()
