import uvicorn
import random
from fastapi import FastAPI

app = FastAPI(title="HeavyTask")

@app.get('/')
def heavy_task():
    num = random.randint(300,305)
    mem = ['A'*500 for _ in range(0, num*num*num)]
    return "Memory intensive task"


if __name__ == "__main__":
    uvicorn.run("view:app", host="0.0.0.0", port=5000, log_level="info")