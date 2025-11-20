# Kiến Trúc Hệ Thống Thực Tế - Face Recognition System

> 📅 Cập nhật: November 19, 2025  
> 🎯 Đây là kiến trúc **THỰC TẾ ĐANG CHẠY**, không phải kiến trúc lý thuyết

---

## 📊 Sơ Đồ Kiến Trúc Thực Tế

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT APPLICATIONS                           │
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│  │   PyQt5 GUI  │    │  CLI Scripts │    │  Test Files  │         │
│  │ (Desktop App)│    │   (Python)   │    │              │         │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘         │
│         │                   │                    │                  │
│         └───────────────────┴────────────────────┘                  │
│                             │                                        │
└─────────────────────────────┼────────────────────────────────────────┘
                              │
                              │ HTTP REST API
                              │ (localhost:8888)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FASTAPI SERVER (Local)                          │
│                                                                      │
│  ┌──────────────────────────────────────────────────────┐           │
│  │              FastAPI Application                     │           │
│  │  • POST /api/v1/enroll     (Enrollment)             │           │
│  │  • POST /api/v1/identify   (Identification)         │           │
│  │  • GET  /api/v1/people     (List people)            │           │
│  │  • GET  /api/v1/health     (Health check)           │           │
│  └────┬─────────────────────────┬─────────────────┬─────┘           │
│       │                         │                 │                 │
│       │                         │                 │                 │
│  ┌────▼─────────┐   ┌──────────▼────────┐  ┌────▼────────────┐    │
│  │ Enrollment   │   │  Identification   │  │   Database      │    │
│  │   Service    │   │     Service       │  │    Manager      │    │
│  └────┬─────────┘   └──────────┬────────┘  └────┬────────────┘    │
│       │                        │                 │                 │
└───────┼────────────────────────┼─────────────────┼─────────────────┘
        │                        │                 │
        │                        │                 │
        └────────┬───────────────┴─────────────────┘
                 │
                 │ boto3 SDK
                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         AWS SERVICES                                 │
│                                                                      │
│  ┌──────────────────┐   ┌──────────────────┐   ┌─────────────────┐│
│  │   Amazon S3      │   │  AWS Rekognition │   │   DynamoDB      ││
│  │                  │   │                  │   │                 ││
│  │  Bucket:         │   │  Collection:     │   │  Tables:        ││
│  │  face-recognition│   │  face-recognition│   │  • people       ││
│  │  -20251119-*     │   │  -collection-dev │   │  • embeddings   ││
│  │                  │   │                  │   │  • matches      ││
│  │  Stores:         │   │  Stores:         │   │                 ││
│  │  • Face images   │   │  • Face vectors  │   │  Stores:        ││
│  │  • Original pics │   │  • Face indexes  │   │  • User metadata││
│  │                  │   │                  │   │  • Match records││
│  └──────────────────┘   └──────────────────┘   └─────────────────┘│
│                                                                      │
│  Region: ap-southeast-1 (Singapore)                                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Chi Tiết Components

### **1. Client Layer**

#### **PyQt5 Desktop GUI** (`app/gui_app.py`)
- **Chức năng:**
  - Camera feed real-time với face detection (OpenCV)
  - Enroll faces từ camera hoặc file
  - Identify faces với auto-refresh mode
  - Quản lý database (view/delete people)
  - Hiển thị tên + confidence trên frame

- **Tech Stack:**
  - PyQt5 (UI framework)
  - OpenCV (camera & face detection)
  - requests (HTTP client)

#### **CLI Scripts**
- `create_database.py` - Tạo DynamoDB tables + S3 bucket
- `reset_database.py` - Xóa toàn bộ dữ liệu
- `check_faces.py` - Kiểm tra faces trong Rekognition
- `test_identify.py` - Test identification API

---

### **2. API Server Layer**

#### **FastAPI Application** (`backend/api/app.py`)
- **Port:** 8888 (localhost)
- **Mode:** Development với auto-reload
- **Authentication:** DISABLED (local dev)

**Endpoints:**

| Method | Path | Function | Description |
|--------|------|----------|-------------|
| POST | `/api/v1/enroll` | `enroll_face()` | Upload ảnh + metadata để enroll |
| POST | `/api/v1/identify` | `identify_face()` | Nhận diện khuôn mặt trong ảnh |
| GET | `/api/v1/people` | `list_people()` | Liệt kê tất cả người đã enroll |
| DELETE | `/api/v1/people/{id}` | `delete_person()` | Xóa người khỏi database |
| GET | `/api/v1/health` | `health_check()` | Kiểm tra trạng thái API |

#### **Service Layer**

**EnrollmentService** (`backend/core/enrollment_service.py`)
- Upload ảnh lên S3
- Index face vào Rekognition collection
- Lưu metadata vào DynamoDB people table
- Lưu embedding info vào embeddings table

**IdentificationService** (`backend/core/identification_service.py`)
- Search faces trong Rekognition collection
- Batch get metadata từ DynamoDB
- Trả về list matches với similarity scores
- **Threshold:** 60% (configurable)

**DatabaseManager** (`backend/core/database_manager.py`)
- CRUD operations cho DynamoDB
- Batch operations cho performance
- Handle Decimal ↔ float conversion

---

### **3. AWS Services Layer**

#### **Amazon S3**
- **Bucket:** `face-recognition-20251119-215108-32ce1e86`
- **Structure:**
  ```
  s3://bucket/
  ├── people/
  │   ├── person_xxx/
  │   │   ├── face_001.jpg
  │   │   ├── face_002.jpg
  │   │   └── ...
  ```
- **Access:** Boto3 S3 client
- **Purpose:** Lưu trữ ảnh gốc

#### **AWS Rekognition**
- **Collection ID:** `face-recognition-collection-dev`
- **Features Used:**
  - `index_faces()` - Index khuôn mặt mới
  - `search_faces_by_image()` - Tìm khuôn mặt tương tự
  - `list_faces()` - List all indexed faces
  - `delete_faces()` - Xóa faces
- **Face Vectors:** 4 faces đã được indexed
- **Threshold:** 60% similarity

#### **DynamoDB Tables**

**Table: `face-recognition-people-dev`**
- **Partition Key:** `person_id` (String)
- **Attributes:**
  - `user_name` - Tên người
  - `gender` - Giới tính
  - `birth_year` - Năm sinh
  - `residence` - Nơi ở
  - `hometown` - Quê quán
  - `embedding_count` - Số ảnh đã enroll
  - `created_at`, `updated_at` - Timestamps

**Table: `face-recognition-embeddings-dev`**
- **Partition Key:** `embedding_id` (String)
- **Attributes:**
  - `person_id` - Foreign key
  - `face_id` - Rekognition face ID
  - `s3_url` - Link ảnh trên S3
  - `image_quality` - Chất lượng ảnh
  - `created_at` - Timestamp

**Table: `face-recognition-matches-dev`**
- **Partition Key:** `match_id` (String)
- **Attributes:**
  - `person_id` - Người được nhận diện
  - `similarity` - Độ tương tự (%)
  - `confidence` - Độ tin cậy
  - `matched_at` - Thời gian match

---

## 🔄 Luồng Xử Lý

### **Enrollment Flow**

```
1. User chụp ảnh từ camera → GUI
2. GUI POST /api/v1/enroll với:
   - image (bytes)
   - user_name, gender, birth_year, residence, hometown
3. EnrollmentService:
   ├─→ S3Client.upload_image() 
   │   └─ Lưu ảnh vào S3, trả về s3_url
   ├─→ RekognitionClient.index_face()
   │   └─ Index face vào collection, trả về face_id
   ├─→ DatabaseManager.create_person()
   │   └─ Lưu metadata vào people table
   └─→ DatabaseManager.save_embedding()
       └─ Lưu embedding info vào embeddings table
4. Trả về success + person_id cho GUI
```

### **Identification Flow**

```
1. User click "Identify Now" hoặc bật "Auto: ON" → GUI
2. GUI POST /api/v1/identify với image (bytes)
3. IdentificationService:
   ├─→ RekognitionClient.search_faces_by_image()
   │   ├─ Threshold: 60%
   │   └─ Trả về list matches với face_id + similarity
   ├─→ DatabaseManager.get_people_batch()
   │   └─ Batch get metadata của matched persons
   └─→ Merge data: matches + metadata
4. Trả về:
   {
     "success": true,
     "faces_detected": 1,
     "faces": [
       {
         "person_id": "person_xxx",
         "user_name": "phuc",
         "similarity": 98.5,
         "confidence": 99.9
       }
     ]
   }
5. GUI:
   ├─→ Hiển thị tên trên frame: "phuc (98.5%)"
   └─→ Update "Last Result: ✅ phuc (98.5%)"
```

---

## 📦 Tech Stack

### **Backend**
- **Framework:** FastAPI 0.104+
- **AWS SDK:** boto3
- **Config:** Pydantic Settings + python-dotenv
- **Logging:** Custom JSON logger
- **Validation:** Pydantic models

### **Frontend**
- **GUI:** PyQt5
- **Computer Vision:** OpenCV (cv2)
- **HTTP Client:** requests
- **Face Detection:** Haar Cascade (local)

### **Infrastructure**
- **Cloud Provider:** AWS
- **Region:** ap-southeast-1 (Singapore)
- **Deployment:** Local development (no containers)
- **Environment:** Development mode

---

## ⚙️ Configuration

### **Environment Variables** (`.env`)
```bash
# AWS
AWS_REGION=ap-southeast-1
AWS_S3_BUCKET=face-recognition-20251119-215108-32ce1e86
AWS_REKOGNITION_COLLECTION=face-recognition-collection-dev
AWS_DYNAMODB_PEOPLE_TABLE=face-recognition-people-dev
AWS_DYNAMODB_EMBEDDINGS_TABLE=face-recognition-embeddings-dev
AWS_DYNAMODB_MATCHES_TABLE=face-recognition-matches-dev

# App
APP_ENV=development
DEBUG=true
ENABLE_CORS=true

# Disabled Features
COGNITO_ENABLED=false
API_KEY_ENABLED=false
ENABLE_XRAY=false
```

### **GUI Configuration** (`app/gui_app.py`)
```python
USE_LOCAL_API = True
LOCAL_API_URL = "http://127.0.0.1:8888"
CAMERA_ID = 0
```

---

## 🎯 Current Status

### **✅ Working Features**
- ✅ Face enrollment từ camera và file
- ✅ Face identification với threshold 60%
- ✅ Real-time camera feed với face detection
- ✅ Auto-identify mode (mỗi 2 giây)
- ✅ Hiển thị tên + confidence trên frame
- ✅ Database management (list, delete)
- ✅ Health check endpoint

### **📊 System Metrics**
- **Enrolled People:** 4
- **Indexed Faces:** 4 (trong Rekognition)
- **API Response Time:** ~200-500ms
- **Face Detection FPS:** ~30 FPS

### **❌ Not Implemented**
- ❌ Authentication (Cognito)
- ❌ Caching (Redis/ElastiCache)
- ❌ Message Queue (SQS/Kinesis)
- ❌ Monitoring (CloudWatch/X-Ray)
- ❌ Encryption (KMS)
- ❌ Notifications (SNS)
- ❌ Serverless deployment (Lambda)
- ❌ API Gateway
- ❌ Step Functions orchestration
- ❌ CloudTrail audit logging

---

## 🔐 Security Notes

⚠️ **Current Security Status: DEVELOPMENT MODE**

- No authentication/authorization
- AWS credentials từ default profile
- No encryption at rest/in transit
- No rate limiting
- No input sanitization
- Local network only (127.0.0.1)

**Không dùng cho production!**

---

## 📈 Performance Characteristics

| Metric | Value | Notes |
|--------|-------|-------|
| Enroll Time | ~1-2s | S3 + Rekognition + DynamoDB |
| Identify Time | ~200-500ms | Rekognition search + DynamoDB batch get |
| Camera FPS | ~30 FPS | Local OpenCV processing |
| Auto-identify Interval | 2s | Configurable |
| Threshold | 60% | Configurable (0-100) |
| Max faces/frame | 5 | Rekognition limit |

---

## 🚀 How to Run

### **Start API Server**
```bash
cd aws
python -m uvicorn backend.api.app:app --reload --host 127.0.0.1 --port 8888
```

### **Start GUI**
```bash
python app/gui_app.py
```

### **Verify System**
```bash
# Check API health
curl http://127.0.0.1:8888/api/v1/health

# List enrolled people
curl http://127.0.0.1:8888/api/v1/people

# Check Rekognition faces
python aws/check_faces.py
```

---

## 📁 Project Structure

```
facerecog/
├── app/
│   └── gui_app.py              # PyQt5 GUI application
├── aws/
│   ├── backend/
│   │   ├── api/
│   │   │   └── app.py          # FastAPI application
│   │   ├── core/
│   │   │   ├── enrollment_service.py
│   │   │   ├── identification_service.py
│   │   │   └── database_manager.py
│   │   ├── aws/
│   │   │   ├── s3_client.py
│   │   │   ├── rekognition_client.py
│   │   │   └── dynamodb_client.py
│   │   └── utils/
│   │       ├── config.py
│   │       └── logger.py
│   ├── .env                    # Environment config
│   ├── create_database.py      # Setup script
│   ├── reset_database.py       # Cleanup script
│   └── check_faces.py          # Verification script
└── docs/
    └── ACTUAL_ARCHITECTURE.md  # This file
```

---

## 🎯 Next Steps (If Going to Production)

1. **Deploy to Lambda + API Gateway**
2. **Add Cognito authentication**
3. **Implement Redis caching**
4. **Add CloudWatch monitoring**
5. **Enable X-Ray tracing**
6. **Set up SQS for async processing**
7. **Add SNS notifications**
8. **Enable KMS encryption**
9. **Configure CloudTrail**
10. **Set up CI/CD pipeline**

---

**📝 Note:** Đây là kiến trúc **development/testing**, tối ưu cho local development và demo. Không phù hợp cho production environment.
