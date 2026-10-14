import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import json
import time
from pathlib import Path

from preguntar import preguntar_con_documentos, preguntar_sin_documentos

CARPETA = Path(__file__).resolve().parent

# Cada pregunta tiene un dato que sí está escrito en las fichas.
PREGUNTAS = [
    {
        "id": 1,
        "pregunta": "¿Cuál es la tasa de interés anual del crédito hipotecario para clientes con nómina?",
        "respuesta_esperada": "9.85%",
        "claves": ["9.85"],
    },
    {
        "id": 2,
        "pregunta": "¿Cuántos puntos de recompensa otorga la tarjeta Visa Platinum por cada dólar de compra?",
        "respuesta_esperada": "1.5 puntos",
        "claves": ["1.5"],
    },
    {
        "id": 3,
        "pregunta": "¿Cuál es el rendimiento anualizado del fondo BFN Estabilidad en los últimos 12 meses?",
        "respuesta_esperada": "11.2%",
        "claves": ["11.2"],
    },
    {
        "id": 4,
        "pregunta": "¿Cuál es el saldo mínimo para abrir la Cuenta de Ahorro Premium Plus?",
        "respuesta_esperada": "$10,000",
        "claves": ["10,000", "10000", "10.000"],
    },
    {
        "id": 5,
        "pregunta": "¿Qué porcentaje de la suma asegurada se paga por muerte accidental en el seguro de vida?",
        "respuesta_esperada": "200%",
        "claves": ["200%"],
    },
    {
        "id": 6,
        "pregunta": "¿Cuál es la penalización por prepago total del crédito hipotecario antes del tercer año?",
        "respuesta_esperada": "2% del saldo insoluto",
        "claves": ["2% del saldo", "2% sobre el saldo", "2 por ciento del saldo"],
    },
    {
        "id": 7,
        "pregunta": "¿Cuántos retiros mensuales sin comisión permite la cuenta de ahorro premium?",
        "respuesta_esperada": "6 retiros",
        "claves": ["6 retiros", "seis retiros"],
    },
    {
        "id": 8,
        "pregunta": "¿Cuál es la comisión total anual del fondo de inversión en renta fija?",
        "respuesta_esperada": "1.00%",
        "claves": ["1.00"],
    },
    {
        "id": 9,
        "pregunta": "¿Cuál es la prima mensual estimada del seguro de vida para un hombre de 40 años no fumador con suma asegurada de $3,000,000?",
        "respuesta_esperada": "$780/mes",
        "claves": ["780"],
    },
    {
        "id": 10,
        "pregunta": "¿Cuál es el ingreso mínimo mensual requerido para solicitar la tarjeta Visa Platinum?",
        "respuesta_esperada": "$15,000",
        "claves": ["15,000", "15000", "15.000"],
    },
]


def normalizar(texto: str) -> str:
    return texto.lower().replace("$", "").replace(",", "").replace(" ", "")


def contiene_dato(respuesta: str, claves: list[str]) -> bool:
    """Revisa si la respuesta incluye el dato que está en la ficha."""
    texto = normalizar(respuesta)
    return any(normalizar(clave) in texto for clave in claves)


def main():
    print("=" * 60)
    print("COMPARACIÓN: CON DOCUMENTOS Y SIN DOCUMENTOS")
    print("Este paso hace varias consultas. Puede tardar unos minutos.")
    print("=" * 60)

    correctas_con = 0
    correctas_sin = 0
    detalle = []

    for item in PREGUNTAS:
        print()
        print("-" * 60)
        print(f"Pregunta {item['id']} de {len(PREGUNTAS)}")
        print(item["pregunta"])
        print(f"Dato de la ficha: {item['respuesta_esperada']}")

        try:
            resultado = preguntar_con_documentos(item["pregunta"])
            respuesta_con = resultado["respuesta"]
            fuentes = [
                fuente["metadata"].get("doc_source")
                for fuente in resultado["fuentes"]
            ]
        except Exception as error:
            respuesta_con = f"No se pudo consultar: {error}"
            fuentes = []

        acierto_con = contiene_dato(respuesta_con, item["claves"])
        if acierto_con:
            correctas_con += 1
        print()
        print("Con documentos:")
        print(respuesta_con[:300])
        print("Dato de la ficha presente:", "sí" if acierto_con else "no")

        time.sleep(1)

        try:
            respuesta_sin = preguntar_sin_documentos(item["pregunta"])
        except Exception as error:
            respuesta_sin = f"No se pudo consultar: {error}"

        acierto_sin = contiene_dato(respuesta_sin, item["claves"])
        if acierto_sin:
            correctas_sin += 1
        print()
        print("Sin documentos:")
        print(respuesta_sin[:300])
        print("Dato de la ficha presente:", "sí" if acierto_sin else "no")

        detalle.append(
            {
                "id": item["id"],
                "pregunta": item["pregunta"],
                "respuesta_esperada": item["respuesta_esperada"],
                "respuesta_con_documentos": respuesta_con,
                "correcto_con_documentos": acierto_con,
                "respuesta_sin_documentos": respuesta_sin,
                "correcto_sin_documentos": acierto_sin,
                "fuentes": fuentes,
            }
        )
        time.sleep(1)

    total = len(PREGUNTAS)
    print()
    print("=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Con documentos: {correctas_con} de {total}")
    print(f"Sin documentos: {correctas_sin} de {total}")
    print(f"Diferencia: {correctas_con - correctas_sin} respuestas más con documentos")

    salida = {
        "resumen": {
            "total_preguntas": total,
            "correctas_con_documentos": correctas_con,
            "correctas_sin_documentos": correctas_sin,
        },
        "detalle": detalle,
    }
    destino = CARPETA / "resultados_evaluacion.json"
    destino.write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Archivo guardado: resultados_evaluacion.json")


if __name__ == "__main__":
    main()
