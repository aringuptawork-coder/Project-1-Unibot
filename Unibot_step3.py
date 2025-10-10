# classify free text into: studying / sports / social / None
def classify(text: str):
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

    # pick the unique max; otherwise return None
    best_topic, best_score = max(scores.items(), key=lambda kv: kv[1])
    if best_score == 0 or list(scores.values()).count(best_score) > 1:
        return None
    return best_topic


# tiny smoke tests
tests = [
    "where is the gym and how do I register",
    "i need help with my exam timetable",
    "are there any parties or clubs this week",
    "help",
]
for s in tests:
    print(f"{s!r} -> {classify(s)}")
