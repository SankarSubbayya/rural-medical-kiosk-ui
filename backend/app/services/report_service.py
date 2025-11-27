"""
Report Service - Generates SOAP reports for patients and physicians.

Produces two versions:
1. Patient Report: Simple language, voice-friendly
2. Physician Report: Formal medical format with ICD codes
"""
import uuid
from datetime import datetime
from typing import Optional
from io import BytesIO

from ..config import get_settings, ICD_CODES, LANGUAGE_NAMES
from ..models.soap import (
    SOAPConsultation, UrgencyLevel, PlanData, TransportationInfo
)


class ReportService:
    """
    Report generation service for SOAP consultations.

    Generates:
    - Patient-friendly summaries (for voice output)
    - Formal physician case reports
    - PDF documents for healthcare facilities
    """

    def __init__(self):
        self.settings = get_settings()

    async def generate_patient_report(
        self,
        consultation: SOAPConsultation
    ) -> str:
        """
        Generate a simple, patient-friendly report.

        This will be read aloud to the patient in their language.
        Uses simple vocabulary and clear instructions.
        """
        subj = consultation.subjective
        assess = consultation.assessment
        plan = consultation.plan

        # Build simple summary
        sections = []

        # What we found
        sections.append("Here is what we found:")
        if subj.chief_complaint:
            sections.append(f"You came in because of {subj.chief_complaint}.")

        # What it might be
        if assess.possible_conditions:
            top_condition = assess.possible_conditions[0]
            sections.append(
                f"Based on what you told me and the picture, this looks like it could be {top_condition.condition}. "
                "This is not a final answer - only a doctor can confirm this."
            )

        # How urgent
        urgency_messages = {
            UrgencyLevel.EMERGENCY: "This needs immediate attention. Please go to the hospital right away.",
            UrgencyLevel.URGENT: "You should see a doctor within the next day or two.",
            UrgencyLevel.ROUTINE: "You can schedule an appointment with a doctor when convenient.",
            UrgencyLevel.SELF_CARE: "This looks like something you can manage at home for now."
        }
        sections.append(urgency_messages.get(
            assess.urgency_level,
            "Please see a doctor for proper evaluation."
        ))

        # What to do next
        sections.append("\nWhat to do next:")
        if plan.patient_next_steps:
            for i, step in enumerate(plan.patient_next_steps, 1):
                sections.append(f"{i}. {step}")
        else:
            sections.append("1. Visit your nearest health center")
            sections.append("2. Show them this report")
            sections.append("3. Follow their advice")

        # Self-care tips
        if plan.self_care_instructions:
            sections.append("\nIn the meantime, you can:")
            for instruction in plan.self_care_instructions:
                sections.append(f"- {instruction}")

        # Transportation info
        if plan.transportation:
            trans = plan.transportation
            sections.append("\nHow to get there:")
            if trans.nearest_facility:
                sections.append(f"Nearest facility: {trans.nearest_facility}")
            if trans.directions:
                sections.append(f"Directions: {trans.directions}")

        # Reminder
        sections.append(
            "\nRemember: I am not a doctor. This information is to help you, "
            "but please get checked by a real doctor."
        )

        return "\n".join(sections)

    async def generate_physician_report(
        self,
        consultation: SOAPConsultation
    ) -> str:
        """
        Generate a formal medical report for healthcare providers.

        Follows standard SOAP format with ICD-10 codes.
        """
        report_id = consultation.id[:8].upper()
        timestamp = consultation.created_at.strftime("%Y-%m-%d %H:%M UTC")

        sections = []

        # Header
        sections.append("=" * 60)
        sections.append("DERMATOLOGY CONSULTATION REFERRAL")
        sections.append("=" * 60)
        sections.append(f"Case ID: {report_id}")
        sections.append(f"Date: {timestamp}")
        sections.append(f"Patient ID: {consultation.patient_id}")
        if consultation.kiosk_id:
            sections.append(f"Kiosk Location: {consultation.kiosk_id}")
        sections.append(f"Language: {LANGUAGE_NAMES.get(consultation.language, consultation.language)}")
        sections.append("")

        # Subjective
        sections.append("-" * 40)
        sections.append("SUBJECTIVE")
        sections.append("-" * 40)
        subj = consultation.subjective
        sections.append(f"Chief Complaint: {subj.chief_complaint or 'Not specified'}")

        if subj.symptoms:
            sections.append("\nSymptoms:")
            for symptom in subj.symptoms:
                line = f"  - {symptom.name}"
                if symptom.duration:
                    line += f" (Duration: {symptom.duration})"
                if symptom.severity:
                    line += f" [Severity: {symptom.severity}]"
                if symptom.location:
                    line += f" @ {symptom.location}"
                sections.append(line)

        if subj.onset:
            sections.append(f"\nOnset: {subj.onset}")
        if subj.duration:
            sections.append(f"Duration: {subj.duration}")

        if subj.aggravating_factors:
            sections.append(f"Aggravating Factors: {', '.join(subj.aggravating_factors)}")
        if subj.relieving_factors:
            sections.append(f"Relieving Factors: {', '.join(subj.relieving_factors)}")

        if subj.previous_treatments:
            sections.append(f"Previous Treatments: {', '.join(subj.previous_treatments)}")

        if subj.medical_history:
            sections.append(f"Medical History: {subj.medical_history}")
        if subj.allergies:
            sections.append(f"Allergies: {', '.join(subj.allergies)}")

        sections.append("")

        # Objective
        sections.append("-" * 40)
        sections.append("OBJECTIVE")
        sections.append("-" * 40)
        obj = consultation.objective

        if obj.primary_body_location:
            sections.append(f"Location: {obj.primary_body_location}")

        if obj.images:
            sections.append(f"\nImages Captured: {len(obj.images)}")
            for img in obj.images:
                sections.append(f"  - {img.body_location} (captured {img.timestamp.strftime('%H:%M')})")
                if img.image_url:
                    sections.append(f"    URL: {img.image_url}")

        if obj.visual_observations:
            sections.append("\nVisual Observations:")
            for obs in obj.visual_observations:
                sections.append(f"  - {obs}")

        if obj.lesion_characteristics:
            sections.append("\nLesion Characteristics:")
            for key, value in obj.lesion_characteristics.items():
                if value:
                    sections.append(f"  - {key.title()}: {value}")

        if obj.distribution_pattern:
            sections.append(f"Distribution: {obj.distribution_pattern}")

        sections.append("")

        # Assessment
        sections.append("-" * 40)
        sections.append("ASSESSMENT")
        sections.append("-" * 40)
        assess = consultation.assessment

        if assess.possible_conditions:
            sections.append("Differential Diagnosis:")
            for i, condition in enumerate(assess.possible_conditions, 1):
                critical_flag = " [CRITICAL]" if condition.is_critical else ""
                sections.append(
                    f"  {i}. {condition.condition}{critical_flag}"
                )
                sections.append(f"     ICD-10: {condition.icd_code}")
                sections.append(f"     Confidence: {condition.confidence * 100:.0f}%")

                if condition.supporting_evidence:
                    sections.append(f"     Supporting: {', '.join(condition.supporting_evidence)}")
                if condition.contraindications:
                    sections.append(f"     Against: {', '.join(condition.contraindications)}")
                sections.append("")

        sections.append(f"Urgency Level: {assess.urgency_level.value.upper()}")
        if assess.urgency_reasoning:
            sections.append(f"Urgency Rationale: {assess.urgency_reasoning}")

        if assess.rag_sources:
            sections.append("\nReference Cases (from database):")
            for source in assess.rag_sources[:3]:
                sections.append(f"  - {source.condition} (similarity: {source.similarity_score:.2f})")

        sections.append(f"\nOverall Confidence: {assess.confidence_overall * 100:.0f}%")
        sections.append(f"Professional Consultation Required: {'Yes' if assess.requires_professional else 'No'}")

        sections.append("")

        # Plan
        sections.append("-" * 40)
        sections.append("PLAN")
        sections.append("-" * 40)
        plan = consultation.plan

        if plan.recommended_tests:
            sections.append("Recommended Tests:")
            for test in plan.recommended_tests:
                sections.append(f"  - {test}")

        if plan.recommended_referrals:
            sections.append("Recommended Referrals:")
            for referral in plan.recommended_referrals:
                sections.append(f"  - {referral}")

        if plan.follow_up:
            sections.append(f"\nFollow-up: {plan.follow_up}")

        sections.append("")

        # Footer
        sections.append("=" * 60)
        sections.append("DISCLAIMER")
        sections.append("=" * 60)
        sections.append(assess.disclaimer)
        sections.append("")
        sections.append(f"Generated by: Agentic Health Kiosk")
        sections.append(f"Case ID: {consultation.id}")
        sections.append(f"Report Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

        return "\n".join(sections)

    async def generate_pdf_report(
        self,
        consultation: SOAPConsultation
    ) -> bytes:
        """
        Generate a PDF version of the physician report.

        Returns PDF as bytes.
        """
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.units import inch

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []

            # Title
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=20,
                alignment=1  # Center
            )
            elements.append(Paragraph("DERMATOLOGY CONSULTATION REFERRAL", title_style))
            elements.append(Spacer(1, 12))

            # Case info table
            case_data = [
                ["Case ID:", consultation.id[:8].upper()],
                ["Date:", consultation.created_at.strftime("%Y-%m-%d %H:%M")],
                ["Patient ID:", consultation.patient_id],
            ]
            case_table = Table(case_data, colWidths=[1.5*inch, 4*inch])
            case_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ]))
            elements.append(case_table)
            elements.append(Spacer(1, 20))

            # Sections
            section_style = ParagraphStyle(
                'Section',
                parent=styles['Heading2'],
                fontSize=14,
                spaceBefore=12,
                spaceAfter=6,
                textColor=colors.darkblue
            )

            # SUBJECTIVE
            elements.append(Paragraph("SUBJECTIVE", section_style))
            subj = consultation.subjective
            elements.append(Paragraph(
                f"<b>Chief Complaint:</b> {subj.chief_complaint or 'Not specified'}",
                styles['Normal']
            ))

            if subj.symptoms:
                symptoms_text = ", ".join([s.name for s in subj.symptoms])
                elements.append(Paragraph(f"<b>Symptoms:</b> {symptoms_text}", styles['Normal']))

            elements.append(Spacer(1, 12))

            # OBJECTIVE
            elements.append(Paragraph("OBJECTIVE", section_style))
            obj = consultation.objective
            if obj.primary_body_location:
                elements.append(Paragraph(f"<b>Location:</b> {obj.primary_body_location}", styles['Normal']))
            elements.append(Paragraph(f"<b>Images:</b> {len(obj.images)} captured", styles['Normal']))
            elements.append(Spacer(1, 12))

            # ASSESSMENT
            elements.append(Paragraph("ASSESSMENT", section_style))
            assess = consultation.assessment

            if assess.possible_conditions:
                for i, cond in enumerate(assess.possible_conditions[:3], 1):
                    critical = " (CRITICAL)" if cond.is_critical else ""
                    elements.append(Paragraph(
                        f"<b>{i}. {cond.condition}{critical}</b> - ICD-10: {cond.icd_code} - Confidence: {cond.confidence*100:.0f}%",
                        styles['Normal']
                    ))

            elements.append(Paragraph(
                f"<b>Urgency:</b> {assess.urgency_level.value.upper()}",
                styles['Normal']
            ))
            elements.append(Spacer(1, 12))

            # PLAN
            elements.append(Paragraph("PLAN", section_style))
            plan = consultation.plan
            if plan.recommended_tests:
                elements.append(Paragraph(
                    f"<b>Tests:</b> {', '.join(plan.recommended_tests)}",
                    styles['Normal']
                ))
            if plan.recommended_referrals:
                elements.append(Paragraph(
                    f"<b>Referrals:</b> {', '.join(plan.recommended_referrals)}",
                    styles['Normal']
                ))

            elements.append(Spacer(1, 30))

            # Disclaimer
            disclaimer_style = ParagraphStyle(
                'Disclaimer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.gray
            )
            elements.append(Paragraph(assess.disclaimer, disclaimer_style))

            # Build PDF
            doc.build(elements)
            return buffer.getvalue()

        except ImportError:
            # If reportlab not installed, return text report
            text_report = await self.generate_physician_report(consultation)
            return text_report.encode('utf-8')

    async def generate_plan_data(
        self,
        consultation: SOAPConsultation,
        language: str = "en"
    ) -> PlanData:
        """
        Generate plan data based on assessment results.

        Creates both patient-friendly and physician-facing guidance.
        """
        assess = consultation.assessment
        urgency = assess.urgency_level

        # Patient guidance based on urgency
        patient_guidance = self._get_urgency_guidance(urgency, language)

        # Generate next steps
        next_steps = self._generate_next_steps(consultation)

        # Self-care instructions (only for non-critical conditions)
        self_care = []
        if urgency in [UrgencyLevel.ROUTINE, UrgencyLevel.SELF_CARE]:
            self_care = self._generate_self_care(consultation)

        # Physician summary
        physician_summary = self._generate_physician_summary(consultation)

        # Recommended tests based on top conditions
        tests = self._recommend_tests(assess.possible_conditions)

        # Referrals
        referrals = self._recommend_referrals(assess.possible_conditions)

        return PlanData(
            patient_guidance=patient_guidance,
            patient_next_steps=next_steps,
            self_care_instructions=self_care,
            physician_summary=physician_summary,
            recommended_tests=tests,
            recommended_referrals=referrals,
            follow_up=self._get_follow_up_recommendation(urgency),
            what_to_expect="The doctor will examine the affected area and may take additional tests to confirm the condition."
        )

    def _get_urgency_guidance(self, urgency: UrgencyLevel, language: str) -> str:
        """Get urgency-specific guidance."""
        guidance = {
            UrgencyLevel.EMERGENCY: "This requires immediate medical attention. Please go to the nearest hospital or emergency room right away. Do not delay.",
            UrgencyLevel.URGENT: "Please see a doctor within the next 24-48 hours. This condition needs professional attention soon.",
            UrgencyLevel.ROUTINE: "You should schedule an appointment with a doctor when convenient. This doesn't appear to be urgent, but professional evaluation is recommended.",
            UrgencyLevel.SELF_CARE: "This appears to be something you can manage at home. However, if symptoms worsen or don't improve in a week, please see a doctor."
        }
        return guidance.get(urgency, guidance[UrgencyLevel.ROUTINE])

    def _generate_next_steps(self, consultation: SOAPConsultation) -> list:
        """Generate list of next steps for the patient."""
        steps = []
        urgency = consultation.assessment.urgency_level

        if urgency == UrgencyLevel.EMERGENCY:
            steps.extend([
                "Go to the nearest hospital emergency room immediately",
                "Bring this case report with you",
                "Tell them about your symptoms and show them the affected area"
            ])
        elif urgency == UrgencyLevel.URGENT:
            steps.extend([
                "Visit your nearest health center within 24-48 hours",
                "Bring this case report with you",
                "Describe all your symptoms to the doctor"
            ])
        else:
            steps.extend([
                "Schedule an appointment with a dermatologist or general physician",
                "Bring this case report to your appointment",
                "Note any changes in your condition before the visit"
            ])

        return steps

    def _generate_self_care(self, consultation: SOAPConsultation) -> list:
        """Generate self-care instructions."""
        instructions = [
            "Keep the affected area clean and dry",
            "Avoid scratching or picking at the area",
            "Wear loose, comfortable clothing over the affected area"
        ]

        # Add condition-specific tips if we can identify the condition
        if consultation.assessment.possible_conditions:
            top = consultation.assessment.possible_conditions[0].condition.lower()

            if "acne" in top:
                instructions.extend([
                    "Wash the area gently with mild soap twice daily",
                    "Avoid oily products on the skin"
                ])
            elif "fungal" in top or "tinea" in top:
                instructions.extend([
                    "Keep the area dry and well-ventilated",
                    "Do not share towels or clothing"
                ])
            elif "eczema" in top or "dermatitis" in top:
                instructions.extend([
                    "Apply unscented moisturizer regularly",
                    "Avoid hot water - use lukewarm water for washing"
                ])

        return instructions

    def _generate_physician_summary(self, consultation: SOAPConsultation) -> str:
        """Generate concise physician summary."""
        subj = consultation.subjective
        assess = consultation.assessment

        summary_parts = []

        # Chief complaint and duration
        if subj.chief_complaint:
            summary_parts.append(f"Patient presents with {subj.chief_complaint}")
            if subj.duration:
                summary_parts.append(f"for {subj.duration}")

        # Top differential
        if assess.possible_conditions:
            top = assess.possible_conditions[0]
            summary_parts.append(
                f"AI assessment suggests {top.condition} ({top.icd_code}) "
                f"with {top.confidence*100:.0f}% confidence"
            )

        # Urgency
        summary_parts.append(f"Urgency: {assess.urgency_level.value}")

        return ". ".join(summary_parts) + "."

    def _recommend_tests(self, conditions) -> list:
        """Recommend diagnostic tests based on conditions."""
        tests = []

        if not conditions:
            return ["Visual examination", "Medical history review"]

        for cond in conditions[:2]:
            condition_lower = cond.condition.lower()

            if "melanoma" in condition_lower or "carcinoma" in condition_lower:
                tests.extend(["Skin biopsy", "Dermoscopy examination"])
            elif "fungal" in condition_lower or "tinea" in condition_lower:
                tests.extend(["KOH preparation", "Fungal culture"])
            elif "bacterial" in condition_lower or "impetigo" in condition_lower:
                tests.append("Bacterial culture and sensitivity")
            elif "herpes" in condition_lower:
                tests.append("Viral culture or PCR")
            elif "scabies" in condition_lower:
                tests.append("Skin scraping microscopy")

        # Remove duplicates while preserving order
        seen = set()
        unique_tests = []
        for test in tests:
            if test not in seen:
                seen.add(test)
                unique_tests.append(test)

        return unique_tests if unique_tests else ["Clinical examination"]

    def _recommend_referrals(self, conditions) -> list:
        """Recommend specialist referrals."""
        referrals = []

        if not conditions:
            return ["Dermatology consultation"]

        for cond in conditions[:2]:
            if cond.is_critical:
                referrals.append("Urgent dermatology referral")
            if "melanoma" in cond.condition.lower() or "carcinoma" in cond.condition.lower():
                referrals.append("Oncology consultation")

        return list(set(referrals)) if referrals else []

    def _get_follow_up_recommendation(self, urgency: UrgencyLevel) -> str:
        """Get follow-up recommendation based on urgency."""
        recommendations = {
            UrgencyLevel.EMERGENCY: "Immediate follow-up with specialist after emergency visit",
            UrgencyLevel.URGENT: "Follow up within one week of initial visit",
            UrgencyLevel.ROUTINE: "Follow up as recommended by physician",
            UrgencyLevel.SELF_CARE: "Seek care if condition worsens or persists beyond one week"
        }
        return recommendations.get(urgency, recommendations[UrgencyLevel.ROUTINE])
