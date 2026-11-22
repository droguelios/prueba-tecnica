import os   
from dotenv import load_dotenv
from typing import Literal
from pydantic import BaseModel , Field
from google import genai
from google.genai import types

load_dotenv()
API_KEY= os.getenv("GEMINI_API_KEY")
class ClasificarSolicitud(BaseModel):
    categoria: Literal["VACACIONES", "CERTIFICADO_LABORAL", "INCAPACIDAD", "ACTUALIZACION_DATOS", "OTRO"]

    fecha_inicio: str | None = None

    fecha_fin: str | None = None

    confianza: float = Field(ge=0.0, le=1.0)

def clasificar_solicitud(texto_enmascarado : str )-> dict:

    client = genai.Client(api_key=API_KEY)
    if not API_KEY : raise ValueError("Falta GEMINI_API_KEY en el archivo .env")

    prompt = f"""
    Eres un asistente especializado en clasificar solicitudes de Recursos Humanos.
    Analiza el siguiente mensaje de un empleado y extrae la información solicitada siguiendo estas reglas estrictas:

    1. Categoría: Clasifica el mensaje exactamente en una de estas opciones:
       - VACACIONES
       - CERTIFICADO_LABORAL
       - INCAPACIDAD
       - ACTUALIZACION_DATOS
       - OTRO (si no encaja claramente en ninguna de las anteriores)

    2. Fechas (fecha_inicio y fecha_fin):
       - Extrae las fechas en formato YYYY-MM-DD solo si el mensaje menciona fechas exactas (especialmente en VACACIONES o INCAPACIDAD).
       - Si el mensaje menciona día y mes pero no el año, asume el año 2026.
       - Si no hay fechas exactas, si son vagas (ej. "el próximo mes", "más adelante") o no aplican a la categoría, devuelve null en ambos campos. Nunca inventes fechas.

    3. Confianza (confianza):
       - Asigna un número entre 0.0 y 1.0 según qué tan clara sea la intención del mensaje.
       - Usa valores menores a 0.8 si el mensaje es ambiguo, confuso o incompleto.

    Mensaje del empleado:
    "{texto_enmascarado}"
    """
    try:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=ClasificarSolicitud, temperature=0.0)
        )
        resultado = ClasificarSolicitud.model_validate_json(response.text)
        return  resultado.model_dump( )
    except Exception as e:
        print(f"Error al clasificar con Gemini: {e}")
        return{
            "categoria": "OTRO", "fecha_inicio": None, "fecha_fin": None, "confianza": 0.0
        }
