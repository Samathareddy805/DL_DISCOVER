import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import json
from functools import wraps
from datetime import datetime
from flask import (
    Flask, render_template, redirect, url_for, request,
    flash, jsonify, send_from_directory, abort
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

from models import (
    db, User, Company, Project, Team, TeamMember,
    DiscoverWeek, Session, MentorSlot, MentorSessionRequest,
    TeamScratchpad, Submission, AIFeedback, AIToDoItem,
    HumanEvaluation, CapabilityPassport
)
from ai_coach import run_proposal_coach_agent

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'degreelabs-discover-secret-key-2026')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///discover.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Uploads directory
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB max

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message = "Please authenticate to access DegreeLabs Discover."
login_manager.login_message_category = "info"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Server-Side Role-Based Access Control Decorator
def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.role not in allowed_roles:
                flash(f"Access restricted. This screen requires one of the following roles: {', '.join(allowed_roles)}.", "danger")
                # Redirect to appropriate home page for user's role
                if current_user.is_student:
                    return redirect(url_for('student_dashboard'))
                elif current_user.is_mentor:
                    return redirect(url_for('mentor_sessions'))
                elif current_user.is_evaluator:
                    return redirect(url_for('evaluator_dashboard'))
                elif current_user.is_company_reviewer:
                    return redirect(url_for('company_dashboard'))
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Context Processor for Global Template Data
@app.context_processor
def inject_global_data():
    all_roles = [
        {"role": "student", "label": "Student Lead (Aarav)", "username": "aarav.student"},
        {"role": "mentor", "label": "Mentor (Dr. Maya)", "username": "maya.mentor"},
        {"role": "evaluator", "label": "Evaluator (Sarah)", "username": "sarah.evaluator"},
        {"role": "company_reviewer", "label": "Company (Vikram)", "username": "vikram.company"}
    ]
    return {
        "all_roles": all_roles,
        "now": datetime.utcnow()
    }


# ==========================================
# AUTHENTICATION & ROLE SWITCHER (SCREEN 1)
# ==========================================

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_student:
            return redirect(url_for('student_dashboard'))
        elif current_user.is_mentor:
            return redirect(url_for('mentor_sessions'))
        elif current_user.is_evaluator:
            return redirect(url_for('evaluator_dashboard'))
        elif current_user.is_company_reviewer:
            return redirect(url_for('company_dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            flash(f"Welcome back, {user.full_name}! Logged in as {user.role.replace('_', ' ').title()}.", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid credentials. Use one-click quick login or enter seeded password.", "danger")

    return render_template('login.html')


@app.route('/quick-login/<role>')
def quick_login(role):
    role_map = {
        'student': 'aarav.student',
        'mentor': 'maya.mentor',
        'evaluator': 'sarah.evaluator',
        'company_reviewer': 'vikram.company'
    }
    username = role_map.get(role)
    if not username:
        flash("Invalid role specified.", "danger")
        return redirect(url_for('login'))

    user = User.query.filter_by(username=username).first()
    if user:
        login_user(user)
        flash(f"Switched identity to {user.full_name} ({user.role.replace('_', ' ').title()}).", "success")
        return redirect(url_for('index'))
    
    flash("Seeded user not found. Please run 'python seed.py' first.", "warning")
    return redirect(url_for('login'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))


# ==========================================
# SCREEN 2: STUDENT DASHBOARD
# ==========================================

@app.route('/dashboard')
@app.route('/student/dashboard')
@login_required
@role_required(['student', 'evaluator'])
def student_dashboard():
    team = current_user.get_team() if current_user.is_student else Team.query.first()
    if not team:
        team = Team.query.first()

    weeks = DiscoverWeek.query.order_by(DiscoverWeek.week_number).all()
    upcoming_sessions = Session.query.filter_by(status='upcoming').order_by(Session.session_number).limit(3).all()
    completed_sessions = Session.query.filter_by(status='completed').count()
    
    # Submissions
    submissions = {s.week_number: s for s in team.submissions} if team else {}
    current_week_obj = DiscoverWeek.query.filter_by(week_number=team.current_week if team else 1).first()

    # Next action needed calculation
    current_sub = submissions.get(team.current_week if team else 1)
    if not current_sub or current_sub.status == Submission.STATUS_WORKING:
        next_action = {
            "title": f"Draft Week {team.current_week if team else 1} Output",
            "desc": f"Submit your team's '{current_week_obj.required_output_title if current_week_obj else 'output'}' and run Proposal Coach feedback.",
            "link": url_for('submission_view', week_num=team.current_week if team else 1),
            "btn_text": "Open Output Editor"
        }
    elif current_sub.status == Submission.STATUS_SUBMITTED:
        next_action = {
            "title": f"Week {team.current_week if team else 1} Submitted - Pending Evaluation",
            "desc": "Your submission is queued for internal evaluation by DegreeLabs Academic & Industry Directors.",
            "link": url_for('submission_view', week_num=team.current_week if team else 1),
            "btn_text": "View Submitted Proposal"
        }
    elif current_sub.status == Submission.STATUS_SHORTLISTED:
        next_action = {
            "title": f"Week {team.current_week if team else 1} Shortlisted!",
            "desc": "Congratulations! Your proposal was approved by internal evaluators and advanced to company review.",
            "link": url_for('timeline'),
            "btn_text": "Proceed to Next Week"
        }
    else:
        next_action = {
            "title": "Review Mentor Guidance",
            "desc": "Check your team workspace for the latest notes from your assigned mentor.",
            "link": url_for('team_workspace'),
            "btn_text": "View Workspace"
        }

    return render_template(
        'student_dashboard.html',
        team=team,
        weeks=weeks,
        submissions=submissions,
        current_week_obj=current_week_obj,
        upcoming_sessions=upcoming_sessions,
        completed_sessions=completed_sessions,
        next_action=next_action
    )


# ==========================================
# SCREEN 3: ASSIGNED PROJECT & PROBLEM
# ==========================================

@app.route('/project')
@login_required
def project_detail():
    team = current_user.get_team() if current_user.is_student else Team.query.first()
    project = team.project if team else Project.query.first()
    if not project:
        project = Project.query.first()
    return render_template('project_detail.html', project=project, team=team)


# ==========================================
# SCREEN 4: DISCOVER TIMELINE (WEEKS 1-4)
# ==========================================

@app.route('/timeline')
@login_required
def timeline():
    team = current_user.get_team() if current_user.is_student else Team.query.first()
    weeks = DiscoverWeek.query.order_by(DiscoverWeek.week_number).all()
    submissions = {s.week_number: s for s in team.submissions} if team else {}
    return render_template('timeline.html', weeks=weeks, team=team, submissions=submissions)


# ==========================================
# SCREEN 5: WEEK DETAIL & 12-SESSION SCHEDULE
# ==========================================

@app.route('/week/<int:week_num>')
@login_required
def week_detail(week_num):
    week = DiscoverWeek.query.filter_by(week_number=week_num).first_or_404()
    sessions = Session.query.filter_by(week_number=week_num).order_by(Session.session_number).all()
    team = current_user.get_team() if current_user.is_student else Team.query.first()
    submission = Submission.query.filter_by(team_id=team.id if team else 1, week_number=week_num).first()
    return render_template('week_detail.html', week=week, sessions=sessions, team=team, submission=submission)


# ==========================================
# SCREEN 6: TEAM WORKSPACE & COLLABORATION
# ==========================================

@app.route('/team')
@login_required
def team_workspace():
    team = current_user.get_team() if current_user.is_student else Team.query.first()
    if not team:
        team = Team.query.first()

    scratchpad = TeamScratchpad.query.filter_by(team_id=team.id, week_number=team.current_week).first()
    if not scratchpad:
        scratchpad = TeamScratchpad(
            team_id=team.id,
            week_number=team.current_week,
            content="Start collaborative notes and draft hypotheses with your team here...",
            updated_by_name=current_user.full_name
        )
        db.session.add(scratchpad)
        db.session.commit()

    submissions = Submission.query.filter_by(team_id=team.id).order_by(Submission.week_number).all()
    session_requests = MentorSessionRequest.query.filter_by(team_id=team.id).order_by(MentorSessionRequest.created_at.desc()).all()

    return render_template(
        'team_workspace.html',
        team=team,
        scratchpad=scratchpad,
        submissions=submissions,
        session_requests=session_requests
    )


@app.route('/team/scratchpad/save', methods=['POST'])
@login_required
@role_required(['student', 'evaluator'])
def save_scratchpad():
    team = current_user.get_team() if current_user.is_student else Team.query.first()
    content = request.form.get('content', '')
    week_number = int(request.form.get('week_number', team.current_week if team else 1))

    scratchpad = TeamScratchpad.query.filter_by(team_id=team.id, week_number=week_number).first()
    if not scratchpad:
        scratchpad = TeamScratchpad(team_id=team.id, week_number=week_number)
        db.session.add(scratchpad)

    scratchpad.content = content
    scratchpad.updated_by_name = current_user.full_name
    scratchpad.updated_at = datetime.utcnow()
    db.session.commit()

    flash("Team scratchpad saved successfully!", "success")
    return redirect(url_for('team_workspace'))


# ==========================================
# SCREEN 7: MENTOR AVAILABILITY & BOOKING
# ==========================================

@app.route('/mentor/sessions')
@app.route('/student/sessions')
@login_required
def mentor_sessions():
    mentor = User.query.filter_by(role='mentor').first()
    team = current_user.get_team() if current_user.is_student else Team.query.first()

    slots = MentorSlot.query.order_by(MentorSlot.id).all()
    
    if current_user.is_mentor:
        requests = MentorSessionRequest.query.order_by(MentorSessionRequest.created_at.desc()).all()
    else:
        requests = MentorSessionRequest.query.filter_by(team_id=team.id if team else 1).order_by(MentorSessionRequest.created_at.desc()).all()

    return render_template(
        'mentor_sessions.html',
        mentor=mentor,
        team=team,
        slots=slots,
        requests=requests
    )


@app.route('/mentor/slots/create', methods=['POST'])
@login_required
@role_required(['mentor', 'evaluator'])
def create_mentor_slot():
    start_time = request.form.get('start_time', '').strip()
    end_time = request.form.get('end_time', '').strip()

    if not start_time or not end_time:
        flash("Please provide both start and end times for the slot.", "danger")
        return redirect(url_for('mentor_sessions'))

    slot = MentorSlot(
        mentor_id=current_user.id if current_user.is_mentor else User.query.filter_by(role='mentor').first().id,
        start_time=start_time,
        end_time=end_time,
        is_booked=False
    )
    db.session.add(slot)
    db.session.commit()
    flash("New mentor availability slot published!", "success")
    return redirect(url_for('mentor_sessions'))


@app.route('/mentor/request/book', methods=['POST'])
@login_required
@role_required(['student', 'evaluator'])
def book_mentor_slot():
    team = current_user.get_team() if current_user.is_student else Team.query.first()
    slot_id = int(request.form.get('slot_id', 0))
    topic = request.form.get('topic', '').strip()
    agenda = request.form.get('agenda_notes', '').strip()

    slot = MentorSlot.query.get_or_404(slot_id)
    if slot.is_booked:
        flash("This slot has already been booked.", "warning")
        return redirect(url_for('mentor_sessions'))

    req = MentorSessionRequest(
        team_id=team.id,
        mentor_slot_id=slot.id,
        topic=topic,
        agenda_notes=agenda,
        status='pending'
    )
    slot.is_booked = True
    db.session.add(req)
    db.session.commit()

    flash("Mentor session requested successfully! Your mentor will review and confirm on-platform.", "success")
    return redirect(url_for('mentor_sessions'))


@app.route('/mentor/request/<int:req_id>/respond', methods=['POST'])
@login_required
@role_required(['mentor', 'evaluator'])
def respond_mentor_request(req_id):
    req_obj = MentorSessionRequest.query.get_or_404(req_id)
    action = request.form.get('action')  # 'accept' or 'decline'
    notes = request.form.get('mentor_notes', '').strip()

    if action == 'accept':
        req_obj.status = 'accepted'
        req_obj.mentor_notes = notes or "Session confirmed. See you in the meeting space."
    elif action == 'decline':
        req_obj.status = 'declined'
        req_obj.mentor_notes = notes or "Slot declined. Please choose an alternate open slot."
        if req_obj.slot:
            req_obj.slot.is_booked = False

    req_obj.responded_at = datetime.utcnow()
    db.session.commit()

    flash(f"Session request {req_obj.status.upper()} with your guidance note.", "success")
    return redirect(url_for('mentor_sessions'))


# ==========================================
# SCREEN 8: OUTPUT SUBMISSION & AI COACH
# ==========================================

@app.route('/submissions/<int:week_num>', methods=['GET', 'POST'])
@login_required
def submission_view(week_num):
    week = DiscoverWeek.query.filter_by(week_number=week_num).first_or_404()
    team = current_user.get_team() if current_user.is_student else Team.query.first()
    if not team:
        team = Team.query.first()

    submission = Submission.query.filter_by(team_id=team.id, week_number=week_num).first()
    if not submission:
        submission = Submission(
            team_id=team.id,
            week_number=week_num,
            title=f"{team.name} - Week {week_num} Deliverable: {week.required_output_title}",
            status=Submission.STATUS_WORKING
        )
        db.session.add(submission)
        db.session.commit()

    if request.method == 'POST':
        # Enforce that only students/evaluators can edit submissions, mentors/company reviewers are read-only
        if not (current_user.is_student or current_user.is_evaluator):
            flash("Read-only access. Mentors and Company Reviewers cannot edit student deliverables.", "warning")
            return redirect(url_for('submission_view', week_num=week_num))

        action = request.form.get('action')  # 'save_draft' or 'final_submit'
        submission.title = request.form.get('title', submission.title)
        submission.executive_summary = request.form.get('executive_summary', '')
        submission.content = request.form.get('content', '')

        # File upload handling
        if 'attachment_file' in request.files:
            file = request.files['attachment_file']
            if file and file.filename != '':
                filename = secure_filename(f"Week{week_num}_{team.name.replace(' ', '_')}_{file.filename}")
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                submission.file_attachment_path = f"/uploads/{filename}"
                submission.file_attachment_name = file.filename

        if action == 'final_submit':
            submission.status = Submission.STATUS_SUBMITTED
            submission.submitted_at = datetime.utcnow()
            flash("Weekly output successfully submitted for internal DegreeLabs evaluation!", "success")
        else:
            if submission.status == Submission.STATUS_ASSIGNED:
                submission.status = Submission.STATUS_WORKING
            flash("Draft output saved.", "info")

        db.session.commit()
        return redirect(url_for('submission_view', week_num=week_num))

    ai_feedback = submission.ai_feedback
    todos = submission.to_do_items

    return render_template(
        'submission_form.html',
        week=week,
        team=team,
        submission=submission,
        ai_feedback=ai_feedback,
        todos=todos
    )


@app.route('/api/ai-coach/run/<int:submission_id>', methods=['POST'])
@login_required
def run_ai_coach_api(submission_id):
    """Triggers the Discover Proposal Coach agentic tool loop and returns JSON result."""
    sub = Submission.query.get_or_404(submission_id)
    
    # Save any unsaved draft content sent in JSON payload first
    data = request.get_json(silent=True) or {}
    if 'title' in data and data['title']:
        sub.title = data['title']
    if 'executive_summary' in data:
        sub.executive_summary = data['executive_summary']
    if 'content' in data:
        sub.content = data['content']
    db.session.commit()

    # Execute the agent
    result = run_proposal_coach_agent(submission_id)
    return jsonify(result)


@app.route('/api/todo/<int:todo_id>/toggle', methods=['POST'])
@login_required
def toggle_todo(todo_id):
    todo = AIToDoItem.query.get_or_404(todo_id)
    todo.is_resolved = not todo.is_resolved
    db.session.commit()
    return jsonify({"status": "success", "is_resolved": todo.is_resolved})


# ==========================================
# SCREEN 9: EVALUATION & SHORTLISTING DASHBOARD
# ==========================================

@app.route('/evaluator/dashboard')
@login_required
@role_required(['evaluator', 'admin'])
def evaluator_dashboard():
    submissions = Submission.query.order_by(Submission.week_number, Submission.created_at.desc()).all()
    weeks = DiscoverWeek.query.order_by(DiscoverWeek.week_number).all()
    teams = Team.query.all()

    total_submissions = len(submissions)
    submitted_count = sum(1 for s in submissions if s.status == Submission.STATUS_SUBMITTED)
    evaluated_count = sum(1 for s in submissions if s.status == Submission.STATUS_EVALUATED)
    shortlisted_count = sum(1 for s in submissions if s.status == Submission.STATUS_SHORTLISTED)

    return render_template(
        'evaluator_dashboard.html',
        submissions=submissions,
        weeks=weeks,
        teams=teams,
        total_submissions=total_submissions,
        submitted_count=submitted_count,
        evaluated_count=evaluated_count,
        shortlisted_count=shortlisted_count
    )


@app.route('/evaluator/evaluate/<int:submission_id>', methods=['POST'])
@login_required
@role_required(['evaluator', 'admin'])
def evaluate_submission(submission_id):
    sub = Submission.query.get_or_404(submission_id)
    
    score = int(request.form.get('score', 85))
    decision = request.form.get('decision', 'shortlisted')  # 'shortlisted', 'rejected', 'evaluated'
    strengths = request.form.get('strengths', '')
    weaknesses = request.form.get('weaknesses', '')
    recommendation_notes = request.form.get('recommendation_notes', '')

    criteria = {
        "problem_clarity": int(request.form.get('criteria_problem_clarity', 90)),
        "methodology_rigor": int(request.form.get('criteria_methodology_rigor', 85)),
        "feasibility": int(request.form.get('criteria_feasibility', 85)),
        "presentation_quality": int(request.form.get('criteria_presentation', 90))
    }

    eval_record = HumanEvaluation.query.filter_by(submission_id=sub.id).first()
    if not eval_record:
        eval_record = HumanEvaluation(
            submission_id=sub.id,
            evaluator_id=current_user.id
        )
        db.session.add(eval_record)

    eval_record.score = score
    eval_record.decision = decision
    eval_record.criteria_scores_json = json.dumps(criteria)
    eval_record.strengths = strengths
    eval_record.weaknesses = weaknesses
    eval_record.recommendation_notes = recommendation_notes
    eval_record.evaluated_at = datetime.utcnow()

    # Update Submission status based on decision
    if decision == 'shortlisted':
        sub.status = Submission.STATUS_SHORTLISTED
    elif decision == 'rejected':
        sub.status = Submission.STATUS_REJECTED
    else:
        sub.status = Submission.STATUS_EVALUATED

    db.session.commit()
    flash(f"Submission evaluation saved! Status updated to {sub.status.upper()}.", "success")
    return redirect(url_for('evaluator_dashboard'))


@app.route('/evaluator/shortlist/<int:submission_id>', methods=['POST'])
@login_required
@role_required(['evaluator', 'admin'])
def quick_shortlist_toggle(submission_id):
    sub = Submission.query.get_or_404(submission_id)
    action = request.form.get('action')  # 'shortlist' or 'reject'

    if action == 'shortlist':
        sub.status = Submission.STATUS_SHORTLISTED
        flash(f"Submission #{sub.id} (Week {sub.week_number}) SHORTLISTED for company review.", "success")
    elif action == 'reject':
        sub.status = Submission.STATUS_REJECTED
        flash(f"Submission #{sub.id} marked as REJECTED.", "warning")

    db.session.commit()
    return redirect(url_for('evaluator_dashboard'))


# ==========================================
# COMPANY REVIEWER DASHBOARD
# ==========================================

@app.route('/company/dashboard')
@app.route('/company/proposals')
@login_required
@role_required(['company_reviewer', 'evaluator'])
def company_dashboard():
    # Only show shortlisted submissions for the reviewer's assigned company project
    company = current_user.company if current_user.company else Company.query.first()
    project = company.projects[0] if company and company.projects else Project.query.first()

    shortlisted_submissions = []
    if project:
        for team in project.teams:
            for sub in team.submissions:
                if sub.status == Submission.STATUS_SHORTLISTED:
                    shortlisted_submissions.append(sub)

    return render_template(
        'company_dashboard.html',
        company=company,
        project=project,
        shortlisted_submissions=shortlisted_submissions
    )


@app.route('/company/select/<int:submission_id>', methods=['POST'])
@login_required
@role_required(['company_reviewer', 'evaluator'])
def company_select_proposal(submission_id):
    sub = Submission.query.get_or_404(submission_id)
    if sub.status != Submission.STATUS_SHORTLISTED:
        flash("Only shortlisted proposals can be selected.", "danger")
        return redirect(url_for('company_dashboard'))

    # Unmark any other selected proposals for this project (exactly one proposal proceeds)
    project = sub.team.project
    for team in project.teams:
        for s in team.submissions:
            s.is_final_selected = False
            if s.status == Submission.STATUS_NEXT_PHASE:
                s.status = Submission.STATUS_SHORTLISTED

    sub.is_final_selected = True
    sub.status = Submission.STATUS_NEXT_PHASE
    sub.company_feedback = request.form.get('company_feedback', 'Selected by Aurex Retail Strategy Team for Phase 2 Validation.')
    db.session.commit()

    flash(f"Proposal for '{sub.title}' officially SELECTED! Advanced to Next Phase (Validate Wks 5–8).", "success")
    return redirect(url_for('company_dashboard'))


# ==========================================
# SCREEN 10: CAPABILITY PASSPORT PREVIEW
# ==========================================

@app.route('/passport')
@login_required
def capability_passport():
    user = current_user
    team = user.get_team() if user.is_student else Team.query.first()
    passport = CapabilityPassport.query.filter_by(team_id=team.id if team else 1).first()

    if not passport:
        passport = CapabilityPassport(
            user_id=user.id,
            team_id=team.id if team else 1,
            passport_code=f"DL-PASSPORT-2026-TEAM-{team.id if team else 1}",
            certificates_json=json.dumps([{
                "title": "Discover Cohort Participant",
                "badge_code": "DISCOVER-CANDIDATE",
                "issued_by": "DegreeLabs Academic Board",
                "date": datetime.utcnow().strftime("%b %d, %Y"),
                "status": "In Progress",
                "score": 85,
                "skills": ["Problem Definition", "Industry Research", "Team Collaboration"]
            }]),
            competency_scores_json=json.dumps({
                "Problem Decomposition & Scoping": 90,
                "Analytical Research & Benchmarking": 85,
                "Algorithmic & Technical Design": 88,
                "Business Strategy & Unit Economics": 86,
                "Executive Communication & Proposal Writing": 82
            }),
            evidence_log_json=json.dumps([])
        )
        db.session.add(passport)
        db.session.commit()

    return render_template('capability_passport.html', passport=passport, team=team, user=user)


# ==========================================
# OUT OF SCOPE ROADMAP / PLACEHOLDERS
# ==========================================

@app.route('/out-of-scope/<feature>')
@login_required
def out_of_scope(feature):
    feature_meta = {
        'validate': {
            'title': 'Validate Phase (Weeks 5–8)',
            'desc': 'Deep technical prototyping, synthetic backtesting with enterprise datasets, and feasibility stress testing.',
            'status': 'Phase 2 - Unlocks after Discover Proposal Selection'
        },
        'grow': {
            'title': 'Grow Phase (~3 Months, Paid Engagement)',
            'desc': 'Direct paid enterprise deployment engagement, production code integration, and store rollouts with client engineering teams.',
            'status': 'Phase 3 - Unlocks after Validate sign-off'
        },
        'talent-pool': {
            'title': 'DegreeLabs Talent Pool',
            'desc': 'Verified student capability profiles accessible to enterprise hiring partners with cryptographic evidence links.',
            'status': 'Post-Program Capability Certification'
        },
        'opportunity-pool': {
            'title': 'Enterprise Opportunity Pool',
            'desc': 'Marketplace of curated enterprise AI & data challenges submitted by partner corporations.',
            'status': 'Enterprise Partner Portal'
        }
    }
    meta = feature_meta.get(feature, {
        'title': feature.replace('-', ' ').title(),
        'desc': 'This capability is outside the 4-week Discover MVP scope and scheduled for future phases.',
        'status': 'Coming in Next Phase'
    })
    return render_template('out_of_scope.html', meta=meta, feature=feature)


# File attachment serving
@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        try:
            from generate_sample_pdf import generate_named_pdf
            generate_named_pdf(filename, file_path)
        except Exception as e:
            app.logger.warning(f"Could not auto-generate PDF {filename}: {e}")
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



# Favicon Route
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
