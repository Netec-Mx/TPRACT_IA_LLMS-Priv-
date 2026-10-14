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
