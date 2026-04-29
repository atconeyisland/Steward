from stable_baselines3 import PPO
from env.resource_env import ResourceEnv
from baseline.round_robin import RoundRobinScheduler
from baseline.fcfs import FCFSScheduler
from baseline.priority_scheduler import PriorityScheduler
from baseline.sjf import SJFScheduler

def benchmark_rl(ticks=200):
    env = ResourceEnv()
    model = PPO.load("models/steward_ppo")
    obs, _ = env.reset()

    for t in range(ticks):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        if terminated or truncated:
            break

    return {
        "completed": info["completed"],
        "avg_wait_time": "N/A",
        "final_cpu": round(env.cpu_used, 2),
        "final_ram": round(env.ram_used, 2)
    }

def run_benchmark():
    print("Running all schedulers...\n")

    results = {
        "RL Agent (Steward)": benchmark_rl(),
        "Round-Robin":        RoundRobinScheduler().run(),
        "FCFS":               FCFSScheduler().run(),
        "Priority":           PriorityScheduler().run(),
        "SJF":                SJFScheduler().run(),
    }

    metrics = ["completed", "avg_wait_time", "final_cpu", "final_ram"]
    labels  = ["Processes Completed", "Avg Wait Time", "Final CPU %", "Final RAM %"]

    col_w = 22
    header = f"{'Metric':<25}" + "".join(f"{k:>{col_w}}" for k in results)
    print(header)
    print("-" * len(header))

    for metric, label in zip(metrics, labels):
        row = f"{label:<25}" + "".join(f"{str(v[metric]):>{col_w}}" for v in results.values())
        print(row)

if __name__ == "__main__":
    run_benchmark()