import os
import pygame

# Version 3.1.11
# Initialize fonts
pygame.font.init()

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SPROTO_IMAGE_PATH = os.path.join(BASE_DIR, "Racers")
SELECTION_BG_PATH = os.path.join(BASE_DIR, "BG", "BG1.png")
RACE_BG_PATHS = {
    "single_options": [
        os.path.join(BASE_DIR, "BG", "BG2.png"),
        os.path.join(BASE_DIR, "BG", "BG3.png"),
        os.path.join(BASE_DIR, "BG", "BG4.png"),
        os.path.join(BASE_DIR, "BG", "BG5.png"),
        os.path.join(BASE_DIR, "BG", "BG6.png"),
        os.path.join(BASE_DIR, "BG", "BG7.png")
    ],
    "tournament": [
        os.path.join(BASE_DIR, "BG", "BG2.png"),  # Race 1
        os.path.join(BASE_DIR, "BG", "BG3.png"),  # Race 2
        os.path.join(BASE_DIR, "BG", "BG4.png"),  # Race 3
        os.path.join(BASE_DIR, "BG", "BG5.png"),  # Race 4
        os.path.join(BASE_DIR, "BG", "BG6.png"),  # Race 5
        os.path.join(BASE_DIR, "BG", "BG7.png"),  # Race 6
        os.path.join(BASE_DIR, "BG", "BG8.png")   # Race 7
    ],
    "results": os.path.join(BASE_DIR, "BG", "BGRESULT.png")
}
SELECTION_MUSIC_PATH = os.path.join(BASE_DIR, "Music", "character.mp3")
RACE_MUSIC_PATH = os.path.join(BASE_DIR, "Music", "ocean.mp3")
TROPHY_PATH = os.path.join(BASE_DIR, "Racers", "trophy.png")
LOG_PATH = os.path.join(BASE_DIR, "sproto_race.log")

# Screen settings
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GRAY = (200, 200, 200)
BLUE_BUTTON = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
GREEN = (0, 255, 0)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
BRONZE = (205, 127, 50)

# Fonts
font = pygame.font.SysFont("arial", 30)
small_font = pygame.font.SysFont("arial", 20)
large_font = pygame.font.SysFont("arial", 40)
place_font = pygame.font.SysFont("arial", 24)
selection_font = pygame.font.SysFont("arial", 24)
race_button_font = pygame.font.SysFont("arial", 18)

# Sproto names and image filenames
sproto_names = [
    "Yannix", "Yo-Yo", "GB", "FHD", "More Light",
    "Vamp", "Jahon", "ReD", "VMU", "Alpha",
    "Dumpstar", "KatieCans", "Turbo", "Jovial", "Speed Demon",
    "Rumble Pak", "Leviosa", "Obama", "Vince", "BPS",
    "Apache", "OG OBAMA", "Oggo", "BigSwole", "GPM", "YXJI", "Snoo"
]
image_filenames = [f"racer{i}.jpg" for i in range(1, 14)] + [
    "racer14.png", "racer15.jpg", "racer16.jpg", "racer17.jpg",
    "racer18.jpg", "racer19.jpg", "racer20.jpg",
    "racer21.png", "racer22.png", "racer23.jpg", "racer24.jpg", "racer25.jpg", "racer26.jpg", "racer27.jpg"
]

# Game settings
RACE_DISTANCE = 1500
RACE_DURATION = 60
MAX_SPROTOS = 5
SPEED_RANGE = (80, 120)
MARQUEE_TEXT = "Sprotos go fast. Race to the finish!"