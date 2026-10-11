import json
import re
from typing import List
from models import (
    CandidateProfile, JobDescriptionAnalysis, 
    TailoredResume, ExperienceItem, ProjectItem, SkillCategory, AtsScoreReport
)
import config

def reorder_skills_for_jd(profile: CandidateProfile, jd: JobDescriptionAnalysis) -> List[SkillCategory]:
    """Reorders skills so that JD-relevant skills appear at the top of each category."""
    target_terms = set([s.lower() for s in jd.required_hard_skills + jd.preferred_skills + jd.domain_keywords])
    
    tailored_categories = []
    for cat in profile.skills_categorized:
        matched = []
        unmatched = []
        for skill in cat.skills:
            if any(term in skill.lower() or skill.lower() in term for term in target_terms):
                matched.append(skill)
            else:
                unmatched.append(skill)
        # Prioritize matching skills first
        ordered_skills = matched + unmatched
        tailored_categories.append(SkillCategory(
            category_name=cat.category_name,
            skills=ordered_skills
        ))
    return tailored_categories

def tailor_summary_heuristic(profile: CandidateProfile, jd: JobDescriptionAnalysis) -> str:
    """Creates a targeted 3-line professional summary emphasizing JD requirements."""
    title = re.sub(r'^[#*_\-\s]+', '', jd.job_title)
    title = re.sub(r'^(job\s*title|role|position|title)\s*:\s*', '', title, flags=re.IGNORECASE)
    title = re.split(r'[*|•\-]|\b(location|experience|exp|yoe|salary)\b', title, flags=re.IGNORECASE)[0].strip(" #*_-:[]()")
    if not title:
        title = "Software Engineer"
    top_skills = jd.required_hard_skills[:4]
    skills_phrase = f" specializing in {', '.join(top_skills)}" if top_skills else ""
    return (
        f"Results-oriented {title}{skills_phrase} with ~1.5 years of experience "
        f"architecting resilient backend microservices, event-driven pipelines, and high-performance APIs. "
        f"Proven track record of optimizing database throughput, implementing structured AI workflows, "
        f"and delivering scalable production systems with high reliability."
    )

def tailor_bullets_heuristic(bullets: List[str], jd: JobDescriptionAnalysis) -> List[str]:
    """Scores existing bullets by keyword relevance and orders high-match bullets first."""
    target_terms = set([s.lower() for s in jd.required_hard_skills + jd.preferred_skills + jd.domain_keywords])
    
    def score_bullet(b: str) -> int:
        score = 0
        b_lower = b.lower()
        for term in target_terms:
            if term in b_lower:
                score += 2
        # Bonus for numbers/metrics (XYZ formula)
        if re.search(r'\d+[%kKxXmsMS]?', b):
            score += 1
        return score

    return sorted(bullets, key=score_bullet, reverse=True)

def tailor_resume(
    profile: CandidateProfile, 
    jd: JobDescriptionAnalysis, 
    score_report: AtsScoreReport
) -> TailoredResume:
    """Generates a tailored resume matching the target JD using Gemini Flash-Lite with heuristic fallback."""
    tailored_skills = reorder_skills_for_jd(profile, jd)
    
    # Try Gemini AI tailoring if API key is provided
    if config.GEMINI_API_KEY:
        try:
            from google import genai
            client = genai.Client(api_key=config.GEMINI_API_KEY)
            
            prompt = f"""
You are an expert technical resume coach and ATS optimization specialist.
Re-tailor this candidate's resume for the target job description.

RULES:
1. NEVER hallucinate false companies, false titles, or fake numbers.
2. Emphasize the candidate's REAL achievements that directly match the JD's requirements.
3. Every bullet point MUST use the Google XYZ formula: "Accomplished [X] as measured by [Y] by doing [Z]".
4. Return ONLY a valid JSON object matching the schema below.

Target Job Title: {jd.job_title}
Key Required Skills: {', '.join(jd.required_hard_skills)}
Key Responsibilities: {', '.join(jd.key_responsibilities[:4])}

Candidate Current Summary:
{profile.professional_summary}

Candidate Work Experience Bullets:
{json.dumps([e.bullets for e in profile.experience])}

Schema to return:
{{
  "tailored_summary": "string (concise 3-line high impact summary)",
  "tailored_experience_bullets": [
    ["bullet1", "bullet2", "bullet3", "bullet4"]
  ]
}}
"""
            response = client.models.generate_content(
                model=config.GEMINI_MODEL_NAME,
                contents=prompt
            )
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            data = json.loads(text.strip())
            
            tailored_summary = data.get("tailored_summary", tailor_summary_heuristic(profile, jd))
            new_exp_bullets = data.get("tailored_experience_bullets", [])
            
            tailored_exp = []
            for i, exp in enumerate(profile.experience):
                bullets = new_exp_bullets[i] if i < len(new_exp_bullets) else exp.bullets
                tailored_exp.append(ExperienceItem(
                    company=exp.company,
                    role=exp.role,
                    location=exp.location,
                    start_date=exp.start_date,
                    end_date=exp.end_date,
                    bullets=bullets,
                    technologies=exp.technologies
                ))
            
            return TailoredResume(
                candidate_profile=profile,
                tailored_summary=tailored_summary,
                tailored_experience=tailored_exp,
                tailored_projects=profile.projects,
                highlighted_skills=tailored_skills,
                ats_score_report=score_report
            )
        except Exception as e:
            print(f"[Resume Tailor Warning] Gemini AI tailoring failed: {e}. Using deterministic optimization.")

    # Deterministic fallback
    tailored_summary = tailor_summary_heuristic(profile, jd)
    tailored_exp = []
    for exp in profile.experience:
        tailored_exp.append(ExperienceItem(
            company=exp.company,
            role=exp.role,
            location=exp.location,
            start_date=exp.start_date,
            end_date=exp.end_date,
            bullets=tailor_bullets_heuristic(exp.bullets, jd),
            technologies=exp.technologies
        ))

    return TailoredResume(
        candidate_profile=profile,
        tailored_summary=tailored_summary,
        tailored_experience=tailored_exp,
        tailored_projects=profile.projects,
        highlighted_skills=tailored_skills,
        ats_score_report=score_report
    )
