"""Kiểm tra khuôn mặt trong Rekognition collection"""
import boto3

client = boto3.client('rekognition', region_name='ap-southeast-1')
response = client.list_faces(
    CollectionId='face-recognition-collection-dev',
    MaxResults=100
)

faces = response.get('Faces', [])
print(f'✅ Total faces in collection: {len(faces)}')
print()

for i, face in enumerate(faces, 1):
    print(f'{i}. FaceId: {face["FaceId"]}')
    print(f'   ExternalImageId: {face.get("ExternalImageId", "N/A")}')
    print()
