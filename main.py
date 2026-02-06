import pygame
from ffmpeg_helper import FFMPEG_helper
from datetime import datetime
from PIL import Image
import requests
import time
import os
import random
import math

# elke keer wanneer we van scherm switchen moet een counter 1 omhoog, zodat bij elke wisseling het weer verandert. Van regen naar sneeuw, van sneeuw naar zonnig enz. met telkens 10 seconden pauze tussen de wisseling.
weather_code = 0

# --- Config ---
WIDTH, HEIGHT = 1200, 800
TRAIN_HEIGHT = 600
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
# --- Trein instellingen ---
stations = ["Enschede", "Hengelo", "Almelo", "Deventer", "Apeldoorn", "Amersfoort Centraal", "Utrecht Centraal"]
huidige_snelheid = 125  # km/u
huidig_station_index = 0
huidig_station = stations[huidig_station_index]
volgende_stop = stations[huidig_station_index + 1]

# --- Scherm status ---
screen_mode = "train"
route_display_time = 3  # seconden
route_start_time = None


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


# --- Functie om weathercode om te zetten naar tekst ---
def weather_description(code):
    mapping = {
        0: "Helder",                 # Clear sky
        1: "Grotendeels zonnig",     # Mainly clear
        2: "Deels bewolkt",          # Partly cloudy
        3: "Bewolkt",                # Overcast
        45: "Mist",                  # Fog
        48: "Damp",                  # Depositing rime fog
        51: "Lichte motregen",       # Drizzle light
        53: "Motregen",              # Drizzle moderate
        55: "Zware motregen",        # Drizzle dense
        56: "IJzige motregen",       # Freezing drizzle light
        57: "Zware ijzige motregen", # Freezing drizzle dense
        61: "Lichte regen",          # Rain light
        63: "Regen",                 # Rain moderate
        65: "Zware regen",           # Rain heavy
        66: "IJzige regen",          # Freezing rain light
        67: "Zware ijzige regen",    # Freezing rain heavy
        71: "Lichte sneeuw",         # Snow fall slight
        73: "Sneeuw",                # Snow fall moderate
        75: "Zware sneeuw",          # Snow fall heavy
        77: "Sneeuwkorrels",         # Snow grains
        80: "Regenbuien",            # Rain showers slight
        81: "Sterke regenbuien",     # Rain showers moderate
        82: "Zware regenbuien",      # Rain showers violent
        85: "Sneeuwbuien",           # Snow showers slight
        86: "Zware sneeuwbuien",     # Snow showers heavy
        95: "Onweersbuien",          # Thunderstorm
        96: "Onweer met lichte hagel", # Thunderstorm with slight hail
        99: "Onweer met zware hagel"   # Thunderstorm with heavy hail
    }
    return mapping.get(code, "Onbekend")


# --- Init weer ---
weather_data = get_weather(LAT, LON)
last_weather_update = time.time()


# Train
def load_gif(path, scale=None):
    pil_gif = Image.open(path)
    frames = []

    try:
        while True:
            frame = pil_gif.convert("RGBA")

            if scale:
                frame = frame.resize(scale, Image.BICUBIC)

            pygame_frame = pygame.image.fromstring(
                frame.tobytes(), frame.size, frame.mode
            )
            frames.append(pygame_frame)

            pil_gif.seek(pil_gif.tell() + 1)
    except EOFError:
        pass

    return frames


GIF_PATH = os.path.join("Pictures", "train.gif")
TRAIN_SIZE = (250, 80)

train_frames = load_gif(GIF_PATH, scale=TRAIN_SIZE)
train_frame_count = len(train_frames)
gif_fps = 16


# Station
STATION_PATH = os.path.join("Pictures", "station.png")
station_image = pygame.image.load(STATION_PATH).convert_alpha()
station_image = pygame.transform.scale(station_image, (160, 120))

station_width = station_image.get_width() * 2
station_height = station_image.get_height() * 2

station_image = pygame.transform.scale(station_image, (station_width, station_height))

station_y = TRAIN_HEIGHT - station_height - 5
left_station_x = -20
right_station_x = WIDTH - station_width + 20

# Track
TRACK_PATH = os.path.join("Pictures", "track.png")
track_image = pygame.image.load(TRACK_PATH).convert_alpha()

track_width = track_image.get_width()
track_height = track_image.get_height()

track_y = TRAIN_HEIGHT

num_tracks = (WIDTH // track_width) + 3
track_tiles = []
for i in range(num_tracks):
    track_tiles.append(i * track_width)

track_speed = 3  # pixels per frame

# Grass
GRASS_PATH = os.path.join("Pictures", "grass.webp")
grass_image = pygame.image.load(GRASS_PATH).convert()

tile_size = 100
grass_image = pygame.transform.scale(grass_image, (tile_size, tile_size))


grass_width = grass_image.get_width()
grass_height = grass_image.get_height()


# rainy settings
RAIN_COLOR = (180, 180, 255)
NUM_RAINDROPS = 350

raindrops = []
for _ in range(NUM_RAINDROPS):
    x = random.randint(0, WIDTH)
    y = random.randint(0, HEIGHT)
    speed = random.randint(6, 14)
    length = random.randint(8, 15)
    raindrops.append([x, y, speed, length])


# snowy settings
SNOW_COLOR = (245, 245, 255)
NUM_SNOWFLAKES = 250

snowflakes = []
for _ in range(NUM_SNOWFLAKES):
    x = random.randint(0, WIDTH)
    y = random.randint(0, HEIGHT)
    speed = random.uniform(1.5, 3.5)
    drift = random.uniform(-0.5, 0.5)
    size = random.randint(2, 4)
    snowflakes.append([x, y, speed, drift, size])


# cloudy settings
NUM_CLOUDS = 10
clouds = []

for _ in range(NUM_CLOUDS):
    width = random.randint(200, 350)
    height = random.randint(100, 180)
    x = random.randint(0, WIDTH)
    y = random.randint(HEIGHT // 4, 3 * HEIGHT // 5)
    speed = random.uniform(0.5, 2.0)
    alpha = random.randint(180, 220)
    clouds.append([x, y, width, height, speed, alpha])

# misty settings
NUM_MIST_CLOUDS = 10
mist_clouds = []

for _ in range(NUM_MIST_CLOUDS):
    w = random.randint(150, 400)
    h = random.randint(80, 200)
    x = random.randint(0, WIDTH - w)
    y = random.randint(0, HEIGHT - h)
    alpha = random.randint(80, 150)
    phase = random.uniform(0, math.pi * 2)
    mist_clouds.append([x, y, w, h, alpha, phase])

# night settings
NUM_STARS = 100
stars = []
for _ in range(NUM_STARS):
    x = random.randint(0, WIDTH)
    y = random.randint(0, HEIGHT // 2)
    base_radius = random.randint(1, 2)
    stars.append([x, y, base_radius])

moon_x, moon_y = WIDTH // 3, HEIGHT // 4
moon_radius = 60


def set_background(weather_code):
    if weather_code == 0:
        screen.fill((20, 20, 40)) # rainy
    
    elif weather_code == 1:
        screen.fill((25, 30, 45)) # snowy

    elif weather_code == 2:
        screen.fill((180, 180, 180)) # cloudy

    elif weather_code == 3:
        screen.fill((135, 206, 235)) # sunny

    elif weather_code == 4:
        screen.fill((200, 200, 200)) # misty

    elif weather_code == 5:
        screen.fill((10, 10, 40)) # night

    for x in range(0, WIDTH, grass_width):
        for y in range(TRAIN_HEIGHT - 25, HEIGHT, grass_height):
            screen.blit(grass_image, (x, y))


def draw_rails(track_tiles):
    for x in track_tiles:
        screen.blit(track_image, (x, track_y))


def draw_train(progress):
    gif_frame_index = int((frame_count / FPS) * gif_fps) % train_frame_count
    train_image = train_frames[gif_frame_index]
    train_x = (WIDTH - TRAIN_SIZE[0]) * progress
    train_y = TRAIN_HEIGHT - 80
    screen.blit(train_image, (train_x, train_y))


# --- Main loop ---
frame_count = 0
running = True
while running:
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

    if screen_mode == "train":
    # --- Scherm logica ---
        progress = frame_count / TOTAL_FRAMES

        if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.quit()
            exit()

        # 1. BEREKENINGEN
        # Bereken voortgang (van 0.0 naar 1.0) op basis van het huidige frame
        progress = frame_count / TOTAL_FRAMES
        
        # 2. ACHTERGRONDEN
        set_background(weather_code)
        
        # 3. INTERFACE ELEMENTEN (HET 'NEXT STOP' SCHERM)
        # Teken de rails
        draw_rails(track_tiles)
        
        # Teken stations
        screen.blit(station_image, (left_station_x, station_y))
        screen.blit(station_image, (right_station_x, station_y))

        # Teken de trein (tijdelijk een rood blok totdat je je pixel art inlaadt)
        # De trein beweegt van links naar rechts over de breedte van het scherm
        draw_train(progress)

        # --- Tekst informatie ---
        stop_label = large_font.render(f"Volgende stop: {volgende_stop}", True, (255, 255, 255))
        current_station_label = large_font.render(f"Huidig station: {huidig_station}", True, (255, 255, 255))
        speed_label = font.render(f"Huidige snelheid: {huidige_snelheid} km/u", True, (255, 255, 255))

        screen.blit(current_station_label, (50, 40))
        screen.blit(stop_label, (50, 100))
        screen.blit(speed_label, (50, 160))


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
            weather_code += 1
            if weather_code > 5:
                weather_code = 0
            if huidig_station_index >= len(stations) - 2:
                running = False  # laatste station bereikt, afsluiten
            else:
                screen_mode = "route"
                route_start_time = time.time()
                frame_count = 0  # reset voor animatie

    elif screen_mode == "route":
        set_background(weather_code)

        for i in range(len(track_tiles)):
            track_tiles[i] -= track_speed

            # als tile volledig uit beeld is rechts opnieuw plaatsen
            if track_tiles[i] <= -track_width:
                track_tiles[i] = max(track_tiles) + track_width
        draw_rails(track_tiles)

        # Teken lijn voor de route
        margin = 100
        line_y = TRAIN_HEIGHT
        # pygame.draw.line(screen, (255, 255, 255), (margin, line_y), (WIDTH - margin, line_y), 5)

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

        # Na korte tijd terug naar trein animatie en update stations
        if time.time() - route_start_time > route_display_time:
            weather_code += 1
            if weather_code > 5:
                weather_code = 0
            screen_mode = "train"
            frame_count = 0
            if huidig_station_index < len(stations) - 2:
                huidig_station_index += 1
                huidig_station = stations[huidig_station_index]
                volgende_stop = stations[huidig_station_index + 1]

    # rainy
    if weather_code == 0:
        for drop in raindrops:
            drop[1] += drop[2]

            pygame.draw.line(
                screen,
                RAIN_COLOR,
                (drop[0], drop[1]),
                (drop[0], drop[1] + drop[3]),
                1
            )

            if drop[1] > HEIGHT:
                drop[1] = random.randint(-20, 0)
                drop[0] = random.randint(0, WIDTH)

    # snowy
    elif weather_code == 1:
        for flake in snowflakes:
            flake[1] += flake[2]
            flake[0] += flake[3]

            pygame.draw.circle(
                screen,
                SNOW_COLOR,
                (int(flake[0]), int(flake[1])),
                flake[4]
            )

            if flake[1] > HEIGHT:
                flake[1] = random.randint(-20, 0)
                flake[0] = random.randint(0, WIDTH)
    
    # cloudy
    elif weather_code == 2:
        for cloud in clouds:
            x, y, w, h, speed, alpha = cloud

            cloud[0] -= speed

            cloud_surface = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.ellipse(cloud_surface, (160, 160, 160, alpha), (0, 0, w, h))
            screen.blit(cloud_surface, (x, y))

            if cloud[0] + w < 0:
                cloud[0] = WIDTH + random.randint(10, 100)
                cloud[1] = random.randint(0, HEIGHT // 2 - h)
                cloud[2] = random.randint(200, 350)
                cloud[3] = random.randint(100, 180)
                cloud[4] = random.uniform(0.2, 1.0)
                cloud[5] = random.randint(180, 220)
    
    # sunny
    elif weather_code == 3:
        glow_radius = 150
        glow_surface = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surface, (255, 223, 0, 60), (glow_radius, glow_radius), glow_radius)
        screen.blit(glow_surface, (WIDTH//2 - glow_radius, HEIGHT//4 - glow_radius))

        sun_radius = 80
        sun_x, sun_y = WIDTH // 2, HEIGHT // 4
        pygame.draw.circle(screen, (255, 223, 0), (sun_x, sun_y), sun_radius)

        shine_radius = 30
        pygame.draw.circle(screen, (255, 255, 180, 100), (sun_x - 20, sun_y - 20), shine_radius)

        cloud_width, cloud_height = 200, 100
        cloud_x, cloud_y = WIDTH - 200, 150
        pygame.draw.ellipse(screen, (255, 255, 255), (cloud_x, cloud_y, cloud_width, cloud_height))

    # misty
    elif weather_code == 4:
        for cloud in mist_clouds:
            x, y, w, h, alpha, phase = cloud

            float_offset = math.sin(pygame.time.get_ticks()/2000 + phase) * 5
            mist_surface = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.ellipse(mist_surface, (150, 150, 150, alpha), (0, 0, w, h))
            screen.blit(mist_surface, (x, y + float_offset))
            
            cloud[2] += 1
            cloud[3] += 0.5

    # night
    elif weather_code == 5:
        pygame.draw.circle(screen, (255, 255, 200), (moon_x, moon_y), moon_radius)
        glow_radius = 100
        moon_glow = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(moon_glow, (255, 255, 200, 60), (glow_radius, glow_radius), glow_radius)
        screen.blit(moon_glow, (moon_x - glow_radius, moon_y - glow_radius))

        for star in stars:
            x, y, base_radius = star
            radius = base_radius + random.choice([0, 0, 1])
            pygame.draw.circle(screen, (255, 255, 150), (x, y), radius)
                
        # Weer links onder blijft
        temp = weather_data["temperature"]
        code = weather_data["weathercode"]
        weather_text = weather_description(code)
        weather_label = font.render(f"Weer: {weather_text} ({temp}°C)", True, (255, 255, 255))
        screen.blit(weather_label, (50, HEIGHT - 50))


    # --- Render & capture ---
    pygame.display.flip()
    ffmpeg.capture_frame()
    clock.tick(FPS)
    frame_count += 1

# --- Afsluiten ---
del ffmpeg
pygame.quit()
