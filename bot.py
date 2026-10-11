import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
from typing import Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters
)

import config
from default_profile import VAIBHAV_PROFILE
from jd_analyzer import analyze_job_description, compute_ats_match_score
from resume_tailor import tailor_resume
from pdf_generator import create_resume_pdf
from models import TemplateType, CandidateProfile
from ats_validator import audit_resume_ats_readiness

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# In-memory user state cache
user_sessions: Dict[int, dict] = {}

def get_user_profile(user_id: int) -> CandidateProfile:
    session = user_sessions.setdefault(user_id, {})
    if "profile" not in session:
        session["profile"] = VAIBHAV_PROFILE.model_copy(deep=True)
    return session["profile"]

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /start command."""
    user = update.effective_user
    welcome_text = (
        f"👋 Hello {user.first_name}!\n\n"
        "Welcome to **ATS Resume Intelligence Bot**.\n\n"
        "I help you tailor your resume to any specific Job Description to achieve **90%+ ATS Shortlist Rates**.\n\n"
        "📌 **Resume Tailoring Commands:**\n"
        "• `/profile` - View your loaded master profile & skills\n"
        "• `/match <paste JD>` - Analyze keyword gaps & ATS match score\n"
        "• `/tailor <paste JD>` - Generate an ATS-optimized resume & export PDF\n\n"
        "⚙️ **Custom Profile (For You or Friends):**\n"
        "• `/setname <Full Name>` - Update candidate name\n"
        "• `/setrole <Target Role>` - Update target job title\n"
        "• `/setskills <skill1, skill2>` - Update your skills\n"
        "• `/resetprofile` - Reset back to default profile\n"
        "• *Or upload a `.json` profile file directly to load a complete profile!*\n\n"
        "💡 *Tip:* You can also simply **paste any Job Description directly into this chat**, and I'll analyze it!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /profile command."""
    user_id = update.effective_user.id
    profile = get_user_profile(user_id)
    
    skills_summary = []
    for cat in profile.skills_categorized:
        skills_summary.append(f"• *{cat.category_name}*: {', '.join(cat.skills[:5])}")

    msg = (
        f"👤 *Candidate Master Profile*\n"
        f"• **Name:** {profile.contact.full_name}\n"
        f"• **Target Role:** {profile.target_role}\n"
        f"• **Location:** {profile.contact.location}\n"
        f"• **Total Experience:** ~1.5 Years (Software Engineer at Talenlio)\n\n"
        f"🛠 *Core Skills:*\n" + "\n".join(skills_summary) + "\n\n"
        f"💼 *Flagship Systems:*\n"
        f"• Kafka Event-Driven Ingestion Pipeline\n"
        f"• Gemini GenAI SDK Candidate Classification\n"
        f"• MongoDB $facet Latency Optimization (60k+ records)\n\n"
        "Send a Job Description to tailor this profile!"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def match_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /match <JD text> command."""
    user_id = update.effective_user.id
    jd_text = " ".join(context.args) if context.args else ""
    
    if not jd_text or len(jd_text.strip()) < 30:
        await update.message.reply_text(
            "⚠️ Please provide the job description text after `/match`.\n\n"
            "*Example:*\n`/match We are looking for a Java Backend Engineer with Spring Boot and Kafka experience...`",
            parse_mode="Markdown"
        )
        return

    await _process_jd_match(update, user_id, jd_text)

async def tailor_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles /tailor <JD text> command."""
    user_id = update.effective_user.id
    jd_text = " ".join(context.args) if context.args else ""

    if not jd_text or len(jd_text.strip()) < 30:
        await update.message.reply_text(
            "⚠️ Please provide the job description text after `/tailor`.\n\n"
            "*Example:*\n`/tailor We are looking for a Full-Stack Engineer with Java, Angular, and MongoDB...`",
            parse_mode="Markdown"
        )
        return

    await _process_jd_tailor(update, user_id, jd_text)

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles raw pasted JD text."""
    user_id = update.effective_user.id
    text = update.message.text
    if len(text.strip()) < 50:
        await update.message.reply_text(
            "Please paste a complete Job Description (at least a few sentences) to analyze."
        )
        return

    await _process_jd_tailor(update, user_id, text)

async def _process_jd_match(update: Update, user_id: int, jd_text: str):
    status_msg = await update.message.reply_text("🔍 Analyzing Job Description with ATS Engine...")
    profile = get_user_profile(user_id)
    
    jd = analyze_job_description(jd_text)
    score_report = compute_ats_match_score(profile, jd)

    match_box = (
        f"🎯 *ATS Match Analysis for: {jd.job_title}*\n\n"
        f"📊 *Scores:*\n"
        f"• **Overall ATS Compatibility:** `{score_report.overall_match_score}%`\n"
        f"• **Keyword Density:** `{score_report.keyword_match_score}%`\n"
        f"• **Semantic Match:** `{score_report.semantic_match_score}%`\n\n"
        f"✅ *Top Matched Keywords:*\n"
        f"`{', '.join(score_report.matched_keywords[:8]) or 'None'}`\n\n"
        f"⚠️ *Missing / Critical Gap Keywords:*\n"
        f"`{', '.join(score_report.missing_critical_keywords) or 'None'}`\n\n"
        f"💡 *Actionable Advice:*\n"
        + "\n".join([f"• {imp}" for imp in score_report.recommended_improvements])
    )
    
    keyboard = [
        [InlineKeyboardButton("📄 Generate Tailored PDF", callback_data="gen_tailored")]
    ]
    user_sessions[user_id]["last_jd"] = jd
    user_sessions[user_id]["last_score"] = score_report

    await status_msg.edit_text(match_box, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def _process_jd_tailor(update: Update, user_id: int, jd_text: str):
    status_msg = await update.message.reply_text("⚙️ Tailoring resume using Gemini Flash-Lite & Google XYZ formula...")
    profile = get_user_profile(user_id)
    
    jd = analyze_job_description(jd_text)
    score_report = compute_ats_match_score(profile, jd)
    tailored = tailor_resume(profile, jd, score_report)
    audit = audit_resume_ats_readiness(tailored)

    user_sessions[user_id]["tailored"] = tailored
    user_sessions[user_id]["last_jd"] = jd

    summary_text = (
        f"✅ *Resume Successfully Tailored!*\n\n"
        f"📌 *Target Role:* `{jd.job_title}`\n"
        f"📈 *ATS Match Score:* `{score_report.overall_match_score}%`\n"
        f"🛡 *ATS Readiness Audit:* `{audit['overall_readiness_score']}/100`\n"
        f"🎯 *XYZ Metric Bullets:* `{audit['metrics_percentage']}%` quantitative\n\n"
        "Choose an ATS-compliant template below to generate your PDF:"
    )

    keyboard = [
        [
            InlineKeyboardButton("🏛 Harvard Classic (100% ATS)", callback_data="tpl_harvard_classic"),
            InlineKeyboardButton("💻 Modern Tech", callback_data="tpl_modern_tech")
        ],
        [
            InlineKeyboardButton("📄 Compact 1-Page", callback_data="tpl_compact_one_page")
        ]
    ]

    await status_msg.edit_text(summary_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles template selection and document export."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    session = user_sessions.get(user_id, {})
    
    if query.data == "gen_tailored":
        jd = session.get("last_jd")
        if not jd:
            await query.message.reply_text("Session expired. Please paste the JD again.")
            return
        score_report = session.get("last_score")
        profile = get_user_profile(user_id)
        tailored = tailor_resume(profile, jd, score_report)
        session["tailored"] = tailored
        
        keyboard = [
            [
                InlineKeyboardButton("🏛 Harvard Classic", callback_data="tpl_harvard_classic"),
                InlineKeyboardButton("💻 Modern Tech", callback_data="tpl_modern_tech")
            ],
            [
                InlineKeyboardButton("📄 Compact 1-Page", callback_data="tpl_compact_one_page")
            ]
        ]
        await query.message.reply_text("Select your desired template:", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    if query.data.startswith("tpl_"):
        template_name = query.data.replace("tpl_", "")
        template = TemplateType(template_name)
        tailored = session.get("tailored")

        if not tailored:
            await query.message.reply_text("No tailored resume found. Please send a JD first.")
            return

        wait_msg = await query.message.reply_text(f"⏳ Compiling {template.value} vector PDF...")
        try:
            pdf_path = create_resume_pdf(tailored, template)
            with open(pdf_path, 'rb') as f:
                await query.message.reply_document(
                    document=f,
                    filename=os.path.basename(pdf_path),
                    caption=(
                        f"📄 **{tailored.candidate_profile.contact.full_name}** - Tailored Resume\n"
                        f"🎯 **Target Role:** {tailored.candidate_profile.target_role}\n"
                        f"🎨 **Template:** `{template.value}`\n"
                        f"🏆 **ATS Compatibility:** `{tailored.ats_score_report.overall_match_score}%`"
                    ),
                    parse_mode="Markdown"
                )
            await wait_msg.delete()
        except Exception as e:
            logger.error(f"Error generating PDF: {e}", exc_info=True)
            await wait_msg.edit_text(f"❌ Error generating PDF: {str(e)}")

async def setname_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets custom candidate name for this session."""
    name = " ".join(context.args).strip()
    if not name:
        await update.message.reply_text("Usage: `/setname John Doe`", parse_mode="Markdown")
        return
    user_id = update.effective_user.id
    profile = get_user_profile(user_id)
    profile.contact.full_name = name
    await update.message.reply_text(f"✅ Candidate name updated to: *{name}*", parse_mode="Markdown")

async def setrole_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets custom target role for this session."""
    role = " ".join(context.args).strip()
    if not role:
        await update.message.reply_text("Usage: `/setrole Frontend Developer`", parse_mode="Markdown")
        return
    user_id = update.effective_user.id
    profile = get_user_profile(user_id)
    profile.target_role = role
    await update.message.reply_text(f"✅ Target role updated to: *{role}*", parse_mode="Markdown")

async def setskills_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sets custom skills for this session."""
    skills_text = " ".join(context.args).strip()
    if not skills_text:
        await update.message.reply_text("Usage: `/setskills React, Node.js, Python, PostgreSQL`", parse_mode="Markdown")
        return
    skills_list = [s.strip() for s in skills_text.split(",") if s.strip()]
    user_id = update.effective_user.id
    profile = get_user_profile(user_id)
    from models import SkillCategory
    profile.skills_categorized = [
        SkillCategory(category_name="Custom Skills", skills=skills_list)
    ]
    await update.message.reply_text(f"✅ Skills updated ({len(skills_list)}): {', '.join(skills_list)}", parse_mode="Markdown")

async def resetprofile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Resets profile to default master profile."""
    user_id = update.effective_user.id
    user_sessions.setdefault(user_id, {})["profile"] = VAIBHAV_PROFILE.model_copy(deep=True)
    await update.message.reply_text("✅ Profile reset to default master profile.", parse_mode="Markdown")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles uploaded .json profile files."""
    doc = update.message.document
    if doc.file_name and doc.file_name.endswith(".json"):
        file = await context.bot.get_file(doc.file_id)
        content_bytes = await file.download_as_bytearray()
        try:
            custom_profile = CandidateProfile.model_validate_json(content_bytes)
            user_id = update.effective_user.id
            user_sessions.setdefault(user_id, {})["profile"] = custom_profile
            await update.message.reply_text(
                f"✅ Profile loaded from `{doc.file_name}` for *{custom_profile.contact.full_name}* ({custom_profile.target_role})!",
                parse_mode="Markdown"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Could not parse JSON profile: {str(e)}")

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass

def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

def main():
    """Runs the Telegram Bot."""
    # Start background HTTP health server for Render Free Web Service
    threading.Thread(target=start_health_server, daemon=True).start()

    if not config.TELEGRAM_BOT_TOKEN:
        print("[!] TELEGRAM_BOT_TOKEN not configured in .env. Bot cannot start without token.")
        print("[i] You can still test resume generation using python cli_runner.py!")
        return

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("match", match_command))
    app.add_handler(CommandHandler("tailor", tailor_command))
    app.add_handler(CommandHandler("setname", setname_command))
    app.add_handler(CommandHandler("setrole", setrole_command))
    app.add_handler(CommandHandler("setskills", setskills_command))
    app.add_handler(CommandHandler("resetprofile", resetprofile_command))
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    print("🤖 Telegram Resume Bot is active and listening for messages...")
    app.run_polling()

if __name__ == "__main__":
    main()
