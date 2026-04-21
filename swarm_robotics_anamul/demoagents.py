"""
agents.py - Creature agent with roles, movement, signals.
Person B: implement role actions, energy/temp, death, signal emission.
Person A: implements movement methods (move_toward_signals, move_toward, random_walk).
"""

from mesa import Agent

class Creature(Agent):
    def __init__(self, unique_id, model, role, energy, temp, threshold):
        super().__init__(unique_id, model)
        self.role = role          # "nurse", "forager", "scout"
        self.energy = energy
        self.temp = temp
        self.threshold = threshold   # personal propensity to become forager (0..1)
        self.signal_to_send = None   # dict: {"type": str, "strength": float, "pos": (x,y)}
        self.received_signals = []   # filled by model.communication_step()
        self.signal_memory = []      # last 5 signal types (e.g., ["FOOD","FOOD","DANGER",...])
        self.distance_moved = 0      # store how far moved this step (for energy cost)

    def step(self):
        """
        TODO: Main agent step (Person B).
        1. inside_nest = (self.pos == self.model.nest_pos)
        2. Call role-specific action:
           if self.role == "nurse": self.nurse_action(inside_nest)
           elif self.role == "forager": self.forager_action(inside_nest)
           elif self.role == "scout": self.scout_action(inside_nest)
        3. self.update_energy_temp(inside_nest)
        4. self.check_death()
        5. (Optional) Update signal memory: add any received signal types, keep last 5
        """
        pass

    # ---------- Person B: role actions ----------
    def nurse_action(self, inside_nest):
        """
        Nurse behavior: stay in nest, cool down, maybe switch to forager.
        TODO: 
        - Only act if inside_nest is True.
        - Compute stimulus: count "FOOD" signals in self.signal_memory (max 5).
          stimulus = min(1.0, food_count / 5)
        - If stimulus > self.threshold: self.role = "forager"
        Hint: self.signal_memory is a list of strings like "FOOD", "NEW_FOOD", "DANGER".
        """
        pass

    def forager_action(self, inside_nest):
        """
        Forager behavior: move outside, find food, consume, return if exhausted.
        TODO:
        - If inside_nest: set self.role = "nurse" and return.
        - Call self.move_toward_signals()   # Person A
        - Check if current cell has food (self.model.food_grid[x][y] > 0):
            - Reduce food by 1: self.model.food_grid[x][y] -= 1
            - Increase energy: self.energy = min(100, self.energy + 2)
            - Set self.signal_to_send = {"type": "FOOD", "strength": 0.8, "pos": self.pos}
        - If self.temp > 40 or self.energy < 20:
            - Move toward nest: self.move_toward(self.model.nest_pos)  # Person A
        """
        pass

    def scout_action(self, inside_nest):
        """
        Scout behavior: explore randomly, discover new rich clusters.
        TODO:
        - If inside_nest: self.role = "nurse" (or random choice) and return.
        - Call self.random_walk()   # Person A
        - (Optional) Track visited clusters: store set of cluster IDs.
          If first time on a cell with food > 50 and cluster not visited:
            self.signal_to_send = {"type": "NEW_FOOD", "strength": 1.0, "pos": self.pos}
        - If self.temp > 41 or self.energy < 15:
            self.move_toward(self.model.nest_pos)
        """
        pass

    # ---------- Person A: movement methods ----------
    def move_toward_signals(self):
        """
        Move toward strongest FOOD or NEW_FOOD signal.
        TODO:
        - Iterate self.received_signals, find signal with highest "strength"
          where signal["type"] in ("FOOD", "NEW_FOOD").
        - If found and random.random() < 0.7: self.move_toward(signal["pos"])
        - Else: self.random_walk()
        """
        pass

    def move_toward(self, target_pos):
        """
        Move agent toward target_pos using Chebyshev distance (max speed = model.max_speed).
        TODO:
        - Compute dx = target_pos[0] - self.pos[0], dy = target_pos[1] - self.pos[1]
        - step_x = max(-self.model.max_speed, min(self.model.max_speed, dx))
        - step_y = max(-self.model.max_speed, min(self.model.max_speed, dy))
        - new_pos = (self.pos[0] + step_x, self.pos[1] + step_y)
        - Clamp to grid bounds (0 to width-1, 0 to height-1).
        - Store distance moved: self.distance_moved = max(abs(step_x), abs(step_y))
        - Use self.model.grid.move_agent(self, new_pos)
        """
        pass

    def random_walk(self):
        """
        Random movement within max_speed.
        TODO:
        - dx = self.model.random.randint(-self.model.max_speed, self.model.max_speed)
        - dy = self.model.random.randint(-self.model.max_speed, self.model.max_speed)
        - new_x = max(0, min(self.model.width-1, self.pos[0] + dx))
        - new_y = max(0, min(self.model.height-1, self.pos[1] + dy))
        - self.distance_moved = max(abs(dx), abs(dy))
        - self.model.grid.move_agent(self, (new_x, new_y))
        """
        pass

    # ---------- Person B: energy, temperature, death ----------
    def update_energy_temp(self, inside_nest):
        """
        Update energy and temperature based on time, movement, and location.
        TODO:
        - Energy decay: self.energy -= 0.1 + (self.distance_moved * 0.05)
        - Temperature: if inside_nest: self.temp -= 0.5 else: self.temp += 0.3
        - Clamp: self.energy = max(0, min(100, self.energy))
                 self.temp = max(0, min(42, self.temp))
        - Reset self.distance_moved = 0 for next step.
        """
        pass

    def check_death(self):
        """
        Remove agent if energy <= 0 or temp >= 42.
        TODO:
        - if self.energy <= 0 or self.temp >= 42:
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
        """
        pass