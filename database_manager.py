"""
Database Manager - Quản lý database theo cấu trúc folder
Mỗi người 1 folder riêng trong face_database/

Cấu trúc:
face_database/
├── nguyen_van_a/
│   ├── info.json (tên, giới tính, năm sinh, quê, nơi ở)
│   └── embeddings.npy (numpy array của tất cả embeddings)
├── nguyen_van_a_1/  (nếu trùng tên)
│   ├── info.json
│   └── embeddings.npy
└── ...
"""

import os
import json
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import shutil

class DatabaseManager:
    """Quản lý database theo cấu trúc folder"""
    
    def __init__(self, db_root: str = "face_database"):
        """
        Args:
            db_root: Thư mục gốc chứa database
        """
        self.db_root = db_root
        if not os.path.exists(db_root):
            os.makedirs(db_root)
    
    def _generate_unique_folder_name(self, base_name: str) -> str:
        """
        Tạo tên folder duy nhất, tự động đánh số nếu trùng
        
        Args:
            base_name: Tên cơ bản (ví dụ: "nguyen_van_a")
            
        Returns:
            Tên folder duy nhất (ví dụ: "nguyen_van_a" hoặc "nguyen_van_a_1")
        """
        # Chuẩn hóa tên: loại bỏ ký tự đặc biệt, chuyển thành lowercase, thay space bằng _
        normalized = base_name.lower().strip()
        normalized = normalized.replace(" ", "_")
        # Loại bỏ ký tự không hợp lệ
        normalized = "".join(c for c in normalized if c.isalnum() or c == "_")
        
        folder_path = os.path.join(self.db_root, normalized)
        
        # Nếu chưa tồn tại, dùng tên gốc
        if not os.path.exists(folder_path):
            return normalized
        
        # Nếu đã tồn tại, thêm số đánh thứ tự
        counter = 1
        while True:
            new_name = f"{normalized}_{counter}"
            new_path = os.path.join(self.db_root, new_name)
            if not os.path.exists(new_path):
                return new_name
            counter += 1
    
    def create_person(
        self,
        user_name: str,
        gender: str = "",
        birth_year: str = "",
        hometown: str = "",
        residence: str = "",
        embeddings: Optional[List[np.ndarray]] = None,
        custom_data: Optional[Dict] = None
    ) -> Dict:
        """
        Tạo hồ sơ người mới trong database
        
        Args:
            user_name: Tên người (bắt buộc)
            gender: Giới tính
            birth_year: Năm sinh
            hometown: Quê quán
            residence: Nơi sinh sống
            embeddings: List các embeddings (128D vectors)
            custom_data: Dữ liệu tùy chỉnh khác
            
        Returns:
            Dict kết quả với folder_name
        """
        # Tạo folder name duy nhất
        folder_name = self._generate_unique_folder_name(user_name)
        folder_path = os.path.join(self.db_root, folder_name)
        
        # Tạo folder
        os.makedirs(folder_path, exist_ok=True)
        
        # Tạo thông tin
        info = {
            "folder_name": folder_name,
            "user_name": user_name,
            "gender": gender,
            "birth_year": birth_year,
            "hometown": hometown,
            "residence": residence,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "embedding_count": len(embeddings) if embeddings else 0,
            "custom_data": custom_data or {}
        }
        
        # Lưu info.json
        info_path = os.path.join(folder_path, "info.json")
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        
        # Lưu embeddings.npy
        if embeddings:
            embeddings_array = np.array(embeddings)
            embeddings_path = os.path.join(folder_path, "embeddings.npy")
            np.save(embeddings_path, embeddings_array)
        
        return {
            "success": True,
            "folder_name": folder_name,
            "folder_path": folder_path,
            "message": f"✅ Đã tạo hồ sơ: {user_name} (folder: {folder_name})"
        }
    
    def add_embedding(self, folder_name: str, embedding: np.ndarray) -> Dict:
        """
        Thêm embedding mới cho người đã tồn tại
        
        Args:
            folder_name: Tên folder của người
            embedding: Embedding mới (128D vector)
            
        Returns:
            Dict kết quả
        """
        folder_path = os.path.join(self.db_root, folder_name)
        
        if not os.path.exists(folder_path):
            return {
                "success": False,
                "message": f"❌ Không tìm thấy folder: {folder_name}"
            }
        
        # Load embeddings hiện tại
        embeddings_path = os.path.join(folder_path, "embeddings.npy")
        
        if os.path.exists(embeddings_path):
            existing_embeddings = np.load(embeddings_path)
            # Thêm embedding mới
            updated_embeddings = np.vstack([existing_embeddings, embedding])
        else:
            updated_embeddings = np.array([embedding])
        
        # Lưu lại
        np.save(embeddings_path, updated_embeddings)
        
        # Cập nhật info.json
        info_path = os.path.join(folder_path, "info.json")
        with open(info_path, 'r', encoding='utf-8') as f:
            info = json.load(f)
        
        info["embedding_count"] = len(updated_embeddings)
        info["updated_at"] = datetime.now().isoformat()
        
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "message": f"✅ Đã thêm embedding (tổng: {len(updated_embeddings)})"
        }
    
    def get_person_info(self, folder_name: str) -> Optional[Dict]:
        """
        Lấy thông tin của người
        
        Args:
            folder_name: Tên folder
            
        Returns:
            Dict thông tin hoặc None nếu không tìm thấy
        """
        folder_path = os.path.join(self.db_root, folder_name)
        info_path = os.path.join(folder_path, "info.json")
        
        if not os.path.exists(info_path):
            return None
        
        with open(info_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_person_embeddings(self, folder_name: str) -> Optional[np.ndarray]:
        """
        Lấy tất cả embeddings của người
        
        Args:
            folder_name: Tên folder
            
        Returns:
            Numpy array hoặc None
        """
        folder_path = os.path.join(self.db_root, folder_name)
        embeddings_path = os.path.join(folder_path, "embeddings.npy")
        
        if not os.path.exists(embeddings_path):
            return None
        
        return np.load(embeddings_path)
    
    def get_all_people(self) -> List[Dict]:
        """
        Lấy danh sách tất cả người trong database
        
        Returns:
            List thông tin của tất cả người
        """
        people = []
        
        if not os.path.exists(self.db_root):
            return people
        
        for folder_name in os.listdir(self.db_root):
            folder_path = os.path.join(self.db_root, folder_name)
            
            if os.path.isdir(folder_path):
                info = self.get_person_info(folder_name)
                if info:
                    people.append(info)
        
        return people
    
    def get_all_embeddings_with_info(self) -> Tuple[List[np.ndarray], List[Dict]]:
        """
        Lấy tất cả embeddings và metadata (để nhận diện 1:N)
        
        Returns:
            Tuple (list embeddings, list metadata)
        """
        all_embeddings = []
        all_metadata = []
        
        for person_info in self.get_all_people():
            folder_name = person_info["folder_name"]
            embeddings = self.get_person_embeddings(folder_name)
            
            if embeddings is not None:
                # Mỗi embedding gắn với metadata của người đó
                for embedding in embeddings:
                    all_embeddings.append(embedding)
                    all_metadata.append(person_info)
        
        return all_embeddings, all_metadata
    
    def update_person_info(
        self,
        folder_name: str,
        user_name: Optional[str] = None,
        gender: Optional[str] = None,
        birth_year: Optional[str] = None,
        hometown: Optional[str] = None,
        residence: Optional[str] = None
    ) -> Dict:
        """
        Cập nhật thông tin của người
        
        Args:
            folder_name: Tên folder
            user_name, gender, birth_year, hometown, residence: Thông tin cần update
            
        Returns:
            Dict kết quả
        """
        info = self.get_person_info(folder_name)
        
        if not info:
            return {
                "success": False,
                "message": f"❌ Không tìm thấy: {folder_name}"
            }
        
        # Cập nhật các trường được cung cấp
        if user_name is not None:
            info["user_name"] = user_name
        if gender is not None:
            info["gender"] = gender
        if birth_year is not None:
            info["birth_year"] = birth_year
        if hometown is not None:
            info["hometown"] = hometown
        if residence is not None:
            info["residence"] = residence
        
        info["updated_at"] = datetime.now().isoformat()
        
        # Lưu lại
        folder_path = os.path.join(self.db_root, folder_name)
        info_path = os.path.join(folder_path, "info.json")
        
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "message": f"✅ Đã cập nhật thông tin: {folder_name}"
        }
    
    def delete_person(self, folder_name: str) -> Dict:
        """
        Xóa hoàn toàn 1 người khỏi database
        
        Args:
            folder_name: Tên folder cần xóa
            
        Returns:
            Dict kết quả
        """
        folder_path = os.path.join(self.db_root, folder_name)
        
        if not os.path.exists(folder_path):
            return {
                "success": False,
                "message": f"❌ Không tìm thấy: {folder_name}"
            }
        
        shutil.rmtree(folder_path)
        
        return {
            "success": True,
            "message": f"✅ Đã xóa: {folder_name}"
        }
    
    def search_by_name(self, name_query: str) -> List[Dict]:
        """
        Tìm kiếm người theo tên (không phân biệt hoa/thường)
        
        Args:
            name_query: Từ khóa tìm kiếm
            
        Returns:
            List thông tin người phù hợp
        """
        results = []
        query_lower = name_query.lower()
        
        for person_info in self.get_all_people():
            if query_lower in person_info["user_name"].lower():
                results.append(person_info)
        
        return results


# Testing
if __name__ == "__main__":
    # Test DatabaseManager
    db = DatabaseManager()
    
    print("=" * 60)
    print("TEST DATABASE MANAGER")
    print("=" * 60)
    
    # Test 1: Tạo người mới
    print("\n1. Tạo người mới:")
    dummy_embedding = np.random.rand(128)
    
    result = db.create_person(
        user_name="Nguyễn Văn A",
        gender="Nam",
        birth_year="1990",
        hometown="Hà Nội",
        residence="TP.HCM",
        embeddings=[dummy_embedding]
    )
    print(result["message"])
    
    # Test 2: Tạo người trùng tên
    print("\n2. Tạo người trùng tên:")
    result2 = db.create_person(
        user_name="Nguyễn Văn A",
        gender="Nam",
        birth_year="1995",
        hometown="Đà Nẵng",
        residence="Hà Nội",
        embeddings=[dummy_embedding]
    )
    print(result2["message"])
    
    # Test 3: Liệt kê tất cả
    print("\n3. Danh sách tất cả người:")
    people = db.get_all_people()
    for person in people:
        print(f"   - {person['user_name']} (folder: {person['folder_name']})")
        print(f"     Giới tính: {person['gender']}, Năm sinh: {person['birth_year']}")
        print(f"     Quê: {person['hometown']}, Nơi ở: {person['residence']}")
    
    # Test 4: Thêm embedding
    print("\n4. Thêm embedding:")
    result3 = db.add_embedding(result["folder_name"], dummy_embedding)
    print(result3["message"])
    
    print("\n✅ TEST HOÀN TẤT")
