import streamlit as st
import requests
from datetime import datetime, date

@st.cache_data(ttl=60, show_spinner=False)
def obtener_partidos_extra():
    # Usamos el CDN público de API-Football (imágenes PNG nativas, transparentes y sin bloqueos)
    ligas_espn = {
        "esp.copa_del_rey": {"name": "Copa del Rey", "emblem": "https://media.api-sports.io/football/leagues/143.png"},
        "eng.fa": {"name": "FA Cup", "emblem": "https://media.api-sports.io/football/leagues/45.png"},
        "eng.league_cup": {"name": "Carabao Cup", "emblem": "https://media.api-sports.io/football/leagues/48.png"},
        "esp.super_cup": {"name": "Supercopa de España", "emblem": "https://media.api-sports.io/football/leagues/556.png"},
        "uefa.super_cup": {"name": "Supercopa de Europa", "emblem": "https://media.api-sports.io/football/leagues/531.png"}
    }

    partidos_traducidos = []
    hoy = date.today()

    for liga_code, liga_info in ligas_espn.items():
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{liga_code}/scoreboard"
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                eventos = res.json().get("events", [])

                for evento in eventos:
                    
                    # --- 1. FILTRO DE FECHA (SOLO HOY) ---
                    # ESPN manda la hora en formato UTC (ej: 2026-09-16T19:00:00Z)
                    fecha_utc_str = evento["date"].replace('Z', '+00:00')
                    fecha_local = datetime.fromisoformat(fecha_utc_str).astimezone()
                    
                    # Si el día del partido no es exactamente hoy, lo ignoramos y pasamos al siguiente
                    if fecha_local.date() != hoy:
                        continue
                    # -------------------------------------

                    comp = evento["competitions"][0]
                    equipos = comp["competitors"]
                    
                    # Identificar local y visitante
                    home = equipos[0] if equipos[0]["homeAway"] == "home" else equipos[1]
                    away = equipos[1] if equipos[0]["homeAway"] == "home" else equipos[0]

                    # --- TRADUCCIÓN DE ESTADOS DEFINITIVA ---
                    tipo_estado = evento["status"]["type"]
                    fase_partido = tipo_estado.get("state", "pre")  # "pre", "in", "post"
                    completado = tipo_estado.get("completed", False)
                    nombre_estado = tipo_estado.get("name", "")
                    reloj_partido = evento["status"].get("displayClock", "")
                    
                    if nombre_estado in ["STATUS_POSTPONED", "STATUS_CANCELED", "STATUS_SUSPENDED", "STATUS_DELAYED"]:
                        estado = "SUSPENDED"
                    elif completado or fase_partido == "post":
                        estado = "FINISHED"
                    elif fase_partido == "in":
                        if nombre_estado in ["STATUS_HALFTIME", "STATUS_END_OF_REGULATION", "STATUS_END_OF_EXTRA_TIME"]:
                            estado = "PAUSED"
                        else:
                            estado = "IN_PLAY"
                    else:
                        estado = "TIMED"
                    # ----------------------------------------

                    # Goles
                    goles_home = int(home.get("score", 0)) if home.get("score") else None
                    goles_away = int(away.get("score", 0)) if away.get("score") else None

                    # Creamos un "clon" del formato de football-data.org
                    partido_clon = {
                        "competition": {"name": liga_info["name"], "emblem": liga_info["emblem"]},
                        "homeTeam": {"name": home["team"]["name"], "crest": home["team"].get("logo", "")},
                        "awayTeam": {"name": away["team"]["name"], "crest": away["team"].get("logo", "")},
                        "status": estado,
                        "minute": reloj_partido,
                        "utcDate": evento["date"],
                        "score": {"fullTime": {"home": goles_home, "away": goles_away}},
                        "venue": comp.get("venue", {}).get("fullName", "")
                    }
                    partidos_traducidos.append(partido_clon)
        except:
            continue

    return partidos_traducidos