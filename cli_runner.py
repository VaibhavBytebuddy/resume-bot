import sys
from pathlib import Path
from default_profile import VAIBHAV_PROFILE
from jd_analyzer import analyze_job_description, compute_ats_match_score
from resume_tailor import tailor_resume
from pdf_generator import create_resume_pdf
from models import TemplateType
from ats_validator import audit_resume_ats_readiness
import config

SAMPLE_JD = """
Job Title: Backend Software Engineer (Java / Spring Boot / Kafka)
Company: FinTech Global Solutions
Location: Pune, India / Remote
Experience: 1-3 years

About the Role:
We are seeking a talented Backend Software Engineer to design, build, and maintain mission-critical microservices.
You will work on high-throughput event streaming architectures, asynchronous processing, and cloud database optimization.

Requirements & Qualifications:
• 1-3 years experience building scalable backend services using Java (17+) and Spring Boot.
• Hands-on experience with Apache Kafka, message queues, and event-driven architecture.
• Strong database proficiency with MongoDB, document modeling, and index query optimization.
• Solid understanding of RESTful API design, microservices patterns, and Docker.
• Experience integrating AI/LLM APIs into enterprise services is a big plus.
• Familiarity with Angular, TypeScript, or modern frontend frameworks is desirable.
• Strong problem-solving skills and dedication to clean, maintainable code.

Responsibilities:
• Architect resilient microservices handling high-volume transaction processing.
• Optimize database queries, eliminate performance bottlenecks, and monitor p99 latency.
• Collaborate with cross-functional teams to deliver secure, production-grade features.
"""

def main():
    print("=" * 65)
    print("🚀 Running ATS Resume Intelligence Engine (CLI Test Runner)")
    print("=" * 65)

    print("\n1. Ingesting & Analyzing Job Description...")
    jd = analyze_job_description(SAMPLE_JD)
    print(f"   • Extracted Title: {jd.job_title}")
    print(f"   • Required Hard Skills: {', '.join(jd.required_hard_skills[:6])}")

    print("\n2. Computing ATS Match & Gap Analysis...")
    score_report = compute_ats_match_score(VAIBHAV_PROFILE, jd)
    print(f"   • Overall Compatibility Score: {score_report.overall_match_score}%")
    print(f"   • Keyword Match Score: {score_report.keyword_match_score}%")
    print(f"   • Semantic Alignment: {score_report.semantic_match_score}%")
    print(f"   • Matched Keywords ({len(score_report.matched_keywords)}): {', '.join(score_report.matched_keywords[:6])}")
    print(f"   • Missing Keywords ({len(score_report.missing_critical_keywords)}): {', '.join(score_report.missing_critical_keywords) or 'None'}")

    print("\n3. Tailoring Resume (Google XYZ formula & Keyword Alignment)...")
    tailored = tailor_resume(VAIBHAV_PROFILE, jd, score_report)
    print("   • Tailored Summary Generated:")
    print(f"     \"{tailored.tailored_summary}\"")

    print("\n4. Auditing ATS Readiness...")
    audit = audit_resume_ats_readiness(tailored)
    print(f"   • ATS Readiness Score: {audit['overall_readiness_score']}/100")
    print(f"   • XYZ Metric Bullets: {audit['metrics_percentage']}%")
    print(f"   • Strong Action Verbs: {audit['action_verbs_percentage']}%")

    print("\n5. Generating PDF Resumes Across All 3 ATS Templates...")
    templates = [
        TemplateType.HARVARD_CLASSIC,
        TemplateType.MODERN_TECH,
        TemplateType.COMPACT_ONE_PAGE
    ]
    
    generated_files = []
    for tpl in templates:
        pdf_path = create_resume_pdf(tailored, tpl)
        size_kb = Path(pdf_path).stat().st_size / 1024
        print(f"   ✅ [{tpl.value.upper()}] Generated: {pdf_path} ({size_kb:.1f} KB)")
        generated_files.append(pdf_path)

    print("\n" + "=" * 65)
    print(f"🎉 SUCCESS! All 3 production-grade ATS resumes generated in:")
    print(f"   {config.OUTPUT_DIR}")
    print("=" * 65)

if __name__ == "__main__":
    main()
