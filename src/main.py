import csv
import json
from pathlib import Path
import sqlite3
import time

from src.ai_agent import clasificar_solicitud
from src.api_client import  api_festivos
from src.business_rules import enmascarar_datos , evaluar_solicitud , calcular_dias_habiles
from src.database import (
    DB_PATH,
    buscar_empleado,
    cargar_solicitudes,
    cargar_y_limpiar_empleados,
    crear_tablas,
    insertar_datos, ejecutar_consultas_sql
)
def procesar_solicitud(solicitud , conexion , festivos) -> dict: 
            
    id_solicitud = solicitud["id_solicitud"]
    id_empleado = solicitud["id_empleado" ]
    texto_original = solicitud ["texto" ]
        
    empleado = buscar_empleado(conexion , id_empleado )
        
    texto_enmascarado = enmascarar_datos(texto_original)
        
    clasificacion = clasificar_solicitud(texto_enmascarado)
    time.sleep(2)

    dias_habiles= 0 
    if clasificacion["categoria"] == "VACACIONES" and clasificacion["fecha_inicio"] and clasificacion["fecha_fin"]:
        dias_habiles = (calcular_dias_habiles(clasificacion["fecha_inicio"], clasificacion["fecha_fin"], festivos))
    evaluacion = evaluar_solicitud(
    empleado=empleado,
    categoria=clasificacion["categoria"],
    confianza=clasificacion["confianza"],
    fecha_inicio=clasificacion["fecha_inicio"],
    fecha_fin=clasificacion["fecha_fin"],
    dias_habiles=dias_habiles,
    )
    return { "id_solicitud": id_solicitud,
        "id_empleado": id_empleado,
        "nombre": empleado["nombre"] if empleado else "No encontrado",
        "area": empleado["area"] if empleado else "N/A",
        "canal": solicitud["canal"],
        "etiqueta_esperada": solicitud["etiqueta_esperada"],
        "categoria_ia": clasificacion["categoria"],
        "fecha_inicio": clasificacion["fecha_inicio"],
        "fecha_fin": clasificacion["fecha_fin"],
        "dias_habiles": dias_habiles,
        "confianza": clasificacion["confianza"],
        "saldo_suficiente": evaluacion["saldo_suficiente"],
        "requiere_revision": evaluacion["requiere_revision"],
        "motivo": evaluacion["motivo"],}

def ejecutar_pipeline () -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(DB_PATH)

    try:
        crear_tablas(conexion)
        empleados = cargar_y_limpiar_empleados("data/empleados.csv")
        solicitudes = cargar_solicitudes ("data/solicitudes.json")
        insertar_datos (conexion, empleados, solicitudes)

        consultas_sql = ejecutar_consultas_sql(conexion)
        with open(Path("output/consultas_sql.json"), "w", encoding="utf-8") as archivo_sql:
            json.dump(consultas_sql, archivo_sql, ensure_ascii=False, indent=2)

        festivos = api_festivos(2026)
        resultados = []

        for solicitud in solicitudes :
            resultado = procesar_solicitud(solicitud , conexion , festivos)
            resultados.append(resultado)
        with open(Path("output/resultados.json") , "w" , encoding="utf-8" ) as archivo:
                json.dump(resultados, archivo , ensure_ascii=False , indent=2)

        csv_path = Path("output/reporte_solicitudes.csv")

        if resultados:
            with open(csv_path, mode="w", encoding="utf-8-sig", newline="") as archivo_csv:
                writer = csv.DictWriter(archivo_csv, fieldnames=resultados[0].keys())
                writer.writeheader()
                writer.writerows(resultados)

        aciertos = 0
        errores = []

        for item in resultados:
            if item["categoria_ia"] == item["etiqueta_esperada"]:
                aciertos += 1
            else:
                errores.append({
                    "id_solicitud": item["id_solicitud"],
                    "esperada": item["etiqueta_esperada"],
                    "predicha": item["categoria_ia"],
                })

        total = len(resultados)
        exactitud = round((aciertos / total) * 100, 2) if total > 0 else 0.0

        metricas = {
            "total": total,
            "aciertos": aciertos,
            "exactitud_porcentaje": exactitud,
            "errores": errores,
        }

        with open(Path("output/metricas_ia.json"), "w", encoding="utf-8") as archivo_metricas:
            json.dump(metricas, archivo_metricas, ensure_ascii=False, indent=2)

        print(f"Exactitud IA: {aciertos}/{total} ({exactitud}%) | Errores: {len(errores)}")

        
                    
    finally:
        conexion.close()
if __name__ == "__main__":
     ejecutar_pipeline()

      
    