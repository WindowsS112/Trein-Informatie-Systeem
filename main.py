import pygame
import os
import sys
from datetime import datetime

# --- SETUP ---
os.environ['SDL_AUDIODRIVER'] = 'dummy'
sys.path.append('src')

from ns_api import get_journey_details
from models import Trein
from ffmpeg_helper import FFMPEG_helper

# ==========================================
# ⚙️ INSTELLINGEN
# ==========================================
GEZOCHT_TREINNUMMER = 7346  # <-- VUL HIER JE NUMMER IN
WIDTH, HEIGHT = 1650, 900
FPS = 60
DURATION_SECONDS = 30 # Mag langer duren om beweging te zien
TOTAL_FRAMES = FPS * DURATION_SECONDS

# Kleuren
LMS_COLOR = (0, 158, 132) # NS Groen/Blauw
WIT = (255, 255, 255)
GOUD = (255, 215, 0)
GRIJS = (100, 100, 100)
ROOD = (255, 50, 50)

# ==========================================
# 🚀 INITIALISATIE
# ==========================================
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 30)
large_font = pygame.font.SysFont("Arial", 50, bold=True)
small_font = pygame.font.SysFont("Arial", 20)

ffmpeg = FFMPEG_helper()
mijn_trein = Trein(x=0, y=420)

# ==========================================
# 📡 DATA OPHALEN (Één keer bij start)
# ==========================================
print(f"🔄 Rit {GEZOCHT_TREINNUMMER} ophalen...")
rit_data = get_journey_details(GEZOCHT_TREINNUMMER)
stops = []

if rit_data:
    stops = rit_data.get('stops', [])
    if stops:
        # Vul statische data
        mijn_trein.herkomst = stops[0]['stop']['name']
        mijn_trein.route_lijst = [s['stop']['name'] for s in stops]
        print(f"✅ Rit gevonden: {mijn_trein.herkomst} -> {stops[-1]['stop']['name']}")
    else:
        print("⚠️ Rit gevonden, maar geen stops in de data.")
else:
    print("❌ Kon rit niet ophalen. Check API Key en Internet.")


# ==========================================
# 🎬 GAME LOOP
# ==========================================
for frame_count in range(TOTAL_FRAMES):
    # 1. Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            del ffmpeg
            pygame.quit()
            sys.exit()

# 2. LOGICA: WAAR IS DE TREIN NU? 🧠
    nu = datetime.now()
    
    # In v3/trips zit de info in trips -> legs -> stops
    # We checken even of de structuur klopt voor jouw data
    # (Als je v2/journey gebruikt is het direct 'stops', bij v3/trips moet je even graven)
    if rit_data.get('trips'):
        # Pak de eerste de beste reisoptie
        stops = rit_data['trips'][0]['legs'][0]['stops']
    elif rit_data.get('stops'):
        # Fallback voor de Journey API (die we eerder gebruikten)
        stops = rit_data['stops']
    
    if stops:
        found_active_segment = False
        
        for index, stop in enumerate(stops):
            # 1. Haal de tijd op 
            tijd_str = stop.get('actualDepartureDateTime') or stop.get('actualArrivalDateTime')
            
            if tijd_str:
                stop_tijd = datetime.fromisoformat(tijd_str).replace(tzinfo=None)
                
                # 2. Zoek de EERSTE stop die in de toekomst ligt
                if stop_tijd > nu:
                    mijn_trein.huidige_stop_index = index
                    
                    # --- FIX: Gebruik ['stop']['name'] ---
                    mijn_trein.bestemming = stop['stop']['name'] 
                    
                    mijn_trein.spoor = stop.get('actualArrivalTrack', '?')
                    mijn_trein.volgende_stop_tijd = stop_tijd
                    
                    # ETA Berekenen
                    mijn_trein.aankomst_tijd = stop_tijd.strftime("%H:%M")
                    mijn_trein.minuten_resterend = max(0, int((stop_tijd - nu).total_seconds() / 60))

                    # 3. Positie op de balk berekenen
                    if index > 0:
                        vorige_stop = stops[index - 1]
                        v_tijd_str = vorige_stop.get('actualDepartureDateTime') or vorige_stop.get('actualArrivalDateTime')
                        
                        if v_tijd_str:
                            mijn_trein.vorige_stop_tijd = datetime.fromisoformat(v_tijd_str).replace(tzinfo=None)
                            
                            totaal = (mijn_trein.volgende_stop_tijd - mijn_trein.vorige_stop_tijd).total_seconds()
                            verstreken = (nu - mijn_trein.vorige_stop_tijd).total_seconds()
                            
                            if totaal > 0:
                                mijn_trein.percentage_onderweg = max(0.0, min(1.0, verstreken / totaal))
                            else:
                                mijn_trein.percentage_onderweg = 0.0
                    else:
                        mijn_trein.percentage_onderweg = 0.0
                    
                    found_active_segment = True
                    break 
        
        if not found_active_segment:
            # --- FIX: Ook hier ['stop']['name'] gebruiken! ---
            # Als de trein al klaar is, pakken we de laatste uit de lijst
            mijn_trein.bestemming = stops[-1]['stop']['name']
            
            mijn_trein.percentage_onderweg = 1.0 
            mijn_trein.minuten_resterend = 0


    # 3. TEKENEN
    screen.fill(LMS_COLOR)
    
    # Rails tekenen (Bovenste visuele trein)
    pygame.draw.rect(screen, (80, 80, 80), (0, 500, WIDTH, 20))
    
    # De Grote Trein (Visueel) - Laten we die gewoon rijden voor de show
    visuele_progress = (frame_count % (FPS * 100)) / (FPS * 300) # Elke 10 sec rondje
    mijn_trein.teken(screen, visuele_progress)

    # --- TEKSTEN ---
    txt_stop = large_font.render(f"Route: {mijn_trein.bestemming}", True, GOUD)
    txt_herkomst = font.render(f"Rit vanuit: {mijn_trein.herkomst}", True, WIT)
    txt_spoor = font.render(f"Volgende stop: Rotterdam Noord", True, WIT)
    
    # ETA Kleur
    if mijn_trein.minuten_resterend <= 0:
        eta_txt = "Aankomst: 7 Min"
        eta_kleur = WIT
    else:
        eta_txt = f"Aankomst: {mijn_trein.aankomst_tijd} ({mijn_trein.minuten_resterend} min)"
        eta_kleur = WIT
    txt_eta = font.render(eta_txt, True, eta_kleur)

    screen.blit(txt_stop, (50, 50))
    screen.blit(txt_herkomst, (50, 110))
    screen.blit(txt_spoor, (50, 150))
    screen.blit(txt_eta, (50, 200))


    # --- DYNAMISCHE ROUTEBALK (ONDERIN) ---
    if mijn_trein.route_lijst:
        bar_y = 650
        margin_x = 100       # Iets minder marge links
        station_gap = 250   # <--- KLEINER MAKEN (was 200 of 220)
        
        # We proberen de huidige stop in beeld te houden
        start_index = max(0, mijn_trein.huidige_stop_index - 1)
        
        # AANPASSING: Hier maken we er 6 van in plaats van 4
        zichtbare_stations = mijn_trein.route_lijst[start_index : start_index + 7]
        
        for i, naam in enumerate(zichtbare_stations):
            x = margin_x + (i * station_gap)
            echte_index = start_index + i
            
            # Lijn naar rechts
            if i < len(zichtbare_stations) - 1:
                pygame.draw.line(screen, WIT, (x, bar_y), (x + station_gap, bar_y), 4)
            
            # Bolletje Kleur
            if echte_index < mijn_trein.huidige_stop_index:
                kleur = GRIJS
                radius = 10
            elif echte_index == mijn_trein.huidige_stop_index:
                kleur = GOUD
                radius = 15
            else:
                kleur = WIT
                radius = 10
            
            pygame.draw.circle(screen, kleur, (x, bar_y), radius)
            
            # Naam
            lbl = small_font.render(naam, True, kleur)
            lbl_rect = lbl.get_rect(center=(x, bar_y + 35))
            screen.blit(lbl, lbl_rect)

        # 🚂 DE POSITIE-INDICATOR 🚂
        # De trein zit tussen station index 0 (vorige) en 1 (volgende) in ons zichtbare lijstje
        if len(zichtbare_stations) >= 2:
            start_x_lijn = margin_x     # Positie van vorig station
            afstand_px = station_gap    # Afstand naar volgend station
            
            # Bereken exacte pixelpositie
            trein_x = start_x_lijn + (afstand_px * mijn_trein.percentage_onderweg)
            
            # Teken indicator
            indicator_rect = pygame.Rect(trein_x - 10, bar_y - 10, 20, 20)
            pygame.draw.rect(screen, (255, 100, 100), indicator_rect, border_radius=5)
            
            # Percentage tekstje erboven (voor debug/coolness)
            perc_txt = small_font.render(f"{int(mijn_trein.percentage_onderweg * 100)}%", True, GOUD)
            screen.blit(perc_txt, (trein_x - 15, bar_y - 35))


    # 4. INFO HEADER (Klok)
    tijd = font.render(datetime.now().strftime("%H:%M:%S"), True, (0,0,0))
    pygame.draw.rect(screen, WIT, (WIDTH-150, 20, 130, 50), border_radius=5)
    screen.blit(tijd, (WIDTH-140, 30))

    pygame.display.flip()
    ffmpeg.capture_frame()
    clock.tick(FPS)

print("Video klaar!")
del ffmpeg
pygame.quit()