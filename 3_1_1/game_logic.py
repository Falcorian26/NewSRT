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
                table_height = row_height + 30

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

def run_pocket_sprotos_mode(screen, sprotos):
    import pygame
    clock = pygame.time.Clock()
    running = True

    # Each sproto gets 100 HP
    hp = [100, 100]
    max_hp = [100, 100]
    player = 0
    npc = 1
    turn = random.choice([player, npc])
    action_menu = ["Attack", "Magic", "Flee", "Item"]
    selected_action = 0
    sproto_juice = [1, 1]
    menu_font = pygame.font.SysFont("arial", 32, bold=True)
    hp_font = pygame.font.SysFont("arial", 28, bold=True)
    msg_font = pygame.font.SysFont("arial", 26, bold=True)
    damage_font = pygame.font.SysFont("arial", 36, bold=True)
    message = ""
    message_timer = 0
    combat_text = ""
    combat_text_timer = 0
    damage_display = [None, None]  # (damage, timer)
    ANIMATION_NONE = 0
    ANIMATION_FIGHT = 1
    ANIMATION_MAGIC = 2
    animation_state = ANIMATION_NONE
    animation_timer = 0
    anim_actor = None  # 0 or 1
    anim_target = None
    anim_progress = 0.0
    anim_damage = 0

    # Pre-scale images for animation
    big_sprite_size = (180, 180)
    big_sprites = [pygame.transform.smoothscale(s.sprite, big_sprite_size) for s in sprotos]

    def draw_battle_screen(anim_offset=None, bolt_pos=None, bolt_path=None):
        screen.fill((80, 160, 80))
        # Draw player (bottom left)
        p_img_x, p_img_y = 140, 420
        n_img_x, n_img_y = 880, 120
        # Animation offset
        p_offset = [0, 0]
        n_offset = [0, 0]
        if anim_offset:
            if anim_actor == player:
                p_offset = anim_offset
            else:
                n_offset = anim_offset

        # Draw player sprite and border
        screen.blit(big_sprites[0], (p_img_x + p_offset[0], p_img_y + p_offset[1]))
        pygame.draw.rect(screen, WHITE, (p_img_x + p_offset[0], p_img_y + p_offset[1], 180, 180), 4)
        screen.blit(hp_font.render(f"{sprotos[0].name}", True, WHITE), (p_img_x, p_img_y + 190))
        screen.blit(hp_font.render(f"HP: {hp[0]}", True, WHITE), (p_img_x, p_img_y + 220))
        screen.blit(hp_font.render(f"Juice: {sproto_juice[0]}", True, YELLOW), (p_img_x, p_img_y + 250))

        # Draw NPC sprite and border
        screen.blit(big_sprites[1], (n_img_x + n_offset[0], n_img_y + n_offset[1]))
        pygame.draw.rect(screen, WHITE, (n_img_x + n_offset[0], n_img_y + n_offset[1], 180, 180), 4)
        screen.blit(hp_font.render(f"{sprotos[1].name}", True, WHITE), (n_img_x, n_img_y + 190))
        screen.blit(hp_font.render(f"HP: {hp[1]}", True, WHITE), (n_img_x, n_img_y + 220))
        screen.blit(hp_font.render(f"Juice: {sproto_juice[1]}", True, YELLOW), (n_img_x, n_img_y + 250))

        # Draw damage numbers above character
        for idx in [0, 1]:
            if damage_display[idx] and damage_display[idx][1] > 0:
                dmg, timer = damage_display[idx]
                color = RED if dmg > 0 else GREEN
                dmg_text = f"-{dmg}" if dmg > 0 else f"+{abs(dmg)}"
                x = p_img_x + 90 if idx == 0 else n_img_x + 90
                y = (p_img_y if idx == 0 else n_img_y) - 40
                text_surf = damage_font.render(dmg_text, True, color)
                text_rect = text_surf.get_rect(center=(x, y))
                screen.blit(text_surf, text_rect)

        # Draw projectile for Potter Bolt
        if bolt_pos and bolt_path:
            # Draw a yellow lightning bolt (zigzag)
            for i in range(len(bolt_path) - 1):
                pygame.draw.line(screen, YELLOW, bolt_path[i], bolt_path[i + 1], 8)
            pygame.draw.circle(screen, YELLOW, bolt_pos, 18)

        # Draw combat text at top
        if combat_text:
            screen.blit(msg_font.render(combat_text, True, WHITE), (SCREEN_WIDTH // 2 - 200, 60))

        # Draw menu box (bottom)
        pygame.draw.rect(screen, BLACK, (200, 650, 800, 120))
        pygame.draw.rect(screen, WHITE, (200, 650, 800, 120), 3)
        for i, label in enumerate(action_menu):
            color = YELLOW if i == selected_action else WHITE
            screen.blit(menu_font.render(label, True, color), (240 + i * 200, 690))

        # Draw turn indicator (below menu)
        turn_text = f"{sprotos[turn].name}'s turn!"
        screen.blit(menu_font.render(turn_text, True, YELLOW), (SCREEN_WIDTH // 2 - 120, 600))

        pygame.display.flip()

    while running:
        # Handle animation state
        if animation_state == ANIMATION_FIGHT:
            # Fight animation: run, jump, slash, return
            anim_time = 0.7  # total animation time in seconds
            dt = clock.tick(60) / 1000.0
            animation_timer += dt
            progress = animation_timer / anim_time
            if progress < 0.25:
                # Run forward
                offset_x = int(200 * progress / 0.25)
                offset_y = 0
            elif progress < 0.5:
                # Jump up
                offset_x = 200
                offset_y = int(-80 * (progress - 0.25) / 0.25)
            elif progress < 0.7:
                # Slash (pause at target)
                offset_x = 200
                offset_y = -80
            else:
                # Return to start
                offset_x = int(200 * (1 - (progress - 0.7) / 0.3))
                offset_y = int(-80 * (1 - (progress - 0.7) / 0.3))
            if anim_actor == player:
                anim_offset = [offset_x, offset_y]
            else:
                anim_offset = [-offset_x, offset_y]
            draw_battle_screen(anim_offset=anim_offset)
            if animation_timer >= anim_time:
                # Apply damage and show damage text
                hp[anim_target] = max(0, hp[anim_target] - anim_damage)
                damage_display[anim_target] = (anim_damage, 3.0)
                combat_text = f"{sprotos[anim_actor].name} attacks! {sprotos[anim_target].name} takes {anim_damage} damage."
                combat_text_timer = 2.0
                animation_state = ANIMATION_NONE
                animation_timer = 0
                turn = 1 - anim_actor
            continue
        elif animation_state == ANIMATION_MAGIC:
            # Potter Bolt animation
            anim_time = 0.8
            dt = clock.tick(60) / 1000.0
            animation_timer += dt
            progress = min(animation_timer / anim_time, 1.0)
            # Bolt path: from caster to target
            if anim_actor == player:
                start = (230, 510)
                end = (970, 210)
            else:
                start = (970, 210)
                end = (230, 510)
            # Lightning zigzag
            bolt_path = []
            steps = 8
            for i in range(steps + 1):
                t = i / steps
                x = int(start[0] + (end[0] - start[0]) * t)
                y = int(start[1] + (end[1] - start[1]) * t)
                if i not in [0, steps]:
                    y += random.randint(-18, 18)
                bolt_path.append((x, y))
            # Bolt head position
            head_idx = int(progress * steps)
            head_idx = min(head_idx, steps)
            bolt_pos = bolt_path[head_idx]
            draw_battle_screen(bolt_pos=bolt_pos, bolt_path=bolt_path[:head_idx+1])
            if animation_timer >= anim_time:
                # Apply damage and show damage text
                hp[anim_target] = max(0, hp[anim_target] - anim_damage)
                damage_display[anim_target] = (anim_damage, 3.0)
                combat_text = f"{sprotos[anim_actor].name} casts Potter Bolt! {sprotos[anim_target].name} takes {anim_damage} damage."
                combat_text_timer = 2.0
                animation_state = ANIMATION_NONE
                animation_timer = 0
                turn = 1 - anim_actor
            continue

        # Draw normal battle screen
        draw_battle_screen()

        # Update damage display timers
        for idx in [0, 1]:
            if damage_display[idx]:
                dmg, timer = damage_display[idx]
                timer -= clock.get_time() / 1000.0
                if timer <= 0:
                    damage_display[idx] = None
                else:
                    damage_display[idx] = (dmg, timer)

        # Update combat text timer
        if combat_text:
            combat_text_timer -= clock.get_time() / 1000.0
            if combat_text_timer <= 0:
                combat_text = ""

        # Check for win
        if hp[0] <= 0 or hp[1] <= 0:
            winner = sprotos[0].name if hp[1] <= 0 else sprotos[1].name
            combat_text = f"{winner} wins!"
            draw_battle_screen()
            pygame.time.wait(1800)
            break

        if animation_state == ANIMATION_NONE:
            if turn == player:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        return
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RIGHT:
                            selected_action = (selected_action + 1) % len(action_menu)
                        elif event.key == pygame.K_LEFT:
                            selected_action = (selected_action - 1) % len(action_menu)
                        elif event.key == pygame.K_RETURN:
                            if action_menu[selected_action] == "Attack":
                                dmg = random.randint(15, 20)
                                animation_state = ANIMATION_FIGHT
                                animation_timer = 0
                                anim_actor = player
                                anim_target = npc
                                anim_damage = dmg
                            elif action_menu[selected_action] == "Magic":
                                dmg = random.randint(33, 39)
                                animation_state = ANIMATION_MAGIC
                                animation_timer = 0
                                anim_actor = player
                                anim_target = npc
                                anim_damage = dmg
                            elif action_menu[selected_action] == "Flee":
                                return  # Go back to selection screen
                            elif action_menu[selected_action] == "Item":
                                if sproto_juice[player] > 0:
                                    heal = 25
                                    hp[player] = min(max_hp[player], hp[player] + heal)
                                    sproto_juice[player] -= 1
                                    damage_display[player] = (-heal, 3.0)
                                    combat_text = f"{sprotos[player].name} uses Sproto Juice! Recovers {heal} HP."
                                    combat_text_timer = 2.0
                                    turn = npc
                                else:
                                    combat_text = "No Sproto Juice left!"
                                    combat_text_timer = 2.0
                        elif event.key == pygame.K_ESCAPE:
                            return
            else:
                # NPC always attacks for now, with animation
                dmg = random.randint(15, 20)
                animation_state = ANIMATION_FIGHT
                animation_timer = 0
                anim_actor = npc
                anim_target = player
                anim_damage = dmg

        clock.tick(60)