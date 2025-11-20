# 🚀 HƯỚNG DẪN CHẠY HỆ THỐNG

**Ngày:** 20/11/2024  
**Trạng thái:** ✅ HỆ THỐNG ĐANG CHẠY

---

## ✅ BACKEND API SERVER (ĐANG CHẠY)

### 📊 Thông Tin Server

```
🟢 Status: RUNNING
📍 URL: http://127.0.0.1:5555
🔧 Mode: Development (Auto-reload enabled)
📦 Version: 2.0.0
```

### 🌐 Endpoints Chính

| Endpoint | URL | Mô Tả |
|----------|-----|-------|
| **API Docs** | http://127.0.0.1:5555/docs | Interactive API documentation (Swagger) |
| **ReDoc** | http://127.0.0.1:5555/redoc | Alternative API documentation |
| **Health Check** | http://127.0.0.1:5555/health | Kiểm tra trạng thái server |
| **Readiness** | http://127.0.0.1:5555/ready | Kiểm tra database connectivity |
| **Metrics** | http://127.0.0.1:5555/metrics | Prometheus metrics |

### 📡 API Endpoints

#### Face Enrollment
```http
POST http://127.0.0.1:5555/api/v1/enroll
Content-Type: multipart/form-data

# Form data:
- image: file (JPG, PNG)
- user_name: string (required)
- gender: string (optional)
- birth_year: string (optional)
- hometown: string (optional)
- residence: string (optional)
```

#### Face Identification
```http
POST http://127.0.0.1:5555/api/v1/identify
Content-Type: multipart/form-data

# Form data:
- image: file (JPG, PNG)
- threshold: float (0-100, default: 90.0)
```

#### People Management
```http
GET  http://127.0.0.1:5555/api/v1/people         # List all people
GET  http://127.0.0.1:5555/api/v1/people/{id}    # Get person details
DELETE http://127.0.0.1:5555/api/v1/people/{id}  # Delete person
```

#### Authentication
```http
POST http://127.0.0.1:5555/api/v1/auth/token     # Get JWT token
POST http://127.0.0.1:5555/api/v1/auth/register  # Register new user
```

#### System
```http
GET http://127.0.0.1:5555/api/v1/telemetry      # System metrics (CPU, memory, disk)
```

---

## 🎨 FRONTEND (React + Tauri)

### Cách 1: Chạy Web Development Server

```powershell
# Từ terminal mới:
cd face-recognition-app
npm install          # Nếu chưa install
npm run dev
```

**URL:** http://localhost:5173

### Cách 2: Chạy Tauri Desktop App

```powershell
cd face-recognition-app
npm run tauri dev
```

### Features Frontend:
- ✅ Login/Authentication
- ✅ Camera capture
- ✅ Face enrollment
- ✅ Face identification
- ✅ People management
- ✅ Real-time recognition

---

## 🧪 TESTING API

### Sử dụng curl (PowerShell)

#### 1. Health Check
```powershell
curl http://127.0.0.1:5555/health
```

#### 2. Upload và Enroll Face
```powershell
$boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
$headers = @{
    "Content-Type" = "multipart/form-data; boundary=$boundary"
}

curl -X POST http://127.0.0.1:5555/api/v1/enroll `
  -F "image=@path/to/your/image.jpg" `
  -F "user_name=John Doe" `
  -F "gender=Male" `
  -F "birth_year=1990"
```

#### 3. Identify Face
```powershell
curl -X POST http://127.0.0.1:5555/api/v1/identify `
  -F "image=@path/to/test/image.jpg" `
  -F "threshold=90.0"
```

#### 4. List People
```powershell
curl http://127.0.0.1:5555/api/v1/people
```

### Sử dụng Swagger UI

Mở browser và truy cập: **http://127.0.0.1:5555/docs**

Tại đây bạn có thể:
- ✅ Xem tất cả API endpoints
- ✅ Test trực tiếp trên browser
- ✅ Xem request/response schemas
- ✅ Thử nghiệm với dữ liệu mẫu

---

## 📊 MONITORING

### System Metrics
```powershell
curl http://127.0.0.1:5555/api/v1/telemetry
```

**Response:**
```json
{
  "cpu_usage": 15.5,
  "memory_usage": 45.8,
  "disk_usage": 75.2
}
```

### Prometheus Metrics
```powershell
curl http://127.0.0.1:5555/metrics
```

---

## 🛠️ TROUBLESHOOTING

### Backend không start được?

**Kiểm tra port:**
```powershell
netstat -ano | findstr :5555
```

**Chạy lại server:**
```powershell
# Từ terminal mới:
cd aws
python -m uvicorn backend.api.app:app --host 127.0.0.1 --port 5555 --reload
```

### Frontend không kết nối được backend?

1. Kiểm tra backend đang chạy: http://127.0.0.1:5555/health
2. Kiểm tra CORS settings trong `.env`
3. Kiểm tra API URL trong frontend config

### AWS Features không hoạt động?

Backend đang chạy ở **Development Mode** - AWS features sẽ bị disabled nếu không có credentials.

**Để enable AWS:**
1. Tạo file `.env` trong root directory
2. Điền AWS credentials và resource names:
```env
AWS_REGION=ap-southeast-1
AWS_S3_BUCKET=your-bucket-name
AWS_REKOGNITION_COLLECTION=your-collection-name
AWS_DYNAMODB_PEOPLE_TABLE=your-table-name
# ... more AWS settings
```
3. Restart server

---

## 🔌 STOP SERVER

### Stop Backend
```powershell
# Press CTRL+C in the terminal running uvicorn
```

### Stop Frontend
```powershell
# Press CTRL+C in the terminal running npm/tauri
```

### Force Kill (if needed)
```powershell
# Find and kill process on port 5555
$process = Get-NetTCPConnection -LocalPort 5555 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($process) { Stop-Process -Id $process -Force }
```

---

## 📝 NOTES

### Current Status:
- ✅ Backend API: **RUNNING** on port 5555
- ✅ All fixes applied and verified
- ✅ No linter errors
- ✅ Dependencies installed
- ⚠️ AWS features: **DISABLED** (no credentials configured)
- ⚠️ Redis cache: **DISABLED** (not running locally)

### Features Available:
- ✅ API Documentation (Swagger/ReDoc)
- ✅ Health checks
- ✅ Metrics collection
- ✅ Authentication (local)
- ⚠️ Face enrollment (requires AWS Rekognition)
- ⚠️ Face identification (requires AWS Rekognition)
- ⚠️ Database operations (requires AWS DynamoDB)

### For Full Functionality:
Configure AWS services or use mock data for local development.

---

## 🎯 NEXT STEPS

1. ✅ **Backend đang chạy** - Test API với Swagger UI
2. 🚀 **Chạy Frontend** - `cd face-recognition-app && npm run dev`
3. 🔧 **Configure AWS** (optional) - Để enable full features
4. 🧪 **Run Tests** - `python -m pytest tests/`
5. 📊 **Monitor** - Check metrics và logs

---

**HỆ THỐNG SẴN SÀNG!** 🎉

Truy cập **http://127.0.0.1:5555/docs** để bắt đầu test API!

