import os
import json
import logging

from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from google import genai
from google.genai import types

from typing import Dict, Any, List, Optional
from models import db, DiscoverWeek, Submission, AIFeedback, AIToDoItem
load_dotenv()

logger = logging.getLogger(__name__)

# Gemini Function Definitions for Discover Proposal Coach
AI_COACH_TOOLS = [
    {
        "name": "get_week_rubric",
        "description": "Fetch the official objective, focus area, deliverable title, and required rubric checklist criteria for a specific Discover program week.",
        "parameters": {
            "type": "object",
            "properties": {
                "week_number": {
                    "type": "integer",
                    "description": "The Discover program week number (1, 2, 3, or 4)."
                }
            },
            "required": ["week_number"]
        }
    },
    {
        "name": "get_submission_draft",
        "description": "Fetch the current submission draft content, title, executive summary, attachment file name, extracted attachment document text, and status for a given submission ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "submission_id": {
                    "type": "integer",
                    "description": "The unique database ID of the student submission draft."
                }
            },
            "required": ["submission_id"]
        }
    },
    {
        "name": "save_ai_feedback",
        "description": "Persist structured proposal evaluation feedback into the database, including readiness score (0-100), key strengths, identified gaps against the rubric, and suggested actionable next steps.",
        "parameters": {
            "type": "object",
            "properties": {
                "submission_id": {
                    "type": "integer",
                    "description": "The ID of the submission being reviewed."
                },
                "readiness_score": {
                    "type": "integer",
                    "description": "Suggested readiness score from 0 (very incomplete) to 100 (ready for internal evaluation and industry submission)."
                },
                "strengths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of specific strengths identified in the draft corresponding to the rubric."
                },
                "gaps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of missing criteria, weak justifications, or gaps identified relative to the week's rubric."
                },
                "suggested_next_steps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Prioritized actionable recommendations for the student team before final submission."
                }
            },
            "required": ["submission_id", "readiness_score", "strengths", "gaps", "suggested_next_steps"]
        }
    },
    {
        "name": "flag_missing_section",
        "description": "Flag a specific mandatory rubric section that is missing or insufficient in the student draft, creating an actionable to-do item for the team.",
        "parameters": {
            "type": "object",
            "properties": {
                "submission_id": {
                    "type": "integer",
                    "description": "The ID of the submission."
                },
                "section_name": {
                    "type": "string",
                    "description": "The exact name of the missing rubric deliverable or section (e.g., 'Defined Problem Statement', 'Market Validation Evidence')."
                },
                "prompt_for_student": {
                    "type": "string",
                    "description": "A concise, constructive guiding prompt explaining what the student team needs to add or refine to satisfy this rubric requirement."
                }
            },
            "required": ["submission_id", "section_name", "prompt_for_student"]
        }
    }
]

# Tool Execution Handlers
def execute_get_week_rubric(week_number: int) -> Dict[str, Any]:
    week = DiscoverWeek.query.filter_by(week_number=week_number).first()
    if not week:
        return {"error": f"Discover week {week_number} not found in database."}
    return {
        "week_number": week.week_number,
        "title": week.title,
        "focus_area": week.focus_area,
        "objective": week.objective,
        "required_output_title": week.required_output_title,
        "rubric_checklist": week.rubric_checklist
    }

def extract_attachment_text(file_attachment_path: Optional[str]) -> str:
    """
    Extracts text from an attached document (PDF, TXT, MD, CSV, JSON).
    Returns extracted text string, or empty string if no attachment or unable to extract.
    """
    if not file_attachment_path:
        return ""

    base_dir = os.path.abspath(os.path.dirname(__file__))
    clean_path = file_attachment_path.lstrip("/").replace("\\", "/")
    full_path = os.path.join(base_dir, clean_path)

    if not os.path.exists(full_path):
        alt_path = os.path.join(base_dir, "uploads", os.path.basename(file_attachment_path))
        if os.path.exists(alt_path):
            full_path = alt_path
        else:
            return ""

    try:
        ext = os.path.splitext(full_path)[1].lower()
        if ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(full_path)
                pages_text = []
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text and text.strip():
                        pages_text.append(f"--- [Attachment Page {i+1}] ---\n{text.strip()}")
                return "\n\n".join(pages_text)
            except Exception as pdf_err:
                logger.warning("Error extracting text with pypdf: %s", pdf_err)
                return ""
        elif ext in [".txt", ".md", ".csv", ".json"]:
            with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
    except Exception as e:
        logger.warning("Failed to extract text from attachment '%s': %s", full_path, e)
        return ""
    return ""

def execute_get_submission_draft(submission_id: int) -> Dict[str, Any]:
    sub = db.session.get(Submission, submission_id)
    if not sub:
        return {"error": f"Submission {submission_id} not found."}
    
    attachment_text = extract_attachment_text(sub.file_attachment_path)

    return {
        "submission_id": sub.id,
        "team_id": sub.team_id,
        "team_name": sub.team.name if sub.team else "Unknown Team",
        "week_number": sub.week_number,
        "title": sub.title or "",
        "executive_summary": sub.executive_summary or "",
        "content": sub.content or "",
        "file_attachment_name": sub.file_attachment_name or "None",
        "attachment_extracted_text": attachment_text if attachment_text else "No attachment or no readable text extracted.",
        "status": sub.status
    }

def execute_save_ai_feedback(submission_id: int, readiness_score: int, strengths: List[str], gaps: List[str], suggested_next_steps: List[str], raw_summary: str = "") -> Dict[str, Any]:
    sub = db.session.get(Submission, submission_id)
    if not sub:
        return {"error": f"Submission {submission_id} not found."}
    
    # Cap readiness score between 0 and 100
    readiness_score = max(0, min(100, int(readiness_score)))
    
    feedback = AIFeedback.query.filter_by(submission_id=submission_id).first()
    if not feedback:
        feedback = AIFeedback(submission_id=submission_id)
        db.session.add(feedback)

    feedback.readiness_score = readiness_score
    feedback.strengths_json = json.dumps(strengths)
    feedback.gaps_json = json.dumps(gaps)
    feedback.suggested_next_steps_json = json.dumps(suggested_next_steps)
    feedback.raw_summary = raw_summary or f"Proposal Coach evaluated submission with readiness score {readiness_score}/100."

    db.session.commit()
    return {
        "status": "success",
        "message": f"AI Feedback saved successfully. Readiness Score: {readiness_score}/100.",
        "readiness_score": readiness_score,
        "feedback_id": feedback.id
    }

def execute_flag_missing_section(submission_id: int, section_name: str, prompt_for_student: str) -> Dict[str, Any]:
    sub = db.session.get(Submission, submission_id)
    if not sub:
        return {"error": f"Submission {submission_id} not found."}

    # Check if item already exists to avoid duplicates
    existing = AIToDoItem.query.filter_by(
        submission_id=submission_id,
        section_name=section_name
    ).first()

    if not existing:
        todo = AIToDoItem(
            submission_id=submission_id,
            section_name=section_name,
            prompt_for_student=prompt_for_student,
            is_resolved=False
        )
        db.session.add(todo)
        db.session.commit()
        return {
            "status": "success",
            "message": f"Flagged missing section: '{section_name}' as a student to-do item.",
            "todo_id": todo.id
        }
    else:
        existing.prompt_for_student = prompt_for_student
        db.session.commit()
        return {
            "status": "success",
            "message": f"Updated existing to-do item for '{section_name}'.",
            "todo_id": existing.id
        }


def dispatch_tool(tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    """Routes Gemini function calls to corresponding local database function."""
    if tool_name == "get_week_rubric":
        return execute_get_week_rubric(tool_input.get("week_number", 1))
    elif tool_name == "get_submission_draft":
        return execute_get_submission_draft(tool_input.get("submission_id", 0))
    elif tool_name == "save_ai_feedback":
        return execute_save_ai_feedback(
            submission_id=tool_input.get("submission_id", 0),
            readiness_score=tool_input.get("readiness_score", 50),
            strengths=tool_input.get("strengths", []),
            gaps=tool_input.get("gaps", []),
            suggested_next_steps=tool_input.get("suggested_next_steps", [])
        )
    elif tool_name == "flag_missing_section":
        return execute_flag_missing_section(
            submission_id=tool_input.get("submission_id", 0),
            section_name=tool_input.get("section_name", "Missing Section"),
            prompt_for_student=tool_input.get("prompt_for_student", "Please review and complete this required section.")
        )
    else:
        return {"error": f"Unknown tool: {tool_name}"}


def run_gemini_agent(sub: Submission, api_key: str) -> Dict[str, Any]:
    """Executes the agentic loop using Google Gemini API."""
    submission_id = sub.id
    week_number = sub.week_number
    team_name = sub.team.name if sub.team else f"Team {sub.team_id}"

    client = genai.Client(api_key=api_key)

    system_prompt = (
        "You are the DegreeLabs Discover Proposal Coach. You evaluate student team proposal drafts strictly "
        "against the official DegreeLabs Discover program week rubric.\n\n"
        "Execution Instructions:\n"
        "1. First, call `get_week_rubric(week_number)` to retrieve the mandatory objectives and checklist criteria for this week.\n"
        "2. Next, call `get_submission_draft(submission_id)` to inspect the student team's draft content, title, summary, and any attached document text (`attachment_extracted_text`).\n"
        "3. Thoroughly cross-reference the draft text and attached document text against every rubric checklist criterion.\n"
        "4. Call `save_ai_feedback` with an objective readiness score (0-100), verified strengths, rubric gaps, and prioritized next steps.\n"
        "5. If any mandatory rubric items or key sections are missing or insufficient, call `flag_missing_section` "
        "for EACH missing element so the student team gets clear actionable to-do items.\n"
        "6. After all tools are executed, provide a concise, motivating 2-paragraph natural-language summary summarizing "
        "where the draft stands and what the team should focus on before final submission.\n"
        "Do not hallucinate external requirements outside the official rubric."
    )

    initial_message = (
        f"Review the Week {week_number} submission for Team '{team_name}' (Submission ID: {submission_id}). "
        f"Please fetch the week rubric and submission draft, assess proposal readiness, persist structured feedback, "
        f"and flag any missing rubric sections."
    )

    messages = [
        {
            "role": "user",
            "parts": [
                {"text": initial_message}
            ]
        }
    ]

    max_turns = 8
    summary_text = ""
    tool_call_log = []

    for turn in range(max_turns):
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=messages,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.0,
                tools=[
                    types.Tool(
                        function_declarations=AI_COACH_TOOLS
                    )
                ]
            )
        )

        if response.candidates:
            for cand in response.candidates:
                if cand.content and cand.content.parts:
                    for part in cand.content.parts:
                        if getattr(part, "text", None):
                            summary_text += part.text

        function_calls = response.function_calls
        if not function_calls:
            break

        messages.append(response.candidates[0].content)

        function_response_parts = []
        for function_call in function_calls:
            t_name = function_call.name
            t_input = function_call.args

            result_data = dispatch_tool(t_name, t_input)
            tool_call_log.append({
                "tool": t_name,
                "input": t_input,
                "result": result_data
            })

            function_response_parts.append(
                types.Part.from_function_response(
                    name=t_name,
                    response=result_data
                )
            )

        messages.append(
            types.Content(
                role="tool",
                parts=function_response_parts
            )
        )

    # Update raw summary in DB feedback
    fb = AIFeedback.query.filter_by(submission_id=submission_id).first()
    if fb and summary_text.strip():
        fb.raw_summary = summary_text.strip()
        db.session.commit()

    return {
        "success": True,
        "mode": "agentic_gemini",
        "summary": summary_text.strip() or "Evaluation completed by Proposal Coach.",
        "tool_calls": tool_call_log,
        "feedback": {
            "readiness_score": fb.readiness_score if fb else 75,
            "strengths": fb.strengths if fb else [],
            "gaps": fb.gaps if fb else [],
            "suggested_next_steps": fb.suggested_next_steps if fb else []
        },
        "todos": [
            {"section_name": t.section_name, "prompt": t.prompt_for_student}
            for t in AIToDoItem.query.filter_by(submission_id=submission_id).all()
        ]
    }


def run_groq_agent(sub: Submission, api_key: str) -> Dict[str, Any]:
    """Executes the agentic loop using Groq API (e.g. Llama 3.3 70B) with function calling."""
    from groq import Groq
    client = Groq(api_key=api_key)

    submission_id = sub.id
    week_number = sub.week_number
    team_name = sub.team.name if sub.team else f"Team {sub.team_id}"

    groq_tools = [{"type": "function", "function": tool} for tool in AI_COACH_TOOLS]

    system_prompt = (
        "You are the DegreeLabs Discover Proposal Coach. You evaluate student team proposal drafts strictly "
        "against the official DegreeLabs Discover program week rubric.\n\n"
        "Execution Instructions:\n"
        "1. First, call `get_week_rubric(week_number)` to retrieve the mandatory objectives and checklist criteria for this week.\n"
        "2. Next, call `get_submission_draft(submission_id)` to inspect the student team's draft content, title, summary, and any attached document text (`attachment_extracted_text`).\n"
        "3. Thoroughly cross-reference the draft text and attached document text against every rubric checklist criterion.\n"
        "4. Call `save_ai_feedback` with an objective readiness score (0-100), verified strengths, rubric gaps, and prioritized next steps.\n"
        "5. If any mandatory rubric items or key sections are missing or insufficient, call `flag_missing_section` "
        "for EACH missing element so the student team gets clear actionable to-do items.\n"
        "6. After all tools are executed, provide a concise, motivating 2-paragraph natural-language summary summarizing "
        "where the draft stands and what the team should focus on before final submission.\n"
        "Do not hallucinate external requirements outside the official rubric."
    )

    initial_message = (
        f"Review the Week {week_number} submission for Team '{team_name}' (Submission ID: {submission_id}). "
        f"Please fetch the week rubric and submission draft, assess proposal readiness, persist structured feedback, "
        f"and flag any missing rubric sections."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": initial_message}
    ]

    groq_models = ["openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile"]
    selected_model = groq_models[0]

    max_turns = 8
    summary_text = ""
    tool_call_log = []

    for turn in range(max_turns):
        # Try candidate models in case of model access availability
        response = None
        for model_name in groq_models:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    tools=groq_tools,
                    tool_choice="auto",
                    temperature=0.0
                )
                selected_model = model_name
                break
            except Exception as model_err:
                if "model_not_found" in str(model_err) or "does not exist" in str(model_err):
                    continue
                raise model_err

        if response is None:
            raise RuntimeError("No supported Groq models available for tool calling.")

        response_message = response.choices[0].message
        messages.append(response_message)

        if response_message.content:
            summary_text += response_message.content

        tool_calls = response_message.tool_calls
        if not tool_calls:
            break

        for tool_call in tool_calls:
            t_name = tool_call.function.name
            try:
                t_input = json.loads(tool_call.function.arguments)
            except Exception:
                t_input = {}

            result_data = dispatch_tool(t_name, t_input)
            tool_call_log.append({
                "tool": t_name,
                "input": t_input,
                "result": result_data
            })

            messages.append({
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": t_name,
                "content": json.dumps(result_data)
            })

    # Update raw summary in DB feedback
    fb = AIFeedback.query.filter_by(submission_id=submission_id).first()
    if fb and summary_text.strip():
        fb.raw_summary = summary_text.strip()
        db.session.commit()

    return {
        "success": True,
        "mode": f"agentic_groq ({selected_model})",
        "summary": summary_text.strip() or "Evaluation completed by Proposal Coach.",
        "tool_calls": tool_call_log,
        "feedback": {
            "readiness_score": fb.readiness_score if fb else 75,
            "strengths": fb.strengths if fb else [],
            "gaps": fb.gaps if fb else [],
            "suggested_next_steps": fb.suggested_next_steps if fb else []
        },
        "todos": [
            {"section_name": t.section_name, "prompt": t.prompt_for_student}
            for t in AIToDoItem.query.filter_by(submission_id=submission_id).all()
        ]
    }


def run_proposal_coach_agent(submission_id: int) -> Dict[str, Any]:
    """
    Executes the multi-turn agentic Proposal Coach loop with multi-provider fallback:
    1. If GROQ_API_KEY is configured, runs with Groq (Llama 3.3 70B).
    2. If GEMINI_API_KEY is configured, runs with Google Gemini.
    3. If quota is exceeded or an error occurs, seamlessly attempts the alternate provider.
    4. If no keys are set or all providers fail, falls back gracefully to heuristic rubric coach.
    """
    sub = db.session.get(Submission, submission_id)
    if not sub:
        return {"success": False, "error": f"Submission {submission_id} not found."}

    # Clear previous unresolved AI to-do items before new evaluation run
    AIToDoItem.query.filter_by(submission_id=submission_id, is_resolved=False).delete()
    db.session.commit()

    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()

    # Strategy: Try Groq first if key present (high free limits), or Gemini
    providers = []
    if groq_key:
        providers.append(("groq", lambda: run_groq_agent(sub, groq_key)))
    if gemini_key:
        providers.append(("gemini", lambda: run_gemini_agent(sub, gemini_key)))

    for name, runner in providers:
        try:
            return runner()
        except Exception as e:
            logger.warning("Provider '%s' failed (quota or error): %s. Trying next provider.", name, str(e))

    # Graceful fallback when no keys are configured or all API calls failed
    return run_heuristic_rubric_coach(sub, is_fallback=True)


def run_heuristic_rubric_coach(sub: Submission, is_fallback: bool = True, error_msg: Optional[str] = None) -> Dict[str, Any]:
    """
    Robust rubric-grounded heuristic evaluator used when GEMINI_API_KEY is not set or network fails.
    Inspects draft text against week's rubric criteria, calculates score, and flags missing sections.
    """
    week = DiscoverWeek.query.filter_by(week_number=sub.week_number).first()
    checklist = week.rubric_checklist if week else []
    
    attachment_text = extract_attachment_text(sub.file_attachment_path)
    content = (sub.content or "") + " " + (sub.executive_summary or "") + " " + (sub.title or "") + " " + attachment_text
    content_lower = content.lower()
    
    strengths = []
    gaps = []
    missing_sections = []
    score_points = 0
    total_criteria = len(checklist) if checklist else 1
    points_per_item = 100 // total_criteria

    for item in checklist:
        # Check if keywords from rubric criterion appear in draft text
        keywords = [w.lower() for w in item.replace(",", " ").replace("-", " ").split() if len(w) > 4]
        match_count = sum(1 for kw in keywords if kw in content_lower)
        
        if len(keywords) > 0 and (match_count / len(keywords)) >= 0.4:
            strengths.append(f"Addressed: {item}")
            score_points += points_per_item
        else:
            gaps.append(f"Requires elaboration: {item}")
            missing_sections.append(item)

    # Length and depth heuristic adjustment
    word_count = len(content.split())
    if word_count > 350:
        score_points = min(100, score_points + 15)
        strengths.append(f"Comprehensive proposal draft ({word_count} words drafted).")
    elif word_count > 150:
        score_points = min(100, score_points + 5)
    else:
        gaps.append("Draft is brief (< 150 words); expand analytical detail and supporting rationale.")

    readiness_score = max(25, min(95, score_points))

    next_steps = [
        f"Incorporate missing rubric section: '{missing_sections[0]}'" if missing_sections else "Review draft with team for final formatting.",
        "Refine executive summary to highlight key business impact and ROI metrics.",
        "Schedule a mentor review slot to validate assumptions before final submission."
    ]

    # Save to database
    save_res = execute_save_ai_feedback(
        submission_id=sub.id,
        readiness_score=readiness_score,
        strengths=strengths,
        gaps=gaps,
        suggested_next_steps=next_steps,
        raw_summary=(
            f"Discover Proposal Coach completed rubric review. The draft scored a readiness score of {readiness_score}/100. "
            f"The team has strong foundations but needs to address {len(missing_sections)} specific rubric items before final evaluator submission."
        )
    )

    for item in missing_sections:
        execute_flag_missing_section(
            submission_id=sub.id,
            section_name=item,
            prompt_for_student=f"Provide dedicated details and evidence for '{item}' per Week {sub.week_number} deliverable requirements."
        )

    todos = AIToDoItem.query.filter_by(submission_id=sub.id).all()

    notice = " (Running in simulated rubric mode: add GEMINI_API_KEY in .env for live Gemini agent)" if is_fallback else ""

    return {
        "success": True,
        "mode": "heuristic_fallback",
        "notice": notice,
        "error_detail": error_msg,
        "summary": (
            f"Proposal Coach Rubric Assessment completed for Week {sub.week_number}{notice}. "
            f"Readiness Score: {readiness_score}/100. "
            f"Identified {len(strengths)} strengths and {len(gaps)} areas for improvement."
        ),
        "feedback": {
            "readiness_score": readiness_score,
            "strengths": strengths,
            "gaps": gaps,
            "suggested_next_steps": next_steps
        },
        "todos": [
            {"section_name": t.section_name, "prompt": t.prompt_for_student}
            for t in todos
        ]
    }
