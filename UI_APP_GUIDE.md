# 🎨 HƯỚNG DẪN CHẠY ỨNG DỤNG UI

**Ngày:** 20/11/2024  
**Trạng thái:** 🚀 ĐANG KHỞI ĐỘNG

---

## 🖥️ HỆ THỐNG ĐANG CHẠY

### ✅ Backend API Server
```
Status:   🟢 RUNNING
URL:      http://127.0.0.1:5555
API Docs: http://127.0.0.1:5555/docs
```

### 🎨 Frontend UI Application
```
Status:   🟡 STARTING...
URL:      http://localhost:5173
Type:     React + Vite + Face-API.js
```

---

## 🌐 MỞ ỨNG DỤNG

Sau khi frontend khởi động xong (khoảng 10-15 giây), hãy:

### **MỞ BROWSER VÀ TRUY CẬP:**

# 👉 **http://localhost:5173** 👈

Hoặc:
- Chrome: `start chrome http://localhost:5173`
- Edge: `start msedge http://localhost:5173`
- Firefox: `start firefox http://localhost:5173`

---

## 🎯 TÍNH NĂNG ỨNG DỤNG UI

### 🔐 **1. Login Page**
- Username: `admin`
- Password: `admin123`
- Hoặc đăng ký tài khoản mới

### 📸 **2. Camera Page**
- **Enroll Face:** Chụp ảnh và đăng ký khuôn mặt mới
  - Nhập tên, giới tính, năm sinh, quê quán
  - Chụp ảnh từ webcam
  - Upload ảnh từ file
  
- **Identify Face:** Nhận dạng khuôn mặt
  - Chụp ảnh từ webcam
  - Upload ảnh từ file
  - Xem kết quả match với độ tin cậy

### 👥 **3. People Management**
- Xem danh sách người đã đăng ký
- Xem chi tiết thông tin từng người
- Xóa người khỏi hệ thống
- Thống kê số lượng

---

## 🔧 NẾU FRONTEND KHÔNG TỰ MỞ

### Cách 1: Chạy thủ công
```powershell
cd face-recognition-app
npm run dev
```

### Cách 2: Mở terminal mới
1. Mở PowerShell mới
2. Chạy:
```powershell
cd C:\Users\ADMIN\Downloads\facerecog\face-recognition-app
npm run dev
```

### Cách 3: Kiểm tra port
```powershell
# Xem port 5173 có đang chạy không
netstat -ano | findstr :5173
```

---

## 📱 DESKTOP APP (TÙY CHỌN)

Nếu muốn chạy dưới dạng Desktop App thay vì web:

```powershell
cd face-recognition-app
npm run tauri dev
```

---

## 🎥 SỬ DỤNG WEBCAM

### Cho phép truy cập webcam:
1. Browser sẽ hỏi quyền truy cập camera
2. Click **"Allow"** / **"Cho phép"**
3. Nếu bị từ chối, vào Settings → Privacy → Camera

### Kiểm tra webcam:
- Windows Camera app: `start microsoft.windows.camera:`
- Hoặc Settings → Camera

---

## 🐛 TROUBLESHOOTING

### Frontend không start?

**1. Kiểm tra port:**
```powershell
netstat -ano | findstr :5173
```

**2. Xóa cache và reinstall:**
```powershell
cd face-recognition-app
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
npm run dev
```

**3. Kiểm tra log trong terminal**

### Không kết nối được Backend?

**Kiểm tra backend:**
```powershell
curl http://127.0.0.1:5555/health
```

**Nếu backend chết, restart:**
```powershell
cd aws
python -m uvicorn backend.api.app:app --host 127.0.0.1 --port 5555 --reload
```

### Webcam không hoạt động?

1. Check browser permissions
2. Check Windows Camera settings
3. Try different browser (Chrome recommended)
4. Reload page (Ctrl+F5)

---

## 🎬 WORKFLOW SỬ DỤNG

### Bước 1: Login
```
1. Mở http://localhost:5173
2. Login với admin/admin123
3. Hoặc đăng ký tài khoản mới
```

### Bước 2: Đăng Ký Khuôn Mặt (Enroll)
```
1. Click tab "Camera"
2. Nhập thông tin: Tên, giới tính, năm sinh, etc.
3. Chọn cách chụp:
   - Webcam: Click "Capture from Camera"
   - File: Click "Upload Image"
4. Click "Enroll Face"
5. Đợi kết quả
```

### Bước 3: Nhận Dạng (Identify)
```
1. Ở tab "Camera"
2. Chụp ảnh hoặc upload ảnh
3. Click "Identify Face"
4. Xem kết quả matching
```

### Bước 4: Quản Lý (People)
```
1. Click tab "People"
2. Xem danh sách người đã đăng ký
3. Click vào từng người để xem chi tiết
4. Xóa người nếu cần
```

---

## ⚠️ LƯU Ý QUAN TRỌNG

### AWS Configuration
Hiện tại hệ thống đang chạy **Development Mode** mà không có AWS credentials:

- ✅ UI có thể chạy và hiển thị
- ⚠️ Face enrollment sẽ báo lỗi (cần AWS Rekognition)
- ⚠️ Face identification sẽ báo lỗi (cần AWS Rekognition)
- ✅ People list sẽ trả về rỗng

### Để Enable Full Features:
1. Tạo file `.env` với AWS credentials
2. Configure AWS Rekognition collection
3. Configure DynamoDB tables
4. Configure S3 bucket
5. Restart backend

---

## 📊 SYSTEM STATUS

```
┌─────────────────────────────────────────────┐
│  🟢 Backend:    http://127.0.0.1:5555      │
│  🟡 Frontend:   http://localhost:5173      │
│  📸 Webcam:     Ready                       │
│  🔐 Auth:       Local JWT                   │
│  ⚠️  AWS:        Not Configured             │
└─────────────────────────────────────────────┘
```

---

## 🎉 ENJOY!

**Sau khi frontend khởi động:**

👉 **MỞ:** http://localhost:5173

👉 **LOGIN:** admin / admin123

👉 **BẮT ĐẦU SỬ DỤNG!**

---

**Happy Coding!** 🚀✨

