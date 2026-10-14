import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from herramientas import alpha_guardado, consultar

PREGUNTA = "¿Cuáles son la tasa de interés y los requisitos del crédito hipotecario Residencial Plus?"


def main():
    alpha = alpha_guardado()
    print(f"Se usa alpha {alpha}: ese es el peso del significado.")
    print("El programa filtra el tipo de producto, mezcla significado y palabras, reordena y redacta.")
    print("Puede tardar un minuto.")
    print()
    resultado = consultar(PREGUNTA, alpha=alpha, hibrido=True, usar_reorden=True, filtrar=True)
    print(f"Pregunta: {resultado['pregunta']}")
    print(f"Tipo detectado: {resultado['tipo']}")
    print()
    print("Respuesta:")
    print(resultado["respuesta"])
    print()
    print("Fragmentos usados:")
    for numero, fragmento in enumerate(resultado["fragmentos"], 1):
        print(f"  {numero}. {fragmento.get('fuente', 'sin archivo')}")


if __name__ == "__main__":
    main()
