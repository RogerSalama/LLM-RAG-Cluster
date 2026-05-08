import gevent.monkey
gevent.monkey.patch_all()
import time
import math
import itertools
import requests as raw_requests
import logging
from dataclasses import asdict
from locust import HttpUser, task, between, LoadTestShape
from common.models import Request

request_counter = itertools.count(1)

RETRYABLE_STATUS = {0, 500, 502, 503}
NETWORK_EXCEPTIONS = (
    ConnectionResetError,
    ConnectionAbortedError,
    raw_requests.exceptions.ConnectionError,
    raw_requests.exceptions.RequestException,
    raw_requests.exceptions.ChunkedEncodingError,
    EOFError,
)

MAX_RETRIES = 5
RETRY_DELAY = 3


class RAGUser(HttpUser):
    wait_time = between(1, 2)
    host = "http://10.2.213.200:8085"

    @task
    def test_rag_query(self):
        request_id = next(request_counter)
        payload = asdict(Request(id=request_id, query="i want to make a cake , give me a recipe."))
        url = f"{self.host}/process"

        start_time = time.time()
        final_status = None
        final_exception = None
        response_length = 0

        # --- Retry loop using raw requests (NOT Locust's client) ---
        # Nothing is reported to Locust until after this loop completes.
        for attempt in range(MAX_RETRIES):
            is_last = (attempt == MAX_RETRIES - 1)

            try:
                resp = raw_requests.post(url, json=payload, timeout=100)
                final_status = resp.status_code
                response_length = len(resp.content)

                if resp.status_code == 200:
                    # Genuine success — stop retrying immediately
                    break

                elif resp.status_code in RETRYABLE_STATUS:
                    if is_last:
                        # Ran out of retries — this is a real failure
                        final_exception = Exception(
                            f"All {MAX_RETRIES} retries exhausted. "
                            f"Final status: {resp.status_code}"
                        )
                    else:
                        time.sleep(RETRY_DELAY)

                else:
                    # 4xx or other — don't retry, it's a client-side issue
                    final_exception = Exception(f"Non-retryable status: {resp.status_code}")
                    break

            except NETWORK_EXCEPTIONS as e:
                final_status = 0
                final_exception = e
                if not is_last:
                    time.sleep(RETRY_DELAY)

        # --- Fire EXACTLY ONE event to Locust after all retries ---
        elapsed_ms = (time.time() - start_time) * 1000
        if final_exception:
            # This prints directly to the terminal running Locust
            logging.error(f"[Req ID: {request_id}] Failed after {MAX_RETRIES} attempts. Exception: {final_exception}")

        self.environment.events.request.fire(
            request_type="POST",
            name="/process",
            response_time=elapsed_ms,
            response_length=response_length,
            exception=final_exception,  # None = success, anything else = failure
            context={},
        )


class StepLoadShape(LoadTestShape):
    """
    Gradually increases load to find the breaking point of the GPUs.
    """
    step_time = 20  # Hold each user count for 20 seconds
    step_users = 100  # Add 100 users per step
    spawn_rate = 20  # Spawn 20 users per second during the ramp-up
    max_users = 1000  # Target maximum load

    def tick(self):
        run_time = self.get_run_time()

        # Calculate which step we are currently in
        current_step = math.floor(run_time / self.step_time) + 1
        target_users = current_step * self.step_users

        # If we exceed max_users, stop the test
        if target_users > self.max_users:
            return None

        return (target_users, self.spawn_rate)