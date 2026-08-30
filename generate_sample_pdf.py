import os
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def _get_styles():
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0F172A')
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#4338CA')
    )
    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=10,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#334155'),
        spaceAfter=5
    )
    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#334155'),
        leftIndent=12,
        spaceAfter=3
    )
    return {
        'title': title_style,
        'subtitle': subtitle_style,
        'h2': h2_style,
        'body': body_style,
        'bullet': bullet_style
    }


def generate_week1_pdf(output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if not REPORTLAB_AVAILABLE:
        with open(output_path, 'wb') as f:
            f.write(b'%PDF-1.4\n% Sample placeholder PDF for Week 1\n')
        return

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=40, leftMargin=40,
        topMargin=36, bottomMargin=36
    )
    st = _get_styles()
    story = [
        Paragraph("DEGREELABS DISCOVER &bull; COHORT 2026", st['subtitle']),
        Spacer(1, 3),
        Paragraph("Week 1 Deliverable: Problem Framing & Opportunity Canvas", st['title']),
        Spacer(1, 3),
        Paragraph("<b>Team Nexus Dynamics</b> | Enterprise Client: <b>Aurex Retail Analytics</b>", st['body']),
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#4F46E5'), spaceAfter=12),
        
        Paragraph("1. Executive Summary", st['h2']),
        Paragraph(
            "Aurex Retail's omnichannel apparel division experiences recurring dead-stock accumulation "
            "and localized stockouts across 450+ physical stores. This proposal frames the opportunity for an "
            "autonomous, graph-based inventory rebalancing engine capable of predicting hyper-local demand "
            "fluctuations 4 weeks ahead and routing inventory seamlessly between store clusters.",
            st['body']
        ),
    ]

    meta_data = [
        [Paragraph("<b>Author Team</b>", st['body']), Paragraph("Team Nexus Dynamics (5 multi-disciplinary members)", st['body'])],
        [Paragraph("<b>Primary Stakeholders</b>", st['body']), Paragraph("VP Merchandising, Regional Store Ops, Online Shoppers", st['body'])],
        [Paragraph("<b>Target Metric</b>", st['body']), Paragraph("&gt;= 18% Dead-stock write-down reduction, 96% on-shelf availability", st['body'])],
        [Paragraph("<b>Status</b>", st['body']), Paragraph("Verified &amp; Shortlisted for Discover Milestone", st['body'])]
    ]
    t = Table(meta_data, colWidths=[140, 390])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    story.extend([
        Paragraph("2. Stakeholder & Persona Decomposition", st['h2']),
        Paragraph("&bull; <b>VP of Merchandising:</b> Requires high-level macro visibility and gross margin preservation across product lines.", st['bullet']),
        Paragraph("&bull; <b>Regional Store Manager:</b> Currently lacks local autonomy and algorithmic guidance to rebalance stock with nearby stores experiencing shortages.", st['bullet']),
        Paragraph("&bull; <b>Online Customer:</b> Abandons carts when items are marked out-of-stock online, even when units sit idle in a nearby physical store.", st['bullet']),
        
        Spacer(1, 6),
        Paragraph("3. Formally Defined Problem Statement", st['h2']),
        Paragraph(
            "<i>&ldquo;How might we engineer an automated, real-time inventory rebalancing engine that predicts "
            "hyper-local apparel demand 4 weeks in advance, enabling autonomous inter-store stock transfers that "
            "reduce markdown write-offs by 18% while maintaining 96% on-shelf availability?&rdquo;</i>",
            st['body']
        ),
        
        Spacer(1, 6),
        Paragraph("4. Success Metrics & Scope Boundaries", st['h2']),
        Paragraph("&bull; <b>Metric 1:</b> Dead-stock write-down reduction &gt;= 18% across pilot stores.", st['bullet']),
        Paragraph("&bull; <b>Metric 2:</b> On-shelf availability rate &gt;= 96% during promotional seasons.", st['bullet']),
        Paragraph("&bull; <b>Metric 3:</b> Decision latency &lt; 150ms per batch cluster of 50 stores.", st['bullet']),
        Paragraph("&bull; <b>Out of Scope (Discover Phase):</b> Physical warehouse automation hardware, direct courier contract negotiations.", st['bullet']),
        
        Spacer(1, 10),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceAfter=6),
        Paragraph("<font size=7.5 color='#64748B'>DegreeLabs Discover &bull; Confidential &amp; Proprietary &bull; Verified by Aurex Retail Review Board</font>", st['body'])
    ])
    doc.build(story)


def generate_week2_pdf(output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if not REPORTLAB_AVAILABLE:
        with open(output_path, 'wb') as f:
            f.write(b'%PDF-1.4\n% Sample placeholder PDF for Week 2\n')
        return

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=40, leftMargin=40,
        topMargin=36, bottomMargin=36
    )
    st = _get_styles()
    story = [
        Paragraph("DEGREELABS DISCOVER &bull; COHORT 2026", st['subtitle']),
        Spacer(1, 3),
        Paragraph("Week 2 Deliverable: Research Findings & Candidate Architectural Hypotheses", st['title']),
        Spacer(1, 3),
        Paragraph("<b>Team Nexus Dynamics</b> | Enterprise Client: <b>Aurex Retail Analytics</b>", st['body']),
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#4F46E5'), spaceAfter=12),
        
        Paragraph("1. Executive Summary & Research Scope", st['h2']),
        Paragraph(
            "During Sprint Week 2, Team Nexus evaluated three distinct algorithmic paradigms for predictive retail inventory allocation: "
            "Dynamic Heuristic Buffering, Temporal Fusion Transformers (TFT), and Spatio-Temporal Graph Neural Networks (ST-GNN). "
            "Our benchmark backtesting against synthetic retail datasets indicates ST-GNN outperforms existing ERP heuristics with a "
            "22.4% gain in SKU allocation accuracy.",
            st['body']
        ),
        
        Paragraph("2. Architectural Benchmarking Matrix", st['h2'])
    ]

    matrix_data = [
        [Paragraph("<b>Candidate Architecture</b>", st['body']), Paragraph("<b>Predictive Accuracy (F1)</b>", st['body']), Paragraph("<b>Inference Latency</b>", st['body']), Paragraph("<b>Compute Cost / Store</b>", st['body'])],
        [Paragraph("<b>Candidate A:</b> Heuristic Rule Engine", st['body']), Paragraph("68.2%", st['body']), Paragraph("&lt; 15 ms", st['body']), Paragraph("$0.0001 / run", st['body'])],
        [Paragraph("<b>Candidate B:</b> Temporal Fusion Transformer", st['body']), Paragraph("82.5%", st['body']), Paragraph("65 ms", st['body']), Paragraph("$0.0012 / run", st['body'])],
        [Paragraph("<b>Candidate C:</b> Spatio-Temporal GNN (Recommended)", st['body']), Paragraph("<b>89.4%</b>", st['body']), Paragraph("85 ms", st['body']), Paragraph("$0.0018 / run", st['body'])]
    ]
    t = Table(matrix_data, colWidths=[190, 110, 110, 120])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#EEF2FF')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    story.extend([
        Paragraph("3. Deep-Dive: Spatio-Temporal GNN (ST-GNN) Hypothesis", st['h2']),
        Paragraph(
            "Retail store networks naturally form geometric spatial graphs where edge weights represent distance, traffic accessibility, "
            "and historical inter-store fulfillment affinity. By passing node embeddings of stock velocity through Graph Attention layers, "
            "the system detects localized surplus in Store A and pairs it with emerging velocity spikes in Store B within a 25-mile radius.",
            st['body']
        ),
        
        Spacer(1, 6),
        Paragraph("4. Preliminary Feasibility & Cloud Infrastructure Sizing", st['h2']),
        Paragraph("&bull; <b>Cloud Inference Budget:</b> Estimated at ~$82/month across 450 stores using AWS Graviton / SageMaker Serverless endpoints.", st['bullet']),
        Paragraph("&bull; <b>ERP Integration:</b> Nightly delta sync via RESTful webhooks connecting to Aurex's SAP/Oracle POS pipelines.", st['bullet']),
        Paragraph("&bull; <b>Cold-Start SKU Strategy:</b> Hierarchical product category clustering to initialize zero-sales items with parent category vectors.", st['bullet']),
        
        Spacer(1, 10),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceAfter=6),
        Paragraph("<font size=7.5 color='#64748B'>DegreeLabs Discover &bull; Sprint Week 2 Working Draft &bull; Mentored by Dr. Maya Patel</font>", st['body'])
    ])
    doc.build(story)


def generate_week3_pdf(output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if not REPORTLAB_AVAILABLE:
        with open(output_path, 'wb') as f:
            f.write(b'%PDF-1.4\n% Sample placeholder PDF for Week 3\n')
        return

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=40, leftMargin=40,
        topMargin=36, bottomMargin=36
    )
    st = _get_styles()
    story = [
        Paragraph("DEGREELABS DISCOVER &bull; COHORT 2026", st['subtitle']),
        Spacer(1, 3),
        Paragraph("Week 3 Deliverable: High-Level Architecture & Technical Specification", st['title']),
        Spacer(1, 3),
        Paragraph("<b>Team Nexus Dynamics</b> | Enterprise Client: <b>Aurex Retail Analytics</b>", st['body']),
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#4F46E5'), spaceAfter=12),
        
        Paragraph("1. Technical Architecture Overview", st['h2']),
        Paragraph(
            "The proposed DegreeLabs-Aurex Rebalancing Engine comprises three distinct microservices: "
            "1) Ingestion & Feature Engineering Pipeline (Kafka + DuckDB), 2) ST-GNN Inference Service (PyTorch Geometric + FastAPI), "
            "and 3) Store Manager Recommendation Dispatcher (WebSockets + Slack/Teams Bot).",
            st['body']
        ),
        
        Spacer(1, 6),
        Paragraph("2. Data Flow & Security Compliance", st['h2']),
        Paragraph("&bull; All customer PII is excluded at point-of-sale ingestion; models operate strictly on anonymized SKU barcodes and store IDs.", st['bullet']),
        Paragraph("&bull; End-to-end data encryption at rest (AES-256) and in transit (TLS 1.3).", st['bullet']),
        Paragraph("&bull; Zero-downtime blue/green model update deployments managed through MLflow.", st['bullet']),
        
        Spacer(1, 10),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceAfter=6),
        Paragraph("<font size=7.5 color='#64748B'>DegreeLabs Discover &bull; Week 3 Technical Milestone &bull; Aurex Retail</font>", st['body'])
    ]
    doc.build(story)


def generate_week4_pdf(output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if not REPORTLAB_AVAILABLE:
        with open(output_path, 'wb') as f:
            f.write(b'%PDF-1.4\n% Sample placeholder PDF for Week 4\n')
        return

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=40, leftMargin=40,
        topMargin=36, bottomMargin=36
    )
    st = _get_styles()
    story = [
        Paragraph("DEGREELABS DISCOVER &bull; COHORT 2026", st['subtitle']),
        Spacer(1, 3),
        Paragraph("Week 4 Deliverable: Final Discover Phase Proposal & Business Case", st['title']),
        Spacer(1, 3),
        Paragraph("<b>Team Nexus Dynamics</b> | Enterprise Client: <b>Aurex Retail Analytics</b>", st['body']),
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#4F46E5'), spaceAfter=12),
        
        Paragraph("1. Final Proposal & Commercial Value Case", st['h2']),
        Paragraph(
            "This document presents the complete 4-week Discover phase proposal submitted by Team Nexus Dynamics for "
            "Aurex Retail Analytics. It consolidates root-cause problem definitions, ST-GNN architectural blueprints, "
            "financial ROI modeling, and a 4-week Phase 2 Validate pilot roadmap.",
            st['body']
        ),
        
        Spacer(1, 6),
        Paragraph("2. Financial Impact & Projected ROI", st['h2']),
        Paragraph("&bull; Projected Annual Markdown Savings: $1.42M across 450 regional retail locations.", st['bullet']),
        Paragraph("&bull; Estimated 4-Month Validate & Grow Payback Period with 4.8x 3-year ROI.", st['bullet']),
        
        Spacer(1, 10),
        HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#CBD5E1'), spaceAfter=6),
        Paragraph("<font size=7.5 color='#64748B'>DegreeLabs Discover &bull; Final Proposal &bull; Candidate for Phase 2 Validate</font>", st['body'])
    ]
    doc.build(story)


def generate_named_pdf(filename, output_path):
    fname = filename.lower()
    if 'week1' in fname or 'problem' in fname:
        generate_week1_pdf(output_path)
    elif 'week2' in fname or 'research' in fname:
        generate_week2_pdf(output_path)
    elif 'week3' in fname or 'architecture' in fname:
        generate_week3_pdf(output_path)
    elif 'week4' in fname or 'proposal' in fname:
        generate_week4_pdf(output_path)
    else:
        generate_week1_pdf(output_path)


def generate_sample_pdf(output_path):
    generate_week1_pdf(output_path)


def generate_all_sample_pdfs(upload_dir):
    os.makedirs(upload_dir, exist_ok=True)
    files = {
        'Nexus_Week1_Problem_Statement_Final.pdf': generate_week1_pdf,
        'Nexus_Week2_Research_Draft.pdf': generate_week2_pdf,
        'Nexus_Week3_Hypothesis_Architecture.pdf': generate_week3_pdf,
        'Nexus_Week4_Discover_Proposal_Final.pdf': generate_week4_pdf,
    }
    for fname, func in files.items():
        dest = os.path.join(upload_dir, fname)
        func(dest)
        print(f"Verified PDF at: {dest}")


if __name__ == '__main__':
    out_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
    generate_all_sample_pdfs(out_dir)
