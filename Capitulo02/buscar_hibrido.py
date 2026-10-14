import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import json

from herramientas import (
    CARPETA,
    alpha_guardado,
    buscar_palabras,
    buscar_significado,
    detectar_tipo,
    mezclar,
    reordenar,
)

PREGUNTA = "¿Cuáles son la tasa de interés y los requisitos del crédito hipotecario Residencial Plus?"

PRUEBAS = [
    {
        "pregunta": "¿Cuál es la tasa de interés anual del crédito hipotecario Residencial Plus?",
        "fuente": "credito_hipotecario_00.md",
    },
    {
        "pregunta": "¿Cuánto es la anualidad de la tarjeta Platinum Rewards?",
        "fuente": "tarjeta_00.md",
    },
    {
        "pregunta": "¿Cuál es el rendimiento del último año del Fondo Renta Fija MX?",
        "fuente": "fondo_inversion_00.md",
    },
]


def mostrar_lista(titulo: str, elementos: list[dict]) -> None:
    print(titulo)
    if not elementos:
        print("  Sin resultados.")
        return
    for numero, item in enumerate(elementos[:3], 1):
        extra = ""
        if "puntaje_rerank" in item:
            extra = f" | relevancia {item['puntaje_rerank']:.2f}"
        origen = ""
        if item.get("origen"):
            origen = " | viene de: " + ", ".join(item["origen"])
        print(f"  {numero}. {item.get('fuente', 'sin archivo')}{extra}{origen}")


def aciertos(alpha: float) -> int:
    total = 0
    for prueba in PRUEBAS:
        tipo = detectar_tipo(prueba["pregunta"])
        mezcla = mezclar(
            buscar_significado(prueba["pregunta"], tipo, 8),
            buscar_palabras(prueba["pregunta"], tipo, 8),
            alpha,
        )
        finales = reordenar(prueba["pregunta"], mezcla[:12], 3)
        fuentes = [item.get("fuente") for item in finales]
        if prueba["fuente"] in fuentes:
            total += 1
    return total


def main():
    tipo = detectar_tipo(PREGUNTA)
    print(f"Pregunta: {PREGUNTA}")
    print(f"La pregunta habla de: {tipo}.")
    print("La búsqueda se limita a ese tipo de producto.")
    print()

    significados = buscar_significado(PREGUNTA, tipo, 8)
    palabras = buscar_palabras(PREGUNTA, tipo, 8)
    mostrar_lista("Por significado:", significados)
    print()
    mostrar_lista("Por palabras exactas:", palabras)
    print()

    alpha = 0.5
    mezcla = mezclar(significados, palabras, alpha)
    print("Mezcla con alpha 0.5: el significado y las palabras pesan igual.")
    mostrar_lista("Mezcla:", mezcla)
    print()
    print("Cohere vuelve a ordenar los fragmentos según la pregunta.")
    finales = reordenar(PREGUNTA, mezcla[:12], 4)
    mostrar_lista("Después de reordenar:", finales)
    print()

    print("Ahora se prueba alpha 0.3, 0.5 y 0.7 con tres preguntas.")
    print("Alpha es la parte que pesa el significado. El resto pesa las palabras.")
    print("Esto puede tardar unos minutos.")
    resultados = {}
    for valor in (0.3, 0.5, 0.7):
        resultados[valor] = aciertos(valor)
        print(f"Alpha {valor}: la ficha correcta quedó entre los primeros en {resultados[valor]} de 3 preguntas.")

    mejor = max(resultados, key=resultados.get)
    ruta = CARPETA / "configuracion.json"
    ruta.write_text(json.dumps({"alpha": mejor}, indent=2), encoding="utf-8")
    print(f"Se usará alpha {mejor} en los siguientes pasos.")
    print("Archivo guardado: configuracion.json")
    print(f"Alpha guardado ahora: {alpha_guardado()}")


if __name__ == "__main__":
    main()
