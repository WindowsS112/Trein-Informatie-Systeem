import pygame
from ffmpeg_helper import FFMPEG_helper
from datetime import datetime
import requests
import time

# --- Config ---
WIDTH, HEIGHT = 1200, 800
FPS = 24
DURATION_SECONDS = 5
TOTAL_FRAMES = FPS * DURATION_SECONDS
LMS_COLOR = (0, 158, 132)  # Achtergrond
ETA_TOTAAL_SECONDEN = 4 * 60

# --- Weer instellingen ---
LAT, LON = 52.22, 6.89  # Enschede
WEATHER_UPDATE_INTERVAL = 60  # seconden

# --- Init pygame ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 30)
large_font = pygame.font.SysFont("Arial", 50, bold=True)
ffmpeg = FFMPEG_helper()

# --- Trein instellingen ---
stations = ["Enschede", "Hengelo", "Almelo", "Deventer", "Apeldoorn", "Amersfoort Centraal", "Utrecht Centraal"]
huidige_snelheid = 125  # km/u
huidig_station_index = 0
huidig_station = stations[huidig_station_index]
volgende_stop = stations[huidig_station_index + 1]

# --- Weer functies ---
def get_weather(lat, lon):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&current_weather=true"
    )
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return response.json()["current_weather"]

def is_raining(weathercode):
    return weathercode in (
        51, 53, 55,
        61, 63, 65,
        66, 67,
        80, 81, 82,
        95, 96, 99
    )

# --- Init weer ---
weather_data = get_weather(LAT, LON)
last_weather_update = time.time()

# --- Main loop ---
for frame_count in range(TOTAL_FRAMES):
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            exit()

    # --- Update weer (elke minuut) ---
    if time.time() - last_weather_update > WEATHER_UPDATE_INTERVAL:
        try:
            weather_data = get_weather(LAT, LON)
            last_weather_update = time.time()
        except Exception as e:
            print("Weer update mislukt:", e)

    # --- Berekeningen ---
    progress = frame_count / TOTAL_FRAMES

    # --- Achtergrond ---
    screen.fill(LMS_COLOR)

    # --- Rails ---
    pygame.draw.rect(screen, (80, 80, 80), (0, 500, WIDTH, 20))

    # --- Trein ---
    train_width = 250
    train_x = (WIDTH - train_width) * progress
    pygame.draw.rect(screen, (220, 20, 60), (train_x, 420, train_width, 80), border_radius=10)

    # --- Tekst informatie ---
    # Huidig station / Volgende stop / Snelheid / ETA
    stop_label = large_font.render(f"Volgende stop: {volgende_stop}", True, (255, 255, 255))
    current_station_label = large_font.render(f"Huidig station: {huidig_station}", True, (255, 255, 255))
    speed_label = font.render(f"Huidige snelheid: {huidige_snelheid} km/u", True, (255, 255, 255))

    resterende_seconden = int(ETA_TOTAAL_SECONDEN * (1 - progress))
    minuten = resterende_seconden // 60
    seconden = resterende_seconden % 60
    eta_label = font.render(f"ETA: {minuten}:{seconden:02d}", True, (255, 255, 255))

    screen.blit(current_station_label, (50, 40))
    screen.blit(stop_label, (50, 100))
    screen.blit(speed_label, (50, 160))
    screen.blit(eta_label, (50, 200))

    # --- Voortgangsbalk ---
    bar_width = 400
    bar_x = WIDTH // 2 - bar_width // 2
    bar_y = 700
    pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, 10))
    pygame.draw.circle(screen, (255, 215, 0), (int(bar_x + (bar_width * progress)), bar_y + 5), 15)

    # Stations bij balk
    vertrek_station = huidig_station
    bestemming_station = stations[huidig_station_index + 1] if huidig_station_index < len(stations) - 1 else ""
    vertrek_label = font.render(vertrek_station, True, (255, 255, 255))
    bestemming_label = font.render(bestemming_station, True, (255, 255, 255))
    screen.blit(vertrek_label, (bar_x - vertrek_label.get_width() - 15, bar_y - 10))
    screen.blit(bestemming_label, (bar_x + bar_width + 15, bar_y - 10))

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
    weather_text = "Regen" if is_raining(code) else "Droog"
    weather_label = font.render(f"Weer: {weather_text} ({temp}°C)", True, (255, 255, 255))
    screen.blit(weather_label, (50, HEIGHT - 50))

    # --- Station automatisch wisselen ---
    if resterende_seconden <= 0:
        if huidig_station_index < len(stations) - 2:
            huidig_station_index += 1
            huidig_station = stations[huidig_station_index]
            volgende_stop = stations[huidig_station_index + 1]
            frame_count = 0

    # --- Render & capture ---
    pygame.display.flip()
    ffmpeg.capture_frame()
    clock.tick(FPS)

del ffmpeg
pygame.quit()
