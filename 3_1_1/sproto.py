import pygame
import random
from settings import *

def get_track_position(position, lane, race_distance, lane_height=100):
    track_y = 50 if lane_height < 100 else SCREEN_HEIGHT // 4
    sprite_width = 25 if lane_height < 100 else 50
    if lane_height == 100:  # Single/tournament: curved path
        t = (position / race_distance)  # Normalized position [0, 1]
        start_x, start_y = 0, track_y + lane * lane_height + lane_height // 2
        end_x, end_y = SCREEN_WIDTH - sprite_width, track_y + lane * lane_height + lane_height // 2
        control1_x, control1_y = SCREEN_WIDTH // 4, track_y + lane * lane_height + lane_height // 2 - 50
        control2_x, control2_y = 3 * SCREEN_WIDTH // 4, track_y + lane * lane_height + lane_height // 2 + 50
        x = (1-t)**3 * start_x + 3*(1-t)**2*t * control1_x + 3*(1-t)*t**2 * control2_x + t**3 * end_x
        y = (1-t)**3 * start_y + 3*(1-t)**2*t * control1_y + 3*(1-t)*t**2 * control2_y + t**3 * end_y
    else:  # All-characters: straight path
        x = (position / race_distance) * (SCREEN_WIDTH - sprite_width)
        y = track_y + lane * lane_height + lane_height // 2
    return x, y

class Sproto:
    def __init__(self, name, position, lane, image):
        self.name = name
        self.position = position
        self.lane = lane
        self.sprite = image
        self.small_sprite = pygame.transform.scale(image, (23, 23))  # Cache for all-characters mode
        self.current_speed = 0
        self.min_speed = 0
        self.max_speed = 0
        self.finished = False
        self.start_time = 0
        self.finish_time = 0
        self.finish_place = None
        self.tournament_speeds = []
        self.tournament_wins = 0
        self.tournament_points = 0

    def set_speed(self, min_speed, max_speed):
        self.min_speed = min_speed
        self.max_speed = max_speed
        self.current_speed = random.uniform(min_speed, max_speed)

    def reset(self, race_distance):
        self.position = 0
        self.set_speed(self.min_speed, self.max_speed)  # Ensure speed is set during reset
        self.finished = False
        self.start_time = 0
        self.finish_time = 0
        self.finish_place = None

    def reset_tournament(self):
        self.tournament_speeds = []
        self.tournament_wins = 0
        self.tournament_points = 0

    def run(self, race_distance, dt, finishers, time_elapsed):
        if not self.finished:
            if self.start_time == 0:
                self.start_time = time_elapsed
            self.position += self.current_speed * dt  # Update position based on speed and time
            if self.position >= race_distance:
                self.position = race_distance
                self.finished = True
                self.finish_time = time_elapsed
                if self not in finishers:
                    self.finish_place = len(finishers) + 1
                    finishers.append(self)
            if random.random() < 0.01:  # Randomly adjust speed occasionally
                self.current_speed = random.uniform(self.min_speed, self.max_speed)

    def get_average_speed(self):
        if self.finish_time > self.start_time:
            return self.position / (self.finish_time - self.start_time)
        return 0

    def get_tournament_avg_speed(self):
        return sum(self.tournament_speeds) / len(self.tournament_speeds) if self.tournament_speeds else 0

    def get_place_suffix(self):
        if self.finish_place is None:
            return ""
        last_digit = self.finish_place % 10
        if 10 <= self.finish_place % 100 <= 13:
            return "th"
        if last_digit == 1:
            return "st"
        if last_digit == 2:
            return "nd"
        if last_digit == 3:
            return "rd"
        return "th"

    def mark_as_qualified(self, color):
        """Mark the racer as qualified with a visual indicator."""
        self.qualified_marker_color = color

    def draw_marker(self, screen, x, y):
        """Draw the qualification marker next to the racer."""
        if hasattr(self, 'qualified_marker_color'):
            pygame.draw.circle(screen, self.qualified_marker_color, (x, y), 5)