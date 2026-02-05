import pygame
from datetime import datetime


class Trein:
    def __init__(self, x, y):
        # --- Visuele Eigenschappen ---
        self.x = x
        self.y = y
        self.width = 250
        self.height = 80
        self.aankomst_tijd = "--:--"
        self.minuten_resterend = 0
        self.percentage_onderweg = 0.0 # Getal tussen 0.0 en 1.0
        self.vorige_stop_tijd = None
        self.volgende_stop_tijd = None
        
        # Probeer een plaatje te laden, anders gebruiken we een blok
        try:
            # Let op: pad kan verschillen afhankelijk van waar je het script start
            original_img = pygame.image.load("assets/trein.png").convert_alpha()
            self.image = pygame.transform.scale(original_img, (self.width, self.height))
        except FileNotFoundError:
            self.image = None # Geen plaatje gevonden, we tekenen een blok
        
        # --- Data Eigenschappen (Start leeg) ---
        self.herkomst = "Laden..."
        self.bestemming = "Laden..."  # <--- NIEUW
        self.spoor = "?"
        self.vertraging = None
        self.route_lijst = []       # Lijst met namen: ["Enschede", "Hengelo", ...]
        self.huidige_stop_index = 0 # Waar zijn we nu?

    def update_data(self, api_data, huidig_station_naam="Onbekend"):
        """Vul de trein-info met data uit de NS API"""
        if api_data:
            self.herkomst = api_data.get('origin', 'Onbekend')
            self.spoor = api_data.get('actualTrack', 'Enschede Kennispark')
            ruwe_tijd = api_data.get('actualDateTime')

            if ruwe_tijd:
                # PARSEN: We maken er een echt tijd-object van
                try:
                    # fromisoformat snapt de NS tijdnotatie
                    aankomst_obj = datetime.fromisoformat(ruwe_tijd)
                    
                    # A. Voor de klokweergave (HH:MM)
                    self.aankomst_tijd = aankomst_obj.strftime("%H:%M")
                    
                    # B. Voor de countdown (minuten resterend)
                    # We moeten wel zorgen dat 'nu' ook een tijdzone heeft, 
                    # of we strippen de tijdzone van beide af (makkelijker).
                    nu = datetime.now().replace(tzinfo=None)
                    aankomst_no_tz = aankomst_obj.replace(tzinfo=None)
                    
                    verschil = aankomst_no_tz - nu
                    # Zet om naar minuten (total_seconds / 60)
                    self.minuten_resterend = int(verschil.total_seconds() / 60)
                    
                    if self.minuten_resterend < 0:
                        self.minuten_resterend = 0 # Niet "-1 min" tonen
                        
                except ValueError:
                    self.aankomst_tijd = "??"

    def teken(self, screen, progress):
        """Bereken positie en teken de trein"""
        # 1. Update positie op basis van progressie (0.0 tot 1.0)
        # We bewegen van links (0) naar rechts (schermbreedte - treinbreedte)
        scherm_breedte = screen.get_width()
        max_x = scherm_breedte - self.width
        self.x = max_x * progress

        # 2. Teken de trein
        if self.image:
            screen.blit(self.image, (self.x, self.y))
        else:
            # Fallback: Rood blok met afgeronde hoeken
            pygame.draw.rect(screen, (220, 20, 60), (self.x, self.y, self.width, self.height), border_radius=10)
            
            # Teken ramen erin voor het effect
            window_color = (200, 230, 255)
            for i in range(3):
                win_x = self.x + 20 + (i * 70)
                pygame.draw.rect(screen, window_color, (win_x, self.y + 10, 50, 30))
