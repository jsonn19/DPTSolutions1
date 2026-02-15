import pygame
import random
import time
import os
import math

# --- Configuration ---
GRID_SIZE = 70
GARDEN_ROWS = 8
GARDEN_COLS = 8
SCREEN_WIDTH = GARDEN_COLS * GRID_SIZE + 300
SCREEN_HEIGHT = GARDEN_ROWS * GRID_SIZE
SEED_DECAY_TIME = 10.0
SCORE_FILE = "highscores.txt"
GAME_DURATION = 120

PLANT_TYPES = {
    'A': {'base_rate': 2.0, 'life': (4, 8), 'color': (255, 80, 80), 'cost': 100},
    'B': {'base_rate': 1.5, 'life': (10, 18), 'color': (255, 230, 80), 'cost': 80},
    'C': {'base_rate': 0.5, 'life': (20, 35), 'color': (80, 255, 80), 'cost': 60}
}

# --- Colors ---
PLAYER_COLOR = (0, 180, 255)
UI_BG = (30, 30, 35)
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)
METEOR_FLASH = (255, 0, 0)


# --- Asset Loading ---
def load_game_assets():
    def get_img(path, size=(GRID_SIZE, GRID_SIZE)):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(img, size)
        except:
            # Fallback surface if file missing
            s = pygame.Surface(size)
            s.fill((100, 100, 100))
            return s

    assets = {
        "tiles": {
            "NORMAL": get_img("grass_ui.jpg"),
            "DROUGHT": get_img("drought_ui.jpg"),
            "RAIN": get_img("wet_grass_ui.jpg")
        },
        "player": get_img("player.png", (GRID_SIZE - 20, GRID_SIZE - 20)),
        "plants": {
            'A': get_img("player.png"),
            'B': get_img("player.png"),
            'C': get_img("player.png"),
            'A_mut': get_img("player.png"),
            'B_mut': get_img("player.png"),
            'C_mut': get_img("player.png")
        },
        "seeds": {
            'A': get_img("player.png", (30, 30)),
            'B': get_img("player.png", (30, 30)),
            'C': get_img("player.png", (30, 30))
        }
    }
    return assets


def dim_surface(surf):
    """Creates a decayed look by darkening the sprite."""
    dark = pygame.Surface(surf.get_size()).convert_alpha()
    dark.fill((0, 0, 0, 150))
    new_surf = surf.copy()
    new_surf.blit(dark, (0, 0))
    return new_surf


def load_high_score():
    if os.path.exists(SCORE_FILE):
        with open(SCORE_FILE, "r") as f:
            try:
                highscore = int(f.read())
                f.close()
                return highscore
            except:
                return 0
    return 0


def save_high_score(new_score):
    current_high = load_high_score()
    if new_score > current_high:
        with open(SCORE_FILE, "w") as f:
            f.write(str(new_score))
            f.close()
        return True
    return False


class Seed:
    def __init__(self, p_type, x, y, is_mutated=False):
        self.type = p_type
        self.pos = (x, y)
        self.spawn_time = time.time()
        self.is_mutated = is_mutated
        self.rect = pygame.Rect(x * GRID_SIZE + 20, y * GRID_SIZE + 20, 30, 30)

    def is_expired(self):
        return time.time() - self.spawn_time > SEED_DECAY_TIME


class Plant:
    def __init__(self, p_type, x, y, is_mutated=False):
        self.type = p_type
        self.is_mutated = is_mutated
        self.base_rate = PLANT_TYPES[p_type]['base_rate']
        self.lifespan = random.uniform(*PLANT_TYPES[p_type]['life'])
        if is_mutated:
            if random.random() > 0.5:
                self.base_rate *= 2.0
            else:
                self.lifespan *= 1.5
        self.spawn_time = time.time()
        self.pos = (x * GRID_SIZE, y * GRID_SIZE)
        self.last_harvest = time.time()
        self.drought_multiplier = 1.0

    def is_dead(self):
        age = (time.time() - self.spawn_time) * self.drought_multiplier
        return age > self.lifespan

    def is_decaying(self):
        """Returns True if plant has lived more than 50% of its life."""
        age = (time.time() - self.spawn_time) * self.drought_multiplier
        return age > (self.lifespan / 2)

    def get_current_points(self):
        now = time.time()
        time_alive = now - self.spawn_time
        elapsed = now - self.last_harvest
        points = (self.base_rate * time_alive) * elapsed
        self.last_harvest = now
        return points


def run_game(assets):
    screen = pygame.display.get_surface()
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Verdana", 16, bold=True)
    sm_font = pygame.font.SysFont("Verdana", 12, bold=True)
    high_score = load_high_score()

    player_pos = [0, 0]
    plants, seeds = {}, []
    inventory = {'A': 2, 'B': 2, 'C': 2}
    total_score, start_time = 0.0, time.time()
    inv_keys = ['A', 'B', 'C']
    selected_idx = 0

    current_event, warning_event = None, None
    event_start_time, event_end_time, next_check_time = 0, 0, time.time() + 5
    meteor_flash_timer = 0

    running = True
    while running:
        now = time.time()
        elapsed = now - start_time
        remaining = max(0, GAME_DURATION - elapsed)
        if remaining <= 0: break

        # Event Logic
        if not warning_event and not current_event and now > next_check_time:
            warning_event = random.choice(["DROUGHT", "METEOR", "RAIN"])
            event_start_time = now + 4.0

        if warning_event and now >= event_start_time:
            current_event = warning_event
            warning_event = None
            event_end_time = now + 6.0
            if current_event == "METEOR":
                plants.clear()
                meteor_flash_timer = now + 0.6
            elif current_event == "RAIN":
                for p in plants.values(): p.lifespan += 10

        if current_event and now > event_end_time:
            current_event = None
            next_check_time = now + random.uniform(8, 15)

        for event in pygame.event.get():
            if event.type == pygame.QUIT: return "QUIT"
            if event.type == pygame.KEYDOWN:
                new_pos = list(player_pos)
                if event.key == pygame.K_w:
                    new_pos[1] -= 1
                elif event.key == pygame.K_s:
                    new_pos[1] += 1
                elif event.key == pygame.K_a:
                    new_pos[0] -= 1
                elif event.key == pygame.K_d:
                    new_pos[0] += 1
                if 0 <= new_pos[0] < GARDEN_COLS and 0 <= new_pos[1] < GARDEN_ROWS:
                    if tuple(new_pos) not in plants: player_pos = new_pos
                if event.key == pygame.K_UP: selected_idx = (selected_idx - 1) % 3
                if event.key == pygame.K_DOWN: selected_idx = (selected_idx + 1) % 3
                if event.key == pygame.K_q:
                    p_type = inv_keys[selected_idx]
                    if total_score >= PLANT_TYPES[p_type]['cost']:
                        total_score -= PLANT_TYPES[p_type]['cost']
                        inventory[p_type] += 1
                if event.key == pygame.K_e:
                    target_pos = (player_pos[0] + 1, player_pos[1])
                    p_type = inv_keys[selected_idx]
                    if target_pos[0] < GARDEN_COLS and target_pos not in plants and inventory[p_type] > 0:
                        is_mutated = (elapsed > 60 and random.random() < 0.3)
                        plants[target_pos] = Plant(p_type, target_pos[0], target_pos[1], is_mutated)
                        inventory[p_type] -= 1

        for s in seeds[:]:
            if s.pos == tuple(player_pos):
                inventory[s.type] += 1
                seeds.remove(s)

        dead_keys = []
        for pos, plant in plants.items():
            total_score += plant.get_current_points()
            plant.drought_multiplier = 4.0 if current_event == "DROUGHT" else 1.0
            if plant.is_dead():
                dead_keys.append(pos)
                seeds.append(Seed(plant.type, pos[0], pos[1], plant.is_mutated))
        for k in dead_keys: del plants[k]
        seeds = [s for s in seeds if not s.is_expired()]

        # --- RENDERING ---
        tile_key = "NORMAL"
        if current_event == "DROUGHT":
            tile_key = "DROUGHT"
        elif current_event == "RAIN":
            tile_key = "RAIN"

        screen.fill((20, 20, 20))
        # 1. Tiles
        for r in range(GARDEN_ROWS):
            for c in range(GARDEN_COLS):
                rect = (c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                screen.blit(assets["tiles"][tile_key], (rect[0], rect[1]))
                pygame.draw.rect(screen, (80, 80, 80), rect, 1)

        # 2. Meteor Flash
        if meteor_flash_timer > now:
            if (0.45 < meteor_flash_timer - now < 0.6) or (0.15 < meteor_flash_timer - now < 0.3):
                flash_surf = pygame.Surface((GARDEN_COLS * GRID_SIZE, SCREEN_HEIGHT))
                flash_surf.set_alpha(150);
                flash_surf.fill(METEOR_FLASH)
                screen.blit(flash_surf, (0, 0))

        # 3. Seeds
        for s in seeds:
            screen.blit(assets["seeds"][s.type], s.rect.topleft)
            if s.is_mutated:  # Visual indicator for mutated seed
                pygame.draw.rect(screen, (180, 0, 255), s.rect, 2)

        # 4. Plants
        for pos, plant in plants.items():
            key = plant.type if not plant.is_mutated else f"{plant.type}_mut"
            p_img = assets["plants"][key]
            if plant.is_decaying():
                p_img = dim_surface(p_img)
            screen.blit(p_img, plant.pos)

            # Life bar
            age_ratio = min(1.0, ((time.time() - plant.spawn_time) * plant.drought_multiplier) / plant.lifespan)
            pygame.draw.rect(screen, WHITE,
                             (plant.pos[0] + 5, plant.pos[1] + GRID_SIZE - 10, (GRID_SIZE - 10) * (1 - age_ratio), 4))

        # 5. Player
        px, py = player_pos[0] * GRID_SIZE + 10, player_pos[1] * GRID_SIZE + 10
        screen.blit(assets["player"], (px, py))

        # 6. UI Side Panel
        ui_x = GARDEN_COLS * GRID_SIZE
        pygame.draw.rect(screen, UI_BG, (ui_x, 0, 300, SCREEN_HEIGHT))
        screen.blit(font.render(f"SCORE: {int(total_score)}", True, GOLD), (ui_x + 20, 20))
        screen.blit(font.render(f"BEST: {max(high_score, int(total_score))}", True, (100, 255, 100)), (ui_x + 20, 50))
        screen.blit(font.render(f"TIME: {int(remaining)}s", True, WHITE), (ui_x + 20, 80))

        # Warning Panel
        pygame.draw.rect(screen, (50, 50, 55), (ui_x + 10, 110, 280, 80), border_radius=5)
        if warning_event:
            screen.blit(font.render(f"WARNING: {warning_event}", True, (255, 50, 50)), (ui_x + 20, 125))
            screen.blit(font.render(f"INCOMING: {int(event_start_time - now)}s", True, WHITE), (ui_x + 20, 150))
        elif current_event:
            screen.blit(font.render(f"EVENT: {current_event}", True, GOLD), (ui_x + 20, 125))
            screen.blit(font.render(f"ENDS IN: {int(event_end_time - now)}s", True, WHITE), (ui_x + 20, 150))
        else:
            screen.blit(font.render("STATUS: CLEAR", True, (100, 255, 100)), (ui_x + 20, 135))

        if elapsed > 60: screen.blit(font.render("MUTATIONS ACTIVE!", True, (180, 0, 255)), (ui_x + 20, 200))

        # Shop
        for i, p_type in enumerate(inv_keys):
            box_y = 250 + (i * 90)
            is_selected = (i == selected_idx)
            if is_selected: pygame.draw.rect(screen, WHITE, (ui_x + 10, box_y - 5, 280, 80), 1)
            # Use plant sprite in shop
            shop_img = pygame.transform.scale(assets["plants"][p_type], (50, 50))
            screen.blit(shop_img, (ui_x + 20, box_y))
            screen.blit(font.render(f"{p_type}: {inventory[p_type]} qty", True, WHITE), (ui_x + 80, box_y))
            cost = PLANT_TYPES[p_type]['cost']
            can_afford = total_score >= cost
            cost_col = (100, 255, 100) if (can_afford and is_selected) else (200, 200, 200)
            screen.blit(font.render(f"Cost: ${cost}", True, cost_col), (ui_x + 80, box_y + 25))
            if is_selected:
                buy_txt = "[Q] BUY" if can_afford else "NEED FUNDS"
                plant_txt = "[E] PLANT" if inventory[p_type] > 0 else "NO SEEDS"
                screen.blit(sm_font.render(f"{buy_txt} | {plant_txt}", True, cost_col), (ui_x + 80, box_y + 45))

        pygame.display.flip()
        clock.tick(60)

    save_high_score(int(total_score))
    return int(total_score)


def main_menu():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Botanical Apocalypse 8x8")
    game_assets = load_game_assets()
    f_lg, f_sm = pygame.font.SysFont("Verdana", 28, bold=True), pygame.font.SysFont("Verdana", 16)
    last_score = None
    while True:
        high_score = load_high_score()
        screen.fill((15, 15, 20))
        title = f_lg.render("GREENHOUSE Sprites", True, GOLD)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))
        best_txt = f_sm.render(f"ALL-TIME HIGH SCORE: {high_score}", True, (100, 255, 100))
        screen.blit(best_txt, (SCREEN_WIDTH // 2 - best_txt.get_width() // 2, 100))
        screen.blit(f_lg.render("120s Sprite Sprint", True, WHITE), (SCREEN_WIDTH // 2 - 120, 150))
        instr = ["WASD: Move | Q: Buy | E: Plant", "Mutated Plants provide extra points", "Plants darken when decaying",
                 "ENTER: Start Game"]
        for i, m in enumerate(instr):
            txt = f_sm.render(m, True, (200, 200, 200))
            screen.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, 230 + i * 35))
        if last_score is not None:
            s_msg = f_lg.render(f"SCORE: {last_score}", True, GOLD)
            screen.blit(s_msg, (SCREEN_WIDTH // 2 - s_msg.get_width() // 2, 480))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN: last_score = run_game(game_assets)


if __name__ == "__main__":
    main_menu()