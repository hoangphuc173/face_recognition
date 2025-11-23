import requests
import boto3
import os
import json
import time

# Configuration
API_URL = "https://54bpk3wr20.execute-api.ap-southeast-1.amazonaws.com/prod"
USER_POOL_ID = "ap-southeast-1_X8y0FiuqS"
CLIENT_ID = "48g9mt2ksa356tod8ootrau9u0"
REGION = "ap-southeast-1"

# Test User
USERNAME = "test_admin_user"
PASSWORD = "TestPassword123!"
EMAIL = "test_admin@example.com"

cognito = boto3.client('cognito-idp', region_name=REGION)

def create_test_user():
    print(f"Creating test user {USERNAME}...")
    try:
        cognito.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=USERNAME,
            UserAttributes=[
                {'Name': 'email', 'Value': EMAIL},
                {'Name': 'email_verified', 'Value': 'true'},
                {'Name': 'name', 'Value': 'Test Admin'},
            ],
            TemporaryPassword=PASSWORD,
            MessageAction='SUPPRESS'
        )
        cognito.admin_set_user_password(
            UserPoolId=USER_POOL_ID,
            Username=USERNAME,
            Password=PASSWORD,
            Permanent=True
        )
        print("User created.")
    except cognito.exceptions.UsernameExistsException:
        print("User already exists.")

def promote_to_admin():
    print(f"Promoting {USERNAME} to Admin...")
    try:
        cognito.admin_add_user_to_group(
            UserPoolId=USER_POOL_ID,
            Username=USERNAME,
            GroupName='Admin'
        )
        print("User promoted to Admin.")
    except Exception as e:
        print(f"Failed to promote: {e}")

def test_login_and_rbac():
    print("Testing Login...")
    response = requests.post(f"{API_URL}/auth/token", json={
        "username": USERNAME,
        "password": PASSWORD
    })
    
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return
    
    data = response.json()
    token = data['access_token']
    role = data.get('role')
    print(f"Login successful. Role: {role}")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test Get Profile
    print("Testing Get Profile...")
    res = requests.get(f"{API_URL}/auth/profile", headers=headers)
    print(f"Profile Response: {res.status_code}")
    if res.status_code == 200:
        print(json.dumps(res.json(), indent=2))
    
    # Test Admin Endpoint
    print("Testing Admin List Users...")
    res = requests.get(f"{API_URL}/auth/admin/users", headers=headers)
    print(f"Admin Users Response: {res.status_code}")
    if res.status_code == 200:
        users = res.json()
        print(f"Found {len(users)} users.")
        print(json.dumps(users[:2], indent=2))
    else:
        print(f"Admin access failed: {res.text}")

if __name__ == "__main__":
    create_test_user()
    promote_to_admin()
    time.sleep(2) # Wait for propagation
    test_login_and_rbac()
