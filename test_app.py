import pytest
import json
from app import app, db
from models import User, Company, Project, Team, DiscoverWeek, Submission, MentorSlot, MentorSessionRequest, AIFeedback, AIToDoItem, HumanEvaluation
from ai_coach import (
    execute_get_week_rubric,
    execute_get_submission_draft,
    execute_save_ai_feedback,
    execute_flag_missing_section,
    run_proposal_coach_agent,
    extract_attachment_text
)
from seed import seed_database

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        seed_database()
        with app.test_client() as client:
            yield client

def test_database_seeding(client):
    with app.app_context():
        # Check users
        users = User.query.all()
        assert len(users) >= 8  # 5 students, 1 mentor, 1 evaluator, 1 company reviewer
        
        # Check company & project
        company = Company.query.first()
        assert company is not None
        assert "Aurex" in company.name
        
        project = Project.query.first()
        assert project is not None
        assert "Predictive" in project.title

        # Check Discover weeks
        weeks = DiscoverWeek.query.all()
        assert len(weeks) == 4

        # Check seeded team
        team = Team.query.first()
        assert team is not None
        assert len(team.members) == 5

def test_role_based_access_control(client):
    # Unauthenticated user should be redirected to login
    res = client.get('/dashboard')
    assert res.status_code == 302
    assert '/login' in res.headers['Location']

    # Login as student (Aarav)
    res = client.get('/quick-login/student', follow_redirects=True)
    assert res.status_code == 200
    assert b"Aarav Sharma" in res.data
    assert b"Nexus Dynamics" in res.data

    # Student trying to access Evaluator Dashboard should be blocked/redirected
    res = client.get('/evaluator/dashboard', follow_redirects=True)
    assert res.status_code == 200
    assert b"Access restricted" in res.data

    # Switch to Evaluator (Sarah)
    res = client.get('/quick-login/evaluator', follow_redirects=True)
    assert res.status_code == 200
    assert b"Sarah Jenkins" in res.data

    # Evaluator can access evaluation dashboard
    res = client.get('/evaluator/dashboard')
    assert res.status_code == 200
    assert b"Evaluation &amp; Shortlisting Dashboard" in res.data or b"Evaluation & Shortlisting Dashboard" in res.data

def test_ai_coach_tool_execution(client):
    with app.app_context():
        # Test tool 1: get_week_rubric
        rubric_res = execute_get_week_rubric(1)
        assert "week_number" in rubric_res
        assert rubric_res["week_number"] == 1
        assert len(rubric_res["rubric_checklist"]) >= 3

        # Test tool 2: get_submission_draft
        sub = Submission.query.first()
        assert sub is not None
        draft_res = execute_get_submission_draft(sub.id)
        assert draft_res["submission_id"] == sub.id
        assert len(draft_res["content"]) > 0

        # Test tool 3: save_ai_feedback
        save_res = execute_save_ai_feedback(
            submission_id=sub.id,
            readiness_score=88,
            strengths=["Clear problem framing", "Strong metrics"],
            gaps=["Needs cold-start SKU details"],
            suggested_next_steps=["Test with mock data"]
        )
        assert save_res["status"] == "success"
        assert save_res["readiness_score"] == 88

        # Test tool 4: flag_missing_section
        flag_res = execute_flag_missing_section(
            submission_id=sub.id,
            section_name="Cold-Start Strategy",
            prompt_for_student="Provide details on how cold-start stores are initialized."
        )
        assert flag_res["status"] == "success"

        # Verify DB records
        fb = AIFeedback.query.filter_by(submission_id=sub.id).first()
        assert fb is not None
        assert fb.readiness_score == 88
        assert "Clear problem framing" in fb.strengths

        todos = AIToDoItem.query.filter_by(submission_id=sub.id).all()
        assert any(t.section_name == "Cold-Start Strategy" for t in todos)

def test_ai_coach_agent_run(client):
    with app.app_context():
        sub = Submission.query.filter_by(week_number=2).first()
        assert sub is not None
        
        # Run Proposal Coach Agent
        agent_res = run_proposal_coach_agent(sub.id)
        assert agent_res["success"] is True
        assert "feedback" in agent_res
        assert agent_res["feedback"]["readiness_score"] > 0
        assert len(agent_res["feedback"]["strengths"]) > 0

def test_submission_lifecycle_and_shortlisting(client):
    with app.app_context():
        sub = Submission.query.filter_by(week_number=2).first()
        sub.status = Submission.STATUS_SUBMITTED
        db.session.commit()
        sub_id = sub.id

    # Login as Evaluator
    client.get('/quick-login/evaluator', follow_redirects=True)

    # Evaluator scores and shortlists submission
    res = client.post(f'/evaluator/evaluate/{sub_id}', data={
        'score': 94,
        'decision': 'shortlisted',
        'criteria_problem_clarity': 95,
        'criteria_methodology_rigor': 92,
        'criteria_feasibility': 94,
        'criteria_presentation': 95,
        'strengths': 'Exceptional benchmarking matrix and GNN architecture.',
        'weaknesses': 'Minor clarification on batch inference latency.',
        'recommendation_notes': 'Strongly recommended for Aurex Retail.'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        updated_sub = db.session.get(Submission, sub_id)
        assert updated_sub.status == Submission.STATUS_SHORTLISTED
        assert updated_sub.human_evaluation.score == 94

    # Login as Company Reviewer
    client.get('/quick-login/company_reviewer', follow_redirects=True)
    comp_res = client.get('/company/dashboard')
    assert comp_res.status_code == 200
    assert b"Nexus Dynamics" in comp_res.data

    # Company Reviewer selects proposal as winner
    select_res = client.post(f'/company/select/{sub_id}', data={
        'company_feedback': 'Selected by Aurex Retail for Phase 2 Validate.'
    }, follow_redirects=True)
    assert select_res.status_code == 200

    with app.app_context():
        winner_sub = db.session.get(Submission, sub_id)
        assert winner_sub.is_final_selected is True
        assert winner_sub.status == Submission.STATUS_NEXT_PHASE

def test_mentor_session_workflow(client):
    # Student requests slot
    client.get('/quick-login/student', follow_redirects=True)
    with app.app_context():
        slot = MentorSlot.query.filter_by(is_booked=False).first()
        slot_id = slot.id

    res = client.post('/mentor/request/book', data={
        'slot_id': slot_id,
        'topic': 'Reviewing GNN Model Trade-offs',
        'agenda_notes': 'Discuss latency vs accuracy.'
    }, follow_redirects=True)
    assert res.status_code == 200

    # Mentor accepts slot
    client.get('/quick-login/mentor', follow_redirects=True)
    with app.app_context():
        req = MentorSessionRequest.query.filter_by(mentor_slot_id=slot_id).first()
        req_id = req.id

    res = client.post(f'/mentor/request/{req_id}/respond', data={
        'action': 'accept',
        'mentor_notes': 'Session confirmed! Bring your architecture diagram.'
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        req = db.session.get(MentorSessionRequest, req_id)
        assert req.status == 'accepted'
        assert 'Session confirmed' in req.mentor_notes

def test_attachment_text_extraction(client, tmp_path):
    with app.app_context():
        # Test text extraction with a temporary text file
        test_file = tmp_path / "test_doc.txt"
        test_file.write_text("DegreeLabs Week 1 Problem Statement: High return rates in online fashion.", encoding="utf-8")
        
        extracted = extract_attachment_text(str(test_file))
        assert "DegreeLabs Week 1 Problem Statement" in extracted
        
        # Test None / empty path
        assert extract_attachment_text(None) == ""
        assert extract_attachment_text("") == ""
