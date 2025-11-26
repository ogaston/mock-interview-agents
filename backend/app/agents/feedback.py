"""
Feedback Agent - Generates personalized feedback and recommendations using LLM.
"""
from app.config import settings
from app.models.schemas import InterviewState, InterviewFeedback, FeedbackItem, AnswerEvaluation

from app.mocks.agents import MockFeedbackAgent
from app.prompts.feedback import get_feedback_prompt, get_qa_history_prompt

class FeedbackAgent:
    """Agent responsible for generating personalized feedback."""

    def __init__(self):
        """Initialize the feedback agent with LLM."""
        self.llm = self._initialize_llm()

    def _initialize_llm(self):
        """Initialize the appropriate LLM based on configuration."""
        config = settings.get_llm_config()

        if config["provider"] == "mock":
            mock_feedback_agent = MockFeedbackAgent()
            return mock_feedback_agent._initialize_llm()
            
        elif config["provider"] == "openai":
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
            qa_history += get_qa_history_prompt(question, answer, evaluation, i)
        return get_feedback_prompt(state, overall_score, qa_history)

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

        # Extract sections (support both Spanish and English headers)
        summary = self._extract_section(lines, "RESUMEN GENERAL") or self._extract_section(lines, "OVERALL SUMMARY")
        strengths = self._extract_list_items(lines, "FORTALEZAS") or self._extract_list_items(lines, "STRENGTHS")
        improvements = self._extract_list_items(lines, "ÁREAS DE MEJORA") or self._extract_list_items(lines, "AREAS FOR IMPROVEMENT")
        resources = self._extract_list_items(lines, "RECURSOS RECOMENDADOS") or self._extract_list_items(lines, "RECOMMENDED RESOURCES")

        # Extract detailed feedback items
        feedback_items = []

        # Communication Skills
        comm_feedback = (self._extract_detailed_feedback(lines, "Habilidades de Comunicación") or 
                         self._extract_detailed_feedback(lines, "Communication Skills"))
        if comm_feedback:
            feedback_items.append(comm_feedback)

        # Technical Knowledge
        tech_feedback = (self._extract_detailed_feedback(lines, "Conocimiento Técnico") or 
                         self._extract_detailed_feedback(lines, "Technical Knowledge"))
        if tech_feedback:
            feedback_items.append(tech_feedback)

        # Problem-Solving
        ps_feedback = (self._extract_detailed_feedback(lines, "Enfoque de Resolución de Problemas") or 
                       self._extract_detailed_feedback(lines, "Problem-Solving Approach"))
        if ps_feedback:
            feedback_items.append(ps_feedback)

        return InterviewFeedback(
            overall_score=overall_score,
            overall_summary=summary or "Evaluación de desempeño completada.",
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

            # Look for Strength, Weakness, and Suggestions (support both Spanish and English)
            for i in range(start_idx + 1, len(lines)):
                line = lines[i].strip()

                if line.startswith('###') or line.startswith('##'):
                    break

                # Check for strength (English and Spanish)
                if line.startswith('Strength:') or line.startswith('Fortaleza:'):
                    strength = line.replace('Strength:', '').replace('Fortaleza:', '').strip()
                # Check for weakness (English and Spanish)
                elif line.startswith('Weakness:') or line.startswith('Debilidad:'):
                    weakness = line.replace('Weakness:', '').replace('Debilidad:', '').strip()
                # Check for suggestions (English and Spanish)
                elif line.startswith('Suggestions:') or line.startswith('Sugerencias:'):
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
