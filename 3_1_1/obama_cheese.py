import pygame
import random
import os
from settings import *

def run_obama_cheese_mode(screen):
    clock = pygame.time.Clock()
    running = True

    # Load Obama sprite (find by name)
    from assets import load_sproto_images
    from settings import sproto_names, image_filenames, SPROTO_IMAGE_PATH

    obama_idx = None
    for idx, name in enumerate(sproto_names):
        if name.lower().startswith("obama"):
            obama_idx = idx
            break
    if obama_idx is None:
        obama_idx = 0  # fallback

    sproto_images = load_sproto_images()
    obama_sprite = pygame.transform.scale(sproto_images[obama_idx], (100, 100))

    # Cheese settings
    cheese_font = pygame.font.SysFont("comic sans ms", 28, bold=True)  # Smaller cheese text
    cheese_text = cheese_font.render("cheese", True, YELLOW)
    cheese_rect = cheese_text.get_rect()
    cheese_pos = [random.randint(100, SCREEN_WIDTH - 200), random.randint(100, SCREEN_HEIGHT - 200)]

    # Obama position
    obama_pos = [SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2]
    obama_speed = 5.0

    # End game button
    button_font = pygame.font.SysFont("arial", 32, bold=True)
    button_w, button_h = 220, 70
    end_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - button_w // 2, SCREEN_HEIGHT - 120, button_w, button_h)

    # Cheese movement timer
    cheese_move_timer = 0
    cheese_move_interval = 1.2  # seconds

    # Cheese never gets caught
    cheese_min_dist = 220  # Increased so Obama never gets close

    # Timer for cheese mode
    cheese_timer = 0.0

    while running:
        dt = clock.tick(60) / 1000.0
        cheese_timer += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if end_button_rect.collidepoint(mx, my):
                    return

        # Move cheese randomly every interval
        cheese_move_timer += dt
        if cheese_move_timer > cheese_move_interval:
            cheese_pos[0] = random.randint(80, SCREEN_WIDTH - 180)
            cheese_pos[1] = random.randint(80, SCREEN_HEIGHT - 180)
            cheese_move_timer = 0

        # Move Obama toward cheese, but never close enough
        dx = cheese_pos[0] - obama_pos[0]
        dy = cheese_pos[1] - obama_pos[1]
        dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
        if dist > cheese_min_dist:
            obama_pos[0] += obama_speed * dx / dist
            obama_pos[1] += obama_speed * dy / dist
        else:
            # Obama gets close, but cheese jumps away
            cheese_pos[0] = random.randint(80, SCREEN_WIDTH - 180)
            cheese_pos[1] = random.randint(80, SCREEN_HEIGHT - 180)

        # Draw everything
        screen.fill(BLUE)
        # Draw cheese
        cheese_rect.topleft = (int(cheese_pos[0]), int(cheese_pos[1]))
        screen.blit(cheese_text, cheese_rect)
        # Draw Obama
        obama_rect = obama_sprite.get_rect(center=(int(obama_pos[0]), int(obama_pos[1])))
        screen.blit(obama_sprite, obama_rect)
        # Draw cheese mode timer
        timer_font = pygame.font.SysFont("arial", 28, bold=True)
        timer_text = timer_font.render(f"Time: {cheese_timer:.1f}s", True, WHITE)
        screen.blit(timer_text, (30, 30))
        # Draw "He really wants it!" blinking text
        want_font = pygame.font.SysFont("arial", 36, bold=True)
        blink = int(pygame.time.get_ticks() / 400) % 2 == 0
        want_color = YELLOW if blink else WHITE
        want_text = want_font.render("He really wants it.", True, want_color)
        screen.blit(want_text, (SCREEN_WIDTH // 2 - want_text.get_width() // 2, 80))
        # Draw end game button
        pygame.draw.rect(screen, RED, end_button_rect)
        pygame.draw.rect(screen, WHITE, end_button_rect, 3)
        end_surf = button_font.render("End Game", True, BLACK)
        screen.blit(end_surf, end_surf.get_rect(center=end_button_rect.center))
        pygame.display.flip()
