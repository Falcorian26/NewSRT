import pygame
import os
import logging
from settings import *

# Setup logging
try:
    log_dir = os.path.dirname(LOG_PATH)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename=LOG_PATH
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(console_handler)
except (OSError, PermissionError) as e:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.error(f"Failed to setup file logging to '{LOG_PATH}': {e}. Using console logging.")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(console_handler)

def load_sproto_images():
    sproto_images = []
    fallback_image = pygame.Surface((50, 50))
    fallback_image.fill(PURPLE)
    missing_files = []

    if not os.path.exists(SPROTO_IMAGE_PATH):
        logging.error(f"Directory '{SPROTO_IMAGE_PATH}' does not exist. Using fallback images.")
        return [fallback_image] * len(sproto_names)
    
    logging.info(f"Files in {SPROTO_IMAGE_PATH}: {os.listdir(SPROTO_IMAGE_PATH)}")
    
    for idx, filename in enumerate(image_filenames):
        file_path = os.path.join(SPROTO_IMAGE_PATH, filename)
        logging.debug(f"Attempting to load {file_path} for Sproto '{sproto_names[idx]}'")
        if not os.path.exists(file_path):
            logging.warning(f"Image file '{filename}' not found for Sproto '{sproto_names[idx]}'. Using fallback image.")
            missing_files.append(filename)
            sproto_images.append(fallback_image)
        else:
            try:
                image = pygame.image.load(file_path).convert_alpha()
                image = pygame.transform.scale(image, (50, 50))
                sproto_images.append(image)
                logging.info(f"Loaded image '{filename}' for Sproto '{sproto_names[idx]}'")
            except pygame.error as e:
                logging.error(f"Error loading image '{filename}' for Sproto '{sproto_names[idx]}': {e}. Using fallback image.")
                missing_files.append(filename)
                sproto_images.append(fallback_image)

    if missing_files:
        logging.error(f"Missing image files: {', '.join(missing_files)}")

    if len(sproto_images) != len(sproto_names):
        logging.error(f"Mismatch: {len(sproto_images)} images loaded but {len(sproto_names)} Sprotos defined. Adjusting with fallbacks.")
        if len(sproto_images) < len(sproto_names):
            sproto_images.extend([fallback_image] * (len(sproto_names) - len(sproto_images)))
        else:
            sproto_images = sproto_images[:len(sproto_names)]
    
    return sproto_images

def load_selection_background(screen):
    if not os.path.exists(SELECTION_BG_PATH):
        logging.error(f"Background image '{SELECTION_BG_PATH}' not found. Using white background.")
        screen.fill(BLACK)
        error_text = font.render("Background image missing!", True, RED)
        screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        pygame.time.wait(2000)
        return None
    try:
        bg = pygame.image.load(SELECTION_BG_PATH).convert()
        bg = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        logging.info(f"Loaded selection screen background: {SELECTION_BG_PATH}")
        return bg
    except Exception as e:
        logging.error(f"Error loading background image '{SELECTION_BG_PATH}': {e}. Using white background.")
        screen.fill(BLACK)
        error_text = font.render("Background image load failed!", True, RED)
        screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        pygame.time.wait(2000)
        return None

def load_race_backgrounds():
    try:
        race_backgrounds = {
            "single_options": [pygame.image.load(path).convert_alpha() for path in RACE_BG_PATHS["single_options"]],
            "tournament": [pygame.image.load(path).convert_alpha() for path in RACE_BG_PATHS["tournament"]],
            "results": pygame.image.load(RACE_BG_PATHS["results"]).convert_alpha()
        }
        return race_backgrounds, race_backgrounds["single_options"]
    except Exception as e:
        logging.error(f"Failed to load race backgrounds: {e}")
        return {}, []

def load_trophy_image():
    try:
        return pygame.image.load(TROPHY_PATH).convert_alpha()
    except Exception as e:
        logging.error(f"Failed to load trophy image: {e}")
        return None