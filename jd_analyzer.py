import re
import json
from typing import List, Tuple, Set
from models import CandidateProfile, JobDescriptionAnalysis, AtsScoreReport
import config

COMMON_TECH_SKILLS = [
    "java", "spring boot", "kafka", "apache kafka", "mongodb", "mongo", "mysql", "postgresql",
    "sql", "redis", "docker", "kubernetes", "aws", "gcp", "google cloud", "azure", "angular",
    "react", "typescript", "javascript", "python", "go", "golang", "microservices", "rest api",
    "restful", "ci/cd", "git", "gitlab", "github", "junit", "maven", "gradle", "rabbitmq",
    "graphql", "flutter", "dart", "nosql", "elasticsearch", "gemini", "llm", "generative ai"
]

def parse_jd_heuristic(jd_text: str) -> JobDescriptionAnalysis:
    """Fast local parser when API key is offline."""
    lower_jd = jd_text.lower()
    
    # Extract matching skills
    found_skills = []
    for skill in COMMON_TECH_SKILLS:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, lower_jd):
            found_skills.append(skill.title() if len(skill) > 3 else skill.upper())
            
    # Try to extract job title from first lines
    lines = [l.strip() for l in jd_text.strip().split("\n") if l.strip()]
    job_title = "Software Engineer"
    for line in lines[:5]:
        if any(term in line.lower() for term in ["engineer", "developer", "architect", "lead", "specialist"]):
            clean_title = re.sub(r'^[#*_\-\s]+', '', line)
            clean_title = re.sub(r'^(job\s*title|role|position|title)\s*:\s*', '', clean_title, flags=re.IGNORECASE)
            clean_title = re.split(r'[*|•\-]|\b(location|experience|exp|yoe|salary)\b', clean_title, flags=re.IGNORECASE)[0]
            clean_title = clean_title.strip(" #*_-:[]()")
            if clean_title:
                job_title = clean_title[:40]
            break

    # Extract bullet points as responsibilities
    responsibilities = []
    for line in lines:
        if line.startswith(("-", "•", "*", "–")) or re.match(r'^\d+\.', line):
            clean = re.sub(r'^[-•*–\d\.]+\s*', '', line).strip()
            if len(clean) > 20:
                responsibilities.append(clean)
                if len(responsibilities) >= 6:
                    break

    return JobDescriptionAnalysis(
        job_title=job_title,
        required_hard_skills=found_skills[:12],
        preferred_skills=found_skills[12:18],
        key_responsibilities=responsibilities if responsibilities else ["Deliver scalable features and backend services."],
        domain_keywords=found_skills[:8],
        minimum_years_experience=2
    )

def analyze_job_description(jd_text: str) -> JobDescriptionAnalysis:
    """Analyzes JD using Gemini Flash-Lite with fallback to local heuristic engine."""
    if not jd_text or len(jd_text.strip()) < 20:
        raise ValueError("Job description is too short to analyze.")

    if not config.GEMINI_API_KEY:
        return parse_jd_heuristic(jd_text)

    try:
        from google import genai
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        
        prompt = f"""
You are an expert ATS (Applicant Tracking System) parser.
Analyze this Job Description and return a strictly valid JSON object matching this schema:
{{
  "job_title": "string",
  "company_name": "string",
  "required_hard_skills": ["string"],
  "preferred_skills": ["string"],
  "key_responsibilities": ["string"],
  "domain_keywords": ["string"],
  "minimum_years_experience": integer
}}

Job Description Text:
\"\"\"
{jd_text[:4000]}
\"\"\"

Return ONLY the raw JSON object, no markdown codeblocks, no commentary.
"""
        response = client.models.generate_content(
            model=config.GEMINI_MODEL_NAME,
            contents=prompt
        )
        text = response.text.strip()
        # Clean potential markdown wrapping
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        data = json.loads(text)
        return JobDescriptionAnalysis(**data)
    except Exception as e:
        print(f"[JD Analyzer Warning] Gemini API error: {e}. Falling back to heuristic analyzer.")
        return parse_jd_heuristic(jd_text)

def compute_ats_match_score(profile: CandidateProfile, jd: JobDescriptionAnalysis) -> AtsScoreReport:
    """Computes comprehensive keyword and qualification alignment between candidate and target JD."""
    # Flatten candidate skills
    candidate_tokens = set()
    for cat in profile.skills_categorized:
        for s in cat.skills:
            candidate_tokens.add(s.lower().strip())
    
    # Also gather tokens from experience & projects
    for exp in profile.experience:
        for b in exp.bullets:
            for word in re.findall(r'\b[a-zA-Z0-9\+\#\.\-]{2,}\b', b.lower()):
                candidate_tokens.add(word)
        for t in exp.technologies:
            candidate_tokens.add(t.lower().strip())

    for proj in profile.projects:
        for b in proj.bullets:
            for word in re.findall(r'\b[a-zA-Z0-9\+\#\.\-]{2,}\b', b.lower()):
                candidate_tokens.add(word)
        for t in proj.technologies:
            candidate_tokens.add(t.lower().strip())

    matched_keywords = []
    missing_keywords = []

    target_requirements = set([s.lower().strip() for s in jd.required_hard_skills + jd.preferred_skills])
    if not target_requirements:
        target_requirements = set([s.lower().strip() for s in jd.domain_keywords])

    for req in target_requirements:
        # Check direct or substring match
        if any(req in cand or cand in req for cand in candidate_tokens):
            matched_keywords.append(req.title())
        else:
            missing_keywords.append(req.title())

    total_reqs = max(len(target_requirements), 1)
    kw_ratio = len(matched_keywords) / total_reqs
    keyword_score = int(min(kw_ratio * 100, 100))

    # Base score incorporates core experience presence
    has_experience = 1 if len(profile.experience) > 0 else 0
    has_projects = 1 if len(profile.projects) > 0 else 0
    has_summary = 1 if len(profile.professional_summary) > 50 else 0

    completeness_score = int((has_experience * 40) + (has_projects * 30) + (has_summary * 30))
    overall_score = int((keyword_score * 0.65) + (completeness_score * 0.35))
    semantic_score = min(keyword_score + 10, 98)

    improvements = []
    if missing_keywords:
        top_missing = missing_keywords[:4]
        improvements.append(f"Consider integrating these target keywords if you have hands-on experience: {', '.join(top_missing)}")
    if keyword_score < 70:
        improvements.append("Tailor bullet points to emphasize relevant domain terminology matching the job specification.")
    improvements.append("Ensure bullet points follow the Google XYZ formula (Accomplished [X] measured by [Y] by doing [Z]).")

    return AtsScoreReport(
        overall_match_score=overall_score,
        keyword_match_score=keyword_score,
        semantic_match_score=semantic_score,
        matched_keywords=matched_keywords,
        missing_critical_keywords=missing_keywords[:6],
        recommended_improvements=improvements
    )
