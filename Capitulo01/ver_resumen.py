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
