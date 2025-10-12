"""
Launcher - Chọn chế độ chạy chương trình
"""

import subprocess
import sys
import os

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    """Chạy full demo"""
    clear_screen()
    
    print("=" * 60)
    print("  🔍 CHƯƠNG TRÌNH NHẬN DIỆN KHUÔN MẶT")
    print("=" * 60)
    print()
    print("Chọn chế độ chạy:")
    print()
    print("  1️⃣  GUI - Giao diện đồ họa (Khuyến nghị) 🎨")
    print("      → Dễ sử dụng, đầy đủ tính năng")
    print("      → Đăng ký, nhận diện, quản lý")
    print()
    print("  2️⃣  Services - Sử dụng API Python 📚")
    print("      → Enrollment & Identification Services")
    print("      → Tích hợp vào code của bạn")
    print()
    print("  3️⃣  Thoát ❌")
    print()
    print("=" * 60)
    
    while True:
        choice = input("\nNhập lựa chọn (1-3): ").strip()
        
        if choice == "1":
            print("\n🚀 Đang khởi động GUI...")
            python_exe = sys.executable
            subprocess.run([python_exe, "gui_app.py"])
            break
            
        elif choice == "2":
            print("\n� PYTHON API SERVICES")
            print("\nSử dụng trong code:")
            print()
            print("# Đăng ký khuôn mặt")
            print("from enrollment_service import FaceEnrollmentService")
            print("enrollment = FaceEnrollmentService()")
            print("result = enrollment.enroll_face(")
            print("    image_path='photo.jpg',")
            print("    user_id='user_001',")
            print("    user_name='Nguyen Van A'")
            print(")")
            print()
            print("# Nhận dạng khuôn mặt")
            print("from identification_service import FaceIdentificationService")
            print("identification = FaceIdentificationService()")
            print("result = identification.identify_face('unknown.jpg')")
            print()
            print("📖 Xem thêm: ARCHITECTURE.md")
            print()
            
            run_gui = input("Mở GUI? (y/n): ").strip().lower()
            if run_gui == 'y':
                python_exe = sys.executable
                subprocess.run([python_exe, "gui_app.py"])
            break
            
        elif choice == "3":
            print("\n👋 Tạm biệt!")
            break
            
        else:
            print("❌ Lựa chọn không hợp lệ. Vui lòng chọn 1, 2 hoặc 3.")

if __name__ == "__main__":
    main()
