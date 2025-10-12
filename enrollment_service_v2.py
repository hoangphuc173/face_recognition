"""
Face Recognition System - Enrollment Module V2
Luồng Đăng ký với Database Manager (folder-based structure)

Chức năng:
1. Thu thập ảnh tham chiếu chất lượng cao
2. Trích xuất đặc trưng (embedding) từ khuôn mặt
3. Lưu embedding vào face_database/<folder_name>/embeddings.npy
4. Lưu thông tin vào face_database/<folder_name>/info.json
5. Tự động đánh số nếu trùng tên
6. Lưu ảnh vào faces/<folder_name>/
"""

import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional

import cv2
import face_recognition
import numpy as np

from database_manager import DatabaseManager


class FaceEnrollmentServiceV2:
    """Service quản lý đăng ký khuôn mặt - Phiên bản 2 với folder structure"""

    def __init__(self, storage_path: str = "faces", db_root: str = "face_database"):
        """
        Args:
            storage_path: Đường dẫn lưu ảnh tham chiếu (faces/)
            db_root: Đường dẫn database root (face_database/)
        """
        self.storage_path = storage_path
        self.db = DatabaseManager(db_root=db_root)

        # Tạo thư mục nếu chưa có
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)

    def enroll_face(
        self,
        image_path: str,
        user_name: str,
        gender: str = "",
        birth_year: str = "",
        hometown: str = "",
        residence: str = "",
        check_duplicate: bool = True,
        duplicate_threshold: float = 0.6,
    ) -> Dict:
        """
        Đăng ký khuôn mặt mới vào hệ thống

        Args:
            image_path: Đường dẫn ảnh tham chiếu
            user_name: Tên người dùng (bắt buộc)
            gender: Giới tính (Nam/Nữ)
            birth_year: Năm sinh
            hometown: Quê quán
            residence: Nơi sinh sống hiện tại
            check_duplicate: Kiểm tra trùng lặp
            duplicate_threshold: Ngưỡng phát hiện trùng lặp

        Returns:
            Dict chứa kết quả enrollment
        """
        result = {
            "success": False,
            "user_name": user_name,
            "folder_name": None,
            "message": "",
            "duplicate_found": False,
            "duplicate_info": None,
        }

        try:
            # Bước 1: Tải ảnh tham chiếu
            print(f"📸 [ENROLLMENT] Đang xử lý ảnh: {image_path}")
            image = face_recognition.load_image_file(image_path)

            # Bước 2: Phát hiện khuôn mặt
            face_locations = face_recognition.face_locations(image)

            if not face_locations:
                result["message"] = "❌ Không phát hiện khuôn mặt trong ảnh"
                return result

            if len(face_locations) > 1:
                result["message"] = "⚠️ Phát hiện nhiều khuôn mặt. Vui lòng dùng ảnh chỉ có 1 người"
                return result

            # Bước 3: Trích xuất embedding (đặc trưng)
            print(f"🔬 [ENROLLMENT] Đang trích xuất đặc trưng...")
            face_encodings = face_recognition.face_encodings(image, face_locations)

            if not face_encodings:
                result["message"] = "❌ Không thể trích xuất đặc trưng khuôn mặt"
                return result

            new_embedding = face_encodings[0]

            # Bước 4: Kiểm tra trùng lặp (tìm kiếm 1:N)
            if check_duplicate:
                print(f"🔍 [ENROLLMENT] Kiểm tra trùng lặp trong database...")
                duplicate_info = self._check_duplicate(new_embedding, duplicate_threshold)

                if duplicate_info:
                    result["duplicate_found"] = True
                    result["duplicate_info"] = duplicate_info
                    result["message"] = (
                        f"⚠️ Phát hiện trùng lặp với: {duplicate_info['user_name']} (folder: {duplicate_info['folder_name']}, Độ tương đồng: {duplicate_info['similarity']:.1f}%)"
                    )
                    print(result["message"])
                    return result

            # Bước 5: Tạo folder name duy nhất
            folder_name = self.db._generate_unique_folder_name(user_name)

            # Bước 6: Tạo hồ sơ trong database
            db_result = self.db.create_person(
                user_name=user_name,
                gender=gender,
                birth_year=birth_year,
                hometown=hometown,
                residence=residence,
                embeddings=[new_embedding],
            )

            if not db_result["success"]:
                result["message"] = db_result["message"]
                return result

            # Bước 7: Lưu ảnh vào faces/<folder_name>/
            person_folder = os.path.join(self.storage_path, folder_name)
            if not os.path.exists(person_folder):
                os.makedirs(person_folder)

            # Đếm số ảnh hiện có
            existing_images = len(
                [
                    f
                    for f in os.listdir(person_folder)
                    if f.lower().endswith((".jpg", ".jpeg", ".png"))
                ]
            )

            # Copy ảnh vào folder
            image_filename = f"{folder_name}_{existing_images + 1}.jpg"
            dest_path = os.path.join(person_folder, image_filename)

            if image_path != dest_path:
                shutil.copy(image_path, dest_path)

            result["success"] = True
            result["folder_name"] = folder_name
            result["message"] = f"✅ Đã đăng ký thành công: {user_name} (folder: {folder_name})"
            print(result["message"])
            print(f"📁 [ENROLLMENT] Ảnh lưu tại: {dest_path}")
            print(f"💾 [ENROLLMENT] Database: face_database/{folder_name}/")

        except Exception as e:
            result["message"] = f"❌ Lỗi: {str(e)}"
            print(result["message"])

        return result

    def _check_duplicate(self, new_embedding: np.ndarray, threshold: float) -> Optional[Dict]:
        """
        Kiểm tra trùng lặp trong database

        Args:
            new_embedding: Embedding cần kiểm tra
            threshold: Ngưỡng phát hiện trùng lặp

        Returns:
            Dict chứa thông tin duplicate nếu tìm thấy, None nếu không
        """
        all_embeddings, all_metadata = self.db.get_all_embeddings_with_info()

        if not all_embeddings:
            return None

        # So sánh với tất cả embeddings
        distances = face_recognition.face_distance(all_embeddings, new_embedding)

        # Tìm kết quả khớp nhất
        best_match_index = np.argmin(distances)
        best_distance = distances[best_match_index]

        if best_distance < threshold:
            metadata = all_metadata[best_match_index]
            return {
                "folder_name": metadata["folder_name"],
                "user_name": metadata["user_name"],
                "distance": float(best_distance),
                "similarity": (1 - best_distance) * 100,
                "metadata": metadata,
            }

        return None

    def add_image_to_existing_person(self, image_path: str, folder_name: str) -> Dict:
        """
        Thêm ảnh mới cho người đã đăng ký

        Args:
            image_path: Đường dẫn ảnh mới
            folder_name: Tên folder của người

        Returns:
            Dict chứa kết quả
        """
        # Kiểm tra người có tồn tại không
        person_info = self.db.get_person_info(folder_name)

        if not person_info:
            return {"success": False, "message": f"❌ Không tìm thấy folder: {folder_name}"}

        try:
            # Trích xuất embedding
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image)

            if not face_locations:
                return {"success": False, "message": "❌ Không phát hiện khuôn mặt trong ảnh"}

            face_encodings = face_recognition.face_encodings(image, face_locations)

            if not face_encodings:
                return {"success": False, "message": "❌ Không thể trích xuất đặc trưng"}

            new_embedding = face_encodings[0]

            # Thêm embedding vào database
            db_result = self.db.add_embedding(folder_name, new_embedding)

            if not db_result["success"]:
                return db_result

            # Lưu ảnh vào faces/<folder_name>/
            person_folder = os.path.join(self.storage_path, folder_name)
            if not os.path.exists(person_folder):
                os.makedirs(person_folder)

            existing_images = len(
                [
                    f
                    for f in os.listdir(person_folder)
                    if f.lower().endswith((".jpg", ".jpeg", ".png"))
                ]
            )

            image_filename = f"{folder_name}_{existing_images + 1}.jpg"
            dest_path = os.path.join(person_folder, image_filename)
            shutil.copy(image_path, dest_path)

            return {
                "success": True,
                "message": f"✅ Đã thêm ảnh cho {person_info['user_name']} ({db_result['message']})",
            }

        except Exception as e:
            return {"success": False, "message": f"❌ Lỗi: {str(e)}"}

    def list_enrolled_people(self) -> List[Dict]:
        """Liệt kê tất cả người đã đăng ký"""
        return self.db.get_all_people()

    def remove_person(self, folder_name: str, remove_images: bool = True) -> Dict:
        """
        Xóa người khỏi database

        Args:
            folder_name: Tên folder cần xóa
            remove_images: Có xóa folder ảnh không

        Returns:
            Dict kết quả
        """
        # Xóa khỏi database
        db_result = self.db.delete_person(folder_name)

        if not db_result["success"]:
            return db_result

        # Xóa folder ảnh
        if remove_images:
            person_folder = os.path.join(self.storage_path, folder_name)
            if os.path.exists(person_folder):
                shutil.rmtree(person_folder)

        return db_result

    def get_stats(self) -> Dict:
        """Lấy thống kê database"""
        people = self.db.get_all_people()
        total_embeddings = sum(p["embedding_count"] for p in people)

        return {
            "total_people": len(people),
            "total_embeddings": total_embeddings,
            "average_images_per_person": total_embeddings / len(people) if people else 0,
            "storage_path": self.storage_path,
            "database_path": self.db.db_root,
        }


# Testing
if __name__ == "__main__":
    print("=" * 70)
    print("TEST ENROLLMENT SERVICE V2 - FOLDER STRUCTURE")
    print("=" * 70)

    enrollment = FaceEnrollmentServiceV2()

    # Test với ảnh có sẵn
    test_images = []
    if os.path.exists("faces"):
        for person_folder in os.listdir("faces"):
            person_path = os.path.join("faces", person_folder)
            if os.path.isdir(person_path):
                for img_file in os.listdir(person_path):
                    if img_file.lower().endswith((".jpg", ".jpeg", ".png")):
                        test_images.append(
                            {
                                "path": os.path.join(person_path, img_file),
                                "name": person_folder.capitalize(),
                            }
                        )
                        break

    if test_images:
        img = test_images[0]
        print(f"\n📸 Test đăng ký: {img['name']}")
        print(f"   Ảnh: {img['path']}\n")

        result = enrollment.enroll_face(
            image_path=img["path"],
            user_name=img["name"],
            gender="Nam",
            birth_year="1990",
            hometown="Hà Nội",
            residence="TP.HCM",
            check_duplicate=True,
        )

        print(f"\n{result['message']}")

        # Stats
        print("\n📊 Thống kê:")
        stats = enrollment.get_stats()
        print(f"   Số người: {stats['total_people']}")
        print(f"   Tổng embeddings: {stats['total_embeddings']}")
        print(f"   Trung bình ảnh/người: {stats['average_images_per_person']:.1f}")
    else:
        print("\n⚠️ Không tìm thấy ảnh test")

    print("\n✅ TEST HOÀN TẤT")
