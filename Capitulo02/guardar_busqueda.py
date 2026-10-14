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
