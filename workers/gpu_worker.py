import time
import uvicorn
from fastapi import FastAPI, Request

# Initialize the FastAPI application
app = FastAPI(title="GPU Worker Node (Dummy)")

# Create the single /process endpoint
@app.post("/process")
def process_task(request: Request):
    print("[Worker] Received a new task over the network!")
    
    # Simulate the heavy GPU inference and RAG retrieval delay
    time.sleep(2)
    
    # Return the dummy response (FastAPI automatically converts this to JSON)
    return {
        "status": "Task Complete", 
        "latency": 2.0,
        "message": "Sallam is tired."
    }

if __name__ == "__main__":
    # Binding to 0.0.0.0 allows it to accept traffic from ZeroTier
    # Port 8000 is where this specific worker will listen
    print("Starting GPU Worker Node...")
    uvicorn.run(app, host="0.0.0.0", port=8000)