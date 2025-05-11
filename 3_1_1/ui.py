import pygame
import logging
from settings import *

def cache_track_surface(race_distance, num_lanes, lane_height=100):
    if num_lanes == 0:  # Handle case with no lanes
        logging.warning("No lanes to render. Returning an empty surface.")
        return pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    track_surface = pygame.Surface((SCREEN_WIDTH, num_lanes * lane_height), pygame.SRCALPHA)
    return track_surface

def draw_text_with_shadow(screen, text, font, color, pos, stroke=False):
    text_surface = font.render(text, True, color)
    shadow_surface = font.render(text, True, BLACK)
    
    if stroke:
        stroke_positions = [
            (pos[0] - 1, pos[1] - 1), (pos[0], pos[1] - 1), (pos[0] + 1, pos[1] - 1),
            (pos[0] - 1, pos[1]),                     (pos[0] + 1, pos[1]),
            (pos[0] - 1, pos[1] + 1), (pos[0], pos[1] + 1), (pos[0] + 1, pos[1] + 1)
        ]
        for stroke_pos in stroke_positions:
            screen.blit(font.render(text, True, BLACK), stroke_pos)
    
    screen.blit(shadow_surface, (pos[0] + 2, pos[1] + 2))
    screen.blit(text_surface, pos)

class Button:
    def __init__(self, text, x, y, width, height, color, hover_color=BLUE, custom_font=None):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.hover_color = hover_color
        self.font = custom_font if custom_font is not None else pygame.font.SysFont("arial", 24)

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = self.rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, self.hover_color if is_hovered else self.color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        text_color = YELLOW if is_hovered else WHITE
        text_surf = self.font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

class MuteButton:
    def __init__(self, x, y, width, height, color, hover_color=BLUE):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.hover_color = hover_color
        self.font = pygame.font.SysFont("arial", 16)

    def draw(self, screen, is_muted):
        mouse_pos = pygame.mouse.get_pos()
        is_hovered = self.rect.collidepoint(mouse_pos)
        pygame.draw.rect(screen, self.hover_color if is_hovered else self.color, self.rect)
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        text = "Mute" if not is_muted else "Unmute"
        text_color = YELLOW if is_hovered else WHITE
        text_surf = self.font.render(text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def is_clicked(self, event, is_muted, current_music_path):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                is_muted = not is_muted
                if is_muted:
                    pygame.mixer.music.pause()
                    logging.info("Music muted.")
                else:
                    if not pygame.mixer.music.get_busy():
                        try:
                            logging.info(f"Attempting to load music file: {current_music_path}")
                            if not os.path.exists(current_music_path):
                                logging.error(f"Music file not found at: {current_music_path}")
                            else:
                                pygame.mixer.music.load(current_music_path)  # Reload the music file dynamically
                                pygame.mixer.music.set_volume(0.35)
                                pygame.mixer.music.play(loops=-1)
                                logging.info("Music unmuted and playing dynamically.")
                        except Exception as e:
                            logging.error(f"Error starting music dynamically: {e}")
                    else:
                        pygame.mixer.music.unpause()
                        logging.info("Music unmuted and playing.")
                return True, is_muted
        return False, is_muted