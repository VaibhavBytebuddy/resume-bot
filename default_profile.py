from models import (
    CandidateProfile, ContactInfo, ExperienceItem, 
    ProjectItem, EducationItem, SkillCategory
)

VAIBHAV_PROFILE = CandidateProfile(
    contact=ContactInfo(
        full_name="Vaibhav Bhadane",
        email="vaibhav.bhadane@example.com",
        phone="+91-9876543210",
        location="Pune, India",
        linkedin_url="https://linkedin.com/in/vaibhav-bhadane",
        github_url="https://github.com/vaibhav-bhadane",
        portfolio_url="https://vaibhavbhadane.dev"
    ),
    target_role="Full-Stack & Backend Software Engineer",
    professional_summary=(
        "Software Engineer with ~1.5 years of experience architecting scalable backend microservices, "
        "event-driven pipelines with Apache Kafka, and production Generative AI integrations. "
        "Demonstrated expertise in Spring Boot (Java 17/21), MongoDB query optimization, and Angular/TypeScript. "
        "Proven track record of optimizing database aggregation latencies and delivering high-throughput production features."
    ),
    skills_categorized=[
        SkillCategory(
            category_name="Languages & Core",
            skills=["Java 17/21", "TypeScript", "JavaScript", "Python", "Dart", "SQL"]
        ),
        SkillCategory(
            category_name="Backend & Messaging",
            skills=["Spring Boot", "Apache Kafka", "Microservices", "RESTful APIs", "Node.js", "Spring Data MongoDB"]
        ),
        SkillCategory(
            category_name="Frontend & Mobile",
            skills=["Angular", "RxJS", "Tailwind CSS", "HTML5/CSS3", "Flutter"]
        ),
        SkillCategory(
            category_name="Databases & Cloud/DevOps",
            skills=["MongoDB Atlas", "Cloud Firestore", "Docker", "GCP (Pub/Sub, Cloud Storage)", "Git / GitLab CI"]
        ),
        SkillCategory(
            category_name="AI & Tools",
            skills=["Google Gemini GenAI SDK", "Structured Output Parsing", "Prompt Engineering", "Postman", "ReportLab"]
        )
    ],
    experience=[
        ExperienceItem(
            company="Talenlio",
            role="Software Engineer (Full-Stack / Backend)",
            location="Pune, India",
            start_date="06/2025",
            end_date="Present",
            bullets=[
                "Architected event-driven email recruitment ingestion pipeline using Apache Kafka consumer groups and Spring Boot, processing thousands of async messages with zero data loss.",
                "Integrated Google GenAI SDK (Gemini) with structured JSON schemas into Spring Boot microservices, automating candidate parsing and slashing manual screening time by 65%.",
                "Diagnosed and resolved critical MongoDB $facet 100MB memory limit crashes on 60,000+ document pipelines, optimizing query execution via compound B-Tree indexes and reducing p95 latency by 40%.",
                "Built and maintained core RESTful APIs for candidate management, coupon billing, and multi-tenant recruiter portals across distributed microservices.",
                "Engineered reactive Angular (RxJS) interfaces for HireOS and Standout portals, ensuring seamless state management and sub-second UI response times."
            ],
            technologies=["Java 21", "Spring Boot", "Apache Kafka", "MongoDB", "Google Gemini AI", "Angular", "RxJS", "Docker"]
        )
    ],
    projects=[
        ProjectItem(
            title="AI-Powered Resume ATS Optimization & Multi-Template Export",
            subtitle="Full-Stack Resume Engine",
            link="https://github.com/vaibhav-bhadane/resume-ats-engine",
            bullets=[
                "Designed end-to-end resume tailoring platform that parses Job Descriptions, identifies keyword gaps, and computes semantic vector similarity scores.",
                "Engineered automated PDF generation microservice producing 100% ATS-compliant single-column and multi-template vector documents with dynamic page-height constraints.",
                "Built interactive Telegram Bot interface enabling instant mobile JD matching, match analysis, and customized PDF delivery."
            ],
            technologies=["Python", "ReportLab", "Gemini 2.5 Flash", "Telegram Bot API", "SQLite"]
        ),
        ProjectItem(
            title="High-Throughput Candidate Assessment & Sandbox Evaluation",
            subtitle="Enterprise Microservice",
            link="https://github.com/vaibhav-bhadane/assessment-eval-service",
            bullets=[
                "Implemented Spring Boot backend services to orchestrate automated code challenge evaluations and scoring pipelines across 80+ test cases.",
                "Designed MongoDB schemas and caching layers for assessment status tracking, ensuring sub-100ms response times under concurrent test submissions."
            ],
            technologies=["Java 17", "Spring Boot", "MongoDB", "REST APIs", "JUnit"]
        )
    ],
    education=[
        EducationItem(
            degree="Bachelor of Engineering (Computer Engineering)",
            institution="Savitribai Phule Pune University",
            location="Pune, India",
            graduation_year="2025",
            grade_or_gpa="First Class with Distinction"
        )
    ],
    certifications=[
        "Google Cloud Fundamentals (Core Infrastructure)",
        "Spring Boot Microservices & Enterprise Architecture"
    ]
)
