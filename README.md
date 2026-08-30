# DegreeLabs "Discover" MVP Prototype

A working prototype web application for **DegreeLabs Discover** — the 4-week student capability accelerator where 5-member student teams work on real-world enterprise problem statements, engage with dedicated industry mentors on-platform, iterate on weekly deliverables with an **agentic AI Proposal Coach**, and undergo internal evaluation and shortlisting for company review.

---

## 1. Quick Start & Execution Guide

### Prerequisites
- Python 3.11+
- (Optional) `ANTHROPIC_API_KEY` for live Claude 3.5 Sonnet Proposal Coach execution. If omitted, the application runs in a simulated rubric evaluation mode with zero crashes.

### Run in 3 Commands:
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Seed the database with realistic demo data
python seed.py

# 3. Start the Flask application
python app.py
```

Open your browser and navigate to: `http://localhost:5000`

---

## 2. Seeded Demo Accounts (1-Click Login Available)

For seamless live assessment and walkthroughs, the login screen (`/login`) includes **1-Click Quick Login** buttons for all 4 roles:

| Role | Name | Seeded Username | Seeded Password | Core Functionality |
|---|---|---|---|---|
| **Student (Lead)** | Aarav Sharma | `aarav.student` | `student123` | View assigned project, track 4-week progress, draft deliverables, run AI Coach feedback, request mentor slots, view Capability Passport. |
| **Mentor** | Dr. Maya Patel | `maya.mentor` | `mentor123` | Declare availability slots, review and accept/decline team session requests, provide guidance notes. |
| **Evaluator / Admin** | Sarah Jenkins | `sarah.evaluator` | `evaluator123` | Internal quality gate: score submissions on rubric, compare AI readiness vs human score side-by-side, shortlist or reject proposals. |
| **Company Reviewer** | Vikram Malhotra | `vikram.company` | `company123` | View **only shortlisted** proposals for Aurex Retail, select exactly one winning proposal to proceed to Phase 2 (Validate). |

---

## 3. Business Justification for the AI Proposal Coach

> Weekly student outputs undergo internal evaluation and scoring by DegreeLabs academic and industry directors before any deliverable reaches the client company. Providing student teams with structured, rubric-grounded AI feedback *before* final submission reduces wasted evaluator turnaround time, catches missing deliverable components early, and directly elevates proposal quality — directly serving the mission of verifiable, evidence-based capability rather than AI decoration.

### The Agentic Tool-Use Loop

The **Discover Proposal Coach** is built as an autonomous multi-turn tool-calling agent using the Anthropic Python SDK (`anthropic` tool-use API):

```
                       ┌───────────────────────────────┐
                       │  Student clicks "Get AI       │
                       │  Feedback" on Submission Form │
                       └───────────────┬───────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │  Claude Agent receives        │
                       │  Review Task (Week N, Team X) │
                       └───────────────┬───────────────┘
                                       │
               ┌───────────────────────┴───────────────────────┐
               ▼                                               ▼
    1. get_week_rubric(week_num)                 2. get_submission_draft(sub_id)
    Queries DiscoverWeek rubric checklist        Queries title, summary & content text
               │                                               │
               └───────────────────────┬───────────────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │  Agent Reasons & Cross-Checks │
                       │  Draft against Rubric Criteria│
                       └───────────────┬───────────────┘
                                       │
               ┌───────────────────────┴───────────────────────┐
               ▼                                               ▼
    3. save_ai_feedback(...)                     4. flag_missing_section(...)
    Persists readiness score (0-100),            Flags missing rubric items as
    strengths, gaps, & next steps                actionable student to-do items
               │                                               │
               └───────────────────────┬───────────────────────┘
                                       │
                                       ▼
                       ┌───────────────────────────────┐
                       │  Agent returns natural-       │
                       │  language summary to student  │
                       └───────────────────────────────┘
```

1. **Tool `get_week_rubric(week_number)`**: Fetches official week objective and rubric checklist items from the database.
2. **Tool `get_submission_draft(submission_id)`**: Retrieves the student team's drafted proposal text, executive summary, and uploaded artifacts.
3. **Tool `save_ai_feedback(submission_id, readiness_score, strengths, gaps, suggested_next_steps)`**: Persists structured findings, readiness score (0–100), verified strengths, and rubric gaps into the `AIFeedback` table.
4. **Tool `flag_missing_section(submission_id, section_name, prompt_for_student)`**: Iteratively called for each missing rubric element to create actionable to-do checklist items in `AIToDoItem`.
5. **Graceful Fallback**: If `ANTHROPIC_API_KEY` is not present in `.env`, the agent gracefully triggers a deterministic rubric keyword evaluation engine so the demo remains fully interactive without errors.

---

## 4. All 10 Screens Built in Discover MVP

1. **Screen 1: Login & Role Selection** (`/login`) — DegreeLabs brand interface with 1-click role switcher tiles.
2. **Screen 2: Student Dashboard** (`/student/dashboard`) — Current week indicator, 4-week milestone progress bar, assigned company project overview, upcoming session countdown, dynamic next-action banner.
3. **Screen 3: Assigned Project & Company Problem** (`/project`) — Aurex Retail Analytics company profile, enterprise problem statement, 4-week scope boundaries, SLA constraints, and non-elective assignment badge.
4. **Screen 4: Discover Timeline (Weeks 1–4)** (`/timeline`) — Interactive 4-step visual tracker with status badges and deliverable checklists.
5. **Screen 5: Week Detail** (`/week/<int:week_num>`) — Objective, breakdown of that week's learning (8 total) vs. working (4 total) sessions, status indicators, and mock recording modals.
6. **Screen 6: Team Workspace** (`/team`) — 5-member roster with university disciplines, shared collaborative scratchpad with save/load, mentor guidance feed, and submission history.
7. **Screen 7: Mentor Availability & Booking** (`/mentor/sessions`) — Mentor declared slots, student booking modal with topic/agenda, mentor accept/decline controls, and meeting links.
8. **Screen 8: Output Submission & AI Coach Drawer** (`/submissions/<int:week_num>`) — Proposal editor, file attachment upload (`/uploads`), "Get AI Feedback" button, live AI Coach drawer with readiness score gauge, gaps, strengths, and to-do item checkboxes.
9. **Screen 9: Evaluation & Shortlisting Dashboard** (`/evaluator/dashboard`) — Evaluator/Admin quality gate, side-by-side human score vs. AI readiness score, rubric scoring modal, and 1-click shortlist/reject actions.
10. **Screen 10: Capability Passport Preview** (`/passport`) — Read-only credential preview, verified milestone badges, competency matrix bars (Problem Decomposition, Research, Technical Architecture, Business Strategy, Executive Communication), and evidence audit log.

---

## 5. Submission Lifecycle Status Model

Every weekly output moves through an explicit lifecycle enum enforced in `models.py` and controllers:

```
assigned  ──►  working  ──►  submitted  ──►  evaluated  ──►  shortlisted  ──►  next phase
                                                             │
                                                             └──► rejected
```

- **`assigned`**: Week initialized.
- **`working`**: Team actively drafting in the workspace and running AI Coach reviews.
- **`submitted`**: Team locked and submitted for internal DegreeLabs review.
- **`evaluated`**: Internal evaluator scored criteria on rubric.
- **`shortlisted`**: Approved by evaluator; now visible on Company Reviewer dashboard.
- **`rejected`**: Not approved; revision requested before company visibility.
- **`next phase`**: Selected by Company Reviewer to proceed to Phase 2 (Validate).

---

## 6. Assumptions & Scope Boundaries

1. **Non-Elective Project Assignment**: In DegreeLabs Discover, student teams are matched directly with enterprise company problems by program directors rather than selecting projects from a catalog.
2. **5-Member Cross-Functional Teams**: Teams are seeded with 5 complementary academic disciplines: Computer Science & ML, Data Science & Modeling, Business Strategy & Supply Chain, Financial Economics, and UX Product Design.
3. **Session Distribution**: 12 online sessions distributed across 4 weeks (8 learning sessions, 4 collaborative working sprints) with a required 8 hours/week output commitment.
4. **Internal Quality Gate Before Company Visibility**: Company reviewers never see raw or rejected student drafts. Only proposals evaluated and marked as `shortlisted` by DegreeLabs staff appear on the Company Reviewer portal. Exactly one proposal is selected by the company to advance to Validate.
5. **Local Upload Storage**: Uploaded proposal attachments are stored locally in `./uploads` with secure filenames, designed to transition seamlessly to S3/GCS in production.
6. **Downstream Lifecycle Scope**: Validate (Wks 5–8), Grow (~3 months paid), Talent Pool, and full Opportunity Pool are modeled as static roadmap placeholders (`/out-of-scope/<feature>`) per the brief specification.

---

## 7. How the Data Model Extends to Future Phases

The relational SQLite schema in `models.py` uses SQLAlchemy ORM constructs designed to migrate to PostgreSQL:

- **Validate Phase (Weeks 5–8)**: `Project` and `Team` entities link to a `ValidationSprint` table tracking synthetic dataset backtest runs, prototype code repos, and technical feasibility reports.
- **Grow Phase (~3 Months Paid)**: `Team` and `Company` link to an `EnterpriseContract` and `MilestonePayment` table.
- **Capability Passport & Talent Pool**: The `CapabilityPassport` table already stores granular competency scores, verified badges, and evidence logs. In the Talent Pool phase, this connects to an `EnterpriseRecruiterAccess` table allowing verified recruiters to filter candidates by proven problem-solving metrics.
- **Opportunity Pool**: The `Company` and `Project` tables expand to support company RFP intake forms and automated student skill-matching algorithms.

---

## 8. Live 5-Minute Walkthrough Demo Script

Follow this script to demonstrate the complete prototype end-to-end:

1. **Login as Student**: Go to `http://localhost:5000/login` and click **"Aarav Sharma (Student Lead)"**.
2. **Student Dashboard**: Inspect current progress (Week 2 of 4), assigned project summary (Aurex Retail Analytics), and upcoming sessions.
3. **Assigned Project**: Click **"Assigned Project"** in the sidebar to review the full problem statement and SLA constraints.
4. **Timeline & Week Detail**: Click **"4-Week Timeline"** &rarr; drill into **"Week 1"** to view completed sessions and click **"Watch Recording"** to trigger the session archive modal.
5. **Team Workspace**: Click **"Team Workspace"** to view the 5 team members across disciplines, write a quick note in the **Collaborative Scratchpad**, and click **"Save Scratchpad"**.
6. **Output & AI Coach**: Navigate to **"Output & AI Coach"** (Week 2). Click **"Get AI Feedback (Proposal Coach)"** to trigger the agentic tool loop. Watch the readiness score, strengths, gaps, and actionable to-dos populate. Check off a to-do item and click **"Final Submit"**.
7. **Mentor Engagement**: Click **"Mentor Sessions"** &rarr; request an open availability slot with a meeting topic.
8. **Evaluator Quality Gate**: Use the top role switcher to switch to **"Evaluator (Sarah)"**. Open the **Evaluation Dashboard**, see the side-by-side human vs. AI score, open the review modal, score the submission, and click **"Shortlist"**.
9. **Company Winner Selection**: Switch role to **"Company (Vikram)"**. Confirm only the shortlisted proposal is visible, and click **"Select This Proposal as Winner"** (advancing it to Validate Wks 5–8).
10. **Capability Passport**: Switch back to **"Student (Aarav)"** &rarr; open **"Capability Passport"** to inspect the verified credential and evidence audit log.
