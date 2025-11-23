import sys
import os
import time
import uuid

def test_s3_path():
    print("Testing S3 Path Generation...")
    
    user_id = "test-user-123"
    timestamp = int(time.time())
    
    # Logic from enroll/main.py
    key_raw = f"raw/{user_id}/{timestamp}.jpg"
    key_processed = f"processed/{user_id}/{timestamp}.jpg"
    
    print(f"User ID: {user_id}")
    print(f"Generated Raw Key: {key_raw}")
    print(f"Generated Processed Key: {key_processed}")
    
    if f"/{user_id}/" in key_raw:
        print("✅ User ID is in the folder path")
    else:
        print("❌ User ID is NOT in the folder path")

if __name__ == "__main__":
    test_s3_path()
