# 🚀 KHỞI ĐỘNG ỨNG DỤNG UI - HƯỚNG DẪN NHANH

**Cập nhật:** 20/11/2024  
**Trạng thái Backend:** ✅ ĐANG CHẠY (Port 5555)  
**Trạng thái Frontend:** ⏳ CẦN KHỞI ĐỘNG

---

## ⚡ CÁCH NHANH NHẤT - CHẠY NGAY!

### **Bước 1: Mở PowerShell hoặc Command Prompt MỚI**

### **Bước 2: Chọn 1 trong 3 cách:**

#### 🎯 **Cách 1: Dùng Batch File (KHUYẾN NGHỊ)**
```cmd
start-frontend.bat
```
Hoặc double-click file `start-frontend.bat`

#### 🎯 **Cách 2: Dùng PowerShell Script**
```powershell
.\start-frontend.ps1
```

#### 🎯 **Cách 3: Manual (Luôn hoạt động)**
```cmd
cd face-recognition-app
npm run dev
```

### **Bước 3: Đợi và Mở Browser**

Sau khoảng **10-15 giây**, bạn sẽ thấy message:

```
  ➜  Local:   http://localhost:5173/
  ➜  ready in 1234 ms
```

### **Bước 4: MỞ BROWSER**

👉 **http://localhost:5173** 👈

Browser sẽ tự động mở, hoặc copy link vào browser!

---

## 🔐 ĐĂNG NHẬP

```
Username: admin
Password: admin123
```

Hoặc click **"Register"** để tạo tài khoản mới!

---

## 🎨 GIAO DIỆN ỨNG DỤNG

### 📸 **Camera Tab**
- **Enroll Face:** Đăng ký khuôn mặt mới
  - Nhập thông tin (tên, giới tính, năm sinh...)
  - Chụp từ webcam hoặc upload ảnh
  - Click "Enroll"
  
- **Identify Face:** Nhận dạng khuôn mặt
  - Chụp từ webcam hoặc upload ảnh
  - Click "Identify"
  - Xem kết quả matching

### 👥 **People Tab**
- Xem danh sách người đã đăng ký
- Chi tiết từng người
- Xóa người khỏi hệ thống

---

## 🔧 KHI FRONTEND CHẠY

Bạn sẽ thấy trong terminal:

```
  VITE v7.2.2  ready in 1234 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

Lúc này **MỞ BROWSER** đến: **http://localhost:5173**

---

## 🎯 KIỂM TRA HỆ THỐNG

### ✅ Backend Running?
```powershell
curl http://127.0.0.1:5555/health
```

### ✅ Frontend Running?
```powershell
curl http://localhost:5173
```

### ✅ Xem Port Nào Đang Chạy
```powershell
netstat -ano | findstr "5555 5173"
```

**Expected:**
```
TCP    127.0.0.1:5555    ← Backend
TCP    127.0.0.1:5173    ← Frontend
```

---

## 🐛 NẾU CÓ VẤN ĐỀ

### ❌ Port 5173 đã được sử dụng?
```cmd
# Tìm process đang dùng port 5173
netstat -ano | findstr :5173

# Kill process (thay PID bằng số process ID)
taskkill /F /PID <PID>

# Sau đó chạy lại npm run dev
```

### ❌ npm run dev báo lỗi?
```cmd
cd face-recognition-app

# Xóa node_modules và cài lại
rmdir /s /q node_modules
del package-lock.json
npm install

# Chạy lại
npm run dev
```

### ❌ Backend không chạy?
```cmd
# Terminal mới
cd aws
python -m uvicorn backend.api.app:app --host 127.0.0.1 --port 5555 --reload
```

---

## 📊 CẢ 2 SERVICE PHẢI CHẠY

```
┌─────────────────────────────────────────────┐
│  🟢 Backend:    http://127.0.0.1:5555      │
│     └─ API Docs: /docs                      │
│                                             │
│  🟢 Frontend:   http://localhost:5173      │
│     └─ React UI với Webcam                 │
└─────────────────────────────────────────────┘
```

---

## 🎬 VIDEO HƯỚNG DẪN SỬ DỤNG

### 1️⃣ **Đăng Ký Khuôn Mặt (Enrollment)**

```
1. Login vào ứng dụng
2. Vào tab "Camera"
3. Điền form:
   - User Name: Tên của bạn
   - Gender: Nam/Nữ
   - Birth Year: Năm sinh
   - Hometown: Quê quán
   - Residence: Nơi ở hiện tại
4. Click "Capture from Camera" hoặc "Upload Image"
5. Chụp ảnh rõ mặt
6. Click "Enroll Face"
7. Đợi kết quả!
```

### 2️⃣ **Nhận Dạng Khuôn Mặt (Identification)**

```
1. Vào tab "Camera"
2. Click "Capture from Camera" hoặc "Upload Image"
3. Chụp/Upload ảnh cần nhận dạng
4. Click "Identify Face"
5. Xem kết quả: Tên + độ tin cậy (%)
```

### 3️⃣ **Quản Lý Người (People Management)**

```
1. Vào tab "People"
2. Xem danh sách tất cả người đã đăng ký
3. Click vào từng người để xem chi tiết
4. Click "Delete" để xóa người
```

---

## ⚠️ LƯU Ý QUAN TRỌNG

### **Hiện Tại:**
- ✅ UI chạy được 100%
- ✅ Backend API đang chạy
- ⚠️ **AWS Features bị disabled** (chưa config AWS)

### **Ảnh Hưởng:**
- ✅ Bạn có thể thấy UI, login, điều hướng
- ❌ Face Enrollment sẽ báo lỗi "AWS not configured"
- ❌ Face Identification sẽ báo lỗi "AWS not configured"
- ✅ People list sẽ trả về rỗng (empty array)

### **Để Enable Full Features:**
Cần configure AWS trong file `.env`:
```env
AWS_REGION=ap-southeast-1
AWS_S3_BUCKET=your-bucket-name
AWS_REKOGNITION_COLLECTION=your-collection-id
AWS_DYNAMODB_PEOPLE_TABLE=your-table-name
# ... etc
```

Sau đó restart backend.

---

## 🎉 THÀNH CÔNG!

Khi cả backend VÀ frontend đều chạy:

```
✅ Backend: http://127.0.0.1:5555 ← API Server
✅ Frontend: http://localhost:5173 ← UI Application
```

**MỞ BROWSER VÀ TRẢI NGHIỆM!** 🚀

---

## 🆘 CẦN HELP?

1. Check backend: `curl http://127.0.0.1:5555/health`
2. Check frontend: `curl http://localhost:5173`
3. Xem logs trong terminal
4. Restart cả 2 services nếu cần

---

**Ready to Go!** 🎨✨

**HƯỚNG DẪN:** Chỉ cần chạy `start-frontend.bat` và đợi browser tự mở!

