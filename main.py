# main.py
import subprocess
import sys
import time
from client.run_load_test import start_locust_cluster

def main():
    print("--- Booting up LLM-RAG Cluster Architecture ---")
    
    print("Starting Smart Load Balancer...")
    # 1. Start the Load Balancer as a background process
    # Using sys.executable ensures it uses your exact Python environment
    lb_process = subprocess.Popen([sys.executable, "lb/smart_balancer.py"])
    
    # 2. Give the FastAPI server a couple of seconds to fully start and bind to the port
    time.sleep(2)
    
    try:
        # 3. Start the Locust Load Generators (this will block the script until you hit Ctrl+C)
        start_locust_cluster()
    except KeyboardInterrupt:
        # Locust handles its own shutdown, we just need to catch the signal here
        pass 
    finally:
        # 4. Safely tear down the Load Balancer when the script exits
        print("\nShutting down Smart Load Balancer...")
        lb_process.terminate()
        lb_process.wait()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()