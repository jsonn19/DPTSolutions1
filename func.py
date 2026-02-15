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

# --- Number Formatting ---
def format_num(n):
    """
    Shortens large numbers for clean UI rendering.
    """
    n = int(n)
    if n < 10000:
        return str(n)
    elif n < 1000000:
        return f"{n // 1000}K"
    else:
        return f"{n // 1000000}M"

# --- Procedural Generation & Data Loading ---
def load_plant_manifest(filepath="plants.csv"):
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

# --- Asset Loading ---
def load_assets(plant_data):
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

# --- Classes ---
class Plant:
    def __init__(self, p_type, x, y, plant_data):
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
        self.paused = False

    def _update_age(self):
        now = time.time()
        dt = now - self.last_update_time
        self.last_update_time = now
        
        if not self.paused:
            self.age += dt * self.drought_mult

    def is_dead(self):
        self._update_age()
        return self.age > self.lifespan

    def get_yield(self):
        if self.paused:
            self.last_harvest = time.time()
            return 0
            
        now = time.time()
        elapsed = now - self.last_harvest
        produced = (self.base_rate * elapsed) * self.locust_mult
        self.last_harvest = now
        return produced

    def get_life_ratio(self):
        self._update_age()
        return max(0.0, min(1.0, self.age / self.lifespan))

class EventManager:
    def __init__(self):
        self.current_event = None
        self.warning_event = None
        self.event_start = 0
        self.event_end = 0
        self.next_check = time.time() + 10
        self.meteor_flash_alpha = 0 
        
        self.pool = ["DROUGHT", "RAIN", "HAILSTORM", "LOCUSTS", "ECLIPSE", "METEOR"]
        self.weights = [60, 50, 40, 30, 20, 10]
        
        # Roll the first upcoming event and generate its forecast
        self.upcoming_event = random.choices(self.pool, weights=self.weights, k=1)[0]
        self.forecast_text = ""
        self.generate_forecast()

    def generate_forecast(self):
        """Creates a prediction for the player. 50% Unknown, 40% True, 10% False"""
        roll = random.random()
        if roll < 0.50:
            self.forecast_text = "Unknown"
        elif roll < 0.90:
            self.forecast_text = self.upcoming_event
        else:
            wrong_pool = [e for e in self.pool if e != self.upcoming_event]
            self.forecast_text = random.choice(wrong_pool)

    def update(self, plants, craters, total_score):
        now = time.time()
        
        if self.meteor_flash_alpha > 0:
            self.meteor_flash_alpha = max(0, self.meteor_flash_alpha - 5)
        
        if not self.warning_event and not self.current_event and now > self.next_check:
            # Trigger the pre-rolled upcoming event
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
            
            # Roll the NEXT event and update the forecast for the peaceful period
            self.upcoming_event = random.choices(self.pool, weights=self.weights, k=1)[0]
            self.generate_forecast()

        self.apply_continuous_events(plants, total_score)

    def apply_instant_events(self, plants, craters):
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
        base_delay = 60.0
        min_delay = 15.0
        reductions = total_score // 50000 
        calculated_delay = base_delay - (reductions * 5.0)
        return max(min_delay, calculated_delay)

    def apply_continuous_events(self, plants, total_score):
        severity = 1.0 + ((total_score // 100000) * 0.5)
        locust_mult = max(0.0, 1.0 - (total_score / 500000.0))
        
        for p in plants.values():
            p.drought_mult = 3.0 * severity if self.current_event == "DROUGHT" else 1.0
            p.locust_mult = locust_mult if self.current_event == "LOCUSTS" else 1.0
            p.paused = (self.current_event == "ECLIPSE")

    def clear_events(self, plants):
        for p in plants.values():
            p.drought_mult = 1.0
            p.locust_mult = 1.0
            p.paused = False

class Shop:
    def __init__(self, plant_data):
        self.is_open = False
        self.tier = 1
        self.plant_data = plant_data
        self.offerings = []
        self.refresh_offerings()

    def refresh_offerings(self):
        available = [p for p, d in self.plant_data.items() if d['tier'] <= self.tier]
        highest_tier_plants = [p for p in available if self.plant_data[p]['tier'] == self.tier]
        
        self.offerings = []
        if highest_tier_plants:
            self.offerings.append(random.choice(highest_tier_plants))
            
        while len(self.offerings) < 3:
            self.offerings.append(random.choice(available))

    def check_progression(self, score):
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
        inflation_steps = total_score // 50000
        return 1.0 + (inflation_steps * 0.10)

    def get_adjusted_cost(self, plant_name, total_score):
        base_cost = self.plant_data[plant_name]['cost']
        multiplier = self.get_inflation_multiplier(total_score)
        return int(base_cost * multiplier)

def draw_text(surface, text, font, color, pos):
    render = font.render(text, True, color)
    surface.blit(render, pos)