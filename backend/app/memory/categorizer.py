"""
Nidhi — Memory Categorizer

Automatically categorizes memories using LLM analysis.
Categories: preference, goal, fact, event, relationship, habit, skill.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# ── Category definitions ─────────────────────────────────────────────

MEMORY_CATEGORIES = {
    "preference": {
        "description": "User likes, dislikes, preferences, favorites",
        "keywords": [
            "like", "love", "prefer", "favorite", "hate", "dislike",
            "enjoy", "want", "wish", "rather", "best", "worst",
            "pasand", "achha", "bura", "favourite",
        ],
        "examples": [
            "I love dark mode",
            "My favorite color is blue",
            "I prefer Python over JavaScript",
        ],
    },
    "goal": {
        "description": "User goals, ambitions, plans, targets",
        "keywords": [
            "goal", "want to", "plan", "aim", "dream", "achieve",
            "target", "aspire", "working on", "building", "learning",
            "karna hai", "seekhna", "banana hai",
        ],
        "examples": [
            "I want to become an AI engineer",
            "My goal is to learn LangGraph",
        ],
    },
    "fact": {
        "description": "Personal facts, information about the user",
        "keywords": [
            "i am", "my name", "i work", "i live", "i study",
            "my age", "born in", "graduated", "profession",
            "mera naam", "mein kaam", "mein rehta",
        ],
        "examples": [
            "My name is Uday",
            "I am a software developer",
            "I live in India",
        ],
    },
    "event": {
        "description": "Events, meetings, appointments, past happenings",
        "keywords": [
            "meeting", "event", "appointment", "yesterday", "tomorrow",
            "next week", "last month", "happened", "scheduled",
            "kal", "parso", "next", "last",
        ],
        "examples": [
            "I have a meeting tomorrow at 3 PM",
            "Yesterday I finished the project",
        ],
    },
    "relationship": {
        "description": "Information about people the user knows",
        "keywords": [
            "friend", "brother", "sister", "mother", "father", "boss",
            "colleague", "wife", "husband", "partner", "team",
            "bhai", "behen", "dost", "maa", "papa",
        ],
        "examples": [
            "My friend Rahul works at Google",
            "My boss is very supportive",
        ],
    },
    "habit": {
        "description": "User routines, habits, daily patterns",
        "keywords": [
            "usually", "always", "every day", "routine", "habit",
            "morning", "night", "daily", "weekly", "regular",
            "roz", "hamesha", "subah", "raat",
        ],
        "examples": [
            "I wake up at 6 AM every day",
            "I always code at night",
        ],
    },
    "skill": {
        "description": "User skills, expertise, technologies known",
        "keywords": [
            "know", "expert", "experienced", "skill", "proficient",
            "familiar", "certified", "built", "developed",
            "aata hai", "seekha", "jaanta",
        ],
        "examples": [
            "I know Python and React",
            "I have 5 years of experience in ML",
        ],
    },
}


def categorize_memory(content: str) -> str:
    """
    Categorize a memory based on keyword matching.

    This is a fast, rule-based categorizer. For higher accuracy,
    use `categorize_memory_with_llm()` which uses the LLM.

    Args:
        content: The memory content text.

    Returns:
        Category string (e.g., 'preference', 'goal', 'fact').
    """
    content_lower = content.lower()
    scores: dict[str, int] = {}

    for category, info in MEMORY_CATEGORIES.items():
        score = 0
        for keyword in info["keywords"]:
            # Count keyword occurrences
            pattern = r"\b" + re.escape(keyword) + r"\b"
            matches = re.findall(pattern, content_lower)
            score += len(matches)
        scores[category] = score

    # Return the highest-scoring category, default to 'fact'
    if max(scores.values()) == 0:
        return "fact"

    return max(scores, key=scores.get)


def estimate_importance(content: str) -> float:
    """
    Estimate the importance of a memory (0.0 — 1.0).

    Heuristic-based: longer, more specific content is more important.
    """
    score = 0.5  # baseline

    # Length bonus (more detail = more important)
    word_count = len(content.split())
    if word_count > 20:
        score += 0.1
    if word_count > 50:
        score += 0.1

    # Personal info bonus
    personal_markers = [
        "my name", "i am", "i work", "my goal", "i want",
        "important", "remember", "always", "never forget",
    ]
    for marker in personal_markers:
        if marker in content.lower():
            score += 0.05

    # Emotional emphasis bonus
    if any(w in content.lower() for w in ["love", "hate", "dream", "passion"]):
        score += 0.1

    return min(score, 1.0)


def get_category_info() -> dict:
    """Return category definitions for reference."""
    return {
        cat: {
            "description": info["description"],
            "examples": info["examples"],
        }
        for cat, info in MEMORY_CATEGORIES.items()
    }
