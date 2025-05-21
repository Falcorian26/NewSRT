import pygame
import logging
import os
from settings import *
from assets import *
from sproto import Sproto
from screens import select_sprotos, show_tournament_results, MuteButton
from game_logic import simulate_race, simulate_all_characters_race, run_pocket_sprotos_mode

def check_missing_images():
    missing_files = []
    for filename in image_filenames:
        file_path = os.path.join(SPROTO_IMAGE_PATH, filename)
        if not os.path.exists(file_path):
            missing_files.append(filename)
    if missing_files:
        logging.warning(f"Missing racer images: {', '.join(missing_files)}. Using fallback images.")

def main():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Sproto Race Simulation")

    check_missing_images()
    sproto_images = load_sproto_images()
    selection_background = load_selection_background(screen)
    trophy_image = load_trophy_image()
    if trophy_image is None:
        logging.error("Trophy image failed to load. Ensure the file path is correct.")
        return

    race_backgrounds, single_bg_options = load_race_backgrounds()
    if "results" not in race_backgrounds or race_backgrounds["results"] is None:
        logging.error("Results background failed to load. Ensure the file path is correct.")
        return

    sproto_list = [Sproto(name, 0, i, sproto_images[i]) for i, name in enumerate(sproto_names)]

    logging.info("Available Sprotos:")
    for sproto in sproto_list:
        logging.info(f"{sproto.name}")

    game_running = True
    selected_sprotos = None
    is_muted = True
    race_mode = None

    mute_button = MuteButton(x=10, y=10, width=50, height=50, color=(255, 0, 0))  # Provide required arguments

    while game_running:
        if selected_sprotos is None:
            result = select_sprotos(screen, sproto_list, MAX_SPROTOS, selection_background, is_muted)
            if result is None:
                logging.info("No sprotos selected or window closed. Exiting.")
                break
            selected_sprotos, is_tournament, is_muted, race_mode = result
            if not selected_sprotos and race_mode not in ["all_characters", "pocket_sprotos", "cheese_mode"]:
                logging.info("No sprotos selected or window closed. Exiting.")
                break
            if race_mode == "all_characters":
                selected_sprotos = sproto_list
                is_tournament = False

        # --- Handle Cheese Mode ---
        if race_mode == "cheese_mode":
            from obama_cheese import run_obama_cheese_mode
            run_obama_cheese_mode(screen)
            selected_sprotos = None
            race_mode = None
            continue

        # --- Handle Pocket Sprotos mode BEFORE any race logic ---
        if race_mode == "pocket_sprotos":
            run_pocket_sprotos_mode(screen, selected_sprotos)
            selected_sprotos = None
            race_mode = None
            continue

        for i, sproto in enumerate(selected_sprotos):
            sproto.lane = i
            sproto.set_speed(SPEED_RANGE[0], SPEED_RANGE[1])
            sproto.reset(RACE_DISTANCE)
            sproto.reset_tournament()

        logging.info("\nSelected Sprotos for This Race:")
        for sproto in selected_sprotos:
            logging.info(f"{sproto.name}: Initial Speed = {sproto.current_speed:.2f} units/s")

        if is_tournament:
            logging.info("\nStarting Tournament (7 Races)")
            if os.path.exists(RACE_MUSIC_PATH):
                try:
                    pygame.mixer.music.load(RACE_MUSIC_PATH)
                    pygame.mixer.music.set_volume(0.35)
                    if not is_muted:
                        pygame.mixer.music.play(loops=-1)
                        logging.info(f"Playing tournament music: {RACE_MUSIC_PATH} at 35% volume")
                    else:
                        logging.info("Tournament music loaded but muted.")
                except Exception as e:
                    logging.error(f"Error loading tournament music '{RACE_MUSIC_PATH}': {e}")
            else:
                logging.error(f"Tournament music file '{RACE_MUSIC_PATH}' not found.")

            for race_num in range(1, 8):
                logging.info(f"\n--- Starting Race #{race_num} ---")
                for sproto in selected_sprotos:
                    sproto.reset(RACE_DISTANCE)
                winner, choice, is_muted = simulate_race(screen, selected_sprotos, RACE_DISTANCE, RACE_DURATION, race_backgrounds, single_bg_options, trophy_image, race_number=race_num, tournament_mode=True, is_muted=is_muted)
                if winner:
                    logging.info(f"Race #{race_num} Winner: {winner.name}")
                if choice == "end":
                    pygame.mixer.music.stop()
                    logging.info("Tournament music stopped.")
                    game_running = False
                    break
                elif choice == "back_to_selection":
                    pygame.mixer.music.stop()
                    logging.info("Tournament music stopped.")
                    selected_sprotos = None
                    race_mode = None
                    break
            if game_running and selected_sprotos:
                try:
                    result, is_muted = show_tournament_results(
                        screen, 
                        selected_sprotos, 
                        race_backgrounds, 
                        trophy_image, 
                        is_muted  # Removed current_music_path argument
                    )
                except Exception as e:
                    logging.error(f"Error during tournament results screen: {e}")
                    result = False  # Exit the game if an error occurs
                if not result:
                    game_running = False
                selected_sprotos = None
                race_mode = None
        else:
            if race_mode == "all_characters":
                result = simulate_all_characters_race(
                    screen, 
                    selected_sprotos, 
                    RACE_DISTANCE, 
                    RACE_DURATION, 
                    race_backgrounds, 
                    single_bg_options, 
                    trophy_image, 
                    is_muted=is_muted
                )
                # Handle new 3-value return for tournament with top 5
                if isinstance(result, tuple) and len(result) == 3 and result[1] == "tournament_with_top5":
                    selected_sprotos, _, is_muted = result
                    is_tournament = True
                    race_mode = "tournament"
                    continue
                else:
                    winner, choice, is_muted = result
            else:
                try:
                    winner, choice, is_muted = simulate_race(
                        screen, 
                        selected_sprotos, 
                        RACE_DISTANCE, 
                        RACE_DURATION, 
                        race_backgrounds, 
                        single_bg_options, 
                        trophy_image, 
                        is_muted=is_muted
                    )
                except Exception as e:
                    logging.error(f"Error during single racer results screen: {e}")
                    winner, choice = None, "end"  # Exit gracefully if an error occurs
                if choice == "mute_toggle":
                    for event in pygame.event.get():  # Add event loop to define 'event'
                        is_muted = mute_button.is_clicked(event, is_muted, RACE_MUSIC_PATH)[1]
            pygame.mixer.music.stop()
            logging.info("Race music stopped.")
            if winner:
                logging.info(f"\nWinner: {winner.name}")
            if choice == "retry_same":
                continue
            elif choice == "select_new" or choice == "back_to_selection":
                selected_sprotos = None
                race_mode = None
                continue
            else:
                game_running = False

    pygame.mixer.quit()
    pygame.quit()

if __name__ == "__main__":
    main()