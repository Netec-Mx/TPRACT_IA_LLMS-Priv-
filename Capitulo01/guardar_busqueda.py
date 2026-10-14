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
