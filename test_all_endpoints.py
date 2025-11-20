import requests
import json

BASE_URL = 'https://r7hwlthie5.execute-api.ap-southeast-1.amazonaws.com/prod'

print("="*80)
print("🧪 TESTING ALL ENDPOINTS")
print("="*80)
print()

# Test 1: Health Check
print("1️⃣ Testing Health Check...")
print(f"   GET {BASE_URL}/health")
try:
    response = requests.get(f'{BASE_URL}/health', timeout=10)
    print(f"   ✅ Status: {response.status_code}")
    print(f"   📊 Response: {json.dumps(response.json(), indent=6)}")
except Exception as e:
    print(f"   ❌ Error: {e}")
print()

# Test 2: Database Stats
print("2️⃣ Testing Database Stats...")
print(f"   GET {BASE_URL}/stats")
try:
    response = requests.get(f'{BASE_URL}/stats', timeout=10)
    print(f"   ✅ Status: {response.status_code}")
    print(f"   📊 Response: {json.dumps(response.json(), indent=6)}")
except Exception as e:
    print(f"   ❌ Error: {e}")
print()

# Test 3: List People
print("3️⃣ Testing List People...")
print(f"   GET {BASE_URL}/people")
try:
    response = requests.get(f'{BASE_URL}/people', timeout=10)
    print(f"   ✅ Status: {response.status_code}")
    result = response.json()
    print(f"   📊 Response: Found {result.get('count', 0)} people")
    if result.get('people'):
        print(f"       {json.dumps(result, indent=6)}")
    else:
        print(f"       {json.dumps(result, indent=6)}")
except Exception as e:
    print(f"   ❌ Error: {e}")
print()

# Test 4: Get Thresholds
print("4️⃣ Testing Get Thresholds...")
print(f"   GET {BASE_URL}/thresholds")
try:
    response = requests.get(f'{BASE_URL}/thresholds', timeout=10)
    print(f"   ✅ Status: {response.status_code}")
    print(f"   📊 Response: {json.dumps(response.json(), indent=6)}")
except Exception as e:
    print(f"   ❌ Error: {e}")
print()

# Test 5: Enroll (will test with test_enroll.py separately)
print("5️⃣ Enroll Endpoint")
print(f"   POST {BASE_URL}/enroll")
print(f"   ⏭️  Run: python test_enroll.py")
print()

# Test 6: Identify (will test with test_identify.py separately)
print("6️⃣ Identify Endpoint")
print(f"   POST {BASE_URL}/identify")
print(f"   ⏭️  Run: python test_identify.py")
print()

print("="*80)
print("✅ Basic endpoint tests completed!")
print("📝 For enroll/identify with images, run:")
print("   python test_enroll.py")
print("   python test_identify.py")
print("="*80)
