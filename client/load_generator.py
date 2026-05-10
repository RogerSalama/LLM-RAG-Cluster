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
from locust import events

from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv("API")
# ==============================================================
# 1. GRAFANA ANNOTATIONS SETUP (Token Auth)
# ==============================================================
GRAFANA_IP = "10.2.213.8"
GRAFANA_ANNOTATIONS_URL = f"http://{GRAFANA_IP}:3000/api/annotations"

# Your new Grafana API Token
GRAFANA_TOKEN = api_key
HEADERS = {
    "Authorization": f"Bearer {GRAFANA_TOKEN}",
    "Content-Type": "application/json"
}

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print(f"🚀 Test starting... Sending alert across ZeroTier to {GRAFANA_IP}!")
    payload = {"text": "🟢 Locust Load Test Started", "tags": ["locust", "start"]}
    try:
        # Replaced 'auth=' with 'headers='
        response = raw_requests.post(GRAFANA_ANNOTATIONS_URL, json=payload, headers=HEADERS, timeout=3)
        if response.status_code == 200:
            print("✅ Grafana successfully received the Start signal!")
        else:
            print(f"⚠️ Grafana returned an error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Failed to reach Grafana over ZeroTier: {e}")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print(f"🛑 Test stopped... Sending alert across ZeroTier to {GRAFANA_IP}!")
    payload = {"text": "🔴 Locust Load Test Stopped", "tags": ["locust", "stop"]}
    try:
        # Replaced 'auth=' with 'headers='
        raw_requests.post(GRAFANA_ANNOTATIONS_URL, json=payload, headers=HEADERS, timeout=10)
    except Exception as e:
        print(f"❌ Failed to reach Grafana over ZeroTier: {e}")
# ==============================================================
# 2. LOCUST LOAD TESTING LOGIC
# ==============================================================
request_counter = itertools.count(1)

RETRYABLE_STATUS = {0, 500, 502, 503, 504}
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
    # FIXED: Changed from 100-200 to 1-2 seconds!
    wait_time = between(5, 10)
    host = "http://10.2.213.200:8085"

    def on_start(self):
        self.session = raw_requests.Session()

    @task
    def test_rag_query(self):
        request_id = next(request_counter)
        payload = asdict(
            Request(id=request_id, query="i want to make a cake , maybe an orange cake , give me a recipie"))
        url = f"{self.host}/process"

        start_time = time.time()
        final_status = None
        final_exception = None
        response_length = 0

        for attempt in range(MAX_RETRIES):
            is_last = (attempt == MAX_RETRIES - 1)

            try:
                resp = self.session.post(url, json=payload, timeout=100)
                final_status = resp.status_code
                response_length = len(resp.content)

                node_id = resp.headers.get("X-Node-Addr", "Unknown Node")

                if resp.status_code == 200:
                    final_exception = None
                    break

                elif resp.status_code in RETRYABLE_STATUS:
                    if is_last:
                        final_exception = Exception(
                            f"All {MAX_RETRIES} retries exhausted. Final status: {resp.status_code}")
                    else:
                        logging.error(f"[Timestamp: {time.strftime('%H:%M:%S')}] [Req ID: {request_id}] Received status {resp.status_code} from {node_id} on attempt {attempt + 1}. Retrying...")
                        time.sleep(RETRY_DELAY)

                else:
                    final_exception = Exception(f"Non-retryable status: {resp.status_code}")
                    break

            except NETWORK_EXCEPTIONS as e:
                final_status = 0
                # FIXED: Corrected the backwards if-statement logic here
                if is_last:
                    final_exception = Exception(f"Network Error after {MAX_RETRIES} attempts: {type(e).__name__} - {e}")
                else:
                    logging.error(f"[Timestamp: {time.strftime('%H:%M:%S')}] [Req ID: {request_id}] Received status {resp.status_code} from {node_id} on attempt {attempt + 1}. Retrying...")
                    time.sleep(RETRY_DELAY)

        elapsed_ms = (time.time() - start_time) * 1000

        if final_exception:
            logging.error(f"[Req ID: {request_id}] Failed. Exception: {final_exception}")

        self.environment.events.request.fire(
            request_type="POST",
            name="/process",
            response_time=elapsed_ms,
            response_length=response_length,
            exception=final_exception,
            context={},
        )


class StepLoadShape(LoadTestShape):
    step_time = 20
    step_users = 100
    spawn_rate = 20
    max_users = 1000

    def tick(self):
        run_time = self.get_run_time()
        current_step = math.floor(run_time / self.step_time) + 1
        target_users = current_step * self.step_users

        if target_users > self.max_users:
            return None

        return (target_users, self.spawn_rate)