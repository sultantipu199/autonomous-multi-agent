"""Critic Agent: Adversarial self-reflection checking for fluff, tone, and technical depth.

Scrutinizes generated carousel content against production standards before human review.
"""

from typing import List
from state import CarouselContent, CritiqueResult


class ContentCritic:
    """Evaluates technical depth, fluff ratio, and actionable value of carousel content."""

    def evaluate(self, carousel: CarouselContent) -> CritiqueResult:
        """Runs rule-based and heuristics-based adversarial evaluation."""
        deductions = []
        tech_score = 10.0
        hook_score = 10.0
        fluff_score = 10.0

        # Check Slide 1: Hook and Badge
        slide_1 = carousel.slides[0]
        if "Marketer → GenAI Engineer" not in slide_1.badge:
            deductions.append("Slide 1 is missing the required brand badge 'Marketer → GenAI Engineer'")
            hook_score -= 2.0
        if len(slide_1.title) < 15:
            deductions.append("Slide 1 title is too brief to be a high-converting hook")
            hook_score -= 1.5

        # Check Slide 2: Core Engineering Problem
        slide_2 = carousel.slides[1]
        if len(slide_2.body_bullets) < 2:
            deductions.append("Slide 2 must contain at least 2 distinct technical problem statements")
            fluff_score -= 1.5

        # Check Slide 3: Code Snippet / Architecture
        slide_3 = carousel.slides[2]
        if not slide_3.code_snippet or len(slide_3.code_snippet.strip()) < 20:
            deductions.append("Slide 3 lacks a concrete, technical code snippet or architecture definition")
            tech_score -= 3.5
        elif "def " not in slide_3.code_snippet and "import " not in slide_3.code_snippet and "{" not in slide_3.code_snippet:
            deductions.append("Slide 3 code snippet looks generic rather than executable code")
            tech_score -= 1.5

        # Check Slide 4: Measurable ROI & Metrics
        slide_4 = carousel.slides[3]
        if not slide_4.metrics or len(slide_4.metrics) < 2:
            deductions.append("Slide 4 lacks quantifiable business & engineering ROI metrics")
            tech_score -= 2.0

        # Check Slide 5: Checklist & CTA
        slide_5 = carousel.slides[4]
        if not slide_5.cta_text:
            deductions.append("Slide 5 is missing a save/swipe CTA")
            hook_score -= 1.0

        # Check First Comment
        if not carousel.first_comment or len(carousel.first_comment) < 30:
            deductions.append("First comment is missing or too brief to drive discussion")
            hook_score -= 1.5

        # Buzzword / Fluff Check
        banned_fluff = ["game-changing", "revolutionary", "paradigm shift", "skyrocket", "magic"]
        found_fluff = [w for w in banned_fluff if w in carousel.post_caption.lower()]
        if found_fluff:
            deductions.append(f"Post caption contains marketing fluff buzzwords: {', '.join(found_fluff)}")
            fluff_score -= 1.5 * len(found_fluff)

        # Calculate final composite score
        final_score = round(
            max(1.0, min(10.0, (tech_score * 0.45) + (hook_score * 0.30) + (fluff_score * 0.25))),
            1
        )
        passed = final_score >= 8.0

        feedback = "Adversarial check PASSED: Content meets high technical depth and retention requirements." if passed else \
                   f"Adversarial check FAILED (Score: {final_score}/10): Refinements required."

        return CritiqueResult(
            score=final_score,
            passed=passed,
            technical_depth_score=tech_score,
            hook_clarity_score=hook_score,
            fluff_ratio_score=fluff_score,
            feedback=feedback,
            actionable_revisions=deductions
        )
