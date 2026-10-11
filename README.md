# 🎯 ATS Resume Intelligence & Telegram Bot

An AI-powered system designed to analyze Job Descriptions, detect keyword/semantic gaps, reframe candidate achievements using Google's XYZ formula, and automatically generate ATS-compliant vector PDF resumes across 3 industry-standard templates.

---

## 🌟 Key Features

1. **Dual ATS Screening Engine**:
   - **Lexical/Keyword Analysis**: Exact token matching against mandatory and preferred skills (Kafka, Spring Boot, MongoDB, Docker, etc.).
   - **Semantic Alignment**: Measures domain alignment and responsibility relevance.
2. **Anti-Hallucination Resume Tailoring**:
   - Rewrites the professional summary and orders bullet points according to the target job description.
   - Enforces **Google's XYZ Formula**: *"Accomplished [X] as measured by [Y] by doing [Z]"*.
   - Strictly preserves true facts, metrics, and dates without fabricating fake experience.
3. **Multi-Template PDF Generator (ReportLab)**:
   - **Harvard Classic**: 100% parse-rate single-column template favored by top ATS (Workday, Taleo, Greenhouse).
   - **Modern Tech**: Accent typography, skills-first layout optimized for engineering recruiters.
   - **Compact 1-Page**: Dynamic padding control to guarantee a crisp single-page fit for 1–2 YOE.
4. **Interactive Telegram Bot**:
   - `/start` - Welcome & instructions
   - `/profile` - View current master profile
   - `/match <JD>` - Instant ATS compatibility score and gap analysis
   - `/tailor <JD>` - Generates tailored resume and sends downloadable PDF directly in chat.

---

## 🚀 Quick Start

### 1. Activate Environment
```bash
cd /Users/vaibhav/.gemini/antigravity/scratch/resume-bot
source venv/bin/activate
```

### 2. Configure Credentials
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your tokens:
- `TELEGRAM_BOT_TOKEN`: From Telegram's `@BotFather`
- `GEMINI_API_KEY`: From Google AI Studio (optional, automatic heuristic engine runs offline if unset)

### 3. Run Offline / Test Runner (CLI)
You can test resume tailoring and generate sample PDFs immediately without Telegram:
```bash
python cli_runner.py
```
Output PDFs will be saved to `generated_resumes/`.

### 4. Start Telegram Bot
```bash
python bot.py
```

---

## 📂 Project Structure

```
resume-bot/
├── models.py             # Pydantic schemas for Profile, JD, and ATS reports
├── default_profile.py   # Vaibhav's authentic master profile & STAR metrics
├── jd_analyzer.py       # Job description parser & ATS gap scoring
├── resume_tailor.py     # Gemini Flash-Lite & heuristic tailoring engine
├── pdf_generator.py     # ReportLab vector PDF builder (3 templates)
├── ats_validator.py     # 7-point ATS readiness auditor
├── bot.py               # Telegram bot handlers & document exporter
├── cli_runner.py        # Standalone test runner
├── config.py            # Environment & paths configuration
├── generated_resumes/   # Output folder for generated PDFs
├── requirements.txt     # Python dependencies
└── README.md            # Documentation
```
