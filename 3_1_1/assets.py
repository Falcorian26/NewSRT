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
    race_backgrounds = {"single": None, "tournament": [None] * 7, "results": None}
    single_bg_options = []
    
    for bg_path in RACE_BG_PATHS["single_options"]:
        if not os.path.exists(bg_path):
            logging.error(f"Single race background option '{bg_path}' not found. Skipping.")
            single_bg_options.append(None)
        else:
            try:
                bg = pygame.image.load(bg_path).convert()
                bg = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
                single_bg_options.append(bg)
                logging.info(f"Loaded single race background option: {bg_path}")
            except Exception as e:
                logging.error(f"Error loading single race background option '{bg_path}': {e}. Skipping.")
                single_bg_options.append(None)

    for i, bg_path in enumerate(RACE_BG_PATHS["tournament"]):
        if not os.path.exists(bg_path):
            logging.error(f"Tournament race {i+1} background image '{bg_path}' not found. Using blue background.")
            race_backgrounds["tournament"][i] = None
        else:
            try:
                bg = pygame.image.load(bg_path).convert()
                bg = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
                race_backgrounds["tournament"][i] = bg
                logging.info(f"Loaded tournament race {i+1} background: {bg_path}")
            except Exception as e:
                logging.error(f"Error loading tournament race {i+1} background '{bg_path}': {e}. Using blue background.")
                race_backgrounds["tournament"][i] = None

    if not os.path.exists(RACE_BG_PATHS["results"]):
        logging.error(f"Results background image '{RACE_BG_PATHS['results']}' not found. Using blue background.")
        race_backgrounds["results"] = None
    else:
        try:
            bg = pygame.image.load(RACE_BG_PATHS["results"]).convert()
            bg = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
            race_backgrounds["results"] = bg
            logging.info(f"Loaded results background: {RACE_BG_PATHS['results']}")
        except Exception as e:
            logging.error(f"Error loading results background '{RACE_BG_PATHS['results']}': {e}. Using blue background.")
            race_backgrounds["results"] = None
    
    return race_backgrounds, single_bg_options

def load_trophy_image():
    if not os.path.exists(TROPHY_PATH):
        logging.error(f"Trophy image '{TROPHY_PATH}' not found. Using purple square.")
        trophy_image = pygame.Surface((100, 100))
        trophy_image.fill(PURPLE)
        return trophy_image
    try:
        trophy_image = pygame.image.load(TROPHY_PATH).convert_alpha()
        trophy_image = pygame.transform.scale(trophy_image, (100, 100))
        logging.info(f"Loaded trophy image: {TROPHY_PATH}")
        return trophy_image
    except Exception as e:
        logging.error(f"Error loading trophy image '{TROPHY_PATH}': {e}. Using purple square.")
        trophy_image = pygame.Surface((100, 100))
        trophy_image.fill(PURPLE)
        return trophy_image