# 📂 CẤU TRÚC DATABASE MỚI - FOLDER-BASED

## 🎯 Thay đổi lớn

Hệ thống đã được nâng cấp từ **single-file database** sang **folder-based structure**:

### ❌ TRƯỚC (face_database.pkl):
```
face_database.pkl  (tất cả embeddings + metadata trong 1 file)
```

### ✅ SAU (face_database/):
```
face_database/
├── hong/
│   ├── info.json          (tên, giới tính, năm sinh, quê, nơi ở)
│   └── embeddings.npy     (tất cả embeddings của Hong)
├── nguyen_van_a/
│   ├── info.json
│   └── embeddings.npy
├── nguyen_van_a_1/        ← Tự động đánh số nếu trùng tên!
│   ├── info.json
│   └── embeddings.npy
└── ...
```

---

## 🌟 Ưu điểm

### 1️⃣ **Tự động đánh số khi trùng tên**
```
Nguyễn Văn A → nguyen_van_a/
Nguyễn Văn A (khác) → nguyen_van_a_1/
Nguyễn Văn A (khác nữa) → nguyen_van_a_2/
```

### 2️⃣ **Dễ quản lý**
- Mỗi người 1 folder riêng
- Xem thông tin: mở `info.json`
- Xem embeddings: load `embeddings.npy`
- Xóa người: xóa folder

### 3️⃣ **Tương ứng với faces/**
```
faces/hong/          ↔  face_database/hong/
faces/nguyen_van_a/  ↔  face_database/nguyen_van_a/
```

### 4️⃣ **Mở rộng dễ dàng**
- Thêm field mới vào `info.json`
- Không cần rebuild toàn bộ database
- Backup từng người riêng lẻ

---

## 📋 Cấu trúc File

### info.json
```json
{
  "folder_name": "nguyen_van_a",
  "user_name": "Nguyễn Văn A",
  "gender": "Nam",
  "birth_year": "1990",
  "hometown": "Hà Nội",
  "residence": "TP. Hồ Chí Minh",
  "created_at": "2025-10-12T22:45:57",
  "updated_at": "2025-10-12T22:45:57",
  "embedding_count": 3,
  "custom_data": {}
}
```

### embeddings.npy
- Numpy array shape: `(N, 128)` 
- N = số ảnh đã đăng ký
- 128 = kích thước embedding vector

---

## 🔄 Migration

### Tự động migrate dữ liệu cũ:
```bash
python migrate_to_folder_db.py
```

Script sẽ:
1. ✅ Backup `face_database.pkl` → `face_database.pkl.backup`
2. ✅ Đọc tất cả embeddings + metadata
3. ✅ Nhóm theo người
4. ✅ Tạo folder cho mỗi người
5. ✅ Lưu `info.json` và `embeddings.npy`

---

## 💻 Sử dụng API mới

### Enrollment Service V2:
```python
from enrollment_service_v2 import FaceEnrollmentServiceV2

enrollment = FaceEnrollmentServiceV2()

# Đăng ký người mới
result = enrollment.enroll_face(
    image_path='photo.jpg',
    user_name='Nguyễn Văn A',  # Tự động tạo folder duy nhất
    gender='Nam',
    birth_year='1990',
    hometown='Hà Nội',
    residence='TP.HCM'
)

print(result['folder_name'])  # → nguyen_van_a
# Nếu đăng ký người trùng tên:
# → nguyen_van_a_1, nguyen_van_a_2, ...
```

### Identification Service V2:
```python
from identification_service_v2 import FaceIdentificationServiceV2

identification = FaceIdentificationServiceV2()

# Nhận diện
result = identification.identify_face('unknown.jpg')

for face in result['faces']:
    if face['best_match']:
        match = face['best_match']
        print(f"Tên: {match['user_name']}")
        print(f"Folder: {match['folder_name']}")  # ← MỚI
        print(f"Giới tính: {match['gender']}")
        print(f"Năm sinh: {match['birth_year']}")
        print(f"Quê: {match['hometown']}")
```

### Database Manager (Low-level):
```python
from database_manager import DatabaseManager

db = DatabaseManager()

# Tạo người mới
db.create_person(
    user_name='Nguyễn Văn A',
    gender='Nam',
    embeddings=[embedding_vector]
)

# Lấy thông tin
info = db.get_person_info('nguyen_van_a')
print(info['user_name'])  # → Nguyễn Văn A

# Lấy embeddings
embeddings = db.get_person_embeddings('nguyen_van_a')
print(embeddings.shape)  # → (3, 128)

# Liệt kê tất cả
people = db.get_all_people()
for person in people:
    print(f"{person['user_name']} - {person['folder_name']}")

# Xóa người
db.delete_person('nguyen_van_a')
```

---

## 📊 So sánh

| Tính năng | face_database.pkl | face_database/ |
|-----------|-------------------|----------------|
| Cấu trúc | Single file | Folder-based |
| Trùng tên | Conflict | Tự động đánh số |
| Quản lý | Phải rebuild | Edit từng file |
| Backup | Toàn bộ | Từng người |
| Mở rộng | Khó | Dễ dàng |
| Tốc độ | Nhanh (trong RAM) | Đọc từ disk |

---

## 🔧 Files mới

| File | Mô tả |
|------|-------|
| `database_manager.py` | Class quản lý database folder |
| `enrollment_service_v2.py` | Enrollment với folder structure |
| `identification_service_v2.py` | Identification với folder structure |
| `migrate_to_folder_db.py` | Script migrate dữ liệu cũ |

---

## ✅ Checklist Migration

- [x] Tạo DatabaseManager
- [x] Tạo Enrollment Service V2
- [x] Tạo Identification Service V2
- [x] Script migrate dữ liệu cũ
- [x] Test với dữ liệu thật
- [x] Tự động đánh số khi trùng tên
- [x] Tương thích với faces/ folder
- [x] Documentation đầy đủ

---

## 🚀 Bước tiếp theo

1. **Migrate dữ liệu:**
   ```bash
   python migrate_to_folder_db.py
   ```

2. **Test hệ thống mới:**
   ```bash
   python enrollment_service_v2.py
   python identification_service_v2.py
   ```

3. **Cập nhật GUI:** (nếu cần)
   - Import `enrollment_service_v2` thay vì `enrollment_service`
   - Import `identification_service_v2` thay vì `identification_service`

4. **Xóa file cũ:** (sau khi test OK)
   ```bash
   del face_database.pkl
   ```

---

**Version:** 3.0 - Folder-Based Database  
**Date:** October 12, 2025  
**Status:** ✅ Ready to use
