# 🖥️ HƯỚNG DẪN CHẠY DESKTOP GUI APP

**Cập nhật:** 20/11/2024  
**Loại App:** Python Desktop Application (PyQt5)

---

## 🎯 **CÓ 2 LOẠI DESKTOP APP**

### **Option 1: Python Desktop App (PyQt5)** ⭐ STANDALONE
- **Ngôn ngữ:** Pure Python
- **UI Framework:** PyQt5
- **Đặc điểm:** 
  - Standalone desktop application
  - Giao diện native Windows
  - Không cần browser
  - Tích hợp webcam trực tiếp
  - Tự động quét liên tục

### **Option 2: Tauri Desktop App** ⭐⭐ MODERN
- **Ngôn ngữ:** React + Rust
- **UI Framework:** React + Vite
- **Đặc điểm:**
  - Modern web technologies
  - Cross-platform
  - Smaller bundle size
  - Web-based UI trong desktop wrapper

---

## 🚀 **CHẠY PYTHON DESKTOP APP (OPTION 1)**

### **Prerequisites:**
✅ Backend API đang chạy (http://127.0.0.1:5555)  
✅ PyQt5 đã cài đặt (already installed ✅)  
✅ OpenCV đã cài đặt (already installed ✅)

### **Cách 1: Double-Click File** (DỄ NHẤT)

1. Tìm file **`start-desktop-app.bat`** trong thư mục project
2. **Double-click** để chạy
3. Desktop app sẽ mở ra!

### **Cách 2: Command Line**

```cmd
python app\gui_app.py
```

### **Cách 3: PowerShell**

```powershell
python app/gui_app.py
```

---

## 🎨 **TÍNH NĂNG PYTHON DESKTOP APP**

### **📸 Tab Camera/Enrollment:**
- **Live Camera Feed:** Xem camera real-time
- **Continuous Scanning:** Tự động quét và nhận dạng liên tục
- **Enroll Face:**
  - Điền thông tin (Tên, giới tính, năm sinh, quê, nơi ở)
  - Capture từ webcam
  - Upload từ file
  - Automatic face detection
- **Identify Face:**
  - Real-time identification
  - Hiển thị tên + độ tin cậy
  - Bounding box quanh khuôn mặt

### **👥 Tab People Management:**
- **View All People:** Bảng danh sách người đã đăng ký
- **Search:** Tìm kiếm theo tên
- **View Details:** Xem chi tiết từng người
- **Delete:** Xóa người khỏi hệ thống
- **Statistics:** Thống kê số lượng

### **⚙️ Settings:**
- **API Configuration:**
  - Local API URL
  - Timeout settings
  - Retry configuration
- **Camera Settings:**
  - Select camera device
  - Resolution
  - FPS
- **Recognition Settings:**
  - Confidence threshold
  - Detection interval

### **📊 System Monitor:**
- CPU usage
- Memory usage
- API response time
- Recognition statistics

---

## 🖼️ **GIAO DIỆN DESKTOP APP**

```
┌──────────────────────────────────────────────────┐
│  Face Recognition System          [_] [□] [X]   │
├──────────────────────────────────────────────────┤
│ [Camera] [People] [Settings] [About]            │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌─────────────────┐  ┌────────────────────┐   │
│  │                 │  │  Person Info       │   │
│  │  WEBCAM FEED    │  │  Name: _______     │   │
│  │                 │  │  Gender: _____     │   │
│  │   [Live Video]  │  │  Birth: ______     │   │
│  │                 │  │                    │   │
│  └─────────────────┘  │  [Enroll]          │   │
│                       │  [Identify]        │   │
│  Status: Ready        └────────────────────┘   │
│  FPS: 30                                        │
│                                                  │
│  Last Recognition:                               │
│  Name: John Doe (95.5%)                         │
├──────────────────────────────────────────────────┤
│ Status: Connected to API ✓     Camera: Active ✓│
└──────────────────────────────────────────────────┘
```

---

## 🚀 **CHẠY TAURI DESKTOP APP (OPTION 2)**

Nếu bạn muốn chạy React-based desktop app:

```powershell
cd face-recognition-app
npm run tauri dev
```

Hoặc build để có file .exe:

```powershell
npm run tauri build
```

**Lưu ý:** Tauri yêu cầu Rust toolchain (chưa build được .exe)

---

## 🎬 **WORKFLOW SỬ DỤNG PYTHON DESKTOP APP**

### **1. Start Application**
```
Double-click start-desktop-app.bat
↓
Desktop window opens
↓
Camera feed activates
```

### **2. Enroll New Face**
```
1. Tab "Camera/Enrollment"
2. Điền form thông tin
3. Click "Capture from Camera"
4. Webcam chụp ảnh
5. Click "Enroll"
6. Đợi kết quả từ API
```

### **3. Continuous Recognition**
```
1. Tab "Camera"
2. Enable "Continuous Scanning"
3. App tự động quét và nhận dạng
4. Hiển thị tên + confidence real-time
```

### **4. Manage People**
```
1. Tab "People"
2. Xem danh sách
3. Search, view, delete
```

---

## 🔧 **CONFIGURATION**

### **API Settings (trong code):**

File: `app/gui_app.py` (dòng 47-52)

```python
USE_LOCAL_API = True
LOCAL_API_URL = "http://127.0.0.1:5555"  # ✅ Đã update
AWS_API_URL = "https://your-api-gateway-url"
```

### **Camera Settings:**
- Default camera: Camera 0
- Có thể chọn camera khác trong Settings
- Resolution: 640x480 (có thể điều chỉnh)

---

## ⚠️ **LƯU Ý**

### **Backend API PHẢI chạy trước:**
```
✅ Backend: http://127.0.0.1:5555
```

Kiểm tra:
```powershell
curl http://127.0.0.1:5555/health
```

### **Webcam Permission:**
- Windows có thể hỏi quyền truy cập camera
- Cho phép (Allow) để app hoạt động

### **AWS Features:**
- ⚠️ Desktop app sẽ gọi API backend
- ⚠️ API backend cần AWS configured để enrollment/identify hoạt động
- ✅ Nếu chưa có AWS, app vẫn chạy nhưng features bị hạn chế

---

## 🐛 **TROUBLESHOOTING**

### **Desktop app không mở được?**

1. **Kiểm tra Python:**
```cmd
python --version
```

2. **Kiểm tra PyQt5:**
```cmd
python -c "import PyQt5; print('OK')"
```

3. **Reinstall nếu cần:**
```cmd
pip install PyQt5 opencv-python
```

### **Camera không hiển thị?**

1. Check camera permission trong Windows Settings
2. Thử camera khác (Settings → Camera Device)
3. Test với Windows Camera app

### **API connection failed?**

1. Kiểm tra backend đang chạy
2. Check URL trong code (phải là 5555 không phải 8888)
3. Xem logs trong console

---

## 📊 **SO SÁNH 2 OPTIONS**

| Feature | Python Desktop (PyQt5) | Tauri Desktop (React) |
|---------|------------------------|------------------------|
| **Technology** | Python + PyQt5 | React + Rust |
| **Startup** | Fast | Medium |
| **Bundle Size** | ~100MB | ~50MB |
| **UI** | Native widgets | Web-based |
| **Camera** | Direct OpenCV | Browser API |
| **Performance** | Excellent | Very Good |
| **Development** | Python only | JavaScript + Rust |
| **Build** | No build needed | Needs build |
| **Ready to run** | ✅ Yes | ⚠️ Dev mode only |

---

## ✅ **KHUYẾN NGHỊ**

### **Dùng Python Desktop App nếu:**
- ✅ Muốn app standalone ngay lập tức
- ✅ Không cần build
- ✅ Thích native Windows UI
- ✅ Cần tích hợp camera trực tiếp

### **Dùng Tauri App nếu:**
- ✅ Thích modern web UI
- ✅ Muốn cross-platform
- ✅ Đã quen với React
- ✅ Cần smaller bundle

---

## 🎉 **CHẠY NGAY!**

### **Python Desktop App:**

```cmd
python app\gui_app.py
```

Hoặc double-click: **`start-desktop-app.bat`**

### **Tauri Desktop App:**

```cmd
cd face-recognition-app
npm run tauri dev
```

---

## 📸 **DEMO**

Sau khi chạy, bạn sẽ thấy:
- ✅ Desktop window với giao diện đẹp
- ✅ Live webcam feed
- ✅ Form enrollment
- ✅ Recognition results real-time
- ✅ People management table

**Enjoy your Desktop App!** 🖥️✨

---

**Status:**
- ✅ Backend: RUNNING (port 5555)
- ✅ Python Desktop App: READY TO RUN
- ✅ Tauri Desktop App: DEV MODE AVAILABLE

