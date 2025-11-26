from app.models.schemas import InterviewState

def get_initial_question_prompt(state: InterviewState, focus_areas_text: str) -> str:
    """Get the interview prompt for the given state."""
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


def get_followup_question_prompt(state: InterviewState, question_id: int, category: str, qa_history: str, focus_areas_text: str) -> str:
    """Get the interview prompt for the given state."""
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



def get_all_questions_prompt(state: InterviewState, focus_areas_text: str) -> str:
    """Get the interview prompt for the given state."""
    return f"""
    Eres un entrevistador técnico experimentado conduciendo una entrevista simulada.

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