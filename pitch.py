import streamlit as st
import proximos
import ticker
import copas
import requests
from datetime import datetime
import json
import os
import base64
import unicodedata
from streamlit_autorefresh import st_autorefresh
from dotenv import load_dotenv 

load_dotenv()  

# Configuración de página ancha para aprovechar el monitor
st.set_page_config(page_title="Pitch", layout="wide")

API_KEY = os.environ.get("FOOTBALL_API_KEY", "TU_API_TOKEN_AQUI")
URL = "https://api.football-data.org/v4/matches"
ARCHIVO_PREFS = "preferencias.json"
MAX_PARTIDOS = 4 # Número máximo de partidos que caben en tu pantalla

@st.cache_data(ttl=60, show_spinner=False)
def obtener_partidos():
    headers = {"X-Auth-Token": API_KEY}
    response = requests.get(URL, headers=headers)
    if response.status_code == 200:
        return response.json().get("matches", [])
    return []

@st.cache_data(ttl=900, show_spinner=False)  # Se actualiza cada 15 minutos
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
        # Obligamos a leer en UTF-8 para que no rompa las tildes ni las eñes
        with open(ARCHIVO_PREFS, "r", encoding="utf-8") as archivo:
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
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700&family=Space+Grotesk:wght@400;700&display=swap" rel="stylesheet">   
    <style>
        /* 1. Todo el panel usa Space Grotesk por defecto */
        * {
            font-family: 'Space Grotesk', sans-serif !important;
        }
        
        /* 2. TRUCO DE ESPACIO: Matamos por completo la cabecera invisible de Streamlit */
        #MainMenu, header, footer, [data-testid="stHeader"] {
            visibility: hidden;
            display: none !important;
            height: 0px !important;
        }
        
        /* 3. TRUCO DE ESPACIO: Subimos el panel pegándolo arriba y dejamos margen abajo para el Ticker */
        .block-container {
            padding-top: 0rem !important; 
            margin-top: -1.5rem !important; 
            padding-bottom: 4rem !important;
            max-width: 98% !important;
        }
        
        html, body {
            font-size: 14px !important;
        }
        
        /* 4. TRUCO DE ESPACIO: Reducimos el aire debajo del encabezado (reloj/fecha) */
        .header-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.5rem; 
            border-bottom: 2px solid #333;
            padding-bottom: 0.5rem; 
            margin-top: 0;
        }

        /* Clase exclusiva para que el marcador destaque con Barlow Condensed Bold */
        .fuente-marcador {
            font-family: 'Barlow Condensed', sans-serif !important;
            letter-spacing: 1px;
        }

        /* Animación para el punto pulsante de los partidos en directo */
        @keyframes latido-verde {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(57, 255, 20, 0.7); }
            70% { transform: scale(1.1); box-shadow: 0 0 0 10px rgba(57, 255, 20, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(57, 255, 20, 0); }
        }
        
        .punto-directo {
            width: 12px;
            height: 12px;
            background-color: #39FF14;
            border-radius: 50%;
            display: inline-block;
            margin-right: 10px;
            animation: latido-verde 2s infinite;
        }

        /* 5. TRUCO NINJA: Matar el oscurecimiento (dimming) de Streamlit cuando recarga */
        .element-container, 
        [data-testid="stAppViewBlockContainer"],
        [data-testid="stAppViewContainer"],
        [data-testid="stVerticalBlock"] {
            opacity: 1 !important;
            filter: none !important;
            transition: none !important;
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

# --- MOTOR HÍBRIDO DE PARTIDOS ---
matches = obtener_partidos()
matches_extra = copas.obtener_partidos_extra()
matches.extend(matches_extra) # Fusionamos ambas listas en una sola

if not matches:
    # 1. Obtenemos los próximos partidos usando el nuevo archivo
    partidos_futuros = proximos.obtener_proximos(API_KEY)
    
    # 2. Renderizamos el Encabezado genérico (mantenemos el Reloj y el Clima)
    logo_url = cargar_logo_local("logo.png")
    mi_logo_html = f'<img src="{logo_url}" height="50" style="margin-right: 10px; vertical-align: middle;">'
    
    header_html = f"""<div class="header-container" style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
        <div style="flex: 1; display: flex; align-items: center;">
        <div style="font-size: 2.2rem; font-weight: bold; color: #fff; display: flex; align-items: center; font-variant-numeric: tabular-nums;">
        {mi_logo_html} <span style="margin-left: 8px;">{hora_actual}</span>
        </div>
        </div>
        <div style="font-size: 1.4rem; font-weight: bold; color: #ddd; display: flex; align-items: center; justify-content: center; flex: 1.2; text-align: center;">
        Próximos Partidos
        </div>
        <div style="flex: 1; display: flex; flex-direction: column; align-items: flex-end;">
        <div style="white-space: nowrap; display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 1.1rem; font-weight: bold; color: #ddd;">{fecha_hoy}</span>
        <span style="font-size: 1.1rem; color: #555;">|</span>
        <span style="font-size: 1rem; color: #aaa; font-weight: normal;">{clima_actual}</span>
        </div>
        </div>
        </div>"""
    st.markdown(header_html, unsafe_allow_html=True)
    
    # 3. Llamamos a nuestra función para pintar las filas
    proximos.renderizar(partidos_futuros)
else:
    # 1. Agrupar partidos por competición
    partidos_por_liga = {}
    ligas_fav = preferencias.get("ligas", [])
    equipos_fav = preferencias.get("equipos", [])
    
    # --- FUNCIÓN DE BÚSQUEDA INTELIGENTE (A PRUEBA DE TILDES) ---
    def normalizar_texto(texto):
        # Esta función quita las tildes y convierte a minúsculas
        texto = unicodedata.normalize('NFD', texto)
        return ''.join(c for c in texto if unicodedata.category(c) != 'Mn').lower()

    def es_equipo_fav(nombre_api, lista_favoritos):
        nombre_api_norm = normalizar_texto(nombre_api)
        for fav in lista_favoritos:
            # Comparamos ambas palabras sin tildes y en minúsculas
            if normalizar_texto(fav) in nombre_api_norm:
                return True
        return False
    # ------------------------------------------------------------
    
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
        # Reutilizamos el estado vacío que llama a proximos.py si después de filtrar no queda nada
        partidos_futuros = proximos.obtener_proximos(API_KEY)
        logo_url = cargar_logo_local("logo.png")
        mi_logo_html = f'<img src="{logo_url}" height="50" style="margin-right: 10px; vertical-align: middle;">'
        
        header_html = f"""<div class="header-container" style="display: flex; justify-content: space-between; align-items: center; width: 100%;">
            <div style="flex: 1; display: flex; align-items: center;">
            <div style="font-size: 2.2rem; font-weight: bold; color: #fff; display: flex; align-items: center; font-variant-numeric: tabular-nums;">
            {mi_logo_html} <span style="margin-left: 8px;">{hora_actual}</span>
            </div>
            </div>
            <div style="font-size: 1.4rem; font-weight: bold; color: #ddd; display: flex; align-items: center; justify-content: center; flex: 1.2; text-align: center;">
            Próximos Partidos
            </div>
            <div style="flex: 1; display: flex; flex-direction: column; align-items: flex-end;">
            <div style="white-space: nowrap; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.1rem; font-weight: bold; color: #ddd;">{fecha_hoy}</span>
            <span style="font-size: 1.1rem; color: #555;">|</span>
            <span style="font-size: 1rem; color: #aaa; font-weight: normal;">{clima_actual}</span>
            </div>
            </div>
            </div>"""
        st.markdown(header_html, unsafe_allow_html=True)
        proximos.renderizar(partidos_futuros)
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
        mi_logo_html = f'<img src="{logo_url}" height="60" style="margin-right: 10px; vertical-align: middle;">' if logo_url else "⚽"

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
        total_partidos = len(pagina_activa["partidos"])
        
        for idx, match in enumerate(pagina_activa["partidos"]):
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
                # Verde neón brillante con el punto pulsante
                estado_html = '<div style="color: #39FF14; display: flex; align-items: center;"><span class="punto-directo"></span> EN JUEGO</div>'
            elif estado == "PAUSED":
                # Ámbar/Naranja neutro, sin animar
                estado_html = '<div style="color: #FFB347;">DESCANSO</div>'
            elif estado == "FINISHED":
                # Gris muy apagado, se funde con el fondo
                estado_html = '<div style="color: #555555;">FINALIZADO</div>'
            elif estado in ["SUSPENDED", "POSTPONED", "CANCELLED"]:
                # Rojo de alerta para partidos suspendidos o aplazados
                estado_html = '<div style="color: #FF4444; font-weight: bold;">SUSPENDIDO</div>'
            else:
                # Hora del partido (gris claro)
                estado_html = f'<div style="color: #aaaaaa;">{hora}</div>'
                
            col_estadio, col_partido, col_estado = st.columns([1.5, 3, 1.5], vertical_alignment="center") 
            
            with col_estadio:
                st.markdown(f'<div style="text-align: left; color: #aaaaaa; font-size: 1.1em; font-weight: 400;">{estadio}</div>', unsafe_allow_html=True)    
            
            with col_partido:
                if estado in ["IN_PLAY", "PAUSED", "FINISHED"]:
                    goles_local = match.get('score', {}).get('fullTime', {}).get('home')
                    goles_visitante = match.get('score', {}).get('fullTime', {}).get('away')
                    goles_local = goles_local if goles_local is not None else 0
                    goles_visitante = goles_visitante if goles_visitante is not None else 0
                    
                    # Marcador centrado, compacto y con line-height 1 para evitar aire extra
                    elemento_central = f'<div style="background-color: #222; border-radius: 8px; padding: 4px 20px; margin: 0 20px; border: 1px solid #444; box-shadow: 0 4px 6px rgba(0,0,0,0.3); display: flex; align-items: center;"><span class="fuente-marcador" style="font-size: 2.8rem; font-weight: bold; color: #fff; line-height: 1;">{goles_local} - {goles_visitante}</span></div>'
                else:
                    elemento_central = '<span style="color: #555; font-size: 1.5rem; margin: 0 30px;">vs</span>'

                # Margin-top rebajado a 5px
                html_equipos = f'<div style="display: flex; align-items: center; justify-content: center; height: 100%; margin-top: 5px;"><img src="{escudo_local}" width="50" style="display: block;">{elemento_central}<img src="{escudo_visitante}" width="50" style="display: block;"></div>'                
                st.markdown(html_equipos, unsafe_allow_html=True)
                
            with col_estado:
                st.markdown(f"<div style='height: 100%; display: flex; align-items: center; justify-content: flex-end; font-size: 1.4rem; font-weight: bold;'>{estado_html}</div>", unsafe_allow_html=True)    
            
            # Control de la línea separadora
            if idx < total_partidos - 1:
                st.divider()

# Renderizamos el Ticker de noticias en el pie de página (fuera de todos los if/else)
ticker.renderizar()