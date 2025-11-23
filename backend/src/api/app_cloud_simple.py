"""
Simplified Cloud Backend - Routes only (no AWS services initialization)
This version uses the modular routes from backend/src/api/routes/
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

app = FastAPI(title="Face Recognition API - Cloud Mode", version="2.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include modular routes
try:
    from routes import auth
    app.include_router(auth.router, prefix="/auth", tags=["authentication"])
    print("✅ Loaded Auth routes")
except ImportError as e:
    print(f"⚠️ Could not load Auth routes: {e}")

# Health check
@app.get("/health")
def health():
    return {"status": "healthy", "mode": "cloud_simplified"}

@app.get("/")
def root():
    return {
        "message": "Face Recognition API - Cloud Mode (Simplified)",
        "available_endpoints": [
            "/health",
            "/auth/token",
            "/auth/register",
            "/auth/otp/send",
            "/auth/profile",
            "/docs"
        ]
    }

if __name__ == "__main__":
    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", "8000"))
    
    print("="*60)
    print("Face Recognition API - Cloud Mode (Simplified)")
    print("="*60)
    print()
    print(f"URL: http://{host}:{port}")
    print(f"Docs: http://{host}:{port}/docs")
    print()
    print("Features:")
    print("  - User Registration with OTP")
    print("  - Authentication (JWT)")
    print("  - Profile Management")
    print()
    print("="*60)
    print()
    
    uvicorn.run(app, host=host, port=port, log_level="info")
