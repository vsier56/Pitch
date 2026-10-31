# ⚽ Pitch — Real-Time Live Score Kiosk

**Pitch** is a sports display dashboard (kiosk-mode dashboard) built with **Python 3.12** and **Streamlit**, designed to run full-screen on a dedicated monitor, mini-PC, or Raspberry Pi.

It displays the day's matches for your favorite teams and competitions with live scores, match status and minute, local weather, a digital clock, and a seamless, flicker-free breaking news ticker at the bottom.

---

## ✨ Key Features

- **Hybrid Competition Engine**:
  - **UEFA/FIFA Leagues and Tournaments**: Integrated with the [football-data.org](https://www.football-data.org/) v4 API.
  - **Domestic Cups and Super Cups**: Automatic integration with the public ESPN API ([`copas.py`](copas.py)) to include *Copa del Rey*, *FA Cup*, *Carabao Cup*, *Spanish Super Cup*, and *UEFA Super Cup* without consuming additional API quota.
- **Real-Time Updates (with Smart Caching)**:
  - On-screen page rotation every **10 seconds** (`MAX_PARTIDOS = 4` per screen).
  - Live score refresh every **60 seconds** backed by `st.session_state` to protect against brief Wi-Fi drops.
  - Pulsing visual indicator (`EN JUEGO` / LIVE) accompanied by the current match minute.
- **Stadium Enrichment**:
  - If the API does not return a match's venue, it intelligently looks it up (ignoring accents, casing, or suffixes like `FC`/`CF`) in [`estadios.json`](estadios.json). If it isn't found anywhere, it automatically logs it into `estadios_faltantes.txt`.
- **"Upcoming Matches" Mode**:
  - On days when none of your favorite teams or leagues are playing, the screen automatically switches to display the next 4 scheduled matches for your primary team ([`proximos.py`](proximos.py)).
- **"Indestructible" Bottom Ticker**:
  - RSS news feed at the bottom of the screen ([`ticker.py`](ticker.py)) injected directly into the browser's parent DOM so the CSS animation never resets when Streamlit reloads data every 10 seconds.
- **Live Weather**:
  - Local temperature and weather icon updated every 15 minutes via [Open-Meteo](https://open-meteo.com/) (no API key required).

---

## 🛠️ Requirements & Installation (Python 3.12)

1. **Clone the repository and create a virtual environment with Python 3.12**:
   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   *(On Linux / Raspberry Pi: `python3.12 -m venv .venv && source .venv/bin/activate`)*

2. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Configure the API key (`.env`)**:
   Create a `.env` file in the project root with your free token from [football-data.org](https://www.football-data.org/):
   ```env
   FOOTBALL_API_KEY=your_token_here
   ```

---

## ⚙️ Configuration (`preferencias.json`)

All dashboard settings are centralized in [`preferencias.json`](preferencias.json) and are **fully customizable to the user's liking** without touching the source code. You can freely edit this file to follow your favorite clubs, competitions, news sources, and local weather location:

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

- **`ligas` / `equipos`**: Filters the day's matches according to your preferences. The team matcher is case- and accent-insensitive, so partial names like `"Deportivo"` or `"Atlético"` work out of the box.
- **`equipo_principal_*`**: Defines the primary team queried for the *Upcoming Matches* fallback view when no matches are scheduled today (`81` corresponds to FC Barcelona in `football-data.org`).
- **`noticias_query`**: Custom Google News RSS search query for the bottom news ticker.
- **`clima`**: Latitude and longitude of your city for the weather widget in the top-right corner.

---

## 🚀 Usage

To launch the web dashboard in kiosk mode:

```powershell
.\.venv\Scripts\python.exe -m streamlit run pitch.py
```

You can also use the helper script [`partidos_hoy.py`](partidos_hoy.py) to quickly check in the terminal which matches the API returns for today:

```powershell
.\.venv\Scripts\python.exe partidos_hoy.py
```

---

## 📁 Project Structure

| File | Description |
| :--- | :--- |
| [`pitch.py`](pitch.py) | Main Streamlit application, Kiosk CSS layout, pagination, and hybrid engine. |
| [`copas.py`](copas.py) | ESPN API connector to fetch domestic cup and super cup matches. |
| [`proximos.py`](proximos.py) | Fallback view showing the next 4 upcoming matches when there are no games today. |
| [`ticker.py`](ticker.py) | Google News RSS reader and persistent footer JS/CSS component. |
| [`partidos_hoy.py`](partidos_hoy.py) | CLI script to debug today's matches in the console. |
| [`preferencias.json`](preferencias.json) | User-customizable configuration for leagues, favorite teams, primary team, news, and coordinates. |
| [`estadios.json`](estadios.json) | Local database mapping teams to their stadiums. |
| `estadios_faltantes.txt` | Auto-generated log when a home team has no stadium listed in either the API or `estadios.json`. |
