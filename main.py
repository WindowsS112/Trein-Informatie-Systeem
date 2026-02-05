import pygame
from ffmpeg_helper import FFMPEG_helper
from datetime import datetime
import os
import random
import math

# elke keer wanneer we van scherm switchen moet een counter 1 omhoog, zodat bij elke wisseling het weer verandert. Van regen naar sneeuw, van sneeuw naar zonnig enz. met telkens 10 seconden pauze tussen de wisseling.
weather_code = int(input("Enter the weather type you want: (0: rainy, 1: snowy, 2: cloudy, 3: sunny, 4: misty, 5: night): "))

WIDTH, HEIGHT = 1200, 800
FPS = 24
DURATION_SECONDS = 5
TOTAL_FRAMES = FPS * DURATION_SECONDS
LMS_COLOR = (0, 158, 132) # De basis achtergrondkleur

# Init pygame
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

# Station
STATION_PATH = os.path.join("Pictures", "station.png")
station_image = pygame.image.load(STATION_PATH).convert_alpha()
station_image = pygame.transform.scale(station_image, (160, 120))

station_width = station_image.get_width()
station_height = station_image.get_height()

station_y = 500 - station_height - 5
left_station_x = 20
right_station_x = WIDTH - station_width - 20


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


for frame_count in range(TOTAL_FRAMES):
    for event in pygame.event.get():
        if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.quit()
            exit()

    # 1. BEREKENINGEN
    # Bereken voortgang (van 0.0 naar 1.0) op basis van het huidige frame
    progress = frame_count / TOTAL_FRAMES
    
    # 2. ACHTERGRONDEN

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
            
    # 3. INTERFACE ELEMENTEN (HET 'NEXT STOP' SCHERM)
    # Teken de rails
    pygame.draw.rect(screen, (80, 80, 80), (0, 500, WIDTH, 20))
    
    # Teken de trein (tijdelijk een rood blok totdat je je pixel art inlaadt)
    # De trein beweegt van links naar rechts over de breedte van het scherm
    train_width = 250
    train_x = (WIDTH - train_width) * progress
    pygame.draw.rect(screen, (220, 20, 60), (train_x, 420, train_width, 80), border_radius=10)
    
    # Teken stations
    screen.blit(station_image, (left_station_x, station_y))
    screen.blit(station_image, (right_station_x, station_y))

    # Teken tekst informatie
    stop_label = large_font.render(f"Volgende stop: {volgende_stop}", True, (255, 255, 255))
    speed_label = font.render(f"Huidige snelheid: {huidige_snelheid} km/u", True, (255, 255, 255))
    eta_label = font.render(f"ETA: 4 min", True, (255, 255, 255))
    
    screen.blit(stop_label, (50, 50))
    screen.blit(speed_label, (50, 110))
    screen.blit(eta_label, (50, 150))

    # 4. VOORTGANGSINDICATOR (Kleine balk onderin)
    bar_width = 400
    pygame.draw.rect(screen, (255, 255, 255), (WIDTH//2 - bar_width//2, 700, bar_width, 10))
    pygame.draw.circle(screen, (255, 215, 0), (int(WIDTH//2 - bar_width//2 + (bar_width * progress)), 705), 15)

    # Digitale klok (rechtsboven)
    current_time = datetime.now().strftime("%H:%M:%S")
    clock_label = font.render(current_time, True, (0, 0, 0))  # zwarte tekst

    padding = 10
    bg_rect = pygame.Rect(
        WIDTH - clock_label.get_width() - padding*2 - 20,
        20,
        clock_label.get_width() + padding*2,
        clock_label.get_height() + padding*2
    )

    pygame.draw.rect(screen, (255, 255, 255), bg_rect, border_radius=6)
    screen.blit(clock_label, (bg_rect.x + padding, bg_rect.y + padding))

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
                
    # Render en capture
    pygame.display.flip()
    ffmpeg.capture_frame()
    clock.tick(FPS)


del ffmpeg
pygame.quit()
