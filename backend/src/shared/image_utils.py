import io
from PIL import Image, ImageStat, ImageFilter
import boto3

rekognition = boto3.client('rekognition')

class ImageQualityError(Exception):
    pass

def validate_image(image_bytes: bytes) -> bool:
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
        return True
    except Exception:
        return False

def check_face_quality_rekognition(image_bytes: bytes):
    """
    Uses Rekognition DetectFaces to check:
    - Face size >= 100x100 pixels
    - Head pose (Pitch, Roll, Yaw all < 30 degrees)
    Raises ImageQualityError if checks fail.
    """
    try:
        response = rekognition.detect_faces(
            Image={'Bytes': image_bytes},
            Attributes=['ALL']
        )
        
        if not response.get('FaceDetails'):
            raise ImageQualityError("No face detected in image")
        
        face = response['FaceDetails'][0]
        bbox = face['BoundingBox']
        
        # Calculate face size in pixels (assuming 640x480 image)
        face_width = bbox['Width'] * 640
        face_height = bbox['Height'] * 480
        
        if face_width < 100 or face_height < 100:
            raise ImageQualityError(
                f"Face too small ({face_width:.0f}x{face_height:.0f}). Minimum 100x100 pixels required."
            )
        
        # Check head pose
        pose = face['Pose']
        pitch = abs(pose['Pitch'])
        roll = abs(pose['Roll'])
        yaw = abs(pose['Yaw'])
        
        if pitch > 30 or roll > 30 or yaw > 30:
            raise ImageQualityError(
                f"Head pose out of range. Pitch: {pitch:.1f}°, Roll: {roll:.1f}°, Yaw: {yaw:.1f}° (max 30° each)"
            )
        
        # Check quality
        quality = face.get('Quality', {})
        brightness = quality.get('Brightness', 50)
        sharpness = quality.get('Sharpness', 50)
        
        if brightness < 30 or brightness > 95:
            raise ImageQualityError(f"Image brightness {brightness:.1f} out of optimal range (30-95)")
        
        if sharpness < 30:
            raise ImageQualityError(f"Image too blurry. Sharpness: {sharpness:.1f} (min 30)")
            
    except ImageQualityError:
        raise
    except Exception as e:
        raise ImageQualityError(f"Face quality check failed: {str(e)}")

def preprocess_image(image_bytes: bytes) -> bytes:
    """
    Resize to 640x480.
    Check brightness (50-205).
    Check contrast (>20).
    Check blur (using edge detection).
    Check face size and head pose using Rekognition.
    Returns processed image bytes or raises ImageQualityError.
    """
    img = Image.open(io.BytesIO(image_bytes))
    
    # Resize
    img = img.resize((640, 480))
    gray_img = img.convert('L')
    
    # Check Brightness
    stat = ImageStat.Stat(gray_img)
    brightness = stat.mean[0]
    if brightness < 50 or brightness > 205:
        raise ImageQualityError(f"Image brightness {brightness:.2f} out of range (50-205)")

    # Check Contrast
    if stat.stddev[0] < 20:
        raise ImageQualityError(f"Image contrast {stat.stddev[0]:.2f} too low (<20)")

    # Check Blur (Basic Edge Detection)
    edges = gray_img.filter(ImageFilter.FIND_EDGES)
    edge_stat = ImageStat.Stat(edges)
    edge_mean = edge_stat.mean[0]
    if edge_mean < 5: 
        raise ImageQualityError(f"Image appears blurry (Edge score: {edge_mean:.2f})")

    # Convert back to bytes for Rekognition
    output = io.BytesIO()
    img.save(output, format="JPEG")
    processed_bytes = output.getvalue()
    
    # Check face quality using Rekognition
    check_face_quality_rekognition(processed_bytes)
    
    return processed_bytes
