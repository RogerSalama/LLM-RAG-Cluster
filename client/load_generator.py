import sys
import os

# Force Python to recognize the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    #sys.path.append(project_root)
    sys.path.insert(0, project_root)  # Insert at the beginning to prioritize our project imports

# Your existing imports can go here
from common.models import Request
import math
import itertools
from dataclasses import asdict
from locust import HttpUser, task, between, LoadTestShape

# Import your model from the common package
from common.models import Request

# Create a thread-safe sequential counter starting at 1
request_counter = itertools.count(1)


class RAGUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def test_rag_query(self):
        # Grab the next sequential integer from the counter
        request_id = next(request_counter)

        # Instantiate the Request model (I also added the ID to the query string for easier tracking!)
        request_data = Request(id=request_id, query=f"hi")

        # Convert the dataclass instance to a dictionary for the POST request
        payload = asdict(request_data)

        # Send the request to your endpoint
        #self.client.post("/query", json=payload)
        self.client.post("/process", json=payload)


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