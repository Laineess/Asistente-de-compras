# Glosario

Términos usados en la documentación y el código del proyecto.

| Término | Definición |
|---|---|
| **Agente** | Sistema que percibe un entorno, razona y ejecuta acciones mediante herramientas para cumplir un objetivo. |
| **Agente reactivo** | Responde a estímulos inmediatos sin planificación extensa. |
| **Agente deliberativo** | Planifica antes de actuar usando un modelo del mundo. |
| **Agente híbrido** | Combina planificación y reacción; es el enfoque habitual en agentes basados en LLM. |
| **LLM** | *Large Language Model*. Modelo de lenguaje que razona y genera texto; actúa como "cerebro" del agente. |
| **Prompt** | Instrucción o plantilla que guía al LLM. |
| **Herramienta (tool)** | Función externa que el agente puede invocar (búsqueda, base de datos, API). |
| **Tool calling** | Mecanismo por el que el LLM solicita ejecutar una herramienta con argumentos estructurados. |
| **ReAct** | Patrón *Reason + Act*: el agente alterna razonamiento y acciones hasta resolver la tarea. |
| **Chain** | Secuencia predefinida de pasos en LangChain. |
| **LCEL** | *LangChain Expression Language*. DSL para componer cadenas con el operador `|`. |
| **LangChain** | Framework para construir aplicaciones con LLM: modelos, prompts, herramientas, memoria e integraciones. |
| **LangGraph** | Extensión de LangChain para orquestar agentes como grafos con estado, ciclos y persistencia. |
| **StateGraph** | Grafo de LangGraph cuyo estado compartido se actualiza nodo a nodo. |
| **Nodo** | Unidad de ejecución de un grafo (una función o agente). |
| **Arista (edge)** | Transición entre nodos. |
| **Arista condicional** | Transición decidida por una función de enrutamiento según el estado. |
| **Estado (state)** | Estructura de datos compartida entre nodos de un grafo. |
| **Reducer** | Función que define cómo se combinan las actualizaciones de un campo del estado (por ejemplo, concatenar listas). |
| **Checkpoint** | Punto de guardado del estado para reanudar o auditar una ejecución. |
| **Checkpointer** | Componente de LangGraph que persiste checkpoints. |
| **HITL** | *Human-in-the-loop*. Intervención humana en un punto del flujo del agente. |
| **Subgrafo** | Grafo anidado dentro de otro grafo. |
| **Supervisor** | Agente que decide qué agente especializado actúa a continuación. |
| **Multiagente** | Sistema compuesto por varios agentes con responsabilidades separadas. |
| **Handoff** | Transferencia de control de un agente a otro. |
| **Memoria** | Estado retenido entre interacciones (corto o largo plazo). |
| **RAG** | *Retrieval-Augmented Generation*. Generación aumentada con recuperación de documentos. |
| **Structured output** | Respuesta del LLM validada contra un esquema (por ejemplo, Pydantic). |
| **Provider** | Adaptador que obtiene datos de una fuente concreta (Tavily, mock, tienda). |
| **Mock** | Datos simulados usados como respaldo o para pruebas. |
| **Fallback** | Ruta alternativa cuando la principal falla. |
| **ORM** | *Object-Relational Mapping*. Mapeo entre objetos y tablas (SQLAlchemy). |
| **Repositorio** | Clase que encapsula las operaciones de acceso a datos (guardar, listar, contar, limpiar). |
| **Persistencia best-effort** | Guardado que no bloquea la respuesta si la base de datos falla; se registra una advertencia. |
| **SSE** | *Server-Sent Events*. Canal unidireccional servidor → cliente para progreso en tiempo real. |
| **CORS** | Política del navegador que controla peticiones entre orígenes distintos. |
| **Token** | Unidad de texto que procesa un LLM; afecta costo y límite de contexto. |
| **Embedding** | Representación vectorial de texto usada para búsqueda semántica. |
| **Trazabilidad (tracing)** | Registro detallado de pasos, entradas y salidas de un agente. |
| **Bot** | Programa que interactúa por chat y ejecuta acciones de forma automatizada; en este proyecto, el cliente de Telegram. |
| **Telegram Bot API** | API de Telegram para crear y operar bots mediante un token. |
| **Long polling** | Técnica en la que el bot consulta periódicamente a Telegram; no requiere webhook ni puerto público. |
| **Allowlist** | Lista explícita de usuarios autorizados; el resto se rechaza. |
| **Slot** | Dato necesario o útil para ejecutar una consulta (producto, tiendas, presupuesto, perfil). |
| **Slot filling** | Proceso de extraer y completar slots conversacionalmente antes de ejecutar. |
| **STT** | *Speech-to-Text*. Transcripción de audio a texto; aquí con `faster-whisper`. |
| **TTS** | *Text-to-Speech*. Síntesis de voz a partir de texto; aquí con `edge-tts`. |
| **Nota de voz** | Mensaje de audio de Telegram en formato OGG/Opus, distinto de un archivo de audio. |
| **systemd** | Gestor de servicios de Linux; mantiene el bot activo y lo reinicia si falla. |
| **Unidad systemd** | Archivo `.service` que describe cómo ejecutar un proceso. |
| **VPS** | Servidor privado virtual donde se despliega el bot 24/7. |
| **Rate limit** | Límite de solicitudes por usuario y periodo para evitar abuso. |
| **Modo `fast`** | Ejecución sin Gemini; usa búsqueda y heurísticas deterministas. |
| **Modo `detallado`** | Ejecución con Gemini para enriquecer reseñas, audiencia y síntesis. |
