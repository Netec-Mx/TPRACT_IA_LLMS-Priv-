# Prerrequisitos del taller

Este archivo es para quien prepara el equipo: instructor o soporte. Los participantes del taller no instalan programas, librerías ni bases de datos. Ellos siguen solo [README.md](README.md).

Este taller continúa el capítulo 1 en el mismo Windows Server. Visual Studio Code, Python y Qdrant ya deben estar listos, y Qdrant debe seguir encendido. La colección `financial_products_basic` del capítulo 1 se conserva.

La terminal de los participantes es PowerShell.

## Qué debe quedar listo

| Pieza | Para qué sirve |
|---|---|
| Lo preparado en el capítulo 1 | Visual Studio Code, Python, Qdrant y la clave de OpenAI |
| Elasticsearch 8 en Windows | Busca por palabras exactas (BM25), en español |
| Clave de Cohere | Vuelve a ordenar los fragmentos según la pregunta |
| Librerías nuevas de Python | Elasticsearch, Cohere y la evaluación RAGAS |
| Carpeta `C:\TallerRAG\Capitulo02` | Carpeta de trabajo de este taller |
| Archivo `.env` dentro de esa carpeta | Claves de OpenAI y Cohere, y direcciones de Qdrant y Elasticsearch |

La carpeta de trabajo se llama `Capitulo02`. El nombre lleva el cero: `Capitulo02`. La sección 3 explica cómo crearla y cómo dejar dentro cada archivo.

## 1. Librerías nuevas

En una ventana de PowerShell distinta de la de Qdrant:

```powershell
python -m pip install elasticsearch cohere ragas datasets
```

| Librería | Uso en el taller |
|---|---|
| `elasticsearch` | Guarda y busca los fragmentos por palabras |
| `cohere` | Reordena los fragmentos con la pregunta |
| `ragas` y `datasets` | Calculan fidelidad, relevancia y precisión del contexto |

Python, LangChain, Qdrant y OpenAI quedan como los instaló el capítulo 1. Si este servidor no tiene el capítulo 1, prepara primero [Prerequisitos.md](../Capitulo01/Prerequisitos.md) y deja Qdrant encendido.

## 2. Elasticsearch en Windows Server

Elasticsearch es la búsqueda por palabras. Se instala aparte de Qdrant. Las dos quedan encendidas al mismo tiempo.

### 2.1 Descargar y colocar el programa

1. Descarga el zip de Windows de Elasticsearch 8.19:

https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.19.23-windows-x86_64.zip

2. Descomprime el zip.
3. Renombra la carpeta descomprimida a `C:\Elasticsearch`. Dentro debe existir `C:\Elasticsearch\bin\elasticsearch.bat`.

### 2.2 Dejarlo sin contraseña, antes del primer arranque

Abre `C:\Elasticsearch\config\elasticsearch.yml` con Visual Studio Code. Al final del archivo agrega estas dos líneas:

```yaml
discovery.type: single-node
xpack.security.enabled: false
```

Guarda el archivo. Hazlo antes de iniciar Elasticsearch por primera vez. Así el taller se conecta a `http://localhost:9200` sin usuario ni contraseña.

### 2.3 Iniciar Elasticsearch

Abre PowerShell y ejecuta:

```powershell
$env:ES_JAVA_OPTS = "-Xms512m -Xmx512m"
Set-Location C:\Elasticsearch\bin
.\elasticsearch.bat
```

Deja esa ventana abierta durante todo el taller. En el navegador del servidor abre `http://localhost:9200`. Debes ver un texto con `"tagline" : "You Know, for Search"`.

Qdrant sigue en su propia ventana. No la cierres.

### 2.4 Si pide contraseña o no arranca

Eso pasa cuando Elasticsearch ya arrancó una vez con la seguridad automática.

1. Cierra la ventana de Elasticsearch.
2. Borra la carpeta `C:\Elasticsearch\data`.
3. Confirma que `elasticsearch.yml` tiene las dos líneas del paso 2.2.
4. Vuelve a ejecutar `elasticsearch.bat`.

## 3. Crear la carpeta Capitulo02 y sus archivos

La carpeta de trabajo es:

`C:\TallerRAG\Capitulo02`

Ahí viven la guía y los programas. Los documentos de productos los crea el participante al ejecutar `crear_documentos.py`. No los copies a mano.

Estos archivos aparecen durante la sesión. No los crees ahora:

- `datos\documentos\`
- `configuracion.json`
- `resultados_evaluacion.json`
- `RESUMEN.md`

Si Qdrant o Elasticsearch ya están corriendo, abre otra ventana de PowerShell para estos comandos.

### 3.1 Crear la carpeta

#### Qué haces

Creas la carpeta de trabajo de este taller. `New-Item` la crea. `-Force` permite ejecutarlo de nuevo si la carpeta ya existe.

#### Resultado esperado

En el Explorador de archivos existe `C:\TallerRAG\Capitulo02`.

#### Código a ejecutar

```powershell
New-Item -ItemType Directory -Force -Path "C:\TallerRAG\Capitulo02"
```

### 3.2 Copiar los archivos del material

Los archivos salen de la carpeta `Capitulo02` del material del curso: la misma carpeta donde está este `Prerequisitos.md`.

#### Qué haces

Copias esa carpeta a `C:\TallerRAG\Capitulo02`. Entran la guía, este archivo y los programas `.py`. Sustituye `PEGA_AQUI_LA_RUTA` por la ruta real del material. En Visual Studio Code: clic derecho en la carpeta `Capitulo02` del material, **Copiar ruta**.

Si el material ya está en `C:\TallerRAG\Capitulo02`, no lo copies sobre sí mismo. Pasa al paso 3.3.

#### Resultado esperado

```text
C:\TallerRAG\Capitulo02
├── README.md
├── Prerequisitos.md
├── herramientas.py
├── revisar_entorno.py
├── crear_documentos.py
├── comparar_cortes.py
├── guardar_busqueda.py
├── guardar_palabras.py
├── buscar_hibrido.py
├── responder.py
└── evaluar.py
```

#### Código a ejecutar

```powershell
$origen = "PEGA_AQUI_LA_RUTA\Capitulo02"
$destino = "C:\TallerRAG\Capitulo02"
Copy-Item -Path (Join-Path $origen "*") -Destination $destino -Recurse -Force
Remove-Item -LiteralPath (Join-Path $destino "__pycache__") -Recurse -Force -ErrorAction SilentlyContinue
```

### 3.3 Comprobar que están todos los archivos

#### Qué haces

El comando revisa los 11 archivos del taller. Escribe `OK` cuando el archivo está y `FALTA` cuando no está.

#### Resultado esperado

Once líneas `OK` y ninguna línea `FALTA`.

#### Código a ejecutar

```powershell
$base = "C:\TallerRAG\Capitulo02"
$archivos = @(
  "README.md",
  "Prerequisitos.md",
  "herramientas.py",
  "revisar_entorno.py",
  "crear_documentos.py",
  "comparar_cortes.py",
  "guardar_busqueda.py",
  "guardar_palabras.py",
  "buscar_hibrido.py",
  "responder.py",
  "evaluar.py"
)
foreach ($relativo in $archivos) {
  $ruta = Join-Path $base $relativo
  if (Test-Path -LiteralPath $ruta) {
    Write-Output "OK     $relativo"
  } else {
    Write-Output "FALTA  $relativo"
  }
}
```

## 4. Claves y archivo .env

Hace falta una clave de OpenAI con saldo y una clave de Cohere. La clave de Cohere se crea en https://dashboard.cohere.com/api-keys. El plan gratuito alcanza para este taller.

El archivo `.env` se crea en `C:\TallerRAG\Capitulo02`.

### Qué haces

El comando crea `.env` con las dos claves, Qdrant, Elasticsearch y los modelos. Después abres el archivo y sustituyes las dos claves de ejemplo por las claves reales.

Cada clave va en una sola línea, sin comillas y sin espacios alrededor del signo `=`.

`COHERE_RERANK_MODEL` se queda en `rerank-multilingual-v3.0` porque los documentos están en español. `OPENAI_EMBEDDING_MODEL` se queda en `text-embedding-3-small`.

No subas `.env` a un repositorio.

### Resultado esperado

Existe `C:\TallerRAG\Capitulo02\.env` con las claves reales.

### Código a ejecutar

```powershell
@"
OPENAI_API_KEY=sk-coloca-aqui-la-clave-real
COHERE_API_KEY=coloca-aqui-la-clave-cohere
QDRANT_HOST=localhost
QDRANT_PORT=6333
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o
COHERE_RERANK_MODEL=rerank-multilingual-v3.0
"@ | Set-Content -LiteralPath "C:\TallerRAG\Capitulo02\.env" -Encoding utf8
```

Para poner las claves reales:

1. En Visual Studio Code, menú **Archivo** > **Abrir carpeta**.
2. Elige `C:\TallerRAG\Capitulo02`.
3. Abre `.env` y sustituye las dos claves de ejemplo.
4. Guarda con `Ctrl+S`.

## 5. Prueba antes de la sesión

Qdrant y Elasticsearch deben estar encendidos.

1. La carpeta abierta en Visual Studio Code es `C:\TallerRAG\Capitulo02`.
2. **Terminal** > **Nueva terminal**, en PowerShell.
3. Si la ruta no termina en `Capitulo02`, ejecuta:

```powershell
Set-Location C:\TallerRAG\Capitulo02
```

4. Ejecuta:

```powershell
python .\revisar_entorno.py
```

Resultado esperado:

```text
Embeddings listos. Cada lista tiene 1536 números.
Modelo de respuestas listo. Dijo: LISTO
Qdrant listo en localhost:6333.
Colección del primer taller lista. Fragmentos: ...
Búsqueda por palabras lista. Elasticsearch 8.19.23, estado green o yellow.
Reordenamiento listo con Cohere.
Todo listo. Puedes continuar.
```

La versión de Elasticsearch puede variar dentro de la serie 8. El estado puede decir `green` o `yellow`. La frase **Todo listo** debe aparecer.

## 6. Durante la sesión

- Qdrant permanece encendido.
- Elasticsearch permanece encendido.
- Los participantes abren `C:\TallerRAG\Capitulo02` en Visual Studio Code.
- Los participantes no instalan software ni ejecutan `pip`.
- La colección nueva se llama `financial_products_optimized`. La del capítulo 1, `financial_products_basic`, se conserva.

## 7. Limpieza, solo al cerrar todos los talleres

Cierra la ventana de `elasticsearch.bat`. Qdrant puede seguir si todavía se usa el capítulo 1.

Para apagar Qdrant, cierra su ventana o, si lo iniciaste con Docker en el capítulo 1, usa las instrucciones de limpieza de ese capítulo.
