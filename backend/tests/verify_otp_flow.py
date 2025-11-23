import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from shared.otp_manager import OTPManager
import time

def test_otp_flow():
    print("Testing OTP Flow...")
    manager = OTPManager(region_name="us-east-1")
    
    email = "test@example.com"
    otp = manager.generate_otp()
    print(f"Generated OTP: {otp}")
    
    # Mock DynamoDB table for local test if needed, or rely on boto3 mocking
    # For this script, we will just test the logic flow assuming table exists or mock it
    
    # Since we don't have a real DynamoDB locally, we can mock the table object
    class MockTable:
        def __init__(self):
            self.items = {}
        def put_item(self, Item):
            self.items[Item['email']] = Item
        def get_item(self, Key):
            return {'Item': self.items.get(Key['email'])}
        def delete_item(self, Key):
            if Key['email'] in self.items:
                del self.items[Key['email']]

    manager.table = MockTable()
    
    # Test Save
    print("Saving OTP...")
    manager.save_otp(email, otp)
    
    # Test Verify (Success)
    print("Verifying OTP (Correct)...")
    success, msg = manager.verify_otp(email, otp)
    if success:
        print("✅ OTP Verified Successfully")
    else:
        print(f"❌ OTP Verification Failed: {msg}")
        
    # Test Verify (Fail - Replay)
    print("Verifying OTP (Replay)...")
    success, msg = manager.verify_otp(email, otp)
    if not success:
        print("✅ Replay Attack Prevented")
    else:
        print(f"❌ Replay Attack Allowed: {msg}")

    # Test Verify (Fail - Wrong OTP)
    otp2 = manager.generate_otp()
    manager.save_otp(email, otp2)
    print("Verifying OTP (Wrong)...")
    success, msg = manager.verify_otp(email, "000000")
    if not success:
        print("✅ Wrong OTP Rejected")
    else:
        print(f"❌ Wrong OTP Accepted: {msg}")

if __name__ == "__main__":
    test_otp_flow()
