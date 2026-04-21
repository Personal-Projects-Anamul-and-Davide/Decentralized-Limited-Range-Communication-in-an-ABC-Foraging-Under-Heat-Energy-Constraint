"""
server.py - Visualization server for Mesa.
Person B: implement agent_portrayal with role colors.
"""

from mesa.visualization import CanvasGrid, ChartModule
from mesa.visualization import ModularServer
from model import SwarmModel

def agent_portrayal(agent):
    """
    Return dictionary for drawing agent.
    TODO:
    - Map role to color:
        "nurse" -> "blue"
        "forager" -> "green"
        "scout" -> "orange"
    - Shape = "circle", r = 2, Filled = "true"
    - Optionally add text for energy? Not needed.
    """
    return {"Shape": "circle", "r": 2, "Color": "gray", "Filled": "true"}

grid = CanvasGrid(agent_portrayal, 60, 60, 600, 600)
chart = ChartModule([{"Label": "Alive", "Color": "black"}])
server = ModularServer(SwarmModel, [grid, chart], "Acoustic Bee Swarm")
server.port = 8521
server.launch()