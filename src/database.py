import csv
import json
import sqlite3
from pathlib import Path

DB_PATH = Path("output/talento_andino.db")


def crear_tablas(conexion: sqlite3.Connection) -> None:
    cursor = conexion.cursor()
    cursor.executescript("""
        DROP TABLE IF EXISTS empleados;
        DROP TABLE IF EXISTS solicitudes;
    """)

    cursor.executescript("""
        CREATE TABLE empleados (
            id_empleado TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            correo TEXT NOT NULL,
            area TEXT NOT NULL,
            cargo TEXT NOT NULL,
            fecha_ingreso TEXT NOT NULL,
            dias_vacaciones_disponibles INTEGER NOT NULL,
            documento TEXT NOT NULL
        );

        CREATE TABLE solicitudes (
            id_solicitud TEXT PRIMARY KEY,
            id_empleado TEXT NOT NULL,
            fecha_recepcion TEXT NOT NULL,
            canal TEXT NOT NULL,
            texto TEXT NOT NULL,
            etiqueta_esperada TEXT NOT NULL
        );
    """)

    conexion.commit()

def ejecutar_consultas_sql(conexion) -> dict:
    cursor = conexion.cursor()

    consultas = {
        "solicitudes_por_categoria_y_area": """
            SELECT 
                s.etiqueta_esperada AS categoria,
                COALESCE(e.area, 'No registrado') AS area,
                COUNT(*) AS total
            FROM solicitudes s
            LEFT JOIN empleados e ON s.id_empleado = e.id_empleado
            GROUP BY s.etiqueta_esperada, COALESCE(e.area, 'No registrado')
            ORDER BY total DESC, categoria;
        """,
        "solicitudes_sin_empleado_en_nomina": """
            SELECT 
                s.id_solicitud,
                s.id_empleado,
                s.fecha_recepcion,
                s.canal,
                s.etiqueta_esperada
            FROM solicitudes s
            LEFT JOIN empleados e ON s.id_empleado = e.id_empleado
            WHERE e.id_empleado IS NULL;
        """,
        "empleados_menos_5_dias_vacaciones": """
            SELECT 
                id_empleado,
                nombre,
                area,
                dias_vacaciones_disponibles
            FROM empleados
            WHERE dias_vacaciones_disponibles < 5
            ORDER BY dias_vacaciones_disponibles ASC;
        """,
    }

    resultados = {}
    for nombre_consulta, sql in consultas.items():
        cursor.execute(sql)
        columnas = [col[0] for col in cursor.description]
        resultados[nombre_consulta] = [
            dict(zip(columnas, fila)) for fila in cursor.fetchall()
        ]

    return resultados


def cargar_y_limpiar_empleados(ruta_csv: str) -> list[dict]:
    empleado_limpios = []
    ids_vistos = set()

    with open(ruta_csv, mode="r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)

        for fila in lector:
            id_emp = fila["id_empleado"]

            if id_emp in ids_vistos:
                print(f"Alerta: empleado duplicado omitido -> {id_emp}")
                continue

            fila["correo"] = fila["correo"].strip().lower()

            if not fila["area"].strip():
                print(f"Alerta: Área vacía corregida para -> {id_emp}")
                fila["area"] = "Sin asignar"

            fila["dias_vacaciones_disponibles"] = int(
                fila["dias_vacaciones_disponibles"]
            )

            empleado_limpios.append(fila)
            ids_vistos.add(id_emp)

    return empleado_limpios


def cargar_solicitudes(ruta_json: str) -> list[dict]:
    with open(ruta_json, mode="r", encoding="utf-8") as archivo:
        return json.load(archivo)


def insertar_datos(conexion: sqlite3.Connection, empleados: list[dict], solicitudes: list[dict],) -> None:
    cursor = conexion.cursor()
    datos_empleados = [
        (
            e["id_empleado"],
            e["nombre"],
            e["correo"],
            e["area"],
            e["cargo"],
            e["fecha_ingreso"],
            e["dias_vacaciones_disponibles"],
            e["documento"],
        )
        for e in empleados
    ]
    cursor.executemany(
        "INSERT INTO empleados VALUES (?,?,?,?,?,?,?,?)", datos_empleados
    )

    solicitudes_empleados = [
        (
            i["id_solicitud"],
            i["id_empleado"],
            i["fecha_recepcion"],
            i["canal"],
            i["texto"],
            i["etiqueta_esperada"],
        )
        for i in solicitudes
    ]
    cursor.executemany(
        "INSERT INTO solicitudes VALUES (?,?,?,?,?,?)", solicitudes_empleados
    )

    conexion.commit()


def buscar_empleado(conexion: sqlite3.Connection, id_empleado: str) -> dict | None:
    conexion.row_factory = sqlite3.Row
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT * FROM empleados WHERE id_empleado = ?", (id_empleado,)
    )
    fila = cursor.fetchone()
    return dict(fila) if fila else None