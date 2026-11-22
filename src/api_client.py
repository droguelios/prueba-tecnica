import requests
import json


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

