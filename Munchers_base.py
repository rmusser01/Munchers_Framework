import random
import json
import os
from datetime import datetime


class Grid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cells = [[None for _ in range(width)] for _ in range(height)]

    def set_cell(self, x, y, content):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.cells[y][x] = content

    def get_cell(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.cells[y][x]
        return None


class Muncher:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.lives = 3
        self.score = 0
        self.munch_combo = 0

    def move(self, dx, dy, grid):
        new_x = self.x + dx
        new_y = self.y + dy
        if 0 <= new_x < grid.width and 0 <= new_y < grid.height:
            self.x = new_x
            self.y = new_y
            return True
        return False

    def munch(self, grid, rules):
        cell_value = grid.get_cell(self.x, self.y)
        if cell_value is not None and rules.check_valid(cell_value):
            grid.set_cell(self.x, self.y, None)
            self.munch_combo += 1
            self.score += self.munch_combo * 10  # Increase score based on combo
            return True
        else:
            self.munch_combo = 0
            return False


class Troggle:
    def __init__(self, x, y, behavior):
        self.x = x
        self.y = y
        self.behavior = behavior
        self.move_cooldown = 0
        self.direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])

    def move(self, grid, muncher):
        if self.move_cooldown > 0:
            self.move_cooldown -= 1
            return

        if self.behavior == "random":
            self._move_random(grid)
        elif self.behavior == "horizontal":
            self._move_horizontal(grid)
        elif self.behavior == "vertical":
            self._move_vertical(grid)
        elif self.behavior == "chase":
            self._move_chase(grid, muncher)

        self.move_cooldown = random.randint(1, 3)  # Add some randomness to movement speed

    def _move_random(self, grid):
        if random.random() < 0.2:  # 20% chance to change direction
            self.direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])

        new_x = self.x + self.direction[0]
        new_y = self.y + self.direction[1]

        if 0 <= new_x < grid.width and 0 <= new_y < grid.height:
            self.x, self.y = new_x, new_y
        else:
            self.direction = (-self.direction[0], -self.direction[1])  # Reverse direction if hitting a wall

    def _move_horizontal(self, grid):
        if self.direction[0] == 0:
            self.direction = random.choice([(1, 0), (-1, 0)])

        new_x = self.x + self.direction[0]

        if 0 <= new_x < grid.width:
            self.x = new_x
        else:
            self.direction = (-self.direction[0], 0)  # Reverse direction if hitting a wall

    def _move_vertical(self, grid):
        if self.direction[1] == 0:
            self.direction = random.choice([(0, 1), (0, -1)])

        new_y = self.y + self.direction[1]

        if 0 <= new_y < grid.height:
            self.y = new_y
        else:
            self.direction = (0, -self.direction[1])  # Reverse direction if hitting a wall

    def _move_chase(self, grid, muncher):
        dx = muncher.x - self.x
        dy = muncher.y - self.y

        if abs(dx) > abs(dy):
            self.direction = (1 if dx > 0 else -1, 0)
        else:
            self.direction = (0, 1 if dy > 0 else -1)

        new_x = self.x + self.direction[0]
        new_y = self.y + self.direction[1]

        if 0 <= new_x < grid.width and 0 <= new_y < grid.height:
            self.x, self.y = new_x, new_y


class GameRules:
    def __init__(self, rule_type, parameter):
        self.rule_type = rule_type
        self.parameter = parameter

    def check_valid(self, number):
        if self.rule_type == "multiples":
            return number % self.parameter == 0
        elif self.rule_type == "factors":
            return self.parameter % number == 0
        elif self.rule_type == "primes":
            if number < 2:
                return False
            for i in range(2, int(number ** 0.5) + 1):
                if number % i == 0:
                    return False
            return True
        return False


class HighScores:
    def __init__(self, filename="high_scores.json"):
        self.filename = filename
        self.scores = self.load_scores()

    def load_scores(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as file:
                return json.load(file)
        return []

    def save_scores(self):
        with open(self.filename, 'w') as file:
            json.dump(self.scores, file)

    def add_score(self, player_name, score):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.scores.append({"player": player_name, "score": score, "date": timestamp})
        self.scores.sort(key=lambda x: x["score"], reverse=True)
        self.scores = self.scores[:10]  # Keep only top 10 scores
        self.save_scores()

    def get_top_scores(self, n=10):
        return self.scores[:n]


class Game:
    def __init__(self, grid_width, grid_height):
        self.grid = Grid(grid_width, grid_height)
        self.muncher = Muncher(grid_width // 2, grid_height // 2)
        self.troggles = []
        self.rules = None
        self.level = 1
        self.numbers_to_munch = 0
        self.high_scores = HighScores()

    def start_level(self, rule_type, parameter):
        self.rules = GameRules(rule_type, parameter)
        self.populate_grid()
        self.spawn_troggles()
        self.numbers_to_munch = self.count_valid_numbers()

    def populate_grid(self):
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                self.grid.set_cell(x, y, random.randint(1, 100))

    def spawn_troggles(self):
        self.troggles = []  # Clear existing troggles
        num_troggles = self.level + 2  # Increase number of Troggles as levels progress
        behaviors = ["random", "horizontal", "vertical", "chase"]

        for _ in range(num_troggles):
            x = random.randint(0, self.grid.width - 1)
            y = random.randint(0, self.grid.height - 1)
            behavior = random.choice(behaviors)
            self.troggles.append(Troggle(x, y, behavior))

    def update(self):
        # Move Troggles
        for troggle in self.troggles:
            troggle.move(self.grid, self.muncher)

        # Check for collisions between Muncher and Troggles
        if self.check_collision():
            self.muncher.lives -= 1
            self.muncher.munch_combo = 0
            if self.muncher.lives <= 0:
                self.game_over()
            else:
                self.reset_muncher_position()

        # Check win condition
        if self.numbers_to_munch <= 0:
            self.next_level()

    def move_muncher(self, dx, dy):
        if self.muncher.move(dx, dy, self.grid):
            if self.muncher.munch(self.grid, self.rules):
                self.numbers_to_munch -= 1

    def check_collision(self):
        for troggle in self.troggles:
            if troggle.x == self.muncher.x and troggle.y == self.muncher.y:
                return True
        return False

    def reset_muncher_position(self):
        self.muncher.x = self.grid.width // 2
        self.muncher.y = self.grid.height // 2

    def count_valid_numbers(self):
        count = 0
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                if self.grid.get_cell(x, y) is not None and self.rules.check_valid(self.grid.get_cell(x, y)):
                    count += 1
        return count

    def next_level(self):
        self.level += 1
        print(f"Level {self.level} completed! Score: {self.muncher.score}")
        self.start_level(self.rules.rule_type, self.rules.parameter + 1)  # Increase difficulty

    def save_game(self, filename="savegame.json"):
        game_state = {
            "grid": self.grid.cells,
            "muncher": {
                "x": self.muncher.x,
                "y": self.muncher.y,
                "lives": self.muncher.lives,
                "score": self.muncher.score,
                "munch_combo": self.muncher.munch_combo
            },
            "troggles": [{"x": t.x, "y": t.y, "behavior": t.behavior} for t in self.troggles],
            "rules": {
                "rule_type": self.rules.rule_type,
                "parameter": self.rules.parameter
            },
            "level": self.level,
            "numbers_to_munch": self.numbers_to_munch
        }
        with open(filename, 'w') as file:
            json.dump(game_state, file)
        print(f"Game saved to {filename}")

    @classmethod
    def load_game(cls, filename="savegame.json"):
        with open(filename, 'r') as file:
            game_state = json.load(file)

        game = cls(len(game_state["grid"][0]), len(game_state["grid"]))
        game.grid.cells = game_state["grid"]
        game.muncher = Muncher(game_state["muncher"]["x"], game_state["muncher"]["y"])
        game.muncher.lives = game_state["muncher"]["lives"]
        game.muncher.score = game_state["muncher"]["score"]
        game.muncher.munch_combo = game_state["muncher"]["munch_combo"]
        game.troggles = [Troggle(t["x"], t["y"], t["behavior"]) for t in game_state["troggles"]]
        game.rules = GameRules(game_state["rules"]["rule_type"], game_state["rules"]["parameter"])
        game.level = game_state["level"]
        game.numbers_to_munch = game_state["numbers_to_munch"]

        print(f"Game loaded from {filename}")
        return game

    def game_over(self):
        print(f"Game Over! Final Score: {self.muncher.score}")
        player_name = input("Enter your name for the high score: ")
        self.high_scores.add_score(player_name, self.muncher.score)
        print("Top 10 High Scores:")
        for i, score in enumerate(self.high_scores.get_top_scores(), 1):
            print(f"{i}. {score['player']}: {score['score']} ({score['date']})")


# Example usage:
game = Game(6, 5)
game.start_level("multiples", 3)

# Simulate a few turns
for _ in range(20):
    game.move_muncher(random.choice([-1, 0, 1]), random.choice([-1, 0, 1]))
    game.update()

print(f"Current Level: {game.level}")
print(f"Muncher Score: {game.muncher.score}")
print(f"Muncher Lives: {game.muncher.lives}")
print(f"Numbers left to munch: {game.numbers_to_munch}")
print(f"Number of Troggles: {len(game.troggles)}")

# Save the game
game.save_game()

# Load the game
loaded_game = Game.load_game()

# Display high scores
print("\nTop 10 High Scores:")
for i, score in enumerate(loaded_game.high_scores.get_top_scores(), 1):
    print(f"{i}. {score['player']}: {score['score']} ({score['date']})")