# Taller Práctico de Fundamentos de RAG y Búsqueda Híbrida

1. Comprenda los fundamentos de RAG y sus principales componentes para construir una solución básica de recuperación aumentada con modelos de lenguaje. Explore técnicas de búsqueda por palabras clave, búsqueda semántica y filtrado de metadatos para construir una estrategia de recuperación híbrida. 2. Aprenda cómo las bases de datos vectoriales permiten escalar la recuperación de información en sistemas RAG y cómo optimizar la calidad de los resultados recuperados. Aplique técnicas de chunking, análisis sintáctico de consultas y reranking para mejorar la relevancia de la información utilizada por el LLM. La práctica se diferencia de los talleres anteriores porque no se enfoca en conversar con documentos ni en responder preguntas, sino en recuperar información, estructurarla y validar que cada dato generado tenga respaldo documental.

## Estructura

- `CapituloXX/README.md`: guía de laboratorio por capítulo.

## Lista de laboratorios

### Capítulo 1

- [Explore cómo RAG puede utilizarse para consultar y contextualizar información sobre productos financieros, como créditos, tarjetas, cuentas y servicios de inversión, reduciendo la dependencia del conocimiento incorporado directamente en el modelo de lenguaje.](Capitulo01/README.md#explore-cómo-rag-puede-utilizarse-para-consultar-y-contextualizar-información-sobre-productos-financieros-como-créditos-tarjetas-cuentas-y-servicios-de-inversión-reduciendo-la-dependencia-del-conocimiento-incorporado-directamente-en-el-modelo-de-lenguaje)
  - Descripción: A través de un caso práctico, conozca cómo combinar diferentes estrategias de búsqueda para recuperar información relevante sobre productos financieros y generar respuestas más precisas y contextualizadas. La sesión combina conceptos y práctica, comenzando con una arquitectura RAG básica y avanzando hacia una estrategia de búsqueda híbrida que integre búsqueda por palabras clave, búsqueda semántica y filtrado por metadatos.
  - Duración estimada: 105 min

### Capítulo 2

- [Explore cómo optimizar sistemas RAG utilizados para consultar información de productos financieros, especialmente cuando las bases de conocimiento contienen grandes volúmenes de documentos, condiciones comerciales, características y políticas.](Capitulo02/README.md#explore-cómo-optimizar-sistemas-rag-utilizados-para-consultar-información-de-productos-financieros-especialmente-cuando-las-bases-de-conocimiento-contienen-grandes-volúmenes-de-documentos-condiciones-comerciales-características-y-políticas)
  - Descripción: Mediante ejercicios prácticos, conozca cómo dividir documentos, interpretar consultas y ordenar los resultados recuperados para proporcionar al modelo de lenguaje información más relevante y mejorar la calidad de las respuestas sobre productos financieros. La sesión parte de los conceptos de recuperación trabajados en el primer taller y avanza hacia estrategias de optimización mediante bases de datos vectoriales, chunking, análisis de consultas y reranking.
  - Duración estimada: 105 min

## Flujo de colaboración

- Trabajar en `changes_course`.
- Crear Pull Request hacia `main`.
- Merge por `Squash and merge`.
