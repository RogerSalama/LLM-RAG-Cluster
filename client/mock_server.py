# mock_server.py
from fastapi import FastAPI
import uvicorn

app = FastAPI()

# This matches the endpoint in your Locust script
@app.post("/query")
async def handle_query(payload: dict):
    # Simulates a fast response so Locust can easily scale up
    return {"status": "success", "message": "Mock response received"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)