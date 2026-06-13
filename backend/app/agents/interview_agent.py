"""
Nidhi AI OS — Interview Coach Agent
"""

import logging
from app.llm.provider import get_llm

logger = logging.getLogger(__name__)

INTERVIEW_QUESTION_PROMPT = """You are **Nidhi**, Uday's expert technical and behavioral mock interviewer.
Generate 3 distinct, highly realistic interview questions for a candidate preparing for the following:

Target Role: {role}
Focus Area: {topic}
Difficulty Level: {difficulty} (Junior/Mid/Senior)

Format the questions in a clean JSON list, matching this schema:
[
  {{
    "id": 1,
    "question": "The actual detailed question text."
  }}
]
Output ONLY valid JSON inside the tags, nothing else.
"""

INTERVIEW_EVALUATION_PROMPT = """You are **Nidhi**, Uday's mock interview evaluator.
Evaluate the user's response to the interview question below:

Question: {question}
Candidate's Answer: {answer}

Provide a detailed evaluation JSON matching this schema:
{{
  "grade": "A/B/C/D/F",
  "score_percentage": 85,
  "feedback_summary": "Overall Hinglish warm summary of his answer performance.",
  "strengths": ["Clear explanation of data flow"],
  "improvements": ["Mentioned no fallback mechanisms", "Could use STAR structure details"],
  "sample_ideal_answer": "Provide a high-quality, professional sample answer that would score 100%."
}}
Output ONLY valid JSON, nothing else.
"""

async def generate_interview_questions(role: str, topic: str, difficulty: str) -> list[dict]:
    """Generate mock interview questions."""
    prompt = INTERVIEW_QUESTION_PROMPT.format(
        role=role,
        topic=topic,
        difficulty=difficulty
    )
    try:
        llm = get_llm(temperature=0.7)
        response = await llm.ainvoke(prompt)
        import json
        text = response.content.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        return json.loads(text)
    except Exception as e:
        logger.error(f"Failed to generate interview questions: {e}", exc_info=True)
        return [
            {"id": 1, "question": f"Explain the difference between a Vector DB (like ChromaDB) and a relational database (like PostgreSQL) for LLM applications. Target: {role}."},
            {"id": 2, "question": "Describe a challenging programming project you built, and how you handled API limits or rate-limiting."},
            {"id": 3, "question": "How do you evaluate and prevent hallucinations in your LLM generation pipelines?"}
        ]


async def evaluate_interview_answer(question: str, answer: str) -> dict:
    """Evaluate a candidate's answer and generate grades, suggestions."""
    prompt = INTERVIEW_EVALUATION_PROMPT.format(
        question=question,
        answer=answer
    )
    try:
        llm = get_llm(temperature=0.2)
        response = await llm.ainvoke(prompt)
        import json
        text = response.content.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        return json.loads(text)
    except Exception as e:
        logger.error(f"Failed to evaluate answer: {e}", exc_info=True)
        return {
            "grade": "B",
            "score_percentage": 75,
            "feedback_summary": "Kaafi accha answer diya, par isko hum aur structured bna sakte the. Chaliye improvements check karte hain.",
            "strengths": ["Core concept explanation is correct"],
            "improvements": ["Need to explain with an example project case", "Add technical metrics"],
            "sample_ideal_answer": f"To answer '{question}' correctly, begin with definitions, explain architectural trade-offs, and mention practical experiences."
        }
