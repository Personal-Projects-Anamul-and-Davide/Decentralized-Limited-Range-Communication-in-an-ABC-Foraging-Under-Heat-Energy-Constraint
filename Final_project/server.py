"""
server.py - Visualization server for Mesa.
Person B: implement agent_portrayal with role colors.
"""

from mesa.visualization import CanvasGrid, ChartModule
from mesa.visualization import ModularServer
from model import SwarmModel

def agent_portrayal(agent):
    """
    Defines how each agent is drawn on the grid.
    """

    # Map roles to colors
    if agent.role == "nurse":
        color = "blue"
    elif agent.role == "forager":
        color = "green"
    elif agent.role == "scout":
        color = "orange"
    else:
        color = "gray"  # fallback (should not happen)

    return {
        "Shape": "circle",
        "r": 0.8,
        "Color": color,
        "Filled": "true",
        "Layer": 0
        
    }

grid = CanvasGrid(agent_portrayal, 60, 60, 600, 600)
chart = ChartModule([{"Label": "Alive", "Color": "black"}])
server = ModularServer(SwarmModel, [grid, chart], "Acoustic Bee Swarm")
server.port = 8521
server.launch()