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
        self.nest_pos=(width//2,height//2)
        self.grid=MultiGrid(width,height,torus=False)
        self.schedule=RandomActivation(self)        
        self.food_grid=generate_food_clusters(width,height,num_clusters,food_coverage,self.random)      
        
        for i in range(self.num_agents):
            rand = self.random.random()
            if rand < 0.1:
                role = "forager"
            elif rand < 0.2:
                role = "scout"
            else:
                role = "nurse"

            agent = Creature(i, self, role, 100, 36, self.random.uniform(0.3, 0.7))
            self.schedule.add(agent)
            self.grid.place_agent(agent, self.nest_pos)

        model_reporters = {"SurvivalTime": lambda m: m.schedule.steps if not m.schedule.agents else None,"Alive": lambda m: len(m.schedule.agents)}
        agent_reporters = {"Energy": "energy", "Temp": "temp", "Role": "role"}
        self.datacollector = DataCollector(
        model_reporters=model_reporters,
        agent_reporters=agent_reporters
        )
        self.running = True


    def step(self):
        print(f"Step {self.schedule.steps}")
        self.schedule.step()
        self.communication_step()
        self.datacollector.collect(self)
        if (len(self.schedule.agents)==0):
            self.running=False	
        

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