"""
Script quản lý database - Xem, sửa, xóa thông tin người
"""

import os
import json
from database_manager import DatabaseManager
from tabulate import tabulate

def view_all_people():
    """Xem danh sách tất cả người trong database"""
    db = DatabaseManager()
    
    db_folders = [f for f in os.listdir(db.db_root) 
                  if os.path.isdir(os.path.join(db.db_root, f))]
    
    if not db_folders:
        print("❌ Database trống!")
        return
    
    print("\n" + "=" * 100)
    print("👥 DANH SÁCH NGƯỜI TRONG DATABASE")
    print("=" * 100)
    
    table_data = []
    
    for i, folder_name in enumerate(sorted(db_folders), 1):
        info = db.get_person_info(folder_name)
        
        if info:
            table_data.append([
                i,
                folder_name,
                info.get("user_name", "N/A"),
                info.get("gender", "N/A"),
                info.get("birth_year", "N/A"),
                info.get("hometown", "N/A"),
                info.get("residence", "N/A"),
                info.get("embedding_count", 0)
            ])
        else:
            table_data.append([
                i,
                folder_name,
                "❌ ERROR",
                "-",
                "-",
                "-",
                "-",
                0
            ])
    
    headers = ["#", "Folder", "Họ tên", "Giới tính", "Năm sinh", "Quê", "Nơi ở", "Embeddings"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print(f"\n📊 Tổng: {len(db_folders)} người")


def view_person_detail(folder_name: str):
    """Xem chi tiết thông tin 1 người"""
    db = DatabaseManager()
    info = db.get_person_info(folder_name)
    
    if not info:
        print(f"❌ Không tìm thấy '{folder_name}' trong database!")
        return
    
    print("\n" + "=" * 70)
    print(f"📋 CHI TIẾT THÔNG TIN - {folder_name}")
    print("=" * 70)
    
    print(f"\n📁 Folder Name:    {info.get('folder_name', 'N/A')}")
    print(f"👤 Họ và tên:      {info.get('user_name', 'N/A')}")
    print(f"⚧  Giới tính:      {info.get('gender', 'N/A')}")
    print(f"🎂 Năm sinh:       {info.get('birth_year', 'N/A')}")
    print(f"🏠 Quê quán:       {info.get('hometown', 'N/A')}")
    print(f"📍 Nơi sinh sống:  {info.get('residence', 'N/A')}")
    
    print(f"\n📊 Số embeddings:  {info.get('embedding_count', 0)}")
    print(f"📅 Tạo lúc:        {info.get('created_at', 'N/A')}")
    print(f"🔄 Cập nhật lần cuối: {info.get('updated_at', 'N/A')}")
    
    # Kiểm tra folder ảnh
    faces_folder = os.path.join("faces", folder_name)
    if os.path.exists(faces_folder):
        image_files = [f for f in os.listdir(faces_folder) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        print(f"📸 Số ảnh trong faces/: {len(image_files)}")
    else:
        print(f"⚠️  Không có folder trong faces/")
    
    print("=" * 70)


def edit_person_info(folder_name: str):
    """Sửa thông tin người"""
    db = DatabaseManager()
    info = db.get_person_info(folder_name)
    
    if not info:
        print(f"❌ Không tìm thấy '{folder_name}' trong database!")
        return
    
    print("\n" + "=" * 70)
    print(f"✏️ CHỈNH SỬA THÔNG TIN - {folder_name}")
    print("=" * 70)
    
    print("\n📝 Nhập thông tin mới (Enter để giữ nguyên):\n")
    
    # Họ tên
    current_name = info.get("user_name", "")
    new_name = input(f"👤 Họ và tên [{current_name}]: ").strip()
    if not new_name:
        new_name = current_name
    
    # Giới tính
    current_gender = info.get("gender", "")
    new_gender = input(f"⚧  Giới tính (Nam/Nữ/Khác) [{current_gender}]: ").strip()
    if not new_gender:
        new_gender = current_gender
    
    # Năm sinh
    current_birth = info.get("birth_year", "")
    new_birth = input(f"🎂 Năm sinh [{current_birth}]: ").strip()
    if not new_birth:
        new_birth = current_birth
    
    # Quê quán
    current_hometown = info.get("hometown", "")
    new_hometown = input(f"🏠 Quê quán [{current_hometown}]: ").strip()
    if not new_hometown:
        new_hometown = current_hometown
    
    # Nơi sinh sống
    current_residence = info.get("residence", "")
    new_residence = input(f"📍 Nơi sinh sống [{current_residence}]: ").strip()
    if not new_residence:
        new_residence = current_residence
    
    # Xác nhận
    print("\n" + "-" * 70)
    print("📋 THÔNG TIN MỚI:")
    print(f"   Họ tên: {new_name}")
    print(f"   Giới tính: {new_gender}")
    print(f"   Năm sinh: {new_birth}")
    print(f"   Quê quán: {new_hometown}")
    print(f"   Nơi sinh sống: {new_residence}")
    print("-" * 70)
    
    confirm = input("\n💾 Lưu thay đổi? (yes/no): ").strip().lower()
    
    if confirm == "yes":
        update_data = {
            "user_name": new_name,
            "gender": new_gender,
            "birth_year": new_birth,
            "hometown": new_hometown,
            "residence": new_residence
        }
        
        result = db.update_person_info(folder_name, update_data)
        
        if result["success"]:
            print(f"\n✅ Đã cập nhật thông tin cho '{folder_name}'!")
        else:
            print(f"\n❌ Lỗi: {result.get('message', 'Không xác định')}")
    else:
        print("\n❌ Đã hủy chỉnh sửa")


def delete_person(folder_name: str):
    """Xóa người khỏi database"""
    db = DatabaseManager()
    info = db.get_person_info(folder_name)
    
    if not info:
        print(f"❌ Không tìm thấy '{folder_name}' trong database!")
        return
    
    print("\n" + "=" * 70)
    print(f"🗑️  XÓA NGƯỜI - {folder_name}")
    print("=" * 70)
    
    print(f"\n⚠️  BẠN SẮP XÓA:")
    print(f"   📁 Folder: {folder_name}")
    print(f"   👤 Tên: {info.get('user_name', 'N/A')}")
    print(f"   📊 Embeddings: {info.get('embedding_count', 0)}")
    
    # Kiểm tra folder ảnh
    faces_folder = os.path.join("faces", folder_name)
    if os.path.exists(faces_folder):
        image_files = [f for f in os.listdir(faces_folder) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        print(f"   📸 Ảnh: {len(image_files)}")
        delete_faces = input(f"\n   Xóa luôn folder faces/{folder_name}/ ? (yes/no): ").strip().lower()
    else:
        delete_faces = "no"
    
    confirm = input(f"\n🗑️  XÁC NHẬN XÓA '{folder_name}'? (yes/no): ").strip().lower()
    
    if confirm == "yes":
        result = db.delete_person(folder_name)
        
        if result["success"]:
            print(f"\n✅ Đã xóa database của '{folder_name}'")
            
            # Xóa folder ảnh nếu người dùng đồng ý
            if delete_faces == "yes" and os.path.exists(faces_folder):
                import shutil
                shutil.rmtree(faces_folder)
                print(f"✅ Đã xóa folder faces/{folder_name}/")
        else:
            print(f"\n❌ Lỗi: {result.get('message', 'Không xác định')}")
    else:
        print("\n❌ Đã hủy xóa")


def search_by_name(keyword: str):
    """Tìm kiếm người theo tên"""
    db = DatabaseManager()
    results = db.search_by_name(keyword)
    
    if not results:
        print(f"\n❌ Không tìm thấy ai với từ khóa '{keyword}'")
        return
    
    print("\n" + "=" * 100)
    print(f"🔍 KẾT QUẢ TÌM KIẾM: '{keyword}'")
    print("=" * 100)
    
    table_data = []
    
    for i, info in enumerate(results, 1):
        table_data.append([
            i,
            info.get("folder_name", "N/A"),
            info.get("user_name", "N/A"),
            info.get("gender", "N/A"),
            info.get("birth_year", "N/A"),
            info.get("hometown", "N/A"),
            info.get("residence", "N/A")
        ])
    
    headers = ["#", "Folder", "Họ tên", "Giới tính", "Năm sinh", "Quê", "Nơi ở"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print(f"\n📊 Tìm thấy: {len(results)} người")


def main_menu():
    """Menu chính"""
    while True:
        print("\n" + "=" * 70)
        print("🗂️  QUẢN LÝ DATABASE NHẬN DIỆN KHUÔN MẶT")
        print("=" * 70)
        print("\n1️⃣  Xem danh sách tất cả người")
        print("2️⃣  Xem chi tiết 1 người")
        print("3️⃣  Sửa thông tin")
        print("4️⃣  Xóa người")
        print("5️⃣  Tìm kiếm theo tên")
        print("0️⃣  Thoát")
        
        choice = input("\n👉 Chọn chức năng: ").strip()
        
        if choice == "1":
            view_all_people()
        
        elif choice == "2":
            folder_name = input("\n📁 Nhập folder_name: ").strip()
            view_person_detail(folder_name)
        
        elif choice == "3":
            folder_name = input("\n📁 Nhập folder_name cần sửa: ").strip()
            edit_person_info(folder_name)
        
        elif choice == "4":
            folder_name = input("\n📁 Nhập folder_name cần xóa: ").strip()
            delete_person(folder_name)
        
        elif choice == "5":
            keyword = input("\n🔍 Nhập từ khóa tìm kiếm: ").strip()
            search_by_name(keyword)
        
        elif choice == "0":
            print("\n👋 Tạm biệt!")
            break
        
        else:
            print("\n❌ Lựa chọn không hợp lệ!")


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Đã thoát!")
    except Exception as e:
        print(f"\n❌ Lỗi: {str(e)}")
