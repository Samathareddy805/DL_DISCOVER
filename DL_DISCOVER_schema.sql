-- DL_DISCOVER database schema
-- Matches the uploaded models.py exactly.
-- Target: PostgreSQL

BEGIN;

CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    industry VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    logo_url VARCHAR(255),
    website VARCHAR(150),
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL,
    full_name VARCHAR(120) NOT NULL,
    avatar_url VARCHAR(255),
    discipline VARCHAR(100),
    created_at TIMESTAMP,
    company_id INTEGER REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL REFERENCES companies(id),
    title VARCHAR(255) NOT NULL,
    problem_statement TEXT NOT NULL,
    scope_summary TEXT NOT NULL,
    target_audience VARCHAR(255),
    business_constraints TEXT,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    project_id INTEGER NOT NULL REFERENCES projects(id),
    mentor_id INTEGER REFERENCES users(id),
    current_week INTEGER DEFAULT 1,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS team_members (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    role_in_team VARCHAR(100) NOT NULL,
    joined_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS discover_weeks (
    id SERIAL PRIMARY KEY,
    week_number INTEGER NOT NULL UNIQUE,
    title VARCHAR(150) NOT NULL,
    focus_area VARCHAR(255) NOT NULL,
    objective TEXT NOT NULL,
    required_output_title VARCHAR(200) NOT NULL,
    rubric_checklist_json TEXT NOT NULL,
    deadline_days INTEGER DEFAULT 7
);

CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    week_number INTEGER NOT NULL,
    session_number INTEGER NOT NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    session_type VARCHAR(30) NOT NULL,
    description TEXT NOT NULL,
    scheduled_at VARCHAR(100) NOT NULL,
    duration_minutes INTEGER DEFAULT 90,
    status VARCHAR(30) DEFAULT 'upcoming',
    recording_url VARCHAR(255),
    mock_meeting_link VARCHAR(255) DEFAULT 'https://degreelabs.ai/session/live-room'
);

CREATE TABLE IF NOT EXISTS mentor_slots (
    id SERIAL PRIMARY KEY,
    mentor_id INTEGER NOT NULL REFERENCES users(id),
    start_time VARCHAR(100) NOT NULL,
    end_time VARCHAR(100) NOT NULL,
    is_booked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mentor_session_requests (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    mentor_slot_id INTEGER NOT NULL REFERENCES mentor_slots(id),
    topic VARCHAR(200) NOT NULL,
    agenda_notes TEXT,
    status VARCHAR(30) DEFAULT 'pending',
    mentor_notes TEXT,
    meeting_link VARCHAR(255) DEFAULT 'https://degreelabs.ai/mentor/space-room',
    created_at TIMESTAMP,
    responded_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS team_scratchpads (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    week_number INTEGER NOT NULL,
    content TEXT DEFAULT '',
    updated_by_name VARCHAR(100),
    updated_at TIMESTAMP,
    CONSTRAINT uq_team_scratchpad_week UNIQUE (team_id, week_number)
);

CREATE TABLE IF NOT EXISTS submissions (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(id),
    week_number INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    executive_summary TEXT,
    content TEXT,
    file_attachment_path VARCHAR(255),
    file_attachment_name VARCHAR(255),
    status VARCHAR(30) NOT NULL DEFAULT 'working',
    is_final_selected BOOLEAN DEFAULT FALSE,
    company_feedback TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    submitted_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_feedbacks (
    id SERIAL PRIMARY KEY,
    submission_id INTEGER NOT NULL UNIQUE REFERENCES submissions(id),
    readiness_score INTEGER NOT NULL,
    strengths_json TEXT NOT NULL,
    gaps_json TEXT NOT NULL,
    suggested_next_steps_json TEXT NOT NULL,
    raw_summary TEXT NOT NULL,
    created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_to_do_items (
    id SERIAL PRIMARY KEY,
    submission_id INTEGER NOT NULL REFERENCES submissions(id),
    section_name VARCHAR(150) NOT NULL,
    prompt_for_student TEXT NOT NULL,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP,
    CONSTRAINT uq_ai_todo_section UNIQUE (submission_id, section_name)
);

CREATE TABLE IF NOT EXISTS human_evaluations (
    id SERIAL PRIMARY KEY,
    submission_id INTEGER NOT NULL UNIQUE REFERENCES submissions(id),
    evaluator_id INTEGER NOT NULL REFERENCES users(id),
    score INTEGER NOT NULL,
    criteria_scores_json TEXT,
    strengths TEXT,
    weaknesses TEXT,
    recommendation_notes TEXT,
    decision VARCHAR(30) DEFAULT 'evaluated',
    evaluated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS capability_passports (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    team_id INTEGER NOT NULL REFERENCES teams(id),
    passport_code VARCHAR(50) NOT NULL UNIQUE,
    certificates_json TEXT NOT NULL,
    competency_scores_json TEXT NOT NULL,
    evidence_log_json TEXT NOT NULL,
    issued_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_company_id ON users(company_id);
CREATE INDEX IF NOT EXISTS idx_projects_company_id ON projects(company_id);
CREATE INDEX IF NOT EXISTS idx_teams_project_id ON teams(project_id);
CREATE INDEX IF NOT EXISTS idx_teams_mentor_id ON teams(mentor_id);
CREATE INDEX IF NOT EXISTS idx_team_members_team_id ON team_members(team_id);
CREATE INDEX IF NOT EXISTS idx_team_members_user_id ON team_members(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_week_number ON sessions(week_number);
CREATE INDEX IF NOT EXISTS idx_mentor_slots_mentor_id ON mentor_slots(mentor_id);
CREATE INDEX IF NOT EXISTS idx_mentor_requests_team_id ON mentor_session_requests(team_id);
CREATE INDEX IF NOT EXISTS idx_submissions_team_id ON submissions(team_id);
CREATE INDEX IF NOT EXISTS idx_submissions_week_number ON submissions(week_number);
CREATE INDEX IF NOT EXISTS idx_ai_feedback_submission_id ON ai_feedbacks(submission_id);
CREATE INDEX IF NOT EXISTS idx_ai_todo_submission_id ON ai_to_do_items(submission_id);
CREATE INDEX IF NOT EXISTS idx_human_evaluation_evaluator_id ON human_evaluations(evaluator_id);
CREATE INDEX IF NOT EXISTS idx_capability_passport_team_id ON capability_passports(team_id);

COMMIT;
