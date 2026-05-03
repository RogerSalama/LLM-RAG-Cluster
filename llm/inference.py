# llm/inference.py
import requests
import time

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
        # --- Hardware Maximization ---
        "num_gpu": 99,        # Force all layers to NVIDIA
        "num_thread": 12,     # Use all available CPU cores for prompt prefill
        "num_ctx": 512,       # MINIMIZE memory window (Extreme speed boost)
        "num_batch": 1024,    # Process large chunks of the prompt at once
        
        # --- Search Reduction (The "Speed" settings) ---
        "temperature": 0.0,   # Remove randomness logic (Greedy decoding is fastest)
        "top_k": 1,           # Only look at the single most likely word
        "top_p": 1.0,         # Disable nucleus sampling overhead
        
        # --- Output Restriction ---
        "num_predict": 64,    # Hard cap on response length (Don't let it ramble)
        "repeat_penalty": 1.0,# Disable repetition checking math
        
        # --- Memory Efficiency ---
        "f16_kv": True,       # Use half-precision cache
        "use_mlock": True,    # Lock model in RAM so it NEVER swaps to SSD
        "use_mmap": True      # High-speed memory mapping
    }
}
    
    try:
        response = requests.post(url, json=payload)
        data = response.json()
        print(f"LLM Response: {data.get('response')}")
        print(f"Total time: {data.get('total_duration') / 1e9:.2f}s")
        print(f"Load time: {data.get('load_duration') / 1e9:.2f}s")
        print(f"Inference time: {data.get('eval_duration') / 1e9:.2f}s")
        endTime = time.time()
        print(f"Total execution time: {endTime - startTime:.2f}s")
        return data.get("response")
    except Exception as e:
        return f"Inference Error: {str(e)}"

# startTime = time.time()
# print("Asking LLM...")
# result = run_llm("What is the capital of France?", "The user is asking about geography.")
# print(f"LLM Response: {result}")
# endTime = time.time()
# print(f"Total execution time: {endTime - startTime:.2f}s")