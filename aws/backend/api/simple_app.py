"""
Simple test API to verify basic functionality
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Simple Test API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/api/v1/people")
def list_people():
    """Return empty list"""
    return []

@app.post("/api/v1/enroll")
async def enroll_face():
    """Enroll endpoint - returns AWS not configured message"""
    return {
        "success": False,
        "message": "⚠️ AWS services not configured. Please set up AWS Rekognition, S3, and DynamoDB to use this feature.",
        "user_name": "",
        "person_id": None,
        "face_id": None
    }

@app.post("/api/v1/identify")
async def identify_face():
    """Identify endpoint - returns AWS not configured message"""
    return {
        "success": False,
        "faces_detected": 0,
        "faces": [],
        "message": "⚠️ AWS services not configured. Please set up AWS Rekognition and DynamoDB to use this feature.",
        "processing_time_ms": 0
    }

@app.get("/api/v1/telemetry")
def get_telemetry():
    """System telemetry"""
    import psutil
    return {
        "cpu_usage": psutil.cpu_percent(interval=0.1),
        "memory_usage": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage("/").percent
    }

@app.get("/api/v1/test")
def test():
    return {"status": "ok", "message": "API working"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=5555)

