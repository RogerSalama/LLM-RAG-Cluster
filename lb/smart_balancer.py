import asyncio
import httpx
from fastapi import FastAPI, Request, HTTPException
import uvicorn

app = FastAPI(title="Smart Load-Aware Balancer")

# List your ZeroTier Worker IPs here
WORKER_NODES = [
    "http://10.2.213.82:8000", #Seif
    "http://10.2.213.176:8000",#Sallam
    "http://10.2.213.8:8000",  #Ashraf
    "http://10.2.213.91:8000", #Roger
    #"http://10.2.213.81:8000", #Andrew
    # Add your other laptops here
]

# The live scorecard
worker_health = {node: {"active_requests": 0, "gpu_usage": 0, "temperature": 0, "alive": True} for node in WORKER_NODES}


async def check_worker_health():
    """Background task: Polls workers every 2 seconds to update the scorecard."""
    async with httpx.AsyncClient(timeout=1.0) as client:
        while True:
            for node in WORKER_NODES:
                try:
                    response = await client.get(f"{node}/metrics")
                    if response.status_code == 200:
                        data = response.json()
                        worker_health[node].update(data)
                        #worker_health[node] = response.json()
                        worker_health[node]["alive"] = True
                except Exception:
                    # If the worker crashes or goes offline, mark it dead
                    worker_health[node]["alive"] = False
                    print(f"[Warning] Worker {node} is DOWN.")
            
            await asyncio.sleep(2) # Wait 2 seconds before checking again

@app.on_event("startup")
async def startup_event():
    # Start the background health checker when the balancer boots
    asyncio.create_task(check_worker_health())


def get_best_worker():
    """The Load-Aware Routing Algorithm."""
    alive_workers = {k: v for k, v in worker_health.items() if v["alive"]}
    
    ### step 1: filter out dead workers
    if not alive_workers:
        raise HTTPException(status_code=503, detail="CRITICAL:All worker nodes are dead.")

    ### step 2: thermal cutoff, if any gpu is overheating skip it.
    # filter out any laptops with more than 85c
    cool_workers = {k: v for k, v in alive_workers.items() if v["temperature"] < 85}

    ### if every laptop is overheating, fall back to using all live laptops
    # so we don't completely drop off all locust traffic.
    target_pool = cool_workers if cool_workers else alive_workers
    
    ### step 3: sort by fewest active requests, then by lowest GPU usage
    best_node = min(
        target_pool.keys(), 
        key=lambda n: (target_pool[n]["active_requests"], target_pool[n]["gpu_usage"])
    )
    return best_node

@app.post("/process")
async def route_traffic(request: Request):
    """Intercepts traffic from Locust and forwards it to the best worker."""
    best_node = get_best_worker()
    
    # Extract the JSON payload sent by Locust
    payload = await request.json()
    
    # Forward the request to the chosen worker
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(f"{best_node}/process", json=payload)
            return response.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to reach worker: {str(e)}")

if __name__ == "__main__":
    print("Starting Smart Load Balancer on Port 80...")
    # Run on Port 80 so Locust can easily find it
    uvicorn.run(app, host="0.0.0.0", port=80)