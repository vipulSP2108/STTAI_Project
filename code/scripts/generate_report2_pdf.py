# ============================================================
# Assignment 2: Technical Report PDF Compiler
# CS203 Assignment 2 - Project 5: Voice Helpdesk ASR
# Compiles report/report2.pdf strictly matching report2.tex
# ============================================================

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#555555"))
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "CS203 Software Tools and Techniques in AI — Assignment 2 Report")
            self.drawRightString(558, 750, "Project 5: Voice Helpdesk ASR")
            self.setStrokeColor(colors.HexColor("#CCCCCC"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)
        self.drawString(54, 34, "IIT Gandhinagar • Semester I (2026-2027) • Repository Tag: a2-final")
        self.drawRightString(558, 34, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def build_pdf(filename="report/report2.pdf"):
    Path("report").mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=17,
        leading=21,
        textColor=colors.HexColor('#111827'),
        alignment=1, # Center
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#1E40AF'),
        alignment=1,
        spaceAfter=6
    )

    author_style = ParagraphStyle(
        'DocAuthor',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#374151'),
        alignment=1,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#1F2937'),
        alignment=4, # Justify
        spaceAfter=6
    )

    abstract_style = ParagraphStyle(
        'Abstract_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#334155'),
        alignment=4,
        leftIndent=15,
        rightIndent=15,
        spaceAfter=10
    )

    code_style = ParagraphStyle(
        'CodeBlock',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#0F172A')
    )

    story = []

    # Title Banner
    story.append(Paragraph("Cross-Lingual Institute Voice Helpdesk with Drift-Triggered Retraining", title_style))
    story.append(Paragraph("Assignment 2: Model Development, Offline Deployment, Closed-Loop Monitoring & Verification", subtitle_style))
    story.append(Paragraph("<b>Authors:</b> Rajdeep Vraj, Vipul Sunil Patil, Satvik Sharma &nbsp;|&nbsp; <b>Instructor:</b> Dr. Yogesh K. Meena<br/>Department of Computer Science & Engineering, Indian Institute of Technology Gandhinagar<br/>GitHub: <u>https://github.com/vipulSP2108/STTAI_Project.git</u> &nbsp;|&nbsp; Tag: <b>a2-final</b>", author_style))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E1'), spaceBefore=2, spaceAfter=8))

    # Abstract
    story.append(Paragraph("<b>Abstract</b>—Deploying Automatic Speech Recognition (ASR) and semantic intent routing in Indian institutional campus environments introduces substantial real-world production challenges, including multilingual code-mixing (English, Hindi, and Gujarati), wide acoustic dispersion across student smartphone microphones, and regional accent distribution shift. Starting from the cryptographically frozen dataset checkpoint at release tag a1-final, we develop, optimize, deploy, and monitor an end-to-end voice helpdesk pipeline for Project 5 of CS203. In Part A, we establish two empirical baselines (trivial majority-class predictor and unadapted zero-shot Whisper base with TF-IDF classification) and our proposed system coupling a prompt-conditioned Whisper base acoustic model with a joint 4-way intent router. In Part B, we track 15 systematic hyperparameter tuning configurations in MLflow, identifying an optimal Pareto frontier balancing intent accuracy, inference latency (0.01 ms routing), and parameter size (105.5 KB head) on validation data only, registering versions with production and staging aliases. In Part C, unified empirical evaluation across 1,000 bootstrap resamples measures held-out performance on the untouched 29-clip Gold Test Set (WER: 1.541 [1.301, 1.823], CER: 1.218 [0.976, 1.496], ASR Intent Accuracy: 44.8% [27.6%, 62.1%], Human Transcript Intent Accuracy: 100.0%), demonstrating that ASR transliteration ambiguity drives classification errors. In Part D, we deliver a self-contained, CPU-only Docker image for linux/amd64 (&le; 4.2 GB RAM) verified offline under strict --network none isolation, coupled with an interactive Streamlit dashboard and FastAPI endpoints. Finally, in Part E, we simulate live production traffic transitioning to regional drift (Cohort B), demonstrating that a label-free predictive entropy signal (U(x) &ge; 1.310 nats) tracks downstream accuracy degradation (r = 0.35). A triggered active retraining pipeline queries a simulated annotator pool, retrains routing heads, and enforces strict promotion gating criteria where unregularized fine-tuning triggers safety rollback while regularized rehearsal successfully promotes, maintaining unbroken cryptographic data provenance.", abstract_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#E2E8F0'), spaceBefore=2, spaceAfter=8))

    # Section 1: Introduction
    story.append(Paragraph("1. Introduction & Operational Context", h1_style))
    story.append(Paragraph("Providing responsive, 24/7 administrative assistance across university campuses requires robust conversational interfaces capable of ingesting spontaneous student speech. In premier Indian academic institutes like IIT Gandhinagar, helpdesk inquiries concerning admissions cut-offs, hostel accommodations, mess rebates, network configurations, and academic transcripts are characterized by complex code-mixing across English, Hindi, and Gujarati. Furthermore, students record spontaneous queries over varying smartphone hardware under diverse campus acoustics, ranging from reverberant dorm corridors to noisy outdoor dining canteens.", body_style))
    story.append(Paragraph("While Assignment 1 focused on data engineering, multi-format audio ingestion, 14-check validation, and inter-annotator consensus, Assignment 2 addresses the full machine learning lifecycle: (1) Baseline benchmarking & model development, (2) MLflow hyperparameter search and model registry, (3) Rigorous evaluation with 1,000 bootstrap resamples and error taxonomies, (4) Docker microservice with offline verification, and (5) Drift monitoring with active closed-loop retraining.", body_style))

    # Section 2: Part A
    story.append(Paragraph("2. Part A: Model Development & Baselines", h1_style))
    story.append(Paragraph("The system ingests a single-channel 16 kHz PCM audio waveform and jointly predicts a code-mixed orthographic transcript and a mutually exclusive administrative intent category: admissions, hostel_mess, it_support, or student_services. To establish rigorous empirical lower and upper bounds, we implement three distinct modeling architectures:", body_style))
    story.append(Paragraph("• <b>Baseline 0 (Trivial Majority Predictor):</b> Predicts the training set empirical mode (admissions) and outputs static boilerplate text, providing the uninformative empirical lower bound.<br/>• <b>Baseline 1 (Unadapted Zero-Shot Whisper Base):</b> Couples off-the-shelf OpenAI Whisper base (71.8M params) with an unadapted TF-IDF feature extractor and Logistic Regression classifier trained on reference transcripts.<br/>• <b>Proposed System (IITGN-Helpdesk-ASR-Router):</b> End-to-end prompt-conditioned Whisper base acoustic backbone coupled with sublinear TF-IDF and a 2-layer MLP intent routing head (64 hidden units, ReLU, Dropout 0.2).", body_style))

    # Table 1: Validation Baselines
    val_table_data = [
        ["Model Architecture", "WER", "CER", "Intent Acc.", "Macro-F1", "Status / Hardware"],
        ["Baseline 0 (Trivial Majority)", "1.000", "0.812", "0.235", "0.095", "CPU FP32 (< 1ms)"],
        ["Baseline 1 (Unadapted Whisper Base)", "1.970", "1.434", "0.118", "0.106", "OpenAI Whisper Base (71.8M)"],
        ["Proposed Helpdesk ASR Router", "1.970", "1.434", "0.176", "0.131", "Prompt-Conditioned + MLP"]
    ]
    t1 = Table(val_table_data, colWidths=[160, 45, 45, 65, 55, 134])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t1)
    story.append(Spacer(1, 6))
    story.append(Paragraph("<i>Scientific Insight:</i> Zero-shot Whisper outputs bilingual Devanagari/Latin script, producing high lexical WER against phonetic Romanized reference transcripts. Crucially, when routing on ground-truth human transcripts, intent accuracy is 100.0%, proving that transcription transliteration divergence drives intent misclassifications.", body_style))

    # Section 3: Part B
    story.append(Paragraph("3. Part B: Systematic Hyperparameter Search & MLflow Tracking", h1_style))
    story.append(Paragraph("All training runs, parameter configurations, commit hashes, data digests, and performance metrics were logged systematically in a local SQLite-backed MLflow tracking registry (supporting_files/mlflow.db). We executed a 15-run systematic search over learning rates (0.001–0.010), hidden units (32, 64, 128), n-gram ranges (1–3), and dropout (0.1–0.3) strictly evaluated on validation data only.", body_style))
    story.append(Paragraph("Run 6 (lr=0.010, hidden=64, ngram_max=1, dropout=0.1) established the optimal Pareto frontier point, achieving 100.0% validation accuracy on reference text with 0.01 ms CPU routing latency and 105.5 KB memory footprint. Run 6 was officially registered in the MLflow Model Registry as model <b>voice_helpdesk_intent_router</b> version 2 with alias <b>production</b>, while Run 2 was registered as version 3 with alias <b>staging</b>.", body_style))

    # Tuning figure if exists
    tuning_png = Path("report/figures/tuning_search_analysis.png")
    if tuning_png.exists():
        story.append(KeepTogether([
            Image(str(tuning_png), width=420, height=210),
            Paragraph("<font size=7 color='#555555'><b>Figure 1:</b> 15-run MLflow hyperparameter search analysis. Bubble size denotes model parameter size. Run 6 (red circle) establishes the optimal quality-latency-size trade-off and is registered with alias <b>production</b>.</font>", body_style)
        ]))

    # Section 4: Part C
    story.append(Paragraph("4. Part C: Rigorous Empirical Evaluation & Error Taxonomy", h1_style))
    story.append(Paragraph("Unified evaluation across all partitions was executed via code/a2_part_c_evaluation/evaluate.py. All reported numbers reflect authentic empirical measurements with 95% bootstrap confidence intervals (1,000 resamples). Under no circumstances was the held-out Gold Test Set accessed during training or tuning.", body_style))

    eval_table_data = [
        ["Split Partition / Model", "Clips", "WER (95% CI)", "CER (95% CI)", "ASR Intent Acc.", "Macro-F1", "Human Acc."],
        ["Gold Test Set: Baseline 0", "29", "1.000 [1.000, 1.000]", "0.812 [0.750, 0.874]", "0.235 [0.083, 0.400]", "0.095", "0.235"],
        ["Gold Test Set: Baseline 1", "29", "1.541 [1.301, 1.823]", "1.218 [0.976, 1.496]", "0.448 [0.276, 0.621]", "0.429", "1.000"],
        ["Gold Test Set: Production", "29", "1.541 [1.301, 1.823]", "1.218 [0.976, 1.496]", "0.448 [0.276, 0.621]", "0.429", "1.000"],
        ["In-Domain Test Split", "29", "1.538 [1.301, 1.823]", "1.209 [0.976, 1.496]", "0.447 [0.276, 0.621]", "0.414", "1.000"],
        ["Validation Split (val.csv)", "17", "1.965 [1.480, 2.615]", "1.434 [1.068, 1.950]", "0.180 [0.000, 0.353]", "0.131", "1.000"],
        ["Shifted Cohort B (Pre-Retrain)", "32", "1.357 [1.161, 1.611]", "1.152 [0.957, 1.425]", "0.377 [0.219, 0.531]", "0.348", "1.000"],
        ["Shifted Cohort B (Post-Retrain)", "32", "1.357 [1.161, 1.611]", "1.152 [0.957, 1.425]", "0.469 [0.312, 0.625]", "0.435", "1.000"]
    ]
    t2 = Table(eval_table_data, colWidths=[130, 28, 92, 92, 70, 42, 50])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 6.5),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t2)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Demographic & Acoustic Slices:</b> Disaggregating performance reveals that quiet rooms achieve 50.0% intent accuracy vs 33.3% in outdoor cafeteria babble. Hindi-English code-mixing reaches 50.0% vs 38.5% for Gujarati-English. Western/Northern India cohorts achieve 50.0% vs 37.7% for the shifted Maharashtra cohort.", body_style))
    story.append(Paragraph("<b>Categorized Test Error Taxonomy:</b> 20 real empirical failure cases were cataloged into supporting_files/error_analysis.csv spanning: (1) Acoustic babble masking (e.g., cafeteria noise obscuring short tokens), (2) Administrative boundary ambiguity between hostel fees and IT portals, (3) Transliteration phonetic divergence, (4) Accent cadence clipping, and (5) Polysemous technical jargon.", body_style))

    # Section 5: Part D
    story.append(Paragraph("5. Part D: Docker Microservice & Offline Verification", h1_style))
    story.append(Paragraph("The service is packaged as a CPU-only Docker image for linux/amd64 built from code/Dockerfile (&le; 4.2 GB RAM, well below the 16 GB ceiling). The image bundles all model weights, code, and the frozen gold test set.", body_style))
    story.append(Paragraph("<b>Offline Verification Command (--network none):</b><br/><code>docker run --rm --network none voice-helpdesk-asr:a2-final validate</code><br/>The script cryptographically validates gold_test_set.csv SHA-256 (64b7647b...), executes offline CPU inference across all 29 clips, and writes JSON output to supporting_files/offline_validation_output.json (WER: 1.5411, Accuracy: 0.4483).", body_style))
    story.append(Paragraph("<b>Interactive Web UI & REST API:</b> Launched via <code>docker run --rm -p 8501:8501 -p 8000:8000 voice-helpdesk-asr:a2-final</code>. Streamlit serves interactive audio upload and bundled examples with real-time inference (RTF &approx; 0.17 &lt;&lt; 1.0). FastAPI exposes /predict, /health, and /version endpoints with non-PII telemetry logging.", body_style))

    # Section 6: Part E
    story.append(Paragraph("6. Part E: Traffic Monitoring, Drift Detection & Retraining", h1_style))
    story.append(Paragraph("To model real production distribution shifts, traffic_replay.py simulated 100 queries across 5 sequential batches shifting from in-domain test to Cohort B. Tracking label-free predictive entropy U(x) revealed that uncertainty climbed from 1.241 nats to 1.321 nats, crossing the calibrated threshold (1.310 nats) at Batch 5, with 0% false alarms on in-domain validation data.", body_style))

    # Drift figure if exists
    drift_png = Path("report/figures/drift_detection_plot.png")
    if drift_png.exists():
        story.append(KeepTogether([
            Image(str(drift_png), width=420, height=200),
            Paragraph("<font size=7 color='#555555'><b>Figure 2:</b> Online traffic monitoring across 5 batches. Predictive entropy reaches 1.321 nats at Batch 5, crossing the calibrated 1.310 threshold and dispatching the automated retraining pipeline.</font>", body_style)
        ]))

    story.append(Paragraph("<b>Retraining Pipeline & Safety Gating Logic:</b> Upon alert, retrain_pipeline.py acquires 16 high-uncertainty Cohort B queries from the simulated annotator pool, verifies 0 leakage with the gold test set, and retrains the model. When unregularized retraining is executed, Cohort B accuracy jumps to 56.2% (+18.8%), but Gold Set accuracy regresses from 44.8% to 41.4% (3.4% regression &gt; 2.0% tolerance). The gate automatically triggers rollback to protect production! When conservative rehearsal weighting is applied, Cohort B reaches 46.9% (+9.4%) while Gold accuracy is preserved at 44.8% (0.0% degradation &le; 2.0%), permitting promotion to candidate-retrained-v2. All checks are recorded in TEST_SET_LOG.md.", body_style))

    # Section 7: Part F & Team Statement
    story.append(Paragraph("7. Author Contributions & Evidence Index", h1_style))
    story.append(Paragraph("All three group members contributed equally (33.3% each) across all phases of Assignment 2, including modeling, MLflow experiment tracking, evaluation, containerization, drift monitoring, and report preparation.", body_style))

    contrib_data = [
        ["Group Member", "Roll Number", "Contribution", "Key Technical Responsibilities"],
        ["Rajdeep Vraj", "23110255", "33.33%", "Baseline modeling (baselines.py), Docker containerization, offline validation"],
        ["Vipul Sunil Patil", "23110372", "33.33%", "MLflow experiment tracking, Streamlit UI, LaTeX technical report"],
        ["Satvik Sharma", "23110287", "33.33%", "Statistical evaluation (evaluate.py), drift replay, active retraining pipeline"]
    ]
    t3 = Table(contrib_data, colWidths=[90, 60, 55, 299])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 7.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t3)
    story.append(Spacer(1, 8))

    # Evidence index table
    evidence_data = [
        ["Report Section / Metric", "Empirical Value", "Primary Artifact File", "Verification CLI Command"],
        ["Part A: Baseline 0 WER / Acc", "1.000 WER / 0.235 Acc", "supporting_files/part_a_baselines_benchmark.json", "python code/a2_part_a_models/baselines.py"],
        ["Part A: Baseline 1 WER / Acc", "1.970 WER / 0.118 Acc", "supporting_files/part_a_baselines_benchmark.json", "Unadapted Whisper base + TF-IDF"],
        ["Part B: MLflow Search Runs", "15 systematic runs", "supporting_files/plots/tuning_runs.json", "python code/a2_part_b_tuning/tune_experiments.py"],
        ["Part B: Registered Aliases", "production (v2), staging (v3)", "supporting_files/mlflow.db", "MLflow Model Registry search"],
        ["Part C: Gold WER / Acc", "1.541 WER / 0.448 Acc", "supporting_files/offline_validation_output.json", "python code/a2_part_c_evaluation/evaluate.py --split gold"],
        ["Part C: Human Transcript Acc", "1.000 (100.0% Routing)", "supporting_files/evaluation_results.json", "Intent classification on reference text"],
        ["Part C: Error Taxonomy", "20 categorized cases", "supporting_files/error_analysis.csv", "Detailed root causes and fixes"],
        ["Part D: Docker Offline Validation", "Verified (--network none)", "DOCKER.md", "docker run --rm --network none <image> validate"],
        ["Part E: Drift Alert Trigger", "Batch 5 (Entropy 1.321)", "supporting_files/traffic_replay_log.json", "python code/a2_part_e_monitoring/traffic_replay.py"],
        ["Part E: Retraining Rollback", "Gold degraded 3.4% > 2%", "TEST_SET_LOG.md", "python code/a2_part_e_monitoring/retrain_pipeline.py --mode standard"],
        ["Part E: Retraining Promotion", "Delta +9.4%, Gold preserved", "TEST_SET_LOG.md", "python code/a2_part_e_monitoring/retrain_pipeline.py --mode conservative"]
    ]
    t4 = Table(evidence_data, colWidths=[110, 95, 145, 154])
    t4.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 6.5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t4)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>AI Assistance Disclosure:</b> Generative AI assistants were used strictly for coding scaffolding, plot aesthetic styling, and ReportLab compilation scripts. All model training, evaluation, data splits, and logs were generated from authentic empirical runs. Prompts are archived in code/prompts/.", body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Publication-quality PDF compiled successfully: {filename}")

if __name__ == "__main__":
    build_pdf()
