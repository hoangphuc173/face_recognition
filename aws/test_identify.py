"""
Test Identification Service - Demo Script
Kiểm tra chức năng nhận diện khuôn mặt
"""

import requests
import cv2
import numpy as np
from pathlib import Path

# API endpoint
API_URL = "http://127.0.0.1:8888/api/v1/identify"

def test_identify_from_camera():
    """Test nhận diện từ camera"""
    print("=== TEST IDENTIFY FROM CAMERA ===")
    print("Mở camera và chụp ảnh để nhận diện...")
    
    # Mở camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Không thể mở camera")
        return
    
    print("📸 Nhấn SPACE để chụp ảnh, ESC để thoát")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        cv2.imshow('Camera - Press SPACE to capture', frame)
        
        key = cv2.waitKey(1)
        if key == 27:  # ESC
            break
        elif key == 32:  # SPACE
            # Lưu ảnh tạm
            cv2.imwrite('temp_identify.jpg', frame)
            
            # Gọi API identify
            with open('temp_identify.jpg', 'rb') as f:
                files = {'image': f}
                response = requests.post(API_URL, files=files)
            
            if response.status_code == 200:
                result = response.json()
                print("\n✅ Kết quả nhận diện:")
                print(f"   Số khuôn mặt: {result['faces_detected']}")
                print(f"   Thời gian xử lý: {result['processing_time_ms']:.2f}ms")
                
                if result['faces']:
                    for i, face in enumerate(result['faces'], 1):
                        print(f"\n   Khuôn mặt {i}:")
                        print(f"      - Tên: {face['user_name']}")
                        print(f"      - Độ tin cậy: {face['confidence']*100:.2f}%")
                        print(f"      - Giới tính: {face.get('gender', 'N/A')}")
                        print(f"      - Năm sinh: {face.get('birth_year', 'N/A')}")
                        print(f"      - Quê quán: {face.get('hometown', 'N/A')}")
                else:
                    print("   ⚠️ Không tìm thấy khuôn mặt nào khớp")
            else:
                print(f"❌ Lỗi API: {response.status_code}")
                print(f"   {response.text}")
            
            print("\n📸 Nhấn SPACE để chụp lại, ESC để thoát")
    
    cap.release()
    cv2.destroyAllWindows()
    
    # Xóa file tạm
    Path('temp_identify.jpg').unlink(missing_ok=True)


def test_identify_from_file(image_path: str):
    """Test nhận diện từ file ảnh"""
    print(f"\n=== TEST IDENTIFY FROM FILE ===")
    print(f"Đang nhận diện ảnh: {image_path}")
    
    if not Path(image_path).exists():
        print(f"❌ File không tồn tại: {image_path}")
        return
    
    with open(image_path, 'rb') as f:
        files = {'image': f}
        response = requests.post(API_URL, files=files)
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ Kết quả nhận diện:")
        print(f"   Số khuôn mặt: {result['faces_detected']}")
        print(f"   Thời gian xử lý: {result['processing_time_ms']:.2f}ms")
        
        if result['faces']:
            for i, face in enumerate(result['faces'], 1):
                print(f"\n   Khuôn mặt {i}:")
                print(f"      - Tên: {face['user_name']}")
                print(f"      - Độ tin cậy: {face['confidence']*100:.2f}%")
                print(f"      - Similarity: {face['similarity']:.2f}")
                print(f"      - Person ID: {face['person_id']}")
                print(f"      - Giới tính: {face.get('gender', 'N/A')}")
                print(f"      - Năm sinh: {face.get('birth_year', 'N/A')}")
                print(f"      - Quê quán: {face.get('hometown', 'N/A')}")
                print(f"      - Nơi ở: {face.get('residence', 'N/A')}")
        else:
            print("   ⚠️ Không tìm thấy khuôn mặt nào khớp")
    else:
        print(f"❌ Lỗi API: {response.status_code}")
        print(f"   {response.text}")


def test_identify_with_threshold(image_path: str, threshold: float):
    """Test nhận diện với ngưỡng confidence khác nhau"""
    print(f"\n=== TEST WITH THRESHOLD: {threshold} ===")
    
    with open(image_path, 'rb') as f:
        files = {'image': f}
        params = {'threshold': threshold}
        response = requests.post(API_URL, files=files, params=params)
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Khuôn mặt tìm thấy: {result['faces_detected']}")
        if result['faces']:
            for face in result['faces']:
                print(f"      - {face['user_name']}: {face['confidence']*100:.2f}%")


def benchmark_identify():
    """Benchmark performance của identification"""
    print("\n=== BENCHMARK IDENTIFICATION ===")
    
    # Chụp ảnh test
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        print("❌ Không thể chụp ảnh từ camera")
        return
    
    cv2.imwrite('benchmark_test.jpg', frame)
    
    import time
    times = []
    
    print("Chạy 10 lần identify...")
    for i in range(10):
        with open('benchmark_test.jpg', 'rb') as f:
            files = {'image': f}
            start = time.time()
            response = requests.post(API_URL, files=files)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   Run {i+1}: {elapsed:.2f}ms - {result['faces_detected']} faces")
            else:
                print(f"   Run {i+1}: ERROR - {response.status_code}")
    
    print(f"\n📊 Thống kê:")
    print(f"   Trung bình: {np.mean(times):.2f}ms")
    print(f"   Min: {np.min(times):.2f}ms")
    print(f"   Max: {np.max(times):.2f}ms")
    print(f"   Std: {np.std(times):.2f}ms")
    
    Path('benchmark_test.jpg').unlink(missing_ok=True)


if __name__ == "__main__":
    print("="*60)
    print("FACE IDENTIFICATION TEST SUITE")
    print("="*60)
    
    print("\nChọn test:")
    print("1. Nhận diện từ camera (realtime)")
    print("2. Nhận diện từ file ảnh")
    print("3. Test với các threshold khác nhau")
    print("4. Benchmark performance")
    print("0. Thoát")
    
    choice = input("\nNhập lựa chọn (0-4): ").strip()
    
    if choice == "1":
        test_identify_from_camera()
    elif choice == "2":
        image_path = input("Nhập đường dẫn ảnh: ").strip()
        test_identify_from_file(image_path)
    elif choice == "3":
        image_path = input("Nhập đường dẫn ảnh: ").strip()
        print("\nTest với các threshold:")
        for threshold in [0.5, 0.6, 0.7, 0.8, 0.9]:
            test_identify_with_threshold(image_path, threshold)
    elif choice == "4":
        benchmark_identify()
    else:
        print("Thoát")
