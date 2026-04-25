# client/run_load_test.py
import subprocess
import time
import sys

# Define how many CPU cores you want to use
NUM_WORKERS = 4


def start_locust_cluster():
    print("Starting Locust Master...")
    # Start the master process
    master_process = subprocess.Popen(["locust", "-f", "load_generator.py", "--master"])

    # Give the master a second to boot up before connecting workers
    time.sleep(2)

    worker_processes = []
    print(f"Starting {NUM_WORKERS} Locust Workers...")
    # Loop to start the worker processes
    for i in range(NUM_WORKERS):
        p = subprocess.Popen(["locust", "-f", "load_generator.py", "--worker"])
        worker_processes.append(p)
        print(f"Worker {i + 1} started.")

    print("\n--- Cluster is live! ---")
    print("Go to http://localhost:8089 in your browser to start the test.")
    print("Press Ctrl+C in this terminal to shut everything down.\n")

    try:
        # Keep the main script running so the background processes stay alive
        master_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down cluster...")
        master_process.terminate()
        for w in worker_processes:
            w.terminate()
        sys.exit(0)


if __name__ == "__main__":
    start_locust_cluster()