import requests
import json
from datetime import datetime , timedelta

def api_festivos(anio: int= 2026) -> set[str]:
    URL = 'https://date.nager.at/api/v3/PublicHolidays/2026/CO'


    for intentos in range (3):
        try:
            response = requests.get(URL, timeout=5)
            response.raise_for_status()
            datos = response.json()

            with open("data/festivos_co_2026.json" , mode="w" , encoding="utf-8") as archivo:
                json.dump(datos, archivo , indent=2)

                return {item["date"] for item in datos}
            
        except requests.RequestException as e:
            print(f"Intentos {intentos + 1} fallido: {e}")
            
    with open ("data/festivos_co_2026.json" , mode="r" , encoding="utf-8") as archivo :
        datos_respaldo= json.load(archivo)
        return {item["date"] for item in datos_respaldo}

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

if __name__ == "__main__":
    festivos = api_festivos()
    print("S01 (esperado 5):", calcular_dias_habiles("2026-12-14", "2026-12-18", festivos))
    print("S05 (esperado 4):", calcular_dias_habiles("2026-12-07", "2026-12-11", festivos))
    print("S06 (esperado 8):", calcular_dias_habiles("2026-12-21", "2026-12-31", festivos))