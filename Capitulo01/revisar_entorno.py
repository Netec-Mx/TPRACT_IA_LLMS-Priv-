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
