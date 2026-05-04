"""
agents.py
---------
Creature agent: roles (nurse / forager / scout), movement, signals.

FINAL VERSION with:
- Nest food stock (trophallaxis)
- Buffed scouts and emergency nurse→scout conversion
- Foragers deposit food when eating and when returning to nest
- Balanced energy costs
"""

import math
from mesa import Agent


class Creature(Agent):

    def __init__(self, model, role: str, energy: float, temp: float, threshold: float):
        super().__init__(model)

        self.role      = role
        self.energy    = energy
        self.temp      = temp
        self.threshold = threshold

        self.signal_to_send   = None
        self.received_signals = []
        self.signal_memory    = []

        self.distance_moved   = 0.0
        self.visited_clusters = set()
        self.age              = 0

    # ------------------------------------------------------------------ #
    #  Main step                                                        #
    # ------------------------------------------------------------------ #

    def step(self):
        self.age += 1
        inside_nest = (self.pos == self.model.nest_pos)

        if   self.role == "nurse":   self.nurse_action(inside_nest)
        elif self.role == "forager": self.forager_action(inside_nest)
        elif self.role == "scout":   self.scout_action(inside_nest)

        self.update_energy_temp(inside_nest)
        self.check_death()

        for sig in self.received_signals:
            self.signal_memory.append(sig["type"])
        self.signal_memory = self.signal_memory[-10:]

    # ------------------------------------------------------------------ #
    #  Role actions                                                      #
    # ------------------------------------------------------------------ #

    def nurse_action(self, inside_nest: bool):
        if not inside_nest:
            self.move_toward(self.model.nest_pos)
            return

        # ── Consume from nest stock (trophallaxis) ──
        if self.model.nest_food > 0:
            consume = min(0.08, self.model.nest_food)
            self.energy = min(100.0, self.energy + consume)
            self.model.nest_food -= consume

        # ── EMERGENCY: critically low nest food + no recent food signals → become scout ──
        if self.model.nest_food < 5:
            recent_food = any(s in self.signal_memory[-10:] for s in ("FOOD", "NEW_FOOD"))
            if not recent_food:
                scout_count = sum(1 for a in self.model.agents if a.role == "scout")
                max_scouts = 8   # allow more scouts when starving
                scout_prob = 0.35
                if scout_count < max_scouts and self.model.random.random() < scout_prob:
                    self.role = "scout"
                    self.energy = min(120.0, self.energy + 15)   # boost for exploration
                    return

        # ── Normal recruitment nurse → forager based on food signals ──
        n = len(self.signal_memory)
        food_score = (
            sum(
                (i + 1) / n
                for i, s in enumerate(self.signal_memory)
                if s in ("FOOD", "NEW_FOOD")
            )
            if n > 0 else 0.0
        )
        stimulus = min(1.0, food_score / 4.0)

        # Dynamic threshold based on nest food (lower when hungry)
        if self.model.nest_food < 20:
            effective_threshold = self.threshold * 0.6
        else:
            effective_threshold = self.threshold

        if stimulus > effective_threshold:
            all_agents = list(self.model.agents)
            total = len(all_agents)
            if total > 0:
                forager_ratio = sum(1 for a in all_agents if a.role == "forager") / total
                if forager_ratio < 0.25:
                    self.role = "forager"
                    return

        # ── Nurse → scout (normal, weaker version) ──
        scout_count = sum(1 for a in self.model.agents if a.role == "scout")
        recent_food = any(s in self.signal_memory[-5:] for s in ("FOOD", "NEW_FOOD"))
        if scout_count < 4 and not recent_food and self.model.random.random() < 0.08:
            self.role = "scout"

    def forager_action(self, inside_nest: bool):
        in_danger = self.temp > 40 or self.energy < 30

        if in_danger:
            self.move_toward(self.model.nest_pos)
            if self.temp > 40:
                self.signal_to_send = {
                    "type": "DANGER", "strength": 0.9, "pos": self.pos
                }
        else:
            self.move_toward_signals()

        x, y = self.pos
        if self.model.food_grid[x][y] > 0:
            self.model.food_grid[x][y] -= 1
            self.energy = min(100.0, self.energy + 5.0)
            # Deposit food when eating
            deposit = 1.0
            self.model.nest_food = min(self.model.nest_food_capacity,
                                       self.model.nest_food + deposit)
            strength = min(1.0, self.model.food_grid[x][y] / 50.0 + 0.3)
            self.signal_to_send = {
                "type": "FOOD", "strength": strength, "pos": self.pos
            }

        # Trophallaxis: deposit a small amount when entering the nest
        if self.pos == self.model.nest_pos:
            deposit = max(0.5, self.energy * 0.05)   # 5% of current energy
            self.model.nest_food = min(self.model.nest_food_capacity,
                                       self.model.nest_food + deposit)
            # Emit a FOOD signal from the nest to recruit
            self.signal_to_send = {"type": "FOOD", "strength": 0.6, "pos": self.pos}
            if self.energy > 60:
                self.role = "nurse"

    def scout_action(self, inside_nest: bool):
        # Inside nest: if we have food intel, become forager; else nurse
        if self.pos == self.model.nest_pos:
            has_food_intel = any(s in self.signal_memory for s in ("FOOD", "NEW_FOOD"))
            if has_food_intel:
                self.role = "forager"
            else:
                self.role = "nurse"
            return

        # Overheating or low energy: return home (threshold raised to 20)
        if self.temp > 41 or self.energy < 20:
            self.move_toward(self.model.nest_pos)
            return

        self.random_walk()

        # Detect new food with lower threshold (20 instead of 50)
        x, y = self.pos
        if self.model.food_grid[x][y] > 20:
            cluster_id = (x // 3, y // 3)
            if cluster_id not in self.visited_clusters:
                self.visited_clusters.add(cluster_id)
                strength = min(1.0, self.model.food_grid[x][y] / 100.0)
                self.signal_to_send = {
                    "type": "NEW_FOOD", "strength": strength, "pos": self.pos
                }

    # ------------------------------------------------------------------ #
    #  Movement                                                         #
    # ------------------------------------------------------------------ #

    def move_toward_signals(self):
        valid  = [s for s in self.received_signals if s["type"] in ("FOOD", "NEW_FOOD")]
        danger = {s["pos"] for s in self.received_signals if s["type"] == "DANGER"}

        if valid:
            def score(s):
                dx   = s["pos"][0] - self.pos[0]
                dy   = s["pos"][1] - self.pos[1]
                dist = math.sqrt(dx * dx + dy * dy) + 0.1
                near_danger = any(
                    math.sqrt((s["pos"][0] - dp[0]) ** 2 + (s["pos"][1] - dp[1]) ** 2) < 3
                    for dp in danger
                )
                return (s["strength"] / dist) * (0.2 if near_danger else 1.0)

            best     = max(valid, key=score)
            follow_p = min(0.95, 0.60 + best["strength"] * 0.25)
            if self.model.random.random() < follow_p:
                self.move_toward(best["pos"])
                return

        self.random_walk()

    def move_toward(self, target_pos: tuple):
        x, y   = self.pos
        tx, ty = target_pos
        spd    = self.model.max_speed
        step_x = max(-spd, min(spd, tx - x))
        step_y = max(-spd, min(spd, ty - y))
        new_x  = max(0, min(self.model.width  - 1, x + step_x))
        new_y  = max(0, min(self.model.height - 1, y + step_y))
        self.distance_moved = max(abs(step_x), abs(step_y))
        self.model.grid.move_agent(self, (new_x, new_y))

    def random_walk(self):
        spd  = self.model.max_speed
        dx   = self.model.random.randint(-spd, spd)
        dy   = self.model.random.randint(-spd, spd)
        x, y = self.pos
        new_x = max(0, min(self.model.width  - 1, x + dx))
        new_y = max(0, min(self.model.height - 1, y + dy))
        self.distance_moved = max(abs(dx), abs(dy))
        self.model.grid.move_agent(self, (new_x, new_y))

    # ------------------------------------------------------------------ #
    #  Energy / temperature / death                                     #
    # ------------------------------------------------------------------ #

    def update_energy_temp(self, inside_nest: bool):
        # Balanced base costs: nurse 0.05, forager 0.10, scout 0.08
        base_cost = {"nurse": 0.05, "forager": 0.10, "scout": 0.08}.get(self.role, 0.1)
        self.energy -= base_cost + self.distance_moved * 0.04

        if inside_nest:
            self.temp = max(36.0, self.temp - 0.8)
        else:
            # Scouts heat up slightly slower
            heat_rate = 0.20 if self.role == "scout" else 0.25
            self.temp = min(42.0, self.temp + heat_rate)

        self.energy = max(0.0, min(100.0, self.energy))
        self.distance_moved = 0.0

    def check_death(self):
        if self.energy <= 0 or self.temp >= 42.0:
            self.model.grid.remove_agent(self)
            self.remove()