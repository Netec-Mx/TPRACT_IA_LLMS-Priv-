import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import json
import os
from pathlib import Path

from dotenv import load_dotenv

CARPETA = Path(__file__).resolve().parent
CARPETA_DOCUMENTOS = CARPETA / "datos" / "documentos"
COLECCION = "financial_products_optimized"
COLECCION_BASICA = "financial_products_basic"
INDICE = "financial_products_bm25"

load_dotenv(CARPETA / ".env")


def texto_respuesta(mensaje) -> str:
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


def modelo_embedding() -> str:
    return os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")


def modelo_chat() -> str:
    return os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")


def modelo_rerank() -> str:
    return os.getenv("COHERE_RERANK_MODEL", "rerank-multilingual-v3.0")


def alpha_guardado() -> float:
    ruta = CARPETA / "configuracion.json"
    if not ruta.exists():
        return 0.5
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return float(datos.get("alpha", 0.5))


def similitud(vector_a: list[float], vector_b: list[float]) -> float:
    producto = sum(a * b for a, b in zip(vector_a, vector_b))
    norma_a = sum(a * a for a in vector_a) ** 0.5
    norma_b = sum(b * b for b in vector_b) ** 0.5
    if norma_a == 0 or norma_b == 0:
        return 0.0
    return producto / (norma_a * norma_b)


def vectores_de(textos: list[str]) -> list[list[float]]:
    from openai import OpenAI

    cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=60)
    respuesta = cliente.embeddings.create(input=textos, model=modelo_embedding())
    return [item.embedding for item in respuesta.data]


def vector_de(texto: str) -> list[float]:
    return vectores_de([texto])[0]


def cortar_fijo(texto: str) -> list[str]:
    """Corta el texto en pedazos de unas 500 letras, con 50 letras repetidas."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    cortador = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return [pedazo.strip() for pedazo in cortador.split_text(texto) if pedazo.strip()]


def cortar_semantico(texto: str, umbral: float = 0.75) -> list[str]:
    """Junta las frases seguidas cuando su significado se parece."""
    oraciones = []
    for parte in texto.replace("\n", " ").split(". "):
        limpio = parte.strip(" #")
        if len(limpio) > 25:
            oraciones.append(limpio)
    if len(oraciones) <= 1:
        return [texto.strip()] if texto.strip() else []

    vectores = vectores_de(oraciones)
    grupos = [[oraciones[0]]]
    for indice in range(1, len(oraciones)):
        parecido = similitud(vectores[indice], vectores[indice - 1])
        if parecido < umbral:
            grupos.append([oraciones[indice]])
        else:
            grupos[-1].append(oraciones[indice])
    return [". ".join(grupo) + "." for grupo in grupos]


def cortar_jerarquico(texto: str, maximo: int = 800) -> list[str]:
    """Separa el documento por sus títulos. Si una sección es muy larga, la vuelve a cortar."""
    from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

    por_titulos = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("#", "titulo"), ("##", "seccion"), ("###", "subseccion")],
        strip_headers=False,
    )
    secciones = por_titulos.split_text(texto)
    respaldo = RecursiveCharacterTextSplitter(chunk_size=maximo, chunk_overlap=50)
    pedazos = []
    for seccion in secciones:
        contenido = seccion.page_content.strip()
        if len(contenido) < 20:
            continue
        if len(contenido) > maximo:
            pedazos.extend(pedazo.strip() for pedazo in respaldo.split_text(contenido) if pedazo.strip())
        else:
            pedazos.append(contenido)
    return pedazos


def detectar_tipo(pregunta: str) -> str | None:
    """Lee la pregunta y reconoce de qué tipo de producto habla."""
    texto = pregunta.lower()
    reglas = [
        ("credito", ["hipotec", "crédito", "credito", "vivienda", "enganche", "casa"]),
        ("tarjeta", ["tarjeta", "anualidad", "puntos", "rewards", "travel"]),
        ("inversion", ["fondo", "invers", "rendimiento"]),
        ("cuenta", ["cuenta de ahorro", "cuenta"]),
        ("seguro", ["seguro", "póliza", "poliza"]),
    ]
    for tipo, palabras in reglas:
        if any(palabra in texto for palabra in palabras):
            return tipo
    return None


def cliente_qdrant():
    from qdrant_client import QdrantClient

    return QdrantClient(
        host=os.getenv("QDRANT_HOST", "localhost"),
        port=int(os.getenv("QDRANT_PORT", "6333")),
        timeout=30,
    )


def cliente_elastic():
    from elasticsearch import Elasticsearch

    host = os.getenv("ELASTICSEARCH_HOST", "localhost")
    puerto = os.getenv("ELASTICSEARCH_PORT", "9200")
    return Elasticsearch(f"http://{host}:{puerto}", request_timeout=30)


def buscar_significado(pregunta: str, tipo: str | None, cantidad: int, coleccion: str = COLECCION) -> list[dict]:
    from qdrant_client.models import FieldCondition, Filter, MatchValue

    cliente = cliente_qdrant()
    filtro = None
    if tipo:
        filtro = Filter(must=[FieldCondition(key="tipo_producto", match=MatchValue(value=tipo))])
    respuesta = cliente.query_points(
        collection_name=coleccion,
        query=vector_de(pregunta),
        query_filter=filtro,
        limit=cantidad,
    )
    encontrados = []
    for punto in respuesta.points:
        datos = punto.payload or {}
        encontrados.append(
            {
                "texto": datos.get("content") or datos.get("page_content") or "",
                "fuente": datos.get("doc_source") or datos.get("metadata", {}).get("doc_source", "sin archivo"),
                "tipo": datos.get("tipo_producto") or datos.get("metadata", {}).get("tipo_producto", ""),
            }
        )
    return [item for item in encontrados if item["texto"]]


def buscar_palabras(pregunta: str, tipo: str | None, cantidad: int) -> list[dict]:
    consulta = {
        "bool": {
            "must": [
                {
                    "match": {
                        "content": {
                            "query": pregunta,
                            "analyzer": "spanish",
                        }
                    }
                }
            ]
        }
    }
    if tipo:
        consulta["bool"]["filter"] = [{"term": {"tipo_producto": tipo}}]
    respuesta = cliente_elastic().search(index=INDICE, query=consulta, size=cantidad)
    encontrados = []
    for hit in respuesta["hits"]["hits"]:
        origen = hit["_source"]
        encontrados.append(
            {
                "texto": origen.get("content", ""),
                "fuente": origen.get("doc_source", "sin archivo"),
                "tipo": origen.get("tipo_producto", ""),
            }
        )
    return encontrados


def mezclar(significados: list[dict], palabras: list[dict], alpha: float) -> list[dict]:
    """Combina las dos listas. Alpha es el peso del significado. El resto es el peso de las palabras."""
    acumulado = {}
    for posicion, item in enumerate(significados):
        clave = item["texto"]
        ficha = acumulado.setdefault(clave, {**item, "puntaje": 0.0, "origen": []})
        ficha["puntaje"] += alpha / (posicion + 1)
        if "significado" not in ficha["origen"]:
            ficha["origen"].append("significado")
    for posicion, item in enumerate(palabras):
        clave = item["texto"]
        ficha = acumulado.setdefault(clave, {**item, "puntaje": 0.0, "origen": []})
        ficha["puntaje"] += (1 - alpha) / (posicion + 1)
        if "palabras" not in ficha["origen"]:
            ficha["origen"].append("palabras")
    return sorted(acumulado.values(), key=lambda item: item["puntaje"], reverse=True)


def reordenar(pregunta: str, documentos: list[dict], top_n: int) -> list[dict]:
    """Cohere lee la pregunta y los fragmentos, y deja arriba los más útiles."""
    import cohere

    if not documentos:
        return []
    cliente = cohere.Client(api_key=os.getenv("COHERE_API_KEY"))
    respuesta = cliente.rerank(
        model=modelo_rerank(),
        query=pregunta,
        documents=[item["texto"] for item in documentos],
        top_n=min(top_n, len(documentos)),
    )
    ordenados = []
    for resultado in respuesta.results:
        item = dict(documentos[resultado.index])
        item["puntaje_rerank"] = resultado.relevance_score
        ordenados.append(item)
    return ordenados


def redactar(pregunta: str, fragmentos: list[dict]) -> str:
    from langchain_openai import ChatOpenAI

    contexto = "\n\n".join(item["texto"] for item in fragmentos)
    instrucciones = f"""Eres un asesor del Banco Financiero Nacional.
Responde la pregunta usando solamente el contexto.
Si el dato no está en el contexto, di: "No tengo esa información en los documentos disponibles."
Cuando el contexto traiga tasas, montos o plazos, inclúyelos.
Responde en español, de forma breve.

CONTEXTO:
{contexto}

PREGUNTA:
{pregunta}
"""
    modelo = ChatOpenAI(model=modelo_chat(), temperature=0)
    return texto_respuesta(modelo.invoke(instrucciones))


def consultar(pregunta: str, alpha: float = 0.5, hibrido: bool = True, usar_reorden: bool = True, filtrar: bool = True) -> dict:
    tipo = detectar_tipo(pregunta) if filtrar else None
    significados = buscar_significado(pregunta, tipo, 8)
    palabras = buscar_palabras(pregunta, tipo, 8) if hibrido else []
    mezcla = mezclar(significados, palabras, alpha) if hibrido else significados
    if usar_reorden and mezcla:
        finales = reordenar(pregunta, mezcla[:12], 4)
    else:
        finales = mezcla[:4]
    return {
        "pregunta": pregunta,
        "tipo": tipo,
        "alpha": alpha,
        "respuesta": redactar(pregunta, finales),
        "fragmentos": finales,
        "significados": significados[:3],
        "palabras": palabras[:3],
    }
