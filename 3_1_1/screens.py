import pygame
import logging
from settings import *
from ui import *
from sproto import get_track_position

# Dynamic tiny_font based on number of racers
def get_tiny_font(num_sprotos):
    font_size = max(10, min(12, 16 - num_sprotos // 5))  # Scale from 16pt to 10pt
    return pygame.font.Font(None, font_size)

def render_race_screen(screen, sprotos, race_distance, time_elapsed, race_number, winner, track_surface, buttons, current_background, flash_timer, is_muted, lane_height=100):
    if current_background is not None:
        screen.blit(current_background, (0, 0))
    else:
        screen.fill(BLUE)
    track_y = 20 if lane_height < 100 else SCREEN_HEIGHT // 4
    screen.blit(track_surface, (0, track_y))
    
    tiny_font = get_tiny_font(len(sprotos))
    
    if lane_height == 100:  # Single/tournament: curved lanes only
        for i in range(len(sprotos)):
            start = (0, track_y + i * lane_height)
            end = (SCREEN_WIDTH, track_y + i * lane_height)
            control1 = (SCREEN_WIDTH // 4, track_y + i * lane_height - 50)
            control2 = (3 * SCREEN_WIDTH // 4, track_y + i * lane_height + 50)
            points = []
            for t in range(0, 101, 2):
                t = t / 100
                x = (1-t)**3 * start[0] + 3*(1-t)**2*t * control1[0] + 3*(1-t)*t**2 * control2[0] + t**3 * end[0]
                y = (1-t)**3 * start[1] + 3*(1-t)**2*t * control1[1] + 3*(1-t)*t**2 * control2[1] + t**3 * end[1]
                points.append((x, y))
            pygame.draw.lines(screen, YELLOW, False, points, 2)  # Curved lines are now yellow and 2px thick
    
    leader = max(sprotos, key=lambda s: (s.position, -float('inf') if s.finish_place is None else -s.finish_place))
    
    for i, sproto in enumerate(sprotos):
        adjusted_lane = sproto.lane - 1 if lane_height < 100 else sproto.lane
        x, y = get_track_position(sproto.position, adjusted_lane, race_distance, lane_height=lane_height)
        if lane_height < 100:
            sprite = sproto.small_sprite
            sprite_rect = (x, y - 11.5, 23, 23)
            speed_ratio = max(0, min(1, (sproto.current_speed - sproto.min_speed) / (sproto.max_speed - sproto.min_speed)))
            speed_bar_rect = (x, y + 13, 23 * speed_ratio, 2.3)
            speed_bar_border_rect = (x, y + 13, 23 * speed_ratio, 2.3)
            name_font = tiny_font
            place_font_small = tiny_font
            name_x_offset = -50
            name_y_offset = -5
            place_x_offset = 28
        else:
            sprite = sproto.sprite
            sprite_rect = (x, y - 25, 50, 50)
            speed_ratio = max(0, min(1, (sproto.current_speed - sproto.min_speed) / (sproto.max_speed - sproto.min_speed)))
            speed_bar_rect = (x, y + 25, 50 * speed_ratio, 5)
            speed_bar_border_rect = (x, y + 25, 50 * speed_ratio, 5)
            name_font = small_font
            place_font_small = place_font
            name_x_offset = 0
            name_y_offset = -45
            place_x_offset = 60
        
        screen.blit(sprite, sprite_rect[:2])
        pygame.draw.rect(screen, BLACK, sprite_rect, 1)
        text_color = GOLD if sproto == leader else WHITE
        stroke = sproto == leader
        draw_text_with_shadow(screen, sproto.name, name_font, text_color, (x + name_x_offset, y + name_y_offset), stroke=stroke)
        glow_color = (255 * speed_ratio, 255 * (1 - speed_ratio), 0)
        pygame.draw.rect(screen, glow_color, speed_bar_rect)
        pygame.draw.rect(screen, BLACK, speed_bar_border_rect, 1)
        if sproto.finished and sproto.finish_place:
            place_text = f"{sproto.finish_place}{sproto.get_place_suffix()}"
            draw_text_with_shadow(screen, place_text, place_font_small, YELLOW, (x + place_x_offset, y - 11.5 if lane_height < 100 else y - 25))
    
    timer_text = small_font.render(f"Time: {time_elapsed:.1f} seconds", True, WHITE)
    timer_x = SCREEN_WIDTH // 2 - timer_text.get_width() // 2
    draw_text_with_shadow(screen, f"Time: {time_elapsed:.1f} seconds", small_font, WHITE, (timer_x, 10))
    
    if race_number:
        text_color = YELLOW if flash_timer < 3.0 and int(flash_timer * 2) % 2 == 0 else WHITE
        draw_text_with_shadow(screen, f"Race {race_number} / 7", large_font, text_color, (SCREEN_WIDTH // 2 - 70, 50))
        rows = len(sprotos)
        cols = 5
        col_widths = [180, 60, 60, 80, 80]
        table_x = 10
        table_y = 35
        cell_height = 30
        table_width = sum(col_widths)
        table_height = rows * cell_height + 20
        table_surface = pygame.Surface((table_width, table_height), pygame.SRCALPHA)
        table_surface.fill((0, 0, 0, 180))
        screen.blit(table_surface, (table_x, table_y - 20))
        headers = ["Racer", "Wins", "Pts", "AvgSpd", "CurSpd"]
        for col, header in enumerate(headers):
            offset_x = sum(col_widths[:col])
            draw_text_with_shadow(screen, header, small_font, YELLOW, (table_x + offset_x + 2, table_y - 20))
        for row, sproto in enumerate(sprotos):
            cell_y = table_y + row * cell_height
            for col in range(cols):
                offset_x = sum(col_widths[:col])
                if col == 0:
                    draw_text_with_shadow(screen, sproto.name, small_font, YELLOW, (table_x + offset_x + 2, cell_y))
                elif col == 1:
                    draw_text_with_shadow(screen, str(sproto.tournament_wins), small_font, YELLOW, (table_x + offset_x + 2, cell_y))
                elif col == 2:
                    draw_text_with_shadow(screen, str(sproto.tournament_points), small_font, YELLOW, (table_x + offset_x + 2, cell_y))
                elif col == 3:
                    avg_speed = sproto.get_tournament_avg_speed()
                    draw_text_with_shadow(screen, f"{avg_speed:.1f}", small_font, YELLOW, (table_x + offset_x + 2, cell_y))
                elif col == 4:
                    draw_text_with_shadow(screen, f"{sproto.current_speed:.1f}", small_font, YELLOW, (table_x + offset_x + 2, cell_y))
    if winner:
        draw_text_with_shadow(screen, f"Winner: {winner.name}!", font, WHITE, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50))
    for button in buttons:
        if isinstance(button, MuteButton):
            button.draw(screen, is_muted)
        else:
            button.draw(screen)

def select_sprotos(screen, sproto_list, max_selections, selection_background, is_muted):
    selected_sprotos = []
    running = True
    start_button = Button("Start Race", 385, 660, 200, 50, BLUE_BUTTON)
    tourney_button = Button("Tourney", 615, 660, 200, 50, PURPLE)
    all_race_button = Button("All Characters Race", 500, 610, 200, 50, GREEN)
    end_game_button = Button("End Game", 500, 730, 200, 50, RED)
    mute_button = MuteButton(SCREEN_WIDTH - 75, 10, 50, 20, GRAY)

    logging.info("Sprotos available in selection screen:")
    for sproto in sproto_list:
        logging.info(f"- {sproto.name}")

    pygame.mixer.music.stop()
    if os.path.exists(SELECTION_MUSIC_PATH):
        try:
            pygame.mixer.music.load(SELECTION_MUSIC_PATH)
            pygame.mixer.music.set_volume(0 if is_muted else 0.35)
            if not is_muted:
                pygame.mixer.music.play(loops=-1)
                logging.info(f"Playing selection music: {SELECTION_MUSIC_PATH} at 35% volume")
            else:
                logging.info("Selection music loaded but muted.")
        except Exception as e:
            logging.error(f"Error loading selection music '{SELECTION_MUSIC_PATH}': {e}")
            screen.fill(BLACK)
            error_text = font.render("Selection music load failed!", True, RED)
            screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, SCREEN_HEIGHT // 2))
            pygame.display.flip()
            pygame.time.wait(2000)
    else:
        logging.error(f"Selection music file '{SELECTION_MUSIC_PATH}' not found.")
        screen.fill(BLACK)
        error_text = font.render("Music file missing!", True, RED)
        screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, SCREEN_HEIGHT // 2))
        pygame.display.flip()
        pygame.time.wait(2000)

    cols = 3
    cell_width = 220
    cell_height = 50
    table_width = cols * cell_width
    rows = (len(sproto_list) + 2) // 3
    table_height = (rows + 1) * cell_height
    table_x = (SCREEN_WIDTH - table_width) // 2
    table_y = 100

    while running:
        mouse_pos = pygame.mouse.get_pos()
        hovered_idx = None
        for idx, sproto in enumerate(sproto_list):
            col = idx % cols
            row = idx // cols
            cell_x = table_x + col * cell_width
            cell_y = table_y + (row + 1) * cell_height
            rect = pygame.Rect(cell_x, cell_y, cell_width, cell_height)
            if rect.collidepoint(mouse_pos):
                hovered_idx = idx
                break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.mixer.music.stop()
                logging.info("Selection music stopped.")
                return None, False, is_muted, None
            if start_button.is_clicked(event) and len(selected_sprotos) > 0:
                pygame.mixer.music.stop()
                logging.info("Selection music stopped.")
                return selected_sprotos, False, is_muted, "normal"
            if tourney_button.is_clicked(event) and len(selected_sprotos) > 0:
                pygame.mixer.music.stop()
                logging.info("Selection music stopped.")
                return selected_sprotos, True, is_muted, "tournament"
            if all_race_button.is_clicked(event):
                pygame.mixer.music.stop()
                logging.info("Selection music stopped.")
                return sproto_list, False, is_muted, "all_characters"
            if end_game_button.is_clicked(event):
                pygame.mixer.music.stop()
                logging.info("Selection music stopped.")
                return None, False, is_muted, None
            clicked, is_muted = mute_button.is_clicked(event, is_muted, SELECTION_MUSIC_PATH)
            if clicked:
                pass
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                for idx, sproto in enumerate(sproto_list):
                    row = idx // cols
                    col = idx % cols
                    cell_x = table_x + col * cell_width
                    cell_y = table_y + (row + 1) * cell_height
                    rect = pygame.Rect(cell_x, cell_y, cell_width, cell_height)
                    if rect.collidepoint(mouse_pos):
                        if sproto not in selected_sprotos and len(selected_sprotos) < max_selections:
                            selected_sprotos.append(sproto)
                        elif sproto in selected_sprotos:
                            selected_sprotos.remove(sproto)

        if selection_background is not None:
            screen.blit(selection_background, (0, 0))
        else:
            screen.fill(WHITE)

        header_rect = pygame.Rect(table_x, table_y, table_width, cell_height)
        pygame.draw.rect(screen, BLACK, header_rect)
        draw_text_with_shadow(screen, f"Select Up to {max_selections} Sprotos", font, WHITE, (table_x + 150, table_y + 15))

        draw_text_with_shadow(screen, "Version 3.1.1", small_font, WHITE, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT - 40))
        draw_text_with_shadow(screen, "@coinapache on X", small_font, WHITE, (SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT - 20))

        for idx, sproto in enumerate(sproto_list):
            row = idx // cols
            col = idx % cols
            cell_x = table_x + col * cell_width
            cell_y = table_y + (row + 1) * cell_height
            rect = pygame.Rect(cell_x, cell_y, cell_width, cell_height)
            if sproto in selected_sprotos:
                color = BLUE_BUTTON
                text_color = WHITE
            elif idx == hovered_idx:
                color = YELLOW
                text_color = BLUE
            else:
                color = BLACK
                text_color = WHITE
            pygame.draw.rect(screen, color, rect)
            image_x = cell_x + 10
            image_y = cell_y + (cell_height - 50) // 2
            if sproto.name in ["Oggo", "BigSwole", "GPM"]:
                pygame.draw.rect(screen, GREEN, (image_x, image_y, 50, 50), 2)
            screen.blit(sproto.sprite, (image_x, image_y))
            draw_text_with_shadow(screen, f"{sproto.name}", selection_font, text_color, (image_x + 50, cell_y + (cell_height - 24) // 2))

        draw_text_with_shadow(screen, f"Selected: {len(selected_sprotos)}/{max_selections}", font, WHITE, (SCREEN_WIDTH // 2 - 80, 620))
        start_button.draw(screen)
        tourney_button.draw(screen)
        all_race_button.draw(screen)
        end_game_button.draw(screen)
        mute_button.draw(screen, is_muted)
        pygame.display.flip()

    pygame.mixer.music.stop()
    logging.info("Selection music stopped.")
    return None, False, is_muted, None

def show_results_screen(screen, sprotos, finishers, race_backgrounds, trophy_image, is_muted):
    running = True
    clock = pygame.time.Clock()
    sorted_sprotos = sorted(sprotos, key=lambda h: finishers.index(h) if h in finishers else len(finishers))
    black_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    continue_button = Button("Continue", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 50, GREEN)
    mute_button = MuteButton(SCREEN_WIDTH - 75, 10, 50, 20, GRAY)
    marquee_text = MARQUEE_TEXT
    marquee_x = SCREEN_WIDTH
    marquee_y = SCREEN_HEIGHT - 150
    marquee_width = small_font.render(marquee_text, True, WHITE).get_width()
    
    table_width = int(SCREEN_WIDTH * 0.8)
    table_x = (SCREEN_WIDTH - table_width) // 2
    table_y = 120
    cell_height = 60
    num_cols = 3
    cell_width = table_width // num_cols
    table_height = len(sorted_sprotos) * cell_height
    max_visible_rows = 10
    scroll_offset = 0
    scroll_speed = 100

    logging.info("\nDetailed Speed Analysis:")
    for idx, sproto in enumerate(sorted_sprotos):
        avg_speed = sproto.get_average_speed()
        finish_time = sproto.finish_time if sproto.finish_time is not None else 0
        logging.info(f"{idx + 1}. {sproto.name}: Finish Time={finish_time:.2f}s, Average Speed={avg_speed:.2f}")

    # Ensure trophy_image is loaded
    if trophy_image is None:
        logging.error("Trophy image is missing. Ensure the file path is correct.")
        return False, is_muted

    # Ensure race_backgrounds["results"] is loaded
    if "results" not in race_backgrounds or race_backgrounds["results"] is None:
        logging.error("Results background is missing. Ensure the file path is correct.")
        return False, is_muted

    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False, is_muted
            if continue_button.is_clicked(event):
                running = False
            clicked, is_muted = mute_button.is_clicked(event, is_muted, RACE_MUSIC_PATH)
            if clicked:
                pass
            if event.type == pygame.MOUSEWHEEL:
                scroll_offset -= event.y * 30
                scroll_offset = max(0, min(scroll_offset, max(0, table_height - max_visible_rows * cell_height)))

        marquee_x -= 100 * dt
        if marquee_x < -marquee_width:
            marquee_x = SCREEN_WIDTH

        if race_backgrounds["results"] is not None:
            screen.blit(race_backgrounds["results"], (0, 0))
        else:
            screen.fill(BLUE)

        black_surface.fill((0, 0, 0, 180))
        visible_height = min(table_height, max_visible_rows * cell_height + 60)
        pygame.draw.rect(black_surface, (0, 0, 0, 180), (table_x - 10, table_y - 30, table_width + 20, visible_height))
        screen.blit(black_surface, (0, 0))
        black_surface.fill((0, 0, 0, 0))

        draw_text_with_shadow(screen, "Race Results", font, WHITE, (SCREEN_WIDTH // 2 - 80, 60))

        headers = ["Racer", "Place", "Avg Speed"]
        for col, header in enumerate(headers):
            cell_x = table_x + col * cell_width
            draw_text_with_shadow(screen, header, small_font, YELLOW, (cell_x + cell_width // 2 - 30, table_y - 20))
            pygame.draw.rect(screen, WHITE, (cell_x, table_y - 30, cell_width, 30), 1)

        start_row = scroll_offset // cell_height
        end_row = min(start_row + max_visible_rows, len(sorted_sprotos))
        for row in range(start_row, end_row):
            sproto = sorted_sprotos[row]
            cell_y = table_y + (row - start_row) * cell_height
            for col in range(num_cols):
                cell_x = table_x + col * cell_width
                pygame.draw.rect(screen, WHITE, (cell_x, cell_y, cell_width, cell_height), 1)
                if col == 0:
                    image_x = cell_x + 10
                    image_y = cell_y + (cell_height - 50) // 2
                    border_color = GOLD if row == 0 else SILVER if row == 1 else BRONZE if row == 2 else None
                    if border_color:
                        pygame.draw.rect(screen, border_color, (image_x - 3, image_y - 3, 56, 56), 3)
                    screen.blit(sproto.sprite, (image_x, image_y))
                    name_text = small_font.render(sproto.name, True, WHITE)
                    name_x = image_x + 60
                    name_y = cell_y + (cell_height - name_text.get_height()) // 2
                    draw_text_with_shadow(screen, sproto.name, small_font, WHITE, (name_x, name_y))
                elif col == 1:
                    place_text = f"{row + 1}{sproto.get_place_suffix()}"
                    draw_text_with_shadow(screen, place_text, small_font, WHITE, (cell_x + 10, cell_y + (cell_height - 20) // 2))
                elif col == 2:
                    avg_speed = sproto.get_average_speed()
                    draw_text_with_shadow(screen, f"{avg_speed:.2f}", small_font, WHITE, (cell_x + 10, cell_y + (cell_height - 20) // 2))

        draw_text_with_shadow(screen, marquee_text, small_font, WHITE, (marquee_x, marquee_y))
        continue_button.draw(screen)
        mute_button.draw(screen, is_muted)
        pygame.display.flip()

    return True, is_muted

def show_tournament_results(screen, sprotos, race_backgrounds, trophy_image, is_muted):
    running = True
    clock = pygame.time.Clock()
    sorted_sprotos = sorted(sprotos, key=lambda s: (-s.tournament_wins, -s.get_tournament_avg_speed()))
    black_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    continue_button = Button("Continue", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 50, GREEN)
    mute_button = MuteButton(SCREEN_WIDTH - 75, 10, 50, 20, GRAY)
    marquee_text = MARQUEE_TEXT
    marquee_x = SCREEN_WIDTH
    marquee_y = SCREEN_HEIGHT - 150
    marquee_width = small_font.render(marquee_text, True, WHITE).get_width()

    logging.info("\nTournament Final Rankings:")
    for idx, sproto in enumerate(sorted_sprotos):
        avg_speed = sproto.get_tournament_avg_speed()
        logging.info(f"{idx + 1}. {sproto.name}: Wins={sproto.tournament_wins}, Points={sproto.tournament_points}, Avg Speed={avg_speed:.2f}")

    table_width = int(SCREEN_WIDTH * 0.8)
    table_x = (SCREEN_WIDTH - table_width) // 2
    table_y = 120
    cell_height = 60
    num_cols = 6
    cell_width = table_width // num_cols
    table_height = len(sorted_sprotos) * cell_height
    max_visible_rows = 10
    scroll_offset = 0
    scroll_speed = 100

    # Ensure trophy_image is loaded
    if trophy_image is None:
        logging.error("Trophy image is missing. Ensure the file path is correct.")
        return False, is_muted

    # Ensure race_backgrounds["results"] is loaded
    if "results" not in race_backgrounds or race_backgrounds["results"] is None:
        logging.error("Results background is missing. Ensure the file path is correct.")
        return False, is_muted

    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.mixer.music.stop()
                logging.info("Tournament music stopped (quit).")
                return False, is_muted
            if continue_button.is_clicked(event):
                pygame.mixer.music.stop()
                logging.info("Tournament music stopped (continue).")
                running = False
            clicked, is_muted = mute_button.is_clicked(event, is_muted, RACE_MUSIC_PATH)
            if clicked:
                pass
            if event.type == pygame.MOUSEWHEEL:
                scroll_offset -= event.y * 30
                scroll_offset = max(0, min(scroll_offset, max(0, table_height - max_visible_rows * cell_height)))

        marquee_x -= 100 * dt
        if marquee_x < -marquee_width:
            marquee_x = SCREEN_WIDTH

        if race_backgrounds["results"] is not None:
            screen.blit(race_backgrounds["results"], (0, 0))
        else:
            screen.fill(BLUE)

        black_surface.fill((0, 0, 0, 180))
        visible_height = min(table_height, max_visible_rows * cell_height + 60)
        pygame.draw.rect(black_surface, (0, 0, 0, 180), (table_x - 10, table_y - 30, table_width + 20, visible_height))
        screen.blit(black_surface, (0, 0))
        black_surface.fill((0, 0, 0, 0))

        draw_text_with_shadow(screen, "Tournament Results", font, WHITE, (SCREEN_WIDTH // 2 - 120, 60))

        headers = ["Racer", "Place", "Points", "Wins", "Avg Speed", "Trophy"]
        for col, header in enumerate(headers):
            cell_x = table_x + col * cell_width
            draw_text_with_shadow(screen, header, small_font, YELLOW, (cell_x + 5, table_y - 20))
            pygame.draw.rect(screen, WHITE, (cell_x, table_y - 30, cell_width, 30), 1)

        start_row = scroll_offset // cell_height
        end_row = min(start_row + max_visible_rows, len(sorted_sprotos))
        for row in range(start_row, end_row):
            sproto = sorted_sprotos[row]
            cell_y = table_y + (row - start_row) * cell_height
            for col in range(num_cols):
                cell_x = table_x + col * cell_width
                pygame.draw.rect(screen, WHITE, (cell_x, cell_y, cell_width, cell_height), 1)
                if col == 0:
                    image_x = cell_x + 10
                    image_y = cell_y + (cell_height - 50) // 2
                    border_color = GOLD if row == 0 else SILVER if row == 1 else BRONZE if row == 2 else None
                    if border_color:
                        pygame.draw.rect(screen, border_color, (image_x - 3, image_y - 3, 56, 56), 3)
                    screen.blit(sproto.sprite, (image_x, image_y))
                    name_text = small_font.render(sproto.name, True, WHITE)
                    name_x = image_x + 60
                    name_y = cell_y + (cell_height - name_text.get_height()) // 2
                    draw_text_with_shadow(screen, sproto.name, small_font, WHITE, (name_x, name_y))
                elif col == 1:
                    place_text = f"{row + 1}{sproto.get_place_suffix()}"
                    draw_text_with_shadow(screen, place_text, small_font, WHITE, (cell_x + 5, cell_y + (cell_height - 20) // 2))
                elif col == 2:
                    draw_text_with_shadow(screen, f"{sproto.tournament_points}", small_font, WHITE, (cell_x + 5, cell_y + (cell_height - 20) // 2))
                elif col == 3:
                    draw_text_with_shadow(screen, f"{sproto.tournament_wins}", small_font, WHITE, (cell_x + 5, cell_y + (cell_height - 20) // 2))
                elif col == 4:
                    avg_speed = sproto.get_tournament_avg_speed()
                    draw_text_with_shadow(screen, f"{avg_speed:.2f}", small_font, WHITE, (cell_x + 5, cell_y + (cell_height - 20) // 2))
                elif col == 5 and row == 0:
                    trophy_x = cell_x + (cell_width - 50) // 2
                    trophy_y = cell_y + (cell_height - 50) // 2
                    scaled_trophy = pygame.transform.scale(trophy_image, (50, 50))
                    screen.blit(scaled_trophy, (trophy_x, trophy_y))

        draw_text_with_shadow(screen, marquee_text, small_font, WHITE, (marquee_x, marquee_y))
        continue_button.draw(screen)
        mute_button.draw(screen, is_muted)
        pygame.display.flip()

    return True, is_muted