"""
model.py
--------
SwarmModel — central simulation model for Mesa 3.5.1.

Mesa 3.5.1 API (what changed from 2.x)
----------------------------------------
REMOVED:
  • mesa.time.RandomActivation       — gone entirely
  • self.schedule                    — gone entirely
  • self.schedule.steps              — replaced by self.steps (on Model)
  • self.schedule.agents             — replaced by self.agents (AgentSet)
  • self.schedule.add(agent)         — replaced by automatic registration;
                                       agents self-register on __init__
  • self.schedule.remove(agent)      — replaced by agent.remove()
  • self.schedule.step()             — replaced by self.agents.shuffle_do("step")

ADDED / CHANGED:
  • self.agents                      — built-in AgentSet, iterable, has len()
  • self.steps                       — built-in integer step counter on Model
  • self.agents.shuffle_do("step")   — activates all agents in random order
  • agent.remove()                   — removes agent from self.agents
  • mesa.spaces.MultiGrid            — 'space' module renamed to 'spaces' (plural)
                                       mesa.space (singular) still works as alias
                                       but mesa.spaces is the canonical 3.x import
"""

import math
import numpy as np

from mesa              import Model
from mesa.space        import MultiGrid          # 3.x canonical import
from mesa.datacollection import DataCollector

from agents import Creature
from utils  import generate_food_clusters


class SwarmModel(Model):

    def __init__(
        self,
        width:         int   = 60,
        height:        int   = 60,
        num_agents:    int   = 50,
        num_clusters:  int   = 12,
        food_coverage: float = 0.15,
        signal_range:  int   = 5,
        max_speed:     int   = 3,
        max_steps:     int   = 8000,
        seed                 = None,
    ):
        super().__init__(seed=seed)              # seed is keyword-only in Mesa 3.x

        # ── Parameters ────────────────────────────────────────────────── #
        self.width        = width
        self.height       = height
        self.num_agents   = num_agents
        self.nest_pos     = (width // 2, height // 2)
        self.signal_range = signal_range
        self.max_speed    = max_speed
        self.max_steps    = max_steps
        self.nest_food = 0.0          # current food stored in the nest
        self.nest_food_capacity = 200 # optional, to prevent infinite accumulation
        
        # ── Spatial grid ──────────────────────────────────────────────── #
        self.grid = MultiGrid(width, height, torus=False)

        # ── Food grid ─────────────────────────────────────────────────── #
        self.food_grid       = generate_food_clusters(
            width, height, num_clusters, food_coverage, self.random
        )
        self._food_collected = 0            # cumulative food eaten this run

        # ── Spawn agents ──────────────────────────────────────────────── #
        # In Mesa 3.5.1 agents self-register into self.agents on __init__.
        # There is NO schedule.add() — just create the agent and place it.
        for _ in range(num_agents):
            r         = self.random.random()
            role      = "forager" if r < 0.10 else ("scout" if r < 0.20 else "nurse")
            threshold = self.random.uniform(0.3, 0.7)
            agent     = Creature(self, role, 100.0, 36.0, threshold)
            self.grid.place_agent(agent, self.nest_pos)

        # ── Data collector ────────────────────────────────────────────── #
        # self.agents is the AgentSet; reporters iterate over it directly.
        self.datacollector = DataCollector(
            model_reporters={
                "Alive":    lambda m: len(m.agents),
                "Nurses":   lambda m: sum(1 for a in m.agents if a.role == "nurse"),
                "Foragers": lambda m: sum(1 for a in m.agents if a.role == "forager"),
                "Scouts":   lambda m: sum(1 for a in m.agents if a.role == "scout"),
                "AvgEnergy": lambda m: (
                    sum(a.energy for a in m.agents) / max(1, len(m.agents))
                ),
                "AvgTemp": lambda m: (
                    sum(a.temp for a in m.agents) / max(1, len(m.agents))
                ),
                "TotalFood":     lambda m: int(np.sum(m.food_grid)),
                "FoodCollected": lambda m: m._food_collected,
            },
            agent_reporters={
                "Energy": "energy",
                "Temp":   "temp",
                "Role":   "role",
                "Age":    "age",
            },
        )

        self.running = True

    # ------------------------------------------------------------------ #
    #  Step                                                                #
    # ------------------------------------------------------------------ #

    def step(self):
        food_before = int(np.sum(self.food_grid))

        # Mesa 3.5.1: activate all agents in random order
        self.agents.shuffle_do("step")
        self.communication_step()

        self._food_collected += max(0, food_before - int(np.sum(self.food_grid)))

        self.datacollector.collect(self)

        # self.steps is the built-in counter incremented by Model.step()
        # It is updated BEFORE our code runs, so compare with >= max_steps
        if len(self.agents) == 0 or self.steps >= self.max_steps:
            self.running = False

    # ------------------------------------------------------------------ #
    #  Communication                                                       #
    # ------------------------------------------------------------------ #

    def communication_step(self):
        """Broadcast each agent's outgoing signal to grid neighbours."""

        # 1. Clear inboxes
        for agent in self.agents:
            agent.received_signals = []

        # 2. Broadcast — signal strength decays with distance
        for agent in self.agents:
            if agent.signal_to_send is None:
                continue
            sig       = agent.signal_to_send
            neighbors = self.grid.get_neighbors(
                agent.pos, moore=True, radius=self.signal_range
            )
            for nbr in neighbors:
                dx   = nbr.pos[0] - agent.pos[0]
                dy   = nbr.pos[1] - agent.pos[1]
                dist = max(1.0, math.sqrt(dx * dx + dy * dy))
                decayed = sig["strength"] / (1.0 + dist * 0.15)
                nbr.received_signals.append({
                    "type":     sig["type"],
                    "strength": decayed,
                    "pos":      sig["pos"],
                })

        # 3. Clear outgoing signals
        for agent in self.agents:
            agent.signal_to_send = None
