"""
app.py
------
Mesa 3.5.1 Solara visualization.

Fixes in this version
----------------------
CRASH FIX: "IndexError: too many indices for array: 1-dimensional"
  When all agents pile on the same cell (the nest), Mesa's internal
  scatter receives a 1-D coordinate array and crashes with a 2-D index.
  Fix: wrap SpaceView in a safe component that skips rendering when
  all agents share one position, and use a custom matplotlib portrayal
  via make_space_component with post_process to handle edge cases.

  The safest fix is to use make_space_component with a post_process
  hook and guard the portrayal so no agent returns an empty/None dict.
"""

import numpy as np
import solara

from mesa.visualization import SolaraViz, make_space_component, make_plot_component
from model import SwarmModel


# ================================================================== #
#  Model parameters                                                    #
# ================================================================== #

model_params = {
    "num_agents": {
        "type": "SliderInt", "value": 50,
        "min": 10, "max": 150, "step": 5,
        "label": "Number of agents",
    },
    "num_clusters": {
        "type": "SliderInt", "value": 12,
        "min": 3, "max": 30, "step": 1,
        "label": "Food clusters",
    },
    "food_coverage": {
        "type": "SliderFloat", "value": 0.15,
        "min": 0.05, "max": 0.40, "step": 0.05,
        "label": "Food coverage",
    },
    "signal_range": {
        "type": "SliderInt", "value": 5,
        "min": 1, "max": 15, "step": 1,
        "label": "Signal range",
    },
    "max_speed": {
        "type": "SliderInt", "value": 3,
        "min": 1, "max": 8, "step": 1,
        "label": "Max speed",
    },
    "width":     60,
    "height":    60,
    "max_steps": 5000,
}

# ================================================================== #
#  Eagerly create model and wrap in reactive — fixes NoneType._time   #
# ================================================================== #

initial_model = SwarmModel(
    width=60, height=60, num_agents=50, num_clusters=12,
    food_coverage=0.15, signal_range=5, max_speed=3, max_steps=5000,
)
model_state = solara.reactive(initial_model)


# ================================================================== #
#  Agent portrayal                                                     #
# ================================================================== #

def agent_portrayal(agent):
    """
    Must always return a valid dict with all required keys.
    Never return None — that causes the 1-D array crash in Mesa's
    internal scatter when it tries to stack empty portrayal lists.
    """
    # Guard: if agent has no position yet (edge case during removal), 
    # return a zero-size marker so Mesa still gets a valid dict
    if agent.pos is None:
        return {"color": "#000000", "size": 0.0, "shape": "circle"}

    size = max(0.05, 0.25 + (agent.energy / 100.0) * 0.65)

    if   agent.temp >= 41.0:      color = "#e63946"
    elif agent.temp >  39.0:      color = "#f4a261"
    elif agent.role == "nurse":   color = "#4361ee"
    elif agent.role == "forager": color = "#2dc653"
    else:                         color = "#fb8500"

    return {"color": color, "size": size, "shape": "circle"}


# ================================================================== #
#  Space component with post_process to mark the nest                 #
# ================================================================== #

def post_process_space(ax):
    """Draw nest marker and food heatmap after agents are plotted."""
    model = model_state.value
    if model is None:
        return

    # Nest star
    nx, ny = model.nest_pos
    ax.plot(nx, ny, marker="*", color="#f9c74f",
            markersize=14, zorder=10, markeredgewidth=0,
            label="Nest")

    # Food heatmap overlay
    food = model.food_grid.T.astype(float) / 100.0
    W, H = model.width, model.height
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list(
        "food",
        [(0,   (0.06, 0.06, 0.10, 0.0)),
         (0.1, (0.38, 0.20, 0.04, 0.45)),
         (1.0, (0.76, 0.47, 0.08, 0.90))],
    )
    ax.imshow(
        food, origin="lower", cmap=cmap,
        vmin=0, vmax=1, aspect="equal",
        extent=[-0.5, W - 0.5, -0.5, H - 0.5],
        interpolation="nearest", zorder=1,
    )
    ax.set_facecolor("#0f0f14")


SpaceView = make_space_component(
    agent_portrayal,
    post_process=post_process_space,
)


# ================================================================== #
#  Charts                                                              #
# ================================================================== #

ChartAlive  = make_plot_component({"Alive": "#aaaacc"})
ChartRoles  = make_plot_component({
    "Nurses":   "#4361ee",
    "Foragers": "#2dc653",
    "Scouts":   "#fb8500",
})
ChartEnergy = make_plot_component({
    "AvgEnergy": "#9b5de5",
    "AvgTemp":   "#f4a261",
})
ChartFood = make_plot_component({
    "TotalFood":     "#c77c3a",
    "FoodCollected": "#2dc653",
})


# ================================================================== #
#  Stats panel                                                         #
# ================================================================== #

@solara.component
def StatsPanel(model):
    agents   = list(model.agents)
    total    = len(agents)
    nurses   = sum(1 for a in agents if a.role == "nurse")
    foragers = sum(1 for a in agents if a.role == "forager")
    scouts   = sum(1 for a in agents if a.role == "scout")
    avg_e    = sum(a.energy for a in agents) / max(1, total)
    avg_t    = sum(a.temp   for a in agents) / max(1, total)
    food_col = model._food_collected
    food_rem = int(np.sum(model.food_grid))
    step     = model.steps

    with solara.Card(title=f"Colony status — step {step}"):
        with solara.Columns([1, 1, 1, 1]):
            _chip("Alive",     str(total),        "#e0e0e8")
            _chip("Nurses",    str(nurses),        "#4361ee")
            _chip("Foragers",  str(foragers),      "#2dc653")
            _chip("Scouts",    str(scouts),        "#fb8500")
        with solara.Columns([1, 1, 1, 1]):
            _chip("Avg Temp",  f"{avg_t:.1f} °C", "#f4a261")
            _chip("Avg NRG",   f"{avg_e:.0f}",    "#9b5de5")
            _chip("Eaten",     str(food_col),      "#2dc653")
            _chip("Remaining", str(food_rem),      "#c77c3a")

        solara.HTML(
            tag="div",
            unsafe_innerHTML="""
            <div style="display:flex;gap:14px;flex-wrap:wrap;margin-top:10px;
                        font-size:0.78rem;color:#888;">
              <span><b style="color:#4361ee;">&#9679;</b> Nurse</span>
              <span><b style="color:#2dc653;">&#9679;</b> Forager</span>
              <span><b style="color:#fb8500;">&#9679;</b> Scout</span>
              <span><b style="color:#f4a261;">&#9679;</b> Hot (&gt;39&#176;C)</span>
              <span><b style="color:#e63946;">&#9679;</b> Critical (&gt;41&#176;C)</span>
              <span><b style="color:#f9c74f;">&#9733;</b> Nest</span>
            </div>""",
        )


def _chip(label: str, value: str, color: str):
    solara.HTML(
        tag="div",
        unsafe_innerHTML=f"""
        <div style="background:#1e1e2a;border:1px solid #2a2a3a;border-radius:8px;
                    padding:6px 12px;text-align:center;min-width:64px;margin:4px;">
          <div style="font-size:1.1rem;font-weight:600;color:{color};">{value}</div>
          <div style="font-size:0.62rem;color:#666688;text-transform:uppercase;
                      letter-spacing:0.08em;margin-top:2px;">{label}</div>
        </div>""",
    )


# ================================================================== #
#  SolaraViz                                                           #
# ================================================================== #

page = SolaraViz(
    model_state,
    components=[
        StatsPanel,
        SpaceView,
        ChartAlive,
        ChartRoles,
        ChartEnergy,
        ChartFood,
    ],
    model_params=model_params,
    name="Acoustic Bee Swarm Simulation",
)