# minimal CLI loop with clarification + MC fallback
from typing import Optional


def classify(text: str) -> Optional[str]:
    t = (text or "").lower()
    study_kw = {
        "study",
        "studying",
        "Studies",
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


def ask(prompt: str) -> str:
    return input(prompt).strip()


def main():
    print("👋 Hi, I'm Unibot. What can I help you with today?")
    user = ask("> ")
    topic = classify(user)

    if topic is None:
        print(
            "That could be a few things. Is it mainly Studying, Sports, or Social activities?"
        )
        user = ask("> ")
        topic = classify(user)

    if topic is None:
        print("Let me be precise: [1] Studying  [2] Sports  [3] Social")
        choice = ask("> ")
        topic = {"1": "studying", "2": "sports", "3": "social"}.get(choice)

    if topic is None:
        print("I couldn't determine the topic. Let's try again later.")
        return

    print(f"✅ Topic selected: {topic}")


if __name__ == "__main__":
    main()
