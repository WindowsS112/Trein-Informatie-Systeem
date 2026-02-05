import pygame
import numpy as np
import wave
from ffmpeg_helper import FFMPEG_helper

# ---------------- CONFIG ----------------
WIDTH, HEIGHT = 1200, 800
AUDIO_FILE = "good-music-example.wav" # <-- only WAV is supported by numpy.fft. Feel free to search for other options
LMS_COLOR = (0, 158, 132)
FONT_COLOR = (219, 6, 80)
BAR_COLOR = (255, 255, 255)
CHUNK_SIZE = 1024
BAR_COUNT = 64
BAR_WIDTH = WIDTH // BAR_COUNT
FPS = 24
DURATION_SECONDS = 30 # try to keep it short 60 seconds should be the max
TOTAL_FRAMES = FPS * DURATION_SECONDS
# ---------------------------------------

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Load and play audio
pygame.mixer.init()
pygame.mixer.music.load(AUDIO_FILE)
pygame.mixer.music.play()

# Read audio file on startup
wf = wave.open(AUDIO_FILE, 'rb')

# fonts
pygame.font.init()
my_font = pygame.font.SysFont('Comic Sans MS', 150)
lms_radio_text = my_font.render('LMS radio', False, FONT_COLOR)

ffmpeg = FFMPEG_helper()


def get_fft_bars():
    data = wf.readframes(CHUNK_SIZE)
    if len(data) == 0:
        exit("invalid sound file")
    samples = np.frombuffer(data, dtype=np.int16)

    fft = np.abs(np.fft.fft(samples))[:BAR_COUNT]
    fft /= max(np.max(fft), 1.0)
    return fft


for _ in range(TOTAL_FRAMES):
    for event in pygame.event.get():
        if event.type == pygame.QUIT or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: # close on x or esc
            pygame.quit()
            exit()

    clock.tick(FPS)
    screen.fill(LMS_COLOR) # all the old pixels do not go away, This makes every pixel reset to the background color
 
    screen.blit(lms_radio_text, (300, 10)) # draw the text

    for i, value in enumerate(get_fft_bars()):

        bar_height = int(value * HEIGHT)
        x = i * BAR_WIDTH
        y = HEIGHT - bar_height

        pygame.draw.rect(
            screen,
            BAR_COLOR,
            (x, y, BAR_WIDTH - 1, bar_height)
        )

    # YOUR OWN CODE...




    pygame.display.flip() # render the screen
    ffmpeg.capture_frame()


del ffmpeg
pygame.quit()

# The audio is not exported. If we want audio, than we have to manually add this to the video later.
# In a train there would also not be any sounds so think hard and well before adding any sounds.
# Example command: ffmpeg -i input_video.mp4 -i good-music-example.wav -c:v copy -c:a aac -map 0:v:0 -map 1:a:0 output.mp4
