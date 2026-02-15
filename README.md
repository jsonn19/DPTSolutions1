# DPT: Develop, Plant, Thrive

## Introduction

**DPT (Develop, Plant, Thrive)** is a 2D roguelike farming simulation built in Python using Pygame.

The project was developed around an overarching philosophical idea of impermanence, that being that nothing lasts forever. The game consists of the player selecting procedurally generated plants that eventually wither. Each plant produces a randomly generated value of fruit, that is tallied in the total score, and can be used to purchase other plants from the shop. Each plant has randomly generated values of output based on each tier (1-10). In essence, the roguelike nature of the game highlights the idea of impermanence, as no two games played will be the same. 

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

* Severity of event scales with total score
* Unreliable weather forecast system

### Shop System

* Tiers unlock as game continues on based on score
* Price inflation relative to score
* Refreshable shop offerings

### Survival Pressure

* A countdown begins whenever the garden is empty
* Countdown shortens as score increases, increasing difficulty

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/jsonn19/DPT-Develop-Plant-Thrive
cd DPT-Develop-Plant-Thrive
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
├── game.py          # Main game loop and visual rendering
├── func.py          # Functions, classes, utilities
├── plants.csv       # Plant sprites
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

* Deductions due to Locust
* Eclipse pauses
* Difficulty based on score

---

### Event Scaling

* Event frequency increases as score increases
* Drought severity increases at high scores
* Locusts become harsher over time
* Inflation increases plant cost every 50,000 score

---

### Tier Progression

Tier requirement formula:

```
required_score = 100 × (2.918 ^ (tier - 1))
```

Maximum Tier: **10**

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

## Contributors

* DPT Solutions: Michio Babcock, Alexander Kozyrev, Jason Louie, Jacob Mann, Muhammand Safwan-ul-Haque
* Built with VSCode using Pygame

## Version

* Version 4.12_DPT
