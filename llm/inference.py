# llm/inference.py
import requests
import time
from prometheus_client import Gauge


# --- NEW: Tell Prometheus about these metrics ---
LLM_TOTAL_DUR = Gauge('llm_total_duration_seconds', 'Total Ollama processing duration')
LLM_LOAD_DUR = Gauge('llm_load_duration_seconds', 'Ollama model load duration')
LLM_EVAL_DUR = Gauge('llm_eval_duration_seconds', 'Ollama inference/eval duration')
LLM_TPS = Gauge('llm_tokens_per_second', 'Generation speed in tokens per second')  # NEW

def run_llm(query, context):
    startTime = time.time()
    # This calls a locally running light model via Ollama
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "smollm2:135m",
        "prompt": f"Context: {context}\nQuestion: {query}",
        "stream": False,
        "keep_alive": "1h",
        "options": {
            "num_gpu": 99,
            "num_thread": 8,
            "top_k": 1,
            "num_predict": 16,
            "temperature": 0.0
        }
    }
    
    try:
        response = requests.post(url, json=payload)
        data = response.json()

        # Calculation of durations (Nanoseconds to Seconds)
        total_dur = data.get('total_duration', 0) / 1e9
        load_dur = data.get('load_duration', 0) / 1e9
        eval_dur = data.get('eval_duration', 0) / 1e9
        eval_count = data.get('eval_count', 0)  # NEW: Get token count

        # --- NEW: Send the numbers to Prometheus! ---
        LLM_TOTAL_DUR.set(total_dur)
        LLM_LOAD_DUR.set(load_dur)
        LLM_EVAL_DUR.set(eval_dur)

        if eval_dur > 0:
            LLM_TPS.set(eval_count / eval_dur)

        print(f"query: {query}")
        print(f"LLM Response: {data.get('response')}")
        print(f"Total time: {data.get('total_duration') / 1e9:.2f}s")
        print(f"Load time: {data.get('load_duration') / 1e9:.2f}s")
        print(f"Inference time: {data.get('eval_duration') / 1e9:.2f}s")
        print(f"Tokens per second: {LLM_TPS._value.get()}")
        endTime = time.time()
        print(f"Total execution time: {endTime - startTime:.2f}s")
        return data.get("response")
    except requests.exceptions.Timeout:
        # We raise this so the worker node catches it and logs it as a Timeout Error!
        raise TimeoutError("Ollama took too long and timed out.")
    except Exception as e:
        raise RuntimeError(f"Inference Error: {str(e)}")

# startTime = time.time()
# print("Asking LLM...")
# result = run_llm("What is the capital of France?", "The user is asking about geography.")
# print(f"LLM Response: {result}")
# endTime = time.time()
# print(f"Total execution time: {endTime - startTime:.2f}s")