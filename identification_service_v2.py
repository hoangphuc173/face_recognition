"""
Face Recognition System - Identification Module V2
Luồng Nhận dạng với Database Manager (folder-based structure)

Chức năng:
1. Thu thập ảnh/video cần nhận diện
2. Trích xuất embedding từ khuôn mặt chưa rõ danh tính
3. Tìm kiếm và so sánh 1:N với database (đọc từ face_database/<folder_name>/)
4. Trả về kết quả trùng khớp với thông tin đầy đủ
"""

import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import cv2
import face_recognition
import numpy as np

from database_manager import DatabaseManager


class FaceIdentificationServiceV2:
    """Service quản lý nhận dạng khuôn mặt - Phiên bản 2"""

    def __init__(self, db_root: str = "face_database"):
        """
        Args:
            db_root: Thư mục gốc database
        """
        self.db = DatabaseManager(db_root=db_root)

    def reload_database(self):
        """Tải lại database (không cần thiết vì đọc trực tiếp từ file)"""
        print(f"🔄 [IDENTIFICATION] Database tự động cập nhật từ: {self.db.db_root}")
        people = self.db.get_all_people()
        print(f"📊 [IDENTIFICATION] Tổng số người: {len(people)}")

    def identify_face(
        self, image_path: str, max_results: int = 5, confidence_threshold: float = 0.6
    ) -> Dict:
        """
        Nhận dạng khuôn mặt từ ảnh

        Args:
            image_path: Đường dẫn ảnh cần nhận diện
            max_results: Số lượng kết quả tối đa trả về
            confidence_threshold: Ngưỡng tin cậy tối thiểu

        Returns:
            Dict chứa kết quả identification
        """
        result = {"success": False, "faces_detected": 0, "faces": [], "message": ""}

        try:
            # Kiểm tra database
            all_embeddings, all_metadata = self.db.get_all_embeddings_with_info()

            if not all_embeddings:
                result["message"] = "⚠️ Database trống. Vui lòng đăng ký khuôn mặt trước!"
                return result

            # Bước 1: Tải ảnh cần nhận diện
            print(f"🔍 [IDENTIFICATION] Đang xử lý ảnh: {image_path}")
            image = face_recognition.load_image_file(image_path)

            # Bước 2: Phát hiện tất cả khuôn mặt
            face_locations = face_recognition.face_locations(image)

            if not face_locations:
                result["message"] = "❌ Không phát hiện khuôn mặt nào trong ảnh"
                return result

            result["faces_detected"] = len(face_locations)
            print(f"👤 [IDENTIFICATION] Phát hiện {len(face_locations)} khuôn mặt")

            # Bước 3: Trích xuất embeddings cho tất cả khuôn mặt
            face_encodings = face_recognition.face_encodings(image, face_locations)

            # Bước 4: Tìm kiếm và so sánh 1:N với database
            for i, (face_location, face_encoding) in enumerate(zip(face_locations, face_encodings)):
                print(f"🔬 [IDENTIFICATION] Đang tìm kiếm cho khuôn mặt #{i+1}...")

                # So sánh với database
                matches = self._search_database(
                    face_encoding,
                    all_embeddings,
                    all_metadata,
                    max_results=max_results,
                    threshold=confidence_threshold,
                )

                face_result = {
                    "face_number": i + 1,
                    "location": {
                        "top": face_location[0],
                        "right": face_location[1],
                        "bottom": face_location[2],
                        "left": face_location[3],
                    },
                    "matches": matches,
                    "best_match": matches[0] if matches else None,
                }

                result["faces"].append(face_result)

                if matches:
                    print(f"✅ [IDENTIFICATION] Tìm thấy {len(matches)} kết quả phù hợp")
                    print(
                        f"   Top match: {matches[0]['user_name']} (folder: {matches[0]['folder_name']}, {matches[0]['confidence']:.1f}%)"
                    )
                else:
                    print(f"❓ [IDENTIFICATION] Không tìm thấy kết quả phù hợp")

            result["success"] = True
            result["message"] = f"✅ Đã xử lý {len(face_locations)} khuôn mặt"

        except Exception as e:
            result["message"] = f"❌ Lỗi: {str(e)}"
            print(result["message"])

        return result

    def identify_face_from_frame(
        self, frame: np.ndarray, confidence_threshold: float = 0.6
    ) -> List[Dict]:
        """
        Nhận dạng khuôn mặt từ frame (dùng cho webcam/video)

        Args:
            frame: Frame ảnh (numpy array)
            confidence_threshold: Ngưỡng tin cậy

        Returns:
            List các kết quả nhận diện
        """
        results = []

        try:
            all_embeddings, all_metadata = self.db.get_all_embeddings_with_info()

            if not all_embeddings:
                return results

            # Resize frame để tăng tốc
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # Phát hiện khuôn mặt
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            for face_location, face_encoding in zip(face_locations, face_encodings):
                # Tìm kiếm trong database
                matches = self._search_database(
                    face_encoding,
                    all_embeddings,
                    all_metadata,
                    max_results=1,
                    threshold=confidence_threshold,
                )

                # Scale lại location về kích thước gốc
                top, right, bottom, left = face_location
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                result = {
                    "location": (top, right, bottom, left),
                    "match": matches[0] if matches else None,
                }

                results.append(result)

        except Exception as e:
            print(f"❌ Lỗi identify_face_from_frame: {e}")

        return results

    def _search_database(
        self,
        query_embedding: np.ndarray,
        all_embeddings: List[np.ndarray],
        all_metadata: List[Dict],
        max_results: int = 5,
        threshold: float = 0.6,
    ) -> List[Dict]:
        """
        Tìm kiếm embedding trong database (1:N search)

        Args:
            query_embedding: Embedding cần tìm
            all_embeddings: List tất cả embeddings
            all_metadata: List tất cả metadata tương ứng
            max_results: Số kết quả tối đa
            threshold: Ngưỡng khoảng cách

        Returns:
            List các kết quả match, sắp xếp theo độ tin cậy
        """
        if not all_embeddings:
            return []

        # Tính khoảng cách với tất cả embeddings
        distances = face_recognition.face_distance(all_embeddings, query_embedding)

        # Tìm các kết quả phù hợp (distance < threshold)
        matches = []
        for i, distance in enumerate(distances):
            if distance < threshold:
                metadata = all_metadata[i]
                confidence = (1 - distance) * 100

                matches.append(
                    {
                        "folder_name": metadata["folder_name"],
                        "user_name": metadata["user_name"],
                        "gender": metadata.get("gender", ""),
                        "birth_year": metadata.get("birth_year", ""),
                        "hometown": metadata.get("hometown", ""),
                        "residence": metadata.get("residence", ""),
                        "confidence": float(confidence),
                        "distance": float(distance),
                        "created_at": metadata.get("created_at"),
                        "embedding_count": metadata.get("embedding_count", 0),
                    }
                )

        # Sắp xếp theo confidence (cao nhất trước)
        matches.sort(key=lambda x: x["confidence"], reverse=True)

        # Giới hạn số kết quả
        return matches[:max_results]

    def identify_and_annotate_image(
        self,
        image_path: str,
        output_path: str,
        confidence_threshold: float = 0.6,
        draw_confidence: bool = True,
    ) -> Dict:
        """
        Nhận dạng và vẽ annotation lên ảnh

        Args:
            image_path: Đường dẫn ảnh input
            output_path: Đường dẫn lưu ảnh output
            confidence_threshold: Ngưỡng tin cậy
            draw_confidence: Vẽ độ tin cậy lên ảnh

        Returns:
            Dict kết quả
        """
        result = self.identify_face(image_path, confidence_threshold=confidence_threshold)

        if not result["success"] or not result["faces"]:
            return result

        # Load ảnh
        image = cv2.imread(image_path)

        # Vẽ lên ảnh
        for face_data in result["faces"]:
            if face_data["best_match"]:
                match = face_data["best_match"]
                loc = face_data["location"]

                # Tạo info text
                info_lines = [match["user_name"]]
                if match.get("gender"):
                    info_lines.append(f"GT: {match['gender']}")
                if match.get("birth_year"):
                    info_lines.append(f"NS: {match['birth_year']}")
                if match.get("hometown"):
                    info_lines.append(f"QQ: {match['hometown']}")
                if match.get("residence"):
                    info_lines.append(f"NSS: {match['residence']}")
                if draw_confidence:
                    info_lines.append(f"{match['confidence']:.1f}%")

                # Vẽ rectangle
                cv2.rectangle(
                    image, (loc["left"], loc["top"]), (loc["right"], loc["bottom"]), (0, 255, 0), 2
                )

                # Vẽ info
                y_offset = loc["top"] - 10
                for line in reversed(info_lines):
                    cv2.putText(
                        image,
                        line,
                        (loc["left"], y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )
                    y_offset -= 25

        # Lưu ảnh
        cv2.imwrite(output_path, image)
        result["output_path"] = output_path

        return result

    def batch_identify(
        self, image_paths: List[str], confidence_threshold: float = 0.6
    ) -> List[Dict]:
        """
        Nhận dạng hàng loạt

        Args:
            image_paths: List đường dẫn ảnh
            confidence_threshold: Ngưỡng tin cậy

        Returns:
            List kết quả
        """
        results = []

        for image_path in image_paths:
            result = self.identify_face(image_path, confidence_threshold=confidence_threshold)
            results.append(result)

        return results


# Testing
if __name__ == "__main__":
    print("=" * 70)
    print("TEST IDENTIFICATION SERVICE V2 - FOLDER STRUCTURE")
    print("=" * 70)

    identification = FaceIdentificationServiceV2()

    # Test với ảnh có sẵn
    test_images = []
    if os.path.exists("faces"):
        for person_folder in os.listdir("faces"):
            person_path = os.path.join("faces", person_folder)
            if os.path.isdir(person_path):
                for img_file in os.listdir(person_path):
                    if img_file.lower().endswith((".jpg", ".jpeg", ".png")):
                        test_images.append(os.path.join(person_path, img_file))
                        break

    if test_images:
        test_img = test_images[0]
        print(f"\n🔍 Test nhận diện: {test_img}\n")

        result = identification.identify_face(image_path=test_img, confidence_threshold=0.6)

        if result["success"] and result["faces"]:
            for face_data in result["faces"]:
                if face_data["best_match"]:
                    match = face_data["best_match"]
                    print(f"\n✅ Nhận diện thành công!")
                    print(f"   👤 Tên: {match['user_name']}")
                    print(f"   📁 Folder: {match['folder_name']}")
                    print(f"   🎯 Độ tin cậy: {match['confidence']:.1f}%")

                    if match.get("gender"):
                        print(f"   ⚥ Giới tính: {match['gender']}")
                    if match.get("birth_year"):
                        print(f"   🎂 Năm sinh: {match['birth_year']}")
                    if match.get("hometown"):
                        print(f"   🏡 Quê quán: {match['hometown']}")
                    if match.get("residence"):
                        print(f"   📍 Nơi sinh sống: {match['residence']}")
        else:
            print(f"\n{result['message']}")
    else:
        print("\n⚠️ Không tìm thấy ảnh test")

    print("\n✅ TEST HOÀN TẤT")
