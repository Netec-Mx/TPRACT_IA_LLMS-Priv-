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
