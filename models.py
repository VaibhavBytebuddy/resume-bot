from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

class TemplateType(str, Enum):
    HARVARD_CLASSIC = "harvard_classic"
    MODERN_TECH = "modern_tech"
    COMPACT_ONE_PAGE = "compact_one_page"

class ContactInfo(BaseModel):
    full_name: str
    email: str
    phone: str
    location: str
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None

class ExperienceItem(BaseModel):
    company: str
    role: str
    location: Optional[str] = None
    start_date: str
    end_date: str
    bullets: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)

class ProjectItem(BaseModel):
    title: str
    subtitle: Optional[str] = None
    link: Optional[str] = None
    bullets: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)

class EducationItem(BaseModel):
    degree: str
    institution: str
    location: Optional[str] = None
    graduation_year: str
    grade_or_gpa: Optional[str] = None

class SkillCategory(BaseModel):
    category_name: str
    skills: List[str]

class CandidateProfile(BaseModel):
    contact: ContactInfo
    target_role: str
    professional_summary: str
    skills_categorized: List[SkillCategory] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)

class JobDescriptionAnalysis(BaseModel):
    job_title: str
    company_name: Optional[str] = "Target Company"
    required_hard_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    key_responsibilities: List[str] = Field(default_factory=list)
    domain_keywords: List[str] = Field(default_factory=list)
    minimum_years_experience: Optional[int] = 1

class AtsScoreReport(BaseModel):
    overall_match_score: int
    keyword_match_score: int
    semantic_match_score: int
    matched_keywords: List[str] = Field(default_factory=list)
    missing_critical_keywords: List[str] = Field(default_factory=list)
    recommended_improvements: List[str] = Field(default_factory=list)

class TailoredResume(BaseModel):
    candidate_profile: CandidateProfile
    tailored_summary: str
    tailored_experience: List[ExperienceItem]
    tailored_projects: List[ProjectItem]
    highlighted_skills: List[SkillCategory]
    ats_score_report: AtsScoreReport
