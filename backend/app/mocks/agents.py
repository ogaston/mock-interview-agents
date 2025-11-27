from typing import Iterator, AsyncIterator
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, AIMessageChunk
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.callbacks import CallbackManagerForLLMRun, AsyncCallbackManagerForLLMRun


class MockChatModel(BaseChatModel):
    """Mock chat model that returns predefined responses in rotation."""
    
    def __init__(self, responses: list[str], **kwargs):
        super().__init__(**kwargs)
        # Use object.__setattr__ to bypass Pydantic validation for these fields
        # since BaseChatModel is a Pydantic model and doesn't allow arbitrary attributes
        object.__setattr__(self, 'responses', responses)
        object.__setattr__(self, '_current_index', 0)
    
    def invoke(self, input, config=None, **kwargs):
        """
        Override invoke to handle both string and message list inputs.
        Ensures we always return an AIMessage with .content attribute.
        """
        # Convert string to HumanMessage if needed
        if isinstance(input, str):
            messages = [HumanMessage(content=input)]
        elif isinstance(input, list):
            messages = input
        else:
            messages = [input]
        
        # Call _generate directly and extract the AIMessage
        result = self._generate(messages, **kwargs)
        # Extract AIMessage from ChatResult
        if result.generations and result.generations[0].message:
            return result.generations[0].message
        # Fallback: create AIMessage from first generation
        return AIMessage(content=result.generations[0].text if result.generations else "")
    
    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs,
    ) -> ChatResult:
        # Get the next response in rotation
        response_text = self.responses[self._current_index % len(self.responses)]
        self._current_index += 1
        
        # Create an AIMessage with the response
        message = AIMessage(content=response_text)
        generation = ChatGeneration(message=message)
        
        return ChatResult(generations=[generation])
    
    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs,
    ) -> ChatResult:
        # Same as sync version
        return self._generate(messages, stop, run_manager, **kwargs)
    
    async def ainvoke(self, input, config=None, **kwargs):
        """
        Override ainvoke to handle both string and message list inputs.
        Ensures we always return an AIMessage with .content attribute.
        """
        # Convert string to HumanMessage if needed
        if isinstance(input, str):
            messages = [HumanMessage(content=input)]
        elif isinstance(input, list):
            messages = input
        else:
            messages = [input]
        
        # Call _agenerate directly and extract the AIMessage
        result = await self._agenerate(messages, **kwargs)
        # Extract AIMessage from ChatResult
        if result.generations and result.generations[0].message:
            return result.generations[0].message
        # Fallback: create AIMessage from first generation
        return AIMessage(content=result.generations[0].text if result.generations else "")
    
    @property
    def _llm_type(self) -> str:
        return "mock"
    
    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs,
    ) -> Iterator[AIMessageChunk]:
        # Get the next response in rotation
        response_text = self.responses[self._current_index % len(self.responses)]
        self._current_index += 1
        
        # Stream the response word by word to simulate real streaming
        # Use AIMessageChunk for streaming chunks
        words = response_text.split()
        for i, word in enumerate(words):
            content = word if i == 0 else f" {word}"
            yield AIMessageChunk(content=content)
    
    async def astream(self, input, config=None, **kwargs):
        """
        Override astream to handle both string and message list inputs.
        Ensures compatibility with LangChain's astream wrapper.
        """
        # Convert string to HumanMessage if needed
        if isinstance(input, str):
            messages = [HumanMessage(content=input)]
        elif isinstance(input, list):
            messages = input
        else:
            messages = [input]
        
        # Call _astream and yield chunks directly (bypassing base class wrapper)
        async for chunk in self._astream(messages, **kwargs):
            yield chunk
    
    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs,
    ) -> AsyncIterator[AIMessageChunk]:
        # Get the next response in rotation
        response_text = self.responses[self._current_index % len(self.responses)]
        self._current_index += 1
        
        # Stream the response word by word to simulate real streaming
        # Use AIMessageChunk for streaming chunks
        words = response_text.split()
        for i, word in enumerate(words):
            content = word if i == 0 else f" {word}"
            yield AIMessageChunk(content=content)


class MockInterviewerAgent:
    """MOCK Agent responsible for generating interview questions."""


    def __init__(self):
        self.llm = self._initialize_llm()

    def _initialize_llm(self):
        """Initialize the mock LLM with rotating responses for variety"""
        mock_responses = [
            "¿Puedes contarme sobre tu experiencia con desarrollo de software?",
            "¿Cómo manejas situaciones de alta presión en proyectos?",
            "¿Qué tecnologías prefieres usar y por qué?",
            "Describe un proyecto desafiante en el que hayas trabajado.",
            "¿Cómo te mantienes actualizado con las nuevas tecnologías?",
            "¿Cuál es tu enfoque para depurar problemas complejos?",
            "Háblame sobre tu experiencia trabajando en equipo.",
            "¿Cómo priorizas las tareas cuando tienes múltiples proyectos?",
            "¿Qué metodologías ágiles has utilizado?",
            "Describe cómo abordas el diseño de una nueva funcionalidad.",
        ]
        return MockChatModel(responses=mock_responses)


class MockFeedbackAgent:
    """MOCK Agent responsible for generating feedback."""

    def __init__(self):
        self.llm = self._initialize_llm()

    def _initialize_llm(self):
        """Initialize the mock LLM with rotating responses for variety"""
        mock_responses = ["""## RESUMEN GENERAL
El candidato demostró un buen nivel de conocimiento técnico y comunicación clara. Las respuestas fueron relevantes y bien estructuradas, mostrando experiencia práctica en desarrollo de software.

## FORTALEZAS
- Comunicación clara y estructurada
- Buen conocimiento técnico demostrado
- Experiencia práctica con tecnologías relevantes
- Capacidad para explicar conceptos complejos

## ÁREAS DE MEJORA
- Podría incluir más ejemplos específicos de proyectos
- Mayor detalle en metodologías de trabajo
- Más profundidad en decisiones técnicas

## RETROALIMENTACIÓN DETALLADA

### Habilidades de Comunicación
Fortaleza: Las respuestas fueron claras y bien organizadas, facilitando la comprensión.
Debilidad: Algunas respuestas podrían beneficiarse de más ejemplos concretos.
Sugerencias:
- Practica estructurar respuestas con ejemplos específicos
- Incluye métricas o resultados cuando sea posible

### Conocimiento Técnico
Fortaleza: Demostró buen dominio de las tecnologías mencionadas.
Debilidad: Podría profundizar más en decisiones de arquitectura.
Sugerencias:
- Estudia patrones de diseño y arquitectura de software
- Practica explicar trade-offs técnicos

### Enfoque de Resolución de Problemas
Fortaleza: Mostró un enfoque sistemático para abordar problemas.
Debilidad: Podría incluir más detalles sobre el proceso de depuración.
Sugerencias:
- Practica explicar tu proceso de pensamiento paso a paso
- Incluye herramientas y técnicas específicas que utilizas

## RECURSOS RECOMENDADOS
- Libro: "Clean Code" de Robert C. Martin
- Curso: "System Design Interview" en educative.io
- Artículo: "Design Patterns in Modern Software Development"
- Comunidad: Stack Overflow y Reddit r/programming"""]
        return MockChatModel(responses=mock_responses)

