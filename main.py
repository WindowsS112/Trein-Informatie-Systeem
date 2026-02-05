import pygame
from ffmpeg_helper import FFMPEG_helper
from datetime import datetime
import requests
import time
import os

# --- Config ---
WIDTH, HEIGHT = 1200, 800
FPS = 24
DURATION_SECONDS = 5
TOTAL_FRAMES = FPS * DURATION_SECONDS
LMS_COLOR = (0, 158, 132)  # Achtergrond

# --- Weer instellingen ---
LAT, LON = 52.22, 6.89  # Enschede
WEATHER_UPDATE_INTERVAL = 60  # seconden

# --- Init pygame ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Fonts voor de informatie
font = pygame.font.SysFont("Arial", 30)
large_font = pygame.font.SysFont("Arial", 50, bold=True)
ffmpeg = FFMPEG_helper()

# --- INSTELLINGEN VOOR HET TREIN SYSTEEM ---
stations = ["Amsterdam", "Utrecht", "Den Bosch", "Eindhoven"]
huidige_snelheid = 125 # km/u
volgende_stop = "Utrecht Centraal"

for frame_count in range(TOTAL_FRAMES):
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            running = False

    # --- Update weer (elke minuut) ---
    if time.time() - last_weather_update > WEATHER_UPDATE_INTERVAL:
        try:
            weather_data = get_weather(LAT, LON)
            last_weather_update = time.time()
        except Exception as e:
            print("Weer update mislukt:", e)

    # --- Scherm logica ---
    if screen_mode == "train":
        progress = frame_count / TOTAL_FRAMES
        screen.fill(LMS_COLOR)

    # 3. INTERFACE ELEMENTEN (HET 'NEXT STOP' SCHERM)
    # Teken de rails
    pygame.draw.rect(screen, (80, 80, 80), (0, 500, WIDTH, 20))
    
    # Teken de trein (tijdelijk een rood blok totdat je je pixel art inlaadt)
    # De trein beweegt van links naar rechts over de breedte van het scherm
    train_width = 250
    train_x = (WIDTH - train_width) * progress
    pygame.draw.rect(screen, (220, 20, 60), (train_x, 420, train_width, 80), border_radius=10)
    
    # Teken tekst informatie
    stop_label = large_font.render(f"Volgende stop: {volgende_stop}", True, (255, 255, 255))
    speed_label = font.render(f"Huidige snelheid: {huidige_snelheid} km/u", True, (255, 255, 255))
    eta_label = font.render(f"ETA: 4 min", True, (255, 255, 255))
    
    screen.blit(stop_label, (50, 50))
    screen.blit(speed_label, (50, 110))
    screen.blit(eta_label, (50, 150))

        # --- Voortgangsbalk ---
        bar_width = 400
        bar_x = WIDTH // 2 - bar_width // 2
        bar_y = 700
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, 10))
        pygame.draw.circle(screen, (255, 215, 0), (int(bar_x + (bar_width * progress)), bar_y + 5), 15)

        # --- Digitale klok rechtsboven ---
        current_time = datetime.now().strftime("%H:%M:%S")
        clock_label = font.render(current_time, True, (0, 0, 0))
        padding = 10
        bg_rect = pygame.Rect(WIDTH - clock_label.get_width() - padding*2 - 20, 20,
                              clock_label.get_width() + padding*2,
                              clock_label.get_height() + padding*2)
        pygame.draw.rect(screen, (255, 255, 255), bg_rect, border_radius=6)
        screen.blit(clock_label, (bg_rect.x + padding, bg_rect.y + padding))

        # --- Weer links onder ---
        temp = weather_data["temperature"]
        code = weather_data["weathercode"]
        weather_text = weather_description(code)
        weather_label = font.render(f"Weer: {weather_text} ({temp}°C)", True, (255, 255, 255))
        screen.blit(weather_label, (50, HEIGHT - 50))


        # --- Station aankomst check ---
        if progress >= 1.0:
            if huidig_station_index >= len(stations) - 2:
                running = False  # laatste station bereikt, afsluiten
            else:
                screen_mode = "route"
                route_start_time = time.time()
                frame_count = 0  # reset voor animatie

    elif screen_mode == "route":
        screen.fill((50, 50, 50))  # donker scherm voor route

        # Teken lijn voor de route
        margin = 100
        line_y = HEIGHT // 2
        pygame.draw.line(screen, (255, 255, 255), (margin, line_y), (WIDTH - margin, line_y), 5)

        # Teken stations afwisselend boven/onder
        n = len(stations)
        spacing = (WIDTH - 2*margin) / (n - 1)
        for i, station in enumerate(stations):
            x = margin + i * spacing
            # kleur van label
            color = (255, 215, 0) if i == huidig_station_index else (255, 255, 255)
            pygame.draw.circle(screen, (255, 255, 255), (int(x), line_y), 15)

            # Afwisselend boven/onder
            y = line_y - 60 if i % 2 == 0 else line_y + 15
            label = font.render(station, True, color)
            screen.blit(label, (int(x - label.get_width()/2), y))

        # --- Geanimeerde trein positie tussen huidige en volgende station ---
        if huidig_station_index < len(stations) - 1:
            progress_route = frame_count / TOTAL_FRAMES
            start_x = margin + huidig_station_index * spacing
            end_x = margin + (huidig_station_index + 1) * spacing
            train_x = start_x + (end_x - start_x) * progress_route
        else:
            train_x = margin + huidig_station_index * spacing  # laatste station

        pygame.draw.circle(screen, (255, 215, 0), (int(train_x), line_y), 10)

        # Digitale klok rechtsboven
        current_time = datetime.now().strftime("%H:%M:%S")
        clock_label = font.render(current_time, True, (0, 0, 0))
        padding = 10
        bg_rect = pygame.Rect(WIDTH - clock_label.get_width() - padding*2 - 20, 20,
                              clock_label.get_width() + padding*2,
                              clock_label.get_height() + padding*2)
        pygame.draw.rect(screen, (255, 255, 255), bg_rect, border_radius=6)
        screen.blit(clock_label, (bg_rect.x + padding, bg_rect.y + padding))

        # Weer links onder blijft
        temp = weather_data["temperature"]
        code = weather_data["weathercode"]
        weather_text = weather_description(code)
        weather_label = font.render(f"Weer: {weather_text} ({temp}°C)", True, (255, 255, 255))
        screen.blit(weather_label, (50, HEIGHT - 50))


        # Na korte tijd terug naar trein animatie en update stations
        if time.time() - route_start_time > route_display_time:
            screen_mode = "train"
            frame_count = 0
            if huidig_station_index < len(stations) - 2:
                huidig_station_index += 1
                huidig_station = stations[huidig_station_index]
                volgende_stop = stations[huidig_station_index + 1]

    # --- Render & capture ---
    pygame.display.flip()
    ffmpeg.capture_frame()
    clock.tick(FPS)
    frame_count += 1

# --- Afsluiten ---
del ffmpeg
pygame.quit()
