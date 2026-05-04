"""
batch_run.py
------------
Run SwarmModel across multiple seeds and collect statistics.
Output: each seed + survival time + remaining agents.
Final: averages (mean, std, min, max) over all seeds for survival, food_collected, avg_energy, remaining_agents.
"""

import argparse
import statistics
import pandas as pd
from model import SwarmModel

def run_experiment(seeds=range(1, 21), **model_kwargs):
    results = []

    for seed in seeds:
        model = SwarmModel(seed=int(seed), **model_kwargs)

        while model.running:
            model.step()

        df_model = model.datacollector.get_model_vars_dataframe()
        survival_time = model.steps
        food_collected = model._food_collected
        remaining_agents = len(model.agents)
        avg_e_final = (
            round(float(df_model["AvgEnergy"].iloc[-1]), 2)
            if len(df_model) > 0 else 0.0
        )

        # Print seed, survival time, and remaining agents
        print(f"Seed {seed:3d} | survival {survival_time:5d} | remaining {remaining_agents:3d}")

        results.append({
            "seed": seed,
            "survival_time": survival_time,
            "remaining_agents": remaining_agents,
            "food_collected": food_collected,
            "avg_energy_final": avg_e_final,
        })

    df = pd.DataFrame(results)
    df.to_csv("survival_results.csv", index=False)

    print("\n=== Summary over all seeds ===")
    for col in ["survival_time", "remaining_agents", "food_collected", "avg_energy_final"]:
        vals = df[col].tolist()
        mean = statistics.mean(vals)
        stdev = statistics.stdev(vals) if len(vals) > 1 else 0.0
        print(f"  {col:<18} mean={mean:8.1f}  std={stdev:7.1f}  min={min(vals)}  max={max(vals)}")

    return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=20, help="Number of seeds (1..N)")
    parser.add_argument("--agents", type=int, default=50, help="num_agents")
    parser.add_argument("--clusters", type=int, default=12, help="num_clusters")
    parser.add_argument("--coverage", type=float, default=0.15, help="food_coverage")
    parser.add_argument("--signal", type=int, default=5, help="signal_range")
    parser.add_argument("--speed", type=int, default=3, help="max_speed")
    parser.add_argument("--maxsteps", type=int, default=5000, help="max_steps per run")
    args = parser.parse_args()

    run_experiment(
        seeds=range(1, args.seeds + 1),
        num_agents=args.agents,
        num_clusters=args.clusters,
        food_coverage=args.coverage,
        signal_range=args.signal,
        max_speed=args.speed,
        max_steps=args.maxsteps,
    )