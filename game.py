import pygame
import random
import time
from func import *

def main():
    """
    The main execution loop for the game, handling inputs, rendering, and state management.
    """
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("DPT: Develop, Plant, Terraform")
    clock = pygame.time.Clock()
    
    font_lg = pygame.font.SysFont("Verdana", 24, bold=True)
    font_sm = pygame.font.SysFont("Verdana", 14, bold=True)
    
    plant_data = generate_run_data()
    assets = load_assets(plant_data)

    # --- Run State Variables ---
    plantfruit = 150.0  
    total_score = 0.0   
    reroll_cost = 50.0  
    plants = {} 
    craters = {}  # Tracks (x, y): expiration_time for craters
    
    inventory = {p: 0 for p in plant_data.keys()}
    t1_plants = [p for p, d in plant_data.items() if d['tier'] == 1]
    inventory[random.choice(t1_plants)] = 2 
    
    selected_seed = None
    shop = Shop(plant_data)
    events = EventManager()

    empty_start_time = None
    game_over = False

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        clicked = False

        # --- EVENT HANDLING ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked = True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                selected_seed = None

        # --- GAME OVER SCREEN ---
        if game_over:
            screen.fill((20, 20, 25))
            draw_text(screen, "GAME OVER - THE GARDEN WITHERED", font_lg, RED, (SCREEN_WIDTH // 2 - 240, SCREEN_HEIGHT // 2 - 60))
            draw_text(screen, f"Final Score: {format_num(total_score)}", font_lg, GOLD, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 20))
            
            restart_rect = pygame.Rect(SCREEN_WIDTH // 2 - 125, SCREEN_HEIGHT // 2 + 30, 250, 60)
            btn_color = (60, 120, 60) if restart_rect.collidepoint(mouse_pos) else (40, 80, 40)
            pygame.draw.rect(screen, btn_color, restart_rect, border_radius=8)
            pygame.draw.rect(screen, GREEN, restart_rect, 2, border_radius=8)
            draw_text(screen, "START NEW RUN", font_lg, WHITE, (SCREEN_WIDTH // 2 - 105, SCREEN_HEIGHT // 2 + 45))
            
            if clicked and restart_rect.collidepoint(mouse_pos):
                plantfruit = 150.0  
                total_score = 0.0   
                reroll_cost = 50.0  
                plants = {} 
                craters = {}
                
                plant_data = generate_run_data()
                inventory = {p: 0 for p in plant_data.keys()}
                
                t1_plants = [p for p, d in plant_data.items() if d['tier'] == 1]
                inventory[random.choice(t1_plants)] = 2 
                
                selected_seed = None
                shop = Shop(plant_data)
                events = EventManager()
                empty_start_time = None
                game_over = False

            pygame.display.flip()
            clock.tick(60)
            continue

        # --- UPDATE STAGE ---
        events.update(plants, craters, total_score)
        shop.check_progression(total_score)
        
        now = time.time()
        expired_craters = [pos for pos, exp in craters.items() if now > exp]
        for pos in expired_craters:
            del craters[pos]

        dead_keys = []
        for pos, p in plants.items():
            yield_amount = p.get_yield()
            plantfruit += yield_amount
            total_score += yield_amount  
            if p.is_dead():
                dead_keys.append(pos)
                
        for k in dead_keys:
            del plants[k]

        if total_score >= 1000000:
            empty_time_limit = 0.1 
        else:
            reductions = total_score // 100000
            empty_time_limit = 10.0 - reductions

        if len(plants) == 0:
            if empty_start_time is None:
                empty_start_time = time.time()
            elif time.time() - empty_start_time >= empty_time_limit: 
                game_over = True
        else:
            empty_start_time = None

        # --- INTERACTION STAGE ---
        owned_plants = [p for p, qty in inventory.items() if qty > 0]
        ui_x = GARDEN_COLS * GRID_SIZE 

        if clicked:
            shop_rect = pygame.Rect(ui_x + 10, 230, 330, 40)
            if shop_rect.collidepoint(mouse_pos):
                shop.is_open = not shop.is_open

            if shop.is_open:
                for i, p_name in enumerate(shop.offerings):
                    btn_y = 290 + (i * 80)
                    btn_rect = pygame.Rect(ui_x + 20, btn_y, 310, 70)
                    cost = shop.get_adjusted_cost(p_name, total_score)
                    
                    if btn_rect.collidepoint(mouse_pos) and plantfruit >= cost:
                        plantfruit -= cost
                        inventory[p_name] += 1
                        available = [p for p, d in plant_data.items() if d['tier'] <= shop.tier]
                        shop.offerings[i] = random.choice(available)
                        
                ref_rect = pygame.Rect(ui_x + 20, 535, 310, 35)
                if ref_rect.collidepoint(mouse_pos) and plantfruit >= reroll_cost:
                    plantfruit -= reroll_cost
                    reroll_cost *= 1.20  
                    shop.refresh_offerings()

            for i, p_name in enumerate(owned_plants):
                inv_rect = pygame.Rect(10 + (i * 80), SCREEN_HEIGHT - 75, 70, 65)
                if inv_rect.collidepoint(mouse_pos):
                    selected_seed = p_name

            if not shop.is_open or mouse_pos[0] < GARDEN_COLS * GRID_SIZE:
                grid_x = mouse_pos[0] // GRID_SIZE
                grid_y = mouse_pos[1] // GRID_SIZE
                
                if 0 <= grid_x < GARDEN_COLS and 0 <= grid_y < GARDEN_ROWS:
                    cell = (grid_x, grid_y)
                    if cell not in plants and cell not in craters and selected_seed and inventory[selected_seed] > 0:
                        plants[cell] = Plant(selected_seed, grid_x, grid_y, plant_data)
                        inventory[selected_seed] -= 1
                        
                        if inventory[selected_seed] == 0:
                            selected_seed = None 

        # --- RENDER STAGE ---
        screen.fill((20, 20, 25))

        if events.current_event == "RAIN":
            bg_texture = assets["ui"].get("rain", assets["ui"]["default"])
        elif events.current_event == "DROUGHT":
            bg_texture = assets["ui"].get("drought", assets["ui"]["default"])
        elif events.current_event == "HAILSTORM":
            bg_texture = assets["ui"].get("hailstorm", assets["ui"]["default"])
        else:
            bg_texture = assets["ui"]["default"]

        for r in range(GARDEN_ROWS):
            for c in range(GARDEN_COLS):
                rect = (c * GRID_SIZE, r * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                
                screen.blit(bg_texture, rect[:2]) 
                pygame.draw.rect(screen, (50, 50, 50), rect, 1)

                cell = (c, r)
                if cell in craters:
                    screen.blit(assets["ui"]["crater"], rect[:2])

                if cell in plants:
                    p = plants[cell]
                    screen.blit(assets["plants"][p.type], (c * GRID_SIZE + 5, r * GRID_SIZE + 5))
                    life_ratio = p.get_life_ratio()
                    bar_w = GRID_SIZE - 10
                    pygame.draw.rect(screen, RED, (c * GRID_SIZE + 5, r * GRID_SIZE + GRID_SIZE - 8, bar_w, 4))
                    pygame.draw.rect(screen, GREEN, (c * GRID_SIZE + 5, r * GRID_SIZE + GRID_SIZE - 8, bar_w * (1 - life_ratio), 4))
                
                if pygame.Rect(rect).collidepoint(mouse_pos):
                    s = pygame.Surface((GRID_SIZE, GRID_SIZE))
                    s.set_alpha(50)
                    s.fill(WHITE)
                    screen.blit(s, rect[:2])

        pygame.draw.rect(screen, UI_BG, (0, SCREEN_HEIGHT - 100, SCREEN_WIDTH, 100))
        draw_text(screen, "INVENTORY (Click to select, Right-click clear)", font_sm, WHITE, (10, SCREEN_HEIGHT - 95))
        
        for i, p_name in enumerate(owned_plants):
            box_rect = (10 + (i * 80), SCREEN_HEIGHT - 75, 70, 65)
            color = GOLD if selected_seed == p_name else (80, 80, 80)
            pygame.draw.rect(screen, color, box_rect, 2)
            screen.blit(pygame.transform.scale(assets["plants"][p_name], (40, 40)), (box_rect[0] + 15, box_rect[1] + 5))
            draw_text(screen, f"x{inventory[p_name]}", font_sm, WHITE, (box_rect[0] + 25, box_rect[1] + 45))

        pygame.draw.rect(screen, (40, 40, 45), (ui_x, 0, 350, SCREEN_HEIGHT - 100))
        
        draw_text(screen, f"FRUIT: {format_num(plantfruit)}", font_lg, GREEN, (ui_x + 20, 20))
        draw_text(screen, f"SCORE: {format_num(total_score)}", font_lg, GOLD, (ui_x + 20, 55))
        draw_text(screen, f"CURRENT TIER: {shop.tier}/10", font_sm, BLUE, (ui_x + 20, 95))

        event_rect = (ui_x + 10, 130, 330, 80)
        pygame.draw.rect(screen, (60, 20, 20) if events.current_event else (30, 30, 30), event_rect, border_radius=5)
        
        if events.warning_event:
            draw_text(screen, f"WARNING: {events.warning_event}", font_sm, RED, (ui_x + 20, 145))
            draw_text(screen, f"Arriving in: {max(0, int(events.event_start - time.time()))}s", font_sm, WHITE, (ui_x + 20, 170))
        elif events.current_event:
            draw_text(screen, f"ACTIVE: {events.current_event}", font_sm, GOLD, (ui_x + 20, 145))
            draw_text(screen, f"Ends in: {max(0, int(events.event_end - time.time()))}s", font_sm, WHITE, (ui_x + 20, 170))
        else:
            draw_text(screen, "SKIES CLEAR", font_sm, GREEN, (ui_x + 20, 160))

        shop_btn_color = (100, 100, 150) if shop.is_open else (80, 80, 80)
        pygame.draw.rect(screen, shop_btn_color, (ui_x + 10, 230, 330, 40), border_radius=5)
        draw_text(screen, "TOGGLE SHOP", font_lg, WHITE, (ui_x + 80, 235))

        # --- SHOP & FORECAST MENU TOGGLE ---
        if shop.is_open:
            pygame.draw.rect(screen, (50, 50, 60), (ui_x + 10, 280, 330, 300), border_radius=5)
            for i, p_name in enumerate(shop.offerings):
                btn_y = 290 + (i * 80)
                data = plant_data[p_name]
                cost = shop.get_adjusted_cost(p_name, total_score)
                can_afford = plantfruit >= cost
                color = (40, 80, 40) if can_afford else (80, 40, 40)
                
                pygame.draw.rect(screen, color, (ui_x + 20, btn_y, 310, 70), border_radius=5)
                screen.blit(pygame.transform.scale(assets["plants"][p_name], (50, 50)), (ui_x + 30, btn_y + 10))
                draw_text(screen, f"{p_name} (T{data['tier']})", font_sm, WHITE, (ui_x + 90, btn_y + 10))
                draw_text(screen, f"Cost: {format_num(cost)} | Rate: {format_num(data['rate'])}/s", font_sm, GOLD, (ui_x + 90, btn_y + 35))

            pygame.draw.rect(screen, (80, 80, 120), (ui_x + 20, 535, 310, 35), border_radius=5)
            draw_text(screen, f"Refresh Offerings ({format_num(reroll_cost)} Fruit)", font_sm, WHITE, (ui_x + 60, 545))
        else:
            # Render Forecast Panel instead of Shop
            pygame.draw.rect(screen, (35, 40, 45), (ui_x + 10, 280, 330, 150), border_radius=5)
            draw_text(screen, "WEATHER FORECAST", font_lg, BLUE, (ui_x + 20, 290))
            
            f_color = (150, 150, 150) if events.forecast_text == "Unknown" else GOLD
            draw_text(screen, f"Predicting: {events.forecast_text}", font_sm, f_color, (ui_x + 20, 335))
            
            # Replaced exact numerical countdown with atmospheric flavor text
            if not events.warning_event and not events.current_event:
                draw_text(screen, "Monitoring atmosphere...", font_sm, (150, 150, 150), (ui_x + 20, 370))
            else:
                draw_text(screen, "Event in progress...", font_sm, (150, 150, 150), (ui_x + 20, 370))

        if selected_seed:
            screen.blit(assets["plants"][selected_seed], (mouse_pos[0] - 20, mouse_pos[1] - 20))

        # --- RENDER TOP-RIGHT OVERLAYS ---
        if events.meteor_flash_alpha > 0:
            flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash_surface.fill((255, 0, 0, events.meteor_flash_alpha))
            screen.blit(flash_surface, (0, 0))

        # The death timer drawn absolute last so it rests aggressively on top of the UI
        if empty_start_time is not None:
            time_left = empty_time_limit - (time.time() - empty_start_time)
            
            # Positioned strictly within the top-right of the garden grid
            timer_x = (GARDEN_COLS * GRID_SIZE) - 220
            timer_y = 10
            
            pygame.draw.rect(screen, (40, 10, 10), (timer_x, timer_y, 210, 60), border_radius=8)
            pygame.draw.rect(screen, RED, (timer_x, timer_y, 210, 60), 2, border_radius=8)
            draw_text(screen, "GARDEN EMPTY!", font_sm, RED, (timer_x + 40, timer_y + 10))
            draw_text(screen, f"Wither in: {max(0, time_left):.1f}s", font_sm, WHITE, (timer_x + 40, timer_y + 35))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()