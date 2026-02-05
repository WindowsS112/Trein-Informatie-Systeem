import pygame
from ffmpeg_helper import FFMPEG_helper
from datetime import datetime
import os


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

# Track
TRACK_PATH = os.path.join("Pictures", "track.png")
track_image = pygame.image.load(TRACK_PATH).convert_alpha()

track_width = track_image.get_width()
track_height = track_image.get_height()

track_y = 500

num_tracks = (WIDTH // track_width) + 3
track_tiles = []
for i in range(num_tracks):
    track_tiles.append(i * track_width)

track_speed = 8  # pixels per frame


for frame_count in range(TOTAL_FRAMES):
    for event in pygame.event.get():
        if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.quit()
            exit()

    # 1. BEREKENINGEN
    # Bereken voortgang (van 0.0 naar 1.0) op basis van het huidige frame
    progress = frame_count / TOTAL_FRAMES
    # for i in range(len(track_tiles)):
    #     track_tiles[i] -= track_speed

    #     # als tile volledig uit beeld is rechts opnieuw plaatsen
    #     if track_tiles[i] <= -track_width:
    #         track_tiles[i] = max(track_tiles) + track_width
    
    # 2. ACHTERGROND TEKENEN
    screen.fill(LMS_COLOR)

    # 3. INTERFACE ELEMENTEN (HET 'NEXT STOP' SCHERM)
    # Teken de rails
    for x in track_tiles:
        screen.blit(track_image, (x, track_y))
    
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

    # Render en capture
    pygame.display.flip()
    ffmpeg.capture_frame()
    clock.tick(FPS)


del ffmpeg
pygame.quit()
