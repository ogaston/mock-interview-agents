"""
LangGraph Workflow for orchestrating the interview process.
Connects InterviewerAgent, EvaluatorAgent, and FeedbackAgent in a deliberative flow.
"""
from typing import Literal
from datetime import datetime
from langgraph.graph import StateGraph, END
from app.models.schemas import InterviewState, Question
from app.agents.interviewer import interviewer_agent
from app.agents.evaluator import evaluator_agent
from app.agents.feedback import feedback_agent


# Define the workflow nodes
def generate_question_node(state: InterviewState) -> InterviewState:
    """
    Node: Generate the next interview question.
    """
    if len(state.questions) == 0:
        # Generate first question
        question = interviewer_agent.generate_first_question(state)
    else:
        # Generate follow-up question
        question = interviewer_agent.generate_next_question(state)

    state.questions.append(question)
    state.current_question_id = question.question_id

    return state


def evaluate_answer_node(state: InterviewState) -> InterviewState:
    """
    Node: Evaluate the most recent answer.
    """
    if not state.answers:
        return state

    # Get the last question and answer
    last_question = state.questions[-1]
    last_answer = state.answers[-1]

    # Evaluate the answer
    evaluation = evaluator_agent.evaluate_answer(last_question, last_answer)
    state.evaluations.append(evaluation)

    return state


def generate_feedback_node(state: InterviewState) -> InterviewState:
    """
    Node: Generate final comprehensive feedback.
    """
    feedback = feedback_agent.generate_feedback(state)
    state.final_feedback = feedback
    state.status = "completed"

    return state


def should_continue(state: InterviewState) -> Literal["evaluate", "generate_feedback", "end"]:
    """
    Conditional edge: Determine next step based on interview progress.
    """
    # If we have an answer that hasn't been evaluated yet
    if len(state.answers) > len(state.evaluations):
        return "evaluate"

    # If we've reached the total number of questions
    if state.current_question_id >= state.total_questions:
        return "generate_feedback"

    # Otherwise, we're done with current cycle (waiting for next answer)
    return "end"


def after_evaluation(state: InterviewState) -> Literal["generate_question", "generate_feedback"]:
    """
    Conditional edge: After evaluation, decide whether to continue or finish.
    """
    # If we've reached the total number of questions, generate feedback
    if state.current_question_id >= state.total_questions:
        return "generate_feedback"

    # Otherwise, generate next question
    return "generate_question"


class InterviewWorkflow:
    """
    LangGraph workflow for managing the interview process.
    """

    def __init__(self):
        """Initialize the workflow graph."""
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph."""

        # Create the graph
        workflow = StateGraph(InterviewState)

        # Add nodes
        workflow.add_node("generate_question", generate_question_node)
        workflow.add_node("evaluate_answer", evaluate_answer_node)
        workflow.add_node("generate_feedback", generate_feedback_node)

        # Set entry point
        workflow.set_entry_point("generate_question")

        # Add conditional edges
        workflow.add_conditional_edges(
            "generate_question",
            should_continue,
            {
                "evaluate": "evaluate_answer",
                "generate_feedback": "generate_feedback",
                "end": END
            }
        )

        workflow.add_conditional_edges(
            "evaluate_answer",
            after_evaluation,
            {
                "generate_question": "generate_question",
                "generate_feedback": "generate_feedback"
            }
        )

        # Feedback leads to end
        workflow.add_edge("generate_feedback", END)

        return workflow.compile()

    def start_interview_incremental(
        self,
        role: str,
        seniority: str,
        focus_areas: list[str] | None = None,
        total_questions: int = 10,
        generate_first_question: bool = True
    ) -> InterviewState:
        """
        Start a new interview session.

        Args:
            role: Job role/position
            seniority: Seniority level
            focus_areas: Optional specific focus areas
            total_questions: Number of questions for the interview
            generate_first_question: Whether to generate the first question immediately.
                                     Set to False for streaming endpoints.

        Returns:
            Initial interview state, with first question generated if generate_first_question=True
        """
        # Create initial state
        initial_state = InterviewState(
            role=role,
            seniority=seniority,
            focus_areas=focus_areas or [],
            total_questions=total_questions
        )

        # Generate first question if requested
        if generate_first_question:
            first_question = interviewer_agent.generate_first_question(initial_state)
            initial_state.questions.append(first_question)
            initial_state.current_question_id = first_question.question_id

        return initial_state

    def submit_answer(self, state: InterviewState, answer: str) -> InterviewState:
        """
        Submit an answer and get the next question from pre-generated list.

        Args:
            state: Current interview state
            answer: User's answer to the current question

        Returns:
            Updated state with answer added (no evaluation yet)
        """
        # Add answer to state
        state.answers.append(answer)

        # Update current question ID to next question if available
        if len(state.answers) < len(state.questions):
            state.current_question_id = state.questions[len(state.answers)].question_id
        else:
            # All questions answered
            state.current_question_id = state.total_questions

        return state

    def evaluate_all_answers(self, state: InterviewState) -> InterviewState:
        """
        Evaluate all answers in bulk.

        Args:
            state: Interview state with all questions and answers

        Returns:
            State with all evaluations added
        """
        # Evaluate all unanswered questions
        new_evaluations = evaluator_agent.evaluate_all_answers(state)
        state.evaluations.extend(new_evaluations)

        return state

    def get_feedback(self, state: InterviewState) -> InterviewState:
        """
        Get final feedback for a completed interview.

        Args:
            state: Interview state

        Returns:
            State with final feedback generated
        """
        if state.final_feedback:
            return state

        # Ensure all answers have been evaluated
        if len(state.evaluations) < len(state.answers):
            state = self.evaluate_all_answers(state)

        # Generate feedback
        state = generate_feedback_node(state)

        return state

    def add_streamed_question(
        self,
        state: InterviewState,
        question_text: str,
        question_id: int,
        category: str
    ) -> InterviewState:
        """
        Add a question that was streamed to the state.

        Args:
            state: Current interview state
            question_text: The full text of the streamed question
            question_id: The ID of the question
            category: The category of the question

        Returns:
            Updated state with the question added
        """
        question = Question(
            question_id=question_id,
            question_text=question_text.strip(),
            category=category,
            timestamp=datetime.utcnow()
        )
        state.questions.append(question)
        state.current_question_id = question.question_id
        return state


# Singleton instance
interview_workflow = InterviewWorkflow()
