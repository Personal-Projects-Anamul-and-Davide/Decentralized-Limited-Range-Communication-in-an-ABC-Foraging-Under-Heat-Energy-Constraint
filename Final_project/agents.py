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
        self.visited_clusters = set()
        
    def step(self):
        # 1. Check if agent is inside the nest
        inside_nest = (self.pos == self.model.nest_pos)

        # 2. Execute behavior based on role
        if self.role == "nurse":
            self.nurse_action(inside_nest)
        elif self.role == "forager":
            self.forager_action(inside_nest)
        elif self.role == "scout":
            self.scout_action(inside_nest)

        # 3. Update energy and temperature
        self.update_energy_temp(inside_nest)
        # 4. Check if agent dies
        self.check_death()
        # 5. Update signal memory (last 5 signals)
        for sig in self.received_signals:
            self.signal_memory.append(sig["type"])
        # Keep only last 5
        self.signal_memory = self.signal_memory[-5:]

    # ---------- Person B: role actions ----------
    def nurse_action(self, inside_nest):
        if not inside_nest:
            return

        # Count FOOD signals in last 5 steps
        food_count = self.signal_memory.count("FOOD") + self.signal_memory.count("NEW_FOOD")

        # Normalize stimulus
        stimulus = min(1.0, food_count / 5)

        # Role switch
        if stimulus > self.threshold:
            self.role = "forager"

    def forager_action(self, inside_nest):
        
        # Move (Person A function)
        self.move_toward_signals()

        x, y = self.pos

        # Check food on current cell
        if self.model.food_grid[x][y] > 0:
            # Eat 1 unit
            self.model.food_grid[x][y] -= 1

            # Gain energy
            self.energy = min(100, self.energy + 2)

            # Send FOOD signal
            self.signal_to_send = {
                "type": "FOOD",
                "strength": 0.8,
                "pos": self.pos
            }

        # Danger / exhaustion -> go back
        if self.temp > 40 or self.energy < 20:
            self.move_toward(self.model.nest_pos)

         # If back at nest after moving, become nurse
        if self.pos == self.model.nest_pos:
            self.role = "nurse"

    def scout_action(self, inside_nest):

        # Explore randomly
        self.random_walk()

        x, y = self.pos

        # Detect rich food
        if self.model.food_grid[x][y] > 50:
            cluster_id = (x, y)  # simple approximation

            if cluster_id not in self.visited_clusters:
                self.visited_clusters.add(cluster_id)

                self.signal_to_send = {
                    "type": "NEW_FOOD",
                    "strength": 1.0,
                    "pos": self.pos
                }

        # Danger condition
        if self.temp > 41 or self.energy < 15:
            self.move_toward(self.model.nest_pos)

        if self.pos == self.model.nest_pos:
        # Random choice after returning
            if self.model.random.random() < 0.5:
                self.role = "nurse"
            else:
                self.role = "forager"
    # ---------- Person B: movement methods ----------
    def move_toward_signals(self):
    # Filter only relevant signals
        valid_signals = [
            s for s in self.received_signals
            if s["type"] in ("FOOD", "NEW_FOOD")
        ]

        # If there are signals, choose the strongest
        if valid_signals:
            strongest = max(valid_signals, key=lambda s: s["strength"])

            # With probability 0.7 follow the signal
            if self.model.random.random() < 0.7:
                self.move_toward(strongest["pos"])
                return

        # Otherwise random movement
        self.random_walk()

    def move_toward(self, target_pos):
        x, y = self.pos
        tx, ty = target_pos

        # Compute direction vector
        dx = tx - x
        dy = ty - y

        # Clamp movement to max_speed
        step_x = max(-self.model.max_speed, min(self.model.max_speed, dx))
        step_y = max(-self.model.max_speed, min(self.model.max_speed, dy))

        # New position
        new_x = x + step_x
        new_y = y + step_y

        # Clamp inside grid bounds
        new_x = max(0, min(self.model.width - 1, new_x))
        new_y = max(0, min(self.model.height - 1, new_y))

        # Chebyshev distance = max(|dx|, |dy|)
        self.distance_moved = max(abs(step_x), abs(step_y))

        # Move agent
        self.model.grid.move_agent(self, (new_x, new_y))

    def random_walk(self):
        # Random step in both directions
        dx = self.model.random.randint(-self.model.max_speed, self.model.max_speed)
        dy = self.model.random.randint(-self.model.max_speed, self.model.max_speed)

        x, y = self.pos

        # Compute new position
        new_x = x + dx
        new_y = y + dy

        # Clamp to grid bounds
        new_x = max(0, min(self.model.width - 1, new_x))
        new_y = max(0, min(self.model.height - 1, new_y))

        # Store distance (Chebyshev)
        self.distance_moved = max(abs(dx), abs(dy))

        # Move agent
        self.model.grid.move_agent(self, (new_x, new_y))

    # ---------- Person B: energy, temperature, death ----------
    def update_energy_temp(self, inside_nest):
        # Energy decay
        self.energy -= 0.1 + (self.distance_moved * 0.05)

        # Temperature dynamics
        if inside_nest:
            self.temp -= 0.5
        else:
            self.temp += 0.3

        # Clamp values
        self.energy = max(0, min(100, self.energy))
        self.temp = max(0, min(42, self.temp))

        # Reset movement
        self.distance_moved = 0

    def check_death(self):
        """
        Remove agent if energy <= 0 or temp >= 42.
        """
        if self.energy <= 0 or self.temp >= 42:
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
