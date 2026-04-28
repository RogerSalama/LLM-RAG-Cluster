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
        "stream": False
        #"options": {"num_ctx": 1024, "num_gpu": 50},
        #"keep_alive": 0      # IMPORTANT: Tell Ollama to clear memory after each request
    }
    
    try:
        response = requests.post(url, json=payload)
        data = response.json()
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