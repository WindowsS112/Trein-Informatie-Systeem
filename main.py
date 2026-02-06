import pygame
from ffmpeg_helper import FFMPEG_helper
from datetime import datetime
from PIL import Image
import requests
import time
import os
import random
import math


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

raw_bg = pygame.image.load("Pictures/border.png").convert_alpha()

# 2. Bepaal hoe groot je de klok wilt hebben op het scherm.
# 666x256 is erg groot. Laten we het schalen naar bijvoorbeeld 250 pixels breed.
# De hoogte rekenen we uit zodat de verhouding klopt.
target_width = 250
aspect_ratio = raw_bg.get_height() / raw_bg.get_width()
target_height = int(target_width * aspect_ratio)

# 3. Maak de definitieve achtergrond
# smoothscale zorgt dat het plaatje mooi scherp blijft bij het verkleinen
clock_bg = pygame.transform.smoothscale(raw_bg, (target_width, target_height))

# Fonts instellen (zorg dat ze passen in de nieuwe target_height)
time_font = pygame.font.SysFont("menlo, consolas", 35, bold=True)


# --- INSTELLINGEN VOOR HET TREIN SYSTEEM ---
# --- Trein instellingen ---
stations = ["Enschede", "Hengelo", "Almelo", "Deventer", "Apeldoorn", "Amersfoort Centraal", "Utrecht Centraal"]
huidige_snelheid = 125  # km/u
huidig_station_index = 0
huidig_station = stations[huidig_station_index]
volgende_stop = stations[huidig_station_index + 1]

# --- Scherm status ---
screen_mode = "train"
route_display_time = 7  # seconden
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


def draw_texture_overlay(surface, width, height, type="dots"):
    """
    Tekent een subtiel patroon over een surface heen voor een technische look.
    type: "dots" (stippen) of "lines" (scanlines)
    """
    texture_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    
    color = (0, 0, 0, 15) # Erg subtiel zwart (alpha 15 van 255)
    
    if type == "lines":
        # Scanline effect (zoals oude monitors of stationsborden)
        for y in range(0, height, 3): # Elke 3 pixels een lijn
            pygame.draw.line(texture_surf, color, (0, y), (width, y))
            
    elif type == "dots":
        # Modern 'Tech' stippenraster
        step = 6 # Afstand tussen stippen
        for y in range(0, height, step):
            for x in range(0, width, step):
                # Een stipje is 1x1 pixel groot
                texture_surf.set_at((x, y), color)
                
    # Plak de texture over de bestaande surface heen
    # 'pygame.BLEND_RGBA_MULT' zorgt dat het mooi samensmelt (optioneel, normaal blit werkt ook)
    surface.blit(texture_surf, (0, 0))


def is_raining(weathercode):
    return weathercode in {
        51, 53, 55,
        61, 63, 65,
        66, 67,
        80, 81, 82,
        95, 96, 99
    }


def map_openmeteo_to_scene(code):
    """
    Zet Open-Meteo weathercode om naar interne weather_code:
    0 = regen
    1 = sneeuw
    2 = bewolkt
    3 = zonnig
    4 = mist
    5 = nacht (optioneel, tijd-gestuurd)
    """

    # Regen
    if code in {51, 53, 55, 61, 63, 65, 80, 81, 82, 95, 96, 99}:
        return 0

    # Sneeuw
    if code in {71, 73, 75, 77, 85, 86}:
        return 1

    # Mist
    if code in {45, 48}:
        return 4

    # Bewolkt
    if code in {2, 3}:
        return 2

    # Helder / zonnig
    if code in {0, 1}:
        return 3

    # Fallback
    return 2


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


# --- Real weather switch ---


HARDCODED_WEATHER_SEQUENCE = [0, 1, 2, 3, 4, 5]

HARDCODED_WEATHER_TEMPS = {
    0: 8,    # Regen
    1: -2,   # Sneeuw
    2: 6,   # Bewolkt
    3: 22,   # Zonnig
    4: 6,    # Mist
    5: 4    # Nacht
}

HARDCODED_WEATHER_TEXT = {
    0: "Regen",
    1: "Sneeuw",
    2: "Bewolkt",
    3: "Zonnig",
    4: "Mist",
    5: "Nacht"
}

hardcoded_weather_index = 0

use_real_weather = True


# --- Init weer ---
weather_data = get_weather(LAT, LON)
last_weather_update = time.time()

weather_code = map_openmeteo_to_scene(weather_data["weathercode"])
display_temperature = weather_data["temperature"]

display_weather_text = weather_description(weather_data["weathercode"])


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

train_width = 175
train_height = 56
GIF_PATH2 = os.path.join("Pictures", "train.gif")
TRAIN_SIZE2 = (train_width, train_height)

train_frames2 = load_gif(GIF_PATH2, scale=TRAIN_SIZE2)
train_frame_count2 = len(train_frames2)


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

scroll_x = 0
SCROLL_SPEED = 8

track_speed = 8  # pixels per frame

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
        pygame.draw.circle(screen, (255, 255, 200), (moon_x, moon_y), moon_radius)
        glow_radius = 100
        moon_glow = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(moon_glow, (255, 255, 200, 60), (glow_radius, glow_radius), glow_radius)
        screen.blit(moon_glow, (moon_x - glow_radius, moon_y - glow_radius))

        for star in stars:
            x, y, base_radius = star
            radius = base_radius + random.choice([0, 0, 1])
            pygame.draw.circle(screen, (255, 255, 150), (x, y), radius)

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

            # ⬇️ KOPPELING TUSSEN API EN ACHTERGROND
            api_code = weather_data["weathercode"]
            weather_code = map_openmeteo_to_scene(api_code)

        except Exception as e:
            print("Weer update mislukt:", e)

    if screen_mode == "train":
        # --- TIMING ---
        START_WAIT_FRAMES = FPS * 1  # 1 second wait at start
        END_WAIT_FRAMES = FPS * 1    # 1 second wait at end
        MOVE_FRAMES = TOTAL_FRAMES   # frames where train moves

        # --- ANIMATION STATES ---
        if frame_count < START_WAIT_FRAMES:
            progress = 0.0  # waiting at start
            in_end_pause = False
        elif frame_count < START_WAIT_FRAMES + MOVE_FRAMES:
            # train moving
            progress = (frame_count - START_WAIT_FRAMES) / MOVE_FRAMES
            in_end_pause = False
        else:
            # train reached end, pause
            progress = 1.0
            in_end_pause = True

        # --- ACHTERGROND EN ELEMENTEN ---
        set_background(weather_code)
        draw_rails(track_tiles)
        screen.blit(station_image, (left_station_x, station_y))
        screen.blit(station_image, (right_station_x, station_y))
        draw_train(progress)

        # --- Tekst en interface ---
        shadow = 2
        stop_label_shadow = large_font.render(f"Volgende stop: {volgende_stop}", True, (0, 0, 0, 0.5))
        current_station_label_shadow = large_font.render(f"Huidig station: {huidig_station}", True, (0, 0, 0, 0.5))
        speed_label_shadow = font.render(f"Huidige snelheid: {huidige_snelheid} km/u", True, (0, 0, 0.5))
        screen.blit(current_station_label_shadow, (50 - shadow, 40 - shadow))
        screen.blit(stop_label_shadow, (50 - shadow, 100 - shadow))
        screen.blit(speed_label_shadow, (50 - shadow, 160 - shadow))
        screen.blit(current_station_label_shadow, (50 + shadow, 40 + shadow))
        screen.blit(stop_label_shadow, (50 + shadow, 100 + shadow))
        screen.blit(speed_label_shadow, (50 + shadow, 160 + shadow))

        stop_label = large_font.render(f"Volgende stop: {volgende_stop}", True, (255, 255, 255))
        current_station_label = large_font.render(f"Huidig station: {huidig_station}", True, (255, 255, 255))
        speed_label = font.render(f"Huidige snelheid: {huidige_snelheid} km/u", True, (255, 255, 255))
        screen.blit(current_station_label, (50, 40))
        screen.blit(stop_label, (50, 100))
        screen.blit(speed_label, (50, 160))

        # --- IN JE GAME LOOP ---
        now = datetime.now()

        # 1. Tijd string maken en renderen
        time_str = now.strftime("%H:%M:%S")
        time_surf = time_font.render(time_str, True, (255, 255, 255))

        # 2. Positie van de achtergrond bepalen (Rechtsboven)
        bg_rect = clock_bg.get_rect()
        bg_rect.topright = (WIDTH - 20, 20)

        # 3. Tekenen
        # A. Eerst de achtergrond (de PNG)
        screen.blit(clock_bg, bg_rect)

        # B. Tijd precies in het midden van de PNG centreren
        # Omdat de datum weg is, hoeven we niet meer te schuiven (geen y += 5 meer nodig)
        time_rect = time_surf.get_rect(center=bg_rect.center)
        screen.blit(time_surf, time_rect)

        # --- Weer info ---
        temp = weather_data["temperature"]
        code = weather_data["weathercode"]
        weather_text = weather_description(code)
        weather_label = font.render(f"Weer: {weather_text} ({temp}°C)", True, (255, 255, 255))
        screen.blit(weather_label, (50, HEIGHT - 50))

        # --- STATION AANKOMST ---
        if in_end_pause and frame_count >= START_WAIT_FRAMES + MOVE_FRAMES + END_WAIT_FRAMES:
            # Na 1 seconde wachten op het einde, switch naar route
            if use_real_weather:
                display_temperature = weather_data["temperature"]
                display_weather_text = weather_description(weather_data["weathercode"])
                use_real_weather = False
                hardcoded_weather_index = 0
            else:
                hardcoded_weather_index = (hardcoded_weather_index + 1) % len(HARDCODED_WEATHER_SEQUENCE)

            weather_code = HARDCODED_WEATHER_SEQUENCE[hardcoded_weather_index]
            display_temperature = HARDCODED_WEATHER_TEMPS[weather_code]
            display_weather_text = HARDCODED_WEATHER_TEXT[weather_code]

            if huidig_station_index >= len(stations) - 2:
                running = False  # laatste station bereikt
            else:
                screen_mode = "route"
                route_start_time = time.time()
                frame_count = 0

    elif screen_mode == "route":
        set_background(weather_code)

        # Teken lijn voor de route
        margin = 100
        line_y = TRAIN_HEIGHT

        # Teken bewegende stations
        scroll_x -= SCROLL_SPEED
        n = len(stations)
        spacing = 250
        for i, station in enumerate(stations):
            x = margin + 2 * spacing + i * spacing + scroll_x

            if x < -50 or x > WIDTH + 50:
                continue

            color = (255, 215, 0) if i == huidig_station_index else (255, 255, 255)
            pygame.draw.circle(screen, (255, 255, 255), (int(x), line_y), 20)
            pygame.draw.circle(screen, (0, 0, 0), (int(x), line_y), 15)

            # Afwisselend boven/onder
            y = line_y - 200 if i % 2 == 0 else line_y - 125
            label = font.render(station, True, color)
            screen.blit(label, (int(x - label.get_width() / 2), y))

        # Teken track
        for i in range(len(track_tiles)):
            track_tiles[i] -= track_speed

            # als tile volledig uit beeld is rechts opnieuw plaatsen
            if track_tiles[i] <= -track_width:
                track_tiles[i] = max(track_tiles) + track_width
        draw_rails(track_tiles)

        # --- Geanimeerde trein positie tussen huidige en volgende station ---
        if huidig_station_index < len(stations) - 1:
            progress_route = frame_count / TOTAL_FRAMES
            start_x = margin + 2 * spacing + huidig_station_index * spacing + scroll_x
            end_x = margin + 2 * spacing - 50 + (huidig_station_index + 1) * spacing + scroll_x
            train_x = start_x + (end_x - start_x) * progress_route
        else:
            train_x = margin + huidig_station_index * spacing  # laatste station

        gif_frame_index = int((frame_count / FPS) * gif_fps) % train_frame_count2
        train_image = train_frames2[gif_frame_index]
        screen.blit(train_image, (train_x - train_width, line_y - train_height))

        dutch_days = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"]
        dutch_months = ["jan", "feb", "mrt", "apr", "mei", "jun", "jul", "aug", "sep", "okt", "nov", "dec"]

        now = datetime.now()

        # 1. Tijd string maken en renderen
        time_str = now.strftime("%H:%M:%S")
        time_surf = time_font.render(time_str, True, (255, 255, 255))

        # 2. Positie van de achtergrond bepalen (Rechtsboven)
        bg_rect = clock_bg.get_rect()
        bg_rect.topright = (WIDTH - 20, 20)

        # 3. Tekenen
        # A. Eerst de achtergrond (de PNG)
        screen.blit(clock_bg, bg_rect)

        # B. Tijd precies in het midden van de PNG centreren
        # Omdat de datum weg is, hoeven we niet meer te schuiven (geen y += 5 meer nodig)
        time_rect = time_surf.get_rect(center=bg_rect.center)
        screen.blit(time_surf, time_rect)

        if time.time() - route_start_time > route_display_time:
            if not use_real_weather:
                hardcoded_weather_index = (hardcoded_weather_index + 1) % len(HARDCODED_WEATHER_SEQUENCE)
                weather_code = HARDCODED_WEATHER_SEQUENCE[hardcoded_weather_index]

        # Na korte tijd terug naar trein animatie en update stations
        if time.time() - route_start_time > route_display_time:
            if not use_real_weather:
                hardcoded_weather_index = (hardcoded_weather_index + 1) % len(HARDCODED_WEATHER_SEQUENCE)
                weather_code = HARDCODED_WEATHER_SEQUENCE[hardcoded_weather_index]
                display_temperature = HARDCODED_WEATHER_TEMPS[weather_code]
                display_weather_text = HARDCODED_WEATHER_TEXT[weather_code]

            screen_mode = "train"
            frame_count = 0
            scroll_x = 0
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
        # Weer links onder blijft
        weather_text = display_weather_text
        temp = display_temperature
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
