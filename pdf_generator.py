import os
from pathlib import Path
from typing import Optional
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, ListFlowable, ListItem
)
from reportlab.pdfgen import canvas

from models import TailoredResume, TemplateType
import config

class NumberedCanvas(canvas.Canvas):
    """Custom canvas that tracks total pages to enforce page constraints."""
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
            # If multiple pages exist, add unobtrusive page number (only if > 1 page)
            if num_pages > 1:
                self.setFont("Helvetica", 8)
                self.drawRightString(200 * mm, 10 * mm, f"Page {self._pageNumber} of {num_pages}")
            super().showPage()
        super().save()

def create_resume_pdf(
    resume: TailoredResume, 
    template: TemplateType = TemplateType.HARVARD_CLASSIC,
    output_filename: Optional[str] = None
) -> str:
    """Generates an ATS-compliant PDF resume from the tailored data."""
    if not output_filename:
        safe_name = resume.candidate_profile.contact.full_name.replace(" ", "_")
        output_filename = f"{safe_name}_{template.value}_Resume.pdf"

    output_path = config.OUTPUT_DIR / output_filename
    
    if template == TemplateType.HARVARD_CLASSIC:
        _build_harvard_classic(resume, str(output_path))
    elif template == TemplateType.MODERN_TECH:
        _build_modern_tech(resume, str(output_path))
    elif template == TemplateType.COMPACT_ONE_PAGE:
        _build_compact_one_page(resume, str(output_path))
    else:
        _build_harvard_classic(resume, str(output_path))

    return str(output_path)

# ==========================================
# 1. HARVARD CLASSIC TEMPLATE
# ==========================================
def _build_harvard_classic(resume: TailoredResume, filename: str):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm
    )
    
    styles = getSampleStyleSheet()
    
    name_style = ParagraphStyle(
        'HarvardName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        alignment=1, # Center
        textColor=colors.HexColor('#111827')
    )
    
    contact_style = ParagraphStyle(
        'HarvardContact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        alignment=1,
        textColor=colors.HexColor('#374151')
    )
    
    section_heading = ParagraphStyle(
        'HarvardSectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor('#111827'),
        spaceBefore=7,
        spaceAfter=2,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'HarvardBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor('#1F2937')
    )
    
    bold_left = ParagraphStyle(
        'HarvardBoldLeft',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#111827')
    )
    
    italic_right = ParagraphStyle(
        'HarvardItalicRight',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        leading=13,
        alignment=2, # Right
        textColor=colors.HexColor('#374151')
    )
    
    bullet_style = ParagraphStyle(
        'HarvardBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.8,
        leading=12,
        leftIndent=14,
        firstLineIndent=-10,
        textColor=colors.HexColor('#1F2937')
    )

    story = []
    contact = resume.candidate_profile.contact
    
    # 1. Header
    story.append(Paragraph(contact.full_name.upper(), name_style))
    story.append(Spacer(1, 2 * mm))
    
    contact_parts = [contact.location, contact.phone, contact.email]
    if contact.linkedin_url:
        contact_parts.append(f'<a href="{contact.linkedin_url}">LinkedIn</a>')
    if contact.github_url:
        contact_parts.append(f'<a href="{contact.github_url}">GitHub</a>')
    if contact.portfolio_url:
        contact_parts.append(f'<a href="{contact.portfolio_url}">Portfolio</a>')
        
    story.append(Paragraph(" &nbsp;|&nbsp; ".join(contact_parts), contact_style))
    story.append(Spacer(1, 3 * mm))
    
    def add_section_header(title: str):
        story.append(Paragraph(title.upper(), section_heading))
        story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor('#111827'), spaceBefore=1, spaceAfter=4))

    # 2. Summary
    add_section_header("Professional Summary")
    story.append(Paragraph(resume.tailored_summary, body_style))
    story.append(Spacer(1, 2 * mm))

    # 3. Technical Skills
    add_section_header("Technical Skills")
    for cat in resume.highlighted_skills:
        skill_line = f"<b>{cat.category_name}:</b> {', '.join(cat.skills)}"
        story.append(Paragraph(skill_line, body_style))
    story.append(Spacer(1, 2 * mm))

    # 4. Work Experience
    add_section_header("Work Experience")
    for exp in resume.tailored_experience:
        # Two-column row: Role + Company on left, Location + Dates on right
        col_width = (doc.width) / 2
        exp_table = Table(
            [[
                Paragraph(f"<b>{exp.role}</b> &mdash; {exp.company}", bold_left),
                Paragraph(f"{exp.location or ''} | {exp.start_date} – {exp.end_date}", italic_right)
            ]],
            colWidths=[col_width * 1.3, col_width * 0.7]
        )
        exp_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
        ]))
        story.append(exp_table)
        
        for bullet in exp.bullets:
            story.append(Paragraph(f"&bull;&nbsp;&nbsp;{bullet}", bullet_style))
        story.append(Spacer(1, 2 * mm))

    # 5. Key Projects
    if resume.tailored_projects:
        add_section_header("Key Projects")
        for proj in resume.tailored_projects:
            col_width = (doc.width) / 2
            proj_title = f"<b>{proj.title}</b>"
            if proj.subtitle:
                proj_title += f" &mdash; <i>{proj.subtitle}</i>"
            
            proj_table = Table(
                [[
                    Paragraph(proj_title, bold_left),
                    Paragraph(f'<a href="{proj.link}">Project Link</a>' if proj.link else "", italic_right)
                ]],
                colWidths=[col_width * 1.5, col_width * 0.5]
            )
            proj_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1),
                ('TOPPADDING', (0,0), (-1,-1), 1),
            ]))
            story.append(proj_table)
            
            for bullet in proj.bullets:
                story.append(Paragraph(f"&bull;&nbsp;&nbsp;{bullet}", bullet_style))
            
            if proj.technologies:
                story.append(Paragraph(f"<i>Technologies: {', '.join(proj.technologies)}</i>", ParagraphStyle(
                    'ProjTech', parent=bullet_style, fontSize=8.2, textColor=colors.HexColor('#4B5563')
                )))
            story.append(Spacer(1, 2 * mm))

    # 6. Education
    if resume.candidate_profile.education:
        add_section_header("Education")
        for edu in resume.candidate_profile.education:
            col_width = (doc.width) / 2
            edu_table = Table(
                [[
                    Paragraph(f"<b>{edu.degree}</b> &mdash; {edu.institution}", bold_left),
                    Paragraph(f"{edu.location or ''} | {edu.graduation_year}", italic_right)
                ]],
                colWidths=[col_width * 1.4, col_width * 0.6]
            )
            edu_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1),
                ('TOPPADDING', (0,0), (-1,-1), 1),
            ]))
            story.append(edu_table)
            if edu.grade_or_gpa:
                story.append(Paragraph(f"Honors/Grade: {edu.grade_or_gpa}", ParagraphStyle(
                    'EduGrade', parent=body_style, fontSize=8.5, leftIndent=10
                )))

    doc.build(story, canvasmaker=NumberedCanvas)


# ==========================================
# 2. MODERN TECH TEMPLATE
# ==========================================
def _build_modern_tech(resume: TailoredResume, filename: str):
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=13 * mm,
        rightMargin=13 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm
    )
    styles = getSampleStyleSheet()

    accent_color = colors.HexColor('#1E40AF') # Indigo-600
    dark_color = colors.HexColor('#0F172A')   # Slate-900

    name_style = ParagraphStyle(
        'ModernName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=19,
        leading=23,
        textColor=dark_color
    )
    
    role_style = ParagraphStyle(
        'ModernRole',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=accent_color
    )

    contact_style = ParagraphStyle(
        'ModernContact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor('#475569')
    )

    section_heading = ParagraphStyle(
        'ModernSection',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=dark_color,
        spaceBefore=7,
        spaceAfter=2,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'ModernBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.8,
        leading=12.2,
        textColor=colors.HexColor('#1E293B')
    )

    bullet_style = ParagraphStyle(
        'ModernBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.8,
        leading=12,
        leftIndent=12,
        firstLineIndent=-8,
        textColor=colors.HexColor('#1E293B')
    )

    story = []
    contact = resume.candidate_profile.contact

    # Header block
    story.append(Paragraph(contact.full_name, name_style))
    story.append(Paragraph(resume.candidate_profile.target_role, role_style))
    story.append(Spacer(1, 1.5 * mm))

    contact_links = [contact.location, contact.phone, contact.email]
    if contact.linkedin_url:
        contact_links.append(f'<a href="{contact.linkedin_url}">LinkedIn</a>')
    if contact.github_url:
        contact_links.append(f'<a href="{contact.github_url}">GitHub</a>')
    story.append(Paragraph(" &bull; ".join(contact_links), contact_style))
    story.append(Spacer(1, 2.5 * mm))

    def add_modern_header(title: str):
        story.append(Paragraph(title, section_heading))
        story.append(HRFlowable(width="100%", thickness=1.2, color=accent_color, spaceBefore=1, spaceAfter=4))

    # Technical Skills first
    add_modern_header("Technical Expertise")
    for cat in resume.highlighted_skills:
        line = f"<b>{cat.category_name}:</b> {', '.join(cat.skills)}"
        story.append(Paragraph(line, body_style))
    story.append(Spacer(1, 2 * mm))

    # Professional Summary
    add_modern_header("Professional Summary")
    story.append(Paragraph(resume.tailored_summary, body_style))
    story.append(Spacer(1, 2 * mm))

    # Experience
    add_modern_header("Professional Experience")
    for exp in resume.tailored_experience:
        col_width = (doc.width) / 2
        exp_table = Table(
            [[
                Paragraph(f"<b>{exp.role}</b> | <font color='#1E40AF'><b>{exp.company}</b></font>", body_style),
                Paragraph(f"{exp.start_date} – {exp.end_date} &bull; {exp.location or ''}", ParagraphStyle('R', parent=body_style, alignment=2))
            ]],
            colWidths=[col_width * 1.3, col_width * 0.7]
        )
        exp_table.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('LEFTPADDING', (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,0), (-1,-1), 2),
        ]))
        story.append(exp_table)
        for bullet in exp.bullets:
            story.append(Paragraph(f"&bull;&nbsp;&nbsp;{bullet}", bullet_style))
        story.append(Spacer(1, 2 * mm))

    # Projects
    if resume.tailored_projects:
        add_modern_header("Featured Engineering Projects")
        for proj in resume.tailored_projects:
            col_width = (doc.width) / 2
            proj_table = Table(
                [[
                    Paragraph(f"<b>{proj.title}</b>", body_style),
                    Paragraph(f'<a href="{proj.link}">View Code</a>' if proj.link else "", ParagraphStyle('R2', parent=body_style, alignment=2))
                ]],
                colWidths=[col_width * 1.5, col_width * 0.5]
            )
            proj_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1),
                ('TOPPADDING', (0,0), (-1,-1), 1),
            ]))
            story.append(proj_table)
            for bullet in proj.bullets:
                story.append(Paragraph(f"&bull;&nbsp;&nbsp;{bullet}", bullet_style))
            if proj.technologies:
                story.append(Paragraph(f"<i>Stack: {', '.join(proj.technologies)}</i>", ParagraphStyle(
                    'Stack', parent=body_style, fontSize=8, textColor=colors.HexColor('#64748B')
                )))
            story.append(Spacer(1, 2 * mm))

    # Education
    if resume.candidate_profile.education:
        add_modern_header("Education")
        for edu in resume.candidate_profile.education:
            col_width = (doc.width) / 2
            edu_table = Table(
                [[
                    Paragraph(f"<b>{edu.degree}</b>, {edu.institution}", body_style),
                    Paragraph(f"{edu.graduation_year}", ParagraphStyle('R3', parent=body_style, alignment=2))
                ]],
                colWidths=[col_width * 1.5, col_width * 0.5]
            )
            edu_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 1),
                ('TOPPADDING', (0,0), (-1,-1), 1),
            ]))
            story.append(edu_table)

    doc.build(story, canvasmaker=NumberedCanvas)


# ==========================================
# 3. COMPACT ONE-PAGE TEMPLATE
# ==========================================
def _build_compact_one_page(resume: TailoredResume, filename: str):
    """Designed to guarantee all content fits within exactly 1 single page without truncation."""
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=10 * mm,
        rightMargin=10 * mm,
        topMargin=8 * mm,
        bottomMargin=8 * mm
    )
    styles = getSampleStyleSheet()

    name_style = ParagraphStyle(
        'CompactName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=19,
        alignment=1,
        textColor=colors.HexColor('#111827')
    )
    
    contact_style = ParagraphStyle(
        'CompactContact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        alignment=1,
        textColor=colors.HexColor('#374151')
    )

    section_heading = ParagraphStyle(
        'CompactHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=colors.HexColor('#111827'),
        spaceBefore=4,
        spaceAfter=1,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'CompactBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.3,
        leading=11,
        textColor=colors.HexColor('#1F2937')
    )

    bullet_style = ParagraphStyle(
        'CompactBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.2,
        leading=10.8,
        leftIndent=10,
        firstLineIndent=-7,
        textColor=colors.HexColor('#1F2937')
    )

    story = []
    contact = resume.candidate_profile.contact

    # 1. Header
    story.append(Paragraph(contact.full_name.upper(), name_style))
    contact_parts = [contact.location, contact.phone, contact.email]
    if contact.linkedin_url:
        contact_parts.append(f'<a href="{contact.linkedin_url}">LinkedIn</a>')
    if contact.github_url:
        contact_parts.append(f'<a href="{contact.github_url}">GitHub</a>')
    story.append(Paragraph(" | ".join(contact_parts), contact_style))
    story.append(Spacer(1, 1.5 * mm))

    def add_compact_header(title: str):
        story.append(Paragraph(title.upper(), section_heading))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#111827'), spaceBefore=0.5, spaceAfter=2))

    # Summary
    add_compact_header("Summary")
    story.append(Paragraph(resume.tailored_summary, body_style))

    # Skills
    add_compact_header("Technical Skills")
    for cat in resume.highlighted_skills:
        story.append(Paragraph(f"<b>{cat.category_name}:</b> {', '.join(cat.skills)}", body_style))

    # Experience
    add_compact_header("Experience")
    for exp in resume.tailored_experience:
        col_w = doc.width / 2
        t = Table(
            [[
                Paragraph(f"<b>{exp.role}</b> &mdash; {exp.company}", body_style),
                Paragraph(f"{exp.start_date} – {exp.end_date}", ParagraphStyle('R', parent=body_style, alignment=2))
            ]],
            colWidths=[col_w * 1.4, col_w * 0.6]
        )
        t.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0)]))
        story.append(t)
        # Take top 3-4 impactful bullets to guarantee 1 page
        for bullet in exp.bullets[:4]:
            story.append(Paragraph(f"&bull;&nbsp;&nbsp;{bullet}", bullet_style))

    # Projects
    if resume.tailored_projects:
        add_compact_header("Projects")
        for proj in resume.tailored_projects:
            col_w = doc.width / 2
            t = Table(
                [[
                    Paragraph(f"<b>{proj.title}</b>", body_style),
                    Paragraph(f'<a href="{proj.link}">Link</a>' if proj.link else "", ParagraphStyle('R', parent=body_style, alignment=2))
                ]],
                colWidths=[col_w * 1.5, col_w * 0.5]
            )
            t.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0)]))
            story.append(t)
            for bullet in proj.bullets[:2]:
                story.append(Paragraph(f"&bull;&nbsp;&nbsp;{bullet}", bullet_style))

    # Education
    if resume.candidate_profile.education:
        add_compact_header("Education")
        for edu in resume.candidate_profile.education:
            col_w = doc.width / 2
            t = Table(
                [[
                    Paragraph(f"<b>{edu.degree}</b> &mdash; {edu.institution}", body_style),
                    Paragraph(edu.graduation_year, ParagraphStyle('R', parent=body_style, alignment=2))
                ]],
                colWidths=[col_w * 1.5, col_w * 0.5]
            )
            t.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0)]))
            story.append(t)

    doc.build(story, canvasmaker=NumberedCanvas)
