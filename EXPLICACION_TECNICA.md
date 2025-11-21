# Explicación Técnica Detallada - Mock Interview Agents

## 📋 Tabla de Contenidos
1. [Arquitectura General](#arquitectura-general)
2. [Modelos de Datos (Schemas)](#modelos-de-datos-schemas)
3. [Agente Entrevistador (InterviewerAgent)](#agente-entrevistador-intervieweragent)
4. [Agente Evaluador (EvaluatorAgent)](#agente-evaluador-evaluatoragent)
5. [Servicio NLP (NLPService)](#servicio-nlp-nlpservice)
6. [Servicio de Lógica Difusa (FuzzyEvaluationService)](#servicio-de-lógica-difusa-fuzzyevaluationservice)
7. [Agente de Retroalimentación (FeedbackAgent)](#agente-de-retroalimentación-feedbackagent)
8. [Workflow LangGraph](#workflow-langgraph)
9. [Flujo Completo de Ejecución](#flujo-completo-de-ejecución)

---

## Arquitectura General

El sistema utiliza una **arquitectura de agentes multi-agente** orquestada por **LangGraph**. Cada agente tiene una responsabilidad específica:

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI REST API                         │
│              (app/api/routes/interviews.py)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              LangGraph Workflow                              │
│              (app/graph/workflow.py)                         │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │  Interviewer │───▶│  Evaluator   │───▶│  Feedback    │ │
│  │    Agent     │    │    Agent     │    │    Agent     │ │
│  └──────────────┘    └──────┬───────┘    └──────────────┘ │
│                              │                              │
│                              ▼                              │
│                    ┌─────────────────┐                      │
│                    │  NLP Service    │                      │
│                    │  Fuzzy Service  │                      │
│                    └─────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Modelos de Datos (Schemas)

### InterviewState - Estado Central del Workflow

El `InterviewState` es el **estado compartido** que fluye a través del grafo de LangGraph:

```python
class InterviewState(BaseModel):
    session_id: str                    # UUID único de la sesión
    role: str                          # Rol del candidato (ej: "Software Engineer")
    seniority: str                     # Nivel: "junior", "mid", "senior", "lead"
    focus_areas: list[str]             # Áreas específicas a enfocar
    
    # Progreso de la entrevista
    current_question_id: int           # ID de la pregunta actual
    total_questions: int                # Total de preguntas (default: 10)
    questions: list[Question]          # Lista de todas las preguntas generadas
    answers: list[str]                  # Lista de todas las respuestas del usuario
    evaluations: list[AnswerEvaluation] # Lista de todas las evaluaciones
    
    # Feedback final
    final_feedback: InterviewFeedback | None
    
    # Estado
    status: Literal["in_progress", "completed"]
    created_at: datetime
```

**Características importantes:**
- Es **inmutable** en teoría, pero LangGraph permite mutaciones controladas
- Se pasa entre nodos del grafo como un objeto compartido
- Contiene todo el contexto necesario para que los agentes tomen decisiones

### NLPFeatures - Características Extraídas

Representa las características lingüísticas extraídas de una respuesta:

```python
class NLPFeatures(BaseModel):
    word_count: int              # Número total de palabras
    sentence_count: int           # Número de oraciones
    avg_sentence_length: float    # Longitud promedio de oraciones
    sentiment_score: float        # -1 (negativo) a 1 (positivo)
    confidence_indicators: int    # Contador de palabras que indican confianza
    filler_words_count: int       # Contador de palabras de relleno ("um", "uh")
    technical_terms_count: int    # Contador de términos técnicos
    coherence_score: float        # 0 a 1: coherencia entre oraciones
    complexity_score: float       # 0 a 1: complejidad del vocabulario
```

### EvaluationScore - Puntuaciones de Evaluación

Resultado de la evaluación con lógica difusa:

```python
class EvaluationScore(BaseModel):
    clarity: float        # 0-10: Claridad de la respuesta
    confidence: float     # 0-10: Nivel de confianza mostrado
    relevance: float      # 0-10: Relevancia técnica
    overall_score: float  # 0-10: Promedio ponderado
                          # (30% clarity + 30% confidence + 40% relevance)
```

---

## Agente Entrevistador (InterviewerAgent)

### Responsabilidad
Genera preguntas contextuales y adaptativas usando un LLM (OpenAI o Anthropic).

### Implementación Interna

#### 1. Inicialización del LLM

```python
def _initialize_llm(self):
    config = settings.get_llm_config()
    
    if config["provider"] == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=config["model"],        # ej: "gpt-4o-mini"
            api_key=config["api_key"],
            temperature=0.7               # Balance entre creatividad y consistencia
        )
```

**Parámetros clave:**
- `temperature=0.7`: Permite variación en las preguntas pero mantiene calidad
- Modelo configurable: Puede usar GPT-4, GPT-4o-mini, Claude, etc.

#### 2. Generación de Primera Pregunta

```python
def generate_first_question(self, state: InterviewState) -> Question:
    prompt = self._build_initial_prompt(state)
    response = self.llm.invoke(prompt)
    
    return Question(
        question_id=1,
        question_text=response.content.strip(),
        category="opening",
        timestamp=datetime.utcnow()
    )
```

**Prompt construido:**
```
You are an experienced technical interviewer conducting a mock interview.

Interview Details:
- Role: {state.role}
- Seniority Level: {state.seniority}
- Specific focus areas: {focus_areas}

Generate an appropriate opening question...
```

**Características:**
- La pregunta es **contextual** al rol y nivel
- Es una pregunta de "apertura" (más fácil, para romper el hielo)
- El LLM genera texto libre que se extrae directamente

#### 3. Generación de Preguntas Siguientes

```python
def generate_next_question(self, state: InterviewState) -> Question:
    question_id = len(state.questions) + 1
    prompt = self._build_followup_prompt(state, question_id)
    response = self.llm.invoke(prompt)
    
    category = self._determine_category(question_id, state.total_questions)
    
    return Question(...)
```

**Prompt incluye:**
- **Historial completo** de Q&A anteriores
- **Puntuaciones** de evaluaciones previas
- **Contexto** del progreso (pregunta X de Y)
- **Categoría** determinada por posición

**Categorización automática:**
```python
def _determine_category(self, question_id: int, total_questions: int) -> str:
    progress = question_id / total_questions
    
    if question_id == 1:
        return "opening"
    elif progress <= 0.3:
        return "foundational"    # Primeras 30%
    elif progress <= 0.6:
        return "intermediate"     # 30-60%
    elif progress <= 0.9:
        return "advanced"         # 60-90%
    else:
        return "closing"          # Últimas 10%
```

**Adaptación de dificultad:**
El prompt incluye instrucciones como:
- "Adjust difficulty based on previous performance"
- "If scores are consistently high, increase difficulty"
- "Build upon topics mentioned in previous answers"

---

## Agente Evaluador (EvaluatorAgent)

### Responsabilidad
Evalúa respuestas usando **NLP + Lógica Difusa** para generar puntuaciones objetivas.

### Flujo de Evaluación

```python
def evaluate_answer(self, question: Question, answer: str) -> AnswerEvaluation:
    # Paso 1: Extraer características NLP
    features = self.nlp_service.extract_features(answer)
    
    # Paso 2: Aplicar lógica difusa
    scores = self.fuzzy_service.evaluate(features, answer)
    
    # Paso 3: Generar resumen interpretable
    feature_summary = self.nlp_service.get_feature_summary(features)
    
    return AnswerEvaluation(
        question_id=question.question_id,
        answer_text=answer,
        scores=scores,
        nlp_features=nlp_features_dict,
        timestamp=datetime.utcnow()
    )
```

**No usa LLM** - Es completamente determinístico basado en análisis lingüístico.

---

## Servicio NLP (NLPService)

### Responsabilidad
Extrae características lingüísticas de texto usando **spaCy** y análisis estadístico.

### Implementación Detallada

#### 1. Inicialización con spaCy

```python
@property
def nlp(self):
    if self._nlp is None:
        import spacy
        try:
            self._nlp = spacy.load("en_core_web_sm")  # Modelo pre-entrenado
        except OSError:
            self._nlp = spacy.blank("en")  # Fallback: modelo básico
    return self._nlp
```

**Modelo spaCy `en_core_web_sm`:**
- Tokenización (separar palabras)
- Análisis morfológico (lemas, POS tags)
- Reconocimiento de entidades
- Análisis de dependencias

#### 2. Extracción de Características

```python
def extract_features(self, text: str) -> NLPFeatures:
    doc = self.nlp(text)  # Procesa el texto con spaCy
    
    # Estadísticas básicas
    words = [token for token in doc if not token.is_punct]
    word_count = len(words)
    sentences = list(doc.sents)
    sentence_count = len(sentences)
    avg_sentence_length = word_count / sentence_count
```

#### 3. Detección de Palabras de Relleno

```python
filler_words = {
    "um", "uh", "like", "you know", "i mean", "sort of", 
    "basically", "actually", "literally", "so", "well"
}

filler_count = sum(1 for word in self.filler_words if word in text_lower)
```

#### 4. Indicadores de Confianza

```python
confidence_indicators = {
    "definitely", "certainly", "clearly", "obviously", 
    "precisely", "exactly", "absolutely", "confident", 
    "sure", "positive", "undoubtedly", "believe", "think", "know"
}

confidence_count = sum(1 for word in self.confidence_indicators if word in text_lower)
```

#### 5. Términos Técnicos

```python
technical_terms = {
    "algorithm", "complexity", "database", "api", "framework",
    "architecture", "scalability", "optimization", "implementation",
    "design pattern", "microservice", "cache", "queue", "stack"
}

technical_count = sum(1 for term in self.technical_terms if term in text_lower)
```

#### 6. Análisis de Sentimiento (Simple)

```python
def _calculate_sentiment(self, text: str) -> float:
    positive_words = {"good", "great", "excellent", "positive", ...}
    negative_words = {"bad", "poor", "fail", "difficult", ...}
    
    pos_count = sum(1 for word in positive_words if word in text)
    neg_count = sum(1 for word in negative_words if word in text)
    
    total = pos_count + neg_count
    if total == 0:
        return 0.0
    
    return (pos_count - neg_count) / total  # -1 a 1
```

**Nota:** Esta es una implementación simple. Para producción, se podría usar un modelo de transformers.

#### 7. Cálculo de Coherencia

```python
def _calculate_coherence(self, doc, sentences: list) -> float:
    # Extrae palabras clave (nombres, verbos) de cada oración
    sentence_keywords = []
    for sent in sentences:
        keywords = {token.lemma_.lower() 
                   for token in sent 
                   if token.pos_ in ["NOUN", "PROPN", "VERB"]}
        sentence_keywords.append(keywords)
    
    # Calcula solapamiento entre oraciones consecutivas
    overlaps = []
    for i in range(len(sentence_keywords) - 1):
        current = sentence_keywords[i]
        next_sent = sentence_keywords[i + 1]
        overlap = len(current & next_sent) / len(current | next_sent)  # Jaccard
        overlaps.append(overlap)
    
    return sum(overlaps) / len(overlaps) if overlaps else 0.5
```

**Método:**
- Extrae palabras clave de cada oración
- Calcula **coeficiente de Jaccard** entre oraciones consecutivas
- Promedia los solapamientos
- Resultado: 0 (sin coherencia) a 1 (muy coherente)

#### 8. Cálculo de Complejidad

```python
def _calculate_complexity(self, words: list) -> float:
    # Diversidad de vocabulario
    unique_words = set(token.lemma_.lower() for token in words)
    diversity = len(unique_words) / len(words)  # Ratio de unicidad
    
    # Longitud promedio de palabras
    avg_word_length = sum(len(token.text) for token in words) / len(words)
    length_score = min(avg_word_length / 10, 1.0)  # Normalizado
    
    # Combinación ponderada
    complexity = (diversity * 0.6) + (length_score * 0.4)
    return complexity
```

**Métricas:**
- **Diversidad:** Ratio de palabras únicas (más diverso = más complejo)
- **Longitud:** Palabras más largas indican vocabulario más sofisticado
- **Combinación:** 60% diversidad + 40% longitud

---

## Servicio de Lógica Difusa (FuzzyEvaluationService)

### Responsabilidad
Convierte características NLP en puntuaciones usando **lógica difusa (fuzzy logic)**.

### ¿Qué es la Lógica Difusa?

La lógica difusa permite manejar **incertidumbre** y **grados de pertenencia** en lugar de valores binarios (sí/no). Es ideal para evaluaciones subjetivas como "claridad" o "confianza".

### Implementación Detallada

#### 1. Definición de Variables de Entrada

```python
# Variables de entrada (normalizadas a 0-10)
self.word_count = ctrl.Antecedent(np.arange(0, 11, 1), 'word_count')
self.coherence = ctrl.Antecedent(np.arange(0, 11, 1), 'coherence')
self.confidence_level = ctrl.Antecedent(np.arange(0, 11, 1), 'confidence_level')
self.technical_depth = ctrl.Antecedent(np.arange(0, 11, 1), 'technical_depth')
self.filler_ratio = ctrl.Antecedent(np.arange(0, 11, 1), 'filler_ratio')
self.complexity = ctrl.Antecedent(np.arange(0, 11, 1), 'complexity')

# Variables de salida (0-10)
self.clarity_score = ctrl.Consequent(np.arange(0, 11, 1), 'clarity_score')
self.confidence_score = ctrl.Consequent(np.arange(0, 11, 1), 'confidence_score')
self.relevance_score = ctrl.Consequent(np.arange(0, 11, 1), 'relevance_score')
```

#### 2. Funciones de Pertenencia (Membership Functions)

Para cada variable, se definen **conjuntos difusos** usando funciones triangulares:

```python
# Ejemplo: Word Count
self.word_count['low'] = fuzz.trimf(self.word_count.universe, [0, 0, 4])
self.word_count['medium'] = fuzz.trimf(self.word_count.universe, [3, 5, 7])
self.word_count['high'] = fuzz.trimf(self.word_count.universe, [6, 10, 10])
```

**Interpretación:**
- `low`: Valores 0-4 (pertenencia máxima en 0)
- `medium`: Valores 3-7 (pertenencia máxima en 5)
- `high`: Valores 6-10 (pertenencia máxima en 10)

**Visualización:**
```
Pertenencia
   1.0 |     low      medium      high
       |     /\        /\         /\
       |    /  \      /  \       /  \
   0.0 |___/    \____/    \_____/    \___
       0  2  4  6  8  10
```

#### 3. Reglas de Inferencia

##### Reglas para CLARIDAD

```python
clarity_rules = [
    # Si coherencia ALTA Y pocos fillers → Claridad EXCELENTE
    ctrl.Rule(self.coherence['high'] & self.filler_ratio['low'], 
              self.clarity_score['excellent']),
    
    # Si coherencia ALTA Y fillers MEDIOS → Claridad BUENA
    ctrl.Rule(self.coherence['high'] & self.filler_ratio['medium'], 
              self.clarity_score['good']),
    
    # Si coherencia MEDIA Y pocos fillers → Claridad BUENA
    ctrl.Rule(self.coherence['medium'] & self.filler_ratio['low'], 
              self.clarity_score['good']),
    
    # Si coherencia MEDIA Y fillers MEDIOS → Claridad REGULAR
    ctrl.Rule(self.coherence['medium'] & self.filler_ratio['medium'], 
              self.clarity_score['fair']),
    
    # Si coherencia BAJA O muchos fillers → Claridad POBRE
    ctrl.Rule(self.coherence['low'] | self.filler_ratio['high'], 
              self.clarity_score['poor']),
]
```

**Lógica:**
- Claridad depende de **coherencia** y **ausencia de fillers**
- Operadores: `&` (AND), `|` (OR)

##### Reglas para CONFIANZA

```python
confidence_rules = [
    # Si indicadores de confianza ALTA Y respuesta LARGA → Confianza EXCELENTE
    ctrl.Rule(self.confidence_level['high'] & self.word_count['high'], 
              self.confidence_score['excellent']),
    
    # Si indicadores ALTA Y respuesta MEDIA → Confianza BUENA
    ctrl.Rule(self.confidence_level['high'] & self.word_count['medium'], 
              self.confidence_score['good']),
    
    # Si indicadores MEDIA Y respuesta MEDIA → Confianza BUENA
    ctrl.Rule(self.confidence_level['medium'] & self.word_count['medium'], 
              self.confidence_score['good']),
    
    # Si indicadores BAJA → Confianza POBRE
    ctrl.Rule(self.confidence_level['low'], 
              self.confidence_score['poor']),
]
```

**Lógica:**
- Confianza depende de **indicadores lingüísticos** y **longitud de respuesta**
- Respuestas más largas con indicadores de confianza = más confianza

##### Reglas para RELEVANCIA

```python
relevance_rules = [
    # Si profundidad técnica ALTA Y complejidad ALTA → Relevancia EXCELENTE
    ctrl.Rule(self.technical_depth['high'] & self.complexity['high'], 
              self.relevance_score['excellent']),
    
    # Si profundidad ALTA Y complejidad MEDIA → Relevancia BUENA
    ctrl.Rule(self.technical_depth['high'] & self.complexity['medium'], 
              self.relevance_score['good']),
    
    # Si profundidad BAJA → Relevancia POBRE
    ctrl.Rule(self.technical_depth['low'], 
              self.relevance_score['poor']),
]
```

**Lógica:**
- Relevancia depende de **profundidad técnica** y **complejidad del vocabulario**

#### 4. Normalización de Características

Antes de aplicar lógica difusa, las características NLP se normalizan a escala 0-10:

```python
def _normalize_features(self, features: NLPFeatures) -> dict:
    # Word count: normalizado basado en rangos esperados (50-200 palabras)
    word_count_norm = min((features.word_count / 150) * 10, 10)
    
    # Coherence: ya está en 0-1, escalar a 0-10
    coherence_norm = features.coherence_score * 10
    
    # Confidence: basado en indicadores por 100 palabras
    confidence_ratio = (features.confidence_indicators / max(features.word_count / 100, 1))
    confidence_norm = min(confidence_ratio * 5, 10)
    
    # Technical depth: términos técnicos por 100 palabras
    technical_ratio = (features.technical_terms_count / max(features.word_count / 100, 1))
    technical_norm = min(technical_ratio * 3, 10)
    
    # Filler ratio: INVERSA (más fillers = peor)
    filler_ratio = (features.filler_words_count / max(features.word_count / 100, 1))
    filler_norm = max(10 - (filler_ratio * 5), 0)  # Invertido
    
    # Complexity: ya está en 0-1, escalar a 0-10
    complexity_norm = features.complexity_score * 10
    
    return {
        'word_count': max(0, min(word_count_norm, 10)),
        'coherence': max(0, min(coherence_norm, 10)),
        'confidence_level': max(0, min(confidence_norm, 10)),
        'technical_depth': max(0, min(technical_norm, 10)),
        'filler_ratio': max(0, min(filler_norm, 10)),
        'complexity': max(0, min(complexity_norm, 10)),
    }
```

#### 5. Proceso de Evaluación

```python
def evaluate(self, features: NLPFeatures, answer_text: str) -> EvaluationScore:
    # 1. Normalizar características
    normalized = self._normalize_features(features)
    
    # 2. Calcular CLARIDAD
    clarity_sim = ctrl.ControlSystemSimulation(self.clarity_system)
    clarity_sim.input['coherence'] = normalized['coherence']
    clarity_sim.input['filler_ratio'] = normalized['filler_ratio']
    clarity_sim.compute()  # Ejecuta inferencia difusa
    clarity = float(clarity_sim.output['clarity_score'])
    
    # 3. Calcular CONFIANZA
    confidence_sim = ctrl.ControlSystemSimulation(self.confidence_system)
    confidence_sim.input['confidence_level'] = normalized['confidence_level']
    confidence_sim.input['word_count'] = normalized['word_count']
    confidence_sim.compute()
    confidence = float(confidence_sim.output['confidence_score'])
    
    # 4. Calcular RELEVANCIA
    relevance_sim = ctrl.ControlSystemSimulation(self.relevance_system)
    relevance_sim.input['technical_depth'] = normalized['technical_depth']
    relevance_sim.input['complexity'] = normalized['complexity']
    relevance_sim.compute()
    relevance = float(relevance_sim.output['relevance_score'])
    
    # 5. Calcular PUNTUACIÓN GENERAL (promedio ponderado)
    overall = (clarity * 0.3) + (confidence * 0.3) + (relevance * 0.4)
    
    return EvaluationScore(
        clarity=round(clarity, 2),
        confidence=round(confidence, 2),
        relevance=round(relevance, 2),
        overall_score=round(overall, 2)
    )
```

**Proceso de inferencia difusa:**
1. **Fuzzificación:** Convierte valores nítidos en grados de pertenencia
2. **Evaluación de reglas:** Aplica todas las reglas y calcula activación
3. **Agregación:** Combina resultados de todas las reglas
4. **Defuzzificación:** Convierte resultado difuso en valor nítido (0-10)

---

## Agente de Retroalimentación (FeedbackAgent)

### Responsabilidad
Genera retroalimentación personalizada usando un LLM que analiza todas las respuestas y evaluaciones.

### Implementación Detallada

#### 1. Construcción del Prompt

El prompt incluye **todo el historial** de la entrevista:

```python
def _build_feedback_prompt(self, state: InterviewState, overall_score: float) -> str:
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
```

**Prompt estructurado:**
```
You are an expert interview coach providing comprehensive feedback...

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

## AREAS FOR IMPROVEMENT
- [Specific area 1]
- [Specific area 2]

## DETAILED FEEDBACK
### Communication Skills
Strength: [What they did well]
Weakness: [What needs improvement]
Suggestions:
- [Specific actionable suggestion 1]

## RECOMMENDED RESOURCES
- [Resource 1: Book/Course/Article]
...
```

#### 2. Parsing de la Respuesta del LLM

El LLM genera texto estructurado que se parsea:

```python
def _parse_llm_feedback(self, llm_response: str, ...) -> InterviewFeedback:
    lines = llm_response.split('\n')
    
    # Extraer secciones
    summary = self._extract_section(lines, "OVERALL SUMMARY")
    strengths = self._extract_list_items(lines, "STRENGTHS")
    improvements = self._extract_list_items(lines, "AREAS FOR IMPROVEMENT")
    resources = self._extract_list_items(lines, "RECOMMENDED RESOURCES")
    
    # Extraer feedback detallado por categoría
    feedback_items = []
    comm_feedback = self._extract_detailed_feedback(lines, "Communication Skills")
    tech_feedback = self._extract_detailed_feedback(lines, "Technical Knowledge")
    ps_feedback = self._extract_detailed_feedback(lines, "Problem-Solving Approach")
    
    return InterviewFeedback(
        overall_score=overall_score,
        overall_summary=summary,
        feedback_items=feedback_items,
        recommended_resources=resources,
        strengths=strengths,
        areas_for_improvement=improvements
    )
```

**Métodos de extracción:**
- `_extract_section()`: Busca un header y extrae texto hasta el siguiente header
- `_extract_list_items()`: Extrae items de lista (líneas que empiezan con `-` o `•`)
- `_extract_detailed_feedback()`: Extrae estructura "Strength/Weakness/Suggestions"

---

## Workflow LangGraph

### Estructura del Grafo

```python
workflow = StateGraph(InterviewState)

# Nodos
workflow.add_node("generate_question", generate_question_node)
workflow.add_node("evaluate_answer", evaluate_answer_node)
workflow.add_node("generate_feedback", generate_feedback_node)

# Punto de entrada
workflow.set_entry_point("generate_question")

# Aristas condicionales
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

workflow.add_edge("generate_feedback", END)
```

### Nodos del Workflow

#### 1. generate_question_node

```python
def generate_question_node(state: InterviewState) -> InterviewState:
    if len(state.questions) == 0:
        question = interviewer_agent.generate_first_question(state)
    else:
        question = interviewer_agent.generate_next_question(state)
    
    state.questions.append(question)
    state.current_question_id = question.question_id
    return state
```

#### 2. evaluate_answer_node

```python
def evaluate_answer_node(state: InterviewState) -> InterviewState:
    if not state.answers:
        return state
    
    last_question = state.questions[-1]
    last_answer = state.answers[-1]
    
    evaluation = evaluator_agent.evaluate_answer(last_question, last_answer)
    state.evaluations.append(evaluation)
    
    return state
```

#### 3. generate_feedback_node

```python
def generate_feedback_node(state: InterviewState) -> InterviewState:
    feedback = feedback_agent.generate_feedback(state)
    state.final_feedback = feedback
    state.status = "completed"
    return state
```

### Funciones Condicionales

#### should_continue

```python
def should_continue(state: InterviewState) -> Literal["evaluate", "generate_feedback", "end"]:
    # Si hay una respuesta sin evaluar
    if len(state.answers) > len(state.evaluations):
        return "evaluate"
    
    # Si se alcanzó el total de preguntas
    if state.current_question_id >= state.total_questions:
        return "generate_feedback"
    
    # Esperando siguiente respuesta
    return "end"
```

#### after_evaluation

```python
def after_evaluation(state: InterviewState) -> Literal["generate_question", "generate_feedback"]:
    # Si se alcanzó el total, generar feedback
    if state.current_question_id >= state.total_questions:
        return "generate_feedback"
    
    # Si no, generar siguiente pregunta
    return "generate_question"
```

### Flujo Visual

```
START
  │
  ▼
[generate_question]
  │
  ├─→ ¿Hay respuesta sin evaluar? ──→ [evaluate_answer]
  │                                        │
  │                                        ├─→ ¿Última pregunta? ──→ [generate_feedback] ──→ END
  │                                        │
  │                                        └─→ [generate_question] ──→ (loop)
  │
  ├─→ ¿Última pregunta? ──→ [generate_feedback] ──→ END
  │
  └─→ END (esperando respuesta)
```

---

## Flujo Completo de Ejecución

### Escenario: Usuario inicia entrevista y responde 3 preguntas

#### 1. POST /api/interviews/start

```python
# En interviews.py
state = interview_workflow.start_interview(
    role="Software Engineer",
    seniority="mid",
    focus_areas=["algorithms"],
    total_questions=10
)
```

**Workflow ejecuta:**
1. Crea `InterviewState` inicial
2. Invoca grafo → `generate_question_node`
3. `InterviewerAgent.generate_first_question()`:
   - Construye prompt con rol y seniority
   - Llama a LLM (OpenAI/Anthropic)
   - Recibe pregunta generada
4. Agrega pregunta a `state.questions`
5. Retorna estado con primera pregunta

**Respuesta API:**
```json
{
  "session_id": "uuid-123",
  "role": "Software Engineer",
  "seniority": "mid",
  "current_question": {
    "question_id": 1,
    "question_text": "Can you explain the difference between a stack and a queue?",
    "category": "opening"
  },
  "total_questions": 10,
  "status": "in_progress"
}
```

#### 2. POST /api/interviews/{session_id}/answer

```python
# Usuario envía respuesta
updated_state = interview_workflow.submit_answer(state, "A stack is LIFO...")
```

**Workflow ejecuta:**
1. Agrega respuesta a `state.answers`
2. Invoca grafo → `should_continue()` detecta respuesta sin evaluar
3. Flujo a `evaluate_answer_node`:
   - `EvaluatorAgent.evaluate_answer()`:
     - **NLP Service:** Extrae características
       - word_count: 45
       - coherence_score: 0.75
       - confidence_indicators: 3
       - filler_words_count: 1
       - technical_terms_count: 5
       - complexity_score: 0.65
     - **Fuzzy Service:** Aplica lógica difusa
       - Normaliza características
       - Evalúa reglas de claridad, confianza, relevancia
       - Calcula scores: clarity=7.5, confidence=8.2, relevance=7.0
       - overall_score = (7.5*0.3) + (8.2*0.3) + (7.0*0.4) = 7.51
4. Agrega evaluación a `state.evaluations`
5. Flujo a `after_evaluation()` → `generate_question_node`
6. `InterviewerAgent.generate_next_question()`:
   - Construye prompt con historial Q&A y scores
   - LLM genera pregunta adaptada
   - Determina categoría: "foundational" (pregunta 2 de 10)
7. Agrega pregunta a `state.questions`

**Respuesta API:**
```json
{
  "session_id": "uuid-123",
  "question_answered": 1,
  "evaluation": {
    "clarity": 7.5,
    "confidence": 8.2,
    "relevance": 7.0,
    "overall_score": 7.51
  },
  "next_question": {
    "question_id": 2,
    "question_text": "How would you implement a queue using two stacks?",
    "category": "foundational"
  },
  "status": "in_progress",
  "questions_remaining": 9
}
```

#### 3. Repetición (preguntas 2 y 3)

El mismo flujo se repite para cada respuesta.

#### 4. GET /api/interviews/{session_id}/feedback

```python
# Después de completar todas las preguntas
state = interview_workflow.get_feedback(state)
```

**Workflow ejecuta:**
1. Verifica que todas las respuestas estén evaluadas
2. `generate_feedback_node`:
   - `FeedbackAgent.generate_feedback()`:
     - Calcula overall_score promedio: (7.51 + 8.2 + 7.8) / 3 = 7.84
     - Construye prompt con TODO el historial:
       - Todas las preguntas y respuestas
       - Todas las evaluaciones y scores
       - Análisis NLP de cada respuesta
     - LLM genera retroalimentación estructurada
     - Parsea respuesta en `InterviewFeedback`
3. Actualiza `state.final_feedback` y `state.status = "completed"`

**Respuesta API:**
```json
{
  "session_id": "uuid-123",
  "feedback": {
    "overall_score": 7.84,
    "overall_summary": "Strong performance with good technical knowledge...",
    "strengths": [
      "Clear communication style",
      "Good grasp of fundamental concepts"
    ],
    "areas_for_improvement": [
      "Could provide more concrete examples",
      "Practice system design patterns"
    ],
    "feedback_items": [
      {
        "category": "Communication Skills",
        "strength": "Well-structured responses",
        "weakness": "Occasional use of filler words",
        "suggestions": ["Practice speaking more slowly"]
      }
    ],
    "recommended_resources": [
      "Book: Cracking the Coding Interview",
      "Platform: LeetCode for algorithm practice"
    ]
  },
  "all_evaluations": [...],
  "interview_duration_minutes": 15.5
}
```

---

## Resumen de Tecnologías y Conceptos Clave

### 1. **LangGraph**
- Framework para orquestar agentes multi-agente
- Grafo de estado compartido (`InterviewState`)
- Nodos = funciones, Aristas = flujo condicional

### 2. **Lógica Difusa (Fuzzy Logic)**
- Maneja incertidumbre y grados de pertenencia
- Ideal para evaluaciones subjetivas
- Usa reglas "si-entonces" con operadores difusos

### 3. **NLP con spaCy**
- Tokenización y análisis morfológico
- Extracción de características lingüísticas
- Análisis de coherencia y complejidad

### 4. **LLMs (OpenAI/Anthropic)**
- Generación de preguntas contextuales
- Generación de retroalimentación personalizada
- Adaptación basada en historial

### 5. **Arquitectura de Agentes**
- Separación de responsabilidades
- Agentes especializados (entrevistador, evaluador, feedback)
- Comunicación a través de estado compartido

---

## Ventajas de esta Arquitectura

1. **Modularidad:** Cada agente es independiente y testeable
2. **Escalabilidad:** Fácil agregar nuevos agentes o modificar existentes
3. **Transparencia:** El estado compartido permite debugging y logging
4. **Flexibilidad:** LangGraph permite flujos complejos con condiciones
5. **Objetividad:** Evaluación basada en NLP + fuzzy logic (no solo LLM)
6. **Personalización:** LLM adapta preguntas y feedback al contexto

---

## Posibles Mejoras

1. **NLP más avanzado:** Usar transformers para sentimiento y análisis semántico
2. **Base de datos:** Persistir sesiones en PostgreSQL/MongoDB
3. **WebSockets:** Entrevistas en tiempo real
4. **Voice-to-text:** Entrevistas verbales
5. **Aprendizaje:** Ajustar reglas fuzzy basado en feedback de usuarios
6. **Multi-idioma:** Soporte para otros idiomas

