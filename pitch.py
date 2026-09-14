import streamlit as st
import requests
from datetime import datetime
import json
import os
import base64
from streamlit_autorefresh import st_autorefresh
from dotenv import load_dotenv 

load_dotenv()  

# Configuración de página ancha para aprovechar el monitor
st.set_page_config(page_title="Pitch", layout="wide")

API_KEY = os.environ.get("FOOTBALL_API_KEY", "TU_API_TOKEN_AQUI")
URL = "https://api.football-data.org/v4/matches"
ARCHIVO_PREFS = "preferencias.json"
MAX_PARTIDOS = 4 # Número máximo de partidos que caben en tu pantalla

@st.cache_data(ttl=60)
def obtener_partidos():
    headers = {"X-Auth-Token": API_KEY}
    response = requests.get(URL, headers=headers)
    if response.status_code == 200:
        return response.json().get("matches", [])
    return []

@st.cache_data(ttl=900)  # Se actualiza cada 15 minutos
def obtener_tiempo():
    # Coordenadas de Madrid (Cámbialas por tu ciudad: busca "Latitud Longitud [Tu Ciudad]" en Google)
    lat = "41.6521"
    lon = "-0.8809"
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    
    try:
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json().get("current_weather", {})
            temp = round(data.get("temperature", 0))
            codigo = data.get("weathercode", 0)
            
            # Mapeo de códigos meteorológicos de la WMO a emojis
            if codigo == 0: icono = "☀️"
            elif codigo in [1, 2, 3]: icono = "⛅"
            elif codigo in [45, 48]: icono = "🌫️"
            elif codigo in [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82]: icono = "🌧️"
            elif codigo in [71, 73, 75, 77, 85, 86]: icono = "❄️"
            elif codigo in [95, 96, 99]: icono = "⛈️"
            else: icono = "🌡️"
            
            return f"{icono} {temp}ºC"
    except:
        pass
    return "" # Si falla, no muestra nada y no rompe la pantalla


def cargar_preferencias():
    if os.path.exists(ARCHIVO_PREFS):
        with open(ARCHIVO_PREFS, "r") as archivo:
            return json.load(archivo)
    return None

def cargar_estadios():
    if os.path.exists("estadios.json"):
        with open("estadios.json", "r", encoding="utf-8") as archivo:
            return json.load(archivo)
    return {}

def registrar_estadio_faltante(nombre_equipo):
    archivo_faltantes = "estadios_faltantes.txt"
    equipos_registrados = set()
    
    # Leemos lo que ya está apuntado para no repetir
    if os.path.exists(archivo_faltantes):
        with open(archivo_faltantes, "r", encoding="utf-8") as f:
            equipos_registrados = set(line.strip() for line in f)
            
    # Si el equipo es nuevo, lo añadimos al final del archivo
    if nombre_equipo not in equipos_registrados:
        with open(archivo_faltantes, "a", encoding="utf-8") as f:
            f.write(f"{nombre_equipo}\n")

def obtener_fecha_actual():
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    
    hoy = datetime.now()
    nombre_dia = dias[hoy.weekday()]
    numero_dia = hoy.day
    nombre_mes = meses[hoy.month - 1]
    
    return f"{nombre_dia}, {numero_dia} {nombre_mes}"

def cargar_logo_local(ruta):
    try:
        with open(ruta, "rb") as img_file:
            codigo_b64 = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{codigo_b64}"
    except FileNotFoundError:
        return "" # Si no encuentra el archivo, no rompe nada

# --- ESTILOS CSS (MODO KIOSCO) ---
st.markdown("""
    <!-- Descargamos la fuente Inter directamente como si fuera una web normal -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Space+Grotesk:wght@400&display=swap" rel="stylesheet">   
    <style>
        /* El asterisco (*) obliga a TODOS los elementos a usar esta fuente */
        * {
            font-family: 'Inter', sans-serif !important;
        }
        /* Excepción: Obliga a usar Space Grotesk a esta clase y a todo lo que haya dentro de ella */
        .fuente-estadio, .fuente-estadio * {
            font-family: 'Space Grotesk', sans-serif !important;
        }
        
        #MainMenu, header, footer {visibility: hidden;}
        
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            max-width: 98% !important;
        }
        
        html, body {
            font-size: 14px !important;
        }
        
        .header-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 2rem;
            border-bottom: 2px solid #333;
            padding-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

preferencias = cargar_preferencias()
estadios_db = cargar_estadios()
clima_actual = obtener_tiempo()
fecha_hoy = obtener_fecha_actual()
hora_actual = datetime.now().strftime("%H:%M")

if preferencias is None:
    st.info("Por favor, configura Pitch primero. (Crea el archivo preferencias.json)")
    st.stop()

# Rotación cada 10 segundos
ciclo_actual = st_autorefresh(interval=10000, limit=None, key="rotacion_paginas")

matches = obtener_partidos()

if not matches:
    st.title("Pitch")
    st.info("No hay datos disponibles en la API hoy.")
else:
    # 1. Agrupar partidos por competición
    partidos_por_liga = {}
    ligas_fav = preferencias.get("ligas", [])
    equipos_fav = preferencias.get("equipos", [])
    
    # --- FUNCIÓN DE BÚSQUEDA FLEXIBLE ---
    def es_equipo_fav(nombre_api, lista_favoritos):
        nombre_api_lower = nombre_api.lower()
        for fav in lista_favoritos:
            # Comprueba si tu palabra clave (ej: "Betis") está dentro del nombre de la API
            if fav.lower() in nombre_api_lower:
                return True
        return False
    # ------------------------------------
    
    # Diccionario para "traducir" los nombres sosos de la API a nombres comerciales
    nombres_comerciales = {
        "Primera Division": "LaLiga EA Sports",
        "Championship": "Sky Bet Championship"
    }
    
    for m in matches:
        comp_name_api = m['competition']['name']
        local = m['homeTeam']['name']
        visitante = m['awayTeam']['name']
        
        # Filtramos usando la nueva búsqueda inteligente
        if comp_name_api in ligas_fav or es_equipo_fav(local, equipos_fav) or es_equipo_fav(visitante, equipos_fav):
            
            # Traducimos el nombre solo para mostrarlo bonito en la pantalla
            comp_name_visual = nombres_comerciales.get(comp_name_api, comp_name_api)
            
            if comp_name_visual not in partidos_por_liga:
                partidos_por_liga[comp_name_visual] = {
                    "emblem": m['competition'].get('emblem', ''),
                    "matches": []
                }
            partidos_por_liga[comp_name_visual]["matches"].append(m)

    # Paginación Matemática (Chunking)
    paginas_a_mostrar = []
    
    for nombre_liga, datos in partidos_por_liga.items():
        lista_partidos = datos["matches"]
        total_partidos = len(lista_partidos)
        total_paginas = (total_partidos + MAX_PARTIDOS - 1) // MAX_PARTIDOS
        
        for i in range(0, total_partidos, MAX_PARTIDOS):
            chunk = lista_partidos[i : i + MAX_PARTIDOS]
            pagina_actual = (i // MAX_PARTIDOS) + 1
            
            paginas_a_mostrar.append({
                "liga": nombre_liga,
                "emblema": datos["emblem"],
                "partidos": chunk,
                "pag_actual": pagina_actual,
                "pag_total": total_paginas
            })

    # Renderizado de la página activa
    if not paginas_a_mostrar:
        st.title("Pitch")
        st.warning("Hoy no hay partidos de tus ligas o equipos favoritos.")
    else:
        # Elegimos qué página toca mostrar en este ciclo
        indice_pagina = ciclo_actual % len(paginas_a_mostrar)
        pagina_activa = paginas_a_mostrar[indice_pagina]
        
       # --- ENCABEZADO ---
        # Detectamos si es la Premier para hacer su logo más grande
        altura_logo = "60" if pagina_activa["liga"] == "Premier League" else "35"
        
        logo_comp_html = f'<img src="{pagina_activa["emblema"]}" height="{altura_logo}" style="margin-right: 15px; vertical-align: middle;">' if pagina_activa["emblema"] else ''
        
        texto_paginacion = f"Pág {pagina_activa['pag_actual']} de {pagina_activa['pag_total']}" if pagina_activa['pag_total'] > 1 else ""
        
        # Cargamos nuestro logo (si falla o no existe, pondrá el emoji por defecto)
        logo_url = cargar_logo_local("logo.png")
        mi_logo_html = f'<img src="{logo_url}" height="50" style="margin-right: 10px; vertical-align: middle;">' if logo_url else "⚽"

        # Encabezado con Reloj a la izquierda en lugar del nombre
        header_html = f"""<div class="header-container" style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
            <div style="flex: 1; display: flex; align-items: center;">
            <div style="font-size: 2.2rem; font-weight: bold; color: #fff; display: flex; align-items: center; font-variant-numeric: tabular-nums;">
            {mi_logo_html} <span style="margin-left: 8px;">{hora_actual}</span>
            </div>
            </div>
            <div style="font-size: 1.4rem; font-weight: bold; color: #ddd; display: flex; align-items: center; justify-content: center; flex: 1.2; text-align: center;">
            {logo_comp_html} {pagina_activa["liga"]}
            </div>
            <div style="flex: 1; display: flex; flex-direction: column; align-items: flex-end;">
            <div style="white-space: nowrap; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.1rem; font-weight: bold; color: #ddd;">{fecha_hoy}</span>
            <span style="font-size: 1.1rem; color: #555;">|</span>
            <span style="font-size: 1rem; color: #aaa; font-weight: normal;">{clima_actual}</span>
            </div>
            <span style="font-size: 0.9rem; color: #888; font-weight: normal; margin-top: 4px;">{texto_paginacion}</span>
            </div>
            </div>"""
        st.markdown(header_html, unsafe_allow_html=True)
        
        # --- FILAS DE PARTIDOS ---
        for match in pagina_activa["partidos"]:
            escudo_local = match['homeTeam'].get('crest', '')
            escudo_visitante = match['awayTeam'].get('crest', '')
            
            # --- Lógica de Estadio Enriquecida ---
            nombre_equipo_local = match['homeTeam']['name']

            if nombre_equipo_local not in estadios_db:
                registrar_estadio_faltante(nombre_equipo_local)
            
            # Intentamos cogerlo de la API
            estadio = match.get('venue')
            
            # Si la API no lo tiene (es None o vacío), miramos en nuestro JSON
            if not estadio:
                estadio = estadios_db.get(nombre_equipo_local)
                
            # Si tampoco lo tenemos en el JSON, ponemos el genérico
            if not estadio:
                estadio = "Estadio Local"

            estado = match['status']
            
            utc_str = match['utcDate'].replace('Z', '+00:00')
            local_time = datetime.fromisoformat(utc_str).astimezone()
            hora = local_time.strftime("%H:%M")
            
            if estado == "IN_PLAY":
                estado_visual = "EN JUEGO"
            elif estado == "PAUSED":
                estado_visual = "DESCANSO"
            elif estado == "FINISHED":
                estado_visual = "FINALIZADO"
            else:
                estado_visual = f" {hora}"
                
            col_estadio, col_partido, col_estado = st.columns([1.5, 3, 1.5], vertical_alignment="center") 
            
            with col_estadio:
                st.markdown(f'<div class="fuente-estadio" style="text-align: left; color: #fff; font-size: 1.1em; font-weight: 400;">{estadio}</div>', unsafe_allow_html=True)
                #st.markdown(f"<div style='text-align: left; color: #fff; font-size: 1.1em; font-family: \"Titillium Web\", sans-serif !important; font-weight: 400;'>{estadio}</div>", unsafe_allow_html=True)            
                #st.markdown(f'<div style="text-align: left; color: #fff; font-size: 1.1em; font-family: \'Space Grotesk\', sans-serif !important; font-weight: 400;">{estadio}</div>', unsafe_allow_html=True)    
            with col_partido:
                if estado in ["IN_PLAY", "PAUSED", "FINISHED"]:
                    goles_local = match.get('score', {}).get('fullTime', {}).get('home')
                    goles_visitante = match.get('score', {}).get('fullTime', {}).get('away')
                    goles_local = goles_local if goles_local is not None else 0
                    goles_visitante = goles_visitante if goles_visitante is not None else 0
                    
                    elemento_central = f'<div style="background-color: #222; border-radius: 8px; padding: 5px 25px; margin: 0 20px; border: 1px solid #444; box-shadow: 0 4px 6px rgba(0,0,0,0.3);"><span style="font-size: 2.2rem; font-weight: bold; color: #fff; font-family: monospace;">{goles_local} - {goles_visitante}</span></div>'
                else:
                    elemento_central = '<span style="color: #555; font-size: 1.5rem; margin: 0 30px;">vs</span>'

                html_equipos = f'<div style="display: flex; align-items: center; justify-content: center; height: 100%;"><img src="{escudo_local}" width="50" style="display: block;">{elemento_central}<img src="{escudo_visitante}" width="50" style="display: block;"></div>'                
                st.markdown(html_equipos, unsafe_allow_html=True)
                
            with col_estado:
                st.markdown(f"<div style='height: 100%; display: flex; align-items: center; justify-content: flex-end; font-size: 1.4rem; font-weight: bold;'>{estado_visual}</div>", unsafe_allow_html=True)
                
            st.divider()