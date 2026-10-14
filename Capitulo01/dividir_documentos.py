import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import json
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

CARPETA = Path(__file__).resolve().parent
CARPETA_FICHAS = CARPETA / "datos" / "productos"

# Cada ficha queda etiquetada con el tipo de producto y la categoría.
ETIQUETAS = {
    "tarjeta_visa_platinum.txt": {"tipo_producto": "tarjeta_credito", "categoria": "premium"},
    "credito_hipotecario.txt": {"tipo_producto": "credito", "categoria": "hipotecario"},
    "cuenta_ahorro_premium.txt": {"tipo_producto": "cuenta", "categoria": "ahorro"},
    "fondo_inversion_renta_fija.txt": {"tipo_producto": "inversion", "categoria": "renta_fija"},
    "seguro_vida_proteccion.txt": {"tipo_producto": "seguro", "categoria": "vida"},
}

if not CARPETA_FICHAS.exists():
    print("No encuentro la carpeta de fichas: datos\\productos.")
    print("Avisa al instructor.")
    raise SystemExit(1)

archivos = sorted(CARPETA_FICHAS.glob("*.txt"))
if len(archivos) == 0:
    print("No hay fichas en datos\\productos.")
    print("Avisa al instructor.")
    raise SystemExit(1)

documentos = []
for archivo in archivos:
    texto = archivo.read_text(encoding="utf-8-sig")
    documentos.append(Document(page_content=texto, metadata={"source": archivo.name}))
    print(f"Ficha leída: {archivo.name} ({len(texto)} caracteres)")

print(f"Fichas cargadas: {len(documentos)}")

# Corta cada ficha en fragmentos de unas 512 letras.
# Repite 50 letras entre un fragmento y el siguiente para no cortar una idea a la mitad.
cortador = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50,
    length_function=len,
    separators=["\n\n", "\n", ". ", " ", ""],
)
fragmentos = cortador.split_documents(documentos)

salida = []
for indice, fragmento in enumerate(fragmentos):
    nombre = Path(str(fragmento.metadata.get("source", ""))).name
    etiquetas = ETIQUETAS.get(nombre, {"tipo_producto": "otro", "categoria": "general"})
    datos = {
        "chunk_id": f"chunk_{indice:04d}",
        "tipo_producto": etiquetas["tipo_producto"],
        "categoria": etiquetas["categoria"],
        "doc_source": nombre,
    }
    salida.append({"content": fragmento.page_content, "metadata": datos})

destino = CARPETA / "fragmentos.json"
destino.write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"Fragmentos creados: {len(salida)}")
print("Fragmentos por ficha:")
conteo = {}
for item in salida:
    nombre = item["metadata"]["doc_source"]
    conteo[nombre] = conteo.get(nombre, 0) + 1
for nombre, cantidad in conteo.items():
    print(f"  {nombre}: {cantidad}")

print("Ejemplo del primer fragmento:")
print(salida[0]["content"][:220].replace("\n", " "))
print("Etiquetas:", salida[0]["metadata"])
print("Archivo guardado: fragmentos.json")
