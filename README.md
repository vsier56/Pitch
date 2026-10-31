# ⚽ Pitch — Kiosco de Resultados en Tiempo Real

**Pitch** es un panel de visualización deportiva (*dashboard* en modo kiosco) desarrollado con **Python 3.12** y **Streamlit**, diseñado para ejecutarse a pantalla completa en un monitor dedicado, mini-PC o Raspberry Pi.

Muestra los partidos del día de tus equipos y competiciones favoritas con marcadores en directo, estado y minuto del partido, clima local, reloj digital y un *ticker* inferior continuo de noticias de última hora sin parpadeos.

---

## ✨ Características principales

- **Motor Híbrido de Competiciones**:
  - **Ligas y Torneos UEFA/FIFA**: Integración con la API v4 de [football-data.org](https://www.football-data.org/).
  - **Copas Nacionales y Supercopas**: Integración automática con la API pública de ESPN ([`copas.py`](copas.py)) para incluir *Copa del Rey*, *FA Cup*, *Carabao Cup*, *Supercopa de España* y *Supercopa de Europa* sin consumir cuota adicional.
- **Actualización en Tiempo Real (con caché inteligente)**:
  - Rotación de páginas en pantalla cada **10 segundos** (`MAX_PARTIDOS = 4` por pantalla).
  - Refresco de marcadores en vivo cada **60 segundos** con respaldo en `st.session_state` frente a microcortes de Wi-Fi.
  - Indicador visual pulsante (`EN JUEGO`) acompañado del minuto de partido.
- **Enriquecimiento de Estadios**:
  - Si la API no devuelve el estadio de un encuentro, lo busca de forma inteligente (ignorando tildes, mayúsculas o sufijos como `FC`/`CF`) en [`estadios.json`](estadios.json). Si no existe en ningún sitio, lo anota automáticamente en `estadios_faltantes.txt`.
- **Modo "Próximos Partidos"**:
  - Si un día no juega ninguno de tus equipos o ligas favoritas, la pantalla muestra automáticamente los próximos 4 encuentros programados de tu equipo principal ([`proximos.py`](proximos.py)).
- **Ticker Inferior "Indestructible"**:
  - Hilo de noticias RSS en el pie de página ([`ticker.py`](ticker.py)) inyectado en el DOM principal del navegador para que la animación CSS nunca se reinicie cuando Streamlit recarga los datos cada 10 segundos.
- **Clima en Vivo**:
  - Temperatura e icono meteorológico actualizados cada 15 minutos mediante [Open-Meteo](https://open-meteo.com/) (sin necesidad de API Key).

---

## 🛠️ Requisitos e Instalación (Python 3.12)

1. **Clonar el repositorio y crear el entorno virtual con Python 3.12**:
   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   *(En Linux / Raspberry Pi: `python3.12 -m venv .venv && source .venv/bin/activate`)*

2. **Instalar las dependencias**:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Configurar la clave de API (`.env`)**:
   Crea un archivo `.env` en la raíz del proyecto con tu token gratuito de [football-data.org](https://www.football-data.org/):
   ```env
   FOOTBALL_API_KEY=tu_token_aqui
   ```

---

## ⚙️ Configuración (`preferencias.json`)

Toda la personalización del panel se centraliza en [`preferencias.json`](preferencias.json):

```json
{
    "ligas": [
        "UEFA Champions League",
        "FIFA World Cup",
        "European Championship",
        "Supercopa de España",
        "Supercopa de Europa"
    ],
    "equipos": [
        "FC Barcelona",
        "Real Madrid",
        "Atlético",
        "Deportivo",
        "Athletic Club"
    ],
    "equipo_principal_id": 81,
    "equipo_principal_nombre": "FC Barcelona",
    "equipo_principal_estadio": "Spotify Camp Nou",
    "noticias_query": "FC Barcelona site:sport.es",
    "clima": {
        "lat": "41.6521",
        "lon": "-0.8809"
    }
}
```

- **`ligas` / `equipos`**: Filtra los partidos del día. El buscador de equipos ignora mayúsculas y tildes, por lo que basta con poner nombres parciales como `"Deportivo"` o `"Atlético"`.
- **`equipo_principal_*`**: Define el equipo que se consultará en la vista de *Próximos Partidos* cuando hoy no haya encuentros (`81` corresponde al FC Barcelona en `football-data.org`).
- **`noticias_query`**: Término de búsqueda en Google News RSS para el ticker inferior.
- **`clima`**: Latitud y longitud de tu ciudad para el indicador meteorológico de la esquina superior derecha.

---

## 🚀 Ejecución

Para iniciar el panel web en modo kiosco:

```powershell
.\.venv\Scripts\python.exe -m streamlit run pitch.py
```

También dispones del script auxiliar [`partidos_hoy.py`](partidos_hoy.py) para comprobar rápidamente por terminal qué partidos devuelve la API en el día actual:

```powershell
.\.venv\Scripts\python.exe partidos_hoy.py
```

---

## 📁 Estructura del Proyecto

| Archivo | Descripción |
| :--- | :--- |
| [`pitch.py`](pitch.py) | Aplicación principal de Streamlit, diseño CSS Kiosco, paginación y motor híbrido. |
| [`copas.py`](copas.py) | Conector con la API de ESPN para obtener partidos de copas nacionales y supercopas. |
| [`proximos.py`](proximos.py) | Vista de respaldo con los próximos 4 partidos cuando hoy no hay jornada. |
| [`ticker.py`](ticker.py) | Lector RSS de Google News y componente JS/CSS persistente en el pie de página. |
| [`partidos_hoy.py`](partidos_hoy.py) | Script CLI para depurar en consola los partidos del día. |
| [`preferencias.json`](preferencias.json) | Configuración de ligas, equipos favoritos, equipo principal, noticias y coordenadas. |
| [`estadios.json`](estadios.json) | Base de datos local de estadios por equipo. |
| `estadios_faltantes.txt` | Registro autogenerado cuando un equipo local no tiene estadio ni en la API ni en `estadios.json`. |
