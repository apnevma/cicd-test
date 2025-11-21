from fastapi import FastAPI

app = FastAPI(title="Simple Health Check API")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "fastapi-backend",
        "message": "Workshop test: Service is running!"
    }
