"""
Interviewer Agent - Generates contextual interview questions using LLM.
"""
from datetime import datetime
from app.config import settings
from app.models.schemas import Question, InterviewState

from app.mocks.agents import MockInterviewerAgent

class InterviewerAgent:
    """Agent responsible for generating interview questions."""

    def __init__(self):
        """Initialize the interviewer agent with LLM."""
        self.llm = self._initialize_llm()

    def _initialize_llm(self):
        """Initialize the appropriate LLM based on configuration."""
        config = settings.get_llm_config()

        if config["provider"] == "mock":
            mock_interviewer_agent = MockInterviewerAgent()
            return mock_interviewer_agent._initialize_llm()
            
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

    async def stream_first_question(self, state: InterviewState):
        """
        Stream the first question for a new interview.

        Args:
            state: Current interview state

        Yields:
            Text chunks as they are generated
        """
        prompt = self._build_initial_prompt(state)
        
        async for chunk in self.llm.astream(prompt):
            if hasattr(chunk, 'content') and chunk.content:
                yield chunk.content

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

    async def stream_next_question(self, state: InterviewState):
        """
        Stream the next question based on previous answers.

        Args:
            state: Current interview state with history

        Yields:
            Text chunks as they are generated
        """
        question_id = len(state.questions) + 1
        prompt = self._build_followup_prompt(state, question_id)
        
        async for chunk in self.llm.astream(prompt):
            if hasattr(chunk, 'content') and chunk.content:
                yield chunk.content

    def generate_all_questions(self, state: InterviewState) -> list[Question]:
        """
        Generate all interview questions upfront.

        Args:
            state: Current interview state

        Returns:
            List of all interview questions
        """
        prompt = self._build_all_questions_prompt(state)
        response = self.llm.invoke(prompt)
        
        # Parse the response to extract all questions
        questions = self._parse_all_questions(response.content.strip(), state.total_questions)
        
        return questions

    def _build_initial_prompt(self, state: InterviewState) -> str:
        """Build prompt for generating the first question."""
        focus_areas_text = ""
        if state.focus_areas:
            focus_areas_text = f"\nÁreas de enfoque específicas: {', '.join(state.focus_areas)}"

        prompt = f"""Eres un entrevistador técnico experimentado conduciendo una entrevista simulada.

Detalles de la Entrevista:
- Puesto: {state.role}
- Nivel de Antigüedad: {state.seniority}{focus_areas_text}
- Total de Preguntas: {state.total_questions}
- Pregunta Actual: 1 (Pregunta de apertura)

Genera una pregunta de apertura apropiada para esta entrevista. La pregunta debe:
1. Ser apropiada para el nivel {state.seniority}
2. Ser relevante para el puesto de {state.role}
3. Ayudar a establecer rapport mientras evalúas la comprensión técnica inicial
4. Ser clara y específica
5. No ser demasiado difícil ya que es la primera pregunta

Proporciona ÚNICAMENTE el texto de la pregunta en español, sin comentarios adicionales ni numeración."""

        return prompt

    def _build_followup_prompt(self, state: InterviewState, question_id: int) -> str:
        """Build prompt for generating follow-up questions."""
        # Build context from previous Q&A
        qa_history = ""
        for i, (q, a) in enumerate(zip(state.questions, state.answers), 1):
            eval_summary = ""
            if i <= len(state.evaluations):
                eval = state.evaluations[i - 1]
                eval_summary = f" [Puntuaciones - Claridad: {eval.scores.clarity}, Confianza: {eval.scores.confidence}, Relevancia: {eval.scores.relevance}]"

            qa_history += f"\nP{i}: {q.question_text}\nR{i}: {a[:200]}...{eval_summary}\n"

        focus_areas_text = ""
        if state.focus_areas:
            focus_areas_text = f"\nÁreas de enfoque específicas: {', '.join(state.focus_areas)}"

        category = self._determine_category(question_id, state.total_questions)

        prompt = f"""Eres un entrevistador técnico experimentado conduciendo una entrevista simulada.

Detalles de la Entrevista:
- Puesto: {state.role}
- Nivel de Antigüedad: {state.seniority}{focus_areas_text}
- Total de Preguntas: {state.total_questions}
- Pregunta Actual: {question_id}
- Categoría de Pregunta: {category}

Historial Previo de la Entrevista:
{qa_history}

Basándote en las respuestas previas del candidato y sus puntuaciones de desempeño, genera la siguiente pregunta de la entrevista.

Directrices:
1. Ajusta la dificultad basándote en el desempeño previo (si las puntuaciones son consistentemente altas, aumenta la dificultad)
2. Para la pregunta {question_id} de {state.total_questions}, esta debe ser una pregunta de tipo {category}
3. Construye sobre o explora temas mencionados en respuestas anteriores cuando sea apropiado
4. Asegúrate de que la pregunta sea apropiada para el nivel {state.seniority}
5. Mantén las preguntas claras, específicas y enfocadas
6. Si esto está cerca del final, considera hacer una pregunta desafiante o un escenario práctico

Proporciona ÚNICAMENTE el texto de la pregunta en español, sin comentarios adicionales ni numeración."""

        return prompt

    def _build_all_questions_prompt(self, state: InterviewState) -> str:
        """Build prompt for generating all questions at once."""
        focus_areas_text = ""
        if state.focus_areas:
            focus_areas_text = f"\nÁreas de enfoque específicas: {', '.join(state.focus_areas)}"

        prompt = f"""Eres un entrevistador técnico experimentado conduciendo una entrevista simulada.

Detalles de la Entrevista:
- Puesto: {state.role}
- Nivel de Antigüedad: {state.seniority}{focus_areas_text}
- Total de Preguntas: {state.total_questions}

Genera todas las {state.total_questions} preguntas de entrevista para esta entrevista. Las preguntas deben:
1. Ser apropiadas para el nivel {state.seniority}
2. Ser relevantes para el puesto de {state.role}
3. Progresar en dificultad desde lo fundamental hasta lo avanzado
4. Cubrir diferentes aspectos: apertura, conceptos fundamentales, temas intermedios, escenarios avanzados y cierre
5. Ser claras, específicas y enfocadas
6. Ser diversas en temas mientras se mantienen relevantes al puesto

Formatea tu respuesta como una lista numerada, con cada pregunta en una nueva línea comenzando con el número de pregunta.
Ejemplo:
1. [Texto de la primera pregunta]
2. [Texto de la segunda pregunta]
3. [Texto de la tercera pregunta]
...

Proporciona ÚNICAMENTE la lista numerada de preguntas en español, sin comentarios adicionales o encabezados."""

        return prompt

    def _parse_all_questions(self, response_text: str, total_questions: int) -> list[Question]:
        """Parse LLM response to extract all questions."""
        questions = []
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Try to extract question number and text
            # Handle formats like "1. Question text" or "1) Question text" or just "Question text"
            question_text = line
            question_id = len(questions) + 1
            
            # Try to parse numbered format
            if line and (line[0].isdigit() or (len(line) > 1 and line[1] in ['.', ')', ':'])):
                # Remove number prefix
                parts = line.split('.', 1)
                if len(parts) == 2:
                    try:
                        question_id = int(parts[0].strip())
                        question_text = parts[1].strip()
                    except ValueError:
                        question_text = line
                else:
                    # Try other separators
                    parts = line.split(')', 1)
                    if len(parts) == 2:
                        try:
                            question_id = int(parts[0].strip())
                            question_text = parts[1].strip()
                        except ValueError:
                            question_text = line
                    else:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            try:
                                question_id = int(parts[0].strip())
                                question_text = parts[1].strip()
                            except ValueError:
                                question_text = line
            
            if question_text:
                category = self._determine_category(question_id, total_questions)
                questions.append(Question(
                    question_id=question_id,
                    question_text=question_text,
                    category=category,
                    timestamp=datetime.utcnow()
                ))
        
        # Ensure we have exactly total_questions
        if len(questions) < total_questions:
            # If we got fewer questions, pad with generic ones
            while len(questions) < total_questions:
                question_id = len(questions) + 1
                category = self._determine_category(question_id, total_questions)
                questions.append(Question(
                    question_id=question_id,
                    question_text=f"Pregunta {question_id} (generada como respaldo)",
                    category=category,
                    timestamp=datetime.utcnow()
                ))
        elif len(questions) > total_questions:
            # If we got more, take only the first total_questions
            questions = questions[:total_questions]
        
        return questions

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
