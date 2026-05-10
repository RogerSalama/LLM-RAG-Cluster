# workers/gpu_worker.py
import time
import asyncio
import pynvml
import psutil
import uvicorn
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Gauge, Counter

# Local imports from your project
from rag.retriever import retrieve_context
from llm.inference import run_llm

app = FastAPI(title="GPU Worker Node")

pynvml.nvmlInit()
gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)

# --- Define Prometheus Custom Metrics ---
GPU_TEMP = Gauge('gpu_temperature_celsius', 'Current GPU temperature')
GPU_UTIL = Gauge('gpu_utilization_percent', 'GPU compute utilization')
GPU_MEM_USED = Gauge('gpu_memory_used_bytes', 'GPU VRAM usage in bytes')
SYSTEM_RAM = Gauge('system_ram_usage_percent', 'Host RAM usage percentage')
CPU_UTIL = Gauge('cpu_utilization_percent', 'Host CPU usage percentage') # NEW
ACTIVE_TASKS = Gauge('worker_active_tasks', 'Number of LLM tasks currently processing')

# NEW: Counter with labels to categorize error types
WORKER_ERRORS = Counter('worker_errors_total', 'Count of worker errors', ['error_type'])

def update_hardware_metrics():
    try:
        util = pynvml.nvmlDeviceGetUtilizationRates(gpu_handle)
        temp = pynvml.nvmlDeviceGetTemperature(gpu_handle, 0)
        mem = pynvml.nvmlDeviceGetMemoryInfo(gpu_handle)

        GPU_TEMP.set(temp)
        GPU_UTIL.set(util.gpu)
        GPU_MEM_USED.set(mem.used)
        SYSTEM_RAM.set(psutil.virtual_memory().percent)
        CPU_UTIL.set(psutil.cpu_percent()) # NEW
    except Exception as e:
        print(f"Metrics Update Error: {e}")

# --- Setup Prometheus Instrumentator ---
instrumentator = Instrumentator()
instrumentator.add()
instrumentator.instrument(app).expose(app)

@app.on_event("startup")
async def start_metrics_polling():
    async def poll_hardware():
        while True:
            update_hardware_metrics()
            await asyncio.sleep(1)
    asyncio.create_task(poll_hardware())

class IncomingRequest(BaseModel):
    id: int
    query: str

@app.get("/health")
async def health_check():
    try:
        pynvml.nvmlDeviceGetTemperature(gpu_handle, 0)
        return {"status": "healthy", "gpu": "accessible"}
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"GPU Node Unhealthy: {e}")

@app.post("/process")
async def process_task(request: IncomingRequest):
    ACTIVE_TASKS.inc()
    start_time = time.time()

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [Worker] Processing Task {request.id}")

        context = await asyncio.to_thread(retrieve_context, request.query)
        result = await asyncio.to_thread(run_llm, request.query, context)

        latency = time.time() - start_time
        return {
            "status": "success",
            "id": request.id,
            "latency": latency,
            "result": result
        }
    except MemoryError:
        # Track OOM Errors
        WORKER_ERRORS.labels(error_type='OOM_GPU_Exhausted').inc()
        from fastapi import Response
        return Response(status_code=503, content="OOM: GPU memory exhausted")
    except TimeoutError:
        # Track Ollama Timeout Errors
        WORKER_ERRORS.labels(error_type='Ollama_Timeout').inc()
        from fastapi import HTTPException
        raise HTTPException(status_code=504, detail="Ollama Timeout")
    except Exception as e:
        # Track General/Other Errors
        WORKER_ERRORS.labels(error_type='General_Exception').inc()
        print(f"[ERROR] Task {request.id} failed: {e}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        ACTIVE_TASKS.dec()

if __name__ == "__main__":
    print("Starting Prometheus-Instrumented GPU Worker...")
    uvicorn.run(app, host="0.0.0.0", port=8000, limit_concurrency=1000, backlog=2048)