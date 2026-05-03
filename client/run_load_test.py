# client/run_load_test.py
import subprocess
import time
import sys
import os

# Define how many CPU cores you want to use
NUM_WORKERS = 4


def start_locust_cluster():
    print("Starting Locust Master...")

    # 1. Dynamically grab the absolute path to your project root (LLM-RAG-Cluster)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 2. Copy the current system environment variables and inject our project root
    custom_env = os.environ.copy()
    custom_env["PYTHONPATH"] = project_root

    # 3. Start the master process (Note: pointing to locustfile.py AND passing env)
    locustfile_path = os.path.join(project_root, "client", "load_generator.py")

    master_process = subprocess.Popen(
        # Replace "locust" with sys.executable and "-m", "locust"
        [sys.executable, "-m", "locust", "-f", locustfile_path, "--master"],
        env=custom_env,
        cwd=project_root,
    )

    # Give the master a second to boot up before connecting workers
    time.sleep(2)

    worker_processes = []
    print(f"Starting {NUM_WORKERS} Locust Workers...")
    # Loop to start the worker processes
    for i in range(NUM_WORKERS):
        p = subprocess.Popen(
            [sys.executable, "-m", "locust", "-f", locustfile_path, "--worker"],
            env=custom_env,
            cwd=project_root,
        )
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