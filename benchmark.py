from stable_baselines3 import PPO
from env.resource_env import ResourceEnv
from baseline.round_robin import RoundRobinScheduler
import numpy as np

def benchmark_rl(ticks=200):
    env = ResourceEnv()
    model = PPO.load("models/arbiter_ppo")
    obs, _ = env.reset()
    wait_times = []
    completed = 0

    for t in range(ticks):
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        completed = info["completed"]
        if terminated or truncated:
            break

    return {
        "completed": completed,
        "final_cpu": round(env.cpu_used, 2),
        "final_ram": round(env.ram_used, 2)
    }

def run_benchmark():
    print("Running RL agent benchmark...")
    rl_results = benchmark_rl()

    print("Running Round-Robin benchmark...")
    rr = RoundRobinScheduler()
    rr_results = rr.run()

    print("\n--- Benchmark Results ---")
    print(f"{'Metric':<20} {'RL Agent':>12} {'Round-Robin':>12}")
    print("-" * 46)
    print(f"{'Completed':<20} {rl_results['completed']:>12} {rr_results['completed']:>12}")
    print(f"{'Final CPU %':<20} {rl_results['final_cpu']:>12} {rr_results['final_cpu']:>12}")
    print(f"{'Final RAM %':<20} {rl_results['final_ram']:>12} {rr_results['final_ram']:>12}")
    print(f"{'Avg Wait Time':<20} {'N/A':>12} {rr_results['avg_wait_time']:>12}")

if __name__ == "__main__":
    run_benchmark()