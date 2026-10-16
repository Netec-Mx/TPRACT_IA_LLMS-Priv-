# Búsqueda más precisa de productos financieros

**Duración:** 105 minutos

En el primer taller el asistente buscaba por el significado de la pregunta. Con pocas fichas eso alcanza. Cuando hay muchos documentos, una sola forma de buscar se queda corta: a veces hace falta la palabra exacta, a veces el tema, y a veces hay que volver a ordenar lo encontrado.

En este taller amplías la base a más de 50 documentos y comparas tres formas de cortarlos. Después buscas de dos maneras a la vez, reordenas los fragmentos y mides si la respuesta se apoya en ellos.

Trabajas en **Windows Server** con **Visual Studio Code**. El equipo ya está preparado. Tú no instalas programas, librerías ni bases de datos.

Quien prepara el equipo sigue [Prerrequisitos.md](Prerrequisitos.md). Si eres participante, quédate en esta guía. El primer taller ya debe estar hecho: Qdrant encendido y la colección `financial_products_basic` conservada.

## Qué vas a aprender

- [ ] Pasar de 5 fichas a más de 50 documentos, con etiquetas de tipo de producto, categoría y fecha
- [ ] Comparar tres cortes: fijo, semántico y jerárquico
- [ ] Guardar los fragmentos para buscar por significado y, aparte, por palabras
- [ ] Leer la pregunta para saber de qué producto habla y limitar la búsqueda a ese tipo
- [ ] Mezclar las dos búsquedas con un peso llamado alpha, y reordenar el resultado con Cohere
- [ ] Medir la respuesta con RAGAS: fidelidad, relevancia y precisión del contexto

## Palabras que vas a usar

| Palabra | Qué significa aquí |
|---|---|
| Corte fijo | Fragmentos de unas 500 letras, con 50 letras repetidas entre uno y el siguiente |
| Corte semántico | Junta las frases seguidas cuando su significado se parece |
| Corte jerárquico | Separa el documento por sus títulos, para que cada sección quede junta |
| Búsqueda por significado | Qdrant compara embeddings. Es la búsqueda del primer taller |
| Búsqueda por palabras (BM25) | Elasticsearch busca las palabras de la pregunta, en español |
| Búsqueda híbrida | Usa las dos listas y les da un peso |
| Alpha | La parte del peso que corresponde al significado. El resto corresponde a las palabras. 0.5 es mitad y mitad |
| Análisis de la pregunta | El programa lee la pregunta y reconoce si habla de crédito, tarjeta, fondo, cuenta o seguro |
| Metadato | Etiqueta del fragmento: tipo de producto, categoría y fecha de vigencia |
| Rerank | Cohere vuelve a leer la pregunta y los fragmentos, y deja arriba los más útiles |
| Fidelidad | La respuesta está sostenida por los fragmentos. En RAGAS se llama faithfulness |
| Relevancia | La respuesta contesta la pregunta. En RAGAS se llama answer relevancy |
| Precisión del contexto | Los primeros fragmentos son los que sirven. En RAGAS se llama context precision |

## Cómo queda armada la consulta

1. Se crean más de 50 documentos de productos, cada uno con etiquetas.
2. Se comparan los tres cortes en un crédito de ejemplo. Para guardar la búsqueda se usa el corte jerárquico.
3. Esos fragmentos se guardan en Qdrant, en la colección `financial_products_optimized`, y también en Elasticsearch.
4. Al preguntar, el programa reconoce el tipo de producto y busca solo en ese tipo.
5. Pide fragmentos por significado y por palabras, los mezcla con alpha y Cohere los reordena.
6. GPT-4o redacta la respuesta con los fragmentos que quedaron arriba.
7. RAGAS pone un puntaje de 0 a 1 a la forma simple y a esta forma optimizada.

## Ritmo sugerido

| Momento | Minutos |
|---|---|
| Abrir el taller y comprobar el equipo | 10 |
| Crear los documentos | 10 |
| Comparar los tres cortes | 10 |
| Guardar la búsqueda por significado | 15 |
| Guardar la búsqueda por palabras | 10 |
| Mezclar, filtrar y reordenar | 15 |
| Una respuesta completa | 10 |
| Medir con cuatro preguntas | 25 |

## Cómo trabajar en Visual Studio Code

1. Abre Visual Studio Code.
2. Menú **Archivo** > **Abrir carpeta**.
3. Elige `C:\TallerRAG\Capitulo02`.
4. Si no ves el Explorador, presiona `Ctrl+Shift+E`.
5. Menú **Terminal** > **Nueva terminal**.
6. La terminal debe decir **PowerShell**.

En cada paso de programa verás tres partes:

- **Qué haces:** qué vas a lograr y qué hace el código.
- **Resultado esperado:** lo que debe aparecer en la terminal.
- **Código a ejecutar:** el comando de PowerShell y el programa.

Los programas ya están en la carpeta. El comando `python` es el que escribes y ejecutas.

Varios programas usan funciones compartidas del archivo `herramientas.py`. Ese archivo no se ejecuta solo. Cada paso indica el programa que sí ejecutas.

---

## Paso 1. Abre la carpeta del taller

### Qué haces

El comando muestra la carpeta en la que está la terminal. Los programas de este taller leen y guardan archivos ahí, así que la ruta tiene que terminar en `Capitulo02`.

### Resultado esperado

Una ruta de Windows que termina en `Capitulo02`.

### Código a ejecutar

```powershell
Get-Location
```

Si la ruta no termina en `Capitulo02`:

```powershell
Set-Location C:\TallerRAG\Capitulo02
Get-Location
```

---

## Paso 2. Comprueba que el equipo responde

### Qué haces

Compruebas las cuatro conexiones de este taller antes de crear documentos.

El programa `revisar_entorno.py`:

1. Lee `.env` y confirma que existen la clave de OpenAI y la clave de Cohere.
2. Pide un embedding de prueba. Debe traer 1,536 números.
3. Pide a GPT-4o una respuesta corta.
4. Confirma que Qdrant está encendido y, si existe, cuántos fragmentos dejó el primer taller en `financial_products_basic`.
5. Confirma que Elasticsearch está encendido. Esa es la búsqueda por palabras.
6. Pide a Cohere que ordene dos frases de prueba. La frase de la tasa debe quedar por encima de la frase del clima.

### Resultado esperado

```text
Embeddings listos. Cada lista tiene 1536 números.
Modelo de respuestas listo. Dijo: LISTO
Qdrant listo en localhost:6333.
Colección del primer taller lista. Fragmentos: ...
Búsqueda por palabras lista. Elasticsearch ...
Reordenamiento listo con Cohere.
Todo listo. Puedes continuar.
```

La palabra después de "Dijo:" puede variar. Deben aparecer **1536** y **Todo listo**.

### Código a ejecutar

```powershell
python .\revisar_entorno.py
```

Programa `revisar_entorno.py`:

```python
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import os
from pathlib import Path

from dotenv import load_dotenv

CARPETA = Path(__file__).resolve().parent
load_dotenv(CARPETA / ".env")


def exigir(nombre: str) -> str:
    valor = os.getenv(nombre, "").strip()
    marcadores = ("PEGAR", "TU_CLAVE", "tu-clave", "coloca-aqui", "changeme", "<")
    if (not valor) or any(marca.lower() in valor.lower() for marca in marcadores):
        print(f"Falta {nombre} en el archivo .env.")
        print("Avisa al instructor.")
        raise SystemExit(1)
    return valor


def main():
    clave_openai = exigir("OPENAI_API_KEY")
    clave_cohere = exigir("COHERE_API_KEY")

    from openai import OpenAI

    cliente = OpenAI(api_key=clave_openai, timeout=60)
    modelo_embedding = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    modelo_chat = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")

    try:
        embedding = cliente.embeddings.create(input="prueba de productos financieros", model=modelo_embedding)
        tamano = len(embedding.data[0].embedding)
        print(f"Embeddings listos. Cada lista tiene {tamano} números.")
        chat = cliente.chat.completions.create(
            model=modelo_chat,
            messages=[{"role": "user", "content": "Responde solo con la palabra LISTO."}],
            max_tokens=5,
        )
        print(f"Modelo de respuestas listo. Dijo: {chat.choices[0].message.content}")
    except Exception as error:
        print("No se pudo hablar con OpenAI.")
        print("Avisa al instructor.")
        print(f"Detalle: {error}")
        raise SystemExit(1)

    if tamano != 1536:
        print("El embedding no tiene 1536 números. Avisa al instructor.")
        raise SystemExit(1)

    from qdrant_client import QdrantClient

    host = os.getenv("QDRANT_HOST", "localhost")
    puerto = int(os.getenv("QDRANT_PORT", "6333"))
    try:
        qdrant = QdrantClient(host=host, port=puerto, timeout=5)
        qdrant.get_collections()
        print(f"Qdrant listo en {host}:{puerto}.")
    except Exception as error:
        print("No hay conexión con Qdrant.")
        print("Avisa al instructor.")
        print(f"Detalle: {error}")
        raise SystemExit(1)

    if qdrant.collection_exists("financial_products_basic"):
        total = qdrant.count(collection_name="financial_products_basic", exact=True).count
        print(f"Colección del primer taller lista. Fragmentos: {total}.")
    else:
        print("No está la colección del primer taller, financial_products_basic.")
        print("Conviene completar el capítulo 1. Este taller puede continuar.")

    from elasticsearch import Elasticsearch

    es_host = os.getenv("ELASTICSEARCH_HOST", "localhost")
    es_puerto = os.getenv("ELASTICSEARCH_PORT", "9200")
    try:
        elastic = Elasticsearch(f"http://{es_host}:{es_puerto}", request_timeout=10)
        info = elastic.info()
        salud = elastic.cluster.health()
        print(f"Búsqueda por palabras lista. Elasticsearch {info['version']['number']}, estado {salud['status']}.")
    except Exception as error:
        print("No hay conexión con Elasticsearch.")
        print("Avisa al instructor.")
        print(f"Detalle: {error}")
        raise SystemExit(1)

    import cohere

    try:
        cohere.Client(api_key=clave_cohere).rerank(
            model=os.getenv("COHERE_RERANK_MODEL", "rerank-multilingual-v3.0"),
            query="tasa de interés",
            documents=["La tasa fija anual es 8.5%.", "El clima de hoy está nublado."],
            top_n=1,
        )
        print("Reordenamiento listo con Cohere.")
    except Exception as error:
        print("No se pudo usar la clave de Cohere.")
        print("Avisa al instructor.")
        print(f"Detalle: {error}")
        raise SystemExit(1)

    print("Todo listo. Puedes continuar.")


if __name__ == "__main__":
    main()

```

---

## Paso 3. Crea más de 50 documentos

El primer taller usó 5 fichas. Aquí la base crece para parecerse a un catálogo: créditos, tarjetas, fondos, cuentas y seguros. Cada documento lleva etiquetas. Esas etiquetas son metadatos: tipo de producto, categoría, fecha de vigencia, nombre y entidad.

### Qué haces

El programa `crear_documentos.py` escribe 54 documentos en `datos\documentos`. Doce son créditos, catorce tarjetas, doce fondos, ocho cuentas y ocho seguros. Junto a cada documento guarda un archivo `.json` con sus etiquetas.

Cuatro datos quedan fijos, porque más adelante los vas a preguntar:

| Documento | Dato |
|---|---|
| Crédito Residencial Plus | Tasa fija anual 8.5% |
| Crédito Mi Primera Casa | Enganche mínimo 15% |
| Tarjeta Platinum Rewards | Anualidad $0 el primer año |
| Fondo Renta Fija MX | Rendimiento del último año 4.5% |

Abre `datos\documentos\credito_hipotecario_00.md` y busca el 8.5%. Así ves que la respuesta futura tiene de dónde salir.

### Resultado esperado

```text
Documentos creados: 54
Deben ser 54: 12 créditos, 14 tarjetas, 12 fondos, 8 cuentas y 8 seguros.
Listo. Hay más de 50 documentos.
```

### Código a ejecutar

```powershell
python .\crear_documentos.py
```

Programa `crear_documentos.py`:

```python
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import json
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
DESTINO = CARPETA / "datos" / "documentos"

CREDITOS = [
    ("Residencial Plus", "8.5%", "20 años", "10%", "2 años", "$5,000,000"),
    ("Mi Primera Casa", "9.2%", "15 años", "15%", "1 año", "$1,000,000"),
    ("Vivienda Flexible", "10.1%", "25 años", "20%", "3 años", "$2,500,000"),
    ("Hipoteca Verde", "7.8%", "30 años", "10%", "2 años", "$3,000,000"),
    ("Casa Segura", "11.0%", "20 años", "15%", "2 años", "$5,000,000"),
    ("Hogar Premium", "8.5%", "15 años", "20%", "3 años", "$4,000,000"),
    ("Vivienda Joven", "9.2%", "10 años", "10%", "1 año", "$800,000"),
    ("Hipoteca Digital", "10.1%", "20 años", "15%", "2 años", "$1,500,000"),
    ("Casa Familiar", "7.8%", "25 años", "10%", "2 años", "$2,000,000"),
    ("Lote Propio", "11.0%", "15 años", "20%", "3 años", "$900,000"),
    ("Departamento Centro", "8.5%", "20 años", "15%", "2 años", "$3,500,000"),
    ("Vivienda Rural", "9.2%", "30 años", "10%", "1 año", "$700,000"),
]

TARJETAS = [
    ("Platinum Rewards", "$0 el primer año", "25%", "1 punto", "$50,000", "$15,000"),
    ("Gold Travel", "$1,200", "28%", "2 puntos", "$150,000", "$25,000"),
    ("Classic", "$800", "32%", "1 punto", "$20,000", "$8,000"),
    ("Black Infinite", "$4,800", "22%", "3 puntos", "$500,000", "$80,000"),
    ("Cashback Plus", "$0", "30%", "1 punto", "$40,000", "$12,000"),
    ("Digital First", "$450", "29%", "2 puntos", "$30,000", "$10,000"),
    ("Empresarial", "$2,500", "27%", "2 puntos", "$300,000", "$40,000"),
    ("Universitaria", "$0 el primer año", "34%", "1 punto", "$8,000", "$5,000"),
    ("Mujer", "$600", "26%", "2 puntos", "$60,000", "$18,000"),
    ("Viaje Nacional", "$900", "31%", "1 punto", "$35,000", "$14,000"),
    ("Nomina", "$0", "24%", "2 puntos", "$80,000", "$20,000"),
    ("Comercios", "$1,500", "33%", "1 punto", "$100,000", "$30,000"),
    ("Familia", "$700", "28%", "2 puntos", "$45,000", "$16,000"),
    ("Senior", "$500", "23%", "1 punto", "$70,000", "$22,000"),
]

FONDOS = [
    ("Renta Fija MX", "4.5%", "$1,000", "bajo", "diaria", "0.8%", "mediano plazo", "AAA"),
    ("Crecimiento Global", "6.8%", "$2,000", "moderado", "semanal", "1.1%", "largo plazo", "AA+"),
    ("Balanceado", "8.2%", "$3,000", "medio", "mensual", "1.4%", "mediano plazo", "AA"),
    ("Agresivo", "10.5%", "$5,000", "alto", "al vencimiento", "1.7%", "largo plazo", "A+"),
    ("Conservador", "4.5%", "$1,000", "bajo", "al vencimiento", "0.5%", "corto plazo", "AAA"),
    ("ESG Sustentable", "6.8%", "$2,500", "moderado", "semanal", "1.0%", "corto plazo", "AA"),
    ("Tecnologia", "12.0%", "$4,000", "muy alto", "mensual", "2.3%", "largo plazo", "A"),
    ("Deuda Soberana", "5.2%", "$1,500", "bajo", "diaria", "0.6%", "mediano plazo", "AAA"),
    ("Dividendos", "7.4%", "$3,500", "medio", "mensual", "1.3%", "largo plazo", "AA"),
    ("Dolares", "5.9%", "$2,000", "moderado", "semanal", "0.9%", "mediano plazo", "AA+"),
    ("Infrastructura", "8.8%", "$6,000", "alto", "al vencimiento", "1.6%", "largo plazo", "A+"),
    ("Liquidez Diaria", "4.1%", "$500", "bajo", "diaria", "0.4%", "corto plazo", "AAA"),
]

CUENTAS = [
    ("Ahorro Diario", "3.0%", "$500", "6 retiros"),
    ("Nomina Plus", "4.2%", "$1,000", "8 retiros"),
    ("Inversion Vista", "5.5%", "$5,000", "4 retiros"),
    ("Joven", "2.5%", "$100", "6 retiros"),
    ("Empresarial", "3.8%", "$10,000", "10 retiros"),
    ("Dolares", "2.0%", "$500", "4 retiros"),
    ("Meta Vacaciones", "4.8%", "$2,000", "2 retiros"),
    ("Retiro", "6.0%", "$3,000", "1 retiro"),
]

SEGUROS = [
    ("Proteccion Familiar", "$500,000", "18 a 65 años", "$420"),
    ("Vida Temporal", "$1,000,000", "18 a 60 años", "$780"),
    ("Educacion Hijos", "$750,000", "25 a 55 años", "$650"),
    ("Accidentes", "$300,000", "18 a 70 años", "$210"),
    ("Invalidez", "$2,000,000", "18 a 60 años", "$1,100"),
    ("Empresarial", "$5,000,000", "18 a 65 años", "$2,400"),
    ("Senior Vida", "$400,000", "50 a 75 años", "$980"),
    ("Digital", "$250,000", "18 a 45 años", "$180"),
]


def ficha_credito(nombre, tasa, plazo, enganche, antiguedad, monto) -> str:
    return f"""# Crédito Hipotecario {nombre}

Producto del Banco Financiero Nacional para compra de vivienda.

## Condiciones generales

El crédito {nombre} financia vivienda nueva o usada. El inmueble debe estar libre de gravámenes.

### Tasa de interés

- Tasa fija anual: {tasa}
- La tasa moratoria es la tasa ordinaria más 5 puntos.
- La tasa no cambia durante el plazo contratado.

### Plazo y monto

- Plazo máximo: {plazo}
- Monto máximo: {monto} MXN
- Enganche mínimo: {enganche} del valor del inmueble

## Requisitos

1. Edad entre 25 y 64 años.
2. Antigüedad laboral mínima de {antiguedad}.
3. Ingresos mínimos comprobables de $25,000 MXN mensuales.
4. Historial sin atrasos mayores a 30 días en los últimos 12 meses.
5. Avalúo realizado por un perito autorizado.

## Comisiones y pago anticipado

- Comisión por apertura: 1.5% del monto del crédito.
- Pago anticipado: sin penalización después del primer año.
- Seguro de vida incluido en la mensualidad.
- Gastos notariales a cargo de quien recibe el crédito.
"""


def ficha_tarjeta(nombre, anualidad, tasa, puntos, limite, ingresos) -> str:
    return f"""# Tarjeta de crédito {nombre}

## Características

La tarjeta {nombre} es una línea de crédito revolvente del Banco Financiero Nacional.

### Costos

- Anualidad: {anualidad}
- Tasa de interés ordinaria: {tasa} anual
- Comisión por disposición de efectivo: 6% del monto dispuesto
- Comisión por pago tardío: $500 MXN

### Límite y recompensas

- Límite de crédito: desde {limite} MXN
- Acumulación: {puntos} por cada $10 MXN de compra
- Vigencia de los puntos: 24 meses

## Requisitos

1. Ser mayor de 18 años.
2. Ingresos mínimos de {ingresos} MXN mensuales.
3. Identificación oficial vigente.
4. Comprobante de domicilio no mayor a 3 meses.

## Seguros incluidos

- Compras protegidas hasta $50,000 MXN por evento.
- Protección contra fraude con responsabilidad de $0 en compras no reconocidas.
"""


def ficha_fondo(nombre, rendimiento, minimo, riesgo, liquidez, comision, horizonte, calificacion) -> str:
    return f"""# Fondo de inversión {nombre}

## Objetivo

El fondo {nombre} busca un rendimiento acorde con su nivel de riesgo. Los rendimientos pasados no garantizan rendimientos futuros.

### Rendimiento y montos

- Rendimiento del último año: {rendimiento} neto
- Monto mínimo de apertura: {minimo} MXN
- Comisión por administración: {comision} anual sobre el saldo

### Riesgo y liquidez

- Nivel de riesgo: {riesgo}
- Horizonte recomendado: {horizonte}
- Liquidez: {liquidez}
- Calificación: {calificacion}

## Información para el cliente

La operadora entrega un prospecto antes de la contratación. El cliente puede consultar el portafolio en la banca en línea.
"""


def ficha_cuenta(nombre, rendimiento, minimo, retiros) -> str:
    return f"""# Cuenta {nombre}

## Condiciones

- Rendimiento anual: {rendimiento}
- Saldo mínimo de apertura: {minimo} MXN
- Disponibilidad: {retiros} sin comisión al mes
- Entidad: Banco Financiero Nacional

## Uso

La cuenta permite transferencias y consulta de saldo en la aplicación. El banco entrega estado de cuenta mensual.
"""


def ficha_seguro(nombre, suma, edad, prima) -> str:
    return f"""# Seguro {nombre}

## Cobertura

- Suma asegurada de referencia: {suma} MXN
- Edad de contratación: {edad}
- Prima mensual de referencia: {prima} MXN
- Entidad: BFN Seguros

## Contratación

Se requiere identificación oficial y designación de beneficiarios. El periodo de espera por enfermedad es de 30 días.
"""


def guardar(prefijo, indice, texto, metadatos) -> None:
    nombre = f"{prefijo}_{indice:02d}.md"
    (DESTINO / nombre).write_text(texto, encoding="utf-8")
    metadatos["doc_source"] = nombre
    (DESTINO / f"{prefijo}_{indice:02d}.json").write_text(
        json.dumps(metadatos, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    for archivo in DESTINO.glob("*"):
        if archivo.suffix in {".md", ".json"}:
            archivo.unlink()

    for indice, datos in enumerate(CREDITOS):
        nombre, tasa, plazo, enganche, antiguedad, monto = datos
        guardar(
            "credito_hipotecario",
            indice,
            ficha_credito(*datos),
            {
                "tipo_producto": "credito",
                "categoria": "hipotecario",
                "nombre_producto": f"Crédito Hipotecario {nombre}",
                "fecha_vigencia": "2024-06-01",
                "entidad": "Banco Financiero Nacional",
            },
        )

    for indice, datos in enumerate(TARJETAS):
        nombre = datos[0]
        guardar(
            "tarjeta",
            indice,
            ficha_tarjeta(*datos),
            {
                "tipo_producto": "tarjeta",
                "categoria": "credito",
                "nombre_producto": f"Tarjeta {nombre}",
                "fecha_vigencia": "2024-07-01",
                "entidad": "Banco Financiero Nacional",
            },
        )

    for indice, datos in enumerate(FONDOS):
        nombre = datos[0]
        guardar(
            "fondo_inversion",
            indice,
            ficha_fondo(*datos),
            {
                "tipo_producto": "inversion",
                "categoria": "fondo",
                "nombre_producto": f"Fondo {nombre}",
                "fecha_vigencia": "2024-05-15",
                "entidad": "Operadora de Fondos XYZ",
            },
        )

    for indice, datos in enumerate(CUENTAS):
        nombre = datos[0]
        guardar(
            "cuenta",
            indice,
            ficha_cuenta(*datos),
            {
                "tipo_producto": "cuenta",
                "categoria": "ahorro",
                "nombre_producto": f"Cuenta {nombre}",
                "fecha_vigencia": "2024-03-01",
                "entidad": "Banco Financiero Nacional",
            },
        )

    for indice, datos in enumerate(SEGUROS):
        nombre = datos[0]
        guardar(
            "seguro",
            indice,
            ficha_seguro(*datos),
            {
                "tipo_producto": "seguro",
                "categoria": "vida",
                "nombre_producto": f"Seguro {nombre}",
                "fecha_vigencia": "2024-08-01",
                "entidad": "BFN Seguros",
            },
        )

    documentos = list(DESTINO.glob("*.md"))
    print(f"Documentos creados: {len(documentos)}")
    print("Deben ser 54: 12 créditos, 14 tarjetas, 12 fondos, 8 cuentas y 8 seguros.")
    print(f"Carpeta: {DESTINO}")
    if len(documentos) < 50:
        print("Faltan documentos. Avisa al instructor.")
        raise SystemExit(1)
    print("Listo. Hay más de 50 documentos.")


if __name__ == "__main__":
    main()

```

---

## Paso 4. Compara tres formas de cortar un documento

El mismo crédito se puede partir de tres maneras. El corte cambia qué texto llega después al modelo.

### Qué haces

El programa `comparar_cortes.py` abre el crédito Residencial Plus y lo corta tres veces.

1. **Fijo.** Pedazos de unas 500 letras, con 50 letras repetidas. Es el corte del primer taller.
2. **Semántico.** Separa el texto en frases, pide el embedding de cada frase y junta las frases seguidas cuando su significado se parece. Si el parecido baja de 0.75, empieza otro fragmento. Este corte llama a OpenAI.
3. **Jerárquico.** Respeta los títulos del documento (`#`, `##`, `###`). Cada sección queda en su fragmento. Si una sección es muy larga, la vuelve a cortar.

Al final verás que el taller guarda la búsqueda con el corte jerárquico, porque en una ficha la tasa, los requisitos y las comisiones están en secciones distintas.

### Resultado esperado

Tres conteos, uno por cada corte, y el inicio del primer fragmento de cada uno. Los tres números pueden ser distintos. El corte semántico puede dejar menos fragmentos si casi todas las frases hablan del mismo crédito. Ningún corte debe decir "no se crearon fragmentos".

### Código a ejecutar

```powershell
python .\comparar_cortes.py
```

Programa `comparar_cortes.py`:

```python
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from herramientas import CARPETA_DOCUMENTOS, cortar_fijo, cortar_jerarquico, cortar_semantico


def mostrar(nombre: str, pedazos: list[str]) -> None:
    if not pedazos:
        print(f"{nombre}: no se crearon fragmentos.")
        return
    promedio = sum(len(pedazo) for pedazo in pedazos) / len(pedazos)
    print(f"{nombre}: {len(pedazos)} fragmentos. Tamaño promedio: {promedio:.0f} letras.")
    print(f"  Empieza así: {pedazos[0][:140].replace(chr(10), ' ')}")


def main():
    ejemplo = CARPETA_DOCUMENTOS / "credito_hipotecario_00.md"
    if not ejemplo.exists():
        print("Falta credito_hipotecario_00.md.")
        print("Ejecuta primero crear_documentos.py.")
        raise SystemExit(1)

    texto = ejemplo.read_text(encoding="utf-8")
    print("Documento de prueba: Crédito Hipotecario Residencial Plus")
    print()
    print("Corte fijo: pedazos de unas 500 letras, con 50 letras repetidas.")
    mostrar("Fijo", cortar_fijo(texto))
    print()
    print("Corte semántico: junta las frases cuando su significado se parece.")
    print("Este corte llama a OpenAI. Puede tardar unos segundos.")
    mostrar("Semántico", cortar_semantico(texto))
    print()
    print("Corte jerárquico: un fragmento por cada título del documento.")
    mostrar("Jerárquico", cortar_jerarquico(texto))
    print()
    print("El taller guarda la búsqueda con el corte jerárquico, porque cada sección de la ficha queda junta.")


if __name__ == "__main__":
    main()

```

---

## Paso 5. Guarda los fragmentos para buscar por significado

### Qué haces

Preparas la colección nueva en Qdrant. El programa `guardar_busqueda.py`:

1. Lee los 54 documentos y sus etiquetas.
2. Los corta con el corte jerárquico.
3. Crea la colección `financial_products_optimized`. Cada embedding tiene 1,536 números y se compara por similitud coseno.
4. Prepara las etiquetas `tipo_producto`, `categoria` y `fecha_vigencia` para poder filtrar.
5. Guarda texto, etiquetas y embedding.
6. Hace una prueba: busca "tasa de interés hipotecario" y se queda solo con el tipo `credito`.

Puede tardar unos minutos. Espera a ver la prueba con filtro.

La colección del primer taller no se borra.

### Resultado esperado

```text
Lugar de búsqueda creado: financial_products_optimized.
Guardado terminado. Fragmentos en financial_products_optimized: ...
Prueba con filtro: solo créditos.
  credito_hipotecario_00.md | Crédito Hipotecario Residencial Plus
```

El número de fragmentos depende del corte. Debe ser mayor que 50. Los tres resultados de la prueba deben ser créditos, no tarjetas ni fondos.

### Código a ejecutar

```powershell
python .\guardar_busqueda.py
```

Programa `guardar_busqueda.py`:

```python
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import json
import time

from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PayloadSchemaType, PointStruct, VectorParams

from herramientas import (
    CARPETA_DOCUMENTOS,
    COLECCION,
    cliente_qdrant,
    cortar_jerarquico,
    vector_de,
    vectores_de,
)


def main():
    documentos = sorted(CARPETA_DOCUMENTOS.glob("*.md"))
    if len(documentos) < 50:
        print("No están los documentos del taller.")
        print("Ejecuta primero crear_documentos.py.")
        raise SystemExit(1)

    cliente = cliente_qdrant()
    if cliente.collection_exists(COLECCION):
        print("Ya había una colección con este nombre. Se vuelve a crear.")
        cliente.delete_collection(COLECCION)
        time.sleep(1)

    cliente.create_collection(
        collection_name=COLECCION,
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )
    for campo in ("tipo_producto", "categoria", "fecha_vigencia"):
        cliente.create_payload_index(
            collection_name=COLECCION,
            field_name=campo,
            field_schema=PayloadSchemaType.KEYWORD,
        )
    print(f"Lugar de búsqueda creado: {COLECCION}.")
    print("Las etiquetas tipo de producto, categoría y fecha quedan listas para filtrar.")

    puntos = []
    identificador = 0
    for ruta in documentos:
        metadatos_ruta = ruta.with_suffix(".json")
        metadatos = json.loads(metadatos_ruta.read_text(encoding="utf-8"))
        pedazos = [pedazo for pedazo in cortar_jerarquico(ruta.read_text(encoding="utf-8")) if len(pedazo) >= 20]
        if not pedazos:
            continue
        vectores = vectores_de(pedazos)
        for pedazo, vector in zip(pedazos, vectores):
            puntos.append(
                PointStruct(
                    id=identificador,
                    vector=vector,
                    payload={
                        "content": pedazo,
                        "doc_source": metadatos["doc_source"],
                        "tipo_producto": metadatos["tipo_producto"],
                        "categoria": metadatos["categoria"],
                        "fecha_vigencia": metadatos["fecha_vigencia"],
                        "nombre_producto": metadatos["nombre_producto"],
                    },
                )
            )
            identificador += 1
        if len(puntos) >= 40:
            cliente.upsert(collection_name=COLECCION, points=puntos)
            print(f"Fragmentos guardados hasta ahora: {identificador}")
            puntos = []
            time.sleep(0.3)

    if puntos:
        cliente.upsert(collection_name=COLECCION, points=puntos)

    total = cliente.count(collection_name=COLECCION, exact=True).count
    print(f"Guardado terminado. Fragmentos en {COLECCION}: {total}")

    prueba = cliente.query_points(
        collection_name=COLECCION,
        query=vector_de("tasa de interés hipotecario"),
        query_filter=Filter(must=[FieldCondition(key="tipo_producto", match=MatchValue(value="credito"))]),
        limit=3,
    )
    print("Prueba con filtro: solo créditos.")
    for punto in prueba.points:
        print(f"  {punto.payload.get('doc_source')} | {punto.payload.get('nombre_producto')}")


if __name__ == "__main__":
    main()

```

---

## Paso 6. Guarda los mismos fragmentos para buscar por palabras

La búsqueda por significado encuentra textos parecidos aunque no usen las mismas palabras. La búsqueda por palabras, llamada BM25, premia los términos que sí aparecen, como "8.5%" o "Residencial Plus". Elasticsearch hace esa búsqueda con un analizador de español.

### Qué haces

El programa `guardar_palabras.py`:

1. Se conecta a Elasticsearch.
2. Crea el índice `financial_products_bm25`.
3. Guarda los mismos fragmentos jerárquicos, con sus etiquetas. El texto queda marcado para buscarse en español.
4. Prueba la frase "tasa de interés del crédito hipotecario" y muestra los tres documentos de arriba.

### Resultado esperado

```text
Elasticsearch conectado. Versión 8...
Índice creado: financial_products_bm25. Las palabras se interpretan en español.
Fragmentos guardados para búsqueda por palabras: ...
Prueba de búsqueda por palabras:
  credito_hipotecario_...
```

El número de fragmentos debe parecerse al del paso 5, porque el corte es el mismo.

### Código a ejecutar

```powershell
python .\guardar_palabras.py
```

Programa `guardar_palabras.py`:

```python
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import json

from elasticsearch.helpers import bulk

from herramientas import CARPETA_DOCUMENTOS, INDICE, cliente_elastic, cortar_jerarquico


def main():
    documentos = sorted(CARPETA_DOCUMENTOS.glob("*.md"))
    if len(documentos) < 50:
        print("No están los documentos del taller.")
        print("Ejecuta primero crear_documentos.py.")
        raise SystemExit(1)

    elastic = cliente_elastic()
    info = elastic.info()
    print(f"Elasticsearch conectado. Versión {info['version']['number']}.")

    if elastic.indices.exists(index=INDICE):
        elastic.indices.delete(index=INDICE)
        print("Ya había un índice con este nombre. Se vuelve a crear.")

    elastic.indices.create(
        index=INDICE,
        settings={"number_of_shards": 1, "number_of_replicas": 0},
        mappings={
            "properties": {
                "content": {"type": "text", "analyzer": "spanish"},
                "tipo_producto": {"type": "keyword"},
                "categoria": {"type": "keyword"},
                "doc_source": {"type": "keyword"},
                "nombre_producto": {"type": "keyword"},
            }
        },
    )
    print(f"Índice creado: {INDICE}. Las palabras se interpretan en español.")

    acciones = []
    identificador = 0
    for ruta in documentos:
        metadatos = json.loads(ruta.with_suffix(".json").read_text(encoding="utf-8"))
        for pedazo in cortar_jerarquico(ruta.read_text(encoding="utf-8")):
            if len(pedazo.strip()) < 20:
                continue
            acciones.append(
                {
                    "_index": INDICE,
                    "_id": identificador,
                    "_source": {
                        "content": pedazo,
                        "doc_source": metadatos["doc_source"],
                        "tipo_producto": metadatos["tipo_producto"],
                        "categoria": metadatos["categoria"],
                        "nombre_producto": metadatos["nombre_producto"],
                    },
                }
            )
            identificador += 1

    bulk(elastic, acciones, raise_on_error=True)
    elastic.indices.refresh(index=INDICE)
    total = elastic.count(index=INDICE)["count"]
    print(f"Fragmentos guardados para búsqueda por palabras: {total}")

    respuesta = elastic.search(
        index=INDICE,
        query={
            "match": {
                "content": {
                    "query": "tasa de interés del crédito hipotecario",
                    "analyzer": "spanish",
                }
            }
        },
        size=3,
    )
    print("Prueba de búsqueda por palabras:")
    for hit in respuesta["hits"]["hits"]:
        print(f"  {hit['_source']['doc_source']} | {hit['_source']['nombre_producto']}")


if __name__ == "__main__":
    main()

```

---

## Paso 7. Mezcla las dos búsquedas y reordénalas

### Qué haces

Ves, en una sola pregunta, las piezas de la búsqueda optimizada. El programa `buscar_hibrido.py` usa esta pregunta:

¿Cuáles son la tasa de interés y los requisitos del crédito hipotecario Residencial Plus?

El programa hace esto:

1. **Lee la pregunta.** Reconoce la palabra crédito y limita la búsqueda al tipo `credito`. Eso es el análisis de la pregunta.
2. Pide 8 fragmentos a Qdrant (significado) y 8 a Elasticsearch (palabras).
3. Los mezcla. **Alpha** es el peso del significado. Con 0.5, significado y palabras pesan igual. Un fragmento que sale en las dos listas sube.
4. Envía la mezcla a Cohere. Cohere la vuelve a ordenar según la pregunta. Eso es el rerank. Arriba queda lo más útil.
5. Repite la mezcla con alpha 0.3, 0.5 y 0.7 en tres preguntas. Cuenta en cuántas la ficha correcta quedó entre los primeros tres fragmentos.
6. Guarda el alpha con más aciertos en `configuracion.json`. Los pasos siguientes usan ese número.

Puede tardar unos minutos.

### Resultado esperado

Primero ves el tipo detectado: `credito`. Luego tres listas: por significado, por palabras y después de reordenar. En la lista reordenada debe aparecer `credito_hipotecario_00.md`.

Al final, una línea por cada alpha y esta frase:

```text
Se usará alpha ... en los siguientes pasos.
Archivo guardado: configuracion.json
```

El alpha ganador puede ser 0.3, 0.5 o 0.7.

### Código a ejecutar

```powershell
python .\buscar_hibrido.py
```

Programa `buscar_hibrido.py`:

```python
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import json

from herramientas import (
    CARPETA,
    alpha_guardado,
    buscar_palabras,
    buscar_significado,
    detectar_tipo,
    mezclar,
    reordenar,
)

PREGUNTA = "¿Cuáles son la tasa de interés y los requisitos del crédito hipotecario Residencial Plus?"

PRUEBAS = [
    {
        "pregunta": "¿Cuál es la tasa de interés anual del crédito hipotecario Residencial Plus?",
        "fuente": "credito_hipotecario_00.md",
    },
    {
        "pregunta": "¿Cuánto es la anualidad de la tarjeta Platinum Rewards?",
        "fuente": "tarjeta_00.md",
    },
    {
        "pregunta": "¿Cuál es el rendimiento del último año del Fondo Renta Fija MX?",
        "fuente": "fondo_inversion_00.md",
    },
]


def mostrar_lista(titulo: str, elementos: list[dict]) -> None:
    print(titulo)
    if not elementos:
        print("  Sin resultados.")
        return
    for numero, item in enumerate(elementos[:3], 1):
        extra = ""
        if "puntaje_rerank" in item:
            extra = f" | relevancia {item['puntaje_rerank']:.2f}"
        origen = ""
        if item.get("origen"):
            origen = " | viene de: " + ", ".join(item["origen"])
        print(f"  {numero}. {item.get('fuente', 'sin archivo')}{extra}{origen}")


def aciertos(alpha: float) -> int:
    total = 0
    for prueba in PRUEBAS:
        tipo = detectar_tipo(prueba["pregunta"])
        mezcla = mezclar(
            buscar_significado(prueba["pregunta"], tipo, 8),
            buscar_palabras(prueba["pregunta"], tipo, 8),
            alpha,
        )
        finales = reordenar(prueba["pregunta"], mezcla[:12], 3)
        fuentes = [item.get("fuente") for item in finales]
        if prueba["fuente"] in fuentes:
            total += 1
    return total


def main():
    tipo = detectar_tipo(PREGUNTA)
    print(f"Pregunta: {PREGUNTA}")
    print(f"La pregunta habla de: {tipo}.")
    print("La búsqueda se limita a ese tipo de producto.")
    print()

    significados = buscar_significado(PREGUNTA, tipo, 8)
    palabras = buscar_palabras(PREGUNTA, tipo, 8)
    mostrar_lista("Por significado:", significados)
    print()
    mostrar_lista("Por palabras exactas:", palabras)
    print()

    alpha = 0.5
    mezcla = mezclar(significados, palabras, alpha)
    print("Mezcla con alpha 0.5: el significado y las palabras pesan igual.")
    mostrar_lista("Mezcla:", mezcla)
    print()
    print("Cohere vuelve a ordenar los fragmentos según la pregunta.")
    finales = reordenar(PREGUNTA, mezcla[:12], 4)
    mostrar_lista("Después de reordenar:", finales)
    print()

    print("Ahora se prueba alpha 0.3, 0.5 y 0.7 con tres preguntas.")
    print("Alpha es la parte que pesa el significado. El resto pesa las palabras.")
    print("Esto puede tardar unos minutos.")
    resultados = {}
    for valor in (0.3, 0.5, 0.7):
        resultados[valor] = aciertos(valor)
        print(f"Alpha {valor}: la ficha correcta quedó entre los primeros en {resultados[valor]} de 3 preguntas.")

    mejor = max(resultados, key=resultados.get)
    ruta = CARPETA / "configuracion.json"
    ruta.write_text(json.dumps({"alpha": mejor}, indent=2), encoding="utf-8")
    print(f"Se usará alpha {mejor} en los siguientes pasos.")
    print("Archivo guardado: configuracion.json")
    print(f"Alpha guardado ahora: {alpha_guardado()}")


if __name__ == "__main__":
    main()

```

---

## Paso 8. Pide una respuesta con los fragmentos reordenados

### Qué haces

Cierras el recorrido: de la pregunta a la respuesta escrita.

El programa `responder.py` toma el alpha guardado y, para la pregunta del crédito Residencial Plus:

1. Detecta el tipo de producto.
2. Busca por significado y por palabras.
3. Mezcla con ese alpha.
4. Reordena con Cohere y se queda con 4 fragmentos.
5. Pide a GPT-4o que responda solo con ese texto.

En la ficha, la tasa fija anual es **8.5%** y la antigüedad laboral mínima es **2 años**.

### Resultado esperado

Una respuesta que menciona 8.5%. Debajo, la lista de fragmentos usados. Entre ellos debe estar `credito_hipotecario_00.md`.

La redacción puede cambiar. El dato de la ficha es lo que buscas.

### Código a ejecutar

```powershell
python .\responder.py
```

Programa `responder.py`:

```python
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from herramientas import alpha_guardado, consultar

PREGUNTA = "¿Cuáles son la tasa de interés y los requisitos del crédito hipotecario Residencial Plus?"


def main():
    alpha = alpha_guardado()
    print(f"Se usa alpha {alpha}: ese es el peso del significado.")
    print("El programa filtra el tipo de producto, mezcla significado y palabras, reordena y redacta.")
    print("Puede tardar un minuto.")
    print()
    resultado = consultar(PREGUNTA, alpha=alpha, hibrido=True, usar_reorden=True, filtrar=True)
    print(f"Pregunta: {resultado['pregunta']}")
    print(f"Tipo detectado: {resultado['tipo']}")
    print()
    print("Respuesta:")
    print(resultado["respuesta"])
    print()
    print("Fragmentos usados:")
    for numero, fragmento in enumerate(resultado["fragmentos"], 1):
        print(f"  {numero}. {fragmento.get('fuente', 'sin archivo')}")


if __name__ == "__main__":
    main()

```

---

## Paso 9. Mide la forma simple y la forma optimizada

Las dos formas buscan en los mismos documentos nuevos. Así la diferencia viene del modo de buscar, no de tener más fichas.

- **Forma simple:** solo significado, como el primer taller. No filtra el tipo de producto y no reordena.
- **Forma optimizada:** lee la pregunta, mezcla significado y palabras, y reordena.

### Qué haces

El programa `evaluar.py` hace cuatro preguntas a cada forma. En cada respuesta revisa si aparece el dato de la ficha.

Después pide a **RAGAS** tres puntajes de 0 a 1:

1. **Fidelidad (faithfulness).** Qué tanto de la respuesta se puede sostener con los fragmentos.
2. **Relevancia (answer relevancy).** Qué tanto la respuesta contesta la pregunta que se hizo.
3. **Precisión del contexto (context precision).** Qué tan arriba quedaron los fragmentos que sí sirven.

Un número más alto es mejor. Los puntajes cambian un poco de una ejecución a otra. Al final escribe `RESUMEN.md`.

Este paso puede tardar varios minutos. Espera hasta ver **Resumen guardado**.

### Resultado esperado

Para cada forma, cuatro líneas de "Dato de la ficha presente: sí" o "no", y después los puntajes RAGAS si el cálculo termina. Luego:

```text
Resumen guardado: RESUMEN.md
Ábrelo en Visual Studio Code.
```

Abre `RESUMEN.md`. Ahí están la tabla de las cuatro preguntas y la tabla de RAGAS.

### Código a ejecutar

```powershell
python .\evaluar.py
```

Programa `evaluar.py`:

```python
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import json
from datetime import datetime

from herramientas import CARPETA, COLECCION, alpha_guardado, consultar

PREGUNTAS = [
    {
        "pregunta": "¿Cuál es la tasa de interés anual del crédito hipotecario Residencial Plus?",
        "dato": "8.5%",
        "claves": ["8.5"],
    },
    {
        "pregunta": "¿Cuál es el enganche mínimo del crédito Mi Primera Casa?",
        "dato": "15%",
        "claves": ["15%", "15 por ciento"],
    },
    {
        "pregunta": "¿Cuánto es la anualidad de la tarjeta Platinum Rewards?",
        "dato": "$0 el primer año",
        "claves": ["$0 el primer año", "0 el primer año", "primer año"],
    },
    {
        "pregunta": "¿Cuál es el rendimiento del último año del Fondo Renta Fija MX?",
        "dato": "4.5%",
        "claves": ["4.5"],
    },
]


def normalizar(texto: str) -> str:
    return texto.lower().replace("$", "").replace(" ", "")


def contiene(respuesta: str, claves: list[str]) -> bool:
    texto = normalizar(respuesta)
    return any(normalizar(clave) in texto for clave in claves)


def puntajes_ragas(filas: list[dict]) -> dict | None:
    """Pide a RAGAS tres puntajes entre 0 y 1."""
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import answer_relevancy, context_precision, faithfulness

        dataset = Dataset.from_dict(
            {
                "question": [fila["pregunta"] for fila in filas],
                "answer": [fila["respuesta"] for fila in filas],
                "contexts": [fila["contextos"] for fila in filas],
                "ground_truth": [fila["dato"] for fila in filas],
            }
        )
        resultado = evaluate(
            dataset=dataset,
            metrics=[faithfulness, answer_relevancy, context_precision],
        )
        tabla = resultado.to_pandas() if hasattr(resultado, "to_pandas") else None
        nombres = {
            "faithfulness": ["faithfulness"],
            "answer_relevancy": ["answer_relevancy", "response_relevancy"],
            "context_precision": ["context_precision", "llm_context_precision_with_reference"],
        }
        puntajes = {}
        for claro, opciones in nombres.items():
            valor = None
            for opcion in opciones:
                try:
                    valor = float(resultado[opcion])
                    break
                except Exception:
                    if tabla is not None and opcion in getattr(tabla, "columns", []):
                        valor = float(tabla[opcion].mean())
                        break
            puntajes[claro] = valor
        if any(valor is None for valor in puntajes.values()):
            print("RAGAS respondió, pero faltó alguna métrica.")
            print(resultado)
            return None
        return puntajes
    except Exception as error:
        print("RAGAS no pudo calcular los puntajes.")
        print("La comparación de los datos de las fichas sí queda guardada.")
        print(f"Detalle: {error}")
        return None


def ejecutar(hibrido: bool, usar_reorden: bool, alpha: float) -> list[dict]:
    filas = []
    for numero, item in enumerate(PREGUNTAS, 1):
        print(f"  Pregunta {numero} de {len(PREGUNTAS)}")
        resultado = consultar(
            item["pregunta"],
            alpha=alpha,
            hibrido=hibrido,
            usar_reorden=usar_reorden,
            filtrar=hibrido,
        )
        filas.append(
            {
                "pregunta": item["pregunta"],
                "dato": item["dato"],
                "respuesta": resultado["respuesta"],
                "contextos": [fragmento["texto"] for fragmento in resultado["fragmentos"]],
                "acierto": contiene(resultado["respuesta"], item["claves"]),
            }
        )
        print("  Dato de la ficha presente:", "sí" if filas[-1]["acierto"] else "no")
    return filas


def texto_puntaje(puntajes: dict | None, nombre: str) -> str:
    if not puntajes or puntajes.get(nombre) is None:
        return "no disponible"
    return f"{puntajes[nombre]:.2f}"


def main():
    alpha = alpha_guardado()
    print("Esta comparación puede tardar varios minutos.")
    print("Primero responde las preguntas. Después calcula los puntajes RAGAS.")
    print()
    print("Forma del primer taller: solo significado, sin filtro y sin reordenar.")
    basico = ejecutar(hibrido=False, usar_reorden=False, alpha=alpha)
    print()
    print("Forma de este taller: filtro de la pregunta, significado, palabras y reordenamiento.")
    optimizado = ejecutar(hibrido=True, usar_reorden=True, alpha=alpha)

    aciertos_basico = sum(1 for fila in basico if fila["acierto"])
    aciertos_optimizado = sum(1 for fila in optimizado if fila["acierto"])
    print()
    print(f"Datos de la ficha con la forma simple: {aciertos_basico} de {len(PREGUNTAS)}")
    print(f"Datos de la ficha con la forma optimizada: {aciertos_optimizado} de {len(PREGUNTAS)}")
    print()
    print("RAGAS revisa tres cosas, con un puntaje de 0 a 1:")
    print("- Fidelidad: la respuesta sale de los fragmentos, sin datos inventados.")
    print("- Relevancia: la respuesta contesta la pregunta.")
    print("- Precisión del contexto: los fragmentos de arriba sirven para esa respuesta.")
    print("Calculando la forma simple...")
    ragas_basico = puntajes_ragas(basico)
    print("Calculando la forma optimizada...")
    ragas_optimizado = puntajes_ragas(optimizado)

    if ragas_basico:
        print(f"Simple. Fidelidad {ragas_basico['faithfulness']:.2f}. Relevancia {ragas_basico['answer_relevancy']:.2f}. Precisión {ragas_basico['context_precision']:.2f}.")
    if ragas_optimizado:
        print(f"Optimizada. Fidelidad {ragas_optimizado['faithfulness']:.2f}. Relevancia {ragas_optimizado['answer_relevancy']:.2f}. Precisión {ragas_optimizado['context_precision']:.2f}.")

    filas = ""
    for item, simple, mejor in zip(PREGUNTAS, basico, optimizado):
        filas += (
            f"| {item['pregunta']} | {item['dato']} | "
            f"{'sí' if simple['acierto'] else 'no'} | "
            f"{'sí' if mejor['acierto'] else 'no'} |\n"
        )

    resumen = f"""# Resumen del taller: búsqueda más precisa

Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M")}

## Qué se comparó

Las dos formas buscan en la colección `{COLECCION}`, que tiene más de 50 documentos.

- Forma simple, como el primer taller: solo significado. No lee el tipo de producto de la pregunta y no reordena.
- Forma de este taller: lee la pregunta para saber el tipo de producto, mezcla significado y palabras, y Cohere reordena los fragmentos.
- Alpha usado: {alpha}. Es el peso del significado. El resto del peso es para las palabras exactas.

## Datos de las fichas

| Pregunta | Dato de la ficha | Forma simple | Forma optimizada |
|---|---|---|---|
{filas}
Aciertos simples: {aciertos_basico} de {len(PREGUNTAS)}.

Aciertos optimizados: {aciertos_optimizado} de {len(PREGUNTAS)}.

## Puntajes RAGAS

Cada puntaje va de 0 a 1. Un número más alto es mejor.

| Qué mide | En palabras | Forma simple | Forma optimizada |
|---|---|---|---|
| Fidelidad (faithfulness) | La respuesta está sostenida por los fragmentos | {texto_puntaje(ragas_basico, "faithfulness")} | {texto_puntaje(ragas_optimizado, "faithfulness")} |
| Relevancia (answer relevancy) | La respuesta contesta lo que se preguntó | {texto_puntaje(ragas_basico, "answer_relevancy")} | {texto_puntaje(ragas_optimizado, "answer_relevancy")} |
| Precisión del contexto (context precision) | Los primeros fragmentos son los que sirven | {texto_puntaje(ragas_basico, "context_precision")} | {texto_puntaje(ragas_optimizado, "context_precision")} |

Los números cambian un poco cada vez. Lo importante es leer las dos columnas y ver qué forma trae el dato de la ficha.
"""
    (CARPETA / "RESUMEN.md").write_text(resumen, encoding="utf-8")
    (CARPETA / "resultados_evaluacion.json").write_text(
        json.dumps(
            {
                "alpha": alpha,
                "aciertos_simple": aciertos_basico,
                "aciertos_optimizado": aciertos_optimizado,
                "ragas_simple": ragas_basico,
                "ragas_optimizado": ragas_optimizado,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("Resumen guardado: RESUMEN.md")
    print("Ábrelo en Visual Studio Code.")


if __name__ == "__main__":
    main()

```

---

## Si algo no sale como esperas

| Lo que ves | Qué hacer |
|---|---|
| `python` no se reconoce | Avisa al instructor. |
| Falta una clave en `.env`, o un error 401 | Avisa al instructor. |
| No hay conexión con Qdrant | Avisa al instructor. Qdrant debe seguir encendido desde el primer taller. |
| No hay conexión con Elasticsearch | Avisa al instructor. La ventana de Elasticsearch debe seguir abierta. |
| No se pudo usar la clave de Cohere | Avisa al instructor. |
| Falta `credito_hipotecario_00.md` | Vuelve al paso 3 y ejecuta `python .\crear_documentos.py`. |
| El paso 5, 7 o 9 parece detenido | Espera. Está llamando a los servicios. Sigue cuando aparezca el mensaje final de ese paso. |
| RAGAS no pudo calcular los puntajes | La tabla de datos de las fichas sí sirve. Avisa al instructor para los puntajes. |

Si necesitas cortar un programa, haz clic en la terminal y presiona `Ctrl+C`.

## Qué te llevas

| Parte | Cómo quedó en este taller |
|---|---|
| Documentos | 54 fichas nuevas, con tipo, categoría y fecha |
| Corte usado al guardar | Jerárquico, después de compararlo con el fijo y el semántico |
| Significado | Qdrant, colección `financial_products_optimized`, 1,536 números, similitud coseno |
| Palabras | Elasticsearch, índice `financial_products_bm25`, BM25 en español |
| Pregunta | Se detecta el tipo de producto y la búsqueda se filtra con esa etiqueta |
| Mezcla | Alpha: peso del significado y de las palabras |
| Orden final | Cohere `rerank-multilingual-v3.0` |
| Respuesta | GPT-4o, con los fragmentos que quedaron arriba |
| Medición | Cuatro preguntas y RAGAS: faithfulness, answer relevancy, context precision |

La herramienta que corta los textos y redacta la respuesta se llama **LangChain**.

## Conserva este trabajo

Deja encendidos Qdrant y Elasticsearch hasta que el instructor cierre la sesión. La colección `financial_products_basic` del primer taller sigue en Qdrant.

Antes de cerrar, responde con tus palabras: en la pregunta del crédito Residencial Plus, ¿qué aportó buscar también por palabras y volver a ordenar los fragmentos?
---LAB---
