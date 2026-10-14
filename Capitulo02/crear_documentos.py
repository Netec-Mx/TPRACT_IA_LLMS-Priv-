import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import json
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
DESTINO = CARPETA / "datos" / "documentos"

CREDITOS = [
    ("Residencial Plus", "8.5%", "20 años", "10%", "2 años", "$5,000,000"),
    ("Mi Primera Casa", "9.2%", "15 años", "15%", "1 año", "$1,000,000"),
    ("Vivienda Flexible", "10.1%", "25 años", "20%", "3 años", "$2,500,000"),
    ("Hipoteca Verde", "7.8%", "30 años", "10%", "2 años", "$3,000,000"),
    ("Casa Segura", "11.0%", "20 años", "15%", "2 años", "$5,000,000"),
    ("Hogar Premium", "8.5%", "15 años", "20%", "3 años", "$4,000,000"),
    ("Vivienda Joven", "9.2%", "10 años", "10%", "1 año", "$800,000"),
    ("Hipoteca Digital", "10.1%", "20 años", "15%", "2 años", "$1,500,000"),
    ("Casa Familiar", "7.8%", "25 años", "10%", "2 años", "$2,000,000"),
    ("Lote Propio", "11.0%", "15 años", "20%", "3 años", "$900,000"),
    ("Departamento Centro", "8.5%", "20 años", "15%", "2 años", "$3,500,000"),
    ("Vivienda Rural", "9.2%", "30 años", "10%", "1 año", "$700,000"),
]

TARJETAS = [
    ("Platinum Rewards", "$0 el primer año", "25%", "1 punto", "$50,000", "$15,000"),
    ("Gold Travel", "$1,200", "28%", "2 puntos", "$150,000", "$25,000"),
    ("Classic", "$800", "32%", "1 punto", "$20,000", "$8,000"),
    ("Black Infinite", "$4,800", "22%", "3 puntos", "$500,000", "$80,000"),
    ("Cashback Plus", "$0", "30%", "1 punto", "$40,000", "$12,000"),
    ("Digital First", "$450", "29%", "2 puntos", "$30,000", "$10,000"),
    ("Empresarial", "$2,500", "27%", "2 puntos", "$300,000", "$40,000"),
    ("Universitaria", "$0 el primer año", "34%", "1 punto", "$8,000", "$5,000"),
    ("Mujer", "$600", "26%", "2 puntos", "$60,000", "$18,000"),
    ("Viaje Nacional", "$900", "31%", "1 punto", "$35,000", "$14,000"),
    ("Nomina", "$0", "24%", "2 puntos", "$80,000", "$20,000"),
    ("Comercios", "$1,500", "33%", "1 punto", "$100,000", "$30,000"),
    ("Familia", "$700", "28%", "2 puntos", "$45,000", "$16,000"),
    ("Senior", "$500", "23%", "1 punto", "$70,000", "$22,000"),
]

FONDOS = [
    ("Renta Fija MX", "4.5%", "$1,000", "bajo", "diaria", "0.8%", "mediano plazo", "AAA"),
    ("Crecimiento Global", "6.8%", "$2,000", "moderado", "semanal", "1.1%", "largo plazo", "AA+"),
    ("Balanceado", "8.2%", "$3,000", "medio", "mensual", "1.4%", "mediano plazo", "AA"),
    ("Agresivo", "10.5%", "$5,000", "alto", "al vencimiento", "1.7%", "largo plazo", "A+"),
    ("Conservador", "4.5%", "$1,000", "bajo", "al vencimiento", "0.5%", "corto plazo", "AAA"),
    ("ESG Sustentable", "6.8%", "$2,500", "moderado", "semanal", "1.0%", "corto plazo", "AA"),
    ("Tecnologia", "12.0%", "$4,000", "muy alto", "mensual", "2.3%", "largo plazo", "A"),
    ("Deuda Soberana", "5.2%", "$1,500", "bajo", "diaria", "0.6%", "mediano plazo", "AAA"),
    ("Dividendos", "7.4%", "$3,500", "medio", "mensual", "1.3%", "largo plazo", "AA"),
    ("Dolares", "5.9%", "$2,000", "moderado", "semanal", "0.9%", "mediano plazo", "AA+"),
    ("Infrastructura", "8.8%", "$6,000", "alto", "al vencimiento", "1.6%", "largo plazo", "A+"),
    ("Liquidez Diaria", "4.1%", "$500", "bajo", "diaria", "0.4%", "corto plazo", "AAA"),
]

CUENTAS = [
    ("Ahorro Diario", "3.0%", "$500", "6 retiros"),
    ("Nomina Plus", "4.2%", "$1,000", "8 retiros"),
    ("Inversion Vista", "5.5%", "$5,000", "4 retiros"),
    ("Joven", "2.5%", "$100", "6 retiros"),
    ("Empresarial", "3.8%", "$10,000", "10 retiros"),
    ("Dolares", "2.0%", "$500", "4 retiros"),
    ("Meta Vacaciones", "4.8%", "$2,000", "2 retiros"),
    ("Retiro", "6.0%", "$3,000", "1 retiro"),
]

SEGUROS = [
    ("Proteccion Familiar", "$500,000", "18 a 65 años", "$420"),
    ("Vida Temporal", "$1,000,000", "18 a 60 años", "$780"),
    ("Educacion Hijos", "$750,000", "25 a 55 años", "$650"),
    ("Accidentes", "$300,000", "18 a 70 años", "$210"),
    ("Invalidez", "$2,000,000", "18 a 60 años", "$1,100"),
    ("Empresarial", "$5,000,000", "18 a 65 años", "$2,400"),
    ("Senior Vida", "$400,000", "50 a 75 años", "$980"),
    ("Digital", "$250,000", "18 a 45 años", "$180"),
]


def ficha_credito(nombre, tasa, plazo, enganche, antiguedad, monto) -> str:
    return f"""# Crédito Hipotecario {nombre}

Producto del Banco Financiero Nacional para compra de vivienda.

## Condiciones generales

El crédito {nombre} financia vivienda nueva o usada. El inmueble debe estar libre de gravámenes.

### Tasa de interés

- Tasa fija anual: {tasa}
- La tasa moratoria es la tasa ordinaria más 5 puntos.
- La tasa no cambia durante el plazo contratado.

### Plazo y monto

- Plazo máximo: {plazo}
- Monto máximo: {monto} MXN
- Enganche mínimo: {enganche} del valor del inmueble

## Requisitos

1. Edad entre 25 y 64 años.
2. Antigüedad laboral mínima de {antiguedad}.
3. Ingresos mínimos comprobables de $25,000 MXN mensuales.
4. Historial sin atrasos mayores a 30 días en los últimos 12 meses.
5. Avalúo realizado por un perito autorizado.

## Comisiones y pago anticipado

- Comisión por apertura: 1.5% del monto del crédito.
- Pago anticipado: sin penalización después del primer año.
- Seguro de vida incluido en la mensualidad.
- Gastos notariales a cargo de quien recibe el crédito.
"""


def ficha_tarjeta(nombre, anualidad, tasa, puntos, limite, ingresos) -> str:
    return f"""# Tarjeta de crédito {nombre}

## Características

La tarjeta {nombre} es una línea de crédito revolvente del Banco Financiero Nacional.

### Costos

- Anualidad: {anualidad}
- Tasa de interés ordinaria: {tasa} anual
- Comisión por disposición de efectivo: 6% del monto dispuesto
- Comisión por pago tardío: $500 MXN

### Límite y recompensas

- Límite de crédito: desde {limite} MXN
- Acumulación: {puntos} por cada $10 MXN de compra
- Vigencia de los puntos: 24 meses

## Requisitos

1. Ser mayor de 18 años.
2. Ingresos mínimos de {ingresos} MXN mensuales.
3. Identificación oficial vigente.
4. Comprobante de domicilio no mayor a 3 meses.

## Seguros incluidos

- Compras protegidas hasta $50,000 MXN por evento.
- Protección contra fraude con responsabilidad de $0 en compras no reconocidas.
"""


def ficha_fondo(nombre, rendimiento, minimo, riesgo, liquidez, comision, horizonte, calificacion) -> str:
    return f"""# Fondo de inversión {nombre}

## Objetivo

El fondo {nombre} busca un rendimiento acorde con su nivel de riesgo. Los rendimientos pasados no garantizan rendimientos futuros.

### Rendimiento y montos

- Rendimiento del último año: {rendimiento} neto
- Monto mínimo de apertura: {minimo} MXN
- Comisión por administración: {comision} anual sobre el saldo

### Riesgo y liquidez

- Nivel de riesgo: {riesgo}
- Horizonte recomendado: {horizonte}
- Liquidez: {liquidez}
- Calificación: {calificacion}

## Información para el cliente

La operadora entrega un prospecto antes de la contratación. El cliente puede consultar el portafolio en la banca en línea.
"""


def ficha_cuenta(nombre, rendimiento, minimo, retiros) -> str:
    return f"""# Cuenta {nombre}

## Condiciones

- Rendimiento anual: {rendimiento}
- Saldo mínimo de apertura: {minimo} MXN
- Disponibilidad: {retiros} sin comisión al mes
- Entidad: Banco Financiero Nacional

## Uso

La cuenta permite transferencias y consulta de saldo en la aplicación. El banco entrega estado de cuenta mensual.
"""


def ficha_seguro(nombre, suma, edad, prima) -> str:
    return f"""# Seguro {nombre}

## Cobertura

- Suma asegurada de referencia: {suma} MXN
- Edad de contratación: {edad}
- Prima mensual de referencia: {prima} MXN
- Entidad: BFN Seguros

## Contratación

Se requiere identificación oficial y designación de beneficiarios. El periodo de espera por enfermedad es de 30 días.
"""


def guardar(prefijo, indice, texto, metadatos) -> None:
    nombre = f"{prefijo}_{indice:02d}.md"
    (DESTINO / nombre).write_text(texto, encoding="utf-8")
    metadatos["doc_source"] = nombre
    (DESTINO / f"{prefijo}_{indice:02d}.json").write_text(
        json.dumps(metadatos, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main():
    DESTINO.mkdir(parents=True, exist_ok=True)
    for archivo in DESTINO.glob("*"):
        if archivo.suffix in {".md", ".json"}:
            archivo.unlink()

    for indice, datos in enumerate(CREDITOS):
        nombre, tasa, plazo, enganche, antiguedad, monto = datos
        guardar(
            "credito_hipotecario",
            indice,
            ficha_credito(*datos),
            {
                "tipo_producto": "credito",
                "categoria": "hipotecario",
                "nombre_producto": f"Crédito Hipotecario {nombre}",
                "fecha_vigencia": "2024-06-01",
                "entidad": "Banco Financiero Nacional",
            },
        )

    for indice, datos in enumerate(TARJETAS):
        nombre = datos[0]
        guardar(
            "tarjeta",
            indice,
            ficha_tarjeta(*datos),
            {
                "tipo_producto": "tarjeta",
                "categoria": "credito",
                "nombre_producto": f"Tarjeta {nombre}",
                "fecha_vigencia": "2024-07-01",
                "entidad": "Banco Financiero Nacional",
            },
        )

    for indice, datos in enumerate(FONDOS):
        nombre = datos[0]
        guardar(
            "fondo_inversion",
            indice,
            ficha_fondo(*datos),
            {
                "tipo_producto": "inversion",
                "categoria": "fondo",
                "nombre_producto": f"Fondo {nombre}",
                "fecha_vigencia": "2024-05-15",
                "entidad": "Operadora de Fondos XYZ",
            },
        )

    for indice, datos in enumerate(CUENTAS):
        nombre = datos[0]
        guardar(
            "cuenta",
            indice,
            ficha_cuenta(*datos),
            {
                "tipo_producto": "cuenta",
                "categoria": "ahorro",
                "nombre_producto": f"Cuenta {nombre}",
                "fecha_vigencia": "2024-03-01",
                "entidad": "Banco Financiero Nacional",
            },
        )

    for indice, datos in enumerate(SEGUROS):
        nombre = datos[0]
        guardar(
            "seguro",
            indice,
            ficha_seguro(*datos),
            {
                "tipo_producto": "seguro",
                "categoria": "vida",
                "nombre_producto": f"Seguro {nombre}",
                "fecha_vigencia": "2024-08-01",
                "entidad": "BFN Seguros",
            },
        )

    documentos = list(DESTINO.glob("*.md"))
    print(f"Documentos creados: {len(documentos)}")
    print("Deben ser 54: 12 créditos, 14 tarjetas, 12 fondos, 8 cuentas y 8 seguros.")
    print(f"Carpeta: {DESTINO}")
    if len(documentos) < 50:
        print("Faltan documentos. Avisa al instructor.")
        raise SystemExit(1)
    print("Listo. Hay más de 50 documentos.")


if __name__ == "__main__":
    main()
