"""
Database Viewer - Hiển thị dữ liệu trong DynamoDB
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import os
from backend.core.database_manager import DatabaseManager
from tabulate import tabulate
from datetime import datetime

def view_database():
    """Xem toàn bộ database"""
    
    print("\n" + "="*80)
    print("🗄️  FACE RECOGNITION DATABASE VIEWER")
    print("="*80 + "\n")
    
    # Initialize database
    os.environ.setdefault('AWS_REGION', 'ap-southeast-1')
    os.environ.setdefault('DYNAMODB_PEOPLE_TABLE', 'face-recognition-people-dev')
    
    try:
        from backend.aws.dynamodb_client import DynamoDBClient
        
        # Initialize DynamoDB client
        dynamodb_client = DynamoDBClient(
            region=os.environ.get('AWS_REGION', 'ap-southeast-1'),
            people_table=os.environ.get('DYNAMODB_PEOPLE_TABLE', 'face-recognition-people-dev'),
            embeddings_table='face-recognition-embeddings-dev',
            matches_table='face-recognition-matches-dev'
        )
        
        print("✅ Connected to DynamoDB\n")
        
        # List all people using DynamoDB client
        response = dynamodb_client.list_people(limit=100)
        people = response.get('people', [])
        
        print(f"📊 Total People: {len(people)}\n")
        
        if people:
            # Format data for table
            table_data = []
            for person in people:
                table_data.append([
                    person.get('user_id', 'N/A')[:20],
                    person.get('name', 'N/A'),
                    person.get('department', 'N/A'),
                    person.get('email', 'N/A')[:30],
                    person.get('status', 'N/A'),
                    person.get('enrollment_date', 'N/A')[:10] if person.get('enrollment_date') else 'N/A'
                ])
            
            headers = ['User ID', 'Name', 'Department', 'Email', 'Status', 'Enrolled']
            print(tabulate(table_data, headers=headers, tablefmt='grid'))
            
            # Statistics
            print(f"\n📈 Statistics:")
            statuses = {}
            departments = {}
            for p in people:
                status = p.get('status', 'unknown')
                dept = p.get('department', 'unknown')
                statuses[status] = statuses.get(status, 0) + 1
                departments[dept] = departments.get(dept, 0) + 1
            
            print(f"   By Status:")
            for status, count in statuses.items():
                print(f"      - {status}: {count}")
            
            print(f"   By Department:")
            for dept, count in departments.items():
                print(f"      - {dept}: {count}")
        else:
            print("⚠️  Database is empty. No people enrolled yet.")
            print("\n💡 To enroll someone:")
            print("   1. Open GUI: python app/gui_app.py")
            print("   2. Or use API: http://127.0.0.1:8888/docs")
        
        print("\n" + "="*80)
        print("✅ Database check completed!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        print("\n💡 Make sure:")
        print("   1. AWS credentials are configured (~/.aws/credentials)")
        print("   2. DynamoDB table exists: face-recognition-people-dev")
        print("   3. You have proper IAM permissions")
        return False
    
    return True

if __name__ == "__main__":
    view_database()
