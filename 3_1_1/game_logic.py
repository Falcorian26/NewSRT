import pygame
import random
import logging
import os
from settings import *
from ui import *
from screens import render_race_screen, show_results_screen

def simulate_race(screen, sprotos, race_distance, race_duration, race_backgrounds, single_bg_options, trophy_image, race_number=None, tournament_mode=False, is_muted=False):
    clock = pygame.time.Clock()
    time_elapsed = 0
    race_finished = False
    winner = None
    choice = None
    running = True
    log_timer = 0
    flash_timer = 0
    finishers = []
    track_surface = cache_track_surface(race_distance, len(sprotos))

    current_background = None
    if tournament_mode and race_number is not None:
        current_background = race_backgrounds["tournament"][race_number - 1]
    else:
        available_bgs = [bg for bg in single_bg_options if bg is not None]
        if available_bgs:
            current_background = random.choice(available_bgs)
            logging.info("Selected random background for single race.")
        else:
            current_background = None
            logging.warning("No valid backgrounds available for single race. Using blue background.")

    if tournament_mode and race_number == 1:
        for sproto in sprotos:
            sproto.tournament_wins = 0
            sproto.tournament_points = 0
            sproto.tournament_speeds = []
            logging.info(f"Initialized tournament stats for {sproto.name}: wins={sproto.tournament_wins}, points={sproto.tournament_points}")

    if not tournament_mode or (tournament_mode and race_number == 1):
        if os.path.exists(RACE_MUSIC_PATH):
            try:
                pygame.mixer.music.load(RACE_MUSIC_PATH)
                pygame.mixer.music.set_volume(0 if is_muted else 0.35)
                if not is_muted:
                    pygame.mixer.music.play(loops=-1)
                    logging.info(f"Playing race music: {RACE_MUSIC_PATH} at 35% volume")
                else:
                    logging.info("Race music loaded but muted.")
            except Exception as e:
                logging.error(f"Error loading race music '{RACE_MUSIC_PATH}': {e}")
        else:
            logging.error(f"Race music file '{RACE_MUSIC_PATH}' not found.")

    button_width = 250
    button_height = 40
    button_spacing = 20
    table_x = (SCREEN_WIDTH - 2 * button_width - button_spacing) // 2
    table_y = SCREEN_HEIGHT * 0.75
    retry_same_button = Button("Retry Same Sprotos", table_x, table_y, button_width, button_height, RED)
    select_new_button = Button("Select New Sprotos", table_x + button_width + button_spacing, table_y, button_width, button_height, BLUE)
    back_to_results_button = Button("Back to Results", table_x, table_y + button_height + button_spacing, button_width, button_height, GREEN)
    end_game_button = Button("End Game", table_x + button_width + button_spacing, table_y + button_height + button_spacing, button_width, button_height, ORANGE)
    mute_button = MuteButton(SCREEN_WIDTH - 75, 10, 50, 20, GRAY)
    back_to_selection_button = Button("Back to Selection Screen", SCREEN_WIDTH - 225, 40, 200, 40, ORANGE, custom_font=race_button_font)
    buttons = [mute_button, back_to_selection_button]

    while running:
        dt = clock.tick(60) / 1000.0
        flash_timer += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                choice = "end"
                running = False
            clicked, is_muted = mute_button.is_clicked(event, is_muted, RACE_MUSIC_PATH)
            if clicked:
                pass
            if back_to_selection_button.is_clicked(event):
                choice = "back_to_selection"
                running = False

        if not race_finished:
            time_elapsed += dt
            for sproto in sprotos:
                sproto.run(race_distance, dt, finishers, time_elapsed)

            log_timer += dt
            if log_timer >= 1.0:
                logging.info(f"\nTime: {time_elapsed:.1f}s")
                for sproto in sprotos:
                    logging.info(f"{sproto.name}: Position={sproto.position:.2f}, Speed={sproto.current_speed:.2f}, Finished={sproto.finished}")
                log_timer = 0

            if all(sproto.finished for sproto in sprotos):
                race_finished = True
                winner = finishers[0] if finishers else max(sprotos, key=lambda h: h.position)
                for sproto in sprotos:
                    sproto.tournament_speeds.append(sproto.get_average_speed())
                logging.info(f"\nRace {'#' + str(race_number) if race_number is not None else ''} finished! Finish order:")
                for idx, sproto in enumerate(finishers):
                    logging.info(f"{idx + 1}. {sproto.name}: Avg Speed={sproto.get_average_speed():.2f}")
                logging.info(f"Selected winner: {winner.name} with avg speed {winner.get_average_speed():.2f}")

                if tournament_mode:
                    winner.tournament_wins += 1
                    num_racers = len(finishers)
                    step = 2 if num_racers > 5 else 1
                    for idx, sproto in enumerate(finishers):
                        place = idx + 1
                        points = max(2, 10 - (place - 1) * step)
                        sproto.tournament_points += points
                        logging.info(f"{sproto.name} finished {place}{sproto.get_place_suffix()}: +{points} points, total={sproto.tournament_points}, wins={sproto.tournament_wins}")

        if race_finished and not tournament_mode:
            buttons = [retry_same_button, select_new_button, back_to_results_button, end_game_button, mute_button, back_to_selection_button]
            draw_text_with_shadow(screen, f"Winner: {winner.name}!", font, WHITE, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50))
            pygame.display.flip()
            pygame.time.delay(2000)

            show_results = True
            while show_results:
                result, is_muted = show_results_screen(screen, sprotos, finishers, race_backgrounds, trophy_image, is_muted)
                if not result:
                    choice = "end"
                    running = False
                    show_results = False
                else:
                    post_race_running = True
                    while post_race_running:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                choice = "end"
                                post_race_running = False
                                running = False
                                show_results = False
                            if retry_same_button.is_clicked(event):
                                choice = "retry_same"
                                post_race_running = False
                                running = False
                                show_results = False
                            if select_new_button.is_clicked(event):
                                choice = "select_new"
                                post_race_running = False
                                running = False
                                show_results = False
                            if back_to_results_button.is_clicked(event):
                                choice = "back_to_results"
                                post_race_running = False
                            if end_game_button.is_clicked(event):
                                choice = "end"
                                post_race_running = False
                                running = False
                                show_results = False
                            clicked, is_muted = mute_button.is_clicked(event, is_muted, RACE_MUSIC_PATH)
                            if clicked:
                                pass
                            if back_to_selection_button.is_clicked(event):
                                choice = "back_to_selection"
                                post_race_running = False
                                running = False
                                show_results = False

                        render_race_screen(screen, sprotos, race_distance, time_elapsed, race_number, winner, track_surface, buttons, current_background, flash_timer, is_muted)
                        pygame.display.flip()

                if choice in ["retry_same", "select_new", "end", "back_to_selection"]:
                    if choice in ["select_new", "back_to_selection", "end"]:
                        pygame.mixer.music.stop()
                        logging.info("Race music stopped.")
                    if choice == "retry_same":
                        if os.path.exists(RACE_MUSIC_PATH):
                            try:
                                pygame.mixer.music.load(RACE_MUSIC_PATH)
                                pygame.mixer.music.set_volume(0 if is_muted else 0.35)
                                if not is_muted:
                                    pygame.mixer.music.play(loops=-1)
                                    logging.info(f"Playing race music (retry): {RACE_MUSIC_PATH} at 35% volume")
                                else:
                                    logging.info("Race music loaded but muted (retry).")
                            except Exception as e:
                                logging.error(f"Error loading race music (retry) '{RACE_MUSIC_PATH}': {e}")
        else:
            render_race_screen(screen, sprotos, race_distance, time_elapsed, race_number, winner, track_surface, buttons, current_background, flash_timer, is_muted)
            pygame.display.flip()

        if race_finished and tournament_mode:
            running = False

    return winner, choice, is_muted

def simulate_all_characters_race(screen, sprotos, race_distance, race_duration, race_backgrounds, single_bg_options, trophy_image, is_muted=False):
    clock = pygame.time.Clock()
    time_elapsed = 0
    race_finished = False
    winner = None
    choice = None
    running = True
    log_timer = 0
    flash_timer = 0
    finishers = []
    
    num_sprotos = len(sprotos)
    lane_height = max(20, SCREEN_HEIGHT // num_sprotos)  # Ensure minimum lane height
    track_surface = cache_track_surface(race_distance, num_sprotos, lane_height=lane_height)

    available_bgs = [bg for bg in single_bg_options if bg is not None]
    current_background = random.choice(available_bgs) if available_bgs else None
    if current_background:
        logging.info("Selected random background for all-characters race.")
    else:
        logging.warning("No valid backgrounds available. Using blue background.")

    if os.path.exists(RACE_MUSIC_PATH):
        try:
            pygame.mixer.music.load(RACE_MUSIC_PATH)
            pygame.mixer.music.set_volume(0 if is_muted else 0.35)
            if not is_muted:
                pygame.mixer.music.play(loops=-1)
                logging.info(f"Playing race music: {RACE_MUSIC_PATH} at 35% volume")
            else:
                logging.info("Race music loaded but muted.")
        except Exception as e:
            logging.error(f"Error loading race music '{RACE_MUSIC_PATH}': {e}")
    else:
        logging.error(f"Race music file '{RACE_MUSIC_PATH}' not found.")

    button_width = 340  # Increased width for "Run tournament with top 5"
    button_height = 40
    button_spacing = 20
    table_x = (SCREEN_WIDTH - 2 * button_width - button_spacing) // 2
    table_y = SCREEN_HEIGHT * 0.75
    retry_same_button = Button("Retry Same Sprotos", table_x, table_y, button_width, button_height, RED)
    select_new_button = Button("Select New Sprotos", table_x + button_width + button_spacing, table_y, button_width, button_height, BLUE)
    back_to_results_button = Button("Back to Results", table_x, table_y + button_height + button_spacing, button_width, button_height, GREEN)
    end_game_button = Button("End Game", table_x + button_width + button_spacing, table_y + button_height + button_spacing, button_width, button_height, ORANGE)
    mute_button = MuteButton(SCREEN_WIDTH - 75, 10, 50, 20, GRAY)
    tournament_button_y = table_y + 2 * (button_height + button_spacing) + 10
    # Use a slightly smaller font for the button to ensure text fits
    tournament_button_font = pygame.font.SysFont("arial", 22, bold=True)
    tournament_button = Button(
        "Run tournament with top 5",
        SCREEN_WIDTH // 2 - button_width // 2,
        tournament_button_y,
        button_width,
        button_height,
        ORANGE,
        custom_font=tournament_button_font
    )

    buttons = [mute_button]
    show_leaderboard = False
    leaderboard_delay = 9.1  # seconds

    while running:
        dt = clock.tick(60) / 1000.0
        flash_timer += dt
        time_elapsed += dt
        if time_elapsed >= leaderboard_delay:
            show_leaderboard = True
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                choice = "end"
                running = False
            clicked, is_muted = mute_button.is_clicked(event, is_muted, RACE_MUSIC_PATH)
            if clicked:
                pass

        if not race_finished:
            time_elapsed += dt
            for sproto in sprotos:
                sproto.run(race_distance, dt, finishers, time_elapsed)

            log_timer += dt
            if log_timer >= 2.0:
                logging.info(f"\nTime: {time_elapsed:.1f}s")
                for sproto in sprotos:
                    logging.info(f"{sproto.name}: Position={sproto.position:.2f}, Speed={sproto.current_speed:.2f}, Finished={sproto.finished}")
                log_timer = 0

            if all(sproto.finished for sproto in sprotos):
                race_finished = True
                winner = finishers[0] if finishers else max(sprotos, key=lambda h: h.position)
                for sproto in sprotos:
                    sproto.tournament_speeds.append(sproto.get_average_speed())
                logging.info(f"\nAll-Characters Race finished! Finish order:")
                for idx, sproto in enumerate(finishers):
                    logging.info(f"{idx + 1}. {sproto.name}: Avg Speed={sproto.get_average_speed():.2f}")
                logging.info(f"Selected winner: {winner.name} with avg speed {winner.get_average_speed():.2f}")

        if race_finished:
            # Arrange all 5 buttons, with the 5th below the 2x2 grid
            buttons = [
                retry_same_button, select_new_button, back_to_results_button, end_game_button, mute_button, tournament_button
            ]
            draw_text_with_shadow(screen, f"Winner: {winner.name}!", font, WHITE, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50))
            pygame.display.flip()
            pygame.time.delay(2000)

            show_results = True
            while show_results:
                result, is_muted = show_results_screen(screen, sprotos, finishers, race_backgrounds, trophy_image, is_muted)
                if not result:
                    choice = "end"
                    running = False
                    show_results = False
                else:
                    post_race_running = True
                    while post_race_running:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                choice = "end"
                                post_race_running = False
                                running = False
                                show_results = False
                            if retry_same_button.is_clicked(event):
                                choice = "retry_same"
                                post_race_running = False
                                running = False
                                show_results = False
                            if select_new_button.is_clicked(event):
                                choice = "select_new"
                                post_race_running = False
                                running = False
                                show_results = False
                            if back_to_results_button.is_clicked(event):
                                choice = "back_to_results"
                                post_race_running = False
                            if end_game_button.is_clicked(event):
                                choice = "end"
                                post_race_running = False
                                running = False
                                show_results = False
                            if mute_button.is_clicked(event, is_muted, RACE_MUSIC_PATH)[0]:
                                pass
                            # 5th button: Run tournament with top 5
                            if tournament_button.is_clicked(event):
                                top5 = finishers[:5]
                                return top5, "tournament_with_top5", is_muted

                        render_race_screen(screen, sprotos, race_distance, time_elapsed, None, winner, track_surface, buttons, current_background, flash_timer, is_muted, lane_height=lane_height)
                        pygame.display.flip()

                if choice in ["retry_same", "select_new", "end"]:
                    if choice in ["select_new", "end"]:
                        pygame.mixer.music.stop()
                        logging.info("Race music stopped.")
                    if choice == "retry_same":
                        if os.path.exists(RACE_MUSIC_PATH):
                            try:
                                pygame.mixer.music.load(RACE_MUSIC_PATH)
                                pygame.mixer.music.set_volume(0 if is_muted else 0.35)
                                if not is_muted:
                                    pygame.mixer.music.play(loops=-1)
                                    logging.info(f"Playing race music (retry): {RACE_MUSIC_PATH} at 35% volume")
                                else:
                                    logging.info("Race music loaded but muted (retry).")
                            except Exception as e:
                                logging.error(f"Error loading race music (retry) '{RACE_MUSIC_PATH}': {e}")
        else:
            render_race_screen(screen, sprotos, race_distance, time_elapsed, None, winner, track_surface, [mute_button], current_background, flash_timer, is_muted, lane_height=lane_height)

            # Draw live leaderboard table after 9.1 seconds
            if show_leaderboard:
                # Sort by finish_place if finished, else by position
                def sort_key(s):
                    return (s.finish_place if s.finished and s.finish_place is not None else 999, -s.position)
                leaders = sorted(sprotos, key=sort_key)[:5]
                table_x = 10
                table_y = 10
                row_height = 48
                col1_width = 160
                col2_width = 70
                table_width = col1_width + col2_width
                table_height = row_height * 5 + 30

                # Draw 50% transparent black background using a Surface with alpha
                table_surface = pygame.Surface((table_width, table_height), pygame.SRCALPHA)
                table_surface.fill((0, 0, 0, 128))  # 128 alpha = 50% transparent
                screen.blit(table_surface, (table_x, table_y))

                # Draw headers
                draw_text_with_shadow(screen, "Racer", small_font, YELLOW, (table_x + 10, table_y + 5))
                draw_text_with_shadow(screen, "Place", small_font, YELLOW, (table_x + col1_width + 10, table_y + 5))
                # Draw rows
                for i, s in enumerate(leaders):
                    row_y = table_y + 30 + i * row_height
                    # Racer image and name
                    screen.blit(s.sprite, (table_x + 5, row_y))
                    draw_text_with_shadow(screen, s.name, small_font, WHITE, (table_x + 60, row_y + 12))
                    # Place
                    if s.finished and s.finish_place is not None:
                        place_num = s.finish_place
                    else:
                        place_num = i + 1
                    last_digit = place_num % 10
                    if 10 <= place_num % 100 <= 13:
                        suffix = "th"
                    elif last_digit == 1:
                        suffix = "st"
                    elif last_digit == 2:
                        suffix = "nd"
                    elif last_digit == 3:
                        suffix = "rd"
                    else:
                        suffix = "th"
                    place_text = f"{place_num}{suffix}"
                    draw_text_with_shadow(screen, place_text, small_font, WHITE, (table_x + col1_width + 20, row_y + 12))

            pygame.display.flip()

    return winner, choice, is_muted