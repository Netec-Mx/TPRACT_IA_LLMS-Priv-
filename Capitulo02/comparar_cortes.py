import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from herramientas import CARPETA_DOCUMENTOS, cortar_fijo, cortar_jerarquico, cortar_semantico


def mostrar(nombre: str, pedazos: list[str]) -> None:
    if not pedazos:
        print(f"{nombre}: no se crearon fragmentos.")
        return
    promedio = sum(len(pedazo) for pedazo in pedazos) / len(pedazos)
    print(f"{nombre}: {len(pedazos)} fragmentos. Tamaño promedio: {promedio:.0f} letras.")
    print(f"  Empieza así: {pedazos[0][:140].replace(chr(10), ' ')}")


def main():
    ejemplo = CARPETA_DOCUMENTOS / "credito_hipotecario_00.md"
    if not ejemplo.exists():
        print("Falta credito_hipotecario_00.md.")
        print("Ejecuta primero crear_documentos.py.")
        raise SystemExit(1)

    texto = ejemplo.read_text(encoding="utf-8")
    print("Documento de prueba: Crédito Hipotecario Residencial Plus")
    print()
    print("Corte fijo: pedazos de unas 500 letras, con 50 letras repetidas.")
    mostrar("Fijo", cortar_fijo(texto))
    print()
    print("Corte semántico: junta las frases cuando su significado se parece.")
    print("Este corte llama a OpenAI. Puede tardar unos segundos.")
    mostrar("Semántico", cortar_semantico(texto))
    print()
    print("Corte jerárquico: un fragmento por cada título del documento.")
    mostrar("Jerárquico", cortar_jerarquico(texto))
    print()
    print("El taller guarda la búsqueda con el corte jerárquico, porque cada sección de la ficha queda junta.")


if __name__ == "__main__":
    main()
