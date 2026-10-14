import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from preguntar import preguntar_con_documentos


def main():
    print("=" * 60)
    print("Preguntas sobre productos del Banco Financiero Nacional")
    print("=" * 60)
    print("Escribe una pregunta y presiona Enter.")
    print("Escribe salir para terminar.")
    print()
    print("Puedes probar con estas:")
    print("- ¿Qué requisitos necesito para un crédito hipotecario?")
    print("- ¿El fondo de inversión tiene comisión de salida?")
    print("- ¿Cuánto cuesta la anualidad de la tarjeta Visa Platinum?")
    print()

    while True:
        pregunta = input("Tu pregunta: ").strip()
        if pregunta.lower() in {"salir", "exit", "quit", "q"}:
            print("Listo. Puedes continuar con el resumen.")
            break
        if not pregunta:
            continue

        print("Buscando en las fichas...")
        try:
            resultado = preguntar_con_documentos(pregunta)
        except Exception as error:
            print("No se pudo completar la pregunta.")
            print("Avisa al instructor.")
            print(f"Detalle: {error}")
            continue

        print()
        print("Respuesta:")
        print(resultado["respuesta"])
        print()
        print(f"Fichas usadas: {len(resultado['fuentes'])}")
        for numero, fuente in enumerate(resultado["fuentes"], 1):
            metadatos = fuente["metadata"]
            print(f"  {numero}. {metadatos.get('doc_source', 'sin archivo')}")
            print(f"     Tipo: {metadatos.get('tipo_producto', 'sin tipo')}")
            print(f"     Fragmento: {fuente['contenido'][:120].replace(chr(10), ' ')}")
        print()


if __name__ == "__main__":
    main()
