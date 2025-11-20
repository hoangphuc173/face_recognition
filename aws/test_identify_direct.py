"""Test identify API trực tiếp với ảnh từ file"""
import requests
import json

# Chụp 1 frame từ camera và lưu thành file test_frame.jpg trước
# Hoặc dùng ảnh bất kỳ có khuôn mặt

API_URL = "http://127.0.0.1:8888"

# Test với file ảnh
image_path = "test_frame.jpg"

try:
    with open(image_path, "rb") as f:
        files = {"image": ("test.jpg", f, "image/jpeg")}
        
        response = requests.post(
            f"{API_URL}/api/v1/identify",
            files=files,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"\nResponse JSON:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Success: {result.get('success')}")
            print(f"Faces Detected: {result.get('faces_detected')}")
            print(f"Matches: {len(result.get('faces', []))}")
            
            for i, face in enumerate(result.get('faces', []), 1):
                print(f"\n Match {i}:")
                print(f"  Name: {face.get('person_name')}")
                print(f"  Confidence: {face.get('confidence')}%")
                print(f"  Similarity: {face.get('similarity')}%")
                
except FileNotFoundError:
    print(f"❌ File not found: {image_path}")
    print("Hãy chụp 1 frame từ camera và lưu thành test_frame.jpg")
except Exception as e:
    print(f"❌ Error: {e}")
