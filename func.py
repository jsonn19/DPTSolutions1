import pygame
import random
import time
import os
import csv

# --- Configuration ---
GRID_SIZE = 70
GARDEN_ROWS = 8
GARDEN_COLS = 8
SCREEN_WIDTH = GARDEN_COLS * GRID_SIZE + 350
SCREEN_HEIGHT = GARDEN_ROWS * GRID_SIZE + 100

# Colors.
UI_BG = (30, 30, 35)
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)
GREEN = (100, 255, 100)
RED = (255, 80, 80)
BLUE = (80, 180, 255)

# --- Procedural Generation & Data Loading ---
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
                manifest.append((row['Plant Name'], row['Sprite Path']))
    except FileNotFoundError:
        print(f"Warning: {filepath} not found. Falling back to temporary data.")
        manifest = [(f"plant{i}", f"/assets/plant{i}.png") for i in range(58)]
        
    return manifest

def generate_run_data():
    """
    Reads the plant manifest, shuffles it, and generates randomized stats and tiers.
    Applies a variance modifier to ensure plants in the same tier have unique values.
    
    Args:
        None
        
    Returns:
        dict: A nested dictionary mapping plant names to their procedural stats.
    """
    manifest = load_plant_manifest()
    random.shuffle(manifest)
    
    run_data = {}
    name_idx = 0
    
    for tier in range(1, 21):
        num_plants = 1 if tier == 20 else 3
        
        for _ in range(num_plants):
            p_name, sprite_path = manifest[name_idx]
            
            # Calculate the baseline mathematical target for this tier.
            base_rate = 5 * (1.684 ** (tier - 1))
            base_cost = 50 * (1.624 ** (tier - 1))
            
            # Apply a +/- 15% random variance so items in the same tier differ slightly.
            rate = int(random.uniform(base_rate * 0.85, base_rate * 1.15))
            cost = int(random.uniform(base_cost * 0.85, base_cost * 1.15))
            life = random.randint(10, 40)
            
            # Hard-code the Tier 20 special plant statistics without variance.
            if tier == 20:
                rate = 100000
                cost = 500000  
                life = 5
                
            run_data[p_name] = {
                'tier': tier,
                'cost': max(5, cost), # Prevent prices from ever dropping below 5
                'rate': max(1, rate), # Prevent yield from hitting 0
                'life': life,
                'sprite': sprite_path
            }
            name_idx += 1
            
    return run_data

# --- Asset Loading ---
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
        except:
            s = pygame.Surface(size)
            s.fill((random.randint(50, 200), random.randint(50, 200), random.randint(50, 200)))
            return s

    assets = {"plants": {}, "ui": {}}
    
    # Iterate dynamically over the generated run data instead of a global list.
    for p_name, data in plant_data.items():
        sprite_path = data['sprite']
        assets["plants"][p_name] = get_img(sprite_path, (GRID_SIZE - 10, GRID_SIZE - 10))
    
    # UI textures.
    for i in range(10):
        assets["ui"][f"texture{i}"] = get_img(f"texture{i}.png", (GRID_SIZE, GRID_SIZE))
        
    return assets

# --- Classes ---
class Plant:
    """Represents a single plant actively growing on the grid."""
    
    def __init__(self, p_type, x, y, plant_data):
        """
        Initializes a new plant with stats retrieved from the current run's data.
        
        Args:
            p_type (str): The unique string identifier for the plant.
            x (int): The grid X coordinate.
            y (int): The grid Y coordinate.
            plant_data (dict): The randomized procedural stat dictionary for the run.
            
        Returns:
            None
        """
        self.type = p_type
        data = plant_data[p_type]
        self.base_rate = data['rate']
        self.lifespan = data['life']
        self.spawn_time = time.time()
        self.last_harvest = time.time()
        self.pos = (x, y)
        self.drought_mult = 1.0
        self.locust_mult = 1.0
        self.paused = False

    def is_dead(self):
        """
        Checks if the plant has exceeded its lifespan.
        
        Args:
            None
            
        Returns:
            bool: True if the plant's age exceeds its lifespan, False otherwise.
        """
        if self.paused:
            self.spawn_time += (time.time() - self.last_harvest)
            
        age = (time.time() - self.spawn_time) * self.drought_mult
        return age > self.lifespan

    def get_yield(self):
        """
        Calculates how much fruit the plant has generated since the last harvest.
        
        Args:
            None
            
        Returns:
            float: The calculated yield amount based on base rate and active multipliers.
        """
        if self.paused:
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
        
        Args:
            None
            
        Returns:
            float: A value between 0.0 (new) and 1.0 (dead).
        """
        age = (time.time() - self.spawn_time) * self.drought_mult
        return max(0.0, min(1.0, age / self.lifespan))

class EventManager:
    """Manages randomized positive and negative events that impact the garden."""
    
    def __init__(self):
        """
        Initializes event timers and the available event pool.
        
        Args:
            None
            
        Returns:
            None
        """
        self.current_event = None
        self.warning_event = None
        self.event_start = 0
        self.event_end = 0
        self.next_check = time.time() + 10
        self.pool = ["DROUGHT", "RAIN", "METEOR", "HAILSTORM", "LOCUSTS", "ECLIPSE"]

    def update(self, plants, total_score):
        """
        Progresses the event timeline and triggers or resolves events based on the timer.
        
        Args:
            plants (dict): Dictionary of currently active plants on the grid.
            total_score (float): The overall score used to calculate event difficulty.
            
        Returns:
            None
        """
        now = time.time()
        
        if not self.warning_event and not self.current_event and now > self.next_check:
            self.warning_event = random.choice(self.pool)
            self.event_start = now + 5.0
            
        if self.warning_event and now >= self.event_start:
            self.current_event = self.warning_event
            self.warning_event = None
            self.event_end = now + random.uniform(5, 10)
            self.apply_instant_events(plants)

        if self.current_event and now > self.event_end:
            self.clear_events(plants)
            self.current_event = None
            self.next_check = now + self.get_next_event_delay(total_score)

        self.apply_continuous_events(plants, total_score)

    def apply_instant_events(self, plants):
        """
        Executes events that trigger a one-time immediate effect upon starting.
        
        Args:
            plants (dict): Dictionary of currently active plants on the grid.
            
        Returns:
            None
        """
        if self.current_event == "METEOR":
            plants.clear()
        elif self.current_event == "HAILSTORM":
            if plants:
                keys_to_kill = random.sample(list(plants.keys()), min(3, len(plants)))
                for k in keys_to_kill:
                    del plants[k]
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
            
        Returns:
            None
        """
        severity = 1.0 + ((total_score // 100000) * 0.5)
        
        for p in plants.values():
            p.drought_mult = 3.0 * severity if self.current_event == "DROUGHT" else 1.0
            p.locust_mult = max(0.01, 0.2 / severity) if self.current_event == "LOCUSTS" else 1.0
            p.paused = (self.current_event == "ECLIPSE")

    def clear_events(self, plants):
        """
        Resets all continuous event modifiers on active plants back to their default states.
        
        Args:
            plants (dict): Dictionary of currently active plants on the grid.
            
        Returns:
            None
        """
        for p in plants.values():
            p.drought_mult = 1.0
            p.locust_mult = 1.0
            p.paused = False

class Shop:
    """Manages plant purchases, storefront UI data, and inflation mechanics."""
    
    def __init__(self, plant_data):
        """
        Initializes the shop with the generated procedural data for the current run.
        
        Args:
            plant_data (dict): The randomized plant dictionary for the run.
            
        Returns:
            None
        """
        self.is_open = False
        self.tier = 1
        self.plant_data = plant_data
        self.offerings = []
        self.refresh_offerings()

    def refresh_offerings(self):
        """
        Pulls a new selection of plants from the currently unlocked tiers to sell.
        
        Args:
            None
            
        Returns:
            None
        """
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
            
        Returns:
            None
        """
        old_tier = self.tier
        
        while self.tier < 20:
            required_score = int(100 * (1.6054 ** (self.tier - 1)))
            
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
        
    Returns:
        None
    """
    render = font.render(text, True, color)
    surface.blit(render, pos)