# 🔍 Hệ Thống Nhận Diện Khuôn Mặt

Hệ thống nhận diện khuôn mặt tiên tiến với giao diện đồ họa, hỗ trợ quản lý thông tin cá nhân đầy đủ, đăng ký bằng ảnh/video, và nhận diện thời gian thực.

## ✨ Tính năng chính

### 📸 Đăng ký khuôn mặt
- **Đăng ký từ file**: Hỗ trợ ảnh (.jpg, .png) và video (.mp4, .avi)
- **Đăng ký từ webcam**: 
  - 📸 Chụp ảnh nhanh
  - 🎥 Ghi video (lưu toàn bộ frame, không giới hạn)
- **Phát hiện trùng lặp**: Tự động so sánh với database, hiển thị 3 lựa chọn:
  - 💾 Lưu vào người đã có
  - 🚫 Không lưu
  - ➕ Đăng ký người mới

### � Quản lý thông tin cá nhân
- **Thông tin đầy đủ**: Tên, Giới tính, Năm sinh, Quê quán, Nơi sinh sống
- **Quản lý database**: Xem danh sách, chỉnh sửa, xóa thông tin
- **Tự động làm mới**: Cập nhật liên tục mỗi 2 giây
- **Mở thư mục**: Truy cập trực tiếp vào ảnh/video của từng người

### 🎯 Nhận diện khuôn mặt
- **Nhận diện từ file**: Xử lý ảnh và video
- **Nhận diện webcam**: Thời gian thực với hiển thị thông tin chi tiết
- **Ghi lại video**: Lưu video nhận diện với đầy đủ frame
- **Hiển thị thông tin**: 
  - Ảnh: 5 dòng với emoji (👤 Name, ⚧ Gender, 🎂 Birth Year, 🏠 Hometown, 📍 Residence)
  - Webcam: 5 dòng viết tắt (Name, GT:, NS:, QQ:, O:)

### 🗂️ Tổ chức file
- **Tự động sắp xếp**: Phân loại ảnh theo người được nhận diện
- **Báo cáo chi tiết**: Thống kê số lượng ảnh cho mỗi người

## 📋 Yêu cầu hệ thống

### Phần mềm
- **Python**: 3.9 trở lên
- **Hệ điều hành**: Windows, macOS, Linux
- **Webcam**: (Tùy chọn) cho tính năng đăng ký/nhận diện từ camera

### Thư viện Python
Xem file `requirements.txt` để biết chi tiết đầy đủ.

## 🚀 Cài đặt

### 1. Clone hoặc tải về repository

```bash
git clone <repository-url>
cd facerecog
```

### 2. Tạo môi trường ảo (khuyến nghị)

```bash
python -m venv .venv
```

### 3. Kích hoạt môi trường ảo

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
.venv\Scripts\activate.bat
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### 4. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

**Lưu ý quan trọng cho Windows:**
- `face-recognition` yêu cầu `dlib` và `cmake`
- Nếu gặp lỗi, cài đặt pre-built wheel từ: https://github.com/ageitgey/face_recognition#installation

## 🎮 Sử dụng

### Khởi chạy ứng dụng

```bash
python launcher.py
```

Hoặc chạy trực tiếp GUI:

```bash
python gui_app.py
```

### Menu chính

Sau khi khởi chạy, bạn sẽ thấy menu với các tùy chọn:

1. **🎨 Giao diện GUI** - Khởi chạy giao diện đồ họa (khuyến nghị)
2. **⌨️ Quản lý Database (CLI)** - Quản lý database qua dòng lệnh
3. **❌ Thoát** - Đóng chương trình

## 📖 Hướng dẫn chi tiết

### 1. Đăng ký khuôn mặt mới

#### Từ file ảnh/video:
1. Nhấn nút **"📝 Đăng ký khuôn mặt"**
2. Chọn file ảnh hoặc video
3. Hệ thống tự động phát hiện khuôn mặt
4. Nếu phát hiện trùng lặp:
   - **💾 Lưu**: Thêm ảnh vào người đã có
   - **🚫 Không lưu**: Bỏ qua ảnh này
   - **➕ Đăng ký mới**: Đăng ký như người mới
5. Nhập thông tin cá nhân (tên, giới tính, năm sinh, quê quán, nơi sinh sống)
6. Nhấn **"Lưu"** để hoàn tất

#### Từ webcam:
1. Nhấn nút **"📷 Đăng ký từ Webcam"**
2. Chọn phương thức:
   - **📸 Chụp ảnh**: Chụp ảnh tức thì
   - **🎥 Ghi video**: Bắt đầu ghi, nhấn lại để dừng
3. Xác nhận hoặc chọn lại nếu cần
4. Nếu phát hiện trùng lặp, chọn 1 trong 3 tùy chọn
5. Nhập thông tin cá nhân
6. Lưu để hoàn tất

### 2. Nhận diện khuôn mặt

#### Từ file:
1. Nhấn nút **"🔍 Nhận diện từ File"**
2. Chọn file ảnh hoặc video
3. Hệ thống sẽ xử lý và hiển thị kết quả với:
   - Khung bao quanh khuôn mặt
   - Thông tin cá nhân đầy đủ (5 dòng)
   - Độ tin cậy (%)

#### Từ webcam:
1. Nhấn nút **"📹 Nhận diện Webcam"**
2. Webcam sẽ bật lên và nhận diện thời gian thực
3. Tùy chọn:
   - **🎥 Ghi video**: Bắt đầu/dừng ghi lại video
   - **❌ Đóng**: Tắt webcam
4. Nhấn **Q** trên cửa sổ video để thoát nhanh

### 3. Quản lý database

1. Nhấn nút **"👥 Quản lý Khuôn mặt"**
2. Danh sách tự động làm mới mỗi 2 giây
3. Các thao tác:
   - **👁️ Xem ảnh**: Mở thư mục chứa ảnh/video của người được chọn
   - **✏️ Sửa**: Chỉnh sửa thông tin cá nhân
   - **🗑️ Xóa**: Xóa người khỏi database (xác nhận trước khi xóa)

### 4. Tổ chức ảnh

1. Nhấn nút **"📁 Tổ chức Ảnh"**
2. Chọn thư mục chứa ảnh cần phân loại
3. Hệ thống sẽ:
   - Quét tất cả ảnh trong thư mục
   - Nhận diện khuôn mặt
   - Sao chép ảnh vào thư mục tương ứng của mỗi người
4. Hiển thị báo cáo thống kê

## 📁 Cấu trúc thư mục

```
facerecog/
├── .venv/                      # Môi trường ảo Python
├── faces/                      # Ảnh và video gốc của mỗi người
│   ├── {person_1}/
│   │   ├── 00000.jpg
│   │   ├── 00001.mp4
│   │   └── ...
│   └── {person_2}/
│       └── ...
├── face_database/              # Database V2 (folder-based)
│   ├── {person_1}/
│   │   ├── info.json          # Thông tin cá nhân
│   │   └── embeddings.npy     # Face embeddings
│   └── {person_2}/
│       └── ...
├── recognized/                 # Video đã nhận diện (output)
│   ├── recognition_20240101_120000.mp4
│   └── ...
├── temp/                       # Thư mục tạm (tự động xóa)
├── gui_app.py                  # Giao diện GUI chính (2178 dòng)
├── launcher.py                 # Menu khởi chạy
├── database_manager.py         # Quản lý database V2
├── enrollment_service_v2.py    # Service đăng ký khuôn mặt
├── identification_service_v2.py # Service nhận diện
├── manage_database.py          # CLI quản lý database
├── requirements.txt            # Danh sách dependencies
├── .gitignore                  # Git ignore patterns
└── README.md                   # File này
```

## 🗄️ Cấu trúc Database V2

### Folder-based Architecture
Mỗi người được lưu trong 1 folder riêng với 2 file:

**1. info.json** - Thông tin cá nhân:
```json
{
  "folder_name": "nguyen_van_a",
  "user_name": "Nguyễn Văn A",
  "gender": "Nam",
  "birth_year": "1990",
  "hometown": "Hà Nội",
  "residence": "TP. Hồ Chí Minh",
  "created_at": "2024-01-01 10:00:00",
  "updated_at": "2024-01-01 10:00:00",
  "embedding_count": 5
}
```

**2. embeddings.npy** - Face embeddings (numpy array kích thước N×128)

### Auto-numbering
Nếu trùng tên, hệ thống tự động đánh số:
- nguyen_van_a
- nguyen_van_a_1
- nguyen_van_a_2
- ...

## ⚙️ Cấu hình

### Thay đổi ngưỡng nhận diện
Mở `identification_service_v2.py`, tìm dòng:
```python
CONFIDENCE_THRESHOLD = 0.6  # Mặc định 60%
```
- Giá trị cao hơn (0.7-0.8): Chính xác hơn, ít nhận diện sai
- Giá trị thấp hơn (0.4-0.5): Nhạy hơn, dễ nhận diện nhưng có thể sai

### Thay đổi FPS video
Mở `gui_app.py`, tìm:
```python
fps = 20  # Frames per second
```

## 🐛 Xử lý lỗi thường gặp

### Lỗi cài đặt dlib (Windows)
**Triệu chứng**: `error: Microsoft Visual C++ 14.0 is required`

**Giải pháp**:
1. Tải pre-built wheel từ: https://github.com/ageitgey/dlib-models
2. Hoặc cài Visual Studio Build Tools

### Webcam không hoạt động
**Triệu chứng**: Màn hình đen hoặc lỗi "Cannot open camera"

**Giải pháp**:
1. Kiểm tra webcam có hoạt động không (thử app Camera của Windows)
2. Đóng các ứng dụng khác đang dùng webcam (Zoom, Teams, etc.)
3. Thử thay đổi camera index trong code

### Unicode/Emoji không hiển thị
**Triệu chứng**: Ký tự lạ thay vì emoji

**Giải pháp**: Hệ thống đã dùng PIL/Pillow, nên emoji sẽ hiển thị đúng. Nếu vẫn lỗi, kiểm tra font chữ.

### Database bị lỗi
**Triệu chứng**: Không load được thông tin

**Giải pháp**:
```bash
python manage_database.py
# Chọn option "Xem tất cả" để kiểm tra
```

## � VS Code Extensions (đã cài đặt)

### Python Development
- **Python** - ms-python.python
- **Pylance** - ms-python.vscode-pylance  
- **Black Formatter** - ms-python.black-formatter

### Git Management
- **GitLens** - eamodio.gitlens
- **Git Graph** - mhutchie.git-graph
- **Git History** - donjayamanne.githistory

### UI/UX
- **Material Icon Theme** - PKief.material-icon-theme

## � Tính năng nổi bật

### 1. Video Recording không giới hạn
- Lưu **toàn bộ frame** từ lúc bắt đầu đến khi kết thúc
- Không sampling, không giới hạn 10 frame
- FPS cao (20 fps) cho video mượt mà

### 2. 3-Option Dialog thông minh
- Phát hiện khuôn mặt trùng lặp tự động
- Cho phép lựa chọn linh hoạt: Lưu/Không lưu/Đăng ký mới
- Áp dụng cho cả ảnh và video

### 3. Auto-refresh Management
- Danh sách cập nhật liên tục mỗi 2 giây
- Giữ nguyên lựa chọn hiện tại
- Không cần nhấn F5

### 4. Direct Folder Access
- Mở thư mục Windows Explorer trực tiếp
- Xem/xóa/chỉnh sửa file dễ dàng
- Hỗ trợ cả ảnh và video

### 5. Unicode/Emoji Support
- Hiển thị emoji đẹp mắt (👤⚧🎂🏠📍)
- Hỗ trợ tiếng Việt hoàn hảo
- Dùng PIL thay vì cv2.putText

## 💡 Tips & Tricks

### Để có kết quả nhận diện tốt nhất:
1. **Đăng ký nhiều góc độ**: Chụp/ghi video từ nhiều góc nhìn khác nhau
2. **Ánh sáng tốt**: Tránh ngược sáng, tối quá hoặc quá sáng
3. **Khuôn mặt rõ ràng**: Không đeo khẩu trang, kính râm
4. **Nhiều biểu cảm**: Cười, nghiêm túc, nhìn sang bên...

### Tổ chức database hiệu quả:
1. Đặt tên rõ ràng, không trùng lặp
2. Định kỳ xóa ảnh mờ, chất lượng kém
3. Cập nhật ảnh mới khi thay đổi ngoại hình nhiều

### Tối ưu hiệu năng:
1. Đóng các ứng dụng không cần thiết khi chạy webcam
2. Giảm FPS nếu máy yếu
3. Xử lý video nhỏ hơn thay vì video 4K

## 📞 Hỗ trợ & Đóng góp

### Báo lỗi
Mở issue trên GitHub với thông tin:
- Hệ điều hành và phiên bản Python
- Mô tả lỗi chi tiết
- Cách tái hiện lỗi
- Log/screenshot (nếu có)

### Đóng góp code
1. Fork repository
2. Tạo branch mới: `git checkout -b feature/ten-tinh-nang`
3. Commit changes: `git commit -m 'Thêm tính năng X'`
4. Push to branch: `git push origin feature/ten-tinh-nang`
5. Tạo Pull Request

## 📜 License

MIT License - Xem file LICENSE để biết thêm chi tiết.

## � Credits

### Thư viện sử dụng:
- **face_recognition** - Adam Geitgey
- **OpenCV** - Open Source Computer Vision Library
- **Pillow** - Python Imaging Library
- **NumPy** - Numerical Python

### Fonts:
- Arial Unicode MS (Windows)

---

**Phát triển bởi**: [Tên của bạn]  
**Phiên bản**: 2.0 (Database V2 - Folder-based Architecture)  
**Cập nhật**: 2024
