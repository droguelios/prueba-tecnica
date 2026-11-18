import csv 
import json 
import sqlite3 
from pathlib import Path

DB_PATH= Path("output/talento_andino.db")


def crear_tablas(conexion : sqlite3.Connection) -> None:
    cursor = conexion.cursor()
    cursor.executescript("""
DROP TABLE IF EXISTS empleados;
DROP TABLE IF EXISTS solicitudes;
""")

    cursor.executescript("""
CREATE TABLE empleados (
id_empleado TEXT PRIMARY KEY,
nombre TEXT NOT NULL,
correo TEXT NOT NULL ,
area TEXT NOT NULL , 
cargo TEXT NOT NULL , 
fecha_ingreso TEXT NOT NULL, 
dias_vacaciones_disponibles INTEGER NOT NULL ,
documento TEXT NOT NULL );

CREATE TABLE solicitudes(
id_solicitud TEXT PRIMARY KEY,
id_empleado TEXT NOT NULL ,
fecha_recepcion TEXT NOT NULL ,
canal TEXT NOT NULL ,
texto TEXT NOT NULL , 
etiqueta_esperada TEXT NOT NULL);
""")
    cursor.executescript("""

SELECT 
""")
    conexion.commit()

    def cargar_y_limpiar_empleados(ruta_csv : str) -> list[dict]:
        empleado_limpios = []

        ids_vistos= set()

        with open(ruta_csv , mode="r" , encoding="utf-8") as archivo:
            lector = csv.DictReader(archivo)

            for fila in lector: 
                id_emp = fila["id_empleado"]

            if id_emp in ids_vistos :
                print(f"Alerta : empleado duplicado omitido -> {id_emp}")

                fila["correo"] = fila["correo"].strip().lower()

            if not fila ["area"].strip():
                print(f"Alerta: Área vacia corregida para -> {id_emp} ")
                fila["area"] = "Sin asignar"

            fila["dias_vacaciones_disponibles"]= int (fila["dias_vacaciones_disponibles"])

            empleado_limpios.append(fila)
            ids_vistos.add(id_emp)
        return empleado_limpios

def cargar_solicitudes ( ruta_json: str) -> list[dict]:
        with open (ruta_json , mode= "r" ,encoding="utf-8") as archivo:
            return json.load(archivo) 

def insertar_datos(conexion: sqlite3.Connection, empleados: list[dict] , solicitudes: list[dict]) -> None:
        cursor= conexion.cursor()
        datos_empleados = [
            (
            e["id_empleado"], e["nombre"], e["correo"], e["area"],
            e["cargo"], e["fecha_ingreso"], e["dias_vacaciones_disponibles"], e["documento"]
        )
        for e in empleados 
    ]
        cursor.executemany("INSERT INTO empleados VALUES (?,?,?,?,?,?,?,?)", datos_empleados)

        solicitudes_empleados= [(
            i ["id_solicitud"] , i["id_empleado"] , i["fecha_recepcion"], i["canal"], i["texto"],
            i["etiqueta_esperada"]

        )
        for i in solicitudes
        
        ]
        cursor.executemany("INSERT INTO solicitudes VALUES(?,?,?,?,?,?)", solicitudes_empleados)


        conexion.commit()
