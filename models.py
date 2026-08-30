import json
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False)  # 'student', 'mentor', 'evaluator', 'company_reviewer'
    full_name = db.Column(db.String(120), nullable=False)
    avatar_url = db.Column(db.String(255), nullable=True)
    discipline = db.Column(db.String(100), nullable=True)  # e.g., 'Computer Science', 'Data Engineering', 'Business Strategy'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    team_memberships = db.relationship('TeamMember', back_populates='user', lazy=True)
    mentored_teams = db.relationship('Team', back_populates='mentor', foreign_keys='Team.mentor_id', lazy=True)
    mentor_slots = db.relationship('MentorSlot', back_populates='mentor', lazy=True)
    evaluations = db.relationship('HumanEvaluation', back_populates='evaluator', lazy=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    company = db.relationship('Company', back_populates='reviewers')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_student(self):
        return self.role == 'student'

    @property
    def is_mentor(self):
        return self.role == 'mentor'

    @property
    def is_evaluator(self):
        return self.role in ['evaluator', 'admin']

    @property
    def is_company_reviewer(self):
        return self.role == 'company_reviewer'

    def get_team(self):
        if self.team_memberships:
            return self.team_memberships[0].team
        return None


class Company(db.Model):
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    industry = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    logo_url = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(150), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    projects = db.relationship('Project', back_populates='company', lazy=True)
    reviewers = db.relationship('User', back_populates='company', lazy=True)


class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    problem_statement = db.Column(db.Text, nullable=False)
    scope_summary = db.Column(db.Text, nullable=False)
    target_audience = db.Column(db.String(255), nullable=True)
    business_constraints = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    company = db.relationship('Company', back_populates='projects')
    teams = db.relationship('Team', back_populates='project', lazy=True)


class Team(db.Model):
    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    current_week = db.Column(db.Integer, default=1)  # 1 to 4
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', back_populates='teams')
    mentor = db.relationship('User', foreign_keys=[mentor_id], back_populates='mentored_teams')
    members = db.relationship('TeamMember', back_populates='team', cascade='all, delete-orphan', lazy=True)
    submissions = db.relationship('Submission', back_populates='team', cascade='all, delete-orphan', lazy=True)
    scratchpads = db.relationship('TeamScratchpad', back_populates='team', cascade='all, delete-orphan', lazy=True)
    session_requests = db.relationship('MentorSessionRequest', back_populates='team', cascade='all, delete-orphan', lazy=True)


class TeamMember(db.Model):
    __tablename__ = 'team_members'

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role_in_team = db.Column(db.String(100), nullable=False)  # 'Team Lead & Strategist', 'Research Lead', etc.
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    team = db.relationship('Team', back_populates='members')
    user = db.relationship('User', back_populates='team_memberships')


class DiscoverWeek(db.Model):
    __tablename__ = 'discover_weeks'

    id = db.Column(db.Integer, primary_key=True)
    week_number = db.Column(db.Integer, unique=True, nullable=False)  # 1, 2, 3, 4
    title = db.Column(db.String(150), nullable=False)
    focus_area = db.Column(db.String(255), nullable=False)
    objective = db.Column(db.Text, nullable=False)
    required_output_title = db.Column(db.String(200), nullable=False)
    rubric_checklist_json = db.Column(db.Text, nullable=False)  # JSON string of required criteria
    deadline_days = db.Column(db.Integer, default=7)

    @property
    def rubric_checklist(self):
        try:
            return json.loads(self.rubric_checklist_json) if self.rubric_checklist_json else []
        except Exception:
            return []


class Session(db.Model):
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    week_number = db.Column(db.Integer, nullable=False)
    session_number = db.Column(db.Integer, unique=True, nullable=False)  # 1 to 12
    title = db.Column(db.String(200), nullable=False)
    session_type = db.Column(db.String(30), nullable=False)  # 'learning' or 'working'
    description = db.Column(db.Text, nullable=False)
    scheduled_at = db.Column(db.String(100), nullable=False)  # e.g., 'Tuesday, 4:00 PM - 5:30 PM'
    duration_minutes = db.Column(db.Integer, default=90)
    status = db.Column(db.String(30), default='upcoming')  # 'upcoming', 'completed'
    recording_url = db.Column(db.String(255), nullable=True)
    mock_meeting_link = db.Column(db.String(255), default='https://degreelabs.ai/session/live-room')


class MentorSlot(db.Model):
    __tablename__ = 'mentor_slots'

    id = db.Column(db.Integer, primary_key=True)
    mentor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.String(100), nullable=False)  # 'Thu, Aug 28, 3:00 PM'
    end_time = db.Column(db.String(100), nullable=False)    # 'Thu, Aug 28, 4:00 PM'
    is_booked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    mentor = db.relationship('User', back_populates='mentor_slots')
    requests = db.relationship('MentorSessionRequest', back_populates='slot', lazy=True)


class MentorSessionRequest(db.Model):
    __tablename__ = 'mentor_session_requests'

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    mentor_slot_id = db.Column(db.Integer, db.ForeignKey('mentor_slots.id'), nullable=False)
    topic = db.Column(db.String(200), nullable=False)
    agenda_notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), default='pending')  # 'pending', 'accepted', 'declined', 'completed'
    mentor_notes = db.Column(db.Text, nullable=True)
    meeting_link = db.Column(db.String(255), default='https://degreelabs.ai/mentor/space-room')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    team = db.relationship('Team', back_populates='session_requests')
    slot = db.relationship('MentorSlot', back_populates='requests')


class TeamScratchpad(db.Model):
    __tablename__ = 'team_scratchpads'

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    week_number = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, default='')
    updated_by_name = db.Column(db.String(100), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = db.relationship('Team', back_populates='scratchpads')


class Submission(db.Model):
    __tablename__ = 'submissions'

    STATUS_ASSIGNED = 'assigned'
    STATUS_WORKING = 'working'
    STATUS_SUBMITTED = 'submitted'
    STATUS_EVALUATED = 'evaluated'
    STATUS_SHORTLISTED = 'shortlisted'
    STATUS_REJECTED = 'rejected'
    STATUS_NEXT_PHASE = 'next phase'

    VALID_STATUSES = [
        STATUS_ASSIGNED,
        STATUS_WORKING,
        STATUS_SUBMITTED,
        STATUS_EVALUATED,
        STATUS_SHORTLISTED,
        STATUS_REJECTED,
        STATUS_NEXT_PHASE
    ]

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    week_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    executive_summary = db.Column(db.Text, nullable=True)
    content = db.Column(db.Text, nullable=True)
    file_attachment_path = db.Column(db.String(255), nullable=True)
    file_attachment_name = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(30), default=STATUS_WORKING, nullable=False)
    is_final_selected = db.Column(db.Boolean, default=False)  # Selected by Company Reviewer
    company_feedback = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    team = db.relationship('Team', back_populates='submissions')
    ai_feedback = db.relationship('AIFeedback', back_populates='submission', uselist=False, cascade='all, delete-orphan')
    to_do_items = db.relationship('AIToDoItem', back_populates='submission', cascade='all, delete-orphan', lazy=True)
    human_evaluation = db.relationship('HumanEvaluation', back_populates='submission', uselist=False, cascade='all, delete-orphan')

    @property
    def status_badge_class(self):
        badges = {
            'assigned': 'badge-secondary',
            'working': 'badge-warning',
            'submitted': 'badge-info',
            'evaluated': 'badge-primary',
            'shortlisted': 'badge-success',
            'rejected': 'badge-danger',
            'next phase': 'badge-purple'
        }
        return badges.get(self.status, 'badge-secondary')


class AIFeedback(db.Model):
    __tablename__ = 'ai_feedbacks'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), unique=True, nullable=False)
    readiness_score = db.Column(db.Integer, nullable=False)  # 0 to 100
    strengths_json = db.Column(db.Text, nullable=False)      # JSON list of strings
    gaps_json = db.Column(db.Text, nullable=False)           # JSON list of strings
    suggested_next_steps_json = db.Column(db.Text, nullable=False)  # JSON list of strings
    raw_summary = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    submission = db.relationship('Submission', back_populates='ai_feedback')

    @property
    def strengths(self):
        try:
            return json.loads(self.strengths_json) if self.strengths_json else []
        except Exception:
            return []

    @property
    def gaps(self):
        try:
            return json.loads(self.gaps_json) if self.gaps_json else []
        except Exception:
            return []

    @property
    def suggested_next_steps(self):
        try:
            return json.loads(self.suggested_next_steps_json) if self.suggested_next_steps_json else []
        except Exception:
            return []


class AIToDoItem(db.Model):
    __tablename__ = 'ai_to_do_items'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), nullable=False)
    section_name = db.Column(db.String(150), nullable=False)
    prompt_for_student = db.Column(db.Text, nullable=False)
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    submission = db.relationship('Submission', back_populates='to_do_items')


class HumanEvaluation(db.Model):
    __tablename__ = 'human_evaluations'

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey('submissions.id'), unique=True, nullable=False)
    evaluator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)  # 0 to 100
    criteria_scores_json = db.Column(db.Text, nullable=True)  # JSON breakdown
    strengths = db.Column(db.Text, nullable=True)
    weaknesses = db.Column(db.Text, nullable=True)
    recommendation_notes = db.Column(db.Text, nullable=True)
    decision = db.Column(db.String(30), default='evaluated')  # 'shortlisted', 'rejected', 'revision_requested'
    evaluated_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    submission = db.relationship('Submission', back_populates='human_evaluation')
    evaluator = db.relationship('User', back_populates='evaluations')

    @property
    def criteria_scores(self):
        try:
            return json.loads(self.criteria_scores_json) if self.criteria_scores_json else {}
        except Exception:
            return {}


class CapabilityPassport(db.Model):
    __tablename__ = 'capability_passports'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    passport_code = db.Column(db.String(50), unique=True, nullable=False)
    certificates_json = db.Column(db.Text, nullable=False)  # JSON list of certificates
    competency_scores_json = db.Column(db.Text, nullable=False)  # JSON dict of competencies
    evidence_log_json = db.Column(db.Text, nullable=False)  # JSON list of logged evidence items
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id])
    team = db.relationship('Team', foreign_keys=[team_id])

    @property
    def certificates(self):
        try:
            return json.loads(self.certificates_json) if self.certificates_json else []
        except Exception:
            return []

    @property
    def competency_scores(self):
        try:
            return json.loads(self.competency_scores_json) if self.competency_scores_json else {}
        except Exception:
            return {}

    @property
    def evidence_log(self):
        try:
            return json.loads(self.evidence_log_json) if self.evidence_log_json else []
        except Exception:
            return []
