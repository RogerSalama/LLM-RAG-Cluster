import math
from locust import HttpUser, task, between, LoadTestShape

class RAGUser(HttpUser):
    wait_time = between(1, 2)
    @task
    def test_rag_query(self):
        payload = {
            "query": "Sample LLM RAG Query"
        }
        self.client.post("/query", json=payload)
class StepLoadShape(LoadTestShape):
    step_time = 60  # Hold each user count for 60 seconds before stepping up
    step_users = 100  # Add 100 users per step
    spawn_rate = 50  # Spawn 50 users per second when ramping up to the next step
    max_users = 1000  # Cap at 1000 concurrent users

    def tick(self):
        run_time = self.get_run_time()
        current_step = math.floor(run_time / self.step_time) + 1
        target_users = current_step * self.step_users

        if target_users > self.max_users:
            return None  # Test completes after we finish the 1000-user step

        return (target_users, self.spawn_rate)

