# # workers/gpu_worker.py
# import time
# from llm.inference import run_llm
# from rag.retriever import retrieve_context

# class GPUWorker:
#     def __init__(self, id):
#         self.id = id

#     def process(self, request):
#         start = time.time()
#         print(f"[Worker {self.id}] Processing request {request.id}")
        
#         # RAG Step
#         context = retrieve_context(request.query)
        
#         # LLM Step
#         result = run_llm(request.query, context)
        
#         latency = time.time() - start
#         return {
#             "id": request.id,
#             "result": result,
#             "latency": latency
#         }

import psutil
import time
import uvicorn
import pynvml
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from rag.retriever import retrieve_context
from llm.inference import run_llm

# 1. Initialize the FastAPI application FIRST
app = FastAPI(title="GPU Worker Node (Dummy)")

# 2. Global counter to track how busy the worker is
active_requests = 0

# Initialize NVIDIA Management Library and grab the first GPU (Index 0)
pynvml.nvmlInit()
gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)

@app.get("/metrics")
async def get_metrics():
    """The Load Balancer calls this to see how stressed this laptop is."""
    utilization = pynvml.nvmlDeviceGetUtilizationRates(gpu_handle)
    temperature = pynvml.nvmlDeviceGetTemperature(gpu_handle, pynvml.NVML_TEMPERATURE_GPU)
    return {
        "active_requests": active_requests,
        "gpu_usage": utilization.gpu,
        #could add ram usage, not sure yet
        "temperature": temperature,
        "ram_usage": psutil.virtual_memory().percent
    }

class IncomingRequest(BaseModel):
    id: int
    query: str

# Create the single /process endpoint.
# This is what the Load Balancer will call to send a task to this worker.
@app.post("/process")
def process_task(request: IncomingRequest):
    global active_requests # Let Python know we want to edit the global variable
    active_requests += 1   # Lock: Mark this worker as busier
    
    try:
        print(f"[Worker] Received Task {request.id}: {request.query}")
        
        context = retrieve_context(request.query)
        result = run_llm(request.query, context)
        
        # Return the response (FastAPI automatically converts this to JSON)
        return {
            "status": "Task Complete",
            "id": request.id,
            "latency": 2.0, 
            "result": result
        }
    finally:
        # Unlock: Free up the worker when done. 
        # Putting it in 'finally' ensures it drops even if the LLM crashes!
        active_requests -= 1 

if __name__ == "__main__":
    # Binding to 0.0.0.0 allows it to accept traffic from ZeroTier
    # Port 8000 is where this specific worker will listen
    print("Starting GPU Worker Node...")
    uvicorn.run(app, host="0.0.0.0", port=8000)