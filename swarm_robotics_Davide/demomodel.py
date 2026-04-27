"""
model.py - Central simulation model.
Person A: implement __init__, step, communication_step.
Hints: Use MultiGrid, RandomActivation, DataCollector.
"""

import numpy as np
from mesa import Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from agents import Creature
from utils import generate_food_clusters

class SwarmModel(Model):
    def __init__(self, width=60, height=60, num_agents=50,num_clusters=12, food_coverage=0.15,signal_range=5, max_speed=3,seed=None):	    	    
        super().__init__(seed=seed)
        self.width=width
	    self.height=height
	    self.num_agents=num_agents
	    self.num_clusters=num_clusters
	    self.food_coverage=food_coverage
	    self.signal_range=signal_range
	    self.max_speed=max_speed
 	    self.__seed=seed
	    self.nest_pos=(width/2,height/2)
	    self.grid=MultiGrid(width,height,torus=False)
	    self.schedule=RandomActivation(self)
	
	    self.food_grid=generate_food_clusters(width,height,num_clusters,food_coverage,self.random)
	
	    for i in range (self.num_agents):
		    agent=Creature(creat_id=i, model=self, role="nurse", energy=100, temp=36, threshold=self.random.uniform(0.3,0.7))
		    self.schedule.add(agent)
		    self.grid.place_agent(agent,self.nest_pos)

        model_reporters = {"SurvivalTime": lambda m: m.schedule.steps if not m.schedule.agents else None,"Alive": lambda m: len(m.schedule.agents)}
        agent_reporters = {"Energy": "energy", "Temp": "temp", "Role": "role"}
        self.datacollector = DataCollector(...)
"""
        TODO: 
        1. Call super().__init__(seed=seed) to initialize Mesa's RNG. Done
        2. Store all parameters as self.xxx. Done 
        3. Create a MultiGrid with torus=False (walls at edges). Done 
        4. Create a RandomActivation schedule. Done 
        5. Set self.nest_pos = (width//2, height//2). Done 
        6. Generate food grid: self.food_grid = generate_food_clusters(
               width, height, num_clusters, food_coverage, self.random)   Done
        7. Create num_agents creatures:
           - Each gets a unique id (start from 0).
           - Random threshold = self.random.uniform(0.3, 0.7)
           - Initial role = "nurse", energy=100.0, temp=36.0
           - agent = Creature(unique_id, self, role, energy, temp, threshold)
           - Place agent at self.nest_pos using self.grid.place_agent()
           - Add agent to self.schedule	Done
        8. Initialize DataCollector:
           - model_reporters = {"SurvivalTime": lambda m: m.schedule.steps if not m.schedule.agents else None,
                                "Alive": lambda m: len(m.schedule.agents)}
           - agent_reporters = {"Energy": "energy", "Temp": "temp", "Role": "role"}
           - self.datacollector = DataCollector(...) Done
        """
        pass

    def step(self):
	    self.schedule.step()
	    self.communication.step()
	    self.datacollector.collect(self)
	    if (len(self.schedule.agents)==0) :
		    self.running=False	
        """
        TODO: Execute one full simulation step.
        1. self.schedule.step()   # all agents act
        2. self.communication_step()   # exchange signals
        3. self.datacollector.collect(self)
        4. If len(self.schedule.agents) == 0: self.running = False		Done 
        """
        pass

    def communication_step(self):
        for agent in self.schedule.agents:
            agent.received_signals=[]
        for agent in self.schedule.agents:
            if agent.signal_to_send is not None:
                neighbors=self.grid.get_neighbors(agent.pos, moore=True, radius=self.signal_range )
            for neighbor in neighbors:
                neighbor.received_signals.append(agent.signal_to_send.copy())
        for agent in self.schedule.agents:
            agent.signal_to_send=None
        """
        TODO: Exchange acoustic signals between agents.
        Steps:
        - Clear received_signals for all agents: agent.received_signals = []
        - For each agent that has signal_to_send (not None):
            - Find all agents within Chebyshev distance <= self.signal_range.
              Use self.grid.get_neighbors(agent.pos, moore=True, radius=self.signal_range)
            - For each neighbor, append a copy of the signal to neighbor.received_signals
        - After distributing, clear each agent's signal_to_send = None
        Hint: signals are dicts with keys: "type", "strength", "pos"
        """
        pass