---LAB_START---
LAB_ID: 01-00-01
---MARKDOWN---
# Implementación de un Sistema RAG para Consulta de Productos Financieros

## 1. Metadatos

| Campo | Valor |
|-------|-------|
| **Duración** | 105 minutos |
| **Complejidad** | Media |
| **Nivel Bloom** | Aplicar |

## 2. Descripción General

En este laboratorio construirás desde cero un pipeline RAG (Retrieval-Augmented Generation) completo aplicado al dominio de productos financieros. Partirás de un corpus de documentos sintéticos sobre créditos, tarjetas, cuentas e inversiones, los procesarás en fragmentos, generarás embeddings vectoriales con OpenAI, los almacenarás en Qdrant y finalmente construirás una cadena de consulta que combine recuperación semántica con generación aumentada usando GPT-4o. El laboratorio culmina con una comparación directa entre respuestas con y sin RAG para evidenciar la reducción de alucinaciones.

## 3. Objetivos de Aprendizaje

- [ ] Comprender la arquitectura fundamental de un sistema RAG y articular sus componentes: ingesta, indexación vectorial, recuperación y generación aumentada
- [ ] Implementar un pipeline RAG completo usando LangChain, OpenAI y Qdrant para consultar información sobre productos financieros
- [ ] Generar embeddings con `text-embedding-3-small` y almacenarlos en una colección Qdrant configurada correctamente
- [ ] Construir un retriever semántico integrado con ChatOpenAI (GPT-4o) mediante una chain RAG funcional
- [ ] Contrastar respuestas con RAG versus sin contexto externo, documentando diferencias en precisión y alucinaciones

## 4. Prerrequisitos

### Conocimientos requeridos

| Conocimiento | Nivel |
|---|---|
| Python: funciones, clases, manejo de archivos, entornos virtuales | Intermedio |
| Concepto de API REST y manejo de API keys | Básico |
| Qué es un modelo de lenguaje (LLM) | Conceptual |
| Vectores de embeddings y similitud coseno | Conceptual |

### Accesos requeridos

- Cuenta activa en OpenAI con créditos disponibles y API key generada
- Docker Desktop instalado y funcionando (v26.1.4+)
- Conexión a Internet estable

## 5. Entorno del Laboratorio

### Hardware mínimo

| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| CPU | 4 núcleos x86_64 | 8 núcleos |
| RAM | 16 GB | 32 GB |
| Disco | 20 GB SSD libres | 20 GB SSD |
| GPU | No requerida | Opcional |

### Software requerido

| Componente | Versión |
|---|---|
| Python | 3.11.9 |
| pip | 24.0+ |
| Docker Desktop | 26.1.4 |
| Docker Compose | 2.27.1 |
| Qdrant (contenedor) | 1.9.4 |

### Configuración inicial del directorio de trabajo

```bash
# Crear estructura de directorios
mkdir -p ~/rag-financiero-workshop/lab01
mkdir -p ~/rag-financiero-workshop/data/corpus
mkdir -p ~/rag-financiero-workshop/volumes/qdrant_storage
cd ~/rag-financiero-workshop
```

## 6. Instrucciones Paso a Paso

---

### Paso 1: Configuración del entorno virtual y dependencias

**Objetivo:** Crear un entorno Python aislado con todas las bibliotecas necesarias para el pipeline RAG.

**Instrucciones:**

1. Crea el entorno virtual en el directorio raíz del workshop:

```bash
cd ~/rag-financiero-workshop
python3.11 -m venv .venv
source .venv/bin/activate
```

2. Crea el archivo `requirements.txt` en `~/rag-financiero-workshop/`:

```text
langchain==0.2.6
langchain-openai==0.1.14
langchain-community==0.2.6
qdrant-client==1.9.1
openai==1.35.7
pypdf==4.2.0
tiktoken==0.7.0
python-dotenv==1.0.1
jupyter==1.0.0
```

3. Instala las dependencias:

```bash
pip install -r requirements.txt
```

4. Crea el archivo de variables de entorno `~/rag-financiero-workshop/.env`:

```bash
cat > ~/rag-financiero-workshop/.env << 'EOF'
OPENAI_API_KEY=<tu-clave-openai-aqui>
COHERE_API_KEY=<tu-clave-cohere-aqui>
QDRANT_HOST=localhost
QDRANT_PORT=6333
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o
COHERE_RERANK_MODEL=rerank-english-v3.0
EOF
```

> **⚠️ Importante:** Reemplaza `<tu-clave-openai-aqui>` con tu API key real de OpenAI.

**Salida esperada:**

```
Successfully installed langchain-0.2.6 langchain-openai-0.1.14 ...
```

**Verificación:**

```bash
python -c "import langchain; import qdrant_client; print(f'LangChain: {langchain.__version__}')"
```

Debe imprimir: `LangChain: 0.2.6`

---

### Paso 2: Levantar Qdrant con Docker Compose

**Objetivo:** Desplegar el contenedor de Qdrant como base de datos vectorial persistente.

**Instrucciones:**

1. Crea el archivo `docker-compose.yml` en `~/rag-financiero-workshop/`:

```yaml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:v1.9.4
    container_name: qdrant-financiero
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./volumes/qdrant_storage:/qdrant/storage
    restart: unless-stopped
```

2. Levanta el contenedor:

```bash
cd ~/rag-financiero-workshop
docker compose up -d
```

3. Verifica que el contenedor esté corriendo:

```bash
docker ps --filter name=qdrant-financiero
```

4. Verifica la conectividad con la API de Qdrant:

```bash
curl -s http://localhost:6333/collections | python -m json.tool
```

**Salida esperada:**

```json
{
    "result": {
        "collections": []
    },
    "status": "ok",
    "time": 0.000...
}
```

**Verificación:** El campo `"status"` debe ser `"ok"` y `"collections"` debe ser una lista vacía (aún no hemos creado ninguna).

---

### Paso 3: Crear el corpus de documentos financieros sintéticos

**Objetivo:** Generar los documentos de texto que simularán folletos de productos financieros reales para alimentar el sistema RAG.

**Instrucciones:**

1. Crea los archivos del corpus en `~/rag-financiero-workshop/data/corpus/`. Ejecuta los siguientes comandos:

```bash
cd ~/rag-financiero-workshop/data/corpus
```

2. Crea el documento de la tarjeta de crédito:

```bash
cat > tarjeta_visa_platinum.txt << 'EOF'
FICHA DE PRODUCTO: TARJETA DE CRÉDITO VISA PLATINUM

Producto: Tarjeta de Crédito Visa Platinum
Emisor: Banco Financiero Nacional
Fecha de vigencia: 01 de enero de 2024

CARACTERÍSTICAS PRINCIPALES:
- Línea de crédito: desde $5,000 hasta $150,000 según perfil crediticio
- Tasa de interés anual: 28.5% sin promoción, 18.9% con nómina domiciliada
- CAT promedio: 42.3% sin IVA (informativo, sujeto a cambios)
- Anualidad: $2,800 (primer año bonificado si facturación mensual supera $8,000)
- Fecha de corte: día 15 de cada mes
- Fecha límite de pago: día 5 del mes siguiente al corte

BENEFICIOS:
- Programa de recompensas: 1.5 puntos por cada dólar de compra
- Acceso a salas VIP en aeropuertos (2 accesos gratuitos por trimestre)
- Seguro de viajero incluido para viajes internacionales (cobertura hasta $500,000)
- Seguro de protección de compras: cubre daño o robo de artículos comprados con la tarjeta hasta 90 días por un monto máximo de $10,000 por evento
- Meses sin intereses: 3, 6, 9 y 12 MSI en comercios participantes
- Asistencia en carretera las 24 horas sin costo adicional

REQUISITOS DE SOLICITUD:
- Edad mínima: 21 años
- Ingreso mínimo mensual comprobable: $15,000
- Antigüedad laboral mínima: 1 año en empleo actual
- Historial crediticio: sin atrasos mayores a 30 días en los últimos 12 meses
- Identificación oficial vigente (INE/pasaporte)
- Comprobante de domicilio no mayor a 3 meses

COMISIONES:
- Disposición de efectivo en cajero: 6.5% del monto + IVA (mínimo $150)
- Pago tardío: $590 por evento
- Reposición de plástico por robo o extravío: $250
- Consulta de saldo en cajeros de otros bancos: $35

PENALIDADES:
- Pago mínimo no realizado: se cobra comisión por pago tardío más intereses moratorios al doble de la tasa ordinaria (57% anual)
- Exceder línea de crédito: comisión de $450 por evento y posible reducción de línea
- Tres meses consecutivos sin pago mínimo: cancelación de la tarjeta y envío a buró de crédito con estatus de cartera vencida

CONTACTO Y ATENCIÓN:
- Línea de atención 24/7: 800-555-0100
- Aplicación móvil: BFN Wallet (disponible iOS y Android)
- Sucursales: más de 450 a nivel nacional
EOF
```

3. Crea el documento del crédito hipotecario:

```bash
cat > credito_hipotecario.txt << 'EOF'
FICHA DE PRODUCTO: CRÉDITO HIPOTECARIO RESIDENCIAL

Producto: Crédito Hipotecario Tasa Fija
Emisor: Banco Financiero Nacional
Fecha de vigencia: 01 de marzo de 2024

CARACTERÍSTICAS PRINCIPALES:
- Monto mínimo de crédito: $500,000
- Monto máximo de crédito: $15,000,000
- Plazo: 10, 15, 20 o 25 años
- Tasa de interés fija anual: 10.99% (para clientes con nómina: 9.85%)
- CAT promedio: 13.2% sin IVA
- Enganche mínimo: 20% del valor de la propiedad
- Aforo máximo: 80% del valor de avalúo
- Tipo de propiedad: vivienda residencial nueva o usada

BENEFICIOS:
- Tasa fija durante toda la vida del crédito (sin sorpresas)
- Posibilidad de prepagos parciales o totales sin penalización a partir del tercer año
- Seguro de vida incluido que cubre el saldo insoluto
- Seguro de daños a la propiedad incluido en la mensualidad
- Deducibilidad fiscal de intereses reales pagados (según legislación vigente)
- Programa de lealtad: reducción de 0.25 puntos porcentuales en tasa después de 5 años de pago puntual

REQUISITOS DE SOLICITUD:
- Edad: entre 25 y 64 años al momento de la solicitud (edad máxima al término del crédito: 79 años)
- Ingreso mínimo mensual comprobable: $35,000
- Antigüedad laboral: mínimo 2 años (1 año en empleo actual)
- Historial crediticio: score mínimo de 680 puntos en buró de crédito
- Enganche comprobable del 20% mínimo
- Identificación oficial vigente
- Últimos 3 estados de cuenta bancarios
- Última declaración anual de impuestos
- Avalúo de la propiedad (coordinado por el banco, costo: $3,500 a $8,000 según valor)

COMISIONES:
- Comisión por apertura: 1.0% del monto del crédito (financiable)
- Avalúo: según valor de la propiedad ($3,500 - $8,000)
- Gastos notariales: entre 4% y 7% del valor de la propiedad (a cargo del cliente)
- Penalización por prepago total antes del tercer año: 2% del saldo insoluto

TABLA DE PAGOS MENSUALES ESTIMADOS (crédito de $2,000,000):
- Plazo 10 años: $27,450 mensuales
- Plazo 15 años: $22,180 mensuales
- Plazo 20 años: $19,850 mensuales
- Plazo 25 años: $18,600 mensuales

PENALIDADES:
- Pago tardío: intereses moratorios equivalentes a 1.5 veces la tasa ordinaria sobre el monto vencido
- Más de 3 mensualidades vencidas: inicio de proceso de recuperación judicial
- Incumplimiento de seguro de daños: el banco puede contratar el seguro y cargarlo a la cuenta del cliente

CONTACTO:
- Centro hipotecario: 800-555-0200
- Simulador en línea: www.bfn.com/hipotecario
- Sucursales especializadas: 85 centros hipotecarios a nivel nacional
EOF
```

4. Crea el documento de la cuenta de ahorro:

```bash
cat > cuenta_ahorro_premium.txt << 'EOF'
FICHA DE PRODUCTO: CUENTA DE AHORRO PREMIUM

Producto: Cuenta de Ahorro Premium Plus
Emisor: Banco Financiero Nacional
Fecha de vigencia: 15 de febrero de 2024

CARACTERÍSTICAS PRINCIPALES:
- Saldo mínimo de apertura: $10,000
- Saldo promedio mínimo mensual para evitar comisión: $25,000
- Rendimiento anual (GAT real): 8.5% antes de impuestos para saldos mayores a $100,000
- Rendimiento anual (GAT real): 6.2% antes de impuestos para saldos entre $25,000 y $100,000
- Rendimiento anual (GAT real): 3.8% antes de impuestos para saldos menores a $25,000
- Periodicidad de pago de intereses: mensual (día 28 de cada mes)
- Disponibilidad de fondos: inmediata (hasta 6 retiros sin comisión al mes)
- Moneda: pesos mexicanos (MXN)

BENEFICIOS:
- Rendimientos competitivos escalonados según saldo
- Tarjeta de débito Visa sin costo anual
- Transferencias SPEI ilimitadas sin comisión
- Acceso a banca en línea y aplicación móvil
- Domiciliación de servicios sin costo
- Protección IPAB hasta 400,000 UDIs (aproximadamente $3,100,000)
- Sin plazo forzoso: disponibilidad total del dinero en cualquier momento
- Estado de cuenta mensual digital sin costo

REQUISITOS DE APERTURA:
- Edad mínima: 18 años
- Identificación oficial vigente (INE/pasaporte)
- Comprobante de domicilio no mayor a 3 meses
- CURP
- Depósito inicial mínimo de $10,000
- No se requiere comprobante de ingresos

COMISIONES:
- Manejo de cuenta (si saldo promedio < $25,000): $150 mensuales
- Retiros adicionales después del sexto en el mes: $50 por operación
- Reposición de tarjeta de débito: $150
- Emisión de cheques de caja: $100 por documento
- Consulta de saldo en cajeros de otros bancos: $20

PENALIDADES:
- No existen penalidades por cancelación anticipada
- Saldo menor a $1,000 durante 6 meses consecutivos: cancelación automática de la cuenta con notificación previa de 30 días

FISCALIDAD:
- Los intereses generados están sujetos a retención de ISR provisional del 0.15% sobre el capital
- El banco emite constancia fiscal anual para declaración de impuestos

CONTACTO:
- Línea de atención: 800-555-0300
- Apertura en línea: www.bfn.com/ahorro-premium
- Sucursales: más de 450 a nivel nacional
EOF
```

5. Crea el documento del fondo de inversión:

```bash
cat > fondo_inversion_renta_fija.txt << 'EOF'
FICHA DE PRODUCTO: FONDO DE INVERSIÓN EN RENTA FIJA

Producto: BFN Fondo Estabilidad - Renta Fija Gubernamental
Clave de pizarra: BFN-ESTAB
Emisor/Operadora: BFN Asset Management
Fecha de vigencia: 01 de abril de 2024
Clasificación: Fondo de Deuda Gubernamental a Mediano Plazo

OBJETIVO DE INVERSIÓN:
Ofrecer a los inversionistas un rendimiento superior a la tasa de referencia (CETES 28 días) mediante la inversión en instrumentos de deuda gubernamental mexicana con horizonte de mediano plazo (1-3 años), manteniendo un perfil de riesgo bajo.

CARACTERÍSTICAS PRINCIPALES:
- Inversión mínima inicial: $50,000
- Inversión mínima adicional: $10,000
- Horizonte de inversión recomendado: 1 a 3 años
- Rendimiento neto anualizado (últimos 12 meses): 11.2%
- Rendimiento neto anualizado (últimos 3 años): 9.8% promedio
- Benchmark: CETES 28 días + 150 puntos base
- Calificación de riesgo: AAA/1 (calidad crediticia sobresaliente, sensibilidad baja a tasas)
- Liquidez: T+1 (disponibilidad al día hábil siguiente de la solicitud de retiro)
- Valuación diaria: precio de la acción publicado cada día hábil a las 18:00 hrs

COMPOSICIÓN DE LA CARTERA (al 31 de marzo de 2024):
- Bonos M (tasa fija gubernamental): 45%
- CETES (corto plazo): 25%
- Udibonos (indexados a inflación): 20%
- Reportos gubernamentales: 8%
- Efectivo y equivalentes: 2%

RÉGIMEN DE INVERSIÓN:
- Mínimo 80% en instrumentos de deuda gubernamental mexicana
- Máximo 20% en instrumentos de deuda bancaria con calificación mínima AA
- No se permite inversión en renta variable ni derivados especulativos
- Duración promedio de la cartera: entre 1 y 3 años

COMISIONES:
- Comisión por administración: 0.85% anual sobre activos netos (cobro diario prorrateado)
- Comisión por distribución: 0.15% anual
- Sin comisión de entrada ni de salida
- Sin comisión por rendimiento (performance fee)
- Comisión total anual: 1.00%

RIESGOS:
- Riesgo de mercado: sensibilidad a movimientos en tasas de interés (duración moderada)
- Riesgo de crédito: bajo (instrumentos gubernamentales y bancarios de alta calificación)
- Riesgo de liquidez: bajo (mercado secundario activo para instrumentos gubernamentales)
- No existe garantía de rendimiento; los rendimientos pasados no garantizan rendimientos futuros

PERFIL DEL INVERSIONISTA:
- Inversionistas conservadores que buscan rendimientos superiores a instrumentos bancarios tradicionales
- Horizonte mínimo recomendado: 1 año
- Tolerancia al riesgo: baja
- Objetivo: preservación de capital con crecimiento moderado

FISCALIDAD:
- Persona física: retención provisional de ISR sobre ganancias realizadas
- Persona moral: acumulación de rendimientos al resultado fiscal del ejercicio
- El fondo proporciona constancia fiscal anual

CONTACTO:
- Mesa de operaciones: 800-555-0400
- Portal de fondos: www.bfn.com/fondos/bfn-estab
- Horario de operaciones: lunes a viernes 8:00 - 14:00 hrs
EOF
```

6. Crea el documento del seguro de vida:

```bash
cat > seguro_vida_proteccion.txt << 'EOF'
FICHA DE PRODUCTO: SEGURO DE VIDA PROTECCIÓN FAMILIAR

Producto: Seguro de Vida Protección Familiar Plus
Emisor: BFN Seguros (subsidiaria de Banco Financiero Nacional)
Fecha de vigencia: 01 de mayo de 2024
Registro CNSF: S0042-0156-2024

CARACTERÍSTICAS PRINCIPALES:
- Suma asegurada: desde $500,000 hasta $20,000,000
- Tipo de seguro: Vida temporal renovable (plazo de 1 año con renovación automática)
- Edad de contratación: 18 a 65 años
- Edad máxima de cobertura: 75 años
- Moneda: pesos mexicanos (MXN) o dólares americanos (USD)
- Pago de prima: mensual, trimestral, semestral o anual

COBERTURAS INCLUIDAS:
- Fallecimiento por cualquier causa: 100% de la suma asegurada
- Muerte accidental: 200% de la suma asegurada (doble indemnización)
- Invalidez total y permanente: 100% de la suma asegurada (exención de pago de primas)
- Enfermedades graves (cobertura anticipada): 25% de la suma asegurada al diagnóstico de cualquiera de las 25 enfermedades cubiertas (incluye cáncer, infarto al miocardio, EVC, insuficiencia renal)
- Gastos funerarios: $50,000 adicionales a la suma asegurada

COBERTURAS OPCIONALES:
- Protección de ingresos por incapacidad temporal: 60% del ingreso mensual hasta por 12 meses ($350/mes adicional por cada $10,000 de ingreso cubierto)
- Cobertura de educación para hijos: pago de colegiatura hasta por 4 años en caso de fallecimiento del asegurado (prima adicional según monto)
- Asistencia médica telefónica 24/7: sin costo adicional (incluida)

PRIMAS MENSUALES ESTIMADAS (suma asegurada de $3,000,000):
- Hombre 30 años, no fumador: $485/mes
- Mujer 30 años, no fumadora: $420/mes
- Hombre 40 años, no fumador: $780/mes
- Mujer 40 años, no fumadora: $650/mes
- Hombre 50 años, no fumador: $1,450/mes
- Mujer 50 años, no fumadora: $1,180/mes
- Fumadores: prima incrementada en 40%

REQUISITOS DE CONTRATACIÓN:
- Identificación oficial vigente
- Cuestionario médico (para sumas aseguradas hasta $5,000,000)
- Examen médico completo (para sumas aseguradas mayores a $5,000,000)
- Comprobante de ingresos (para sumas aseguradas mayores a $10,000,000)
- Designación de beneficiarios (mínimo 1, máximo 5)
- Período de espera: 30 días para enfermedad, sin espera para accidente

EXCLUSIONES:
- Suicidio durante los primeros 2 años de vigencia
- Participación en actos delictivos
- Guerra, terrorismo o conflictos armados
- Práctica profesional de deportes extremos (salvo contratación de cobertura adicional)
- Enfermedades preexistentes no declaradas

PENALIDADES Y CANCELACIÓN:
- Período de libre examen: 30 días desde la contratación (devolución total de prima)
- Cancelación después de 30 días: sin penalidad, cobertura vigente hasta fin del período pagado
- Falta de pago: período de gracia de 30 días; después se cancela la póliza sin valor de rescate

CONTACTO:
- Centro de atención seguros: 800-555-0500
- Portal de seguros: www.bfn.com/seguros/vida
- Red de hospitales y laboratorios: más de 2,000 a nivel nacional
EOF
```

**Salida esperada:**

```bash
ls ~/rag-financiero-workshop/data/corpus/
```

```
cuenta_ahorro_premium.txt
credito_hipotecario.txt
fondo_inversion_renta_fija.txt
seguro_vida_proteccion.txt
tarjeta_visa_platinum.txt
```

**Verificación:** Confirma que hay 5 archivos y que cada uno tiene contenido:

```bash
wc -l ~/rag-financiero-workshop/data/corpus/*.txt
```

Debe mostrar entre 50 y 80 líneas por archivo.

---

### Paso 4: Verificar conectividad con la API de OpenAI

**Objetivo:** Confirmar que las credenciales de OpenAI funcionan correctamente antes de proceder con la generación de embeddings.

**Instrucciones:**

1. Crea el archivo `~/rag-financiero-workshop/lab01/test_openai.py`:

```bash
mkdir -p ~/rag-financiero-workshop/lab01
cd ~/rag-financiero-workshop/lab01
```

```python
# test_openai.py
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Test de embeddings
response = client.embeddings.create(
    input="prueba de conexión para productos financieros",
    model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
)
print(f"✅ Embeddings OK - Dimensiones: {len(response.data[0].embedding)}")
print(f"   Modelo: {response.model}")

# Test de chat
chat_response = client.chat.completions.create(
    model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o"),
    messages=[{"role": "user", "content": "Responde solo 'OK' si recibes este mensaje."}],
    max_tokens=5
)
print(f"✅ Chat OK - Respuesta: {chat_response.choices[0].message.content}")
print(f"   Modelo: {chat_response.model}")
```

2. Ejecuta el test:

```bash
cd ~/rag-financiero-workshop/lab01
python test_openai.py
```

**Salida esperada:**

```
✅ Embeddings OK - Dimensiones: 1536
   Modelo: text-embedding-3-small
✅ Chat OK - Respuesta: OK
   Modelo: gpt-4o-2024-...
```

**Verificación:** Las dimensiones deben ser exactamente `1536` (requerido para la colección Qdrant que crearemos).

---

### Paso 5: Ingesta y chunking de documentos

**Objetivo:** Cargar los documentos financieros, dividirlos en fragmentos (chunks) manejables y preparar los metadatos para la indexación.

**Instrucciones:**

1. Crea el archivo `~/rag-financiero-workshop/lab01/ingesta.py`:

```python
# ingesta.py
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# --- Paso 1: Cargar documentos ---
CORPUS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'corpus')

loader = DirectoryLoader(
    CORPUS_DIR,
    glob="**/*.txt",
    loader_cls=TextLoader,
    loader_kwargs={"encoding": "utf-8"}
)

documents = loader.load()
print(f"📄 Documentos cargados: {len(documents)}")
for doc in documents:
    print(f"   - {os.path.basename(doc.metadata['source'])} ({len(doc.page_content)} caracteres)")

# --- Paso 2: Chunking con RecursiveCharacterTextSplitter ---
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""]
)

chunks = text_splitter.split_documents(documents)
print(f"\n✂️  Chunks generados: {len(chunks)}")

# --- Paso 3: Enriquecer metadatos ---
# Mapeo de archivos a tipos de producto
PRODUCT_MAP = {
    "tarjeta_visa_platinum.txt": {"tipo_producto": "tarjeta_credito", "categoria": "premium"},
    "credito_hipotecario.txt": {"tipo_producto": "credito", "categoria": "hipotecario"},
    "cuenta_ahorro_premium.txt": {"tipo_producto": "cuenta", "categoria": "ahorro"},
    "fondo_inversion_renta_fija.txt": {"tipo_producto": "inversion", "categoria": "renta_fija"},
    "seguro_vida_proteccion.txt": {"tipo_producto": "seguro", "categoria": "vida"},
}

for i, chunk in enumerate(chunks):
    source_file = os.path.basename(chunk.metadata['source'])
    product_info = PRODUCT_MAP.get(source_file, {"tipo_producto": "otro", "categoria": "general"})
    chunk.metadata.update({
        "chunk_id": f"chunk_{i:04d}",
        "tipo_producto": product_info["tipo_producto"],
        "categoria": product_info["categoria"],
        "doc_source": source_file
    })

# --- Paso 4: Estadísticas de tokens ---
encoding = tiktoken.encoding_for_model("text-embedding-3-small")
token_counts = [len(encoding.encode(chunk.page_content)) for chunk in chunks]
print(f"\n📊 Estadísticas de tokens por chunk:")
print(f"   Mínimo: {min(token_counts)}")
print(f"   Máximo: {max(token_counts)}")
print(f"   Promedio: {sum(token_counts)/len(token_counts):.1f}")
print(f"   Total tokens: {sum(token_counts)}")

# --- Mostrar ejemplo de chunk ---
print(f"\n📋 Ejemplo de chunk (primero):")
print(f"   Contenido: {chunks[0].page_content[:200]}...")
print(f"   Metadatos: {chunks[0].metadata}")

# Guardar chunks para el siguiente paso
import json
chunks_data = []
for chunk in chunks:
    chunks_data.append({
        "content": chunk.page_content,
        "metadata": chunk.metadata
    })

output_path = os.path.join(os.path.dirname(__file__), 'chunks_procesados.json')
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(chunks_data, f, ensure_ascii=False, indent=2)

print(f"\n💾 Chunks guardados en: {output_path}")
```

2. Ejecuta la ingesta:

```bash
cd ~/rag-financiero-workshop/lab01
python ingesta.py
```

**Salida esperada:**

```
📄 Documentos cargados: 5
   - tarjeta_visa_platinum.txt (1847 caracteres)
   - credito_hipotecario.txt (2156 caracteres)
   - cuenta_ahorro_premium.txt (1923 caracteres)
   - fondo_inversion_renta_fija.txt (2534 caracteres)
   - seguro_vida_proteccion.txt (2678 caracteres)

✂️  Chunks generados: 38

📊 Estadísticas de tokens por chunk:
   Mínimo: 45
   Máximo: 165
   Promedio: 112.3
   Total tokens: 4267

📋 Ejemplo de chunk (primero):
   Contenido: FICHA DE PRODUCTO: TARJETA DE CRÉDITO VISA PLATINUM...
   Metadatos: {'source': '...', 'chunk_id': 'chunk_0000', 'tipo_producto': 'tarjeta_credito', 'categoria': 'premium', 'doc_source': 'tarjeta_visa_platinum.txt'}

💾 Chunks guardados en: .../lab01/chunks_procesados.json
```

**Verificación:** Confirma que se generaron entre 30 y 50 chunks y que el archivo `chunks_procesados.json` existe.

---

### Paso 6: Generación de embeddings e indexación en Qdrant

**Objetivo:** Generar vectores de embeddings para cada chunk usando OpenAI y almacenarlos en una colección Qdrant con sus metadatos.

**Instrucciones:**

1. Crea el archivo `~/rag-financiero-workshop/lab01/indexar_qdrant.py`:

```python
# indexar_qdrant.py
import os
import sys
import json
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance, PointStruct
)

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# --- Configuración ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
COLLECTION_NAME = "financial_products_basic"
VECTOR_SIZE = 1536

# --- Inicializar clientes ---
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# --- Paso 1: Crear colección en Qdrant ---
collections = qdrant_client.get_collections().collections
existing_names = [c.name for c in collections]

if COLLECTION_NAME in existing_names:
    print(f"⚠️  Colección '{COLLECTION_NAME}' ya existe. Eliminando para recrear...")
    qdrant_client.delete_collection(COLLECTION_NAME)
    time.sleep(1)

qdrant_client.create_collection(
    collection_name=COLLECTION_NAME,
    vectors_config=VectorParams(
        size=VECTOR_SIZE,
        distance=Distance.COSINE
    )
)
print(f"✅ Colección '{COLLECTION_NAME}' creada (vector_size={VECTOR_SIZE}, distance=Cosine)")

# --- Paso 2: Cargar chunks procesados ---
chunks_path = os.path.join(os.path.dirname(__file__), 'chunks_procesados.json')
with open(chunks_path, 'r', encoding='utf-8') as f:
    chunks_data = json.load(f)

print(f"📄 Chunks a indexar: {len(chunks_data)}")

# --- Paso 3: Generar embeddings en lotes ---
BATCH_SIZE = 20
all_embeddings = []

for i in range(0, len(chunks_data), BATCH_SIZE):
    batch = chunks_data[i:i + BATCH_SIZE]
    texts = [chunk["content"] for chunk in batch]
    
    response = openai_client.embeddings.create(
        input=texts,
        model=EMBEDDING_MODEL
    )
    
    batch_embeddings = [item.embedding for item in response.data]
    all_embeddings.extend(batch_embeddings)
    print(f"   Lote {i//BATCH_SIZE + 1}: {len(batch)} embeddings generados")
    time.sleep(0.5)  # Rate limiting cortesía

print(f"\n🧮 Total embeddings generados: {len(all_embeddings)}")

# --- Paso 4: Insertar puntos en Qdrant ---
points = []
for idx, (chunk, embedding) in enumerate(zip(chunks_data, all_embeddings)):
    point = PointStruct(
        id=idx,
        vector=embedding,
        payload={
            "content": chunk["content"],
            "chunk_id": chunk["metadata"]["chunk_id"],
            "tipo_producto": chunk["metadata"]["tipo_producto"],
            "categoria": chunk["metadata"]["categoria"],
            "doc_source": chunk["metadata"]["doc_source"]
        }
    )
    points.append(point)

# Insertar en lotes
for i in range(0, len(points), BATCH_SIZE):
    batch_points = points[i:i + BATCH_SIZE]
    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=batch_points
    )
    print(f"   Insertados puntos {i} a {i + len(batch_points) - 1}")

# --- Paso 5: Verificar colección ---
collection_info = qdrant_client.get_collection(COLLECTION_NAME)
print(f"\n✅ Indexación completada:")
print(f"   Colección: {COLLECTION_NAME}")
print(f"   Puntos totales: {collection_info.points_count}")
print(f"   Estado: {collection_info.status}")
```

2. Ejecuta la indexación:

```bash
cd ~/rag-financiero-workshop/lab01
python indexar_qdrant.py
```

**Salida esperada:**

```
✅ Colección 'financial_products_basic' creada (vector_size=1536, distance=Cosine)
📄 Chunks a indexar: 38
   Lote 1: 20 embeddings generados
   Lote 2: 18 embeddings generados

🧮 Total embeddings generados: 38
   Insertados puntos 0 a 19
   Insertados puntos 20 a 37

✅ Indexación completada:
   Colección: financial_products_basic
   Puntos totales: 38
   Estado: green
```

**Verificación:**

```bash
curl -s http://localhost:6333/collections/financial_products_basic | python -m json.tool | grep points_count
```

Debe mostrar `"points_count": 38` (o el número de chunks generados).

---

### Paso 7: Construir el pipeline RAG con LangChain

**Objetivo:** Integrar el retriever semántico de Qdrant con ChatOpenAI para crear una cadena RAG funcional que responda preguntas sobre productos financieros.

**Instrucciones:**

1. Crea el archivo `~/rag-financiero-workshop/lab01/rag_pipeline.py`:

```python
# rag_pipeline.py
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Qdrant
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from qdrant_client import QdrantClient

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# --- Configuración ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = "financial_products_basic"

# --- Inicializar componentes ---
embeddings = OpenAIEmbeddings(
    model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

qdrant_client = QdrantClient(host=QDRANT_HOST, port=int(QDRANT_PORT))

vectorstore = Qdrant(
    client=qdrant_client,
    collection_name=COLLECTION_NAME,
    embeddings=embeddings
)

retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4}
)

# --- Prompt Template para RAG financiero ---
RAG_PROMPT_TEMPLATE = """Eres un asistente especializado en productos financieros del Banco Financiero Nacional.
Tu tarea es responder preguntas de los clientes usando EXCLUSIVAMENTE la información proporcionada en el contexto.

REGLAS:
1. Responde SOLO con información presente en el contexto proporcionado.
2. Si la información no está en el contexto, di explícitamente: "No tengo información suficiente en los documentos disponibles para responder esta pregunta."
3. Cita datos específicos (tasas, montos, plazos) cuando estén disponibles.
4. Sé conciso pero completo.
5. No inventes información ni hagas suposiciones.

CONTEXTO:
{context}

PREGUNTA DEL CLIENTE:
{question}

RESPUESTA:"""

prompt = PromptTemplate(
    template=RAG_PROMPT_TEMPLATE,
    input_variables=["context", "question"]
)

# --- Crear la cadena RAG ---
llm = ChatOpenAI(
    model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o"),
    temperature=0,
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True,
    chain_type_kwargs={"prompt": prompt}
)

def consultar_rag(pregunta: str) -> dict:
    """Ejecuta una consulta RAG y retorna respuesta con fuentes."""
    resultado = qa_chain.invoke({"query": pregunta})
    return {
        "pregunta": pregunta,
        "respuesta": resultado["result"],
        "fuentes": [
            {
                "contenido": doc.page_content[:200],
                "metadata": doc.metadata
            }
            for doc in resultado["source_documents"]
        ]
    }

def consultar_sin_rag(pregunta: str) -> str:
    """Consulta al LLM sin contexto externo para comparación."""
    llm_directo = ChatOpenAI(
        model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o"),
        temperature=0,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    respuesta = llm_directo.invoke(
        f"Responde la siguiente pregunta sobre productos del Banco Financiero Nacional: {pregunta}"
    )
    return respuesta.content

if __name__ == "__main__":
    # Test rápido
    pregunta_test = "¿Cuál es la tasa de interés de la tarjeta Visa Platinum?"
    
    print("=" * 70)
    print("🔍 CONSULTA CON RAG")
    print("=" * 70)
    resultado = consultar_rag(pregunta_test)
    print(f"\nPregunta: {resultado['pregunta']}")
    print(f"\nRespuesta: {resultado['respuesta']}")
    print(f"\nFuentes utilizadas: {len(resultado['fuentes'])}")
    for i, fuente in enumerate(resultado['fuentes'], 1):
        print(f"  [{i}] {fuente['metadata'].get('doc_source', 'N/A')} - {fuente['contenido'][:100]}...")
    
    print("\n" + "=" * 70)
    print("❌ CONSULTA SIN RAG (solo LLM)")
    print("=" * 70)
    respuesta_sin_rag = consultar_sin_rag(pregunta_test)
    print(f"\nPregunta: {pregunta_test}")
    print(f"\nRespuesta: {respuesta_sin_rag}")
```

2. Ejecuta el pipeline:

```bash
cd ~/rag-financiero-workshop/lab01
python rag_pipeline.py
```

**Salida esperada:**

```
======================================================================
🔍 CONSULTA CON RAG
======================================================================

Pregunta: ¿Cuál es la tasa de interés de la tarjeta Visa Platinum?

Respuesta: La tasa de interés anual de la Tarjeta de Crédito Visa Platinum es del 28.5% sin promoción. Para clientes con nómina domiciliada, la tasa preferencial es del 18.9%.

Fuentes utilizadas: 4
  [1] tarjeta_visa_platinum.txt - FICHA DE PRODUCTO: TARJETA DE CRÉDITO VISA PLATINUM...
  ...

======================================================================
❌ CONSULTA SIN RAG (solo LLM)
======================================================================

Pregunta: ¿Cuál es la tasa de interés de la tarjeta Visa Platinum?

Respuesta: No tengo información específica sobre las tasas de interés actuales de la tarjeta Visa Platinum del Banco Financiero Nacional...
```

**Verificación:** La respuesta con RAG debe citar la tasa exacta (28.5% / 18.9%) presente en el documento fuente. La respuesta sin RAG no tendrá estos datos específicos o los inventará.

---

### Paso 8: Evaluación comparativa con batería de preguntas

**Objetivo:** Ejecutar una batería de 10 preguntas sobre los productos financieros comparando las respuestas con y sin RAG para documentar la reducción de alucinaciones.

**Instrucciones:**

1. Crea el archivo `~/rag-financiero-workshop/lab01/evaluacion_comparativa.py`:

```python
# evaluacion_comparativa.py
import os
import sys
import json
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rag_pipeline import consultar_rag, consultar_sin_rag

# --- Batería de 10 preguntas de evaluación ---
PREGUNTAS_EVALUACION = [
    {
        "id": 1,
        "pregunta": "¿Cuál es la tasa de interés anual del crédito hipotecario para clientes con nómina?",
        "respuesta_esperada": "9.85%",
        "producto": "credito_hipotecario"
    },
    {
        "id": 2,
        "pregunta": "¿Cuántos puntos de recompensa otorga la tarjeta Visa Platinum por cada dólar de compra?",
        "respuesta_esperada": "1.5 puntos",
        "producto": "tarjeta_credito"
    },
    {
        "id": 3,
        "pregunta": "¿Cuál es el rendimiento anualizado del fondo BFN Estabilidad en los últimos 12 meses?",
        "respuesta_esperada": "11.2%",
        "producto": "fondo_inversion"
    },
    {
        "id": 4,
        "pregunta": "¿Cuál es el saldo mínimo para abrir la Cuenta de Ahorro Premium Plus?",
        "respuesta_esperada": "$10,000",
        "producto": "cuenta_ahorro"
    },
    {
        "id": 5,
        "pregunta": "¿Qué porcentaje de la suma asegurada se paga por muerte accidental en el seguro de vida?",
        "respuesta_esperada": "200%",
        "producto": "seguro_vida"
    },
    {
        "id": 6,
        "pregunta": "¿Cuál es la penalización por prepago total del crédito hipotecario antes del tercer año?",
        "respuesta_esperada": "2% del saldo insoluto",
        "producto": "credito_hipotecario"
    },
    {
        "id": 7,
        "pregunta": "¿Cuántos retiros mensuales sin comisión permite la cuenta de ahorro premium?",
        "respuesta_esperada": "6 retiros",
        "producto": "cuenta_ahorro"
    },
    {
        "id": 8,
        "pregunta": "¿Cuál es la comisión total anual del fondo de inversión en renta fija?",
        "respuesta_esperada": "1.00%",
        "producto": "fondo_inversion"
    },
    {
        "id": 9,
        "pregunta": "¿Cuál es la prima mensual estimada del seguro de vida para un hombre de 40 años no fumador con suma asegurada de $3,000,000?",
        "respuesta_esperada": "$780/mes",
        "producto": "seguro_vida"
    },
    {
        "id": 10,
        "pregunta": "¿Cuál es el ingreso mínimo mensual requerido para solicitar la tarjeta Visa Platinum?",
        "respuesta_esperada": "$15,000",
        "producto": "tarjeta_credito"
    }
]

def evaluar_respuesta(respuesta: str, respuesta_esperada: str) -> dict:
    """Evalúa si la respuesta contiene el dato esperado."""
    # Normalizar para comparación
    resp_lower = respuesta.lower().replace(",", "").replace("$", "").replace("%", "")
    esperada_lower = respuesta_esperada.lower().replace(",", "").replace("$", "").replace("%", "")
    
    # Extraer el valor numérico clave
    valores_esperados = [v.strip() for v in esperada_lower.split()]
    contiene_dato = any(v in resp_lower for v in valores_esperados if len(v) > 1)
    
    return {
        "contiene_dato_correcto": contiene_dato,
        "dato_esperado": respuesta_esperada
    }

def ejecutar_evaluacion():
    """Ejecuta la evaluación completa."""
    resultados = []
    
    print("=" * 80)
    print("📊 EVALUACIÓN COMPARATIVA: RAG vs. LLM sin contexto")
    print("=" * 80)
    
    correctas_rag = 0
    correctas_sin_rag = 0
    
    for item in PREGUNTAS_EVALUACION:
        print(f"\n{'─' * 80}")
        print(f"Pregunta {item['id']}: {item['pregunta']}")
        print(f"Respuesta esperada: {item['respuesta_esperada']}")
        print(f"{'─' * 80}")
        
        # Consulta CON RAG
        resultado_rag = consultar_rag(item["pregunta"])
        eval_rag = evaluar_respuesta(resultado_rag["respuesta"], item["respuesta_esperada"])
        
        print(f"\n  🟢 CON RAG: {resultado_rag['respuesta'][:200]}")
        print(f"     ✓ Dato correcto: {'SÍ ✅' if eval_rag['contiene_dato_correcto'] else 'NO ❌'}")
        
        if eval_rag["contiene_dato_correcto"]:
            correctas_rag += 1
        
        # Consulta SIN RAG
        time.sleep(1)  # Rate limiting
        respuesta_sin_rag = consultar_sin_rag(item["pregunta"])
        eval_sin_rag = evaluar_respuesta(respuesta_sin_rag, item["respuesta_esperada"])
        
        print(f"\n  🔴 SIN RAG: {respuesta_sin_rag[:200]}")
        print(f"     ✓ Dato correcto: {'SÍ ✅' if eval_sin_rag['contiene_dato_correcto'] else 'NO ❌'}")
        
        if eval_sin_rag["contiene_dato_correcto"]:
            correctas_sin_rag += 1
        
        resultados.append({
            "id": item["id"],
            "pregunta": item["pregunta"],
            "respuesta_esperada": item["respuesta_esperada"],
            "respuesta_rag": resultado_rag["respuesta"],
            "correcto_rag": eval_rag["contiene_dato_correcto"],
            "respuesta_sin_rag": respuesta_sin_rag,
            "correcto_sin_rag": eval_sin_rag["contiene_dato_correcto"],
            "fuentes_rag": [f["metadata"].get("doc_source") for f in resultado_rag["fuentes"]]
        })
        
        time.sleep(1)  # Rate limiting
    
    # --- Resumen final ---
    print("\n" + "=" * 80)
    print("📈 RESUMEN DE RESULTADOS")
    print("=" * 80)
    print(f"\n  Precisión CON RAG:  {correctas_rag}/{len(PREGUNTAS_EVALUACION)} ({correctas_rag/len(PREGUNTAS_EVALUACION)*100:.0f}%)")
    print(f"  Precisión SIN RAG:  {correctas_sin_rag}/{len(PREGUNTAS_EVALUACION)} ({correctas_sin_rag/len(PREGUNTAS_EVALUACION)*100:.0f}%)")
    print(f"  Mejora con RAG:     +{correctas_rag - correctas_sin_rag} respuestas correctas")
    
    if correctas_rag > correctas_sin_rag:
        print(f"\n  ✅ RAG demuestra una mejora significativa en precisión factual")
    
    # Guardar resultados
    output_path = os.path.join(os.path.dirname(__file__), 'resultados_evaluacion.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            "resumen": {
                "total_preguntas": len(PREGUNTAS_EVALUACION),
                "correctas_rag": correctas_rag,
                "correctas_sin_rag": correctas_sin_rag,
                "precision_rag": correctas_rag / len(PREGUNTAS_EVALUACION),
                "precision_sin_rag": correctas_sin_rag / len(PREGUNTAS_EVALUACION)
            },
            "detalle": resultados
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n  💾 Resultados guardados en: {output_path}")
    return resultados

if __name__ == "__main__":
    ejecutar_evaluacion()
```

2. Ejecuta la evaluación:

```bash
cd ~/rag-financiero-workshop/lab01
python evaluacion_comparativa.py
```

**Salida esperada (resumen):**

```
════════════════════════════════════════════════════════════════════════════════
📈 RESUMEN DE RESULTADOS
════════════════════════════════════════════════════════════════════════════════

  Precisión CON RAG:  9/10 (90%)
  Precisión SIN RAG:  0/10 (0%)
  Mejora con RAG:     +9 respuestas correctas

  ✅ RAG demuestra una mejora significativa en precisión factual

  💾 Resultados guardados en: .../lab01/resultados_evaluacion.json
```

**Verificación:** La precisión con RAG debe ser significativamente mayor (≥70%) que sin RAG (esperado ~0% dado que el corpus es sintético y el LLM no tiene acceso a estos datos inventados).

---

### Paso 9: Exploración interactiva del sistema RAG

**Objetivo:** Crear un script interactivo que permita realizar consultas ad-hoc al sistema RAG y explorar los documentos recuperados.

**Instrucciones:**

1. Crea el archivo `~/rag-financiero-workshop/lab01/consulta_interactiva.py`:

```python
# consulta_interactiva.py
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rag_pipeline import consultar_rag

def main():
    print("=" * 60)
    print("🏦 Sistema RAG - Productos Financieros BFN")
    print("=" * 60)
    print("Escribe tu pregunta sobre productos financieros.")
    print("Escribe 'salir' para terminar.\n")
    
    while True:
        pregunta = input("📝 Tu pregunta: ").strip()
        
        if pregunta.lower() in ['salir', 'exit', 'quit', 'q']:
            print("\n👋 ¡Hasta luego!")
            break
        
        if not pregunta:
            continue
        
        print("\n⏳ Procesando consulta...")
        resultado = consultar_rag(pregunta)
        
        print(f"\n💬 Respuesta:")
        print(f"   {resultado['respuesta']}")
        
        print(f"\n📚 Fuentes consultadas ({len(resultado['fuentes'])}):")
        for i, fuente in enumerate(resultado['fuentes'], 1):
            print(f"   [{i}] {fuente['metadata'].get('doc_source', 'N/A')}")
            print(f"       Tipo: {fuente['metadata'].get('tipo_producto', 'N/A')}")
            print(f"       Fragmento: {fuente['contenido'][:100]}...")
        
        print()

if __name__ == "__main__":
    main()
```

2. Ejecuta y prueba con al menos 3 consultas:

```bash
cd ~/rag-financiero-workshop/lab01
python consulta_interactiva.py
```

**Consultas sugeridas para probar:**

- "¿Qué requisitos necesito para un crédito hipotecario?"
- "¿El fondo de inversión tiene comisión de salida?"
- "¿Cuánto cuesta la anualidad de la tarjeta Visa Platinum y cómo puedo evitarla?"

**Salida esperada:**

```
🏦 Sistema RAG - Productos Financieros BFN
============================================================
Escribe tu pregunta sobre productos financieros.
Escribe 'salir' para terminar.

📝 Tu pregunta: ¿Qué requisitos necesito para un crédito hipotecario?

⏳ Procesando consulta...

💬 Respuesta:
   Para solicitar el Crédito Hipotecario Tasa Fija del Banco Financiero Nacional, necesitas cumplir los siguientes requisitos:
   - Edad: entre 25 y 64 años
   - Ingreso mínimo mensual comprobable: $35,000
   - Antigüedad laboral: mínimo 2 años (1 año en empleo actual)
   - Score mínimo de 680 puntos en buró de crédito
   - Enganche del 20% mínimo
   ...

📚 Fuentes consultadas (4):
   [1] credito_hipotecario.txt
       Tipo: credito
       Fragmento: REQUISITOS DE SOLICITUD: - Edad: entre 25 y 64 años...
```

**Verificación:** Las respuestas deben ser precisas, citar datos específicos del corpus y las fuentes deben corresponder al documento correcto.

---

### Paso 10: Documentar hallazgos y generar reporte final

**Objetivo:** Consolidar los resultados del laboratorio en un reporte que documente la arquitectura implementada, los resultados de la evaluación y las observaciones sobre el comportamiento del sistema.

**Instrucciones:**

1. Crea el archivo `~/rag-financiero-workshop/lab01/generar_reporte.py`:

```python
# generar_reporte.py
import os
import sys
import json
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# --- Cargar resultados de evaluación ---
eval_path = os.path.join(os.path.dirname(__file__), 'resultados_evaluacion.json')
with open(eval_path, 'r', encoding='utf-8') as f:
    evaluacion = json.load(f)

# --- Info de Qdrant ---
qdrant_client = QdrantClient(
    host=os.getenv("QDRANT_HOST", "localhost"),
    port=int(os.getenv("QDRANT_PORT", 6333))
)
collection_info = qdrant_client.get_collection("financial_products_basic")

# --- Generar reporte ---
reporte = f"""# Reporte del Laboratorio 01: Pipeline RAG para Productos Financieros

**Fecha:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Autor:** Estudiante

## 1. Arquitectura Implementada

### Componentes:
- **Modelo de Embeddings:** text-embedding-3-small (OpenAI) - 1536 dimensiones
- **Base de Datos Vectorial:** Qdrant v1.9.4
- **Modelo de Generación:** GPT-4o (OpenAI)
- **Framework:** LangChain 0.2.6
- **Estrategia de Chunking:** RecursiveCharacterTextSplitter (chunk_size=512, overlap=50)

### Colección Qdrant:
- **Nombre:** financial_products_basic
- **Vectores almacenados:** {collection_info.points_count}
- **Distancia:** Cosine
- **Estado:** {collection_info.status}

## 2. Corpus de Documentos

| Documento | Tipo de Producto | Categoría |
|---|---|---|
| tarjeta_visa_platinum.txt | Tarjeta de Crédito | Premium |
| credito_hipotecario.txt | Crédito | Hipotecario |
| cuenta_ahorro_premium.txt | Cuenta | Ahorro |
| fondo_inversion_renta_fija.txt | Inversión | Renta Fija |
| seguro_vida_proteccion.txt | Seguro | Vida |

## 3. Resultados de Evaluación

### Métricas Generales:
- **Preguntas evaluadas:** {evaluacion['resumen']['total_preguntas']}
- **Precisión CON RAG:** {evaluacion['resumen']['precision_rag']*100:.0f}%
- **Precisión SIN RAG:** {evaluacion['resumen']['precision_sin_rag']*100:.0f}%
- **Mejora absoluta:** +{(evaluacion['resumen']['precision_rag'] - evaluacion['resumen']['precision_sin_rag'])*100:.0f} puntos porcentuales

### Detalle por Pregunta:

| # | Producto | Correcto RAG | Correcto Sin RAG |
|---|---|---|---|
"""

for item in evaluacion['detalle']:
    rag_mark = "✅" if item['correcto_rag'] else "❌"
    sin_rag_mark = "✅" if item['correcto_sin_rag'] else "❌"
    reporte += f"| {item['id']} | {item.get('pregunta', '')[:50]}... | {rag_mark} | {sin_rag_mark} |\n"

reporte += f"""
## 4. Observaciones

### Fortalezas del sistema RAG:
1. Respuestas ancladas en datos verificables del corpus
2. Capacidad de citar tasas, montos y condiciones exactas
3. Reducción drástica de alucinaciones (de ~100% a ~{(1-evaluacion['resumen']['precision_rag'])*100:.0f}%)
4. Trazabilidad: cada respuesta indica las fuentes utilizadas

### Limitaciones identificadas:
1. Depende de la calidad del chunking (fragmentos mal cortados pueden perder contexto)
2. Búsqueda puramente semántica puede no capturar términos exactos
3. Ventana de contexto limitada a top-k=4 fragmentos
4. No maneja preguntas que requieran razonamiento sobre múltiples documentos simultáneamente

### Áreas de mejora (para Lab 02):
1. Implementar búsqueda híbrida (semántica + BM25)
2. Aplicar reranking para mejorar la relevancia de los fragmentos recuperados
3. Optimizar estrategia de chunking según tipo de documento
4. Agregar filtrado por metadatos (tipo_producto, categoría)

## 5. Artefactos Producidos

- Colección Qdrant: `financial_products_basic` ({collection_info.points_count} vectores)
- Corpus procesado: `data/corpus/` (5 documentos)
- Chunks: `lab01/chunks_procesados.json`
- Resultados: `lab01/resultados_evaluacion.json`
"""

# Guardar reporte
reporte_path = os.path.join(os.path.dirname(__file__), 'REPORTE_LAB01.md')
with open(reporte_path, 'w', encoding='utf-8') as f:
    f.write(reporte)

print(f"📋 Reporte generado: {reporte_path}")
print(f"\n{'=' * 60}")
print("✅ LABORATORIO 01 COMPLETADO EXITOSAMENTE")
print(f"{'=' * 60}")
```

2. Genera el reporte:

```bash
cd ~/rag-financiero-workshop/lab01
python generar_reporte.py
```

**Salida esperada:**

```
📋 Reporte generado: .../lab01/REPORTE_LAB01.md

============================================================
✅ LABORATORIO 01 COMPLETADO EXITOSAMENTE
============================================================
```

**Verificación:** Abre el archivo `REPORTE_LAB01.md` y confirma que contiene las métricas y observaciones correctas.

---

## 7. Validación y Pruebas

Ejecuta las siguientes verificaciones para confirmar que todo el laboratorio se completó correctamente:

```bash
cd ~/rag-financiero-workshop/lab01

# 1. Verificar que Qdrant tiene la colección con datos
echo "--- Verificación Qdrant ---"
curl -s http://localhost:6333/collections/financial_products_basic | python -c "
import json, sys
data = json.load(sys.stdin)
points = data['result']['points_count']
status = data['result']['status']
assert status == 'green', f'Estado incorrecto: {status}'
assert points >= 30, f'Muy pocos puntos: {points}'
print(f'✅ Qdrant OK: {points} puntos, estado={status}')
"

# 2. Verificar archivos generados
echo "--- Verificación de archivos ---"
for f in chunks_procesados.json resultados_evaluacion.json REPORTE_LAB01.md; do
    if [ -f "$f" ]; then
        echo "✅ $f existe"
    else
        echo "❌ $f NO encontrado"
    fi
done

# 3. Verificar que el corpus está completo
echo "--- Verificación del corpus ---"
CORPUS_COUNT=$(ls ../data/corpus/*.txt 2>/dev/null | wc -l)
if [ "$CORPUS_COUNT" -eq 5 ]; then
    echo "✅ Corpus completo: $CORPUS_COUNT documentos"
else
    echo "❌ Corpus incompleto: $CORPUS_COUNT documentos (esperados: 5)"
fi

# 4. Test de consulta RAG funcional
echo "--- Test de consulta RAG ---"
python -c "
from rag_pipeline import consultar_rag
r = consultar_rag('¿Cuál es la tasa del crédito hipotecario?')
assert '10.99' in r['respuesta'] or '9.85' in r['respuesta'], 'Respuesta no contiene tasa esperada'
print(f'✅ RAG funcional: respuesta contiene datos correctos')
"
```

**Resultado esperado:** Todas las verificaciones deben mostrar ✅.

---

## 8. Solución de Problemas

### Problema 1: Error de conexión a Qdrant

**Síntomas:**
```
ConnectionRefusedError: [Errno 111] Connection refused
```
o
```
qdrant_client.http.exceptions.UnexpectedResponse: Connection error
```

**Causa:** El contenedor Docker de Qdrant no está corriendo o no ha terminado de inicializar.

**Solución:**

```bash
# Verificar estado del contenedor
docker ps --filter name=qdrant-financiero

# Si no aparece, verificar si se detuvo
docker ps -a --filter name=qdrant-financiero

# Reiniciar el contenedor
cd ~/rag-financiero-workshop
docker compose down
docker compose up -d

# Esperar 5 segundos y verificar
sleep 5
curl -s http://localhost:6333/collections | python -m json.tool

# Si persiste, verificar que el puerto 6333 no esté ocupado
lsof -i :6333
```

---

### Problema 2: Error de API key de OpenAI inválida o sin créditos

**Síntomas:**
```
openai.AuthenticationError: Error code: 401 - Invalid API Key
```
o
```
openai.RateLimitError: Error code: 429 - You exceeded your current quota
```

**Causa:** La API key configurada en `.env` es incorrecta, ha expirado o la cuenta no tiene créditos disponibles.

**Solución:**

```bash
# Verificar que la variable está configurada correctamente
cd ~/rag-financiero-workshop
grep OPENAI_API_KEY .env

# Verificar que no hay espacios extra ni comillas incorrectas
# El formato correcto es:
# OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx

# Test rápido de la key
python -c "
from dotenv import load_dotenv
import os
load_dotenv('.env')
key = os.getenv('OPENAI_API_KEY')
print(f'Key cargada: {key[:10]}...{key[-4:]}')
print(f'Longitud: {len(key)} caracteres')
"

# Si la key es correcta pero no hay créditos:
# 1. Accede a https://platform.openai.com/account/billing
# 2. Verifica el saldo disponible
# 3. Agrega créditos si es necesario

# Si necesitas regenerar la key:
# 1. Accede a https://platform.openai.com/api-keys
# 2. Crea una nueva key
# 3. Actualiza el archivo .env con la nueva key
```

---

## 9. Limpieza

> **⚠️ IMPORTANTE:** NO ejecutes la limpieza si vas a continuar con el Laboratorio 2. La colección `financial_products_basic` y el corpus de datos son necesarios como baseline de comparación.

Si necesitas limpiar el entorno por completo (solo al finalizar todos los laboratorios):

```bash
cd ~/rag-financiero-workshop

# Detener contenedores
docker compose down

# Eliminar volúmenes de datos (DESTRUCTIVO)
# rm -rf volumes/qdrant_storage

# Desactivar entorno virtual
deactivate
```

Para limpiar solo los artefactos del lab sin afectar la infraestructura:

```bash
# Eliminar solo archivos intermedios (conservar corpus y colección Qdrant)
rm -f lab01/chunks_procesados.json
rm -f lab01/resultados_evaluacion.json
rm -f lab01/REPORTE_LAB01.md
```

---

## 10. Resumen

En este laboratorio has implementado exitosamente un pipeline RAG completo para consulta de productos financieros:

| Componente | Implementación |
|---|---|
| **Ingesta** | DirectoryLoader + TextLoader (5 documentos financieros) |
| **Chunking** | RecursiveCharacterTextSplitter (512 chars, 50 overlap) → ~38 chunks |
| **Embeddings** | OpenAI text-embedding-3-small (1536 dimensiones) |
| **Almacenamiento vectorial** | Qdrant v1.9.4, colección `financial_products_basic` |
| **Recuperación** | Búsqueda por similitud coseno, top-k=4 |
| **Generación** | GPT-4o con prompt especializado financiero |
| **Evaluación** | 10 preguntas comparativas RAG vs. sin RAG |

**Hallazgo clave:** El sistema RAG demostró una precisión significativamente superior (~90%) comparado con el LLM sin contexto (~0%) al responder preguntas sobre datos específicos de productos financieros sintéticos, validando que la arquitectura RAG reduce efectivamente las alucinaciones al anclar las respuestas en fuentes documentales verificables.

### Recursos adicionales

- [Documentación de LangChain - RAG Tutorial](https://python.langchain.com/docs/tutorials/rag/)
- [Qdrant Documentation - Quick Start](https://qdrant.tech/documentation/quick-start/)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)
- [Lewis et al. (2020) - RAG Paper](https://arxiv.org/abs/2005.11401)

### Próximo laboratorio

En el **Laboratorio 02** optimizarás este sistema implementando búsqueda híbrida (semántica + BM25 con Elasticsearch), reranking con Cohere, chunking estratégico avanzado y payload indexing en Qdrant, usando la colección `financial_products_basic` como baseline de comparación.
---LAB
