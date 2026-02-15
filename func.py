import pygame
import random
import time
import os
import csv


# Configuration
GRID_SIZE = 70
GARDEN_ROWS = 8
GARDEN_COLS = 8
SCREEN_WIDTH = GARDEN_COLS * GRID_SIZE + 350
SCREEN_HEIGHT = GARDEN_ROWS * GRID_SIZE + 100


# Colors
UI_BG = (30, 30, 35)
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)
GREEN = (100, 255, 100)
RED = (255, 80, 80)
BLUE = (80, 180, 255)


# Number Formatting
def format_num(n):
    """
    Shortens large numbers for clean UI rendering.

    Args:
        n (float/int): The numerical value to format.

    Returns:
        str: A shortened string representation of the number (e.g. 150, 45K, 1.24M).
    """
    n = float(n)
    if n < 10000:
        return str(int(n))
    elif n < 1000000:
        return f"{int(n) // 1000}K"
    else:
        return f"{n / 1000000:.2f}M"


# Procedural Generation & Data Loading
def load_plant_manifest(filepath="plants.csv"):
    """
    Reads the static plant manifest CSV containing names and sprite paths.

    Args:
        filepath (str): The relative path to the CSV file.

    Returns:
        list: A list of tuples formatted as (Plant Name, Sprite Path).
    """
    manifest = []
    try:
        with open(filepath, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_path = row['Sprite Path']
                clean_path = raw_path.lstrip('/\\')
                clean_path = os.path.normpath(clean_path)
                manifest.append((row['Plant Name'], clean_path))
    except FileNotFoundError:
        print(f"Warning: {filepath} not found. Falling back to temporary data.")
        manifest = [(f"plant{i}", os.path.normpath(f"assets/plant{i}.png")) for i in range(28)]
        
    return manifest


def generate_run_data():
    """
    Reads the plant manifest, shuffles it, and generates randomized stats and tiers.
    Applies a variance modifier to ensure plants in the same tier have unique values.

    Returns:
        dict: A nested dictionary mapping plant names to their procedural stats.
    """
    manifest = load_plant_manifest()
    random.shuffle(manifest)
    
    run_data = {}
    name_idx = 0
    
    for tier in range(1, 11):
        num_plants = 1 if tier == 10 else 3
        
        for _ in range(num_plants):
            p_name, sprite_path = manifest[name_idx]
            
            base_rate = 5 * (3.129 ** (tier - 1))
            base_cost = 50 * (2.783 ** (tier - 1))
            
            rate = int(random.uniform(base_rate * 0.85, base_rate * 1.15))
            cost = int(random.uniform(base_cost * 0.85, base_cost * 1.15))
            life = random.randint(10, 40)
            
            if tier == 10:
                rate = 100000
                cost = 500000  
                life = 5
                
            run_data[p_name] = {
                'tier': tier,
                'cost': max(5, cost), 
                'rate': max(1, rate), 
                'life': life,
                'sprite': sprite_path
            }
            name_idx += 1
            
    return run_data


# Asset Loading
def load_assets(plant_data):
    """
    Loads all required images into memory, substituting colored squares if missing.

    Args:
        plant_data (dict): The randomized plant dictionary containing sprite paths.

    Returns:
        dict: A nested dictionary containing loaded pygame surfaces for plants and UI.
    """
    def get_img(name, size):
        try:
            img = pygame.image.load(name).convert_alpha()
            return pygame.transform.scale(img, size)
        except Exception as e:
            print(f"FAILED TO LOAD IMAGE '{name}': {e}")
            s = pygame.Surface(size)
            s.fill((random.randint(50, 200), random.randint(50, 200), random.randint(50, 200)))
            return s

    assets = {"plants": {}, "ui": {}}
    
    for p_name, data in plant_data.items():
        sprite_path = data['sprite']
        assets["plants"][p_name] = get_img(sprite_path, (GRID_SIZE - 10, GRID_SIZE - 10))
    
    assets["ui"]["default"] = get_img(os.path.normpath("assets/grass_ui.jpg"), (GRID_SIZE, GRID_SIZE))
    assets["ui"]["rain"] = get_img(os.path.normpath("assets/wet_grass_ui.jpg"), (GRID_SIZE, GRID_SIZE))
    assets["ui"]["drought"] = get_img(os.path.normpath("assets/drought_ui.jpg"), (GRID_SIZE, GRID_SIZE))
    assets["ui"]["hailstorm"] = get_img(os.path.normpath("assets/ice.jpg"), (GRID_SIZE, GRID_SIZE))
    assets["ui"]["crater"] = get_img(os.path.normpath("assets/crater.jpg"), (GRID_SIZE, GRID_SIZE))
        
    return assets


# Classes
class Plant:
    """
    Represents a single plant actively growing on the grid.
    """
    
    def __init__(self, p_type, x, y, plant_data):
        """
        Initializes a new plant with stats retrieved from the current run's data.

        Args:
            p_type (str): The unique string identifier for the plant.
            x (int): The grid X coordinate.
            y (int): The grid Y coordinate.
            plant_data (dict): The randomized procedural stat dictionary for the run.
        """
        self.type = p_type
        data = plant_data[p_type]
        self.base_rate = data['rate']
        self.lifespan = data['life']
        
        self.age = 0.0
        self.last_update_time = time.time()
        self.last_harvest = time.time()
        
        self.pos = (x, y)
        self.drought_mult = 1.0
        self.locust_mult = 1.0
        self.fruit_paused = False

    def _update_age(self):
        """
        Calculates delta time and applies modifiers fairly based on active events.
        """
        now = time.time()
        dt = now - self.last_update_time
        self.last_update_time = now
        
        self.age += dt * self.drought_mult

    def is_dead(self):
        """
        Checks if the plant has exceeded its lifespan.

        Returns:
            bool: True if the plant's age exceeds its lifespan, False otherwise.
        """
        self._update_age()
        return self.age > self.lifespan

    def get_yield(self):
        """
        Calculates how much fruit the plant has generated since the last harvest.

        Returns:
            float: The calculated yield amount based on base rate and active multipliers.
        """
        if self.fruit_paused:
            self.last_harvest = time.time()
            return 0
            
        now = time.time()
        elapsed = now - self.last_harvest
        produced = (self.base_rate * elapsed) * self.locust_mult
        self.last_harvest = now
        return produced

    def get_life_ratio(self):
        """
        Calculates the percentage of the plant's life that has passed.

        Returns:
            float: A value between 0.0 (new) and 1.0 (dead).
        """
        self._update_age()
        return max(0.0, min(1.0, self.age / self.lifespan))


class EventManager:
    """
    Manages randomized positive and negative events that impact the garden.
    """
    
    def __init__(self):
        """
        Initializes event timers, forecasting models, and event variables.
        """
        self.current_event = None
        self.warning_event = None
        self.event_start = 0
        self.event_end = 0
        self.next_check = time.time() + 10
        self.meteor_flash_alpha = 0 
        
        self.pool = ["DROUGHT", "RAIN", "HAILSTORM", "LOCUSTS", "ECLIPSE", "METEOR"]
        self.weights = [60, 50, 40, 30, 20, 10]
        
        self.upcoming_event = random.choices(self.pool, weights=self.weights, k=1)[0]
        self.forecast_text = ""
        self.generate_forecast()

    def generate_forecast(self):
        """
        Creates a prediction of the next event for the player.
        Calculates odds at 50% Unknown, 40% True, and 10% False.
        """
        roll = random.random()
        if roll < 0.50:
            self.forecast_text = "Unknown"
        elif roll < 0.90:
            self.forecast_text = self.upcoming_event
        else:
            wrong_pool = [e for e in self.pool if e != self.upcoming_event]
            self.forecast_text = random.choice(wrong_pool)

    def update(self, plants, craters, total_score):
        """
        Progresses the event timeline and triggers or resolves events based on the timer.

        Args:
            plants (dict): Dictionary of currently active plants on the grid.
            craters (dict): Dictionary mapping hazard locations to expiration times.
            total_score (float): The overall score used to calculate event difficulty.
        """
        now = time.time()
        
        if self.meteor_flash_alpha > 0:
            self.meteor_flash_alpha = max(0, self.meteor_flash_alpha - 5)
        
        if not self.warning_event and not self.current_event and now > self.next_check:
            self.warning_event = self.upcoming_event
            self.event_start = now + 5.0
            
        if self.warning_event and now >= self.event_start:
            self.current_event = self.warning_event
            self.warning_event = None
            self.event_end = now + random.uniform(5, 10)
            self.apply_instant_events(plants, craters)

        if self.current_event and now > self.event_end:
            self.clear_events(plants)
            self.current_event = None
            self.next_check = now + self.get_next_event_delay(total_score)
            
            self.upcoming_event = random.choices(self.pool, weights=self.weights, k=1)[0]
            self.generate_forecast()

        self.apply_continuous_events(plants, total_score)

    def apply_instant_events(self, plants, craters):
        """
        Executes events that trigger a one-time immediate effect upon starting.

        Args:
            plants (dict): Dictionary of currently active plants on the grid.
            craters (dict): Dictionary mapping hazard locations to expiration times.
        """
        now = time.time()
        if self.current_event == "METEOR":
            plants.clear()
            self.meteor_flash_alpha = 255 
            
            cx, cy = random.randint(1, GARDEN_COLS - 2), random.randint(1, GARDEN_ROWS - 2)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    craters[(cx + dx, cy + dy)] = now + 10.0
                    
        elif self.current_event == "HAILSTORM":
            if plants:
                keys_to_kill = random.sample(list(plants.keys()), min(3, len(plants)))
                for k in keys_to_kill:
                    del plants[k]
                    
            for _ in range(6):
                cx, cy = random.randint(0, GARDEN_COLS - 1), random.randint(0, GARDEN_ROWS - 1)
                craters[(cx, cy)] = now + 10.0
                if (cx, cy) in plants:
                    del plants[(cx, cy)]
                    
        elif self.current_event == "RAIN":
            for p in plants.values():
                p.lifespan += 5
    
    def get_next_event_delay(self, total_score):
        """
        Calculates the cooldown time between events, shrinking as the score grows.

        Args:
            total_score (float): The player's overall cumulative score.

        Returns:
            float: The calculated cooldown delay in seconds.
        """
        base_delay = 60.0
        min_delay = 15.0
        reductions = total_score // 50000 
        calculated_delay = base_delay - (reductions * 5.0)
        return max(min_delay, calculated_delay)

    def apply_continuous_events(self, plants, total_score):
        """
        Applies modifiers to all active plants while a continuous event is running.

        Args:
            plants (dict): Dictionary of currently active plants on the grid.
            total_score (float): The player's overall score used to scale difficulty.
        """
        drought_score = min(total_score, 500000)
        drought_severity = 1.0 + ((drought_score // 100000) * 0.5)
        
        locust_mult = max(0.0, 1.0 - (total_score / 500000.0))
        
        for p in plants.values():
            p.drought_mult = 3.0 * drought_severity if self.current_event == "DROUGHT" else 1.0
            p.locust_mult = locust_mult if self.current_event == "LOCUSTS" else 1.0
            p.fruit_paused = (self.current_event == "ECLIPSE")

    def clear_events(self, plants):
        """
        Resets all continuous event modifiers on active plants back to their default states.

        Args:
            plants (dict): Dictionary of currently active plants on the grid.
        """
        for p in plants.values():
            p.drought_mult = 1.0
            p.locust_mult = 1.0
            p.fruit_paused = False


class Shop:
    """
    Manages plant purchases, storefront UI data, and inflation mechanics.
    """
    
    def __init__(self, plant_data):
        """
        Initializes the shop with the generated procedural data for the current run.

        Args:
            plant_data (dict): The randomized plant dictionary for the run.
        """
        self.is_open = False
        self.tier = 1
        self.plant_data = plant_data
        self.offerings = []
        self.last_refresh = time.time()
        self.refresh_interval = 60.0
        self.refresh_offerings()

    def get_refresh_interval(self, total_score):
        """
        Calculates the shop auto-refresh interval, shrinking as the score grows.

        Args:
            total_score (float): The player's overall cumulative score.

        Returns:
            float: The calculated refresh interval in seconds.
        """
        base_interval = 60.0
        min_interval = 10.0
        reductions = total_score // 50000
        calculated_interval = base_interval - (reductions * 5.0)
        return max(min_interval, calculated_interval)

    def update(self, total_score):
        """
        Automatically refreshes the shop offerings based on the dynamically scaled refresh interval.

        Args:
            total_score (float): The player's overall cumulative score.
        """
        self.refresh_interval = self.get_refresh_interval(total_score)
        if time.time() - self.last_refresh >= self.refresh_interval:
            self.refresh_offerings()

    def refresh_offerings(self):
        """
        Pulls a new selection of plants from the currently unlocked tiers to sell.
        """
        self.last_refresh = time.time()
        available = [p for p, d in self.plant_data.items() if d['tier'] <= self.tier]
        highest_tier_plants = [p for p in available if self.plant_data[p]['tier'] == self.tier]
        
        self.offerings = []
        if highest_tier_plants:
            self.offerings.append(random.choice(highest_tier_plants))
            
        while len(self.offerings) < 3:
            self.offerings.append(random.choice(available))

    def check_progression(self, score):
        """
        Advances the player to the next plant tier if they hit the score threshold.

        Args:
            score (float): The player's overall cumulative score.
        """
        old_tier = self.tier
        
        while self.tier < 10:
            required_score = int(100 * (2.918 ** (self.tier - 1)))
            if score >= required_score:
                self.tier += 1
            else:
                break
                
        if self.tier > old_tier:
            self.refresh_offerings()

    def get_inflation_multiplier(self, total_score):
        """
        Calculates how heavily plant prices should be taxed based on the player's progress.

        Args:
            total_score (float): The player's overall cumulative score.

        Returns:
            float: The inflation multiplier percentage.
        """
        inflation_steps = total_score // 50000
        return 1.0 + (inflation_steps * 0.10)

    def get_adjusted_cost(self, plant_name, total_score):
        """
        Calculates the final cost of a plant after applying global inflation.

        Args:
            plant_name (str): The unique string identifier for the plant.
            total_score (float): The player's overall cumulative score.

        Returns:
            int: The dynamically calculated cost of the plant.
        """
        base_cost = self.plant_data[plant_name]['cost']
        multiplier = self.get_inflation_multiplier(total_score)
        return int(base_cost * multiplier)


def draw_text(surface, text, font, color, pos):
    """
    Renders standard text onto a Pygame surface.

    Args:
        surface (pygame.Surface): The target surface to draw upon.
        text (str): The string of text to render.
        font (pygame.font.Font): The Pygame font object to use for styling.
        color (tuple): RGB tuple defining the text color.
        pos (tuple): (X, Y) coordinates indicating where to place the top-left corner of the text.
    """
    render = font.render(text, True, color)
    surface.blit(render, pos)