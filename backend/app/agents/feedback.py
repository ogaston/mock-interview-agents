"""
Feedback Agent - Generates personalized feedback and recommendations using LLM.
"""
from app.config import settings
from app.models.schemas import InterviewState, InterviewFeedback, FeedbackItem, AnswerEvaluation


class FeedbackAgent:
    """Agent responsible for generating personalized feedback."""

    def __init__(self):
        """Initialize the feedback agent with LLM."""
        self.llm = self._initialize_llm()

    def _initialize_llm(self):
        """Initialize the appropriate LLM based on configuration."""
        config = settings.get_llm_config()

        if config["provider"] == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=config["model"],
                api_key=config["api_key"],
                temperature=0.7
            )
        elif config["provider"] == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=config["model"],
                api_key=config["api_key"],
                temperature=0.7
            )
        elif config["provider"] == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=config["model"],
                google_api_key=config["api_key"],
                temperature=0.7
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {config['provider']}")

    def generate_feedback(self, state: InterviewState) -> InterviewFeedback:
        """
        Generate comprehensive feedback for the entire interview.

        Args:
            state: Complete interview state with all Q&A and evaluations

        Returns:
            InterviewFeedback with detailed analysis and recommendations
        """
        # Calculate overall statistics
        overall_score = self._calculate_overall_score(state.evaluations)

        # Build context for LLM
        prompt = self._build_feedback_prompt(state, overall_score)

        # Get LLM feedback
        response = self.llm.invoke(prompt)
        llm_feedback = response.content.strip()

        # Parse LLM response into structured feedback
        feedback = self._parse_llm_feedback(llm_feedback, overall_score, state)

        return feedback

    def _calculate_overall_score(self, evaluations: list[AnswerEvaluation]) -> float:
        """Calculate average overall score across all evaluations."""
        if not evaluations:
            return 0.0

        total_score = sum(eval.scores.overall_score for eval in evaluations)
        return round(total_score / len(evaluations), 2)

    def _build_feedback_prompt(self, state: InterviewState, overall_score: float) -> str:
        """Build comprehensive prompt for generating feedback."""

        # Build detailed Q&A history with scores
        qa_history = ""
        for i, (question, answer, evaluation) in enumerate(
            zip(state.questions, state.answers, state.evaluations), 1
        ):
            qa_history += f"""
Question {i} ({question.category}): {question.question_text}

Answer: {answer}

Evaluation Scores:
- Clarity: {evaluation.scores.clarity}/10
- Confidence: {evaluation.scores.confidence}/10
- Relevance: {evaluation.scores.relevance}/10
- Overall: {evaluation.scores.overall_score}/10

NLP Analysis: {evaluation.nlp_features.get('summary', {})}
---
"""

        prompt = f"""You are an expert interview coach providing comprehensive feedback on a mock interview.

Interview Details:
- Role: {state.role}
- Seniority Level: {state.seniority}
- Total Questions: {len(state.questions)}
- Overall Score: {overall_score}/10

Complete Interview Transcript with Evaluations:
{qa_history}

Based on this interview performance, provide detailed, actionable feedback in the following format:

## OVERALL SUMMARY
[2-3 sentences summarizing the candidate's overall performance]

## STRENGTHS
- [Specific strength 1]
- [Specific strength 2]
- [Specific strength 3]

## AREAS FOR IMPROVEMENT
- [Specific area 1]
- [Specific area 2]
- [Specific area 3]

## DETAILED FEEDBACK

### Communication Skills
Strength: [What they did well]
Weakness: [What needs improvement]
Suggestions:
- [Specific actionable suggestion 1]
- [Specific actionable suggestion 2]

### Technical Knowledge
Strength: [What they did well]
Weakness: [What needs improvement]
Suggestions:
- [Specific actionable suggestion 1]
- [Specific actionable suggestion 2]

### Problem-Solving Approach
Strength: [What they did well]
Weakness: [What needs improvement]
Suggestions:
- [Specific actionable suggestion 1]
- [Specific actionable suggestion 2]

## RECOMMENDED RESOURCES
- [Resource 1: Book/Course/Article with brief description]
- [Resource 2: Practice platform or tool]
- [Resource 3: Specific topic to study]
- [Resource 4: Community or forum to join]

Keep feedback constructive, specific, and actionable. Focus on concrete examples from their answers."""

        return prompt

    def _parse_llm_feedback(
        self,
        llm_response: str,
        overall_score: float,
        state: InterviewState
    ) -> InterviewFeedback:
        """
        Parse LLM-generated feedback into structured format.

        Args:
            llm_response: Raw LLM response
            overall_score: Calculated overall score
            state: Interview state

        Returns:
            Structured InterviewFeedback
        """
        lines = llm_response.split('\n')

        # Extract sections
        summary = self._extract_section(lines, "OVERALL SUMMARY")
        strengths = self._extract_list_items(lines, "STRENGTHS")
        improvements = self._extract_list_items(lines, "AREAS FOR IMPROVEMENT")
        resources = self._extract_list_items(lines, "RECOMMENDED RESOURCES")

        # Extract detailed feedback items
        feedback_items = []

        # Communication Skills
        comm_feedback = self._extract_detailed_feedback(lines, "Communication Skills")
        if comm_feedback:
            feedback_items.append(comm_feedback)

        # Technical Knowledge
        tech_feedback = self._extract_detailed_feedback(lines, "Technical Knowledge")
        if tech_feedback:
            feedback_items.append(tech_feedback)

        # Problem-Solving
        ps_feedback = self._extract_detailed_feedback(lines, "Problem-Solving Approach")
        if ps_feedback:
            feedback_items.append(ps_feedback)

        return InterviewFeedback(
            overall_score=overall_score,
            overall_summary=summary or "Performance evaluation completed.",
            feedback_items=feedback_items,
            recommended_resources=resources,
            strengths=strengths,
            areas_for_improvement=improvements
        )

    def _extract_section(self, lines: list[str], header: str) -> str:
        """Extract a text section following a header."""
        try:
            start_idx = next(i for i, line in enumerate(lines) if header in line.upper())
            content_lines = []

            for i in range(start_idx + 1, len(lines)):
                line = lines[i].strip()
                if line.startswith('##') or not line:
                    if content_lines:
                        break
                    continue
                content_lines.append(line)

            return ' '.join(content_lines)
        except (StopIteration, IndexError):
            return ""

    def _extract_list_items(self, lines: list[str], header: str) -> list[str]:
        """Extract bullet point items following a header."""
        try:
            start_idx = next(i for i, line in enumerate(lines) if header in line.upper())
            items = []

            for i in range(start_idx + 1, len(lines)):
                line = lines[i].strip()
                if line.startswith('##'):
                    break
                if line.startswith('-') or line.startswith('•'):
                    items.append(line.lstrip('-•').strip())

            return items
        except (StopIteration, IndexError):
            return []

    def _extract_detailed_feedback(self, lines: list[str], category: str) -> FeedbackItem | None:
        """Extract detailed feedback for a specific category."""
        try:
            start_idx = next(i for i, line in enumerate(lines) if category in line)

            strength = ""
            weakness = ""
            suggestions = []

            # Look for Strength, Weakness, and Suggestions
            for i in range(start_idx + 1, len(lines)):
                line = lines[i].strip()

                if line.startswith('###') or line.startswith('##'):
                    break

                if line.startswith('Strength:'):
                    strength = line.replace('Strength:', '').strip()
                elif line.startswith('Weakness:'):
                    weakness = line.replace('Weakness:', '').strip()
                elif line.startswith('Suggestions:'):
                    # Collect suggestions
                    for j in range(i + 1, len(lines)):
                        suggestion_line = lines[j].strip()
                        if suggestion_line.startswith('###') or suggestion_line.startswith('##'):
                            break
                        if suggestion_line.startswith('-') or suggestion_line.startswith('•'):
                            suggestions.append(suggestion_line.lstrip('-•').strip())
                    break

            if strength or weakness or suggestions:
                return FeedbackItem(
                    category=category,
                    strength=strength or None,
                    weakness=weakness or None,
                    suggestions=suggestions
                )

            return None
        except (StopIteration, IndexError):
            return None


# Singleton instance
feedback_agent = FeedbackAgent()
