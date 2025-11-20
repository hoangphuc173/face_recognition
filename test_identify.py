import base64
import json
import requests

# Tạo ảnh test nhỏ (giống như trong enroll)
test_image_bytes = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\x7f\x00\xff\xd9'

# Encode to base64
image_b64 = base64.b64encode(test_image_bytes).decode('utf-8')

# API endpoint
url = 'https://r7hwlthie5.execute-api.ap-southeast-1.amazonaws.com/prod/identify'

# Payload
payload = {
    'image': f'data:image/jpeg;base64,{image_b64}',
    'use_case': 'attendance'
}

print("🔍 Testing Identification API...")
print(f"📍 URL: {url}")
print(f"📦 Payload: {json.dumps({**payload, 'image': 'data:image/jpeg;base64,...'}, indent=2)}")
print("\n" + "="*80 + "\n")

try:
    response = requests.post(url, json=payload, timeout=30)
    
    print(f"✅ Status Code: {response.status_code}")
    print(f"📊 Response:")
    print(json.dumps(response.json(), indent=2))
    
except requests.exceptions.RequestException as e:
    print(f"❌ Error: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Response: {e.response.text}")
