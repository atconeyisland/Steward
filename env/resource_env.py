import gymnasium as gym
import numpy as np
from gymnasium import spaces
from env.process_queue import ProcessQueue

class ResourceEnv(gym.Env):
    def __init__(self):
        super().__init__()

        self.max_cpu = 100
        self.max_ram = 100
        self.max_queue = 20

        # observation: [cpu_used, ram_used, queue_length, next_process_priority]
        self.observation_space = spaces.Box(
            low=np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], dtype=np.float32),
            high=np.array([100, 100, self.max_queue, 3, 35, 30, 3, 35, 30, 3, 35, 30], dtype=np.float32)
        )

        # actions: 0 = schedule, 1 = defer, 2 = kill
        self.action_space = spaces.Discrete(3)

        self.process_queue = ProcessQueue()
        self.cpu_used = 0.0
        self.ram_used = 0.0
        self.completed = 0
        self.tick = 0
        self.max_ticks = 200

    def _get_obs(self):
        obs = [self.cpu_used, self.ram_used, len(self.process_queue)]
        processes = sorted(list(self.process_queue.queue), key=lambda p: p["priority"], reverse=True)[:3]
        while len(processes) < 3:
            processes.append({"priority": 0, "cpu": 0, "ram": 0})
        for p in processes:
            obs.extend([p["priority"], p["cpu"], p["ram"]])
        return np.array(obs, dtype=np.float32)

    def step(self, action):
        reward = 0
        terminated = False

        if len(self.process_queue) > 0:
            process = self.process_queue.peek()

            if action == 0:  # schedule
                if (self.cpu_used + process["cpu"] <= self.max_cpu and
                        self.ram_used + process["ram"] <= self.max_ram):
                    self.cpu_used += process["cpu"]
                    self.ram_used += process["ram"]
                    self.process_queue.pop()
                    self.completed += 1
                    reward = 3.0
                else:
                    reward = -0.5

            elif action == 1:  # defer
                self.process_queue.defer()
                reward = -0.3 * (len(self.process_queue) / self.max_queue)

            elif action == 2:  # kill
                self.process_queue.pop()
                reward = -1.0

        else:
            reward = 0.0

        if np.random.rand() < 0.6:
            self.process_queue.add_random()

        self.cpu_used = max(0, self.cpu_used - np.random.uniform(8, 15))
        self.ram_used = max(0, self.ram_used - np.random.uniform(6, 12))

        if self.cpu_used > self.max_cpu or self.ram_used > self.max_ram:
            reward = -10.0
            terminated = True

        self.tick += 1
        if self.tick >= self.max_ticks:
            terminated = True

        return self._get_obs(), reward, terminated, False, {"completed": self.completed}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.cpu_used = 0.0
        self.ram_used = 0.0
        self.completed = 0
        self.tick = 0
        self.process_queue = ProcessQueue()
        return self._get_obs(), {}

    def render(self):
        print(f"Tick {self.tick} | CPU: {self.cpu_used:.1f}% | RAM: {self.ram_used:.1f}% | Queue: {len(self.process_queue)} | Completed: {self.completed}")