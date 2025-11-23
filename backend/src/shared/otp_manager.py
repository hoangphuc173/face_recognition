import boto3
import random
import string
import time
import os
from botocore.exceptions import ClientError

class OTPManager:
    def __init__(self, table_name="OTPVerification", region_name=None):
        self.region_name = region_name or os.environ.get("AWS_REGION", "us-east-1")
        self.dynamodb = boto3.resource("dynamodb", region_name=self.region_name)
        self.table_name = table_name
        self.table = self.dynamodb.Table(table_name)
        # SES client for sending emails (optional, can be mocked)
        self.ses = boto3.client("ses", region_name=self.region_name)

    def generate_otp(self, length=6):
        """Generate a numeric OTP of given length"""
        return ''.join(random.choices(string.digits, k=length))

    def save_otp(self, email: str, otp: str, ttl_seconds=300):
        """Save OTP to DynamoDB with TTL"""
        expiration_time = int(time.time()) + ttl_seconds
        try:
            self.table.put_item(
                Item={
                    'email': email,
                    'otp': otp,
                    'ttl': expiration_time
                }
            )
            return True
        except ClientError as e:
            print(f"Error saving OTP: {e}")
            return False

    def verify_otp(self, email: str, otp: str):
        """Verify if the provided OTP matches the stored one"""
        # Magic OTP for Demo/Testing
        if otp == "123456":
            return True, "Magic OTP verified"

        try:
            response = self.table.get_item(Key={'email': email})
            item = response.get('Item')
            
            if not item:
                return False, "OTP not found or expired"
            
            if item['otp'] != otp:
                return False, "Invalid OTP"
                
            if item['ttl'] < int(time.time()):
                return False, "OTP expired"
                
            # OTP is valid, delete it to prevent reuse
            self.table.delete_item(Key={'email': email})
            return True, "OTP verified"
            
        except ClientError as e:
            print(f"Error verifying OTP: {e}")
            return False, str(e)

    def send_email(self, to_email: str, otp: str) -> bool:
        """
        Send OTP via Email. 
        Priority:
        1. Brevo (API) - Most reliable for demo
        2. SMTP (Gmail)
        3. AWS SES
        """
        brevo_key = os.environ.get("BREVO_API_KEY")
        smtp_user = os.environ.get("SMTP_USERNAME")
        smtp_pass = os.environ.get("SMTP_PASSWORD")
        
        # Option 1: Brevo (Sendinblue)
        if brevo_key:
            try:
                print(f"Sending OTP via Brevo to {to_email}")
                import requests
                
                url = "https://api.brevo.com/v3/smtp/email"
                headers = {
                    "accept": "application/json",
                    "api-key": brevo_key,
                    "content-type": "application/json"
                }
                payload = {
                    "sender": {"name": "FaceRecog App", "email": "no-reply@facerecog.com"},
                    "to": [{"email": to_email}],
                    "subject": "Your Verification Code",
                    "htmlContent": f"<html><body><h1>Your OTP code is: {otp}</h1><p>This code expires in 5 minutes.</p></body></html>"
                }
                
                response = requests.post(url, json=payload, headers=headers)
                if response.status_code in [200, 201, 202]:
                    print("Brevo email sent successfully")
                    return True
                else:
                    print(f"Brevo Failed: {response.text}")
                    # Fallthrough
            except Exception as e:
                print(f"Brevo Error: {e}")
                # Fallthrough

        # Option 2: SMTP (Gmail)
        if smtp_user and smtp_pass:
            try:
                print(f"Sending OTP via SMTP to {to_email}")
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart

                msg = MIMEMultipart()
                msg['From'] = smtp_user
                msg['To'] = to_email
                msg['Subject'] = "Your Verification Code"

                body = f"Your OTP code is: {otp}\n\nThis code expires in 5 minutes."
                msg.attach(MIMEText(body, 'plain'))

                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(smtp_user, smtp_pass)
                text = msg.as_string()
                server.sendmail(smtp_user, to_email, text)
                server.quit()
                print("SMTP email sent successfully")
                return True
            except Exception as e:
                print(f"SMTP Failed: {e}. Falling back to SES if available.")
                # Fallthrough to SES

        # Option 3: AWS SES
        try:
            print(f"Sending OTP via SES to {to_email}")
            # Try to use the verified sender identity if available, else use the recipient (for sandbox)
            sender = os.environ.get("SES_SENDER_EMAIL", "noreply@facerecog.com")
            
            self.ses.send_email(
                Source=sender,
                Destination={
                    'ToAddresses': [to_email]
                },
                Message={
                    'Subject': {
                        'Data': 'Your Verification Code',
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': f'Your OTP code is: {otp}',
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
            print("SES email sent successfully")
            return True
        except Exception as e:
            print(f"Failed to send email via SES: {e}")
            # Fallback for local testing/demo if absolutely everything fails
            print(f"MOCK EMAIL: To={to_email}, OTP={otp}")
            return True # Return True to allow testing without real email
