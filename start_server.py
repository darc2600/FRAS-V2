#!/usr/bin/env python3
"""
Simple server startup script for FRAS backend
"""
import uvicorn
import sys

try:
    print("Importing backend...")
    from backend import app
    print("✅ Backend imported successfully")

    print("Starting FRAS Backend Server...")
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)

except Exception as e:
    print(f"❌ Error starting server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)