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

import time
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from rag.retriever import retrieve_context
from llm.inference import run_llm

# Initialize the FastAPI application
app = FastAPI(title="GPU Worker Node (Dummy)")

class IncomingRequest(BaseModel):
    id: int
    query: str

# Create the single /process endpoint
@app.post("/process")
def process_task(request: IncomingRequest):
    print(f"[Worker] Received Task {request.id}: {request.query}")
    
    context = retrieve_context(request.query)

    result = run_llm(request.query, context)
    
    # Return the dummy response (FastAPI automatically converts this to JSON)
    return {
        "status": "Task Complete",
        "id": request.id,
        "latency": 2.0,
        "result": result
    }

if __name__ == "__main__":
    # Binding to 0.0.0.0 allows it to accept traffic from ZeroTier
    # Port 8000 is where this specific worker will listen
    print("Starting GPU Worker Node...")
    uvicorn.run(app, host="0.0.0.0", port=8000)