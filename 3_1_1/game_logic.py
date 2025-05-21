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
    import textwrap
    clock = pygame.time.Clock()
    running = True

    # Each sproto gets 100 HP, 20 PP (mana)
    hp = [100, 100]
    max_hp = [100, 100]
    pp = [20, 20]
    max_pp = [20, 20]
    player = 0
    npc = 1
    turn = random.choice([player, npc])
    action_menu = ["Attack", "Magic", "Flee", "Item"]
    selected_action = 0
    sproto_juice = [1, 1]
    menu_font = pygame.font.SysFont("arial", 32, bold=True)
    hp_font = pygame.font.SysFont("arial", 18, bold=True)  # Smaller font for under-image text
    msg_font = pygame.font.SysFont("arial", 26, bold=True)
    damage_font = pygame.font.SysFont("arial", 36, bold=True)
    log_font = pygame.font.SysFont("arial", 20)
    message = ""
    message_timer = 0
    combat_text = ""
    combat_text_timer = 0
    damage_display = [None, None]  # (damage, timer)
    crit_display = [None, None]    # (timer) for "Crit!" floating text
    miss_display = [None, None]    # (timer) for "Miss!" floating text
    dodge_display = [None, None]   # (timer) for "Dodge!" floating text
    ANIMATION_NONE = 0
    ANIMATION_FIGHT = 1
    ANIMATION_MAGIC = 2
    animation_state = ANIMATION_NONE
    animation_timer = 0
    anim_actor = None  # 0 or 1
    anim_target = None
    anim_progress = 0.0
    anim_damage = 0

    # Log for actions
    action_log = []
    log_scroll = 0
    LOG_LINES = 5

    # Pre-scale images for animation (increase by 2x)
    orig_size = sprotos[0].sprite.get_size()
    scale_size = (int(orig_size[0] * 2.0), int(orig_size[1] * 2.0))
    big_sprites = [pygame.transform.smoothscale(s.sprite, scale_size) for s in sprotos]
    sprite_w, sprite_h = scale_size

    # Define image positions at the top level so they are accessible everywhere
    p_img_x, p_img_y = 140, 420
    n_img_x, n_img_y = 880, 120

    # Pick a random background from race backgrounds
    from assets import load_race_backgrounds
    race_backgrounds, single_bg_options = load_race_backgrounds()
    fight_bg = None
    if single_bg_options:
        fight_bg = random.choice(single_bg_options)
        fight_bg = pygame.transform.scale(fight_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
    else:
        fight_bg = None

    # --- Show who attacks first ---
    first_attacker = sprotos[turn].name
    second_attacker = sprotos[1 - turn].name
    announce_font = pygame.font.SysFont("arial", 44, bold=True)
    # Split announce text into two lines for better fit
    announce_text1 = f"{first_attacker} got the drop on {second_attacker},"
    announce_text2 = f"{first_attacker} gets to attack first."
    announce_surf1 = announce_font.render(announce_text1, True, YELLOW)
    announce_surf2 = announce_font.render(announce_text2, True, YELLOW)
    announce_rect1 = announce_surf1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
    announce_rect2 = announce_surf2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
    if fight_bg:
        screen.blit(fight_bg, (0, 0))
    else:
        screen.fill((80, 160, 80))
    screen.blit(announce_surf1, announce_rect1)
    screen.blit(announce_surf2, announce_rect2)
    pygame.display.flip()
    # Non-blocking wait with event processing
    announce_timer = 0
    announce_duration = 1800
    announce_start_ticks = pygame.time.get_ticks()
    while announce_timer < announce_duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
        pygame.time.delay(10)
        announce_timer = pygame.time.get_ticks() - announce_start_ticks

    # --- NPC first action delay if NPC goes first ---
    if turn == npc:
        npc_action_delay = 2.0
    else:
        npc_action_delay = 0  # Ensure variable is always defined

    # Button setup for end-of-battle
    button_font = pygame.font.SysFont("arial", 28, bold=True)
    button_w, button_h = 200, 60
    restart_button_rect = pygame.Rect(SCREEN_WIDTH // 2 - button_w - 20, SCREEN_HEIGHT // 2 + 80, button_w, button_h)
    end_button_rect = pygame.Rect(SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 2 + 80, button_w, button_h)

    def draw_health_bar(x, y, hp_val, max_hp_val, width=180, height=18):
        bar_w = int(width * max(0, min(1, hp_val / max_hp_val)))
        pygame.draw.rect(screen, (60, 60, 60), (x, y, width, height))
        pygame.draw.rect(screen, (0, 220, 0), (x, y, bar_w, height))
        pygame.draw.rect(screen, WHITE, (x, y, width, height), 2)

    # Add: Magic and Item submenu state and options
    MAGIC_MENU = False
    magic_menu_options = ["Potter Bolt"]
    magic_menu_selected = 0

    ITEM_MENU = False
    item_menu_options = ["Sproto Juice"]
    item_menu_selected = 0

    # Fight log file
    FIGHT_LOG_PATH = os.path.join(os.path.dirname(__file__), "sproto_fight.log")
    def log_fight_entry(entry):
        with open(FIGHT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

    def draw_battle_screen(anim_offset=None, bolt_pos=None, bolt_path=None, winner=None, show_buttons=False):
        # Draw background
        if fight_bg:
            screen.blit(fight_bg, (0, 0))
        else:
            screen.fill((80, 160, 80))

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
        pygame.draw.rect(screen, WHITE, (p_img_x + p_offset[0], p_img_y + p_offset[1], sprite_w, sprite_h), 3)
        # Draw NPC sprite and border
        screen.blit(big_sprites[1], (n_img_x + n_offset[0], n_img_y + n_offset[1]))
        pygame.draw.rect(screen, WHITE, (n_img_x + n_offset[0], n_img_y + n_offset[1], sprite_w, sprite_h), 3)

        # Draw health bars above both characters (follow animation)
        draw_health_bar(p_img_x + p_offset[0], p_img_y - 28 + p_offset[1], hp[0], max_hp[0], width=sprite_w)
        draw_health_bar(n_img_x + n_offset[0], n_img_y - 28 + n_offset[1], hp[1], max_hp[1], width=sprite_w)

        # Draw yellow triangle above active player's HP bar (follows animation)
        triangle_height = 18
        triangle_width = 24
        if turn == player:
            tri_x = p_img_x + p_offset[0] + sprite_w // 2
            tri_y = p_img_y - 38 + p_offset[1]
        else:
            tri_x = n_img_x + n_offset[0] + sprite_w // 2
            tri_y = n_img_y - 38 + n_offset[1]
        pygame.draw.polygon(
            screen, YELLOW,
            [(tri_x, tri_y), (tri_x - triangle_width // 2, tri_y + triangle_height), (tri_x + triangle_width // 2, tri_y + triangle_height)]
        )

        # Draw name under player image, small font
        name_surf = hp_font.render(f"{sprotos[0].name}", True, WHITE)
        name_rect = name_surf.get_rect(center=(p_img_x + sprite_w // 2, p_img_y + sprite_h + 18))
        screen.blit(name_surf, name_rect)
        name_surf2 = hp_font.render(f"{sprotos[1].name}", True, WHITE)
        name_rect2 = name_surf2.get_rect(center=(n_img_x + sprite_w // 2, n_img_y + sprite_h + 18))
        screen.blit(name_surf2, name_rect2)

        # Draw HP/PP under name with color and shadow, inside a cell with transparent black background
        status_font = pygame.font.SysFont("arial", 16, bold=True)
        # Player
        hp_text = f"HP: {hp[0]}/{max_hp[0]}"
        pp_text = f"PP: {pp[0]}/{max_pp[0]}"
        status_cell_w, status_cell_h = 140, 32
        status_x = p_img_x + sprite_w // 2 - status_cell_w // 2
        status_y = p_img_y + sprite_h + 28
        status_surf = pygame.Surface((status_cell_w, status_cell_h), pygame.SRCALPHA)
        status_surf.fill((0, 0, 0, 160))
        screen.blit(status_surf, (status_x, status_y))
        draw_text_with_shadow(screen, hp_text, status_font, (0, 220, 0), (status_x + 12, status_y + 4))
        draw_text_with_shadow(screen, pp_text, status_font, (0, 120, 255), (status_x + 12, status_y + 18))

        # NPC
        hp_text2 = f"HP: {hp[1]}/{max_hp[1]}"
        pp_text2 = f"PP: {pp[1]}/{max_pp[1]}"
        status_x2 = n_img_x + sprite_w // 2 - status_cell_w // 2
        status_y2 = n_img_y + sprite_h + 28
        status_surf2 = pygame.Surface((status_cell_w, status_cell_h), pygame.SRCALPHA)
        status_surf2.fill((0, 0, 0, 160))
        screen.blit(status_surf2, (status_x2, status_y2))
        draw_text_with_shadow(screen, hp_text2, status_font, (0, 220, 0), (status_x2 + 12, status_y2 + 4))
        draw_text_with_shadow(screen, pp_text2, status_font, (0, 120, 255), (status_x2 + 12, status_y2 + 18))

        # Draw damage numbers above character
        for idx in [0, 1]:
            if damage_display[idx] and damage_display[idx][1] > 0:
                dmg, timer = damage_display[idx]
                color = RED if dmg > 0 else GREEN
                dmg_text = f"-{dmg}" if dmg > 0 else f"+{abs(dmg)}"
                x = p_img_x + sprite_w // 2 if idx == 0 else n_img_x + sprite_w // 2
                y = (p_img_y if idx == 0 else n_img_y) - 40
                text_surf = damage_font.render(dmg_text, True, color)
                text_rect = text_surf.get_rect(center=(x, y))
                screen.blit(text_surf, text_rect)
            # Draw "Crit!" floating text above attacker if crit_display[idx] is active
            if crit_display[idx] and crit_display[idx] > 0:
                x = p_img_x + sprite_w // 2 if idx == 0 else n_img_x + sprite_w // 2
                y = (p_img_y if idx == 0 else n_img_y) - 80
                crit_font = pygame.font.SysFont("arial", 32, bold=True)
                crit_surf = crit_font.render("Crit!", True, YELLOW)
                crit_rect = crit_surf.get_rect(center=(x, y))
                screen.blit(crit_surf, crit_rect)
            # Draw "Miss!" floating text above attacker if miss_display[idx] is active
            if miss_display[idx] and miss_display[idx] > 0:
                x = p_img_x + sprite_w // 2 if idx == 0 else n_img_x + sprite_w // 2
                y = (p_img_y if idx == 0 else n_img_y) - 80
                miss_font = pygame.font.SysFont("arial", 32, bold=True)
                miss_surf = miss_font.render("Miss!", True, RED)
                miss_rect = miss_surf.get_rect(center=(x, y))
                screen.blit(miss_surf, miss_rect)
            # Draw "Dodge!" floating text above defender if dodge_display[idx] is active
            if dodge_display[idx] and dodge_display[idx] > 0:
                x = p_img_x + sprite_w // 2 if idx == 0 else n_img_x + sprite_w // 2
                y = (p_img_y if idx == 0 else n_img_y) - 80
                dodge_font = pygame.font.SysFont("arial", 32, bold=True)
                dodge_surf = dodge_font.render("Dodge!", True, BLUE)
                dodge_rect = dodge_surf.get_rect(center=(x, y))
                screen.blit(dodge_surf, dodge_rect)
        # Draw projectile for Potter Bolt
        if bolt_pos and bolt_path:
            for i in range(len(bolt_path) - 1):
                pygame.draw.line(screen, YELLOW, bolt_path[i], bolt_path[i + 1], 8)
            pygame.draw.circle(screen, YELLOW, bolt_pos, 18)

        # Draw action log (top left)
        log_box_x, log_box_y, log_box_w, log_box_h = 20, 20, 520, 180  # Wider log box
        pygame.draw.rect(screen, (0, 0, 0, 180), (log_box_x, log_box_y, log_box_w, log_box_h))
        pygame.draw.rect(screen, WHITE, (log_box_x, log_box_y, log_box_w, log_box_h), 2)
        # Wrap log text to fit inside the box
        max_log_chars = 60
        visible_logs = []
        for entry in action_log[max(0, len(action_log) - LOG_LINES - log_scroll):len(action_log) - log_scroll if log_scroll > 0 else None]:
            wrapped = textwrap.wrap(entry, max_log_chars)
            visible_logs.extend(wrapped)
        visible_logs = visible_logs[-LOG_LINES:]
        for i, log_entry in enumerate(visible_logs):
            screen.blit(log_font.render(log_entry, True, WHITE), (log_box_x + 10, log_box_y + 10 + i * 28))
        # Draw scroll indicators if needed
        if log_scroll < max(0, len(action_log) - LOG_LINES):
            screen.blit(log_font.render("▼", True, YELLOW), (log_box_x + log_box_w - 30, log_box_y + log_box_h - 28))
        if log_scroll > 0:
            screen.blit(log_font.render("▲", True, YELLOW), (log_box_x + log_box_w - 30, log_box_y + 8))

        # Draw menu box (bottom, moved lower to avoid overlap)
        menu_box_y = 700
        pygame.draw.rect(screen, BLACK, (200, menu_box_y, 800, 90))
        pygame.draw.rect(screen, WHITE, (200, menu_box_y, 800, 90), 3)
        if MAGIC_MENU:
            for i, label in enumerate(magic_menu_options):
                color = YELLOW if i == magic_menu_selected else WHITE
                screen.blit(menu_font.render(label, True, color), (340 + i * 200, menu_box_y + 25))
            back_color = YELLOW if magic_menu_selected == len(magic_menu_options) else WHITE
            screen.blit(menu_font.render("Back", True, back_color), (340 + len(magic_menu_options) * 200, menu_box_y + 25))
        elif ITEM_MENU:
            for i, label in enumerate(item_menu_options):
                color = YELLOW if i == item_menu_selected else WHITE
                screen.blit(menu_font.render(label, True, color), (340 + i * 200, menu_box_y + 25))
            back_color = YELLOW if item_menu_selected == len(item_menu_options) else WHITE
            screen.blit(menu_font.render("Back", True, back_color), (340 + len(item_menu_options) * 200, menu_box_y + 25))
        else:
            for i, label in enumerate(action_menu):
                color = YELLOW if i == selected_action else WHITE
                screen.blit(menu_font.render(label, True, color), (240 + i * 200, menu_box_y + 25))

        # Draw turn indicator (above menu)
        turn_text = f"{sprotos[turn].name}'s turn!"
        screen.blit(menu_font.render(turn_text, True, YELLOW), (SCREEN_WIDTH // 2 - 120, menu_box_y - 40))

        # Draw end-of-battle buttons if needed
        if show_buttons and winner:
            # Draw winner text
            winner_font = pygame.font.SysFont("arial", 40, bold=True)
            winner_text = f"{winner} wins!"
            winner_surf = winner_font.render(winner_text, True, YELLOW)
            winner_rect = winner_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(winner_surf, winner_rect)
            # Draw buttons
            pygame.draw.rect(screen, GREEN, restart_button_rect)
            pygame.draw.rect(screen, RED, end_button_rect)
            pygame.draw.rect(screen, WHITE, restart_button_rect, 3)
            pygame.draw.rect(screen, WHITE, end_button_rect, 3)
            restart_surf = button_font.render("Restart", True, BLACK)
            end_surf = button_font.render("End Game", True, BLACK)
            screen.blit(restart_surf, restart_surf.get_rect(center=restart_button_rect.center))
            screen.blit(end_surf, end_surf.get_rect(center=end_button_rect.center))
        pygame.display.flip()

    # --- Show who attacks first ---
    first_attacker = sprotos[turn].name
    second_attacker = sprotos[1 - turn].name
    announce_font = pygame.font.SysFont("arial", 44, bold=True)
    # Split announce text into two lines for better fit
    announce_text1 = f"{first_attacker} got the drop on {second_attacker},"
    announce_text2 = f"{first_attacker} gets to attack first."
    announce_surf1 = announce_font.render(announce_text1, True, YELLOW)
    announce_surf2 = announce_font.render(announce_text2, True, YELLOW)
    announce_rect1 = announce_surf1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
    announce_rect2 = announce_surf2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
    if fight_bg:
        screen.blit(fight_bg, (0, 0))
    else:
        screen.fill((80, 160, 80))
    screen.blit(announce_surf1, announce_rect1)
    screen.blit(announce_surf2, announce_rect2)
    pygame.display.flip()
    # Non-blocking wait with event processing
    announce_timer = 0
    announce_duration = 1800
    announce_start_ticks = pygame.time.get_ticks()
    while announce_timer < announce_duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
        pygame.time.delay(10)
        announce_timer = pygame.time.get_ticks() - announce_start_ticks

    # --- NPC first action delay if NPC goes first ---
    if turn == npc:
        npc_action_delay = 2.0
    else:
        npc_action_delay = 0  # Ensure variable is always defined

    # --- Main game loop ---
    while running:
        # Handle animation state
        if animation_state == ANIMATION_FIGHT:
            anim_time = 0.7
            dt = clock.tick(60) / 1000.0
            animation_timer += dt
            progress = animation_timer / anim_time
            if progress < 0.25:
                offset_x = int(120 * progress / 0.25)
                offset_y = 0
            elif progress < 0.5:
                offset_x = 120
                offset_y = int(-40 * (progress - 0.25) / 0.25)
            elif progress < 0.7:
                offset_x = 120
                offset_y = -40
            else:
                offset_x = int(120 * (1 - (progress - 0.7) / 0.3))
                offset_y = int(-40 * (1 - (progress - 0.7) / 0.3))
            if anim_actor == player:
                anim_offset = [offset_x, offset_y]
            else:
                anim_offset = [-offset_x, offset_y]
            draw_battle_screen(anim_offset=anim_offset)
            if animation_timer >= anim_time:
                hp[anim_target] = max(0, hp[anim_target] - anim_damage)
                damage_display[anim_target] = (anim_damage, 3.0)
                # Only append a message here if not already appended above
                # (Do not append again, as the combat_text is already added in the logic above)
                animation_state = ANIMATION_NONE
                animation_timer = 0
                turn = 1 - anim_actor
            continue
        elif animation_state == ANIMATION_MAGIC:
            anim_time = 0.8
            dt = clock.tick(60) / 1000.0
            animation_timer += dt
            progress = min(animation_timer / anim_time, 1.0)
            # Use p_img_x, p_img_y, n_img_x, n_img_y as needed
            if anim_actor == player:
                start = (p_img_x + sprite_w, p_img_y + sprite_h // 2)
                end = (n_img_x, n_img_y + sprite_h // 2)
            else:
                start = (n_img_x, n_img_y + sprite_h // 2)
                end = (p_img_x + sprite_w, p_img_y + sprite_h // 2)
            bolt_path = []
            steps = 8
            for i in range(steps + 1):
                t = i / steps
                x = int(start[0] + (end[0] - start[0]) * t)
                y = int(start[1] + (end[1] - start[1]) * t)
                if i not in [0, steps]:
                    y += random.randint(-18, 18)
                bolt_path.append((x, y))
            head_idx = int(progress * steps)
            head_idx = min(head_idx, steps)
            bolt_pos = bolt_path[head_idx]
            draw_battle_screen(bolt_pos=bolt_pos, bolt_path=bolt_path[:head_idx+1])
            if animation_timer >= anim_time:
                hp[anim_target] = max(0, hp[anim_target] - anim_damage)
                damage_display[anim_target] = (anim_damage, 3.0)
                combat_text = f"{sprotos[anim_actor].name} casts Potter Bolt! {sprotos[anim_target].name} takes {anim_damage} damage."
                combat_text_timer = 2.0
                action_log.append(combat_text)
                animation_state = ANIMATION_NONE
                animation_timer = 0
                turn = 1 - anim_actor
            continue

        draw_battle_screen()

        # Update damage/crit/miss/dodge display timers
        for idx in [0, 1]:
            if damage_display[idx]:
                dmg, timer = damage_display[idx]
                timer -= clock.get_time() / 1000.0
                if timer <= 0:
                    damage_display[idx] = None
                else:
                    damage_display[idx] = (dmg, timer)
            if crit_display[idx]:
                crit_display[idx] -= clock.get_time() / 1000.0
                if crit_display[idx] <= 0:
                    crit_display[idx] = None
            if miss_display[idx]:
                miss_display[idx] -= clock.get_time() / 1000.0
                if miss_display[idx] <= 0:
                    miss_display[idx] = None
            if dodge_display[idx]:
                dodge_display[idx] -= clock.get_time() / 1000.0
                if dodge_display[idx] <= 0:
                    dodge_display[idx] = None

        # Update combat text timer
        if combat_text:
            combat_text_timer -= clock.get_time() / 1000.0
            if combat_text_timer <= 0:
                combat_text = ""

        # Check for win
        if hp[0] <= 0 or hp[1] <= 0:
            winner = sprotos[0].name if hp[1] <= 0 else sprotos[1].name
            log_fight_entry(f"{winner} wins!")
            action_log.append(f"{winner} wins!")
            # Show winner and buttons, wait for user input
            waiting_for_choice = True
            while waiting_for_choice:
                draw_battle_screen(winner=winner, show_buttons=True)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mx, my = event.pos
                        if restart_button_rect.collidepoint(mx, my):
                            # Restart round: reset HP, PP, juice, logs, randomize first attacker
                            hp[:] = [100, 100]
                            pp[:] = [20, 20]
                            sproto_juice[:] = [1, 1]
                            damage_display[:] = [None, None]
                            action_log.clear()
                            combat_text = ""
                            combat_text_timer = 0
                            turn = random.choice([player, npc])
                            # Announce who attacks first again
                            first_attacker = sprotos[turn].name
                            second_attacker = sprotos[1 - turn].name
                            announce_font = pygame.font.SysFont("arial", 44, bold=True)
                            # Split announce text into two lines for better fit
                            announce_text1 = f"{first_attacker} got the drop on {second_attacker},"
                            announce_text2 = f"{first_attacker} gets to attack first."
                            announce_surf1 = announce_font.render(announce_text1, True, YELLOW)
                            announce_surf2 = announce_font.render(announce_text2, True, YELLOW)
                            announce_rect1 = announce_surf1.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
                            announce_rect2 = announce_surf2.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 30))
                            if fight_bg:
                                screen.blit(fight_bg, (0, 0))
                            else:
                                screen.fill((80, 160, 80))
                            screen.blit(announce_surf1, announce_rect1)
                            screen.blit(announce_surf2, announce_rect2)
                            pygame.display.flip()
                            # Non-blocking wait with event processing
                            announce_timer = 0
                            announce_duration = 1800
                            announce_start_ticks = pygame.time.get_ticks()
                            while announce_timer < announce_duration:
                                for event in pygame.event.get():
                                    if event.type == pygame.QUIT:
                                        return
                                pygame.time.delay(10)
                                announce_timer = pygame.time.get_ticks() - announce_start_ticks
                            waiting_for_choice = False
                        elif end_button_rect.collidepoint(mx, my):
                            return  # End game, go back to selection
                clock.tick(30)
            continue

        if animation_state == ANIMATION_NONE:
            if turn == player:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                        return
                    # Mouse support for menu selection
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mx, my = event.pos
                        menu_box_y = 700
                        if not MAGIC_MENU and not ITEM_MENU:
                            for i in range(len(action_menu)):
                                rect = pygame.Rect(240 + i * 200, menu_box_y + 25, 180, 40)
                                if rect.collidepoint(mx, my):
                                    selected_action = i
                                    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
                                    pygame.event.post(event)
                        elif MAGIC_MENU:
                            for i in range(len(magic_menu_options)):
                                rect = pygame.Rect(340 + i * 200, menu_box_y + 25, 180, 40)
                                if rect.collidepoint(mx, my):
                                    magic_menu_selected = i
                                    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
                                    pygame.event.post(event)
                            back_rect = pygame.Rect(340 + len(magic_menu_options) * 200, menu_box_y + 25, 180, 40)
                            if back_rect.collidepoint(mx, my):
                                magic_menu_selected = len(magic_menu_options)
                                event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
                                pygame.event.post(event)
                        elif ITEM_MENU:
                            for i in range(len(item_menu_options)):
                                rect = pygame.Rect(340 + i * 200, menu_box_y + 25, 180, 40)
                                if rect.collidepoint(mx, my):
                                    item_menu_selected = i
                                    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
                                    pygame.event.post(event)
                            back_rect = pygame.Rect(340 + len(item_menu_options) * 200, menu_box_y + 25, 180, 40)
                            if back_rect.collidepoint(mx, my):
                                item_menu_selected = len(item_menu_options)
                                event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
                                pygame.event.post(event)
                    elif event.type == pygame.KEYDOWN:
                        if not MAGIC_MENU and not ITEM_MENU:
                            if event.key == pygame.K_RIGHT:
                                selected_action = (selected_action + 1) % len(action_menu)
                            elif event.key == pygame.K_LEFT:
                                selected_action = (selected_action - 1) % len(action_menu)
                            elif event.key == pygame.K_UP:
                                if log_scroll > 0:
                                    log_scroll -= 1
                            elif event.key == pygame.K_DOWN:
                                if log_scroll < max(0, len(action_log) - LOG_LINES):
                                    log_scroll += 1
                            elif event.key == pygame.K_RETURN:
                                if action_menu[selected_action] == "Attack":
                                    roll = random.random()
                                    miss = roll < 0.10
                                    dodge = not miss and random.random() < 0.10
                                    crit = not miss and not dodge and random.random() < 0.20
                                    dmg = random.randint(8, 10)
                                    if miss:
                                        dmg = 0
                                        combat_text = f"{sprotos[player].name} missed!"
                                        combat_text_timer = 1.5
                                        action_log.append(combat_text)
                                        # Show "Miss!" over attacker
                                        miss_display[player] = 1.0
                                        # Still do fight animation
                                        animation_state = ANIMATION_FIGHT
                                        animation_timer = 0
                                        anim_actor = player
                                        anim_target = npc
                                        anim_damage = dmg
                                        log_fight_entry(combat_text)
                                        continue
                                    elif dodge:
                                        dmg = 0
                                        combat_text = f"{sprotos[npc].name} dodged the attack!"
                                        combat_text_timer = 1.5
                                        action_log.append(combat_text)
                                        # Show "Dodge!" over defender
                                        dodge_display[npc] = 1.0
                                        # Still do fight animation
                                        animation_state = ANIMATION_FIGHT
                                        animation_timer = 0
                                        anim_actor = player
                                        anim_target = npc
                                        anim_damage = dmg
                                        log_fight_entry(combat_text)
                                        continue
                                    else:
                                        if crit:
                                            dmg = int(dmg * 2.5)
                                            combat_text = f"Critical hit! {sprotos[player].name} deals {dmg}!"
                                            combat_text_timer = 1.5
                                            action_log.append(combat_text)
                                            crit_display[player] = 1.0
                                        else:
                                            combat_text = f"{sprotos[player].name} attacks! {sprotos[npc].name} takes {dmg} damage."
                                            combat_text_timer = 1.5
                                            action_log.append(combat_text)
                                        animation_state = ANIMATION_FIGHT
                                        animation_timer = 0
                                        anim_actor = player
                                        anim_target = npc
                                        anim_damage = dmg
                                        log_fight_entry(combat_text)
                                    continue
                                elif action_menu[selected_action] == "Magic":
                                    MAGIC_MENU = True
                                    magic_menu_selected = 0
                                elif action_menu[selected_action] == "Flee":
                                    log_fight_entry(f"{sprotos[player].name} fled the battle.")
                                    return  # Go back to selection screen
                                elif action_menu[selected_action] == "Item":
                                    ITEM_MENU = True
                                    item_menu_selected = 0
                            elif event.key == pygame.K_ESCAPE:
                                return
                        elif MAGIC_MENU:
                            if event.key == pygame.K_RIGHT:
                                magic_menu_selected = (magic_menu_selected + 1) % (len(magic_menu_options) + 1)
                            elif event.key == pygame.K_LEFT:
                                magic_menu_selected = (magic_menu_selected - 1) % (len(magic_menu_options) + 1)
                            elif event.key == pygame.K_RETURN:
                                if magic_menu_selected == len(magic_menu_options):
                                    MAGIC_MENU = False
                                elif magic_menu_selected == 0:  # Only one spell for now
                                    if pp[player] >= 10:
                                        dmg = random.randint(33, 39)
                                        pp[player] -= 10
                                        animation_state = ANIMATION_MAGIC
                                        animation_timer = 0
                                        anim_actor = player
                                        anim_target = npc
                                        anim_damage = dmg
                                        MAGIC_MENU = False
                                        log_fight_entry(f"{sprotos[player].name} casts Potter Bolt! {sprotos[npc].name} takes {dmg} damage.")
                                    else:
                                        action_log.append("Not enough PP for Potter Bolt!")
                                        MAGIC_MENU = False
                            elif event.key == pygame.K_ESCAPE:
                                MAGIC_MENU = False
                        elif ITEM_MENU:
                            if event.key == pygame.K_RIGHT:
                                item_menu_selected = (item_menu_selected + 1) % (len(item_menu_options) + 1)
                            elif event.key == pygame.K_LEFT:
                                item_menu_selected = (item_menu_selected - 1) % (len(item_menu_options) + 1)
                            elif event.key == pygame.K_RETURN:
                                if item_menu_selected == len(item_menu_options):
                                    ITEM_MENU = False
                                elif item_menu_selected == 0:  # Sproto Juice
                                    if sproto_juice[player] > 0:
                                        heal = 25
                                        hp[player] = min(max_hp[player], hp[player] + heal)
                                        sproto_juice[player] -= 1
                                        damage_display[player] = (-heal, 3.0)
                                        action_log.append(f"{sprotos[player].name} uses Sproto Juice! Recovers {heal} HP.")
                                        log_fight_entry(f"{sprotos[player].name} uses Sproto Juice! Recovers {heal} HP.")
                                        turn = npc
                                        ITEM_MENU = False  # <-- Close the item menu after use
                                    else:
                                        action_log.append("No Sproto Juice left!")
                                        ITEM_MENU = False
                            elif event.key == pygame.K_ESCAPE:
                                ITEM_MENU = False
            else:
                # --- NPC action delay logic ---
                if 'npc_action_delay' not in locals():
                    npc_action_delay = 0
                if npc_action_delay > 0:
                    npc_action_delay -= clock.get_time() / 1000.0
                    clock.tick(60)
                    continue
                roll = random.random()
                miss = roll < 0.10
                dodge = not miss and random.random() < 0.10
                crit = not miss and not dodge and random.random() < 0.20
                dmg = random.randint(8, 10)
                if miss:
                    dmg = 0
                    combat_text = f"{sprotos[npc].name} missed!"
                    combat_text_timer = 1.5
                    action_log.append(combat_text)
                    miss_display[npc] = 1.0
                    animation_state = ANIMATION_FIGHT
                    animation_timer = 0
                    anim_actor = npc
                    anim_target = player
                    anim_damage = dmg
                    log_fight_entry(combat_text)
                    npc_action_delay = 1.5
                    continue
                elif dodge:
                    dmg = 0
                    combat_text = f"{sprotos[player].name} dodged the attack!"
                    combat_text_timer = 1.5
                    action_log.append(combat_text)
                    dodge_display[player] = 1.0
                    animation_state = ANIMATION_FIGHT
                    animation_timer = 0
                    anim_actor = npc
                    anim_target = player
                    anim_damage = dmg
                    log_fight_entry(combat_text)
                    npc_action_delay = 1.5
                    continue
                else:
                    if crit:
                        dmg = int(dmg * 2.5)
                        combat_text = f"Critical hit! {sprotos[npc].name} deals {dmg}!"
                        combat_text_timer = 1.5
                        action_log.append(combat_text)
                        crit_display[npc] = 1.0
                    else:
                        combat_text = f"{sprotos[npc].name} attacks! {sprotos[player].name} takes {dmg} damage."
                        combat_text_timer = 1.5
                        action_log.append(combat_text)
                    animation_state = ANIMATION_FIGHT
                    animation_timer = 0
                    anim_actor = npc
                    anim_target = player
                    anim_damage = dmg
                    log_fight_entry(combat_text)
                    npc_action_delay = 1.5
                    continue

        clock.tick(60)