# Prerrequisitos del taller

Este archivo es para quien prepara el equipo: instructor o soporte. Los participantes del taller no instalan programas, librerías ni bases de datos. Ellos siguen solo [README.md](README.md).

El taller se usa en el mismo Windows Server donde están Visual Studio Code y la base de búsqueda. La terminal de los participantes es PowerShell.

Prepara el equipo antes de la sesión y deja Qdrant encendido.

## Qué debe quedar listo

| Pieza | Para qué sirve |
|---|---|
| Windows Server | Equipo donde trabajan los participantes |
| Visual Studio Code | Ahí abren la carpeta del taller y la terminal |
| Extensión Python de Visual Studio Code | Para leer los programas con color |
| Python 3.11 o 3.12 | Ejecuta los programas del taller |
| Librerías de Python | Conectan las fichas, OpenAI y Qdrant |
| Microsoft Visual C++ Redistributable | Qdrant lo necesita en Windows Server |
| Qdrant 1.16.2 o superior | Guarda los embeddings y permite buscarlos |
| Clave de OpenAI con saldo | Crea los embeddings y redacta las respuestas |
| Internet | Llega a la API de OpenAI |
| Carpeta `C:\TallerRAG\Capitulo01` | Carpeta de trabajo del taller, con sus programas y fichas |
| Archivo `.env` dentro de esa carpeta | Guarda la clave y los nombres de los modelos |

La carpeta de trabajo se llama `Capitulo01`. El nombre lleva el cero: `Capitulo01`. Los participantes abren esa carpeta en Visual Studio Code. La sección 5 explica cómo crearla y cómo dejar dentro cada archivo.

## 1. Visual Studio Code

1. Instala Visual Studio Code para Windows.
2. Abre Visual Studio Code.
3. Instala la extensión **Python** (editora: Microsoft).
4. Deja PowerShell como terminal:
   - Menú **Terminal** > **Nueva terminal**.
   - Si aparece **cmd** o **Command Prompt**, abre la lista de la terminal y elige **PowerShell**.

## 2. Python

1. Instala Python 3.11 o 3.12 para todos los usuarios.
2. En el instalador, marca **Add python.exe to PATH**.
3. Cierra y vuelve a abrir PowerShell.
4. Comprueba:

```powershell
python --version
```

Debes ver `Python 3.11` o `Python 3.12`.

Para que la terminal muestre bien las tildes:

```powershell
setx PYTHONUTF8 1
```

Cierra PowerShell y ábrelo de nuevo después de `setx`.

## 3. Librerías

Abre PowerShell y ejecuta:

```powershell
python -m pip install --upgrade pip
python -m pip install langchain langchain-openai langchain-qdrant langchain-text-splitters qdrant-client openai python-dotenv
```

Estas librerías cubren el taller:

| Librería | Uso en el taller |
|---|---|
| `langchain` y `langchain-text-splitters` | Cortan las fichas en fragmentos |
| `langchain-openai` | Pide embeddings y respuestas a OpenAI |
| `langchain-qdrant` y `qdrant-client` | Guardan y buscan en Qdrant |
| `openai` | Prueba la conexión con OpenAI |
| `python-dotenv` | Lee la clave desde `.env` |

Qdrant en el servidor debe ser versión **1.10 o superior**. La versión recomendada es **1.16.2**.

## 4. Qdrant en Windows Server

### 4.1 Visual C++

Instala el Microsoft Visual C++ Redistributable más reciente para x64:

https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist

En Windows Server, Qdrant puede cerrarse al instante si falta este componente.

### 4.2 Programa de Qdrant

1. Descarga el paquete de Windows desde la release **v1.16.2**:

https://github.com/qdrant/qdrant/releases/download/v1.16.2/qdrant-x86_64-pc-windows-msvc.zip

2. Descomprime el zip en `C:\Qdrant`.
3. Abre **PowerShell** en esa carpeta. Qdrant se inicia desde la terminal. Un doble clic sobre `qdrant.exe` no es la forma de arrancarlo.
4. Ejecuta:

```powershell
Set-Location C:\Qdrant
.\qdrant.exe
```

5. Deja esa ventana abierta durante todo el taller. Qdrant atiende en `http://localhost:6333`.
6. En el navegador del servidor, abre `http://localhost:6333/dashboard`. Debes ver la pantalla de Qdrant.

La carpeta `C:\Qdrant\storage` guarda los datos. No la borres si vas a continuar con el siguiente taller.

### 4.3 Si el programa se cierra solo

1. Confirma que el Visual C++ Redistributable quedó instalado.
2. Vuelve a ejecutarlo desde PowerShell, no con doble clic.
3. Si el servidor ya tiene Docker Engine, puedes usar esta alternativa. El almacenamiento queda en un volumen de Docker, no en una carpeta de Windows montada dentro del contenedor:

```powershell
docker run -d --name qdrant-financiero -p 6333:6333 -p 6334:6334 -v qdrant-storage:/qdrant/storage qdrant/qdrant:v1.16.2
```

Comprueba que sigue en marcha:

```powershell
docker ps --filter name=qdrant-financiero
```

## 5. Crear la carpeta Capitulo01 y sus archivos

La carpeta de trabajo del taller es:

`C:\TallerRAG\Capitulo01`

Ahí viven la guía, los programas y las fichas. El archivo `.env` se crea en el paso 6, dentro de esta misma carpeta. Estos archivos aparecen durante la sesión, cuando los participantes ejecutan los programas; no los crees ahora:

- `fragmentos.json`
- `resultados_evaluacion.json`
- `RESUMEN.md`

Si Qdrant ya está corriendo en una ventana de PowerShell, abre **otra** ventana para estos comandos. La ventana de Qdrant se queda abierta.

### 5.1 Crear las carpetas

#### Qué haces

Creas la carpeta del taller y la subcarpeta donde van las cinco fichas de productos. `New-Item` crea las dos. `-Force` permite ejecutarlo de nuevo si la carpeta ya existe.

#### Resultado esperado

PowerShell muestra las carpetas creadas. En el Explorador de archivos de Windows deben existir:

```text
C:\TallerRAG\Capitulo01
C:\TallerRAG\Capitulo01\datos\productos
```

#### Código a ejecutar

```powershell
New-Item -ItemType Directory -Force -Path "C:\TallerRAG\Capitulo01\datos\productos"
```

### 5.2 Copiar los archivos del material

Los archivos salen de la carpeta `Capitulo01` del material del curso: la misma carpeta donde está este `Prerequisitos.md`.

#### Qué haces

Copias esa carpeta completa a `C:\TallerRAG\Capitulo01`. El comando copia la guía, los programas `.py` y las cinco fichas. Después borra `__pycache__` si venía en el material; esa carpeta no forma parte del taller.

Antes de ejecutar, sustituye `PEGA_AQUI_LA_RUTA` por la ruta real del material. En Visual Studio Code puedes copiarla así: clic derecho en la carpeta `Capitulo01` del material, **Copiar ruta**.

Si el material ya está en `C:\TallerRAG\Capitulo01`, no lo copies sobre sí mismo. Pasa a la comprobación del paso 5.3.

#### Resultado esperado

PowerShell termina sin mensajes de error. La carpeta de trabajo queda así:

```text
C:\TallerRAG\Capitulo01
├── README.md
├── Prerequisitos.md
├── revisar_entorno.py
├── dividir_documentos.py
├── guardar_busqueda.py
├── preguntar.py
├── comparar_respuestas.py
├── preguntar_libre.py
├── ver_resumen.py
└── datos
    └── productos
        ├── tarjeta_visa_platinum.txt
        ├── credito_hipotecario.txt
        ├── cuenta_ahorro_premium.txt
        ├── fondo_inversion_renta_fija.txt
        └── seguro_vida_proteccion.txt
```

El archivo `.env` todavía no está. Lo creas en el paso 6.

#### Código a ejecutar

```powershell
$origen = "PEGA_AQUI_LA_RUTA\Capitulo01"
$destino = "C:\TallerRAG\Capitulo01"
Copy-Item -Path (Join-Path $origen "*") -Destination $destino -Recurse -Force
Remove-Item -LiteralPath (Join-Path $destino "__pycache__") -Recurse -Force -ErrorAction SilentlyContinue
```

### 5.3 Comprobar que están todos los archivos

#### Qué haces

El comando revisa, uno por uno, los 14 archivos del taller. Escribe `OK` cuando el archivo está y `FALTA` cuando no está.

#### Resultado esperado

Catorce líneas `OK` y ninguna línea `FALTA`. Si aparece `FALTA`, repite el paso 5.2 y confirma que `$origen` apunta a la carpeta `Capitulo01` del material.

#### Código a ejecutar

```powershell
$base = "C:\TallerRAG\Capitulo01"
$archivos = @(
  "README.md",
  "Prerequisitos.md",
  "revisar_entorno.py",
  "dividir_documentos.py",
  "guardar_busqueda.py",
  "preguntar.py",
  "comparar_respuestas.py",
  "preguntar_libre.py",
  "ver_resumen.py",
  "datos\productos\tarjeta_visa_platinum.txt",
  "datos\productos\credito_hipotecario.txt",
  "datos\productos\cuenta_ahorro_premium.txt",
  "datos\productos\fondo_inversion_renta_fija.txt",
  "datos\productos\seguro_vida_proteccion.txt"
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

## 6. Clave de OpenAI y archivo .env

Usa una clave de OpenAI con saldo. El taller llama a los modelos `text-embedding-3-small` y `gpt-4o`.

El archivo `.env` se crea en `C:\TallerRAG\Capitulo01`. En Windows, un nombre que empieza por punto se crea con este comando o desde Visual Studio Code. El Explorador de archivos a menudo no lo deja guardar con ese nombre.

### Qué haces

El comando crea `.env` con la clave, el servidor de Qdrant y los dos modelos. Después abres el archivo y sustituyes `sk-coloca-aqui-la-clave-real` por la clave real.

La clave va en una sola línea, sin comillas y sin espacios alrededor del signo `=`.

No subas `.env` a un repositorio. El `.gitignore` del material ya ignora ese archivo.

Si en tu cuenta el modelo de redacción tiene otro nombre, cambia solo `OPENAI_CHAT_MODEL`. `OPENAI_EMBEDDING_MODEL` se queda en `text-embedding-3-small`, porque el taller espera listas de **1536** números.

### Resultado esperado

Existe el archivo `C:\TallerRAG\Capitulo01\.env`. Al abrirlo en Visual Studio Code se ven cinco líneas y la clave real en `OPENAI_API_KEY`.

### Código a ejecutar

```powershell
@"
OPENAI_API_KEY=sk-coloca-aqui-la-clave-real
QDRANT_HOST=localhost
QDRANT_PORT=6333
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4o
"@ | Set-Content -LiteralPath "C:\TallerRAG\Capitulo01\.env" -Encoding utf8
```

Para poner la clave real:

1. En Visual Studio Code, menú **Archivo** > **Abrir carpeta**.
2. Elige `C:\TallerRAG\Capitulo01`.
3. Abre `.env` y sustituye `sk-coloca-aqui-la-clave-real`.
4. Guarda con `Ctrl+S`.

## 7. Prueba antes de la sesión

1. En Visual Studio Code, la carpeta abierta debe ser `C:\TallerRAG\Capitulo01`.
2. Abre **Terminal** > **Nueva terminal** y confirma que es PowerShell.
3. La ruta debe terminar en `Capitulo01`. Si no, ejecuta:

```powershell
Set-Location C:\TallerRAG\Capitulo01
```

4. Ejecuta:

```powershell
python .\revisar_entorno.py
```

Resultado esperado:

```text
Clave encontrada. No se muestra completa por seguridad.
Búsqueda por significado lista. Cada embedding tiene 1536 números.
Modelo de embeddings: text-embedding-3-small
Modelo de respuestas listo. Dijo: LISTO
Modelo de chat: gpt-4o
Base de búsqueda lista en localhost:6333.
Todo listo. Puedes continuar.
```

El texto de "Dijo" puede traer un punto o variar un poco. Lo importante es que haya una respuesta corta, que el embedding tenga **1536** números y que Qdrant responda.

Si esta prueba falla, corrígela antes de que entren los participantes. Ellos ejecutan el mismo programa al empezar.

## 8. Durante la sesión

- Qdrant permanece encendido.
- Los participantes abren `C:\TallerRAG\Capitulo01` en Visual Studio Code.
- Los participantes no instalan software ni ejecutan `pip`.
- La colección que crea el taller se llama `financial_products_basic`. El siguiente taller la busca con ese nombre. No la borres al terminar este taller si vas a continuar.

El taller 2, en su versión actual, todavía está escrito para Linux y otra ruta de carpetas. La colección `financial_products_basic` sí queda lista en este equipo.

## 9. Limpieza, solo al cerrar todos los talleres

Cuando ya no se vaya a usar la colección:

```powershell
Set-Location C:\Qdrant
```

Cierra la ventana donde está corriendo `qdrant.exe`.

Si lo iniciaste con Docker:

```powershell
docker stop qdrant-financiero
docker rm qdrant-financiero
```

Borrar `C:\Qdrant\storage` o el volumen `qdrant-storage` elimina las búsquedas guardadas.
