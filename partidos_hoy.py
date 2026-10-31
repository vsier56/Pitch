import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de la API
API_KEY = os.environ.get("FOOTBALL_API_KEY", "TU_API_TOKEN_AQUI")
URL = "https://api.football-data.org/v4/matches"

headers = {
    "X-Auth-Token": API_KEY
}

def obtener_partidos_hoy():
    print("Consultando el calendario de hoy...")
    try:
        response = requests.get(URL, headers=headers, timeout=5)
    except requests.RequestException as e:
        print(f"Error de conexión: {e}")
        return

    # Si la petición es exitosa (código 200)
    if response.status_code == 200:
        data = response.json()
        matches = data.get("matches", [])
        
        if not matches:
            print("\nNo hay partidos programados para hoy.")
            return

        print(f"\n--- Partidos de Hoy ({len(matches)}) ---")
        
        for match in matches:
            competicion = match['competition']['name']
            local = match['homeTeam']['name']
            visitante = match['awayTeam']['name']
            estado = match['status']
            
            # La API entrega la hora en formato UTC (ej. 2026-09-12T19:00:00Z)
            # Reemplazamos la 'Z' para que Python reconozca que es UTC
            utc_str = match['utcDate'].replace('Z', '+00:00')
            utc_time = datetime.fromisoformat(utc_str)
            
            # astimezone() convierte la hora UTC a la hora local de tu ordenador/Raspberry
            local_time = utc_time.astimezone()
            hora_formateada = local_time.strftime("%H:%M")
            
            print(f"[{hora_formateada}] {competicion} | {local} vs {visitante} (Estado: {estado})")
            
    else:
        print(f"Error {response.status_code}: No se pudieron obtener los datos.")
        print(response.text)

if __name__ == "__main__":
    obtener_partidos_hoy()