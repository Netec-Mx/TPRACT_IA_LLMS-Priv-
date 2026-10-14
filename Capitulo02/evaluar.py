import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import json
from datetime import datetime

from herramientas import CARPETA, COLECCION, alpha_guardado, consultar

PREGUNTAS = [
    {
        "pregunta": "¿Cuál es la tasa de interés anual del crédito hipotecario Residencial Plus?",
        "dato": "8.5%",
        "claves": ["8.5"],
    },
    {
        "pregunta": "¿Cuál es el enganche mínimo del crédito Mi Primera Casa?",
        "dato": "15%",
        "claves": ["15%", "15 por ciento"],
    },
    {
        "pregunta": "¿Cuánto es la anualidad de la tarjeta Platinum Rewards?",
        "dato": "$0 el primer año",
        "claves": ["$0 el primer año", "0 el primer año", "primer año"],
    },
    {
        "pregunta": "¿Cuál es el rendimiento del último año del Fondo Renta Fija MX?",
        "dato": "4.5%",
        "claves": ["4.5"],
    },
]


def normalizar(texto: str) -> str:
    return texto.lower().replace("$", "").replace(" ", "")


def contiene(respuesta: str, claves: list[str]) -> bool:
    texto = normalizar(respuesta)
    return any(normalizar(clave) in texto for clave in claves)


def puntajes_ragas(filas: list[dict]) -> dict | None:
    """Pide a RAGAS tres puntajes entre 0 y 1."""
    try:
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import answer_relevancy, context_precision, faithfulness

        dataset = Dataset.from_dict(
            {
                "question": [fila["pregunta"] for fila in filas],
                "answer": [fila["respuesta"] for fila in filas],
                "contexts": [fila["contextos"] for fila in filas],
                "ground_truth": [fila["dato"] for fila in filas],
            }
        )
        resultado = evaluate(
            dataset=dataset,
            metrics=[faithfulness, answer_relevancy, context_precision],
        )
        tabla = resultado.to_pandas() if hasattr(resultado, "to_pandas") else None
        nombres = {
            "faithfulness": ["faithfulness"],
            "answer_relevancy": ["answer_relevancy", "response_relevancy"],
            "context_precision": ["context_precision", "llm_context_precision_with_reference"],
        }
        puntajes = {}
        for claro, opciones in nombres.items():
            valor = None
            for opcion in opciones:
                try:
                    valor = float(resultado[opcion])
                    break
                except Exception:
                    if tabla is not None and opcion in getattr(tabla, "columns", []):
                        valor = float(tabla[opcion].mean())
                        break
            puntajes[claro] = valor
        if any(valor is None for valor in puntajes.values()):
            print("RAGAS respondió, pero faltó alguna métrica.")
            print(resultado)
            return None
        return puntajes
    except Exception as error:
        print("RAGAS no pudo calcular los puntajes.")
        print("La comparación de los datos de las fichas sí queda guardada.")
        print(f"Detalle: {error}")
        return None


def ejecutar(hibrido: bool, usar_reorden: bool, alpha: float) -> list[dict]:
    filas = []
    for numero, item in enumerate(PREGUNTAS, 1):
        print(f"  Pregunta {numero} de {len(PREGUNTAS)}")
        resultado = consultar(
            item["pregunta"],
            alpha=alpha,
            hibrido=hibrido,
            usar_reorden=usar_reorden,
            filtrar=hibrido,
        )
        filas.append(
            {
                "pregunta": item["pregunta"],
                "dato": item["dato"],
                "respuesta": resultado["respuesta"],
                "contextos": [fragmento["texto"] for fragmento in resultado["fragmentos"]],
                "acierto": contiene(resultado["respuesta"], item["claves"]),
            }
        )
        print("  Dato de la ficha presente:", "sí" if filas[-1]["acierto"] else "no")
    return filas


def texto_puntaje(puntajes: dict | None, nombre: str) -> str:
    if not puntajes or puntajes.get(nombre) is None:
        return "no disponible"
    return f"{puntajes[nombre]:.2f}"


def main():
    alpha = alpha_guardado()
    print("Esta comparación puede tardar varios minutos.")
    print("Primero responde las preguntas. Después calcula los puntajes RAGAS.")
    print()
    print("Forma del primer taller: solo significado, sin filtro y sin reordenar.")
    basico = ejecutar(hibrido=False, usar_reorden=False, alpha=alpha)
    print()
    print("Forma de este taller: filtro de la pregunta, significado, palabras y reordenamiento.")
    optimizado = ejecutar(hibrido=True, usar_reorden=True, alpha=alpha)

    aciertos_basico = sum(1 for fila in basico if fila["acierto"])
    aciertos_optimizado = sum(1 for fila in optimizado if fila["acierto"])
    print()
    print(f"Datos de la ficha con la forma simple: {aciertos_basico} de {len(PREGUNTAS)}")
    print(f"Datos de la ficha con la forma optimizada: {aciertos_optimizado} de {len(PREGUNTAS)}")
    print()
    print("RAGAS revisa tres cosas, con un puntaje de 0 a 1:")
    print("- Fidelidad: la respuesta sale de los fragmentos, sin datos inventados.")
    print("- Relevancia: la respuesta contesta la pregunta.")
    print("- Precisión del contexto: los fragmentos de arriba sirven para esa respuesta.")
    print("Calculando la forma simple...")
    ragas_basico = puntajes_ragas(basico)
    print("Calculando la forma optimizada...")
    ragas_optimizado = puntajes_ragas(optimizado)

    if ragas_basico:
        print(f"Simple. Fidelidad {ragas_basico['faithfulness']:.2f}. Relevancia {ragas_basico['answer_relevancy']:.2f}. Precisión {ragas_basico['context_precision']:.2f}.")
    if ragas_optimizado:
        print(f"Optimizada. Fidelidad {ragas_optimizado['faithfulness']:.2f}. Relevancia {ragas_optimizado['answer_relevancy']:.2f}. Precisión {ragas_optimizado['context_precision']:.2f}.")

    filas = ""
    for item, simple, mejor in zip(PREGUNTAS, basico, optimizado):
        filas += (
            f"| {item['pregunta']} | {item['dato']} | "
            f"{'sí' if simple['acierto'] else 'no'} | "
            f"{'sí' if mejor['acierto'] else 'no'} |\n"
        )

    resumen = f"""# Resumen del taller: búsqueda más precisa

Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M")}

## Qué se comparó

Las dos formas buscan en la colección `{COLECCION}`, que tiene más de 50 documentos.

- Forma simple, como el primer taller: solo significado. No lee el tipo de producto de la pregunta y no reordena.
- Forma de este taller: lee la pregunta para saber el tipo de producto, mezcla significado y palabras, y Cohere reordena los fragmentos.
- Alpha usado: {alpha}. Es el peso del significado. El resto del peso es para las palabras exactas.

## Datos de las fichas

| Pregunta | Dato de la ficha | Forma simple | Forma optimizada |
|---|---|---|---|
{filas}
Aciertos simples: {aciertos_basico} de {len(PREGUNTAS)}.

Aciertos optimizados: {aciertos_optimizado} de {len(PREGUNTAS)}.

## Puntajes RAGAS

Cada puntaje va de 0 a 1. Un número más alto es mejor.

| Qué mide | En palabras | Forma simple | Forma optimizada |
|---|---|---|---|
| Fidelidad (faithfulness) | La respuesta está sostenida por los fragmentos | {texto_puntaje(ragas_basico, "faithfulness")} | {texto_puntaje(ragas_optimizado, "faithfulness")} |
| Relevancia (answer relevancy) | La respuesta contesta lo que se preguntó | {texto_puntaje(ragas_basico, "answer_relevancy")} | {texto_puntaje(ragas_optimizado, "answer_relevancy")} |
| Precisión del contexto (context precision) | Los primeros fragmentos son los que sirven | {texto_puntaje(ragas_basico, "context_precision")} | {texto_puntaje(ragas_optimizado, "context_precision")} |

Los números cambian un poco cada vez. Lo importante es leer las dos columnas y ver qué forma trae el dato de la ficha.
"""
    (CARPETA / "RESUMEN.md").write_text(resumen, encoding="utf-8")
    (CARPETA / "resultados_evaluacion.json").write_text(
        json.dumps(
            {
                "alpha": alpha,
                "aciertos_simple": aciertos_basico,
                "aciertos_optimizado": aciertos_optimizado,
                "ragas_simple": ragas_basico,
                "ragas_optimizado": ragas_optimizado,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print("Resumen guardado: RESUMEN.md")
    print("Ábrelo en Visual Studio Code.")


if __name__ == "__main__":
    main()
