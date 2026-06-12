"""
Uday AI — Planner Agent
"""

from __future__ import annotations

import json
import logging
from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage

from app.llm.provider import get_llm
from app.agents.state import AgentState

logger = logging.getLogger(__name__)

class PlanStep(BaseModel):
    step_number: int = Field(description="Step number (1-based)")
    tool: str = Field(description="The tool to execute. Must be one of: files, tasks, notes, voice, memory, browser, gmail, calendar, coding, research, github, computer, direct_answer")
    argument: str = Field(description="Parameters or search queries for the tool execution")


class PlannerOutput(BaseModel):
    intent: str = Field(description="User intent classification: files, tasks, notes, voice, memory, browser, gmail, calendar, coding, research, github, computer, direct_answer")
    plan: list[PlanStep] = Field(description="Sequential execution plan steps to resolve the request")
    reasoning: str = Field(description="Reasoning log behind the execution plan")


PLANNER_SYSTEM_PROMPT = """You are the **Planner Agent** for Uday AI, a personal AI Operating System.
Your job is to analyze the user's query and formulate a sequential plan of action.

Available Tools:
1. `files` - Search, upload, query PDFs/text documents (RAG). Use when files/documents are referenced.
2. `tasks` - Create, update, view todo list items. Use for todos, tasks, goals.
3. `notes` - Create, view, search, modify personal memos. Use for quick text notes.
4. `voice` - STT transcription or TTS synthesis queries.
5. `memory` - Fetch specific facts, preferences, or recall user relationships.
6. `browser` - Web browsing, searching, clicking elements, extracting webpage content.
7. `gmail` - Read, draft, send, or summarize emails.
8. `calendar` - Manage events, agenda, weekly schedule.
9. `coding` - Generate, explain, write, or debug software source code.
10. `research` - Detailed web searches, information synthesis, source citations.
11. `github` - Manage pull requests, repositories, issues, or commit changes.
12. `computer` - Open local apps (VS Code, Chrome), open files, directories, and send browser-based WhatsApp messages.
13. `direct_answer` - Use when the request is conversational and requires no tools.

Formulate an optimal plan of steps to execute sequentially.
"""


async def run_planner(state: AgentState) -> dict:
    """
    Run the planner node.
    Parses user query, runs structured LLM output, and populates plan steps in state.
    """
    # Bypass planning if plan is already formulated and we are executing steps
    if state.get("plan") and state.get("current_step", 0) > 0:
        logger.info(f"[Planner] Plan already formulated. Executing step {state.get('current_step') + 1}")
        return {}

    user_msg = state.get("user_message", "")
    if not user_msg:
        # Fallback to last message in history
        messages = state.get("messages", [])
        if messages:
            user_msg = str(messages[-1].content)

    logger.info(f"[Planner] Planning for query: {user_msg[:80]}...")

    llm = get_llm(temperature=0.1)

    try:
        # Structured output binding
        structured_llm = llm.with_structured_output(PlannerOutput)
        planner_res = await structured_llm.ainvoke([
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=user_msg)
        ])

        intent = planner_res.intent
        plan_steps = [
            {"step_number": s.step_number, "tool": s.tool, "argument": s.argument}
            for s in planner_res.plan
        ]
        reasoning = planner_res.reasoning

    except Exception as e:
        logger.warning(f"[Planner] Structured output failed: {e}. Falling back to prompt JSON extraction.")
        # Fallback raw parser
        fallback_prompt = (
            f"{PLANNER_SYSTEM_PROMPT}\n"
            "Output your plan strictly in JSON matching this schema:\n"
            "{\n"
            "  \"intent\": \"files|tasks|notes|voice|memory|direct_answer\",\n"
            "  \"plan\": [\n"
            "    {\"step_number\": 1, \"tool\": \"notes\", \"argument\": \"DAA\"}\n"
            "  ],\n"
            "  \"reasoning\": \"reasoning context\"\n"
            "}\n"
            f"User input: {user_msg}"
        )

        try:
            raw_res = await llm.ainvoke([HumanMessage(content=fallback_prompt)])
            raw_text = raw_res.content.strip()
            # Basic json extractor
            start_idx = raw_text.find("{")
            end_idx = raw_text.rfind("}")
            if start_idx != -1 and end_idx != -1:
                parsed = json.loads(raw_text[start_idx:end_idx + 1])
                intent = parsed.get("intent", "direct_answer")
                plan_steps = parsed.get("plan", [])
                reasoning = parsed.get("reasoning", "")
            else:
                raise ValueError("JSON anchors not found")
        except Exception as fallback_err:
            logger.error(f"[Planner] Fallback parser failed: {fallback_err}")
            intent = "direct_answer"
            plan_steps = [{"step_number": 1, "tool": "direct_answer", "argument": user_msg}]
            reasoning = "Fallback default plan due to extraction failures."

    logger.info(f"[Planner] Formulated Plan (Intent: {intent}): {plan_steps}")

    return {
        "intent": intent,
        "plan": plan_steps,
        "current_step": 0,
        "selected_tools": [plan_steps[0]["tool"]] if plan_steps else [],
        "metadata": {
            **state.get("metadata", {}),
            "planner_reasoning": reasoning
        }
    }
