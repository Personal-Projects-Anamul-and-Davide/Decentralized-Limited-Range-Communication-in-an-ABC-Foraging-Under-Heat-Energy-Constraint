"""
batch_run.py - Run multiple simulations with different seeds, collect survival times.
Person B: implement run_experiment function.
"""

from model import SwarmModel
import pandas as pd

def run_experiment(seeds=range(1, 21)):
    """
    Run SwarmModel for multiple seeds and collect survival times.
    """

    results = []

    for seed in seeds:
        # Initialize model with a fixed seed
        model = SwarmModel(seed=seed)

        # Run simulation until all agents die
        while model.running:
            model.step()

        # Number of steps survived
        survival_time = model.schedule.steps

        # Store result
        results.append({
            "seed": seed,
            "survival_time": survival_time
        })

        print(f"Seed {seed} completed → survival time: {survival_time}")

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Save results
    df.to_csv("survival_results.csv", index=False)

    return df

if __name__ == "__main__":
    run_experiment()