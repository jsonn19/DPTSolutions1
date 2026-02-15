# DPT: Develop, Plant, Thrive

## Introduction

**DPT (Develop, Plant, Thrive)** is a 2D roguelike farming simulation built in Python using Pygame.

The project was developed around the philosophical concept of impermanence. The idea that nothing lasts forever. In the game, plants grow, produce fruit, and eventually wither. A roguelike, by definition, is a game where every run is different, setting the stage for impermanence. The plants and tiers are randomly generated every time, and events occur in different orders via procedural generation. The events and disasters have the potential to ravage the entire grid, ending your run in an instant if you're in a later stage.

Each run features:

* Procedurally generated plant stats
* Dynamic weather systems with forecasting
* Scaling difficulty tied to player progression
* Tier-based shop unlocks
* Inflation mechanics
* Survival pressure if the garden becomes empty

The goal? **Grow, adapt, survive, and thrive your garden into a high-yield ecosystem.**
---

# Design Philosophy

DPT is intentionally designed so that:

Progress is temporary
Stability is fragile
Growth invites risk
Success accelerates collapse

The player is forced to face the idea that permanence is an illusion, directly tying gameplay mechanics to the inspiration.

Some mechanics were inspired by other roguelike games such as Balatro for the shop, and a non-roguelike Terraria for runs with different tiering. 

---

## Features

### Plant System

* Plants are divided into 10 tiers (1–10).
* Higher tiers produce greater yield but cost more.

**Plants have**:
* A production rate
* A lifespan
* A purchase cost
* All plant data is procedurally generated per run.

### Dynamic Weather & Events

* DROUGHT (accelerated aging)
* RAIN (lifespan boost)
* HAILSTORM (random plant destruction, leaves dents where plants cannot be added)
* LOCUSTS (yield reduction)
* ECLIPSE (production pause)
* METEOR (mass extinction + crater creation)

Includes:

* Weighted event probability
* Event severity scaling with score
* Unreliable weather forecast system

### Progressive Shop System

* Tier unlock progression
* Score-based tier advancement
* Dynamic price inflation
* Refreshable shop offerings

### Survival Pressure

* If garden becomes empty → countdown begins
* Countdown shortens as score increases, increasing difficulty

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/dpt-game.git
cd dpt-game
```

### 2. Install Dependencies

```bash
pip install pygame
```

### 3. Run the Game

```bash
python game.py
```

---

## Project Structure

```
dpt-game/
│
├── game.py          # Main game loop and rendering logic
├── func.py          # Core systems, classes, utilities
├── plants.csv       # Plant sprite manifest
├── assets/          # Images (plants + UI textures)
└── README.md        # README Markdown
```

---

## Usage

### Controls

| Action          | Input                |
| --------------- | -------------------- |
| Select seed     | Left-click inventory |
| Clear selection | Right-click          |
| Plant seed      | Left-click grid      |
| Toggle shop     | Click "TOGGLE SHOP"  |
| Buy plant       | Left-click offering  |
| Refresh shop    | Click refresh button |

---

## Game Mechanics

### Yield System

Each plant produces fruit continuously:

```
yield = base_rate × elapsed_time × modifiers
```

Modifiers include:

* Locust penalty
* Eclipse pause
* Score-scaled difficulty

---

### Event Scaling

* Event frequency increases as score increases.
* Drought severity increases at high scores.
* Locusts become harsher over time.
* Inflation increases plant cost every 50,000 score.

---

### Tier Progression

Tier requirement formula:

```
required_score = 100 × (2.918 ^ (tier - 1))
```

Maximum Tier: **10**

---

## Configuration

Located in `func.py`:

```python
GRID_SIZE = 70
GARDEN_ROWS = 8
GARDEN_COLS = 8
```

You can modify:

* Grid dimensions
* Screen resolution
* Event weights
* Inflation scaling
* Plant generation formulas

---

## Dependencies

* Python 3.10+
* `pygame`
* `csv`
* `random`
* `time`
* `os`

Install manually:

```bash
pip install pygame
```

---

## Example Gameplay Loop

1. Start with Tier 1 seeds.
2. Plant efficiently.
3. Accumulate fruit.
4. Buy higher-tier plants.
5. Survive escalating weather chaos.
6. Go for a high score while you
7. Avoid instant wipeout in late-game.

---

## Troubleshooting

### Images Not Loading?

* Ensure `plants.csv` sprite paths are correct.
* Confirm `assets/` directory exists.
* Missing images will auto-generate colored placeholders.

### Game Crashes on Start?

* Verify `pygame` is installed:

  ```bash
  pip install pygame
  ```

### Black Screen?

* Ensure your graphics drivers support SDL.
* Try running in a standard Python interpreter (not IDLE).

---

## Contributors

* DPT Solutions: Michio Babcock, Alexander Kozyrev, Jason Louie, Jacob Mann, Muhammand Safwan-ul-Haque
* Built with VSCode using Pygame
