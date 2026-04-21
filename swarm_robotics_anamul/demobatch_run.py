"""
batch_run.py - Run multiple simulations with different seeds, collect survival times.
Person B: implement run_experiment function.
"""

from model import SwarmModel
import pandas as pd

def run_experiment(seeds=range(1, 21)):
    """
    Run SwarmModel for each seed, record survival time (steps until all dead).
    TODO:
    - results = []
    - for seed in seeds:
        - model = SwarmModel(seed=seed)
        - while model.running:
            model.step()
        - survival_time = model.schedule.steps   # steps executed
        - results.append({"seed": seed, "survival_time": survival_time})
    - df = pd.DataFrame(results)
    - df.to_csv("survival_results.csv", index=False)
    - return df
    """
    pass

if __name__ == "__main__":
    run_experiment()