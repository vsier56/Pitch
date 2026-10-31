import streamlit as st
import requests
import xml.etree.ElementTree as ET
import streamlit.components.v1 as components
import base64

@st.cache_data(ttl=1800)
def obtener_noticias():
    url = "https://news.google.com/rss/search?q=FC+Barcelona+site:sport.es&hl=es&gl=ES&ceid=ES:es"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            titulares = []
            for item in root.findall('./channel/item')[:10]:
                titulo = item.find('title').text
                titulo = titulo.replace(" - Diario Sport", "").replace(" - SPORT", "")
                titulares.append(titulo.strip())
            if titulares:
                return titulares
    except:
        pass
    return ["Problemas de conexión con las noticias..."]

def renderizar():
    noticias = obtener_noticias()
    texto_ticker = " &nbsp;&nbsp;&nbsp; • &nbsp;&nbsp;&nbsp; ".join(noticias)
    
    # Montamos el texto final en HTML
    html_texto = f'<span style="color: #39FF14; font-weight: bold;">ÚLTIMA HORA</span> &nbsp;&nbsp;|&nbsp;&nbsp; {texto_ticker}'
    
    # TRUCO NINJA: Lo codificamos en Base64 (UTF-8) para que viaje 100% seguro al Javascript
    b64_texto = base64.b64encode(html_texto.encode('utf-8')).decode('utf-8')

    # Código Javascript "Indestructible"
    js_code = f"""
    <script>
    // 1. Apuntamos al documento principal del navegador (fuera del control de Streamlit)
    const doc = window.parent.document;
    
    // 2. Buscamos si ya hemos creado nuestro ticker
    let ticker = doc.getElementById('ticker-indestructible');
    
    if (!ticker) {{
        // Si no existe, inyectamos el CSS directamente al navegador
        const style = doc.createElement('style');
        style.innerHTML = `
            #ticker-indestructible {{
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                overflow: hidden;
                background-color: #000;
                border-top: 2px solid #39FF14;
                padding-left: 100%;
                box-sizing: content-box;
                z-index: 999999;
            }}
            .ticker-content {{
                display: inline-block;
                height: 45px;
                line-height: 45px;
                white-space: nowrap;
                padding-right: 100%;
                box-sizing: content-box;
                animation: animacion-ticker 100s linear infinite; /* 50s para lectura suave */
                color: #ddd;
                font-size: 1.2rem;
                font-family: 'Space Grotesk', sans-serif;
            }}
            @keyframes animacion-ticker {{
                0%   {{ transform: translate3d(0, 0, 0); }}
                100% {{ transform: translate3d(-100%, 0, 0); }}
            }}
        `;
        doc.head.appendChild(style);
        
        // Creamos la caja del ticker
        ticker = doc.createElement('div');
        ticker.id = 'ticker-indestructible';
        ticker.innerHTML = '<div class="ticker-content" id="ticker-texto"></div>';
        
        // Lo pegamos al fondo de la pantalla
        const app = doc.querySelector('.stApp') || doc.body;
        app.appendChild(ticker);
    }}
    
    // 3. Decodificamos el texto desde Base64 garantizando las tildes y eñes
    const b64Data = '{b64_texto}';
    const binString = window.atob(b64Data);
    const bytes = new Uint8Array(binString.length);
    for (let i = 0; i < binString.length; i++) {{
        bytes[i] = binString.charCodeAt(i);
    }}
    const nuevoTexto = new TextDecoder('utf-8').decode(bytes);
    
    // ¡LA MAGIA!: Solo tocamos el texto si ha cambiado la noticia. 
    // Como no tocamos la caja en cada ciclo de 10s, la animación jamás se reinicia.
    const tickerTexto = doc.getElementById('ticker-texto');
    if (tickerTexto.innerHTML !== nuevoTexto) {{
        tickerTexto.innerHTML = nuevoTexto;
    }}
    </script>
    """
    
    # Inyectamos el Javascript de forma invisible en la app
    components.html(js_code, height=0, width=0)