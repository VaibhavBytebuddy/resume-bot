import re
from typing import Dict, List, Any
from models import TailoredResume

ACTION_VERBS = [
    "architected", "engineered", "developed", "optimized", "spearheaded", "designed",
    "implemented", "automated", "reduced", "increased", "delivered", "built",
    "diagnosed", "integrated", "refactored", "resolved", "launched", "scaled"
]

def audit_resume_ats_readiness(resume: TailoredResume) -> Dict[str, Any]:
    """Audits the resume against common ATS parser criteria and recruiter standards."""
    checks = []
    score = 100

    # 1. Contact checks
    contact = resume.candidate_profile.contact
    if not contact.email or "@" not in contact.email:
        checks.append({"name": "Email Address", "passed": False, "msg": "Missing or invalid email."})
        score -= 15
    else:
        checks.append({"name": "Email Address", "passed": True, "msg": "Valid email detected."})

    if not contact.phone or len(contact.phone) < 8:
        checks.append({"name": "Phone Number", "passed": False, "msg": "Missing phone number."})
        score -= 10
    else:
        checks.append({"name": "Phone Number", "passed": True, "msg": "Phone number detected."})

    if not contact.linkedin_url:
        checks.append({"name": "LinkedIn Profile", "passed": False, "msg": "LinkedIn URL recommended."})
        score -= 5
    else:
        checks.append({"name": "LinkedIn Profile", "passed": True, "msg": "LinkedIn URL present."})

    # 2. Section Completeness
    has_skills = len(resume.highlighted_skills) > 0
    has_exp = len(resume.tailored_experience) > 0
    has_edu = len(resume.candidate_profile.education) > 0
    has_summary = len(resume.tailored_summary) > 40

    if not (has_skills and has_exp and has_edu and has_summary):
        checks.append({"name": "Standard Sections", "passed": False, "msg": "Missing one or more required sections."})
        score -= 20
    else:
        checks.append({"name": "Standard Sections", "passed": True, "msg": "All standard sections present."})

    # 3. Action Verb Analysis
    all_bullets = []
    for exp in resume.tailored_experience:
        all_bullets.extend(exp.bullets)
    for proj in resume.tailored_projects:
        all_bullets.extend(proj.bullets)

    action_verb_count = 0
    metric_count = 0
    for bullet in all_bullets:
        first_word = bullet.strip().split()[0].lower() if bullet.strip() else ""
        if any(v in first_word for v in ACTION_VERBS):
            action_verb_count += 1
        if re.search(r'\d+[%kKxXmsMS]?', bullet):
            metric_count += 1

    verb_rate = (action_verb_count / max(len(all_bullets), 1)) * 100
    metric_rate = (metric_count / max(len(all_bullets), 1)) * 100

    if verb_rate >= 60:
        checks.append({"name": "Strong Action Verbs", "passed": True, "msg": f"{int(verb_rate)}% of bullets start with strong action verbs."})
    else:
        checks.append({"name": "Strong Action Verbs", "passed": False, "msg": "More bullets should begin with strong action verbs."})
        score -= 10

    if metric_rate >= 50:
        checks.append({"name": "Measurable Metrics (XYZ)", "passed": True, "msg": f"{int(metric_rate)}% of bullets include quantitative impact."})
    else:
        checks.append({"name": "Measurable Metrics (XYZ)", "passed": False, "msg": "Add more measurable numbers and % improvements."})
        score -= 10

    # Total word count estimate
    text_corpus = resume.tailored_summary + " " + " ".join(all_bullets)
    word_count = len(text_corpus.split())

    if 350 <= word_count <= 750:
        checks.append({"name": "Word Count", "passed": True, "msg": f"Optimal length (~{word_count} words for 1 page)."})
    else:
        checks.append({"name": "Word Count", "passed": False, "msg": f"Word count ({word_count}) may cause density issues."})
        score -= 5

    return {
        "overall_readiness_score": max(score, 40),
        "checks": checks,
        "total_bullets_analyzed": len(all_bullets),
        "metrics_percentage": int(metric_rate),
        "action_verbs_percentage": int(verb_rate)
    }
