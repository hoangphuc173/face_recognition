#!/usr/bin/env python
"""
Start Face Recognition API Server
Simple script to run the FastAPI application
"""

import sys
import os
import subprocess

# Add aws directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'aws'))

def main():
    """Start the FastAPI server."""
    print("=" * 60)
    print("🚀 Starting Face Recognition System API Server")
    print("=" * 60)
    print()
    print("📋 Configuration:")
    print(f"   • Host: 127.0.0.1")
    print(f"   • Port: 5555")
    print(f"   • Environment: Development")
    print(f"   • Auto-reload: Enabled")
    print()
    print("📍 Endpoints:")
    print(f"   • API Docs: http://127.0.0.1:5555/docs")
    print(f"   • Health: http://127.0.0.1:5555/health")
    print(f"   • Metrics: http://127.0.0.1:5555/metrics")
    print()
    print("⌨️  Press CTRL+C to stop the server")
    print("=" * 60)
    print()
    
    try:
        # Run uvicorn
        cmd = [
            sys.executable,
            "-m", "uvicorn",
            "backend.api.app:app",
            "--host", "127.0.0.1",
            "--port", "5555",
            "--reload",
            "--log-level", "info"
        ]
        
        # Change to aws directory for proper imports
        os.chdir(os.path.join(os.path.dirname(__file__), 'aws'))
        
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("👋 Server stopped gracefully")
        print("=" * 60)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Error: {e}")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()

