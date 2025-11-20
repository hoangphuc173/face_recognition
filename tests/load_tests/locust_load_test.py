"""
Locust Load Testing Script
Test 5000 req/min throughput (báo cáo 7.2)
"""

from locust import HttpUser, task, between, events
import json
import base64
import random
import time
from datetime import datetime

# Test configuration
API_BASE_URL = "https://your-api-gateway-url.amazonaws.com/prod"
API_TOKEN = "your-jwt-token"  # Get from /auth/token endpoint

# Sample test images (base64 encoded)
TEST_IMAGES = []


class FaceRecognitionUser(HttpUser):
    """
    Simulates face recognition API user
    Target: 5000 req/min = ~83 req/s
    """
    
    # Wait time between tasks (seconds)
    wait_time = between(0.5, 2.0)
    
    def on_start(self):
        """Setup before test - authenticate"""
        
        # Login to get JWT token
        response = self.client.post(
            "/auth/token",
            data={
                "username": "test_user",
                "password": "test_password"
            },
            verify=False
        )
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
        else:
            print(f"❌ Login failed: {response.status_code}")
            self.token = None
            self.headers = {}
    
    @task(10)  # Weight 10 - most common operation
    def identify_face(self):
        """Test identification endpoint (90% of traffic)"""
        
        if not self.token:
            return
        
        # Generate random test image
        image_data = self._generate_test_image()
        
        payload = {
            "image": image_data,
            "confidence_threshold": 90,
            "context": random.choice(["attendance", "access_control"])
        }
        
        start_time = time.time()
        
        with self.client.post(
            "/identify/",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="POST /identify/"
        ) as response:
            
            latency = (time.time() - start_time) * 1000  # ms
            
            if response.status_code == 200:
                result = response.json()
                
                # Validate response structure
                if "user_id" in result or "message" in result:
                    response.success()
                    
                    # Check latency SLA (<2s = 2000ms)
                    if latency > 2000:
                        print(f"⚠️ High latency: {latency:.0f}ms")
                else:
                    response.failure("Invalid response structure")
            
            elif response.status_code == 404:
                # Not found is valid response
                response.success()
            
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(2)  # Weight 2 - less common
    def enroll_face(self):
        """Test enrollment endpoint (10% of traffic)"""
        
        if not self.token:
            return
        
        user_id = f"test_user_{random.randint(1000, 9999)}"
        
        # Generate multiple test images for enrollment
        images = [self._generate_test_image() for _ in range(5)]
        
        payload = {
            "user_id": user_id,
            "name": f"Test User {user_id}",
            "images": images,
            "department": "Testing",
            "email": f"{user_id}@test.com"
        }
        
        start_time = time.time()
        
        with self.client.post(
            "/enroll/",
            json=payload,
            headers=self.headers,
            catch_response=True,
            name="POST /enroll/"
        ) as response:
            
            latency = (time.time() - start_time) * 1000
            
            if response.status_code in [200, 201]:
                response.success()
                
                # Enrollment can be slower
                if latency > 5000:
                    print(f"⚠️ Slow enrollment: {latency:.0f}ms")
            
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(1)  # Weight 1 - rare
    def get_people(self):
        """Test people listing endpoint"""
        
        if not self.token:
            return
        
        with self.client.get(
            "/people/",
            headers=self.headers,
            catch_response=True,
            name="GET /people/"
        ) as response:
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) or "people" in result:
                    response.success()
                else:
                    response.failure("Invalid response structure")
            else:
                response.failure(f"Status {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Test health endpoint"""
        
        with self.client.get(
            "/health",
            catch_response=True,
            name="GET /health"
        ) as response:
            
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")
    
    def _generate_test_image(self) -> str:
        """Generate random test image data (base64)"""
        
        # In real test, use actual face images
        # For now, return mock base64
        mock_data = f"test_image_{random.randint(1, 1000)}_{int(time.time())}"
        return base64.b64encode(mock_data.encode()).decode()


# Custom stats tracking
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Track custom metrics"""
    
    if exception:
        print(f"❌ Request failed: {name} - {exception}")
    
    # Log slow requests
    if response_time > 2000:
        print(f"⚠️ Slow request: {name} took {response_time:.0f}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Print test configuration"""
    
    print(f"""
╔════════════════════════════════════════════════╗
║      Face Recognition Load Test Started       ║
╠════════════════════════════════════════════════╣
║ Target: 5000 requests/minute (~83 req/s)      ║
║ Users: Ramp up gradually                       ║
║ SLA: <2s latency (P95)                         ║
╚════════════════════════════════════════════════╝
    """)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print test summary"""
    
    stats = environment.stats
    
    print(f"""
╔════════════════════════════════════════════════╗
║         Load Test Completed                    ║
╠════════════════════════════════════════════════╣
║ Total Requests: {stats.total.num_requests}
║ Failures: {stats.total.num_failures}
║ Avg Response Time: {stats.total.avg_response_time:.0f}ms
║ P50: {stats.total.get_response_time_percentile(0.5):.0f}ms
║ P95: {stats.total.get_response_time_percentile(0.95):.0f}ms
║ P99: {stats.total.get_response_time_percentile(0.99):.0f}ms
║ RPS: {stats.total.total_rps:.1f}
╚════════════════════════════════════════════════╝
    """)
    
    # Check SLA
    p95 = stats.total.get_response_time_percentile(0.95)
    if p95 > 2000:
        print(f"⚠️ SLA VIOLATION: P95 latency {p95:.0f}ms exceeds 2000ms")
    else:
        print(f"✅ SLA MET: P95 latency {p95:.0f}ms within target")


# Run configuration
# Command: locust -f load_test.py --host=https://your-api.com --users 100 --spawn-rate 10
# Target: 100 concurrent users doing 50 requests each = 5000/min
