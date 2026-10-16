

# Consulta de productos financieros con documentos de apoyo

**Duración:** 105 minutos

En este taller vas a hacer que un asistente responda preguntas sobre productos financieros usando las fichas del banco. El asistente busca primero en esas fichas y después redacta la respuesta con lo que encontró.

Trabajas en **Windows Server** con **Visual Studio Code**. El equipo ya está preparado. Tú no instalas programas, librerías ni bases de datos.

Quien prepara el equipo sigue [Prerrequisitos.md](Prerrequisitos.md). Si eres participante, quédate en esta guía.

## Qué vas a aprender

- [ ] Reconocer las partes de una consulta RAG: fichas, fragmentos, embeddings, búsqueda y respuesta
- [ ] Leer fichas de crédito, tarjeta, cuenta, inversión y seguro, que son la fuente de la respuesta
- [ ] Cortar las fichas en fragmentos y etiquetar cada fragmento con el producto al que pertenece
- [ ] Convertir los fragmentos en embeddings con `text-embedding-3-small` y guardarlos en Qdrant
- [ ] Preguntar y obtener una respuesta de GPT-4o apoyada en los 4 fragmentos más parecidos
- [ ] Comparar esa respuesta con la del modelo cuando no recibe las fichas

RAG significa *Retrieval-Augmented Generation*: el sistema **recupera** texto de los documentos y con ese texto **genera** la respuesta.

## Palabras que vas a usar


| Palabra           | Qué significa aquí                                                                                             |
| ----------------- | -------------------------------------------------------------------------------------------------------------- |
| Ficha             | El documento de un producto: tasas, requisitos, comisiones y contacto                                          |
| Fragmento (chunk) | Un pedazo de la ficha, de unas 512 letras                                                                      |
| Metadato          | Una etiqueta del fragmento: de qué archivo salió, qué tipo de producto es y cuál es su categoría               |
| Embedding         | Una lista de 1,536 números que representa el significado del texto. La crea el modelo `text-embedding-3-small` |
| Qdrant            | El lugar donde se guardan esos números para buscar los fragmentos parecidos a una pregunta                     |
| Similitud coseno  | La forma en que Qdrant decide qué fragmento se parece más a la pregunta                                        |
| GPT-4o            | El modelo que redacta la respuesta a partir de los fragmentos encontrados                                      |
| Alucinación       | Una cifra o una condición que el modelo escribe y que no está en las fichas                                    |




## Cómo queda armada la consulta

1. Hay cinco fichas de productos.
2. Cada ficha se corta en fragmentos, con un poco de texto repetido entre un fragmento y el siguiente.
3. Cada fragmento se convierte en un embedding y se guarda en Qdrant, en la colección `financial_products_basic`.
4. Cuando haces una pregunta, el sistema busca los 4 fragmentos de significado más parecido.
5. GPT-4o redacta la respuesta usando solo ese texto.

Después haces la misma pregunta sin entregar las fichas. Ahí se ve la diferencia: con documentos, la respuesta puede citar el dato de la ficha; sin documentos, el modelo no tiene ese dato oficial.

## Ritmo sugerido


| Momento                                      | Minutos |
| -------------------------------------------- | ------- |
| Abrir el taller y comprobar el equipo        | 15      |
| Leer las fichas                              | 15      |
| Crear los fragmentos                         | 10      |
| Guardar los embeddings                       | 15      |
| Una pregunta con documentos y sin documentos | 15      |
| Diez preguntas de comparación                | 15      |
| Tus preguntas y el resumen                   | 20      |




## Cómo trabajar en Visual Studio Code

1. Abre Visual Studio Code.
2. Menú **Archivo** > **Abrir carpeta**.
3. Elige la carpeta `Capitulo01`.
4. A la izquierda está el Explorador. Si no lo ves, presiona `Ctrl+Shift+E`.
5. Menú **Terminal** > **Nueva terminal**.
6. La terminal debe decir **PowerShell**. Si dice **cmd** o **Command Prompt**, abre la lista de la terminal y elige **PowerShell**.

En cada paso de programa verás tres partes:

- **Qué haces:** qué vas a lograr y qué hace el código.
- **Resultado esperado:** lo que debe aparecer en la terminal.
- **Código a ejecutar:** el comando de PowerShell y el programa.

Los programas ya están en la carpeta. No los copies en la terminal. El comando `python` es el que escribes y ejecutas.

Para ejecutar un comando: haz clic en la terminal, escribe el comando y presiona **Enter**.

---



## Paso 1. Abre la carpeta del taller

Confirma que Visual Studio Code está en `Capitulo01` y que la terminal es PowerShell.

### Qué haces

El comando muestra la carpeta en la que está la terminal. Los siguientes programas leen las fichas y guardan resultados en esa carpeta, así que la ruta tiene que terminar en `Capitulo01`.

### Resultado esperado

Una ruta de Windows que termina en `Capitulo01`.

### Código a ejecutar

```powershell
Get-Location
```

Si la ruta no termina en `Capitulo01`, y la carpeta del curso es la que contiene `Capitulo01`, ejecuta:

```powershell
Set-Location .\Capitulo01
Get-Location
```

---



## Paso 2. Comprueba que el equipo responde



### Qué haces

Compruebas la conexión con OpenAI y con Qdrant antes de consultar productos.

El programa `revisar_entorno.py`:

1. Lee el archivo `.env`, donde el instructor dejó la clave de OpenAI. Muestra que la clave existe y no la escribe completa.
2. Pide un embedding de prueba al modelo `text-embedding-3-small` y cuenta cuántos números trae. Deben ser 1,536.
3. Pide a GPT-4o una respuesta corta, para confirmar que el modelo de redacción también responde.
4. Pregunta a Qdrant, en este mismo servidor, si está encendido.

Si falta la clave o Qdrant está apagado, el programa se detiene y te pide avisar al instructor.

### Resultado esperado

```text
Clave encontrada. No se muestra completa por seguridad.
Búsqueda por significado lista. Cada embedding tiene 1536 números.
Modelo de embeddings: text-embedding-3-small
Modelo de respuestas listo. Dijo: LISTO
Modelo de chat: gpt-4o
Base de búsqueda lista en localhost:6333.
Todo listo. Puedes continuar.
```

La palabra después de "Dijo:" puede variar un poco. El número **1536** y la frase **Todo listo** sí deben aparecer. Este paso puede tardar unos segundos.

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
from openai import OpenAI
from qdrant_client import QdrantClient

CARPETA = Path(__file__).resolve().parent
load_dotenv(CARPETA / ".env")

clave = os.getenv("OPENAI_API_KEY", "").strip()
marcadores = ("PEGAR", "TU_CLAVE", "tu-clave", "changeme", "<")
clave_invalida = (not clave) or any(marca.lower() in clave.lower() for marca in marcadores)

if clave_invalida:
    print("Falta la clave de OpenAI en el archivo .env.")
    print("Avisa al instructor.")
    raise SystemExit(1)

print("Clave encontrada. No se muestra completa por seguridad.")

modelo_embedding = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
modelo_chat = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")
cliente = OpenAI(api_key=clave, timeout=60)

try:
    respuesta_embedding = cliente.embeddings.create(
        input="prueba de conexion para productos financieros",
        model=modelo_embedding,
    )
    tamano = len(respuesta_embedding.data[0].embedding)
    print(f"Búsqueda por significado lista. Cada embedding tiene {tamano} números.")
    print(f"Modelo de embeddings: {respuesta_embedding.model}")

    respuesta_chat = cliente.chat.completions.create(
        model=modelo_chat,
        messages=[{"role": "user", "content": "Responde solo con la palabra LISTO."}],
        max_tokens=5,
    )
    print(f"Modelo de respuestas listo. Dijo: {respuesta_chat.choices[0].message.content}")
    print(f"Modelo de chat: {respuesta_chat.model}")
except Exception as error:
    print("No se pudo hablar con OpenAI.")
    print("Avisa al instructor.")
    print(f"Detalle: {error}")
    raise SystemExit(1)

if tamano != 1536:
    print("El embedding no tiene 1536 números. Avisa al instructor.")
    raise SystemExit(1)

host = os.getenv("QDRANT_HOST", "localhost")
puerto = int(os.getenv("QDRANT_PORT", "6333"))

try:
    qdrant = QdrantClient(host=host, port=puerto, timeout=5)
    qdrant.get_collections()
    print(f"Base de búsqueda lista en {host}:{puerto}.")
except Exception as error:
    print("No hay conexión con la base de búsqueda Qdrant.")
    print("Avisa al instructor.")
    print(f"Detalle: {error}")
    raise SystemExit(1)

print("Todo listo. Puedes continuar.")

```

---



## Paso 3. Conoce las fichas de productos

Las fichas ya están en `datos\productos`. Son la información oficial de este taller. El asistente solo puede responder con lo que está escrito ahí.

Hay cinco productos del Banco Financiero Nacional:


| Archivo                          | Producto              | Un dato para buscar con la vista             |
| -------------------------------- | --------------------- | -------------------------------------------- |
| `tarjeta_visa_platinum.txt`      | Tarjeta Visa Platinum | Tasa de interés anual: 28.5%                 |
| `credito_hipotecario.txt`        | Crédito hipotecario   | Tasa con nómina: 9.85%                       |
| `cuenta_ahorro_premium.txt`      | Cuenta de ahorro      | Saldo mínimo de apertura: $10,000            |
| `fondo_inversion_renta_fija.txt` | Fondo de inversión    | Rendimiento de los últimos 12 meses: 11.2%   |
| `seguro_vida_proteccion.txt`     | Seguro de vida        | Muerte accidental: 200% de la suma asegurada |




### Qué haces

El comando lista los archivos de la carpeta de fichas. Después abres cada archivo en Visual Studio Code y buscas el dato de la tabla. Así sabes qué información podrá citar el asistente más adelante.

### Resultado esperado

Cinco archivos `.txt`:

```text
credito_hipotecario.txt
cuenta_ahorro_premium.txt
fondo_inversion_renta_fija.txt
seguro_vida_proteccion.txt
tarjeta_visa_platinum.txt
```

El orden puede ser alfabético. Deben estar los cinco nombres.

### Código a ejecutar

```powershell
Get-ChildItem .\datos\productos
```

Para leer una ficha, haz clic en el archivo dentro de `datos` > `productos`.

---



## Paso 4. Corta las fichas en fragmentos



### Qué haces

Preparas las fichas para la búsqueda. Una ficha completa es larga. El programa la corta en pedazos y guarda cada pedazo con etiquetas.

El programa `dividir_documentos.py`:

1. Abre los cinco archivos `.txt`.
2. Corta cada texto en fragmentos de unas **512** letras.
3. Repite **50** letras entre un fragmento y el siguiente, para no partir una idea justo en el borde. Ese corte con repetición se llama chunking.
4. Agrega metadatos a cada fragmento: `doc_source` (archivo), `tipo_producto` y `categoria`.
5. Guarda el resultado en `fragmentos.json`.



### Resultado esperado

Verás las cinco fichas, un total de fragmentos mayor que 20 y un ejemplo del primer fragmento con sus etiquetas. El número exacto puede variar un poco. Al final aparece:

```text
Archivo guardado: fragmentos.json
```

En el Explorador también aparece el archivo `fragmentos.json`.

### Código a ejecutar

```powershell
python .\dividir_documentos.py
```

Programa `dividir_documentos.py`:

```python
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import json
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

CARPETA = Path(__file__).resolve().parent
CARPETA_FICHAS = CARPETA / "datos" / "productos"

# Cada ficha queda etiquetada con el tipo de producto y la categoría.
ETIQUETAS = {
    "tarjeta_visa_platinum.txt": {"tipo_producto": "tarjeta_credito", "categoria": "premium"},
    "credito_hipotecario.txt": {"tipo_producto": "credito", "categoria": "hipotecario"},
    "cuenta_ahorro_premium.txt": {"tipo_producto": "cuenta", "categoria": "ahorro"},
    "fondo_inversion_renta_fija.txt": {"tipo_producto": "inversion", "categoria": "renta_fija"},
    "seguro_vida_proteccion.txt": {"tipo_producto": "seguro", "categoria": "vida"},
}

if not CARPETA_FICHAS.exists():
    print("No encuentro la carpeta de fichas: datos\\productos.")
    print("Avisa al instructor.")
    raise SystemExit(1)

archivos = sorted(CARPETA_FICHAS.glob("*.txt"))
if len(archivos) == 0:
    print("No hay fichas en datos\\productos.")
    print("Avisa al instructor.")
    raise SystemExit(1)

documentos = []
for archivo in archivos:
    texto = archivo.read_text(encoding="utf-8-sig")
    documentos.append(Document(page_content=texto, metadata={"source": archivo.name}))
    print(f"Ficha leída: {archivo.name} ({len(texto)} caracteres)")

print(f"Fichas cargadas: {len(documentos)}")

# Corta cada ficha en fragmentos de unas 512 letras.
# Repite 50 letras entre un fragmento y el siguiente para no cortar una idea a la mitad.
cortador = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""],
)
fragmentos = cortador.split_documents(documentos)

salida = []
for indice, fragmento in enumerate(fragmentos):
    nombre = Path(str(fragmento.metadata.get("source", ""))).name
    etiquetas = ETIQUETAS.get(nombre, {"tipo_producto": "otro", "categoria": "general"})
    datos = {
        "chunk_id": f"chunk_{indice:04d}",
        "tipo_producto": etiquetas["tipo_producto"],
        "categoria": etiquetas["categoria"],
        "doc_source": nombre,
    }
    salida.append({"content": fragmento.page_content, "metadata": datos})

destino = CARPETA / "fragmentos.json"
destino.write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"Fragmentos creados: {len(salida)}")
print("Fragmentos por ficha:")
conteo = {}
for item in salida:
    nombre = item["metadata"]["doc_source"]
    conteo[nombre] = conteo.get(nombre, 0) + 1
for nombre, cantidad in conteo.items():
    print(f"  {nombre}: {cantidad}")

print("Ejemplo del primer fragmento:")
print(salida[0]["content"][:220].replace("\n", " "))
print("Etiquetas:", salida[0]["metadata"])
print("Archivo guardado: fragmentos.json")

```

---



## Paso 5. Guarda los embeddings para poder buscar



### Qué haces

Conviertes cada fragmento en números y los dejas listos para buscar por significado.

El programa `guardar_busqueda.py`:

1. Lee `fragmentos.json`.
2. Crea en Qdrant la colección `financial_products_basic`. Si ya existía, la vuelve a crear para empezar limpio. Conserva ese nombre: el siguiente taller lo busca así.
3. Pide a `text-embedding-3-small` el embedding de cada fragmento. Cada embedding tiene **1,536** números.
4. Guarda el texto, las etiquetas y el embedding. Qdrant comparará las preguntas con esos números mediante **similitud coseno**.
5. Hace una búsqueda de prueba con la frase "tasa de interés de la tarjeta de crédito" y muestra el fragmento más parecido.

La primera vez puede tardar uno o dos minutos. Espera a que aparezca el texto de la prueba. La terminal está trabajando aunque parezca quieta un momento.

### Resultado esperado

```text
Fragmentos por guardar: ...
Lugar de búsqueda creado: financial_products_basic.
Cada embedding tiene 1536 números. La comparación usa similitud coseno.
Creando los embeddings y guardándolos. Puede tardar uno o dos minutos.
Guardado terminado.
Nombre: financial_products_basic
Fragmentos guardados: ...
Estado: green
Prueba de búsqueda. El fragmento más parecido empieza así:
...
Viene de: tarjeta_visa_platinum.txt
```

El fragmento de prueba debe hablar de la tarjeta. El estado esperado es `green`.

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
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

CARPETA = Path(__file__).resolve().parent
load_dotenv(CARPETA / ".env")

NOMBRE = "financial_products_basic"
TAMANO = 1536

ruta_fragmentos = CARPETA / "fragmentos.json"
if not ruta_fragmentos.exists():
    print("Falta el archivo fragmentos.json.")
    print("Ejecuta primero dividir_documentos.py.")
    raise SystemExit(1)

fragmentos = json.loads(ruta_fragmentos.read_text(encoding="utf-8"))
documentos = [
    Document(page_content=item["content"], metadata=item["metadata"])
    for item in fragmentos
]
print(f"Fragmentos por guardar: {len(documentos)}")

host = os.getenv("QDRANT_HOST", "localhost")
puerto = int(os.getenv("QDRANT_PORT", "6333"))
cliente = QdrantClient(host=host, port=puerto, timeout=30)

if cliente.collection_exists(NOMBRE):
    print("Ya había información guardada con este nombre. Se vuelve a crear para empezar limpio.")
    cliente.delete_collection(NOMBRE)
    time.sleep(1)

# La colección guarda cada embedding: 1536 números, comparados por similitud coseno.
cliente.create_collection(
    collection_name=NOMBRE,
    vectors_config=VectorParams(size=TAMANO, distance=Distance.COSINE),
)
print(f"Lugar de búsqueda creado: {NOMBRE}.")
print("Cada embedding tiene 1536 números. La comparación usa similitud coseno.")

embeddings = OpenAIEmbeddings(
    model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
)
almacen = QdrantVectorStore(
    client=cliente,
    collection_name=NOMBRE,
    embedding=embeddings,
)

print("Creando los embeddings y guardándolos. Puede tardar uno o dos minutos.")
almacen.add_documents(documentos)

total = cliente.count(collection_name=NOMBRE, exact=True).count
info = cliente.get_collection(NOMBRE)
estado = str(info.status).split(".")[-1].lower()
print("Guardado terminado.")
print(f"Nombre: {NOMBRE}")
print(f"Fragmentos guardados: {total}")
print(f"Estado: {estado}")

prueba = almacen.similarity_search("tasa de interés de la tarjeta de crédito", k=1)
print("Prueba de búsqueda. El fragmento más parecido empieza así:")
print(prueba[0].page_content[:180].replace("\n", " "))
print("Viene de:", prueba[0].metadata.get("doc_source", "sin archivo"))

```

---



## Paso 6. Haz la misma pregunta con documentos y sin documentos



### Qué haces

Comparas las dos formas de responder una pregunta de cliente.

La pregunta es: **¿Cuál es la tasa de interés de la tarjeta Visa Platinum?**

El programa `preguntar.py` hace esto dos veces, con la misma pregunta:

**Con documentos (RAG)**

1. Convierte la pregunta en un embedding.
2. Pide a Qdrant los **4** fragmentos más parecidos.
3. Entrega esos fragmentos a GPT-4o, con la instrucción de responder solo con ese texto.
4. Muestra la respuesta y el nombre de las fichas usadas.

**Sin documentos**

Le hace la misma pregunta a GPT-4o y no le entrega las fichas. El modelo responde con lo que recuerda. Estas fichas son de un banco de práctica, así que el dato oficial de la tarjeta no forma parte de su memoria. Puede decir que no lo conoce o puede inventar una cifra. Esa cifra inventada es una alucinación.

En la respuesta con documentos debes poder reconocer **28.5%**. En la ficha también está **18.9%** para clientes con nómina.

### Resultado esperado

Dos bloques en la terminal:

- **CON DOCUMENTOS:** una respuesta que menciona 28.5%, y entre las fichas consultadas aparece `tarjeta_visa_platinum.txt`.
- **SIN DOCUMENTOS:** una respuesta que no está tomada de la ficha. Puede faltar el 28.5% o puede aparecer otra cifra.

La redacción cambia de una ejecución a otra. El dato de la ficha en el primer bloque es lo que estás buscando.

### Código a ejecutar

```powershell
python .\preguntar.py
```

Programa `preguntar.py`:

```python
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

CARPETA = Path(__file__).resolve().parent
load_dotenv(CARPETA / ".env")

NOMBRE = "financial_products_basic"

INSTRUCCIONES = """Eres un asistente del Banco Financiero Nacional.
Responde la pregunta usando solamente el contexto.
Si el dato no está en el contexto, di: "No tengo esa información en las fichas disponibles."
Cuando el contexto traiga tasas, montos o plazos, inclúyelos en la respuesta.
Responde en español, de forma breve y clara.

CONTEXTO:
{contexto}

PREGUNTA:
{pregunta}

RESPUESTA:"""


def texto_respuesta(mensaje) -> str:
    """Convierte la respuesta del modelo en un texto."""
    contenido = mensaje.content
    if isinstance(contenido, str):
        return contenido.strip()
    if isinstance(contenido, list):
        partes = []
        for bloque in contenido:
            if isinstance(bloque, str):
                partes.append(bloque)
            elif isinstance(bloque, dict):
                partes.append(str(bloque.get("text", "")))
        return "\n".join(partes).strip()
    return str(contenido).strip()


def _almacen():
    cliente = QdrantClient(
        host=os.getenv("QDRANT_HOST", "localhost"),
        port=int(os.getenv("QDRANT_PORT", "6333")),
        timeout=30,
    )
    if not cliente.collection_exists(NOMBRE):
        print("Todavía no están guardados los fragmentos.")
        print("Ejecuta primero guardar_busqueda.py.")
        raise SystemExit(1)
    embeddings = OpenAIEmbeddings(
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    )
    return QdrantVectorStore(
        client=cliente,
        collection_name=NOMBRE,
        embedding=embeddings,
    )


def _modelo():
    return ChatOpenAI(
        model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o"),
        temperature=0,
    )


def preguntar_con_documentos(pregunta: str) -> dict:
    """Busca 4 fragmentos parecidos y redacta la respuesta solo con ese texto."""
    buscador = _almacen().as_retriever(search_kwargs={"k": 4})
    encontrados = buscador.invoke(pregunta)
    contexto = "\n\n".join(documento.page_content for documento in encontrados)
    mensaje = INSTRUCCIONES.replace("{contexto}", contexto).replace("{pregunta}", pregunta)
    respuesta = _modelo().invoke(mensaje)
    return {
        "pregunta": pregunta,
        "respuesta": texto_respuesta(respuesta),
        "fuentes": [
            {
                "contenido": documento.page_content[:200],
                "metadata": documento.metadata,
            }
            for documento in encontrados
        ],
    }


def preguntar_sin_documentos(pregunta: str) -> str:
    """Hace la misma pregunta al modelo, sin entregarle las fichas."""
    respuesta = _modelo().invoke(
        "Responde la siguiente pregunta sobre productos del Banco Financiero Nacional: "
        + pregunta
    )
    return texto_respuesta(respuesta)


def main():
    pregunta = "¿Cuál es la tasa de interés de la tarjeta Visa Platinum?"

    print("=" * 60)
    print("CON DOCUMENTOS")
    print("=" * 60)
    resultado = preguntar_con_documentos(pregunta)
    print(f"Pregunta: {resultado['pregunta']}")
    print()
    print(resultado["respuesta"])
    print()
    print(f"Fichas consultadas: {len(resultado['fuentes'])}")
    for numero, fuente in enumerate(resultado["fuentes"], 1):
        metadatos = fuente["metadata"]
        print(f"  {numero}. {metadatos.get('doc_source', 'sin archivo')}")
        print(f"     Tipo de producto: {metadatos.get('tipo_producto', 'sin tipo')}")

    print()
    print("=" * 60)
    print("SIN DOCUMENTOS")
    print("=" * 60)
    print(f"Pregunta: {pregunta}")
    print()
    print(preguntar_sin_documentos(pregunta))


if __name__ == "__main__":
    main()

```

---



## Paso 7. Compara diez preguntas



### Qué haces

Repites la comparación con diez preguntas. Cada una tiene un dato que sí está escrito en las fichas.

El programa `comparar_respuestas.py`:

1. Recorre las diez preguntas.
2. En cada una llama a la consulta con documentos y a la consulta sin documentos.
3. Revisa si la respuesta incluye el dato de la ficha.
4. Al final cuenta cuántas respuestas trajeron ese dato en cada forma.
5. Guarda el detalle en `resultados_evaluacion.json`.

Este paso hace muchas consultas. Puede tardar varios minutos. Espera hasta ver la palabra **RESUMEN**. Puedes leer cada pregunta mientras avanza.

Lo habitual es que **con documentos** aparezca el dato en la mayoría de las respuestas, y **sin documentos** en pocas o en ninguna.

### Resultado esperado

Diez bloques, uno por pregunta, y al final un resumen parecido a este:

```text
RESUMEN
Con documentos: 8 de 10
Sin documentos: 1 de 10
Diferencia: 7 respuestas más con documentos
Archivo guardado: resultados_evaluacion.json
```

Los números pueden cambiar. La señal del taller es que el conteo con documentos quede por encima del conteo sin documentos.

Si una respuesta se ve correcta y el programa dice "no", lee el texto: a veces el modelo escribió el dato con otras palabras y la revisión automática no lo reconoció. La lectura de las dos respuestas es la comprobación.

### Código a ejecutar

```powershell
python .\comparar_respuestas.py
```

Programa `comparar_respuestas.py`:

```python
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import json
import time
from pathlib import Path

from preguntar import preguntar_con_documentos, preguntar_sin_documentos

CARPETA = Path(__file__).resolve().parent

# Cada pregunta tiene un dato que sí está escrito en las fichas.
PREGUNTAS = [
    {
        "id": 1,
        "pregunta": "¿Cuál es la tasa de interés anual del crédito hipotecario para clientes con nómina?",
        "respuesta_esperada": "9.85%",
        "claves": ["9.85"],
    },
    {
        "id": 2,
        "pregunta": "¿Cuántos puntos de recompensa otorga la tarjeta Visa Platinum por cada dólar de compra?",
        "respuesta_esperada": "1.5 puntos",
        "claves": ["1.5"],
    },
    {
        "id": 3,
        "pregunta": "¿Cuál es el rendimiento anualizado del fondo BFN Estabilidad en los últimos 12 meses?",
        "respuesta_esperada": "11.2%",
        "claves": ["11.2"],
    },
    {
        "id": 4,
        "pregunta": "¿Cuál es el saldo mínimo para abrir la Cuenta de Ahorro Premium Plus?",
        "respuesta_esperada": "$10,000",
        "claves": ["10,000", "10000", "10.000"],
    },
    {
        "id": 5,
        "pregunta": "¿Qué porcentaje de la suma asegurada se paga por muerte accidental en el seguro de vida?",
        "respuesta_esperada": "200%",
        "claves": ["200%"],
    },
    {
        "id": 6,
        "pregunta": "¿Cuál es la penalización por prepago total del crédito hipotecario antes del tercer año?",
        "respuesta_esperada": "2% del saldo insoluto",
        "claves": ["2% del saldo", "2% sobre el saldo", "2 por ciento del saldo"],
    },
    {
        "id": 7,
        "pregunta": "¿Cuántos retiros mensuales sin comisión permite la cuenta de ahorro premium?",
        "respuesta_esperada": "6 retiros",
        "claves": ["6 retiros", "seis retiros"],
    },
    {
        "id": 8,
        "pregunta": "¿Cuál es la comisión total anual del fondo de inversión en renta fija?",
        "respuesta_esperada": "1.00%",
        "claves": ["1.00"],
    },
    {
        "id": 9,
        "pregunta": "¿Cuál es la prima mensual estimada del seguro de vida para un hombre de 40 años no fumador con suma asegurada de $3,000,000?",
        "respuesta_esperada": "$780/mes",
        "claves": ["780"],
    },
    {
        "id": 10,
        "pregunta": "¿Cuál es el ingreso mínimo mensual requerido para solicitar la tarjeta Visa Platinum?",
        "respuesta_esperada": "$15,000",
        "claves": ["15,000", "15000", "15.000"],
    },
]


def normalizar(texto: str) -> str:
    return texto.lower().replace("$", "").replace(",", "").replace(" ", "")


def contiene_dato(respuesta: str, claves: list[str]) -> bool:
    """Revisa si la respuesta incluye el dato que está en la ficha."""
    texto = normalizar(respuesta)
    return any(normalizar(clave) in texto for clave in claves)


def main():
    print("=" * 60)
    print("COMPARACIÓN: CON DOCUMENTOS Y SIN DOCUMENTOS")
    print("Este paso hace varias consultas. Puede tardar unos minutos.")
    print("=" * 60)

    correctas_con = 0
    correctas_sin = 0
    detalle = []

    for item in PREGUNTAS:
        print()
        print("-" * 60)
        print(f"Pregunta {item['id']} de {len(PREGUNTAS)}")
        print(item["pregunta"])
        print(f"Dato de la ficha: {item['respuesta_esperada']}")

        try:
            resultado = preguntar_con_documentos(item["pregunta"])
            respuesta_con = resultado["respuesta"]
            fuentes = [
                fuente["metadata"].get("doc_source")
                for fuente in resultado["fuentes"]
            ]
        except Exception as error:
            respuesta_con = f"No se pudo consultar: {error}"
            fuentes = []

        acierto_con = contiene_dato(respuesta_con, item["claves"])
        if acierto_con:
            correctas_con += 1
        print()
        print("Con documentos:")
        print(respuesta_con[:300])
        print("Dato de la ficha presente:", "sí" if acierto_con else "no")

        time.sleep(1)

        try:
            respuesta_sin = preguntar_sin_documentos(item["pregunta"])
        except Exception as error:
            respuesta_sin = f"No se pudo consultar: {error}"

        acierto_sin = contiene_dato(respuesta_sin, item["claves"])
        if acierto_sin:
            correctas_sin += 1
        print()
        print("Sin documentos:")
        print(respuesta_sin[:300])
        print("Dato de la ficha presente:", "sí" if acierto_sin else "no")

        detalle.append(
            {
                "id": item["id"],
                "pregunta": item["pregunta"],
                "respuesta_esperada": item["respuesta_esperada"],
                "respuesta_con_documentos": respuesta_con,
                "correcto_con_documentos": acierto_con,
                "respuesta_sin_documentos": respuesta_sin,
                "correcto_sin_documentos": acierto_sin,
                "fuentes": fuentes,
            }
        )
        time.sleep(1)

    total = len(PREGUNTAS)
    print()
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Con documentos: {correctas_con} de {total}")
    print(f"Sin documentos: {correctas_sin} de {total}")
    print(f"Diferencia: {correctas_con - correctas_sin} respuestas más con documentos")

    salida = {
        "resumen": {
            "total_preguntas": total,
            "correctas_con_documentos": correctas_con,
            "correctas_sin_documentos": correctas_sin,
        },
        "detalle": detalle,
    }
    destino = CARPETA / "resultados_evaluacion.json"
    destino.write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Archivo guardado: resultados_evaluacion.json")


if __name__ == "__main__":
    main()

```

---



## Paso 8. Haz tus propias preguntas



### Qué haces

Consultas las fichas con preguntas tuyas.

El programa `preguntar_libre.py` espera tu texto en la terminal. En cada pregunta:

1. Busca los 4 fragmentos más parecidos.
2. Pide a GPT-4o que responda solo con esos fragmentos.
3. Muestra la respuesta, el archivo de origen y el tipo de producto.

Escribe una pregunta y presiona **Enter**. Cuando quieras terminar, escribe `salir` y presiona **Enter**.

Puedes empezar con estas:

- ¿Qué requisitos necesito para un crédito hipotecario?
- ¿El fondo de inversión tiene comisión de salida?
- ¿Cuánto cuesta la anualidad de la tarjeta Visa Platinum?

En la anualidad, la ficha dice **$2,800**, y el primer año se bonifica si la facturación mensual supera **$8,000**.

### Resultado esperado

La terminal muestra una respuesta y, debajo, las fichas usadas. En la pregunta del crédito hipotecario, la fuente debe incluir `credito_hipotecario.txt`. En la del fondo, `fondo_inversion_renta_fija.txt`.

Para seguir, escribe `salir`. Debes ver: `Listo. Puedes continuar con el resumen.`

### Código a ejecutar

```powershell
python .\preguntar_libre.py
```

Programa `preguntar_libre.py`:

```python
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from preguntar import preguntar_con_documentos


def main():
    print("=" * 60)
    print("Preguntas sobre productos del Banco Financiero Nacional")
    print("=" * 60)
    print("Escribe una pregunta y presiona Enter.")
    print("Escribe salir para terminar.")
    print()
    print("Puedes probar con estas:")
    print("- ¿Qué requisitos necesito para un crédito hipotecario?")
    print("- ¿El fondo de inversión tiene comisión de salida?")
    print("- ¿Cuánto cuesta la anualidad de la tarjeta Visa Platinum?")
    print()

    while True:
        pregunta = input("Tu pregunta: ").strip()
        if pregunta.lower() in {"salir", "exit", "quit", "q"}:
            print("Listo. Puedes continuar con el resumen.")
            break
        if not pregunta:
            continue

        print("Buscando en las fichas...")
        try:
            resultado = preguntar_con_documentos(pregunta)
        except Exception as error:
            print("No se pudo completar la pregunta.")
            print("Avisa al instructor.")
            print(f"Detalle: {error}")
            continue

        print()
        print("Respuesta:")
        print(resultado["respuesta"])
        print()
        print(f"Fichas usadas: {len(resultado['fuentes'])}")
        for numero, fuente in enumerate(resultado["fuentes"], 1):
            metadatos = fuente["metadata"]
            print(f"  {numero}. {metadatos.get('doc_source', 'sin archivo')}")
            print(f"     Tipo: {metadatos.get('tipo_producto', 'sin tipo')}")
            print(f"     Fragmento: {fuente['contenido'][:120].replace(chr(10), ' ')}")
        print()


if __name__ == "__main__":
    main()

```

---



## Paso 9. Abre el resumen



### Qué haces

Reúnes el resultado en un texto que puedes leer en Visual Studio Code.

El programa `ver_resumen.py`:

1. Lee `resultados_evaluacion.json`, el conteo del paso 7.
2. Consulta cuántos fragmentos hay en la colección `financial_products_basic`.
3. Escribe `RESUMEN.md` con las partes del sistema, la tabla de las diez preguntas y lo que se observa al comparar las dos formas de responder.



### Resultado esperado

```text
Resumen guardado: RESUMEN.md
Ábrelo en Visual Studio Code.
Con documentos: ... de 10
Sin documentos: ... de 10
```

Abre `RESUMEN.md` en el Explorador. Ahí quedan la colección, el número de fragmentos y la comparación.

### Código a ejecutar

```powershell
python .\ver_resumen.py
```

Programa `ver_resumen.py`:

```python
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from qdrant_client import QdrantClient

CARPETA = Path(__file__).resolve().parent
load_dotenv(CARPETA / ".env")

ruta_resultados = CARPETA / "resultados_evaluacion.json"
if not ruta_resultados.exists():
    print("Falta resultados_evaluacion.json.")
    print("Ejecuta primero comparar_respuestas.py.")
    raise SystemExit(1)

evaluacion = json.loads(ruta_resultados.read_text(encoding="utf-8"))
resumen = evaluacion["resumen"]
total = resumen["total_preguntas"]
con_documentos = resumen["correctas_con_documentos"]
sin_documentos = resumen["correctas_sin_documentos"]

host = os.getenv("QDRANT_HOST", "localhost")
puerto = int(os.getenv("QDRANT_PORT", "6333"))
cliente = QdrantClient(host=host, port=puerto, timeout=10)
info = cliente.get_collection("financial_products_basic")
guardados = cliente.count(collection_name="financial_products_basic", exact=True).count
estado = str(info.status).split(".")[-1].lower()

filas = ""
for item in evaluacion["detalle"]:
    marca_con = "sí" if item["correcto_con_documentos"] else "no"
    marca_sin = "sí" if item["correcto_sin_documentos"] else "no"
    filas += (
        f"| {item['id']} | {item['pregunta']} | {item['respuesta_esperada']} | "
        f"{marca_con} | {marca_sin} |\n"
    )

reporte = f"""# Resumen del taller: consulta de productos con documentos

Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M")}

## Qué quedó armado

- Documentos: 5 fichas de productos en `datos/productos`.
- Fragmentos: cada ficha se cortó en pedazos de unas 512 letras, con 50 letras repetidas entre un pedazo y el siguiente.
- Embeddings: el modelo `text-embedding-3-small` convirtió cada fragmento en una lista de 1536 números.
- Búsqueda: esos números están en Qdrant, en la colección `financial_products_basic`.
- Fragmentos guardados: {guardados}.
- Estado de la colección: {estado}.
- Comparación de textos: similitud coseno.
- Respuesta: GPT-4o redacta usando los 4 fragmentos más parecidos a la pregunta.

## Resultado de las 10 preguntas

- Preguntas: {total}
- Respuestas con el dato de la ficha, usando documentos: {con_documentos} de {total}
- Respuestas con el dato de la ficha, sin documentos: {sin_documentos} de {total}

| # | Pregunta | Dato de la ficha | Con documentos | Sin documentos |
|---|---|---|---|---|
{filas}
## Qué se observa

La respuesta que usa las fichas puede citar la tasa, el monto o el plazo que está escrito en el documento, y puede mostrar de qué archivo salió.

La respuesta sin fichas trabaja solo con lo que el modelo recuerda. Estas fichas son de un banco de práctica, así que el modelo normalmente no tiene esas cifras. Puede decir que no las conoce o puede inventar un número. Inventar un dato que no está en la ficha se llama alucinación.

## Límites de esta consulta

- Si un fragmento corta una frase en mal lugar, el modelo puede quedarse sin una parte del dato.
- La búsqueda compara significados. Una pregunta con palabras muy distintas a las de la ficha puede traer otro fragmento.
- Solo se envían 4 fragmentos al modelo.
- Una pregunta que necesite varios productos a la vez es más difícil con este recorte.

## Para el siguiente taller

La colección `financial_products_basic` y las fichas se conservan. El siguiente taller puede mejorar la búsqueda combinando palabras exactas y significado, ordenando mejor los fragmentos y usando las etiquetas de tipo de producto.
"""

destino = CARPETA / "RESUMEN.md"
destino.write_text(reporte, encoding="utf-8")
print(f"Resumen guardado: {destino.name}")
print("Ábrelo en Visual Studio Code.")
print(f"Con documentos: {con_documentos} de {total}")
print(f"Sin documentos: {sin_documentos} de {total}")

```

---



## Si algo no sale como esperas


| Lo que ves                                  | Qué hacer                                                                       |
| ------------------------------------------- | ------------------------------------------------------------------------------- |
| `python` no se reconoce                     | Avisa al instructor. El equipo todavía no tiene Python listo.                   |
| Falta la clave de OpenAI, o un error 401    | Avisa al instructor. La clave está en `.env`.                                   |
| Error 429 o un mensaje de cuota             | Avisa al instructor. La cuenta de OpenAI necesita saldo.                        |
| No hay conexión con Qdrant                  | Avisa al instructor. Qdrant debe estar encendido en este servidor.              |
| `Falta el archivo fragmentos.json`          | Vuelve al paso 4 y ejecuta `python .\dividir_documentos.py`.                    |
| `Todavía no están guardados los fragmentos` | Vuelve al paso 5 y ejecuta `python .\guardar_busqueda.py`.                      |
| El paso 7 parece detenido                   | Espera. Está consultando las diez preguntas. Sigue cuando aparezca **RESUMEN**. |
| Quieres salir del paso 8                    | Escribe `salir` y presiona Enter.                                               |


Si un programa se queda esperando y necesitas cortarlo, haz clic en la terminal y presiona `Ctrl+C`. Luego vuelve a ejecutar el paso.

## Qué te llevas


| Parte       | Cómo quedó en este taller                                                    |
| ----------- | ---------------------------------------------------------------------------- |
| Documentos  | 5 fichas en `datos\productos`                                                |
| Fragmentos  | Corte de 512 letras, con 50 letras repetidas                                 |
| Etiquetas   | Archivo, tipo de producto y categoría                                        |
| Embeddings  | `text-embedding-3-small`, 1,536 números                                      |
| Búsqueda    | Qdrant, colección `financial_products_basic`, similitud coseno, 4 fragmentos |
| Respuesta   | GPT-4o, usando solo el texto recuperado                                      |
| Comparación | 10 preguntas con documentos y sin documentos                                 |


La herramienta que une el corte, la búsqueda y la redacción se llama **LangChain**.

## Conserva este trabajo

Deja Qdrant encendido y no borres la colección `financial_products_basic`. El siguiente taller parte de estos fragmentos para mejorar la búsqueda: combinar palabras exactas con el significado, ordenar mejor los fragmentos y usar las etiquetas de tipo de producto.

Antes de cerrar, responde con tus palabras: ¿qué dato de una ficha apareció en la respuesta con documentos y qué pasó con ese mismo dato en la respuesta sin documentos?
---LAB---
