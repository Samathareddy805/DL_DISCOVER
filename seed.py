import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import json
from datetime import datetime, timedelta
from app import app
from models import (
    db, User, Company, Project, Team, TeamMember,
    DiscoverWeek, Session, MentorSlot, MentorSessionRequest,
    TeamScratchpad, Submission, AIFeedback, AIToDoItem,
    HumanEvaluation, CapabilityPassport
)
from generate_sample_pdf import generate_sample_pdf, generate_all_sample_pdfs

def seed_database():
    with app.app_context():
        # Ensure upload folder and sample files exist
        upload_folder = app.config.get('UPLOAD_FOLDER', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads'))
        os.makedirs(upload_folder, exist_ok=True)
        try:
            generate_all_sample_pdfs(upload_folder)
        except Exception as e:
            print(f"Warning generating sample PDFs: {e}")

        print("Dropping existing tables and creating fresh schema...")
        db.drop_all()
        db.create_all()

        print("Seeding Company & Industry Problem Statement...")
        company = Company(
            name="Aurex Retail Analytics",
            industry="Omni-Channel E-Commerce & Retail Intelligence",
            description=(
                "Aurex Retail Analytics empowers global fashion and apparel retail brands with real-time "
                "supply-chain intelligence, demand prediction, and automated inventory balancing across 1,200+ physical stores "
                "and online fulfillment nodes."
            ),
            logo_url="https://images.unsplash.com/photo-1542744094-3a31f272c490?w=200&auto=format&fit=crop&q=80",
            website="https://aurexretail.ai"
        )
        db.session.add(company)
        db.session.flush()

        project = Project(
            company_id=company.id,
            title="Predictive Inventory Balancing & Mark-Down Optimization for Omni-Channel Apparel Brands",
            problem_statement=(
                "Mid-to-high end apparel retail chains face up to 34% dead-stock write-downs and severe stockouts "
                "during mid-season promotional transitions. Current legacy ERP models rely on static historical store sales "
                "without factoring in localized micro-weather patterns, hyper-local social trend spikes, or dynamic online-to-offline return flow. "
                "Aurex seeks an end-to-end predictive decision framework and store-allocation engine that optimizes inventory distribution "
                "4 weeks in advance, reducing unsold inventory holding costs by at least 18% while maintaining a 96% in-stock availability rate."
            ),
            scope_summary=(
                "1. Root-cause analysis of cross-channel inventory friction and discount leakage.\n"
                "2. Competitive benchmarking of AI allocation frameworks vs. traditional rules engines.\n"
                "3. Technical architecture and algorithm roadmap for localized demand forecasting.\n"
                "4. Comprehensive business case, ROI model, and 90-day pilot rollout roadmap."
            ),
            target_audience="VP of Merchandising, Supply Chain Directors, Store Operations Heads",
            business_constraints="Must integrate seamlessly with SAP/Oracle retail ERPs; maximum 150ms inference latency per store batch."
        )
        db.session.add(project)
        db.session.flush()

        print("Seeding Users across all 4 RBAC roles...")
        # 1. Students (5 members for Team Nexus Dynamics)
        aarav = User(
            username="aarav.student",
            email="aarav.sharma@degree.edu",
            role="student",
            full_name="Aarav Sharma",
            discipline="Computer Science & Machine Learning",
            avatar_url="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80"
        )
        aarav.set_password("student123")

        priya = User(
            username="priya.student",
            email="priya.nair@degree.edu",
            role="student",
            full_name="Priya Nair",
            discipline="Data Science & Quantitative Analytics",
            avatar_url="https://images.unsplash.com/photo-1517841905240-472988babdf9?w=150&auto=format&fit=crop&q=80"
        )
        priya.set_password("student123")

        rohan = User(
            username="rohan.student",
            email="rohan.verma@degree.edu",
            role="student",
            full_name="Rohan Verma",
            discipline="Business Strategy & Supply Chain Management",
            avatar_url="https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&auto=format&fit=crop&q=80"
        )
        rohan.set_password("student123")

        ananya = User(
            username="ananya.student",
            email="ananya.iyer@degree.edu",
            role="student",
            full_name="Ananya Iyer",
            discipline="Commerce & Financial Economics",
            avatar_url="https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=150&auto=format&fit=crop&q=80"
        )
        ananya.set_password("student123")

        kabir = User(
            username="kabir.student",
            email="kabir.das@degree.edu",
            role="student",
            full_name="Kabir Das",
            discipline="Product Design & Human-Computer Interaction",
            avatar_url="https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=150&auto=format&fit=crop&q=80"
        )
        kabir.set_password("student123")

        db.session.add_all([aarav, priya, rohan, ananya, kabir])
        db.session.flush()

        # 2. Mentor
        mentor = User(
            username="maya.mentor",
            email="dr.maya.patel@degreelabs.mentor",
            role="mentor",
            full_name="Dr. Maya Patel",
            discipline="Principal Supply Chain AI Strategist",
            avatar_url="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=150&auto=format&fit=crop&q=80"
        )
        mentor.set_password("mentor123")
        db.session.add(mentor)
        db.session.flush()

        # 3. Evaluator / Admin
        evaluator = User(
            username="sarah.evaluator",
            email="sarah.jenkins@degreelabs.internal",
            role="evaluator",
            full_name="Sarah Jenkins",
            discipline="Director of Academic Evaluation & Industry Readiness",
            avatar_url="https://images.unsplash.com/photo-1580489944761-15a19d654956?w=150&auto=format&fit=crop&q=80"
        )
        evaluator.set_password("evaluator123")
        db.session.add(evaluator)
        db.session.flush()

        # 4. Company Reviewer
        company_reviewer = User(
            username="vikram.company",
            email="vikram.malhotra@aurexretail.ai",
            role="company_reviewer",
            full_name="Vikram Malhotra",
            discipline="VP of Product Innovation & Strategy",
            company_id=company.id,
            avatar_url="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&auto=format&fit=crop&q=80"
        )
        company_reviewer.set_password("company123")
        db.session.add(company_reviewer)
        db.session.flush()

        print("Seeding Team & 5-Member Composition...")
        team = Team(
            name="Nexus Dynamics (Team 04)",
            project_id=project.id,
            mentor_id=mentor.id,
            current_week=2
        )
        db.session.add(team)
        db.session.flush()

        team_memberships = [
            TeamMember(team_id=team.id, user_id=aarav.id, role_in_team="Team Lead & ML Architect"),
            TeamMember(team_id=team.id, user_id=priya.id, role_in_team="Data Science & Modeling Lead"),
            TeamMember(team_id=team.id, user_id=rohan.id, role_in_team="Supply Chain & Operations Strategist"),
            TeamMember(team_id=team.id, user_id=ananya.id, role_in_team="Financial Modeling & ROI Analyst"),
            TeamMember(team_id=team.id, user_id=kabir.id, role_in_team="UX/Product Interaction Designer")
        ]
        db.session.add_all(team_memberships)

        print("Seeding 4 Discover Program Weeks & Rubrics...")
        weeks_data = [
            {
                "week_number": 1,
                "title": "Problem & Company Understanding",
                "focus_area": "Deconstruct industry context, stakeholder map, and root pain points.",
                "objective": "Thoroughly understand the client company, market dynamics, and define a precise, verifiable problem statement.",
                "required_output_title": "Problem/Company Understanding + Defined Problem Statement",
                "rubric_checklist": [
                    "Comprehensive Company & Industry Overview (Aurex business model & value chain)",
                    "Stakeholder & Persona Mapping (Merchandiser, Store Manager, End-Customer)",
                    "Root Cause Problem Decomposition (Why traditional replenishment fails)",
                    "Formally Defined Problem Statement & Scope Boundaries",
                    "Success Metrics & Target KPI Benchmarks (e.g., 18% mark-down reduction)"
                ]
            },
            {
                "week_number": 2,
                "title": "Research & Ideation",
                "focus_area": "Competitive benchmarking, state-of-the-art methodology, candidate solution hypotheses.",
                "objective": "Conduct quantitative research, survey existing industry architectures, and generate 3 viable candidate solution approaches.",
                "required_output_title": "Research Findings + Candidate Solution Ideas",
                "rubric_checklist": [
                    "Market & Academic Literature Synthesis on Demand Forecasting",
                    "Benchmarking Matrix (Legacy ERP vs. Heuristic vs. Transformer ML)",
                    "Three Distinct Candidate Solution Architectures (Rule-based, Multi-agent, Graph Neural Network)",
                    "Comparative Trade-off Analysis (Latency, Explainability, Accuracy, Integration Cost)",
                    "Preliminary Technical & Business Feasibility Assessment"
                ]
            },
            {
                "week_number": 3,
                "title": "Solution Selection & Implementation Plan",
                "focus_area": "Select winning architecture, design system schema, and build 12-week execution roadmap.",
                "objective": "Select the optimal candidate idea with rigorous justification and build a comprehensive execution plan with risk mitigations.",
                "required_output_title": "Selected Idea Justification + Detailed Implementation Plan",
                "rubric_checklist": [
                    "Multi-Criteria Decision Matrix for Solution Selection",
                    "Detailed Technical Architecture & Data Pipeline Diagram",
                    "12-Week Phased Milestone Roadmap (Sprint breakdown)",
                    "Resource, Data, and Cloud Infrastructure Requirements",
                    "Risk Matrix & Failure Mode Mitigation Strategies"
                ]
            },
            {
                "week_number": 4,
                "title": "Industry-Grade Proposal & Presentation",
                "focus_area": "Executive synthesis, commercial viability, pitch deck, and stakeholder presentation.",
                "objective": "Synthesize Weeks 1-3 into a unified, industry-grade client proposal and deliver an executive presentation deck.",
                "required_output_title": "Industry-Grade Proposal Document + Executive Pitch Deck",
                "rubric_checklist": [
                    "Executive Summary with Clear Business Value Proposition",
                    "Consolidated Technical Architecture & Methodology",
                    "Commercial Viability, ROI Model, and 3-Year Financial Forecast",
                    "Change Management & Store Operations Integration Plan",
                    "Professional Presentation Deck & Video Walkthrough Asset"
                ]
            }
        ]

        for w in weeks_data:
            dw = DiscoverWeek(
                week_number=w["week_number"],
                title=w["title"],
                focus_area=w["focus_area"],
                objective=w["objective"],
                required_output_title=w["required_output_title"],
                rubric_checklist_json=json.dumps(w["rubric_checklist"]),
                deadline_days=7
            )
            db.session.add(dw)

        print("Seeding 12 Discover Online Sessions (8 Learning + 4 Working)...")
        sessions_data = [
            # Week 1
            {"week": 1, "num": 1, "title": "Program Kickoff & Company Deep Dive", "type": "learning", "status": "completed", "time": "Week 1 - Day 1 (Mon, 4:00 PM)", "desc": "Welcome address, Aurex Retail company background, and problem space briefing by program director.", "rec": "https://degreelabs.ai/recordings/session-01-kickoff"},
            {"week": 1, "num": 2, "title": "Deconstructing Complex Problem Statements", "type": "learning", "status": "completed", "time": "Week 1 - Day 3 (Wed, 4:00 PM)", "desc": "Structured frameworks for decomposing enterprise supply-chain pain points and framing hypothesis-driven problem statements.", "rec": "https://degreelabs.ai/recordings/session-02-problem-framing"},
            {"week": 1, "num": 3, "title": "Team Sprint: Week 1 Output Drafting & Peer Review", "type": "working", "status": "completed", "time": "Week 1 - Day 5 (Fri, 3:00 PM)", "desc": "Facilitated breakout rooms: teams draft problem statements and receive real-time mentor feedback.", "rec": "https://degreelabs.ai/recordings/session-03-working-sprint"},
            
            # Week 2
            {"week": 2, "num": 4, "title": "Enterprise Market Research & Benchmarking Strategies", "type": "learning", "status": "completed", "time": "Week 2 - Day 1 (Mon, 4:00 PM)", "desc": "Advanced competitive research methodologies, whitepaper analysis, and building defensible feature comparison matrices.", "rec": "https://degreelabs.ai/recordings/session-04-research-methods"},
            {"week": 2, "num": 5, "title": "Ideation & Architectural Trade-off Analysis", "type": "learning", "status": "upcoming", "time": "Week 2 - Day 3 (Wed, 4:00 PM)", "desc": "Techniques for generating distinct solution candidates, assessing algorithmic complexity vs. operational feasibility.", "rec": None},
            {"week": 2, "num": 6, "title": "Team Sprint: Candidate Ideation & Hypothesis Stress-Testing", "type": "working", "status": "upcoming", "time": "Week 2 - Day 5 (Fri, 3:00 PM)", "desc": "Hands-on collaborative sprint to finalize Week 2 candidate solution hypotheses and run AI Proposal Coach checks.", "rec": None},

            # Week 3
            {"week": 3, "num": 7, "title": "Decision Matrices & Solution Justification Frameworks", "type": "learning", "status": "upcoming", "time": "Week 3 - Day 1 (Mon, 4:00 PM)", "desc": "Quantifiable decision weighting, multi-variable scoring, and presenting defensible architectural choices to executive sponsors.", "rec": None},
            {"week": 3, "num": 8, "title": "Roadmap Architecture, Sprints & Risk Mitigation", "type": "learning", "status": "upcoming", "time": "Week 3 - Day 3 (Wed, 4:00 PM)", "desc": "Structuring enterprise deployment phases, identifying technical risks, and designing fallback protocols.", "rec": None},
            {"week": 3, "num": 9, "title": "Team Sprint: Implementation Blueprinting & Data Modeling", "type": "working", "status": "upcoming", "time": "Week 3 - Day 5 (Fri, 3:00 PM)", "desc": "Collaborative working lab for technical diagrams, data schemas, and sprint schedule drafting.", "rec": None},

            # Week 4
            {"week": 4, "num": 10, "title": "Structuring High-Impact Client Proposals", "type": "learning", "status": "upcoming", "time": "Week 4 - Day 1 (Mon, 4:00 PM)", "desc": "Synthesizing research into C-suite executive summaries, commercial financial modeling, and strategic narrative design.", "rec": None},
            {"week": 4, "num": 11, "title": "Pitch Delivery & Stakeholder Q&A Mastery", "type": "learning", "status": "upcoming", "time": "Week 4 - Day 3 (Wed, 4:00 PM)", "desc": "Live presentation rehearsals, defending assumptions against industry review panels, and managing executive feedback.", "rec": None},
            {"week": 4, "num": 12, "title": "Final Discover Showcase & Evaluator Pitch Day", "type": "working", "status": "upcoming", "time": "Week 4 - Day 5 (Fri, 2:00 PM)", "desc": "Official Discover cohort presentation to DegreeLabs Evaluators for company shortlisting decisions.", "rec": None}
        ]

        for s in sessions_data:
            sess = Session(
                week_number=s["week"],
                session_number=s["num"],
                title=s["title"],
                session_type=s["type"],
                description=s["desc"],
                scheduled_at=s["time"],
                status=s["status"],
                recording_url=s["rec"]
            )
            db.session.add(sess)

        print("Seeding Mentor Availability Slots & Session Requests...")
        slot1 = MentorSlot(
            mentor_id=mentor.id,
            start_time="Thursday, Aug 28 - 3:00 PM",
            end_time="Thursday, Aug 28 - 4:00 PM",
            is_booked=True
        )
        slot2 = MentorSlot(
            mentor_id=mentor.id,
            start_time="Friday, Aug 29 - 4:30 PM",
            end_time="Friday, Aug 29 - 5:30 PM",
            is_booked=False
        )
        slot3 = MentorSlot(
            mentor_id=mentor.id,
            start_time="Monday, Sep 01 - 2:00 PM",
            end_time="Monday, Sep 01 - 3:00 PM",
            is_booked=False
        )
        db.session.add_all([slot1, slot2, slot3])
        db.session.flush()

        req1 = MentorSessionRequest(
            team_id=team.id,
            mentor_slot_id=slot1.id,
            topic="Reviewing Week 2 Candidate ML Models & ERP Data Ingestion Strategy",
            agenda_notes="We want Dr. Maya's guidance on comparing GNN vs. Temporal Fusion Transformers for 4-week retail demand spikes.",
            status="accepted",
            mentor_notes="Approved. Bring your data schema and benchmark trade-off matrix to the call. Look into cold-start store allocations.",
            meeting_link="https://degreelabs.ai/mentor/space-room-nexus",
            responded_at=datetime.utcnow() - timedelta(days=1)
        )
        db.session.add(req1)

        print("Seeding Team Scratchpad...")
        scratchpad = TeamScratchpad(
            team_id=team.id,
            week_number=2,
            content=(
                "Team Scratchpad Notes (Week 2 Sprint):\n"
                "- Aarav: Exploring Graph Convolutional Networks (GCN) for inter-store stock rebalancing.\n"
                "- Priya: Running historical synthetic backtests on apparel promotional markdown datasets.\n"
                "- Rohan: Interviewed 2 retail store managers — stockouts often occur due to delayed online return processing.\n"
                "- Ananya: Drafting unit economics model for 18% dead-stock reduction.\n"
                "- Kabir: Wireframing store manager allocation override interface."
            ),
            updated_by_name="Aarav Sharma"
        )
        db.session.add(scratchpad)

        print("Seeding Sample Submissions (Week 1 Evaluated/Shortlisted & Week 2 in Working Draft)...")
        # Week 1 Submission (Fully submitted, AI analyzed, Evaluated, and Shortlisted)
        sub1 = Submission(
            team_id=team.id,
            week_number=1,
            title="Nexus Dynamics - Problem Understanding & Root Cause Statement: Aurex Omnichannel Allocation",
            executive_summary=(
                "A comprehensive root-cause analysis of supply chain friction across Aurex Retail Analytics' client portfolio. "
                "We identified that 72% of mid-season mark-down losses stem from disconnected inventory silos between localized retail stores "
                "and centralized e-commerce warehouses, exacerbated by a 14-day lag in legacy ERP replenishment batch jobs."
            ),
            content=(
                "## 1. Company & Industry Context\n"
                "Aurex Retail Analytics serves Tier-1 fashion retailers. The primary challenge is balancing fast-fashion inventory volatility "
                "with high seasonal markdowns. In the apparel segment, 34% of seasonal margin is lost to emergency discounting.\n\n"
                "## 2. Stakeholder & Persona Decomposition\n"
                "- **VP of Merchandising**: Needs high-level macro visibility and margin preservation.\n"
                "- **Regional Store Manager**: Lacks local autonomy to rebalance stock with nearby stores experiencing shortages.\n"
                "- **Online Customer**: Abandons cart when item is out of stock online even though it sits idle in a physical store 5 miles away.\n\n"
                "## 3. Formally Defined Problem Statement\n"
                "How might we engineer an automated, real-time inventory rebalancing engine that predicts hyper-local apparel demand 4 weeks in advance, "
                "enabling autonomous inter-store stock transfers that reduce markdown write-offs by 18% while maintaining 96% on-shelf availability?\n\n"
                "## 4. Success Metrics & Scope Boundaries\n"
                "- Metric 1: Dead-stock write-down reduction >= 18%\n"
                "- Metric 2: On-shelf availability rate >= 96%\n"
                "- Metric 3: Decision latency < 150ms per batch of 50 stores"
            ),
            file_attachment_name="Nexus_Week1_Problem_Statement_Final.pdf",
            file_attachment_path="/uploads/Nexus_Week1_Problem_Statement_Final.pdf",
            status=Submission.STATUS_SHORTLISTED,
            submitted_at=datetime.utcnow() - timedelta(days=5)
        )
        db.session.add(sub1)
        db.session.flush()

        # AI Feedback for Week 1
        ai_fb1 = AIFeedback(
            submission_id=sub1.id,
            readiness_score=92,
            strengths_json=json.dumps([
                "Crystal clear problem statement with measurable KPIs (18% markdown reduction, 96% availability).",
                "Deep stakeholder persona decomposition spanning merchandising, store ops, and online buyers.",
                "Thorough analysis of Aurex's enterprise ERP integration constraints."
            ]),
            gaps_json=json.dumps([
                "Consider specifying the baseline historical data window required for training."
            ]),
            suggested_next_steps_json=json.dumps([
                "Incorporate Week 2 research comparing multi-node graph models against single-store regressors.",
                "Verify ERP data schema compatibility with Aurex engineering team."
            ]),
            raw_summary=(
                "Exceptional Week 1 deliverable. The problem statement is rigorously bounded, financially justified, "
                "and directly targets Aurex's core supply-chain bottleneck. Readiness score: 92/100."
            )
        )
        db.session.add(ai_fb1)

        # Human Evaluation for Week 1
        eval1 = HumanEvaluation(
            submission_id=sub1.id,
            evaluator_id=evaluator.id,
            score=90,
            criteria_scores_json=json.dumps({
                "problem_clarity": 95,
                "stakeholder_depth": 90,
                "methodological_rigor": 88,
                "business_relevance": 92
            }),
            strengths="Outstanding problem decomposition and stakeholder analysis. The team demonstrated strong grasp of fashion retail unit economics.",
            weaknesses="Ensure Week 2 delves deep into real-time latency trade-offs.",
            recommendation_notes="Approved for shortlisting. Highly recommended for company presentation pipeline.",
            decision="shortlisted",
            evaluated_at=datetime.utcnow() - timedelta(days=4)
        )
        db.session.add(eval1)

        # Week 2 Submission (In Working Draft - ready for AI Coach demo)
        sub2 = Submission(
            team_id=team.id,
            week_number=2,
            title="Nexus Dynamics - Research Findings & Candidate Architectural Hypotheses",
            executive_summary=(
                "Week 2 research report evaluating three distinct algorithmic architectures for predictive retail inventory allocation: "
                "1) Rule-Based Heuristic with Moving Averages, 2) Temporal Fusion Transformer (TFT), and 3) Spatio-Temporal Graph Neural Network (ST-GNN). "
                "Initial backtest simulations show ST-GNN delivers a 22.4% boost in allocation accuracy across clustered store networks."
            ),
            content=(
                "## 1. Literature & Market Research Synthesis\n"
                "We reviewed modern demand forecasting approaches across fast-moving fashion retail. Traditional ARIMA and rule-based heuristics "
                "fail to capture cross-store cannibalization and regional social trend virality.\n\n"
                "## 2. Comparative Benchmarking Matrix\n"
                "We benchmarked three candidate approaches across Accuracy, Interpretability, Computational Cost, and Cold-Start Resilience:\n"
                "- Candidate A: Dynamic Heuristic Buffer Sizing (Fast, low cost, but low accuracy: 68% F1)\n"
                "- Candidate B: Temporal Fusion Transformer (High time-series accuracy, moderate latency)\n"
                "- Candidate C: Spatio-Temporal GNN with Graph Attention (Highest cross-store transfer accuracy: 89% F1)\n\n"
                "## 3. Trade-off Analysis & Feasibility\n"
                "Candidate C provides spatial graph modeling between adjacent stores within a 25-mile radius, allowing autonomous peer-to-peer "
                "inventory transfer suggestions before triggering expensive warehouse shipments."
            ),
            file_attachment_name="Nexus_Week2_Research_Draft.pdf",
            file_attachment_path="/uploads/Nexus_Week2_Research_Draft.pdf",
            status=Submission.STATUS_WORKING,
            submitted_at=None
        )
        db.session.add(sub2)
        db.session.flush()

        # Seed initial AI feedback for Week 2 draft
        ai_fb2 = AIFeedback(
            submission_id=sub2.id,
            readiness_score=78,
            strengths_json=json.dumps([
                "Addressed: Market & Academic Literature Synthesis on Demand Forecasting",
                "Addressed: Benchmarking Matrix (Legacy ERP vs. Heuristic vs. Transformer ML)",
                "Addressed: Three Distinct Candidate Solution Architectures"
            ]),
            gaps_json=json.dumps([
                "Requires elaboration: Preliminary Technical & Business Feasibility Assessment with cloud infrastructure cost estimates",
                "Detailed cold-start handling for new store openings is missing from Candidate C"
            ]),
            suggested_next_steps_json=json.dumps([
                "Add cloud compute sizing (GPU inference costs) to complete the feasibility assessment.",
                "Detail how Candidate C handles new seasonal SKUs with zero historical sales data."
            ]),
            raw_summary=(
                "Promising Week 2 research draft. Strong algorithmic benchmarking and clear trade-off analysis. "
                "To raise readiness score to 90+, expand the technical feasibility assessment and compute budget estimates."
            )
        )
        db.session.add(ai_fb2)

        todo_w2 = AIToDoItem(
            submission_id=sub2.id,
            section_name="Preliminary Technical & Business Feasibility Assessment",
            prompt_for_student="Provide dedicated details on inference latency, cloud compute cost per store, and ERP API rate limits.",
            is_resolved=False
        )
        db.session.add(todo_w2)

        print("Seeding Capability Passport for Aarav Sharma & Team Nexus Dynamics...")
        passport = CapabilityPassport(
            user_id=aarav.id,
            team_id=team.id,
            passport_code="DL-PASSPORT-2026-NEXUS-04",
            certificates_json=json.dumps([
                {
                    "title": "Discover Week 1 Mastery: Enterprise Problem Definition",
                    "badge_code": "DISCOVER-W1-VERIFIED",
                    "issued_by": "DegreeLabs Academic Board",
                    "date": (datetime.utcnow() - timedelta(days=4)).strftime("%b %d, %Y"),
                    "status": "Verified & Issued",
                    "score": 90,
                    "skills": ["Root Cause Analysis", "Stakeholder Mapping", "Problem Scoping", "KPI Formulation"]
                }
            ]),
            competency_scores_json=json.dumps({
                "Problem Decomposition & Scoping": 92,
                "Analytical Research & Benchmarking": 85,
                "Algorithmic & Technical Design": 88,
                "Business Strategy & Unit Economics": 90,
                "Executive Communication & Proposal Writing": 84
            }),
            evidence_log_json=json.dumps([
                {
                    "week": "Week 1",
                    "deliverable": "Problem Understanding & Defined Problem Statement",
                    "timestamp": (datetime.utcnow() - timedelta(days=5)).strftime("%b %d, %Y - 18:30 UTC"),
                    "human_score": "90 / 100",
                    "ai_score": "92 / 100",
                    "evaluator_verdict": "Shortlisted for Industry Presentation",
                    "artifact_url": "/submissions/1"
                },
                {
                    "week": "Week 2",
                    "deliverable": "Research Findings & Candidate Ideas (In Progress)",
                    "timestamp": "Current Sprint",
                    "human_score": "Pending Evaluation",
                    "ai_score": "78 / 100 (AI Coach Draft)",
                    "evaluator_verdict": "Working Draft",
                    "artifact_url": "/submissions/2"
                }
            ])
        )
        db.session.add(passport)

        db.session.commit()
        print("Database seeded successfully with all roles, data, and workflows!")

if __name__ == '__main__':
    seed_database()
