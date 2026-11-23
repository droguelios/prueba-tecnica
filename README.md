# Automatización de Solicitudes de RRHH con IA — Talento Andino S.A.S.

Solución de automatización de extremo a extremo para el procesamiento de solicitudes de Recursos Humanos (vacaciones, certificados laborales, incapacidades y actualización de datos). El pipeline limpia y almacena los datos en SQLite, calcula días hábiles consultando festivos oficiales de Colombia vía API REST, enmascara datos personales (PII), clasifica las solicitudes con **Google Gemini** en formato JSON estructurado y aplica reglas de negocio para enviar únicamente los casos dudosos o inválidos a **revisión humana**.

---

## Arquitectura y estructura del proyecto

```text
reto-automatizador-ia/
├── data/
│   ├── empleados.csv              # Nómina ficticia de empleados
│   ├── solicitudes.json           # Solicitudes recibidas (correo, chat, formulario)
│   └── festivos_co_2026.json      # Respaldo local de festivos de Colombia 2026
├── docs/
│   ├── ficha_inventario.md        # Ficha de inventario de la automatización
│   └── evidencia_power_automate/  # Capturas/evidencia del flujo de Power Automate
├── output/
│   ├── talento_andino.db          # Base de datos SQLite generada
│   ├── consultas_sql.json         # Resultados de las 3 consultas SQL obligatorias
│   ├── reporte_solicitudes.csv    # Reporte final para RRHH (UTF-8 con BOM para Excel)
│   ├── resultados.json            # Respaldo estructurado del reporte final
│   └── metricas_ia.json           # Exactitud de la clasificación IA y detalle de errores
├── src/
│   ├── database.py                # Esquema SQLite, limpieza de datos y consultas SQL
│   ├── api_client.py              # Cliente Nager.Date con timeout, reintentos y fallback local
│   ├── business_rules.py          # Enmascaramiento PII, cálculo de días hábiles y reglas RRHH
│   ├── ai_agent.py                # Clasificación y extracción de fechas con Gemini API
│   └── main.py                    # Orquestador del pipeline y generación de reportes
├── test/
│   └── test_pipeline.py           # 6 pruebas unitarias con pytest
├── .env.example                   # Plantilla de variables de entorno (sin claves reales)
├── .gitignore                     # Excluye .env, entorno virtual y archivos temporales
└── requirements.txt               # Dependencias de Python
```

---

## Requisitos e instalación

* **Python 3.10+**
* Cuenta gratuita en **Google AI Studio** para obtener una API Key de Gemini.
* **Power Automate para escritorio** (incluido en Windows 11 / descargable en Windows 10) para la orquestación local.

### 1. Clonar el repositorio y crear el entorno virtual

```bash
git clone https://github.com/droguelios/prueba-tecnica.git
cd prueba-tecnica
python -m venv .venv
```

Activar el entorno virtual en Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

Copia `.env.example` como `.env` en la raíz del proyecto y agrega tu clave de Gemini:

```env
GEMINI_API_KEY=tu_clave_de_google_ai_studio
```

> **Seguridad:** El archivo `.env` está incluido en `.gitignore`. Ninguna clave real se encuentra en el código fuente ni en el historial de Git.

---

## Ejecución

### Ejecutar el pipeline completo

```bash
python -m src.main
```

Esto genera automáticamente en `output/`:
* `talento_andino.db` (tablas `empleados` y `solicitudes`)
* `consultas_sql.json` (resultados de las 3 consultas SQL de la Misión 1)
* `reporte_solicitudes.csv` y `resultados.json` (reporte para RRHH)
* `metricas_ia.json` (exactitud de la IA frente a `etiqueta_esperada`)

### Ejecutar pruebas unitarias

```bash
pytest -v
```

Incluye **6 pruebas unitarias** que validan:
1. Cálculo de días hábiles descontando fines de semana y festivos de Colombia (`S01 = 5`, `S05 = 4`, `S06 = 8`).
2. Enmascaramiento de datos personales (cédulas, celulares y correos electrónicos).
3. Reglas de revisión humana (baja confianza, vacaciones sin fechas, saldo insuficiente y empleado inexistente).

---

## Limpieza de datos y SQL (Misión 1)

Al cargar `data/empleados.csv` en SQLite (`id_empleado` como `PRIMARY KEY` y `id_solicitud` como `PRIMARY KEY` en `solicitudes`), se detectaron y corrigieron las siguientes anomalías:

| Hallazgo | Registro afectado | Acción aplicada |
| :--- | :--- | :--- |
| **Empleado duplicado** | `E003` (María Torres) | Se omitió el registro duplicado al insertar, conservando los **8 empleados únicos** y emitiendo una alerta en consola. |
| **Correo con mayúsculas y espacios** | `E002` (`ANDRES.PEREZ@ejemplo.com `) | Se aplicó `.strip().lower()` para normalizarlo a `andres.perez@ejemplo.com`. |
| **Área vacía** | `E004` (Julián Rojas) | Se asignó el valor explícito `"Sin asignar"` para evitar nulos en agrupaciones y reportes, emitiendo una alerta en consola. |

Las **3 consultas SQL** obligatorias se ejecutan automáticamente desde `src/database.py` y se guardan en `output/consultas_sql.json`:
1. **Solicitudes por categoría y área:** usa `LEFT JOIN` y `COALESCE(e.area, 'No registrado')` para no perder solicitudes de empleados fuera de nómina.
2. **Solicitudes sin empleado en nómina:** identifica `S10` (`E009`) mediante `LEFT JOIN ... WHERE e.id_empleado IS NULL`.
3. **Empleados con menos de 5 días de vacaciones:** filtra con `< 5` estricto (`E006` con 3 días y `E008` con 0 días; excluye a `E004` que tiene 5).

---

## Decisiones técnicas

* **Privacidad primero (Enmascaramiento PII):** Antes de enviar cualquier texto a la API de Gemini, `business_rules.py` reemplaza números de documento, teléfonos celulares y correos electrónicos por etiquetas genéricas (`[DOCUMENTO]`, `[CELULAR]`, `[CORREO]`) mediante expresiones regulares.
* **Resiliencia en la API de festivos (Nager.Date):** El cliente implementa *timeout*, reintentos y respaldo automático desde `data/festivos_co_2026.json` para que una caída externa no detenga el cálculo de días hábiles.
* **La IA nunca decide sola:** La respuesta del modelo se exige en JSON estructurado y se valida antes de usarse. Cualquier error de API (`429` o `503`), confianza baja, solicitud de vacaciones sin fechas, saldo insuficiente o empleado inexistente marca `requiere_revision = si` con su motivo explícito.
* **Compatibilidad con Excel en Windows:** El reporte `output/reporte_solicitudes.csv` se exporta con codificación `utf-8-sig` (BOM) para preservar tildes y la letra `ñ` al abrirlo directamente en Excel.
* **Orquestación (Power Automate para escritorio - Opción A):** Se utiliza un flujo local que ejecuta el script dentro del entorno virtual, verifica la existencia del reporte final, registra fecha, hora y estado en un archivo de log, y muestra una alerta visual si ocurre un fallo.

---

## Limitaciones conocidas y paso a producción con TI

### Limitaciones actuales
* **Límites del nivel gratuito de Gemini:** La cuota diaria (20 peticiones/día por modelo en Free Tier) y los picos temporales de demanda (`503 UNAVAILABLE` / `429 RESOURCE_EXHAUSTED`) pueden degradar la exactitud si el modelo responde con error y el sistema activa el *fallback* a revisión humana.
* **Ejecución local y base SQLite:** SQLite y Power Automate Desktop están pensados para un entorno local monopuesto y no soportan alta concurrencia ni ejecución desatendida 24/7 sin servidor dedicado.
* **Reglas de fechas relativas:** Frases ambiguas como *"ayer y hoy"* sin contexto de fecha explícita pueden requerir inyectar `fecha_recepcion` en el prompt para mejorar la extracción en incapacidades.

### Cómo llevarlo a producción con TI
1. **Infraestructura y seguridad:** Migrar la ejecución a un contenedor o función serverless (Azure Functions / Cloud Run), mover los secretos a un gestor como **Azure Key Vault** y usar un endpoint empresarial de IA con SLA y acuerdo de privacidad de datos (Cero retención).
2. **Base de datos y conectores:** Reemplazar SQLite por **PostgreSQL / Azure SQL** integrado con el ERP/nómina real de RRHH, y migrar el flujo a **Power Automate en la nube** disparado por eventos reales (Outlook, Forms, Teams).
3. **Observabilidad:** Enviar logs estructurados y métricas de exactitud/deriva del modelo a Application Insights o un tablero en Power BI con alertas automáticas ante tasas altas de revisión humana.

---

## Uso de asistentes de IA

Durante el desarrollo de este reto se utilizó un asistente de IA como apoyo para revisión de arquitectura, depuración de errores de API, redacción de pruebas unitarias y estructuración de la documentación. Todo el código fue integrado, probado y comprendido por el autor para su sustentación técnica.