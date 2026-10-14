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
