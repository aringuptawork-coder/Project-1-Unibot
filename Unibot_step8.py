# Step 8 open-ended prompts & enforced outcomes
from __future__ import annotations
import re
from pathlib import Path
from typing import Optional, List, Tuple, Dict
import pandas as pd


CSV = Path("data/unilife.csv")


# ---------- helpers ----------
def ask(msg: str) -> str:
    return input(msg).strip()


def load_df() -> pd.DataFrame:
    df = pd.read_csv(CSV)
    df.columns = [c.strip().lower() for c in df.columns]
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
    return df


def classify_free(text: str) -> Optional[str]:
    t = (text or "").lower()
    s = any(
        w in t
        for w in [
            "study",
            "exam",
            "advisor",
            "deadline",
            "timetable",
            "grades",
            "enrol",
            "enroll",
        ]
    )
    p = any(
        w in t
        for w in [
            "sport",
            "gym",
            "basketball",
            "football",
            "tennis",
            "run",
            "swim",
            "yoga",
        ]
    )
    soc = any(
        w in t
        for w in [
            "event",
            "party",
            "association",
            "club",
            "society",
            "friends",
            "social",
            "meetup",
            "karaoke",
            "dinner",
        ]
    )
    hits = {"studying": int(s), "sports": int(p), "social": int(soc)}
    if sum(hits.values()) == 0 or list(hits.values()).count(1) > 1:
        return None
    return max(hits, key=hits.get)


# ---------- events ----------
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


# ---------- association pref ----------
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


# ---------- sports rec ----------
TYPE_MAP = {
    "team": ["football", "basketball"],
    "ball": ["football", "basketball", "tennis", "table tennis"],
    "cardio": ["running", "swimming", "badminton"],
    "strength": ["aikido"],
    "martial": ["aikido"],
    "racket": ["tennis", "badminton", "table tennis"],
}


def rec_sport(avail: set[str], desc: str) -> str:
    t = desc.lower()
    bucket_order = []
    for key in ["team", "ball", "cardio", "strength", "martial", "racket"]:
        if key in t:
            bucket_order.append(key)
    if not bucket_order:
        bucket_order = ["team", "cardio", "racket"]  # soft default
    for key in bucket_order:
        for s in TYPE_MAP[key]:
            if s in avail:
                return s.title()
    return next(iter(avail)).title() if avail else "Basketball"


# ---------- branch flows that ENFORCE the screenshot rules ----------
def studying_flow():
    # open-ended only; enforce outcomes
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
                " Suggestion: join a study group."
                # per brief: struggling + willing to share → study group"
            )
        else:
            print(
                " Suggestion: contact the student advisor. "
                # struggling + not sharing → advisor
            )
    else:
        print(" Suggestion: use the Student Desk contact form for practical info. ")


def sports_flow(df: pd.DataFrame):
    sports = set(df["sports"].str.lower())
    q1 = ask(
        "Tell me about the sport situation—do you already have a specific sport in mind, or are you exploring? "
    )
    # if clear specific sport appears, check availability
    specific = None
    for s in sports:
        if s in q1.lower():
            specific = s
            break
    if specific:
        print(
            "✅ That sport is available at the university. Please check the University Sports Centre website."
        )
        print("(per brief: specific sport + available → point to Sports Centre)")
        return
    # otherwise follow-up questions then recommend
    q2 = ask(
        "Describe what you want from a sport (e.g., team vibes, ball games, cardio, strength): "
    )
    rec = rec_sport(sports, q2)
    print(
        f"➡️ Recommendation: {rec}. (per brief: exploring → follow-up → recommend from available list)"
    )


def social_flow(df: pd.DataFrame):
    q1 = ask(
        "What are you looking for socially—upcoming events to attend or joining an association? Describe it in your own words. "
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
        events_sorted = parse_events(df["events"].tolist())
        top3 = [lbl for (lbl, _, _) in events_sorted[:3]]
        print(" The three soonest campus events:")
        for e in top3:
            print(" •", e)
        print(" events → suggest three soonest)")
    else:
        pref = ask(
            "Describe what kind of association fits you (e.g., international, artistic, debate, business, wellness, music, film, science, language): "
        )
        assoc = df["associations"].tolist()
        pick = map_assoc(assoc, pref)
        print(
            f" Try joining: {pick}. "
            # (per brief: association path → follow-up → recommend)
        )


import re


def wants_more_and_remainder(text: str):
    """
    Returns:
      (True, remainder)  -> user wants more; 'remainder' is extra text after yes
      (False, "")        -> user is done
      (None, "")         -> unclear
    """
    t = (text or "").strip()
    low = t.lower()

    yes_words = (
        "yes",
        "yep",
        "yeah",
        "y",
        "sure",
        "please",
        "ok",
        "okay",
        "continue",
        "more",
        "help",
        "go on",
    )
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

    # explicit 'no' anywhere → stop
    if any(w in low for w in no_words):
        return False, ""

    # detect 'yes' intent
    if any(low.startswith(w) for w in yes_words) or any(
        f" {w} " in f" {low} " for w in yes_words
    ):
        # grab remainder after a leading yes-ish word + punctuation
        m = re.match(
            r"^\s*(?:yes|yep|yeah|y|sure|ok(?:ay)?|please|continue|more|help|go on)[\s,.:;-]*(.*)$",
            low,
            flags=re.I,
        )
        remainder = (m.group(1) if m else "").strip()
        return True, remainder

    return None, ""


def run_once(df: pd.DataFrame, seed_text: str | None = None):
    if seed_text:
        user_text = seed_text
    else:
        print("What can I help you with today? (free text, no options)")
        user_text = ask("> ")

    topic = classify_free(user_text)
    if topic is None:
        topic = classify_free(
            ask(
                "I didn’t quite catch that—tell me more about whether it’s studies, sports, or social life: "
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


# ---------- main ----------
def main():
    df = load_df()
    while True:
        run_once(df)
        ans = ask("\nDo you need anything else? (free text) ")
        more, remainder = wants_more_and_remainder(ans)

        if more is True:
            if remainder:
                # use the remainder ("I also want to join sports") directly
                print("Cool — continuing with that.")
                run_once(df, seed_text=remainder)
            else:
                print("Cool — tell me what you need next.")
                run_once(df)
            continue

        if more is False:
            print("Got you. Closing the chat — have a solid day! 👋")
            break

        # unclear → one gentle retry (still open-ended)
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

    df = load_df()
    while True:
        run_once(df)
        ans = ask("\nDo you need anything else? (free text) ")
        more = wants_more(ans)
        if more is True:
            print("Cool — tell me what you need next.")
            continue
        if more is False:
            print("Got you. Closing the chat — have a solid day! 👋")
            break
        # unclear → one gentle retry (still open-ended)
        ans2 = ask("Got it — do you want to continue or end it here? ")
        more2 = wants_more(ans2)
        if more2 is True:
            print("Alright, let’s keep going.")
            continue
        print("All good. Ending here — take care! 👋")
        break


if __name__ == "__main__":
    main()
