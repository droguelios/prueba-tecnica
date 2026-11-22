import sqlite3
from src.business_rules import  calcular_dias_habiles,evaluar_solicitud , enmascarar_datos
from src.database import buscar_empleado, crear_tablas, insertar_datos 



def test_enmascarar_datos_oculta_pii():
    # Arrange
    texto = "Hola, mi cédula es 1020304050 y mi celular 3001234567."

    # Act
    resultado = enmascarar_datos(texto)

    # Assert
    assert "1020304050" not in resultado
    assert "3001234567" not in resultado

def test_calcular_dias_habiles_descuenta_finde_y_festivos():
    festivos = {"2026-06-22"}

    dias = calcular_dias_habiles("2026-06-19" , "2026-06-23" , festivos)

    assert dias == 2


def test_evaluar_solicitud_empleado_no_existe():
    empleado = None
    clasificacion = {"categoria" : "VACACIONES" , "confianza" : 0.95}
    dias_habiles = 3

    resultado = evaluar_solicitud(
        empleado=empleado,
        categoria="VACACIONES",
        confianza=0.95,
        fecha_inicio="2026-07-06",
        fecha_fin="2026-07-10",
        dias_habiles=4,    )

    assert resultado["requiere_revision"] == "si"

def test_evaluar_solicitud_saldo_insuficiente():
    empleado = {"id_empleado": "E001", "dias_vacaciones_disponibles": 2}
    clasificacion = {"categoria": "VACACIONES", "confianza": 0.95}
    dias_habiles = 5
    resultado = evaluar_solicitud(
        empleado=empleado,
        categoria="VACACIONES",
        confianza=0.95,
        fecha_inicio="2026-07-06",
        fecha_fin="2026-07-10",
        dias_habiles=4,
    )

    assert resultado["saldo_suficiente"] == "no"
    assert resultado["requiere_revision"] == "si"

def test_evaluar_solicitud_aprobacion_directa():
    empleado = {"id_empleado": "E001", "dias_vacaciones_disponibles": 10}
    clasificacion = {"categoria": "VACACIONES", "confianza": 0.95}
    dias_habiles = 4

    resultado = evaluar_solicitud(
        empleado=empleado,
        categoria="VACACIONES",
        confianza=0.95,
        fecha_inicio="2026-07-06",
        fecha_fin="2026-07-10",
        dias_habiles=4,
    )

    assert resultado["saldo_suficiente"] == "si"
    assert resultado["requiere_revision"] == "no"
    
# 4. Base de datos SQLite en memoria (no toca tu talento_andino.db)
def test_buscar_empleado_en_sqlite_memoria():
    conexion = sqlite3.connect(":memory:")
    crear_tablas(conexion)

    empleados = [
        {
            "id_empleado": "E999",
            "nombre": "Ana Prueba",
            "correo": "ana@empresa.com",
            "area": "TI",
            "cargo": "Dev",
            "fecha_ingreso": "2024-01-10",
            "dias_vacaciones_disponibles": 12,
            "documento": "10203040",
        }
    ]
    insertar_datos(conexion, empleados, [])

    encontrado = buscar_empleado(conexion, "E999")
    no_encontrado = buscar_empleado(conexion, "E000")
    conexion.close()

    assert encontrado is not None
    assert encontrado["nombre"] == "Ana Prueba"
    assert no_encontrado is None