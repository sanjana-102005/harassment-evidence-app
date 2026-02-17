import re


def _contains_any(text, phrases):
    for p in phrases:
        if p in text:
            return True
    return False


def detect_harassment_types(text: str):
    """
    Returns:
      detected_types: list[str]
      rule_hits: dict[str, list[str]]  (category -> matched phrases)
    """

    text = (text or "").lower().strip()

    detected = []
    hits = {}

    RULES = {
        "Sexual Harassment / Physical Touching": [
            "touched me",
            "touch me",
            "touched my",
            "grabbed",
            "groped",
            "molested",
            "kissed me",
            "forced kiss",
            "sexual",
            "inappropriately",
            "rubbed",
            "pressed against",
            "assaulted",
        ],
        "Workplace Harassment": [
            "boss",
            "manager",
            "hr",
            "office",
            "workplace",
            "team lead",
            "supervisor",
            "colleague",
            "coworker",
            "job",
            "promotion",
            "salary",
        ],
        "Stalking / Repeated Contact": [
            "stalking",
            "followed me",
            "following me",
            "keeps calling",
            "keeps texting",
            "repeatedly",
            "won't stop",
            "outside my house",
            "waited for me",
        ],
        "Threat / Intimidation": [
            "threat",
            "threatened",
            "kill",
            "hurt you",
            "ruin your life",
            "destroy",
            "beat you",
            "i will leak",
            "i will expose",
            "you will regret",
        ],
        "Blackmail / Sextortion": [
            "blackmail",
            "extort",
            "money",
            "pay me",
            "send nudes",
            "nudes",
            "private photos",
            "leak your photos",
            "leak your video",
        ],
        "Online Sexual Harassment / Obscene Content": [
            "dick pic",
            "nude",
            "porn",
            "sex video",
            "obscene",
            "dirty messages",
            "explicit",
        ],
        "Hate-based Harassment": [
            "caste",
            "religion",
            "muslim",
            "hindu",
            "christian",
            "dalit",
            "lower caste",
            "slur",
            "hate",
        ],
        "General Verbal Abuse": [
            "idiot",
            "bitch",
            "slut",
            "whore",
            "stupid",
            "ugly",
            "f***",
            "fuck",
            "bastard",
        ],
    }

    for category, phrases in RULES.items():
        matched = []
        for p in phrases:
            if p in text:
                matched.append(p)

        if matched:
            detected.append(category)
            hits[category] = matched

    # small regex check for phone numbers / repeated contact signals
    if re.search(r"\b\d{10}\b", text) and "Stalking / Repeated Contact" not in detected:
        detected.append("Stalking / Repeated Contact")
        hits["Stalking / Repeated Contact"] = ["10-digit-number-pattern"]

    return detected, hits