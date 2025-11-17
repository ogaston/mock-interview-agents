Agente de Entrenamiento para Entrevistas 

 

Descripción general 

Tipo: Deliberativo 

Framework: LangGraph 

Herramientas: Modelo Fuzzy para evaluación de respuestas 

Descripción: Un entrenador basado en LLM que realiza entrevistas simuladas y evalúa las respuestas mediante reglas difusas (p. ej., claridad, confianza, relevancia). 

Tipos de Agentes: 

Agente Entrevistador: formula preguntas contextualizadas. 

Agente Evaluador: aplica lógica difusa a características lingüísticas. 

Agente de Retroalimentación: sugiere mejoras y preguntas siguientes. 

 

Arquitectura a alto nivel 

InterviewerAgent (LLM): genera preguntas contextuales según rol y seniority. 

EvaluatorAgent (Fuzzy): calcula una puntuación difusa por criterio + score 

FeedbackAgent (LLM): explica fortalezas/debilidades y propone ejercicios/recursos 

 

Stack 

LangGraph para orquestación 

spaCy/Transformers para obtener features desde NLP 

skit-fuzzy para modelo difuso 

LlamaIndex para obtener descripción de roles previamente ingestados (opcional)  

 

Flujo 

El usuario selecciona el rol y el senority 

Entrevistador formula las preguntas  

El usuario responde (texto o voz) 

Se capturan todas las respuestas 

Se extraen los features y pasan al evaluador 

Se obtiene una puntuación y se envia al agente de retroalimentación 

El agente de retroalimentación genera recomendaciones y recursos útiles para mejorar. 