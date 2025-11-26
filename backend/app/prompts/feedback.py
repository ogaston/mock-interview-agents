from app.models.schemas import InterviewState, Question, AnswerEvaluation

def get_feedback_prompt(state: InterviewState, overall_score: float, qa_history: str) -> str:
    """Get the feedback prompt for the given state."""
    prompt = f"""Eres un coach experto de entrevistas proporcionando retroalimentación integral sobre una entrevista simulada.

Detalles de la Entrevista:
- Puesto: {state.role}
- Nivel de Antigüedad: {state.seniority}
- Total de Preguntas: {len(state.questions)}
- Puntuación General: {overall_score}/10

Transcripción Completa de la Entrevista con Evaluaciones:
{qa_history}

Basándote en el desempeño de esta entrevista, proporciona retroalimentación detallada y accionable en el siguiente formato EN ESPAÑOL:

## RESUMEN GENERAL
[2-3 oraciones resumiendo el desempeño general del candidato]

## FORTALEZAS
- [Fortaleza específica 1]
- [Fortaleza específica 2]
- [Fortaleza específica 3]

## ÁREAS DE MEJORA
- [Área específica 1]
- [Área específica 2]
- [Área específica 3]

## RETROALIMENTACIÓN DETALLADA

### Habilidades de Comunicación
Fortaleza: [Lo que hicieron bien]
Debilidad: [Lo que necesita mejora]
Sugerencias:
- [Sugerencia accionable específica 1]
- [Sugerencia accionable específica 2]

### Conocimiento Técnico
Fortaleza: [Lo que hicieron bien]
Debilidad: [Lo que necesita mejora]
Sugerencias:
- [Sugerencia accionable específica 1]
- [Sugerencia accionable específica 2]

### Enfoque de Resolución de Problemas
Fortaleza: [Lo que hicieron bien]
Debilidad: [Lo que necesita mejora]
Sugerencias:
- [Sugerencia accionable específica 1]
- [Sugerencia accionable específica 2]

## RECURSOS RECOMENDADOS
- [Recurso 1: Libro/Curso/Artículo con breve descripción]
- [Recurso 2: Plataforma de práctica o herramienta]
- [Recurso 3: Tema específico para estudiar]
- [Recurso 4: Comunidad o foro para unirse]

Mantén la retroalimentación constructiva, específica y accionable. Enfócate en ejemplos concretos de sus respuestas. Responde TODO en español."""

    return prompt


def get_qa_history_prompt(question: Question, answer: str, evaluation: AnswerEvaluation, i: int) -> str:
    """Get the feedback summary prompt for the given state."""
    return f"""
Pregunta {i} ({question.category}): {question.question_text}

Respuesta: {answer}

Puntuaciones de Evaluación:
- Claridad: {evaluation.scores.clarity}/10
- Confianza: {evaluation.scores.confidence}/10
- Relevancia: {evaluation.scores.relevance}/10
- General: {evaluation.scores.overall_score}/10

Análisis NLP: {evaluation.nlp_features.get('summary', {})}
---
"""