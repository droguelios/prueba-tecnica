import re
from datetime import datetime , timedelta

def enmascarar_datos(texto : str) -> str:
    texto = re.sub(
        r"[\w\.-]+@[\w\.-]+\.\w+" , "[EMAIL]" , texto 
    )

    texto= re.sub(
        r"\b3\d{9}\b" , "[TELEFONO]" , texto
    )

    texto= re.sub(
        r"\b\d{7,10}\b" , "[DOCUMENTO]" , texto
    )
    return texto

def evaluar_solicitud(empleado : dict | None , categoria: str , confianza: float, fecha_inicio : str | None, fecha_fin: str | None,  dias_habiles: int , umbral_confianza : float = 0.8 ):
    motivos = []

    saldo_suficiente = "si"
    
    if empleado is None  :
        motivos.append("empleado no existe en la nómina")
        saldo_suficiente = "no"

    if confianza < umbral_confianza:
        motivos.append(f"Confianza baja de la IA ({confianza:.2f})")

    if categoria == "VACACIONES":
        if not fecha_inicio or not fecha_fin :
            motivos.append("Vacaciones sin fechas definidas")
            saldo_suficiente = "no"

        elif empleado is not None and dias_habiles > empleado["dias_vacaciones_disponibles"]:
            motivos.append(f"{dias_habiles} {empleado['dias_vacaciones_disponibles']} Saldo insuficiente: pidió 8 días y tiene 0 disponibles" )
            saldo_suficiente = "no"
    return {
        "saldo_suficiente" : saldo_suficiente,
        "requiere_revision" : "si" if motivos else "no",
        "motivo" : "; ".join(motivos) if motivos else "sin novedades"
    }


def calcular_dias_habiles(fecha_inicio : str , fecha_fin: str ,festivos:  set[str] ) -> int:
    inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date()
    fin = datetime.strptime(fecha_fin,"%Y-%m-%d").date()

    if inicio > fin:
        return 0 

    actual = inicio
    dias_habiles = 0

    while actual <= fin:
        if actual.weekday() <5 and actual.isoformat() not in festivos:
            dias_habiles +=1
        actual += timedelta(days=1)
    return dias_habiles




