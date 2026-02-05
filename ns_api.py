import requests
import os
from dotenv import load_dotenv

# 1. Laad de API key uit je .env bestand
load_dotenv()
ns_api_key = os.getenv('NS_API_KEY')

if not ns_api_key:
    print("⚠️ LET OP: Geen NS_API_KEY gevonden in .env bestand!")

# 2. Dit zijn de headers die we overal nodig hebben
HEADERS = {'Ocp-Apim-Subscription-Key': ns_api_key}

def get_journey_details(ritnummer):
    """Haal de complete route op van een specifiek ritnummer"""
    url = "https://gateway.apiportal.ns.nl/reisinformatie-api/api/v2/journey"
    
    params = {
        "train": ritnummer
    }
    
    try:
        # We gebruiken hier de globale HEADERS variabele
        # verify=False is nodig op sommige schoolnetwerken
        response = requests.get(url, params=params, headers=HEADERS, timeout=5, verify=False)
        
        if response.status_code == 200:
            payload = response.json().get('payload', {})
            return payload
        else:
            print(f"⚠️ API Fout {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"⚠️ Error bij ophalen rit: {e}")
        return None

def get_arrivals(station_code):
    """(Oude functie) Haal aankomsttijden op"""
    url = "https://gateway.apiportal.ns.nl/reisinformatie-api/api/v2/arrivals"
    params = {
        "station": station_code,
        "lang": "nl",
        "maxJourneys": 25
    }
    
    try:
        # verify=False is nodig als je SSL errors krijgt (school wifi)
        response = requests.get(url, params=params, headers=HEADERS, timeout=5, verify=False)
        if response.status_code == 200:
            return response.json().get('payload', {}).get('arrivals', [])
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def get_station_name(code):
    stations = {
        "HGL": "Hengelo",
        "ES": "Enschede",
        "ESK": "Enschede Kennispark",
        "BN": "Borne",
        "AML": "Almelo",
        "UT": "Utrecht Centraal",
        "ZW": "Zwolle"
    }
    return stations.get(code.upper(), code)