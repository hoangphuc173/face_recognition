# Hướng Dẫn Phát Triển Local

Hướng dẫn thiết lập và chạy dự án Face Recognition trên môi trường local.

---

## Điều Kiện Tiên Quyết

- **Python 3.11+**
- **Node.js 18+**
- **AWS CLI** (đã cấu hình với quyền Admin)
- **Git**

---

## Bước 1: Thiết Lập Môi Trường

### 1. Clone Repository

```bash
git clone https://github.com/hoangphuc173/face_recognition.git
cd face_recognition
```

### 2. Cài Đặt Backend Dependencies

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Cài Đặt Frontend Dependencies

```bash
cd frontend/web
npm install
```

---

## Bước 2: Cấu Hình Biến Môi Trường

### Backend (.env)

Tạo file `backend/.env`:

```bash
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1
DYNAMODB_TABLE=face-recognition-users
S3_BUCKET=face-recognition-images-prod
REKOGNITION_COLLECTION=face-recognition-collection
COGNITO_USER_POOL_ID=us-east-1_xxxxxx
COGNITO_CLIENT_ID=xxxxxx
```

### Frontend (.env.local)

Tạo file `frontend/web/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Bước 3: Chạy Ứng Dụng Local

### Lựa Chọn A: Chạy Toàn Bộ Hệ Thống (Khuyến Nghị)

Sử dụng script tự động:

```bash
# Windows
scripts\local\start-full-local-system.bat
```

Script này sẽ:
1. Khởi động Backend server (FastAPI) tại `http://localhost:8000`
2. Khởi động Frontend server (Next.js) tại `http://localhost:3000`

### Lựa Chọn B: Chạy Thủ Công

**Terminal 1 (Backend)**:
```bash
cd backend
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

**Terminal 2 (Frontend)**:
```bash
cd frontend/web
npm run dev
```

---

## Quy Trình Phát Triển

### Backend Development

1. Sửa đổi code trong `backend/src/`
2. Server tự động reload
3. Test API tại `http://localhost:8000/docs` (Swagger UI)

### Frontend Development

1. Sửa đổi code trong `frontend/web/src/`
2. Browser tự động reload
3. Xem kết quả tại `http://localhost:3000`

---

## Kiểm Thử Local

### Chạy Unit Tests

```bash
cd backend
pytest
```

### Kiểm Tra Linting

```bash
# Backend
flake8 .

# Frontend
npm run lint
```

---

## Xử Lý Sự Cố Local

### Lỗi "Module not found"

Đảm bảo virtual environment đã được kích hoạt:
```bash
# Windows
venv\Scripts\activate
```

### Lỗi kết nối AWS

Đảm bảo AWS credentials chính xác trong `.env` hoặc `~/.aws/credentials`.

### Frontend không gọi được API

Kiểm tra biến `NEXT_PUBLIC_API_URL` trong `.env.local` có trỏ đúng `http://localhost:8000` không.
