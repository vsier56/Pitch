import streamlit as st
import requests
from datetime import datetime

@st.cache_data(ttl=3600, show_spinner=False)
def obtener_proximos(api_key):
    # TRUCO: El ID interno del FC Barcelona en football-data.org es el 81.
    # Al pedir directamente los partidos de un equipo, la API gratuita no nos bloquea.
    url = "https://api.football-data.org/v4/teams/81/matches?status=SCHEDULED"
    headers = {"X-Auth-Token": api_key}
    
    try:
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            partidos = res.json().get("matches", [])
            # Cortamos la lista para devolver exactamente los próximos 4
            return partidos[:4]
    except:
        pass
    return []

def renderizar(partidos):
    if not partidos:
        st.info("No hay partidos programados para el FC Barcelona.")
        return

    total_partidos = len(partidos)

    for idx, match in enumerate(partidos):
        escudo_local = match['homeTeam'].get('crest', '')
        escudo_visitante = match['awayTeam'].get('crest', '')
        
        # Intentamos sacar el estadio de la API
        estadio = match.get('venue')
        if not estadio:
            # Si la API no lo manda, deducimos el estadio si el Barça juega en casa
            if match['homeTeam']['name'] == "FC Barcelona":
                estadio = "Spotify Camp Nou"
            else:
                estadio = "Estadio Visitante"
                
        # Fecha y Hora
        utc_str = match['utcDate'].replace('Z', '+00:00')
        local_time = datetime.fromisoformat(utc_str).astimezone()
        
        # Formateamos para que salga el día y el mes (Ej: 25/10)
        dia_mes = local_time.strftime("%d/%m")
        hora = local_time.strftime("%H:%M")
        
        # Usamos exactamente las mismas columnas y proporciones que en pitch.py
        col_estadio, col_partido, col_estado = st.columns([1.5, 3, 1.5], vertical_alignment="center") 
        
        with col_estadio:
            st.markdown(f'<div style="text-align: left; color: #aaaaaa; font-size: 1.1em; font-weight: 400;">{estadio}</div>', unsafe_allow_html=True)    
        
        with col_partido:
            # En lugar de los goles, ponemos la fecha en la caja central usando la tipografía del marcador
            elemento_central = f'<div style="background-color: #222; border-radius: 8px; padding: 4px 20px; margin: 0 20px; border: 1px solid #444; box-shadow: 0 4px 6px rgba(0,0,0,0.3); display: flex; align-items: center;"><span class="fuente-marcador" style="font-size: 2.8rem; font-weight: bold; color: #fff; line-height: 1;">{dia_mes}</span></div>'

            # Mismo margen superior para cuadrar alturas
            html_equipos = f'<div style="display: flex; align-items: center; justify-content: center; height: 100%; margin-top: 5px;"><img src="{escudo_local}" width="50" style="display: block;">{elemento_central}<img src="{escudo_visitante}" width="50" style="display: block;"></div>'                
            st.markdown(html_equipos, unsafe_allow_html=True)
            
        with col_estado:
            # En la derecha colocamos la hora del partido
            st.markdown(f"<div style='height: 100%; display: flex; align-items: center; justify-content: flex-end; font-size: 1.4rem; font-weight: bold; color: #aaaaaa;'>{hora}</div>", unsafe_allow_html=True)
            
        if idx < total_partidos - 1:
            st.divider()