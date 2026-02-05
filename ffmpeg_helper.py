import pygame
import subprocess


class FFMPEG_helper():
    """
    # REQUIREMENT: INSTALL FFMPEG
    # macos: brew install ffmpeg
    # manjaro: sudo pacman -S ffmpeg

    usage:
    pygame.init() <-- must be first

    ffmpeg = FFMPEG_helper()

    while true:
        ... do game stuff
        ffmpeg.capture_frame(screen)

    del ffmpeg
    """

    process = None

    def __init__(self, output_name="output") -> None:
        """ This spawns ffmpeg as a subprocess
        Args:
            output_name (str, optional): The name of the .mp4 output file.
        """
        screen = pygame.display.get_surface()
        if not screen:
            raise RuntimeError("You must initialize pygame first")
        
        width, height = screen.get_size()
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",                      # overwrite output
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-pix_fmt", "rgb24",
            "-s", f"{width}x{height}",
            "-r", str(24),                  # 24 fps
            "-i", "-",                 # stdin
            "-an",                     # no audio
            "-vcodec", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            output_name+".mp4"
        ]

        self.process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        
    def capture_frame(self):
        """ pygame.display.flip() # <-- this renders to the screen run this command after rendering
        """
        screen = pygame.display.get_surface()
        if screen and self.process and self.process.stdin:
            frame_data = pygame.image.tobytes(screen, 'RGB')
            self.process.stdin.write(frame_data)

    def __del__(self):
        if self.process and self.process.stdin:
            self.process.stdin.close() # We have to close the subprocess
            self.process.wait()
