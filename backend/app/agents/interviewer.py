"""
Interviewer Agent - Generates contextual interview questions using LLM.
"""
from datetime import datetime
from app.config import settings
from app.models.schemas import Question, InterviewState


class InterviewerAgent:
    """Agent responsible for generating interview questions."""

    def __init__(self):
        """Initialize the interviewer agent with LLM."""
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
        else:
            raise ValueError(f"Unsupported LLM provider: {config['provider']}")

    def generate_first_question(self, state: InterviewState) -> Question:
        """
        Generate the first question for a new interview.

        Args:
            state: Current interview state

        Returns:
            The first interview question
        """
        prompt = self._build_initial_prompt(state)
        response = self.llm.invoke(prompt)

        return Question(
            question_id=1,
            question_text=response.content.strip(),
            category="opening",
            timestamp=datetime.utcnow()
        )

    def generate_next_question(self, state: InterviewState) -> Question:
        """
        Generate the next question based on previous answers.

        Args:
            state: Current interview state with history

        Returns:
            The next interview question
        """
        question_id = len(state.questions) + 1
        prompt = self._build_followup_prompt(state, question_id)
        response = self.llm.invoke(prompt)

        # Determine category based on question number
        category = self._determine_category(question_id, state.total_questions)

        return Question(
            question_id=question_id,
            question_text=response.content.strip(),
            category=category,
            timestamp=datetime.utcnow()
        )

    def _build_initial_prompt(self, state: InterviewState) -> str:
        """Build prompt for generating the first question."""
        focus_areas_text = ""
        if state.focus_areas:
            focus_areas_text = f"\nSpecific focus areas: {', '.join(state.focus_areas)}"

        prompt = f"""You are an experienced technical interviewer conducting a mock interview.

Interview Details:
- Role: {state.role}
- Seniority Level: {state.seniority}{focus_areas_text}
- Total Questions: {state.total_questions}
- Current Question: 1 (Opening question)

Generate an appropriate opening question for this interview. The question should:
1. Be appropriate for the {state.seniority} level
2. Be relevant to the {state.role} role
3. Help establish rapport while assessing initial technical understanding
4. Be clear and specific
5. Not be too difficult as it's the first question

Provide ONLY the question text, without any additional commentary or numbering."""

        return prompt

    def _build_followup_prompt(self, state: InterviewState, question_id: int) -> str:
        """Build prompt for generating follow-up questions."""
        # Build context from previous Q&A
        qa_history = ""
        for i, (q, a) in enumerate(zip(state.questions, state.answers), 1):
            eval_summary = ""
            if i <= len(state.evaluations):
                eval = state.evaluations[i - 1]
                eval_summary = f" [Scores - Clarity: {eval.scores.clarity}, Confidence: {eval.scores.confidence}, Relevance: {eval.scores.relevance}]"

            qa_history += f"\nQ{i}: {q.question_text}\nA{i}: {a[:200]}...{eval_summary}\n"

        focus_areas_text = ""
        if state.focus_areas:
            focus_areas_text = f"\nSpecific focus areas: {', '.join(state.focus_areas)}"

        category = self._determine_category(question_id, state.total_questions)

        prompt = f"""You are an experienced technical interviewer conducting a mock interview.

Interview Details:
- Role: {state.role}
- Seniority Level: {state.seniority}{focus_areas_text}
- Total Questions: {state.total_questions}
- Current Question: {question_id}
- Question Category: {category}

Previous Interview History:
{qa_history}

Based on the candidate's previous answers and their performance scores, generate the next interview question.

Guidelines:
1. Adjust difficulty based on previous performance (if scores are consistently high, increase difficulty)
2. For question {question_id} of {state.total_questions}, this should be a {category} question
3. Build upon or explore topics mentioned in previous answers when appropriate
4. Ensure the question is appropriate for {state.seniority} level
5. Keep questions clear, specific, and focused
6. If this is near the end, consider asking a challenging question or a practical scenario

Provide ONLY the question text, without any additional commentary or numbering."""

        return prompt

    def _determine_category(self, question_id: int, total_questions: int) -> str:
        """Determine the category of question based on position in interview."""
        progress = question_id / total_questions

        if question_id == 1:
            return "opening"
        elif progress <= 0.3:
            return "foundational"
        elif progress <= 0.6:
            return "intermediate"
        elif progress <= 0.9:
            return "advanced"
        else:
            return "closing"


# Singleton instance
interviewer_agent = InterviewerAgent()
