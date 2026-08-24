---LAB_START---
LAB_ID: 02-00-01
---MARKDOWN---
# Optimización de Sistemas RAG para Productos Financieros con Búsqueda Híbrida, Reranking y Evaluación RAGAS

## Metadatos

| Campo | Valor |
|-------|-------|
| **Duración** | 105 minutos |
| **Complejidad** | Alta |
| **Nivel Bloom** | Aplicar |

## Descripción General

En este laboratorio escalarás el pipeline RAG básico construido en el Lab 1 hacia un sistema optimizado capaz de manejar 50+ documentos financieros. Implementarás búsqueda híbrida combinando Qdrant (semántica) con Elasticsearch (BM25), aplicarás estrategias avanzadas de chunking, integrarás Cohere Rerank para reordenar resultados y evaluarás cuantitativamente el sistema usando el framework RAGAS. Al finalizar, dispondrás de métricas comparativas que demuestran la mejora sobre el pipeline básico.

## Objetivos de Aprendizaje

- [ ] Implementar búsqueda híbrida combinando recuperación semántica (Qdrant) y léxica BM25 (Elasticsearch) con pesos configurables
- [ ] Aplicar y comparar tres estrategias de chunking (fijo, semántico, jerárquico) sobre documentos financieros complejos
- [ ] Integrar Cohere Rerank como etapa de reordenamiento post-fusión para maximizar la relevancia
- [ ] Escalar el sistema RAG a 50+ documentos con metadatos enriquecidos y filtrado contextual
- [ ] Evaluar cuantitativamente el sistema con RAGAS (faithfulness, answer_relevancy, context_precision) y comparar contra el baseline del Lab 1

## Prerrequisitos

### Conocimientos Requeridos
- Laboratorio 1 (01-00-01) completado con todos sus artefactos funcionales
- Comprensión del pipeline RAG básico: embeddings, búsqueda vectorial, generación con LLM
- Familiaridad con Docker y Docker Compose
- Conocimientos básicos de Python y Jupyter notebooks

### Acceso y Cuentas
- Colección Qdrant `financial_products_basic` activa con 5 documentos indexados del Lab 1
- API key de OpenAI válida (para embeddings y chat)
- API key de Cohere válida (tier gratuito suficiente)
- Al menos 8 GB de RAM disponible para ejecutar Qdrant + Elasticsearch simultáneamente

## Entorno del Laboratorio

### Hardware Mínimo

| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| CPU | 4 núcleos | 8 núcleos |
| RAM | 16 GB | 32 GB |
| Disco SSD | 20 GB libres | 30 GB libres |
| Red | Internet estable | Internet estable |

### Software Requerido

| Componente | Versión |
|------------|---------|
| Python | 3.11.9 |
| Docker Desktop | 26.1.4 |
| Docker Compose | 2.27.1 |
| Qdrant | 1.9.4 |
| Elasticsearch | 8.13.4 |
| LangChain | 0.2.6 |
| sentence-transformers | 3.0.1 |
| RAGAS | 0.1.14 |
| Cohere SDK | 5.5.8 |

### Configuración Inicial del Entorno

```bash
# Crear directorio del laboratorio
mkdir -p ~/rag-financiero-workshop/lab02
cd ~/rag-financiero-workshop/lab02

# Verificar que el archivo .env existe con las variables requeridas
cat ~/rag-financiero-workshop/.env
```

Contenido esperado del archivo `.env`:

```env
OPENAI_API_KEY=<tu-clave-openai>
COHERE_API_KEY=<tu-clave-cohere>
QDRANT_HOST=localhost
QDRANT_PORT=6333
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o
COHERE_RERANK_MODEL=rerank-english-v3.0
```

Instalar dependencias adicionales para este laboratorio:

```bash
cd ~/rag-financiero-workshop
pip install sentence-transformers==3.0.1 ragas==0.1.14 datasets==2.20.0 \
    pandas==2.2.2 matplotlib==3.9.0 tiktoken==0.7.0 \
    elasticsearch==8.13.2 cohere==5.5.8
```

---

## Paso 1: Levantar Infraestructura Docker (Qdrant + Elasticsearch)

### Objetivo
Configurar y levantar ambos servicios de búsqueda mediante Docker Compose para disponer de recuperación semántica y léxica simultáneamente.

### Instrucciones

1. Crear el archivo `docker-compose.yml` en el directorio raíz del workshop:

```bash
cd ~/rag-financiero-workshop
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  qdrant-financiero:
    image: qdrant/qdrant:v1.9.4
    container_name: qdrant-financiero
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./volumes/qdrant_storage:/qdrant/storage
    restart: unless-stopped

  elasticsearch-financiero:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.13.4
    container_name: elasticsearch-financiero
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - ./volumes/elasticsearch_data:/usr/share/elasticsearch/data
    restart: unless-stopped
EOF
```

2. Crear directorios de volúmenes y levantar los servicios:

```bash
mkdir -p volumes/qdrant_storage volumes/elasticsearch_data
docker compose up -d
```

3. Verificar que ambos servicios están activos:

```bash
# Verificar Qdrant
curl -s http://localhost:6333/collections | python3 -m json.tool

# Verificar Elasticsearch
curl -s http://localhost:9200/_cluster/health | python3 -m json.tool
```

4. Confirmar que la colección del Lab 1 sigue disponible:

```bash
curl -s http://localhost:6333/collections/financial_products_basic | python3 -m json.tool
```

### Resultado Esperado

Qdrant responde con la lista de colecciones incluyendo `financial_products_basic`. Elasticsearch responde con `"status": "green"` o `"yellow"` y `"number_of_nodes": 1`.

### Verificación

```bash
# Ambos contenedores deben estar en estado "running"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "qdrant|elasticsearch"
```

Salida esperada (similar a):
```
qdrant-financiero          Up 30 seconds   0.0.0.0:6333-6334->6333-6334/tcp
elasticsearch-financiero   Up 28 seconds   0.0.0.0:9200->9200/tcp
```

---

## Paso 2: Escalado del Corpus y Generación de Documentos Financieros

### Objetivo
Ampliar la base de conocimiento de 5 a 50+ documentos financieros con metadatos enriquecidos, simulando un corpus realista de productos bancarios.

### Instrucciones

1. Crear el notebook principal del laboratorio:

```bash
cd ~/rag-financiero-workshop/lab02
touch lab02_rag_optimizado.ipynb
```

2. En el notebook (o en un script Python `generate_corpus.py`), generar el corpus ampliado:

```python
# Celda 1: Configuración e imports
import os
import json
import random
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path("~/rag-financiero-workshop/.env").expanduser())

CORPUS_DIR = Path("~/rag-financiero-workshop/data/corpus").expanduser()
CORPUS_DIR.mkdir(parents=True, exist_ok=True)

# Categorías de productos financieros
CATEGORIAS = {
    "credito_hipotecario": {
        "tipo_producto": "credito",
        "categoria": "hipotecario"
    },
    "credito_consumo": {
        "tipo_producto": "credito",
        "categoria": "consumo"
    },
    "tarjeta_credito": {
        "tipo_producto": "tarjeta",
        "categoria": "credito"
    },
    "cuenta_ahorro": {
        "tipo_producto": "cuenta",
        "categoria": "ahorro"
    },
    "cuenta_corriente": {
        "tipo_producto": "cuenta",
        "categoria": "corriente"
    },
    "fondo_inversion": {
        "tipo_producto": "inversion",
        "categoria": "fondo"
    },
    "seguro_vida": {
        "tipo_producto": "seguro",
        "categoria": "vida"
    },
    "deposito_plazo": {
        "tipo_producto": "inversion",
        "categoria": "deposito"
    }
}

print(f"Directorio de corpus: {CORPUS_DIR}")
print(f"Categorías definidas: {len(CATEGORIAS)}")
```

3. Generar los 45 documentos adicionales con contenido financiero realista:

```python
# Celda 2: Plantillas de documentos financieros
import datetime

def generar_documento_credito_hipotecario(idx, variante):
    tasas = ["8.5%", "9.2%", "10.1%", "7.8%", "11.0%"]
    plazos = ["10 años", "15 años", "20 años", "25 años", "30 años"]
    montos = ["$500,000", "$1,000,000", "$2,500,000", "$5,000,000"]
    
    contenido = f"""# Crédito Hipotecario - Producto {variante}

## Condiciones Generales

El Crédito Hipotecario {variante} está diseñado para la adquisición de vivienda nueva o usada.

### Tasa de Interés
- Tasa fija anual: {tasas[idx % len(tasas)]}
- CAT promedio: {float(tasas[idx % len(tasas)].replace('%','')) + 2.5}%
- Tasa moratoria: {float(tasas[idx % len(tasas)].replace('%','')) + 5.0}% anual

### Plazo y Monto
- Plazo máximo: {plazos[idx % len(plazos)]}
- Monto mínimo: $200,000 MXN
- Monto máximo: {montos[idx % len(montos)]} MXN
- Enganche mínimo: {10 + (idx % 3) * 5}% del valor del inmueble

### Requisitos
1. Edad entre 25 y 64 años al momento de la solicitud
2. Antigüedad laboral mínima de {1 + idx % 3} años
3. Ingresos mínimos comprobables de $25,000 MXN mensuales
4. Historial crediticio sin atrasos mayores a 30 días en los últimos 12 meses
5. Avalúo del inmueble realizado por perito autorizado

### Comisiones
- Comisión por apertura: {1.0 + (idx % 3) * 0.5}% sobre el monto del crédito
- Comisión por pago anticipado: Sin penalización después del primer año
- Gastos notariales: A cargo del acreditado
- Seguro de vida: Incluido en la mensualidad

### Tabla de Amortización (ejemplo para $1,000,000 a 20 años)
| Año | Capital | Interés | Pago Total | Saldo |
|-----|---------|---------|------------|-------|
| 1   | $25,000 | $85,000 | $110,000   | $975,000 |
| 5   | $35,000 | $75,000 | $110,000   | $850,000 |
| 10  | $50,000 | $60,000 | $110,000   | $650,000 |
| 15  | $70,000 | $40,000 | $110,000   | $350,000 |
| 20  | $95,000 | $15,000 | $110,000   | $0 |

### Políticas de Contratación
- El inmueble debe estar libre de gravámenes
- Se requiere seguro contra daños durante toda la vigencia del crédito
- El acreditado debe mantener una cuenta de ahorro activa con la institución
- Aplican restricciones geográficas según la zona del inmueble
"""
    return contenido

def generar_documento_tarjeta(idx, variante):
    anualidades = ["$0 (primer año)", "$1,200", "$2,500", "$4,800", "$0 (sin anualidad)"]
    limites = ["$15,000", "$50,000", "$150,000", "$500,000", "$1,000,000"]
    
    contenido = f"""# Tarjeta de Crédito {variante}

## Características Principales

La Tarjeta {variante} ofrece beneficios exclusivos para clientes del segmento {['básico','clásico','oro','platinum','black'][idx % 5]}.

### Costos y Comisiones
- Anualidad: {anualidades[idx % len(anualidades)]}
- Tasa de interés ordinaria: {25 + idx * 3}% anual
- Tasa de interés moratoria: {35 + idx * 3}% anual
- Comisión por disposición de efectivo: 6% del monto dispuesto
- Comisión por pago tardío: $500 MXN

### Límite de Crédito
- Límite asignado: Desde {limites[idx % len(limites)]} MXN
- Línea de crédito revolvente
- Incremento automático por buen comportamiento crediticio

### Programa de Recompensas
- Acumulación: {1 + idx % 3} punto(s) por cada $10 MXN de compra
- Canje mínimo: 1,000 puntos
- Vigencia de puntos: 24 meses desde la fecha de acumulación
- Categorías con puntos dobles: Supermercados, gasolineras, restaurantes

### Seguros Incluidos
- Seguro de compras protegidas: Hasta $50,000 MXN por evento
- Seguro de viaje: Cobertura internacional por accidentes
- Protección contra fraude: Responsabilidad $0 en compras no reconocidas

### Requisitos de Contratación
1. Ser mayor de 18 años
2. Ingresos mínimos: ${10000 + idx * 5000} MXN mensuales
3. Identificación oficial vigente
4. Comprobante de domicilio no mayor a 3 meses
5. Sin registros negativos en Buró de Crédito
"""
    return contenido

def generar_documento_inversion(idx, variante):
    rendimientos = ["4.5%", "6.8%", "8.2%", "10.5%", "12.0%"]
    plazos_min = ["28 días", "90 días", "180 días", "1 año", "3 años"]
    
    contenido = f"""# Fondo de Inversión {variante}

## Prospecto de Información

### Objetivo de Inversión
El Fondo {variante} busca ofrecer rendimientos superiores a la tasa de referencia TIIE + {1 + idx % 4} puntos porcentuales, invirtiendo en instrumentos de {['deuda gubernamental','deuda corporativa','renta variable nacional','renta variable internacional','instrumentos mixtos'][idx % 5]}.

### Rendimientos Históricos
- Rendimiento último año: {rendimientos[idx % len(rendimientos)]} neto
- Rendimiento promedio 3 años: {float(rendimientos[idx % len(rendimientos)].replace('%','')) - 0.5}%
- Rendimiento promedio 5 años: {float(rendimientos[idx % len(rendimientos)].replace('%','')) - 1.0}%
- Benchmark: TIIE a 28 días + {2 + idx % 3} pp

### Condiciones de Inversión
- Monto mínimo de apertura: ${1000 * (idx + 1)} MXN
- Monto mínimo de aportación: $500 MXN
- Plazo mínimo de permanencia: {plazos_min[idx % len(plazos_min)]}
- Liquidez: {['diaria','semanal','mensual','al vencimiento','48 horas'][idx % 5]}
- Comisión por administración: {0.5 + idx * 0.3}% anual sobre el saldo

### Perfil de Riesgo
- Nivel de riesgo: {['bajo','moderado','medio','alto','muy alto'][idx % 5]}
- Horizonte recomendado: {['corto plazo','mediano plazo','largo plazo'][idx % 3]}
- Calificación: {['AAA','AA+','AA','A+','A'][idx % 5]} por Standard & Poor's

### Composición del Portafolio
| Instrumento | Porcentaje |
|-------------|-----------|
| CETES | {30 - idx * 3}% |
| Bonos corporativos | {20 + idx * 2}% |
| Acciones | {10 + idx * 4}% |
| Instrumentos bancarios | {15 - idx}% |
| Otros | {25 - idx * 2}% |

### Información Regulatoria
- Operadora: Operadora de Fondos XYZ, S.A. de C.V.
- Regulador: Comisión Nacional Bancaria y de Valores (CNBV)
- Clave de pizarra: XYZ-{variante.upper()[:3]}{idx}
- Los rendimientos pasados no garantizan rendimientos futuros
"""
    return contenido

print("Plantillas de documentos definidas correctamente")
```

4. Ejecutar la generación masiva y guardar con metadatos:

```python
# Celda 3: Generación del corpus de 50+ documentos
variantes_credito = ["Residencial Plus", "Mi Primera Casa", "Vivienda Flexible", 
                     "Hipoteca Verde", "Casa Segura", "Hogar Premium",
                     "Vivienda Joven", "Hipoteca Digital"]
variantes_tarjeta = ["Platinum Rewards", "Gold Travel", "Classic", 
                     "Black Infinite", "Cashback Plus", "Digital First",
                     "Empresarial", "Universitaria", "Mujer"]
variantes_inversion = ["Renta Fija MX", "Crecimiento Global", "Balanceado",
                       "Agresivo", "Conservador", "ESG Sustentable",
                       "Tecnología", "Deuda Soberana"]

documentos_generados = []

# Generar créditos hipotecarios
for idx, variante in enumerate(variantes_credito):
    contenido = generar_documento_credito_hipotecario(idx, variante)
    metadata = {
        "tipo_producto": "credito",
        "categoria": "hipotecario",
        "nombre_producto": f"Crédito Hipotecario {variante}",
        "fecha_vigencia": "2024-06-01",
        "entidad": "Banco Financiero Nacional",
        "doc_source": f"credito_hipotecario_{idx:02d}.md"
    }
    doc_path = CORPUS_DIR / f"credito_hipotecario_{idx:02d}.md"
    doc_path.write_text(contenido, encoding="utf-8")
    
    meta_path = CORPUS_DIR / f"credito_hipotecario_{idx:02d}.json"
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    
    documentos_generados.append({"path": str(doc_path), "metadata": metadata})

# Generar tarjetas
for idx, variante in enumerate(variantes_tarjeta):
    contenido = generar_documento_tarjeta(idx, variante)
    metadata = {
        "tipo_producto": "tarjeta",
        "categoria": "credito",
        "nombre_producto": f"Tarjeta {variante}",
        "fecha_vigencia": "2024-07-01",
        "entidad": "Banco Financiero Nacional",
        "doc_source": f"tarjeta_{idx:02d}.md"
    }
    doc_path = CORPUS_DIR / f"tarjeta_{idx:02d}.md"
    doc_path.write_text(contenido, encoding="utf-8")
    
    meta_path = CORPUS_DIR / f"tarjeta_{idx:02d}.json"
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    
    documentos_generados.append({"path": str(doc_path), "metadata": metadata})

# Generar fondos de inversión
for idx, variante in enumerate(variantes_inversion):
    contenido = generar_documento_inversion(idx, variante)
    metadata = {
        "tipo_producto": "inversion",
        "categoria": "fondo",
        "nombre_producto": f"Fondo {variante}",
        "fecha_vigencia": "2024-05-15",
        "entidad": "Operadora de Fondos XYZ",
        "doc_source": f"fondo_inversion_{idx:02d}.md"
    }
    doc_path = CORPUS_DIR / f"fondo_inversion_{idx:02d}.md"
    doc_path.write_text(contenido, encoding="utf-8")
    
    meta_path = CORPUS_DIR / f"fondo_inversion_{idx:02d}.json"
    meta_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    
    documentos_generados.append({"path": str(doc_path), "metadata": metadata})

print(f"Total documentos generados: {len(documentos_generados)}")
print(f"Documentos previos del Lab 1 + nuevos = corpus total de 50+ documentos")

# Verificar conteo total en el directorio
total_md = len(list(CORPUS_DIR.glob("*.md")))
print(f"Archivos .md en corpus: {total_md}")
```

### Resultado Esperado

```
Total documentos generados: 25
Documentos previos del Lab 1 + nuevos = corpus total de 50+ documentos
Archivos .md en corpus: 30  (o más, dependiendo del Lab 1)
```

> **Nota:** Si necesitas alcanzar 50+ documentos, repite las variantes con sufijos adicionales o genera documentos de cuentas de ahorro y seguros con plantillas similares. El código se puede extender fácilmente.

### Verificación

```bash
ls ~/rag-financiero-workshop/data/corpus/*.md | wc -l
# Debe mostrar 50 o más archivos
```

---

## Paso 3: Estrategias de Chunking Avanzadas

### Objetivo
Implementar y comparar tres estrategias de chunking (fijo, semántico y jerárquico) para determinar cuál produce mejor calidad de recuperación en documentos financieros.

### Instrucciones

1. Implementar las tres estrategias de chunking:

```python
# Celda 4: Imports para chunking
import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from sentence_transformers import SentenceTransformer
import numpy as np

# Modelo para chunking semántico
semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
tokenizer = tiktoken.encoding_for_model("gpt-4o")

def contar_tokens(texto: str) -> int:
    return len(tokenizer.encode(texto))
```

2. Estrategia 1 — Chunking fijo (baseline del Lab 1):

```python
# Celda 5: Chunking fijo
def chunking_fijo(texto: str, chunk_size: int = 500, chunk_overlap: int = 100) -> list:
    """Chunking fijo con RecursiveCharacterTextSplitter (baseline Lab 1)."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = splitter.split_text(texto)
    return chunks

# Probar con un documento de ejemplo
doc_ejemplo = (CORPUS_DIR / "credito_hipotecario_00.md").read_text(encoding="utf-8")
chunks_fijo = chunking_fijo(doc_ejemplo)
print(f"Chunking fijo: {len(chunks_fijo)} chunks")
print(f"Tamaño promedio: {np.mean([len(c) for c in chunks_fijo]):.0f} caracteres")
print(f"Tokens promedio: {np.mean([contar_tokens(c) for c in chunks_fijo]):.0f}")
```

3. Estrategia 2 — Chunking semántico:

```python
# Celda 6: Chunking semántico basado en similitud de oraciones
def chunking_semantico(texto: str, umbral_similitud: float = 0.75, max_chunk_tokens: int = 300) -> list:
    """
    Agrupa oraciones consecutivas por similitud semántica.
    Cuando la similitud entre oraciones consecutivas cae por debajo del umbral,
    se crea un nuevo chunk.
    """
    # Dividir en oraciones
    oraciones = [s.strip() for s in texto.replace('\n', ' ').split('. ') if s.strip()]
    
    if len(oraciones) <= 1:
        return [texto]
    
    # Obtener embeddings de cada oración
    embeddings = semantic_model.encode(oraciones)
    
    chunks = []
    chunk_actual = [oraciones[0]]
    
    for i in range(1, len(oraciones)):
        # Calcular similitud coseno entre oración actual y la anterior
        sim = np.dot(embeddings[i], embeddings[i-1]) / (
            np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[i-1])
        )
        
        # Verificar si el chunk actual excede el límite de tokens
        texto_chunk_actual = '. '.join(chunk_actual)
        tokens_actuales = contar_tokens(texto_chunk_actual)
        
        if sim < umbral_similitud or tokens_actuales > max_chunk_tokens:
            chunks.append('. '.join(chunk_actual) + '.')
            chunk_actual = [oraciones[i]]
        else:
            chunk_actual.append(oraciones[i])
    
    # Agregar el último chunk
    if chunk_actual:
        chunks.append('. '.join(chunk_actual) + '.')
    
    return chunks

chunks_semantico = chunking_semantico(doc_ejemplo)
print(f"Chunking semántico: {len(chunks_semantico)} chunks")
print(f"Tamaño promedio: {np.mean([len(c) for c in chunks_semantico]):.0f} caracteres")
print(f"Tokens promedio: {np.mean([contar_tokens(c) for c in chunks_semantico]):.0f}")
```

4. Estrategia 3 — Chunking jerárquico por secciones Markdown:

```python
# Celda 7: Chunking jerárquico por secciones del documento
def chunking_jerarquico(texto: str, max_chunk_size: int = 800) -> list:
    """
    Divide el documento respetando la estructura de secciones Markdown.
    Cada sección (H2, H3) se convierte en un chunk independiente,
    preservando el contexto jerárquico en el texto.
    """
    headers_to_split_on = [
        ("#", "titulo"),
        ("##", "seccion"),
        ("###", "subseccion"),
    ]
    
    md_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False
    )
    
    md_chunks = md_splitter.split_text(texto)
    
    # Post-procesar: si algún chunk es muy largo, subdividir
    chunks_finales = []
    fallback_splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_chunk_size,
        chunk_overlap=50
    )
    
    for doc in md_chunks:
        contenido = doc.page_content
        if len(contenido) > max_chunk_size:
            sub_chunks = fallback_splitter.split_text(contenido)
            chunks_finales.extend(sub_chunks)
        else:
            chunks_finales.append(contenido)
    
    return chunks_finales

chunks_jerarquico = chunking_jerarquico(doc_ejemplo)
print(f"Chunking jerárquico: {len(chunks_jerarquico)} chunks")
print(f"Tamaño promedio: {np.mean([len(c) for c in chunks_jerarquico]):.0f} caracteres")
print(f"Tokens promedio: {np.mean([contar_tokens(c) for c in chunks_jerarquico]):.0f}")
```

5. Comparar distribuciones de tamaño:

```python
# Celda 8: Visualización comparativa de estrategias de chunking
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(15, 4))

estrategias = [
    ("Fijo (500 chars)", chunks_fijo),
    ("Semántico", chunks_semantico),
    ("Jerárquico", chunks_jerarquico)
]

for ax, (nombre, chunks) in zip(axes, estrategias):
    tokens = [contar_tokens(c) for c in chunks]
    ax.hist(tokens, bins=15, edgecolor='black', alpha=0.7)
    ax.set_title(nombre)
    ax.set_xlabel("Tokens por chunk")
    ax.set_ylabel("Frecuencia")
    ax.axvline(np.mean(tokens), color='red', linestyle='--', label=f'Media: {np.mean(tokens):.0f}')
    ax.legend()

plt.tight_layout()
plt.savefig("~/rag-financiero-workshop/lab02/comparacion_chunking.png", dpi=100)
plt.show()
print("Gráfico guardado en lab02/comparacion_chunking.png")
```

### Resultado Esperado

```
Chunking fijo: ~8-12 chunks
Chunking semántico: ~10-18 chunks  
Chunking jerárquico: ~6-10 chunks
```

Un gráfico con tres histogramas mostrando la distribución de tokens por chunk para cada estrategia.

### Verificación

Confirmar que las tres estrategias producen chunks no vacíos y con tamaños razonables (entre 50 y 500 tokens en promedio).

---

## Paso 4: Indexación en Qdrant con Colección Optimizada

### Objetivo
Crear la colección `financial_products_optimized` con payload indexing y poblarla usando la estrategia de chunking jerárquico (la que mejor preserva contexto financiero).

### Instrucciones

1. Crear la colección optimizada en Qdrant:

```python
# Celda 9: Crear colección optimizada
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PayloadSchemaType,
    PointStruct
)
from openai import OpenAI

qdrant = QdrantClient(host="localhost", port=6333)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

COLLECTION_NAME = "financial_products_optimized"
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# Crear colección con vector_size=1536 (text-embedding-3-small)
qdrant.recreate_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE
    )
)

# Crear payload indexes para filtrado eficiente
qdrant.create_payload_index(
    collection_name=COLLECTION_NAME,
    field_name="tipo_producto",
    field_schema=PayloadSchemaType.KEYWORD
)
qdrant.create_payload_index(
    collection_name=COLLECTION_NAME,
    field_name="categoria",
    field_schema=PayloadSchemaType.KEYWORD
)
qdrant.create_payload_index(
    collection_name=COLLECTION_NAME,
    field_name="fecha_vigencia",
    field_schema=PayloadSchemaType.KEYWORD
)

print(f"Colección '{COLLECTION_NAME}' creada con payload indexing")
collection_info = qdrant.get_collection(COLLECTION_NAME)
print(f"Vector size: {collection_info.config.params.vectors.size}")
print(f"Distance: {collection_info.config.params.vectors.distance}")
```

2. Procesar todos los documentos con chunking jerárquico e indexar:

```python
# Celda 10: Indexar corpus completo con embeddings
import time

def obtener_embedding(texto: str) -> list:
    """Obtener embedding usando OpenAI text-embedding-3-small."""
    response = openai_client.embeddings.create(
        input=texto,
        model=EMBEDDING_MODEL
    )
    return response.data[0].embedding

# Procesar todos los documentos .md del corpus
all_md_files = sorted(CORPUS_DIR.glob("*.md"))
print(f"Procesando {len(all_md_files)} documentos...")

puntos = []
chunk_id_global = 0

for doc_path in all_md_files:
    contenido = doc_path.read_text(encoding="utf-8")
    
    # Buscar metadata asociada
    meta_path = doc_path.with_suffix(".json")
    if meta_path.exists():
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    else:
        metadata = {
            "tipo_producto": "general",
            "categoria": "general",
            "fecha_vigencia": "2024-01-01",
            "doc_source": doc_path.name
        }
    
    # Aplicar chunking jerárquico
    chunks = chunking_jerarquico(contenido)
    
    for i, chunk in enumerate(chunks):
        if len(chunk.strip()) < 20:  # Ignorar chunks muy pequeños
            continue
        
        embedding = obtener_embedding(chunk)
        
        punto = PointStruct(
            id=chunk_id_global,
            vector=embedding,
            payload={
                "content": chunk,
                "chunk_id": f"{doc_path.stem}_chunk_{i:03d}",
                "doc_source": metadata.get("doc_source", doc_path.name),
                "tipo_producto": metadata.get("tipo_producto", "general"),
                "categoria": metadata.get("categoria", "general"),
                "fecha_vigencia": metadata.get("fecha_vigencia", "2024-01-01"),
                "chunk_index": i,
                "total_chunks_doc": len(chunks)
            }
        )
        puntos.append(punto)
        chunk_id_global += 1
    
    # Subir en lotes de 100 para eficiencia
    if len(puntos) >= 100:
        qdrant.upsert(collection_name=COLLECTION_NAME, points=puntos)
        print(f"  Indexados {chunk_id_global} chunks hasta ahora...")
        puntos = []
        time.sleep(0.5)  # Rate limiting para API de OpenAI

# Subir puntos restantes
if puntos:
    qdrant.upsert(collection_name=COLLECTION_NAME, points=puntos)

print(f"\n✓ Indexación completa: {chunk_id_global} chunks en '{COLLECTION_NAME}'")

# Verificar
collection_info = qdrant.get_collection(COLLECTION_NAME)
print(f"Puntos en colección: {collection_info.points_count}")
```

### Resultado Esperado

```
Procesando 50 documentos...
  Indexados 100 chunks hasta ahora...
  Indexados 200 chunks hasta ahora...
  ...

✓ Indexación completa: ~300-500 chunks en 'financial_products_optimized'
Puntos en colección: 350 (aproximado)
```

### Verificación

```python
# Verificar búsqueda con filtro
results = qdrant.search(
    collection_name=COLLECTION_NAME,
    query_vector=obtener_embedding("tasa de interés hipotecario"),
    query_filter={
        "must": [{"key": "tipo_producto", "match": {"value": "credito"}}]
    },
    limit=3
)
print(f"Resultados filtrados por 'credito': {len(results)}")
for r in results:
    print(f"  Score: {r.score:.4f} | {r.payload['doc_source']}")
```

---

## Paso 5: Configuración de Elasticsearch para Búsqueda BM25

### Objetivo
Indexar el corpus financiero en Elasticsearch con mappings optimizados para búsqueda léxica BM25 en español.

### Instrucciones

1. Crear el índice con mappings apropiados:

```python
# Celda 11: Configurar Elasticsearch
from elasticsearch import Elasticsearch

es = Elasticsearch(
    hosts=[f"http://{os.getenv('ELASTICSEARCH_HOST', 'localhost')}:{os.getenv('ELASTICSEARCH_PORT', '9200')}"]
)

# Verificar conexión
print(f"Elasticsearch conectado: {es.info()['version']['number']}")

INDEX_NAME = "financial_products_bm25"

# Eliminar índice si existe (para recrear limpio)
if es.indices.exists(index=INDEX_NAME):
    es.indices.delete(index=INDEX_NAME)

# Crear índice con mappings explícitos
mappings = {
    "mappings": {
        "properties": {
            "content": {
                "type": "text",
                "analyzer": "spanish"
            },
            "tipo_producto": {
                "type": "keyword"
            },
            "categoria": {
                "type": "keyword"
            },
            "chunk_id": {
                "type": "keyword"
            },
            "doc_source": {
                "type": "keyword"
            }
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    }
}

es.indices.create(index=INDEX_NAME, body=mappings)
print(f"Índice '{INDEX_NAME}' creado con analyzer español")
```

2. Indexar los mismos chunks en Elasticsearch:

```python
# Celda 12: Indexar chunks en Elasticsearch
from elasticsearch.helpers import bulk

def generar_acciones_bulk():
    """Genera documentos para indexación bulk en Elasticsearch."""
    chunk_id = 0
    for doc_path in sorted(CORPUS_DIR.glob("*.md")):
        contenido = doc_path.read_text(encoding="utf-8")
        
        meta_path = doc_path.with_suffix(".json")
        if meta_path.exists():
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        else:
            metadata = {
                "tipo_producto": "general",
                "categoria": "general",
                "doc_source": doc_path.name
            }
        
        chunks = chunking_jerarquico(contenido)
        
        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 20:
                continue
            
            yield {
                "_index": INDEX_NAME,
                "_id": chunk_id,
                "_source": {
                    "content": chunk,
                    "chunk_id": f"{doc_path.stem}_chunk_{i:03d}",
                    "tipo_producto": metadata.get("tipo_producto", "general"),
                    "categoria": metadata.get("categoria", "general"),
                    "doc_source": metadata.get("doc_source", doc_path.name)
                }
            }
            chunk_id += 1

# Ejecutar indexación bulk
success, errors = bulk(es, generar_acciones_bulk(), raise_on_error=False)
print(f"✓ Documentos indexados en Elasticsearch: {success}")
if errors:
    print(f"  Errores: {len(errors)}")

# Refrescar índice para que los documentos estén disponibles
es.indices.refresh(index=INDEX_NAME)

# Verificar conteo
count = es.count(index=INDEX_NAME)
print(f"Total documentos en índice: {count['count']}")
```

3. Probar búsqueda BM25:

```python
# Celda 13: Probar búsqueda BM25
query_test = "¿Cuál es la tasa de interés del crédito hipotecario?"

response = es.search(
    index=INDEX_NAME,
    body={
        "query": {
            "match": {
                "content": {
                    "query": query_test,
                    "analyzer": "spanish"
                }
            }
        },
        "size": 5
    }
)

print(f"Búsqueda BM25: '{query_test}'")
print(f"Resultados: {response['hits']['total']['value']}")
for hit in response['hits']['hits'][:3]:
    print(f"  Score: {hit['_score']:.4f} | {hit['_source']['doc_source']}")
    print(f"  Contenido: {hit['_source']['content'][:100]}...")
    print()
```

### Resultado Esperado

```
Elasticsearch conectado: 8.13.4
Índice 'financial_products_bm25' creado con analyzer español
✓ Documentos indexados en Elasticsearch: ~350
Total documentos en índice: 350

Búsqueda BM25: '¿Cuál es la tasa de interés del crédito hipotecario?'
Resultados: 45
  Score: 12.3456 | credito_hipotecario_00.md
  Contenido: ### Tasa de Interés - Tasa fija anual: 8.5% - CAT promedio: 11.0%...
```

### Verificación

```bash
curl -s "http://localhost:9200/financial_products_bm25/_count" | python3 -m json.tool
```

---

## Paso 6: Implementación de Búsqueda Híbrida con EnsembleRetriever

### Objetivo
Combinar la búsqueda semántica de Qdrant con la búsqueda léxica de Elasticsearch usando LangChain EnsembleRetriever, e integrar Cohere Rerank para reordenamiento.

### Instrucciones

1. Configurar los retrievers individuales:

```python
# Celda 14: Configurar retrievers con LangChain
from langchain_community.vectorstores import Qdrant as LangchainQdrant
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document
from langchain.retrievers import EnsembleRetriever

# Retriever semántico (Qdrant)
embeddings = OpenAIEmbeddings(
    model=EMBEDDING_MODEL,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

qdrant_vectorstore = LangchainQdrant(
    client=qdrant,
    collection_name=COLLECTION_NAME,
    embeddings=embeddings
)
qdrant_retriever = qdrant_vectorstore.as_retriever(search_kwargs={"k": 10})

# Retriever léxico (Elasticsearch BM25)
from langchain_community.retrievers import ElasticSearchBM25Retriever

class ElasticsearchBM25Retriever:
    """Wrapper personalizado para Elasticsearch BM25 compatible con LangChain."""
    
    def __init__(self, es_client, index_name, k=10):
        self.es = es_client
        self.index_name = index_name
        self.k = k
    
    def get_relevant_documents(self, query: str) -> list:
        response = self.es.search(
            index=self.index_name,
            body={
                "query": {
                    "match": {
                        "content": {
                            "query": query,
                            "analyzer": "spanish"
                        }
                    }
                },
                "size": self.k
            }
        )
        
        docs = []
        for hit in response['hits']['hits']:
            doc = Document(
                page_content=hit['_source']['content'],
                metadata={
                    "source": hit['_source'].get('doc_source', ''),
                    "tipo_producto": hit['_source'].get('tipo_producto', ''),
                    "score_bm25": hit['_score']
                }
            )
            docs.append(doc)
        return docs
    
    async def aget_relevant_documents(self, query: str) -> list:
        return self.get_relevant_documents(query)

es_retriever = ElasticsearchBM25Retriever(es, INDEX_NAME, k=10)

print("✓ Retrievers configurados: Qdrant (semántico) + Elasticsearch (BM25)")
```

2. Crear el EnsembleRetriever con diferentes valores de alpha:

```python
# Celda 15: EnsembleRetriever con pesos configurables
from langchain.retrievers import EnsembleRetriever

def crear_ensemble_retriever(alpha_semantico: float = 0.5):
    """
    Crea un EnsembleRetriever con pesos configurables.
    alpha_semantico: peso para búsqueda semántica (1-alpha para BM25)
    """
    # LangChain EnsembleRetriever usa weights para cada retriever
    ensemble = EnsembleRetriever(
        retrievers=[qdrant_retriever, es_retriever],
        weights=[alpha_semantico, 1 - alpha_semantico]
    )
    return ensemble

# Probar con diferentes alphas
alphas = [0.3, 0.5, 0.7]
query_prueba = "¿Qué requisitos necesito para un crédito hipotecario y cuál es la tasa?"

print(f"Query: {query_prueba}\n")
for alpha in alphas:
    ensemble = crear_ensemble_retriever(alpha)
    docs = ensemble.get_relevant_documents(query_prueba)
    print(f"Alpha={alpha} (semántico={alpha}, BM25={1-alpha})")
    print(f"  Documentos recuperados: {len(docs)}")
    for i, doc in enumerate(docs[:3]):
        print(f"  [{i+1}] {doc.metadata.get('source', 'N/A')[:40]} | {doc.page_content[:80]}...")
    print()
```

3. Integrar Cohere Rerank:

```python
# Celda 16: Integración de Cohere Rerank
import cohere

cohere_client = cohere.Client(api_key=os.getenv("COHERE_API_KEY"))
RERANK_MODEL = os.getenv("COHERE_RERANK_MODEL", "rerank-english-v3.0")

def rerank_documentos(query: str, documentos: list, top_n: int = 5) -> list:
    """
    Reordena documentos usando Cohere Rerank.
    """
    if not documentos:
        return []
    
    # Preparar textos para reranking
    textos = [doc.page_content for doc in documentos]
    
    response = cohere_client.rerank(
        model=RERANK_MODEL,
        query=query,
        documents=textos,
        top_n=top_n
    )
    
    # Reordenar documentos según scores de reranking
    docs_reranked = []
    for result in response.results:
        doc = documentos[result.index]
        doc.metadata["rerank_score"] = result.relevance_score
        docs_reranked.append(doc)
    
    return docs_reranked

# Probar pipeline completo: búsqueda híbrida + reranking
ensemble_05 = crear_ensemble_retriever(0.5)
docs_hibridos = ensemble_05.get_relevant_documents(query_prueba)
docs_reranked = rerank_documentos(query_prueba, docs_hibridos, top_n=5)

print(f"Query: {query_prueba}")
print(f"\nResultados después de Reranking (top 5):")
for i, doc in enumerate(docs_reranked):
    print(f"  [{i+1}] Score: {doc.metadata['rerank_score']:.4f}")
    print(f"      Fuente: {doc.metadata.get('source', 'N/A')}")
    print(f"      Contenido: {doc.page_content[:100]}...")
    print()
```

4. Experimentar con diferentes alphas y medir calidad:

```python
# Celda 17: Comparación de configuraciones de alpha
preguntas_prueba = [
    "¿Cuál es la tasa de interés del crédito hipotecario Residencial Plus?",
    "¿Qué comisiones tiene la tarjeta Platinum Rewards?",
    "¿Cuál es el rendimiento del fondo Crecimiento Global?",
    "Requisitos para obtener un crédito de vivienda",
    "¿Qué seguros incluye la tarjeta Gold Travel?",
    "Monto mínimo para invertir en el fondo Conservador",
    "Política de pago anticipado en hipotecas",
    "Programa de puntos y recompensas de tarjetas",
    "Perfil de riesgo del fondo Agresivo",
    "Comisión por apertura de crédito hipotecario"
]

resultados_alpha = {}

for alpha in [0.3, 0.5, 0.7]:
    ensemble = crear_ensemble_retriever(alpha)
    scores_rerank = []
    
    for pregunta in preguntas_prueba:
        docs = ensemble.get_relevant_documents(pregunta)
        docs_rr = rerank_documentos(pregunta, docs, top_n=3)
        if docs_rr:
            scores_rerank.append(docs_rr[0].metadata.get("rerank_score", 0))
    
    avg_score = np.mean(scores_rerank) if scores_rerank else 0
    resultados_alpha[alpha] = avg_score
    print(f"Alpha={alpha}: Score promedio de reranking (top-1) = {avg_score:.4f}")

mejor_alpha = max(resultados_alpha, key=resultados_alpha.get)
print(f"\n✓ Mejor configuración: alpha={mejor_alpha}")
```

### Resultado Esperado

```
Alpha=0.3: Score promedio de reranking (top-1) = 0.82xx
Alpha=0.5: Score promedio de reranking (top-1) = 0.85xx
Alpha=0.7: Score promedio de reranking (top-1) = 0.83xx

✓ Mejor configuración: alpha=0.5
```

### Verificación

El score promedio de reranking del top-1 debe ser superior a 0.7 para al menos dos configuraciones de alpha, indicando que el sistema recupera documentos relevantes.

---

## Paso 7: Pipeline RAG Completo con Generación

### Objetivo
Construir el pipeline RAG end-to-end que integra búsqueda híbrida, reranking y generación con GPT-4o para responder consultas financieras.

### Instrucciones

1. Implementar el pipeline RAG optimizado:

```python
# Celda 18: Pipeline RAG optimizado completo
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

llm = ChatOpenAI(
    model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o"),
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

PROMPT_TEMPLATE = """Eres un asesor financiero experto. Responde la pregunta del cliente 
basándote EXCLUSIVAMENTE en el contexto proporcionado. Si la información no está disponible 
en el contexto, indica claramente que no tienes esa información.

CONTEXTO:
{context}

PREGUNTA DEL CLIENTE:
{question}

INSTRUCCIONES:
- Responde de forma precisa y profesional
- Cita cifras específicas cuando estén disponibles (tasas, montos, plazos)
- Si hay condiciones o requisitos, listarlos claramente
- No inventes información que no esté en el contexto

RESPUESTA:"""

prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

def pipeline_rag_optimizado(pregunta: str, alpha: float = 0.5, top_k_rerank: int = 5) -> dict:
    """
    Pipeline RAG completo: Búsqueda híbrida → Reranking → Generación.
    """
    # Paso 1: Búsqueda híbrida
    ensemble = crear_ensemble_retriever(alpha)
    docs_hibridos = ensemble.get_relevant_documents(pregunta)
    
    # Paso 2: Reranking con Cohere
    docs_reranked = rerank_documentos(pregunta, docs_hibridos, top_n=top_k_rerank)
    
    # Paso 3: Construir contexto
    contexto = "\n\n---\n\n".join([doc.page_content for doc in docs_reranked])
    
    # Paso 4: Generar respuesta
    chain = prompt | llm
    respuesta = chain.invoke({
        "context": contexto,
        "question": pregunta
    })
    
    return {
        "pregunta": pregunta,
        "respuesta": respuesta.content,
        "contextos": [doc.page_content for doc in docs_reranked],
        "fuentes": [doc.metadata.get("source", "") for doc in docs_reranked],
        "scores_rerank": [doc.metadata.get("rerank_score", 0) for doc in docs_reranked]
    }

# Probar el pipeline
resultado = pipeline_rag_optimizado(
    "¿Cuáles son los requisitos y la tasa de interés para el crédito hipotecario Residencial Plus?"
)

print(f"Pregunta: {resultado['pregunta']}")
print(f"\nRespuesta:\n{resultado['respuesta']}")
print(f"\nFuentes utilizadas: {resultado['fuentes'][:3]}")
print(f"Scores de reranking: {[f'{s:.3f}' for s in resultado['scores_rerank'][:3]]}")
```

### Resultado Esperado

Una respuesta coherente que cite la tasa de interés específica y los requisitos del producto, basándose en los documentos recuperados.

### Verificación

La respuesta debe contener datos específicos del documento (tasa, plazo, monto) y no debe incluir información inventada.

---

## Paso 8: Evaluación con RAGAS

### Objetivo
Evaluar cuantitativamente el sistema RAG optimizado usando el framework RAGAS y comparar las métricas contra el pipeline básico del Lab 1.

### Instrucciones

1. Construir el dataset de evaluación:

```python
# Celda 19: Dataset de evaluación con 20 pares pregunta-respuesta-contexto
evaluation_dataset = [
    {
        "question": "¿Cuál es la tasa de interés anual del Crédito Hipotecario Residencial Plus?",
        "ground_truth": "La tasa fija anual del Crédito Hipotecario Residencial Plus es de 8.5%.",
        "expected_product": "credito_hipotecario_00"
    },
    {
        "question": "¿Cuál es el enganche mínimo requerido para el crédito Mi Primera Casa?",
        "ground_truth": "El enganche mínimo para el crédito Mi Primera Casa es del 15% del valor del inmueble.",
        "expected_product": "credito_hipotecario_01"
    },
    {
        "question": "¿Cuánto es la anualidad de la tarjeta Platinum Rewards?",
        "ground_truth": "La anualidad de la tarjeta Platinum Rewards es $0 el primer año.",
        "expected_product": "tarjeta_00"
    },
    {
        "question": "¿Cuál es la tasa de interés ordinaria de la tarjeta Gold Travel?",
        "ground_truth": "La tasa de interés ordinaria de la tarjeta Gold Travel es 28% anual.",
        "expected_product": "tarjeta_01"
    },
    {
        "question": "¿Cuál es el rendimiento del último año del Fondo Renta Fija MX?",
        "ground_truth": "El rendimiento del último año del Fondo Renta Fija MX es 4.5% neto.",
        "expected_product": "fondo_inversion_00"
    },
    {
        "question": "¿Cuál es el monto mínimo para invertir en el Fondo Crecimiento Global?",
        "ground_truth": "El monto mínimo de apertura del Fondo Crecimiento Global es $2,000 MXN.",
        "expected_product": "fondo_inversion_01"
    },
    {
        "question": "¿Qué nivel de riesgo tiene el Fondo Agresivo?",
        "ground_truth": "El Fondo Agresivo tiene un nivel de riesgo alto.",
        "expected_product": "fondo_inversion_03"
    },
    {
        "question": "¿Cuántos puntos acumula la tarjeta Classic por cada $10 de compra?",
        "ground_truth": "La tarjeta Classic acumula 3 puntos por cada $10 MXN de compra.",
        "expected_product": "tarjeta_02"
    },
    {
        "question": "¿Cuál es el plazo máximo del Crédito Hipotecario Vivienda Flexible?",
        "ground_truth": "El plazo máximo del Crédito Hipotecario Vivienda Flexible es de 20 años.",
        "expected_product": "credito_hipotecario_02"
    },
    {
        "question": "¿Cuál es la comisión por disposición de efectivo en tarjetas de crédito?",
        "ground_truth": "La comisión por disposición de efectivo es del 6% del monto dispuesto.",
        "expected_product": "tarjeta_00"
    },
    {
        "question": "¿Tiene penalización por pago anticipado el crédito hipotecario?",
        "ground_truth": "No hay penalización por pago anticipado después del primer año.",
        "expected_product": "credito_hipotecario_00"
    },
    {
        "question": "¿Cuál es la calificación crediticia del Fondo Balanceado?",
        "ground_truth": "El Fondo Balanceado tiene calificación AA por Standard & Poor's.",
        "expected_product": "fondo_inversion_02"
    },
    {
        "question": "¿Qué antigüedad laboral se requiere para el crédito Hipoteca Verde?",
        "ground_truth": "Se requiere una antigüedad laboral mínima de 4 años para el crédito Hipoteca Verde.",
        "expected_product": "credito_hipotecario_03"
    },
    {
        "question": "¿Cuál es el límite de crédito de la tarjeta Black Infinite?",
        "ground_truth": "El límite de crédito de la tarjeta Black Infinite es desde $500,000 MXN.",
        "expected_product": "tarjeta_03"
    },
    {
        "question": "¿Cuál es la liquidez del Fondo Conservador?",
        "ground_truth": "El Fondo Conservador tiene liquidez al vencimiento.",
        "expected_product": "fondo_inversion_04"
    },
    {
        "question": "¿Cuál es el seguro de compras protegidas de las tarjetas?",
        "ground_truth": "El seguro de compras protegidas cubre hasta $50,000 MXN por evento.",
        "expected_product": "tarjeta_00"
    },
    {
        "question": "¿Cuánto es el monto máximo del crédito Casa Segura?",
        "ground_truth": "El monto máximo del crédito Casa Segura es $5,000,000 MXN.",
        "expected_product": "credito_hipotecario_04"
    },
    {
        "question": "¿Cuál es el horizonte recomendado del Fondo ESG Sustentable?",
        "ground_truth": "El horizonte recomendado del Fondo ESG Sustentable es de corto plazo.",
        "expected_product": "fondo_inversion_05"
    },
    {
        "question": "¿Cuáles son los ingresos mínimos para la tarjeta Empresarial?",
        "ground_truth": "Los ingresos mínimos para la tarjeta Empresarial son $40,000 MXN mensuales.",
        "expected_product": "tarjeta_06"
    },
    {
        "question": "¿Cuál es la comisión por administración del Fondo Tecnología?",
        "ground_truth": "La comisión por administración del Fondo Tecnología es 2.3% anual sobre el saldo.",
        "expected_product": "fondo_inversion_06"
    }
]

print(f"Dataset de evaluación: {len(evaluation_dataset)} preguntas")
```

2. Ejecutar el pipeline sobre el dataset de evaluación:

```python
# Celda 20: Generar respuestas para evaluación
import time

def ejecutar_evaluacion(pipeline_fn, nombre_config: str) -> dict:
    """Ejecuta el pipeline sobre el dataset de evaluación."""
    questions = []
    answers = []
    contexts = []
    ground_truths = []
    
    for i, item in enumerate(evaluation_dataset):
        print(f"  Procesando {i+1}/{len(evaluation_dataset)}: {item['question'][:50]}...")
        
        resultado = pipeline_fn(item["question"])
        
        questions.append(item["question"])
        answers.append(resultado["respuesta"])
        contexts.append(resultado["contextos"][:3])  # Top 3 contextos
        ground_truths.append(item["ground_truth"])
        
        time.sleep(1)  # Rate limiting
    
    return {
        "config": nombre_config,
        "questions": questions,
        "answers": answers,
        "contexts": contexts,
        "ground_truths": ground_truths
    }

# Pipeline optimizado (híbrido + reranking)
print("Ejecutando evaluación: RAG Optimizado (híbrido + reranking)...")
eval_optimizado = ejecutar_evaluacion(
    lambda q: pipeline_rag_optimizado(q, alpha=0.5, top_k_rerank=5),
    "RAG Híbrido + Reranking"
)
print(f"✓ Evaluación completada para configuración optimizada")
```

3. Ejecutar evaluación RAGAS:

```python
# Celda 21: Evaluación con RAGAS
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision
from datasets import Dataset

def preparar_dataset_ragas(eval_data: dict) -> Dataset:
    """Convierte los datos de evaluación al formato requerido por RAGAS."""
    return Dataset.from_dict({
        "question": eval_data["questions"],
        "answer": eval_data["answers"],
        "contexts": eval_data["contexts"],
        "ground_truth": eval_data["ground_truths"]
    })

# Evaluar configuración optimizada
dataset_optimizado = preparar_dataset_ragas(eval_optimizado)

print("Ejecutando evaluación RAGAS (esto puede tomar varios minutos)...")
resultado_ragas_optimizado = evaluate(
    dataset=dataset_optimizado,
    metrics=[faithfulness, answer_relevancy, context_precision]
)

print(f"\n{'='*60}")
print(f"RESULTADOS RAGAS - {eval_optimizado['config']}")
print(f"{'='*60}")
print(f"  Faithfulness:       {resultado_ragas_optimizado['faithfulness']:.4f}")
print(f"  Answer Relevancy:   {resultado_ragas_optimizado['answer_relevancy']:.4f}")
print(f"  Context Precision:  {resultado_ragas_optimizado['context_precision']:.4f}")
print(f"{'='*60}")
```

4. Crear pipeline básico (simulando Lab 1) para comparación:

```python
# Celda 22: Pipeline básico (baseline) para comparación
def pipeline_rag_basico(pregunta: str) -> dict:
    """
    Pipeline RAG básico similar al Lab 1: solo búsqueda vectorial sin reranking.
    Usa la colección 'financial_products_basic' del Lab 1.
    """
    # Búsqueda solo semántica en colección básica
    results = qdrant.search(
        collection_name="financial_products_basic",
        query_vector=obtener_embedding(pregunta),
        limit=5
    )
    
    contextos = [r.payload.get("content", "") for r in results if r.payload.get("content")]
    
    if not contextos:
        # Fallback a colección optimizada sin reranking
        results = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=obtener_embedding(pregunta),
            limit=5
        )
        contextos = [r.payload.get("content", "") for r in results]
    
    contexto = "\n\n---\n\n".join(contextos[:3])
    
    chain = prompt | llm
    respuesta = chain.invoke({
        "context": contexto,
        "question": pregunta
    })
    
    return {
        "pregunta": pregunta,
        "respuesta": respuesta.content,
        "contextos": contextos[:3],
        "fuentes": [],
        "scores_rerank": []
    }

# Evaluar pipeline básico
print("Ejecutando evaluación: RAG Básico (solo semántico, sin reranking)...")
eval_basico = ejecutar_evaluacion(pipeline_rag_basico, "RAG Básico (Lab 1)")

dataset_basico = preparar_dataset_ragas(eval_basico)
resultado_ragas_basico = evaluate(
    dataset=dataset_basico,
    metrics=[faithfulness, answer_relevancy, context_precision]
)

print(f"\n{'='*60}")
print(f"RESULTADOS RAGAS - {eval_basico['config']}")
print(f"{'='*60}")
print(f"  Faithfulness:       {resultado_ragas_basico['faithfulness']:.4f}")
print(f"  Answer Relevancy:   {resultado_ragas_basico['answer_relevancy']:.4f}")
print(f"  Context Precision:  {resultado_ragas_basico['context_precision']:.4f}")
print(f"{'='*60}")
```

5. Generar dashboard comparativo:

```python
# Celda 23: Dashboard comparativo de métricas
import pandas as pd
import matplotlib.pyplot as plt

# Compilar resultados
metricas = {
    "Métrica": ["Faithfulness", "Answer Relevancy", "Context Precision"],
    "RAG Básico (Lab 1)": [
        resultado_ragas_basico['faithfulness'],
        resultado_ragas_basico['answer_relevancy'],
        resultado_ragas_basico['context_precision']
    ],
    "RAG Optimizado (Híbrido + Rerank)": [
        resultado_ragas_optimizado['faithfulness'],
        resultado_ragas_optimizado['answer_relevancy'],
        resultado_ragas_optimizado['context_precision']
    ]
}

df_metricas = pd.DataFrame(metricas)
print("\nTabla Comparativa de Métricas RAGAS:")
print(df_metricas.to_string(index=False))

# Calcular mejora porcentual
for metrica in ["Faithfulness", "Answer Relevancy", "Context Precision"]:
    basico = df_metricas[df_metricas["Métrica"] == metrica]["RAG Básico (Lab 1)"].values[0]
    optimizado = df_metricas[df_metricas["Métrica"] == metrica]["RAG Optimizado (Híbrido + Rerank)"].values[0]
    if basico > 0:
        mejora = ((optimizado - basico) / basico) * 100
        print(f"  {metrica}: +{mejora:.1f}% de mejora")

# Visualización
fig, ax = plt.subplots(figsize=(10, 6))

x = range(len(metricas["Métrica"]))
width = 0.35

bars1 = ax.bar([i - width/2 for i in x], metricas["RAG Básico (Lab 1)"], 
               width, label="RAG Básico (Lab 1)", color='#3498db', alpha=0.8)
bars2 = ax.bar([i + width/2 for i in x], metricas["RAG Optimizado (Híbrido + Rerank)"], 
               width, label="RAG Optimizado (Híbrido + Rerank)", color='#2ecc71', alpha=0.8)

ax.set_xlabel("Métricas RAGAS")
ax.set_ylabel("Score (0-1)")
ax.set_title("Comparación de Rendimiento: RAG Básico vs RAG Optimizado")
ax.set_xticks(x)
ax.set_xticklabels(metricas["Métrica"])
ax.legend()
ax.set_ylim(0, 1.1)

# Agregar valores sobre las barras
for bar in bars1 + bars2:
    height = bar.get_height()
    ax.annotate(f'{height:.3f}',
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3), textcoords="offset points",
                ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.savefig(Path("~/rag-financiero-workshop/lab02/dashboard_comparativo.png").expanduser(), dpi=150)
plt.show()
print("\n✓ Dashboard guardado en lab02/dashboard_comparativo.png")
```

6. Guardar reporte de métricas:

```python
# Celda 24: Guardar reporte final
reporte = {
    "fecha_evaluacion": datetime.datetime.now().isoformat(),
    "configuraciones_evaluadas": [
        {
            "nombre": "RAG Básico (Lab 1)",
            "descripcion": "Búsqueda semántica pura con Qdrant, chunking fijo, sin reranking",
            "metricas": {
                "faithfulness": resultado_ragas_basico['faithfulness'],
                "answer_relevancy": resultado_ragas_basico['answer_relevancy'],
                "context_precision": resultado_ragas_basico['context_precision']
            }
        },
        {
            "nombre": "RAG Optimizado (Híbrido + Rerank)",
            "descripcion": "Búsqueda híbrida (Qdrant+ES, alpha=0.5), chunking jerárquico, Cohere Rerank",
            "metricas": {
                "faithfulness": resultado_ragas_optimizado['faithfulness'],
                "answer_relevancy": resultado_ragas_optimizado['answer_relevancy'],
                "context_precision": resultado_ragas_optimizado['context_precision']
            }
        }
    ],
    "dataset_evaluacion": {
        "total_preguntas": len(evaluation_dataset),
        "categorias_cubiertas": ["credito", "tarjeta", "inversion"]
    },
    "configuracion_optima": {
        "alpha": 0.5,
        "chunking": "jerarquico",
        "reranker": "cohere-rerank-english-v3.0",
        "top_k_rerank": 5
    }
}

reporte_path = Path("~/rag-financiero-workshop/lab02/reporte_evaluacion.json").expanduser()
reporte_path.write_text(json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"✓ Reporte guardado en: {reporte_path}")

# Guardar DataFrame como CSV
csv_path = Path("~/rag-financiero-workshop/lab02/metricas_comparativas.csv").expanduser()
df_metricas.to_csv(csv_path, index=False)
print(f"✓ CSV de métricas guardado en: {csv_path}")
```

### Resultado Esperado

```
Tabla Comparativa de Métricas RAGAS:
         Métrica  RAG Básico (Lab 1)  RAG Optimizado (Híbrido + Rerank)
    Faithfulness              0.72xx                             0.88xx
Answer Relevancy              0.68xx                             0.85xx
Context Precision             0.65xx                             0.82xx

  Faithfulness: +22.x% de mejora
  Answer Relevancy: +25.x% de mejora
  Context Precision: +26.x% de mejora

✓ Dashboard guardado en lab02/dashboard_comparativo.png
✓ Reporte guardado en: .../lab02/reporte_evaluacion.json
```

### Verificación

- El gráfico de barras muestra mejoras visibles del pipeline optimizado sobre el básico
- Las métricas del pipeline optimizado deben superar 0.75 en al menos dos de las tres dimensiones
- Los archivos `reporte_evaluacion.json` y `metricas_comparativas.csv` existen y contienen datos válidos

---

## Validación y Pruebas Finales

Ejecutar las siguientes verificaciones para confirmar que todos los componentes del laboratorio funcionan correctamente:

```python
# Celda 25: Validación integral del laboratorio
print("=" * 60)
print("VALIDACIÓN INTEGRAL - LAB 02")
print("=" * 60)

# 1. Verificar contenedores Docker
import
