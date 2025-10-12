"""
Giao diện GUI cho Chương trình Nhận diện Khuôn mặt
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from PIL import Image, ImageTk
import cv2
import face_recognition
import numpy as np
import os
import shutil
from datetime import datetime
import threading

# Import services V2 - Folder-based database
from enrollment_service_v2 import FaceEnrollmentServiceV2
from identification_service_v2 import FaceIdentificationServiceV2
from database_manager import DatabaseManager

class PersonInfoDialog:
    """Dialog để nhập thông tin người mới"""
    def __init__(self, parent):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("📝 Nhập thông tin người mới")
        self.dialog.geometry("450x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Title
        title = tk.Label(
            self.dialog,
            text="📝 THÔNG TIN NGƯỜI MỚI",
            font=("Arial", 14, "bold"),
            bg="#3498db",
            fg="white",
            pady=15
        )
        title.pack(fill=tk.X)
        
        # Form frame
        form_frame = tk.Frame(self.dialog, padx=30, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Họ tên
        tk.Label(form_frame, text="👤 Họ và tên: *", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        self.name_entry = tk.Entry(form_frame, font=("Arial", 11), width=30)
        self.name_entry.grid(row=0, column=1, pady=5, padx=10)
        self.name_entry.focus()
        
        # Giới tính
        tk.Label(form_frame, text="⚥ Giới tính:", font=("Arial", 10)).grid(row=1, column=0, sticky="w", pady=5)
        self.gender_var = tk.StringVar()
        gender_frame = tk.Frame(form_frame)
        gender_frame.grid(row=1, column=1, sticky="w", pady=5, padx=10)
        tk.Radiobutton(gender_frame, text="Nam", variable=self.gender_var, value="Nam", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(gender_frame, text="Nữ", variable=self.gender_var, value="Nữ", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.gender_var.set("Nam")
        
        # Năm sinh
        tk.Label(form_frame, text="🎂 Năm sinh:", font=("Arial", 10)).grid(row=2, column=0, sticky="w", pady=5)
        self.birth_year_entry = tk.Entry(form_frame, font=("Arial", 11), width=30)
        self.birth_year_entry.grid(row=2, column=1, pady=5, padx=10)
        
        # Quê quán
        tk.Label(form_frame, text="🏡 Quê quán:", font=("Arial", 10)).grid(row=3, column=0, sticky="w", pady=5)
        self.hometown_entry = tk.Entry(form_frame, font=("Arial", 11), width=30)
        self.hometown_entry.grid(row=3, column=1, pady=5, padx=10)
        
        # Nơi sinh sống
        tk.Label(form_frame, text="📍 Nơi sinh sống:", font=("Arial", 10)).grid(row=4, column=0, sticky="w", pady=5)
        self.residence_entry = tk.Entry(form_frame, font=("Arial", 11), width=30)
        self.residence_entry.grid(row=4, column=1, pady=5, padx=10)
        
        # Note
        note = tk.Label(
            form_frame,
            text="* Trường bắt buộc\nCác trường khác có thể bỏ trống",
            font=("Arial", 9, "italic"),
            fg="gray",
            justify=tk.LEFT
        )
        note.grid(row=5, column=0, columnspan=2, pady=15, sticky="w")
        
        # Buttons
        btn_frame = tk.Frame(self.dialog)
        btn_frame.pack(pady=10)
        
        tk.Button(
            btn_frame,
            text="✅ Xác nhận",
            font=("Arial", 11, "bold"),
            bg="#2ecc71",
            fg="white",
            width=15,
            command=self.on_submit
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            btn_frame,
            text="❌ Hủy",
            font=("Arial", 11),
            bg="#e74c3c",
            fg="white",
            width=15,
            command=self.on_cancel
        ).pack(side=tk.LEFT, padx=10)
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.on_submit())
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
    def on_submit(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Thiếu thông tin", "⚠️ Vui lòng nhập họ tên!", parent=self.dialog)
            self.name_entry.focus()
            return
        
        self.result = {
            "name": name,
            "gender": self.gender_var.get(),
            "birth_year": self.birth_year_entry.get().strip(),
            "hometown": self.hometown_entry.get().strip(),
            "residence": self.residence_entry.get().strip()
        }
        self.dialog.destroy()
        
    def on_cancel(self):
        self.result = None
        self.dialog.destroy()
        
    def show(self):
        """Hiển thị dialog và trả về kết quả"""
        self.dialog.wait_window()
        return self.result

class FaceRecognitionGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔍 Hệ Thống Nhận Diện Khuôn Mặt")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f0f0")
        
        # Khởi tạo services V2 - Folder-based
        self.enrollment_service = FaceEnrollmentServiceV2()
        self.identification_service = FaceIdentificationServiceV2()
        self.db = DatabaseManager()
        
        # Biến lưu trữ
        self.known_face_encodings = []
        self.known_face_names = []
        self.face_metadata = {}  # Lưu metadata đầy đủ của mỗi người
        self.video_capture = None
        self.is_capturing = False
        
        # Tạo các thư mục cần thiết
        self.setup_directories()
        
        # Load dữ liệu khuôn mặt đã lưu
        self.load_known_faces()
        
        # Tạo giao diện
        self.create_widgets()
        
    def setup_directories(self):
        """Tạo các thư mục cần thiết"""
        directories = ['faces', 'recognized']
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
    
    def create_temp_folder(self):
        """Tạo folder temp/ khi cần"""
        if not os.path.exists('temp'):
            os.makedirs('temp')
    
    def remove_temp_folder(self):
        """Xóa folder temp/ sau khi xong"""
        import shutil
        if os.path.exists('temp'):
            try:
                shutil.rmtree('temp')
            except Exception as e:
                print(f"Không thể xóa folder temp: {e}")
                
    def load_known_faces(self):
        """Tải các khuôn mặt và metadata từ face_database/ folder structure"""
        self.known_face_encodings = []
        self.known_face_names = []
        self.face_metadata = {}
        self.person_encodings = {}
        
        # Load từ database folder structure
        all_embeddings, all_metadata = self.db.get_all_embeddings_with_info()
        
        for embedding, metadata in zip(all_embeddings, all_metadata):
            folder_name = metadata["folder_name"]
            user_name = metadata["user_name"]
            
            self.known_face_encodings.append(embedding)
            self.known_face_names.append(folder_name)  # Dùng folder_name để phân biệt
            
            # Lưu metadata đầy đủ (key = folder_name để tránh trùng)
            if folder_name not in self.face_metadata:
                self.face_metadata[folder_name] = {
                    "folder_name": folder_name,
                    "user_name": user_name,
                    "gender": metadata.get("gender", ""),
                    "birth_year": metadata.get("birth_year", ""),
                    "hometown": metadata.get("hometown", ""),
                    "residence": metadata.get("residence", ""),
                    "created_at": metadata.get("created_at", ""),
                    "embedding_count": metadata.get("embedding_count", 0)
                }
            
            # Lưu encodings theo người
            if folder_name not in self.person_encodings:
                self.person_encodings[folder_name] = []
            self.person_encodings[folder_name].append(embedding)
        
        print(f"✅ Đã tải {len(all_embeddings)} embeddings từ {len(self.person_encodings)} người")
        print(f"📂 Database: face_database/")
        
    def create_widgets(self):
        """Tạo giao diện chính"""
        # Header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame, 
            text="🔍 HỆ THỐNG NHẬN DIỆN KHUÔN MẶT",
            font=("Arial", 24, "bold"),
            fg="white",
            bg="#2c3e50"
        )
        title_label.pack(pady=20)
        
        # Main content frame
        content_frame = tk.Frame(self.root, bg="#f0f0f0")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Left panel - Menu
        left_panel = tk.Frame(content_frame, bg="white", relief=tk.RAISED, borderwidth=2)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        menu_title = tk.Label(
            left_panel,
            text="📋 CHỨC NĂNG",
            font=("Arial", 16, "bold"),
            bg="white",
            fg="#2c3e50"
        )
        menu_title.pack(pady=15)
        
        # Menu buttons
        button_config = {
            'font': ("Arial", 11),
            'width': 25,
            'height': 2,
            'relief': tk.RAISED,
            'borderwidth': 2,
            'cursor': 'hand2'
        }
        
        btn_register = tk.Button(
            left_panel,
            text="➕ Đăng ký khuôn mặt mới",
            bg="#3498db",
            fg="white",
            command=self.register_face_menu,
            **button_config
        )
        btn_register.pack(pady=5, padx=10)
        
        btn_recognize = tk.Button(
            left_panel,
            text="🔍 Nhận diện từ ảnh/video",
            bg="#2ecc71",
            fg="white",
            command=self.recognize_from_file,
            **button_config
        )
        btn_recognize.pack(pady=5, padx=10)
        
        btn_organize = tk.Button(
            left_panel,
            text="📁 Tổ chức ảnh theo người",
            bg="#9b59b6",
            fg="white",
            command=self.organize_photos,
            **button_config
        )
        btn_organize.pack(pady=5, padx=10)
        
        btn_manage = tk.Button(
            left_panel,
            text="⚙️ Quản lý khuôn mặt",
            bg="#e67e22",
            fg="white",
            command=self.manage_faces,
            **button_config
        )
        btn_manage.pack(pady=5, padx=10)
        
        btn_webcam = tk.Button(
            left_panel,
            text="📹 Nhận diện từ Webcam",
            bg="#1abc9c",
            fg="white",
            command=self.recognize_from_webcam,
            **button_config
        )
        btn_webcam.pack(pady=5, padx=10)
        
        btn_reload = tk.Button(
            left_panel,
            text="🔄 Tải lại dữ liệu",
            bg="#95a5a6",
            fg="white",
            command=self.reload_data,
            **button_config
        )
        btn_reload.pack(pady=5, padx=10)
        
        # Right panel - Display area
        self.right_panel = tk.Frame(content_frame, bg="white", relief=tk.RAISED, borderwidth=2)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Welcome message
        self.show_welcome_screen()
        
        # Status bar
        self.status_bar = tk.Label(
            self.root,
            text=f"Sẵn sàng | Đã tải {len(self.known_face_encodings)} khuôn mặt",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#ecf0f1",
            font=("Arial", 10)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def show_welcome_screen(self):
        """Hiển thị màn hình chào mừng"""
        self.clear_right_panel()
        
        welcome_label = tk.Label(
            self.right_panel,
            text="👋 Chào mừng đến với\nHệ Thống Nhận Diện Khuôn Mặt",
            font=("Arial", 18, "bold"),
            bg="white",
            fg="#2c3e50"
        )
        welcome_label.pack(pady=50)
        
        info_text = """
        ✨ Các tính năng:
        
        • Đăng ký khuôn mặt mới
        • Nhận diện khuôn mặt từ ảnh/video
        • Tự động tổ chức ảnh theo người
        • Quản lý và đổi tên khuôn mặt
        • Nhận diện real-time từ webcam
        
        👈 Chọn chức năng bên trái để bắt đầu
        """
        
        info_label = tk.Label(
            self.right_panel,
            text=info_text,
            font=("Arial", 12),
            bg="white",
            fg="#34495e",
            justify=tk.LEFT
        )
        info_label.pack(pady=20)
        
    def clear_right_panel(self):
        """Xóa nội dung panel bên phải"""
        # Dừng auto-refresh nếu đang bật
        if hasattr(self, 'is_managing_faces'):
            self.is_managing_faces = False
        
        for widget in self.right_panel.winfo_children():
            widget.destroy()
            
    def update_status(self, message):
        """Cập nhật thanh trạng thái"""
        self.status_bar.config(text=message)
        self.root.update()
        
    def register_face_menu(self):
        """Menu đăng ký khuôn mặt"""
        self.clear_right_panel()
        
        title = tk.Label(
            self.right_panel,
            text="➕ Đăng ký khuôn mặt mới",
            font=("Arial", 16, "bold"),
            bg="white"
        )
        title.pack(pady=20)
        
        # Nút chụp từ webcam
        btn_webcam = tk.Button(
            self.right_panel,
            text="📸 Chụp từ Webcam",
            font=("Arial", 12),
            bg="#3498db",
            fg="white",
            width=30,
            height=2,
            command=self.capture_from_webcam
        )
        btn_webcam.pack(pady=10)
        
        # Nút chọn từ file
        btn_file = tk.Button(
            self.right_panel,
            text="📁 Chọn từ File ảnh",
            font=("Arial", 12),
            bg="#2ecc71",
            fg="white",
            width=30,
            height=2,
            command=self.register_from_file
        )
        btn_file.pack(pady=10)
        
    def capture_from_webcam(self):
        """Chụp ảnh từ webcam để đăng ký"""
        self.clear_right_panel()
        
        title = tk.Label(
            self.right_panel,
            text="📸 Chụp ảnh từ Webcam",
            font=("Arial", 14, "bold"),
            bg="white"
        )
        title.pack(pady=10)
        
        # Video frame
        self.video_label = tk.Label(self.right_panel, bg="black")
        self.video_label.pack(pady=10)
        
        # Buttons frame
        btn_frame = tk.Frame(self.right_panel, bg="white")
        btn_frame.pack(pady=10)
        
        # Nút chụp ảnh
        btn_capture = tk.Button(
            btn_frame,
            text="📸 Chụp ảnh",
            font=("Arial", 11),
            bg="#2ecc71",
            fg="white",
            width=15,
            command=self.save_captured_face
        )
        btn_capture.pack(side=tk.LEFT, padx=5)
        
        # Nút ghi video
        self.is_recording_enrollment = False
        self.enrollment_video_frames = []
        self.record_enrollment_btn = tk.Button(
            btn_frame,
            text="🎥 Ghi video",
            font=("Arial", 11),
            bg="#3498db",
            fg="white",
            width=15,
            command=self.toggle_enrollment_recording
        )
        self.record_enrollment_btn.pack(side=tk.LEFT, padx=5)
        
        # Nút dừng
        btn_stop = tk.Button(
            btn_frame,
            text="❌ Dừng",
            font=("Arial", 11),
            bg="#e74c3c",
            fg="white",
            width=15,
            command=self.stop_capture
        )
        btn_stop.pack(side=tk.LEFT, padx=5)
        
        # Bắt đầu webcam
        self.is_capturing = True
        self.video_capture = cv2.VideoCapture(0)
        self.update_webcam_feed()
        
    def update_webcam_feed(self):
        """Cập nhật video feed từ webcam"""
        if self.is_capturing and self.video_capture.isOpened():
            ret, frame = self.video_capture.read()
            if ret:
                # Detect faces
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame)
                
                # Draw rectangles
                for (top, right, bottom, left) in face_locations:
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                
                # Convert to PhotoImage
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img = img.resize((640, 480), Image.Resampling.LANCZOS)
                imgtk = ImageTk.PhotoImage(image=img)
                
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
                
                self.current_frame = frame
                
                # Nếu đang ghi video enrollment, thu thập frames
                if hasattr(self, 'is_recording_enrollment') and self.is_recording_enrollment:
                    # Chỉ lưu frame có khuôn mặt
                    if len(face_locations) > 0:
                        self.enrollment_video_frames.append(frame.copy())
                
            self.root.after(10, self.update_webcam_feed)
            
    def save_captured_face(self):
        """Lưu khuôn mặt đã chụp với kiểm tra trùng lặp"""
        if hasattr(self, 'current_frame'):
            # Detect face
            rgb_frame = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            
            if face_locations:
                # Encode face
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                if not face_encodings:
                    messagebox.showwarning("Cảnh báo", "⚠️ Không thể mã hóa khuôn mặt!")
                    return
                
                new_face_encoding = face_encodings[0]
                
                # Kiểm tra trùng lặp với database
                matched_person = None
                best_match_distance = 1.0
                
                if self.known_face_encodings:
                    face_distances = face_recognition.face_distance(self.known_face_encodings, new_face_encoding)
                    best_match_index = np.argmin(face_distances)
                    best_match_distance = face_distances[best_match_index]
                    
                    # Ngưỡng nhận diện (0.6 là mặc định, càng thấp càng nghiêm)
                    if best_match_distance < 0.6:
                        matched_person = self.known_face_names[best_match_index]
                
                # Nếu tìm thấy trùng khớp
                if matched_person:
                    response = messagebox.askyesno(
                        "Phát hiện trùng lặp!",
                        f"⚠️ Khuôn mặt này trùng với: {matched_person}\n"
                        f"Độ tương đồng: {(1 - best_match_distance) * 100:.1f}%\n\n"
                        f"Bạn có muốn:\n"
                        f"• YES: Thêm ảnh này vào folder '{matched_person}'\n"
                        f"• NO: Đăng ký như người mới"
                    )
                    
                    if response:
                        # Thêm vào folder người đã có
                        person_folder = os.path.join("faces", matched_person)
                        if not os.path.exists(person_folder):
                            os.makedirs(person_folder)
                        
                        # Đếm số ảnh hiện có
                        existing_count = len([f for f in os.listdir(person_folder) 
                                            if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
                        
                        filename = os.path.join(person_folder, f"{matched_person}_{existing_count + 1}.jpg")
                        cv2.imwrite(filename, self.current_frame)
                        
                        messagebox.showinfo("Thành công", 
                                          f"✅ Đã thêm ảnh vào folder của {matched_person}\n"
                                          f"Tổng số ảnh: {existing_count + 1}")
                        self.update_status(f"Đã thêm ảnh cho: {matched_person}")
                        self.load_known_faces()
                        self.stop_capture()
                        return
                
                # Đăng ký người mới - Mở dialog nhập thông tin đầy đủ
                person_info = PersonInfoDialog(self.root).show()
                
                if person_info:
                    name = person_info["name"]
                    
                    # Tạo folder temp
                    self.create_temp_folder()
                    
                    # Lưu ảnh tạm
                    temp_path = os.path.join("temp", f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
                    cv2.imwrite(temp_path, self.current_frame)
                    
                    # Đăng ký qua service V2 (không cần user_id nữa)
                    result = self.enrollment_service.enroll_face(
                        image_path=temp_path,
                        user_name=name,
                        gender=person_info["gender"],
                        birth_year=person_info["birth_year"],
                        hometown=person_info["hometown"],
                        residence=person_info["residence"],
                        check_duplicate=False  # Đã check trước đó
                    )
                    
                    # Xóa file temp và folder temp
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    self.remove_temp_folder()
                    
                    if result["success"]:
                        info_text = f"✅ Đã đăng ký thành công: {name}\n"
                        if person_info["gender"]:
                            info_text += f"Giới tính: {person_info['gender']}\n"
                        if person_info["birth_year"]:
                            info_text += f"Năm sinh: {person_info['birth_year']}\n"
                        if person_info["hometown"]:
                            info_text += f"Quê quán: {person_info['hometown']}\n"
                        if person_info["residence"]:
                            info_text += f"Nơi sinh sống: {person_info['residence']}\n"
                        
                        messagebox.showinfo("Thành công", info_text)
                        self.update_status(f"Đã đăng ký người mới: {name}")
                    else:
                        messagebox.showerror("Lỗi", result["message"])
                    
                    # Reload data
                    self.identification_service.reload_database()
                    self.load_known_faces()
                    self.stop_capture()
            else:
                messagebox.showwarning("Cảnh báo", "⚠️ Không phát hiện khuôn mặt!\nHãy đảm bảo khuôn mặt hiển thị rõ ràng.")
    
    def toggle_enrollment_recording(self):
        """Bật/tắt ghi video để đăng ký"""
        if not self.is_recording_enrollment:
            # Bắt đầu ghi
            self.start_enrollment_recording()
        else:
            # Dừng ghi và xử lý
            self.stop_enrollment_recording()
    
    def start_enrollment_recording(self):
        """Bắt đầu ghi video enrollment"""
        self.is_recording_enrollment = True
        self.enrollment_video_frames = []
        self.record_enrollment_btn.config(text="⏹️ Dừng ghi", bg="#e74c3c")
        self.update_status("🔴 Đang ghi video... Di chuyển khuôn mặt để lấy nhiều góc độ!")
    
    def stop_enrollment_recording(self):
        """Dừng ghi video và xử lý frames để đăng ký"""
        self.is_recording_enrollment = False
        self.record_enrollment_btn.config(text="🎥 Ghi video", bg="#3498db")
        
        if not self.enrollment_video_frames or len(self.enrollment_video_frames) == 0:
            messagebox.showwarning("Cảnh báo", "⚠️ Không có frame nào được ghi!\nHãy đảm bảo khuôn mặt hiển thị trong video.")
            self.update_status("Sẵn sàng")
            return
        
        # Lấy mẫu frames (mỗi 5 frames lấy 1 để tránh trùng lặp quá nhiều)
        total_frames = len(self.enrollment_video_frames)
        step = max(1, total_frames // 10)  # Tối đa 10 frames
        sampled_frames = self.enrollment_video_frames[::step][:10]
        
        # NHẬN DIỆN frame đầu tiên để check xem có trùng không
        first_frame = sampled_frames[0]
        rgb_frame = cv2.cvtColor(first_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        
        if not face_locations:
            messagebox.showwarning("Cảnh báo", "⚠️ Không phát hiện khuôn mặt trong video!")
            self.enrollment_video_frames = []
            self.update_status("Sẵn sàng")
            return
        
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
        
        if not face_encodings:
            messagebox.showwarning("Cảnh báo", "⚠️ Không thể trích xuất đặc trưng khuôn mặt!")
            self.enrollment_video_frames = []
            self.update_status("Sẵn sàng")
            return
        
        face_encoding = face_encodings[0]
        
        # KIỂM TRA TRÙNG LẶP với database hiện có
        matched_person = None
        best_match_distance = 1.0
        
        if self.known_face_encodings:
            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            best_match_distance = face_distances[best_match_index]
            
            if best_match_distance < 0.6:
                matched_person = self.known_face_names[best_match_index]
        
        # Nếu trùng, hiển thị dialog 3 options
        if matched_person:
            # Tạo dialog với 3 options
            dialog = tk.Toplevel(self.root)
            dialog.title("⚠️ Phát hiện trùng lặp")
            dialog.geometry("550x350")
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Biến lưu lựa chọn
            user_choice = tk.StringVar(value="")
            
            # Header
            header = tk.Label(
                dialog,
                text="⚠️ PHÁT HIỆN TRÙNG LẶP",
                font=("Arial", 14, "bold"),
                bg="#e74c3c",
                fg="white",
                pady=15
            )
            header.pack(fill=tk.X)
            
            # Info frame
            info_frame = tk.Frame(dialog, padx=30, pady=20)
            info_frame.pack(fill=tk.BOTH, expand=True)
            
            info_text = (
                f"Khuôn mặt này trùng với: {matched_person}\n\n"
                f"Độ tương đồng: {(1 - best_match_distance) * 100:.1f}%\n"
                f"Đã ghi: {total_frames} frames\n\n"
                f"Bạn muốn làm gì?"
            )
            tk.Label(
                info_frame,
                text=info_text,
                font=("Arial", 11),
                justify=tk.LEFT
            ).pack(pady=10)
            
            # Button frame
            btn_frame = tk.Frame(dialog)
            btn_frame.pack(pady=20)
            
            # Button 1: Lưu video
            def save_video():
                user_choice.set("save")
                dialog.destroy()
            
            btn_save = tk.Button(
                btn_frame,
                text="💾 Lưu video\nvào folder này",
                font=("Arial", 10, "bold"),
                bg="#27ae60",
                fg="white",
                width=15,
                height=3,
                command=save_video
            )
            btn_save.pack(side=tk.LEFT, padx=10)
            
            # Button 2: Không lưu
            def dont_save():
                user_choice.set("skip")
                dialog.destroy()
            
            btn_skip = tk.Button(
                btn_frame,
                text="🚫 Không lưu\n(Bỏ qua)",
                font=("Arial", 10, "bold"),
                bg="#95a5a6",
                fg="white",
                width=15,
                height=3,
                command=dont_save
            )
            btn_skip.pack(side=tk.LEFT, padx=10)
            
            # Button 3: Đăng ký mới
            def register_new():
                user_choice.set("new")
                dialog.destroy()
            
            btn_new = tk.Button(
                btn_frame,
                text="➕ Đăng ký\nngười mới",
                font=("Arial", 10, "bold"),
                bg="#3498db",
                fg="white",
                width=15,
                height=3,
                command=register_new
            )
            btn_new.pack(side=tk.LEFT, padx=10)
            
            # Wait for user choice
            dialog.wait_window()
            
            # Xử lý theo lựa chọn
            choice = user_choice.get()
            
            if choice == "save":
                # OPTION 1: Lưu VIDEO vào folder người đã có (TOÀN BỘ FRAMES)
                person_folder = os.path.join("faces", matched_person)
                if not os.path.exists(person_folder):
                    os.makedirs(person_folder)
                
                # Tạo folder temp để lưu video tạm
                self.create_temp_folder()
                
                # Đếm số video hiện có
                existing_count = len([f for f in os.listdir(person_folder) 
                                    if f.lower().endswith(('.mp4', '.avi'))])
                
                # Tạo video từ TẤT CẢ FRAMES
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_video_path = f"temp/temp_enrollment_{timestamp}.mp4"
                final_video_path = os.path.join(person_folder, f"{matched_person}_video_{existing_count + 1}.mp4")
                
                # Lấy kích thước frame
                frame_height, frame_width = self.enrollment_video_frames[0].shape[:2]
                
                # Tạo VideoWriter với FPS cao hơn để video mượt hơn
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                video_writer = cv2.VideoWriter(temp_video_path, fourcc, 20.0, (frame_width, frame_height))
                
                # Ghi TẤT CẢ các frames vào video
                for frame in self.enrollment_video_frames:
                    video_writer.write(frame)
                
                video_writer.release()
                
                # Di chuyển video sang folder người
                import shutil
                shutil.move(temp_video_path, final_video_path)
                
                # Xóa folder temp
                self.remove_temp_folder()
                
                file_size = os.path.getsize(final_video_path) / (1024 * 1024)  # MB
                duration = len(self.enrollment_video_frames) / 20.0  # Thời lượng video (giây)
                
                messagebox.showinfo(
                    "Thành công", 
                    f"✅ Đã lưu video vào folder của {matched_person}\n\n"
                    f"📹 File: {matched_person}_video_{existing_count + 1}.mp4\n"
                    f"📦 Kích thước: {file_size:.2f} MB\n"
                    f"🎬 Frames: {len(self.enrollment_video_frames)}\n"
                    f"⏱️ Thời lượng: {duration:.1f}s"
                )
                self.update_status(f"Đã lưu video cho: {matched_person}")
                self.load_known_faces()
                self.enrollment_video_frames = []
                self.stop_capture()
                return
            
            elif choice == "skip":
                # OPTION 2: Không lưu, bỏ qua
                messagebox.showinfo("Thông báo", "❎ Đã bỏ qua video này (không lưu)")
                self.update_status("Đã bỏ qua video")
                self.enrollment_video_frames = []
                return
            
            elif choice == "new":
                # OPTION 3: Đăng ký người mới (tiếp tục xuống dưới)
                pass
            else:
                # User đóng dialog
                self.enrollment_video_frames = []
                self.update_status("Đã hủy")
                return
        
        # KHÔNG TRÙNG - Đăng ký người mới
        messagebox.showinfo(
            "Thông tin",
            f"📹 Đã ghi {total_frames} frames\n"
            f"📸 Sẽ sử dụng {len(sampled_frames)} frames để đăng ký\n\n"
            f"Tiếp tục nhập thông tin..."
        )
        
        # Mở dialog nhập thông tin
        person_info = PersonInfoDialog(self.root).show()
        
        if person_info:
            name = person_info["name"]
            
            # Tạo folder temp
            self.create_temp_folder()
            
            success_count = 0
            failed_count = 0
            
            # Xử lý từng frame
            for i, frame in enumerate(sampled_frames):
                temp_path = os.path.join("temp", f"temp_video_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
                cv2.imwrite(temp_path, frame)
                
                # Đăng ký frame
                if i == 0:
                    # Frame đầu tiên: tạo người mới
                    result = self.enrollment_service.enroll_face(
                        image_path=temp_path,
                        user_name=name,
                        gender=person_info["gender"],
                        birth_year=person_info["birth_year"],
                        hometown=person_info["hometown"],
                        residence=person_info["residence"],
                        check_duplicate=True
                    )
                else:
                    # Các frame tiếp theo: thêm vào người đã tạo
                    result = self.enrollment_service.enroll_face(
                        image_path=temp_path,
                        user_name=name,
                        gender=person_info["gender"],
                        birth_year=person_info["birth_year"],
                        hometown=person_info["hometown"],
                        residence=person_info["residence"],
                        check_duplicate=False
                    )
                
                # Xóa file temp
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                
                if result["success"]:
                    success_count += 1
                else:
                    failed_count += 1
            
            # Xóa folder temp
            self.remove_temp_folder()
            
            # Hiển thị kết quả
            if success_count > 0:
                # LƯU VIDEO vào folder của người mới
                person_folder = os.path.join("faces", self.db._generate_unique_folder_name(name))
                
                # Tìm folder thực tế đã được tạo
                all_folders = [f for f in os.listdir("faces") if os.path.isdir(os.path.join("faces", f)) and f.startswith(name.lower().replace(" ", "_"))]
                if all_folders:
                    person_folder = os.path.join("faces", sorted(all_folders)[-1])  # Lấy folder mới nhất
                    
                    # Tạo folder temp để lưu video
                    self.create_temp_folder()
                    
                    # Tạo video từ TẤT CẢ FRAMES
                    from datetime import datetime
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    temp_video_path = f"temp/temp_enrollment_{timestamp}.mp4"
                    
                    folder_name = os.path.basename(person_folder)
                    final_video_path = os.path.join(person_folder, f"{folder_name}_video_1.mp4")
                    
                    # Lấy kích thước frame
                    frame_height, frame_width = self.enrollment_video_frames[0].shape[:2]
                    
                    # Tạo VideoWriter
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    video_writer = cv2.VideoWriter(temp_video_path, fourcc, 20.0, (frame_width, frame_height))
                    
                    # Ghi TẤT CẢ frames vào video
                    for frame in self.enrollment_video_frames:
                        video_writer.write(frame)
                    
                    video_writer.release()
                    
                    # Di chuyển video sang folder người
                    import shutil
                    shutil.move(temp_video_path, final_video_path)
                    
                    # Xóa folder temp
                    self.remove_temp_folder()
                    
                    file_size = os.path.getsize(final_video_path) / (1024 * 1024)  # MB
                    duration = len(self.enrollment_video_frames) / 20.0
                
                info_text = f"✅ Đã đăng ký thành công: {name}\n\n"
                info_text += f"📊 Thống kê:\n"
                info_text += f"   ✅ Embeddings: {success_count} frames\n"
                if failed_count > 0:
                    info_text += f"   ❌ Thất bại: {failed_count} frames\n"
                
                # Thêm thông tin video
                if all_folders:
                    info_text += f"\n📹 Video:\n"
                    info_text += f"   📦 Kích thước: {file_size:.2f} MB\n"
                    info_text += f"   🎬 Frames: {len(self.enrollment_video_frames)}\n"
                    info_text += f"   ⏱️ Thời lượng: {duration:.1f}s\n"
                
                if person_info["gender"]:
                    info_text += f"\nGiới tính: {person_info['gender']}"
                if person_info["birth_year"]:
                    info_text += f"\nNăm sinh: {person_info['birth_year']}"
                if person_info["hometown"]:
                    info_text += f"\nQuê quán: {person_info['hometown']}"
                if person_info["residence"]:
                    info_text += f"\nNơi sinh sống: {person_info['residence']}"
                
                messagebox.showinfo("Thành công", info_text)
                self.update_status(f"Đã đăng ký: {name} ({success_count} ảnh + video)")
                
                # Reload data
                self.identification_service.reload_database()
                self.load_known_faces()
                
                # Xóa danh sách frames
                self.enrollment_video_frames = []
                
                self.stop_capture()
            else:
                messagebox.showerror("Lỗi", "❌ Không thể đăng ký! Tất cả frames đều thất bại.")
                self.update_status("Đăng ký thất bại")
                # Xóa frames
                self.enrollment_video_frames = []
        else:
            # User hủy dialog, xóa frames
            self.enrollment_video_frames = []
            self.update_status("Sẵn sàng")
        
    def stop_capture(self):
        """Dừng webcam"""
        # Reset recording state nếu đang ghi
        if hasattr(self, 'is_recording_enrollment'):
            self.is_recording_enrollment = False
            self.enrollment_video_frames = []
        
        self.is_capturing = False
        if self.video_capture:
            self.video_capture.release()
        self.show_welcome_screen()
        
    def register_from_file(self):
        """Đăng ký khuôn mặt từ file với kiểm tra trùng lặp"""
        file_path = filedialog.askopenfilename(
            title="Chọn ảnh",
            filetypes=[("Image files", "*.jpg *.jpeg *.png")]
        )
        
        if file_path:
            # Load image
            image = face_recognition.load_image_file(file_path)
            face_locations = face_recognition.face_locations(image)
            
            if face_locations:
                # Encode face
                face_encodings = face_recognition.face_encodings(image, face_locations)
                if not face_encodings:
                    messagebox.showwarning("Cảnh báo", "⚠️ Không thể mã hóa khuôn mặt!")
                    return
                
                new_face_encoding = face_encodings[0]
                
                # Kiểm tra trùng lặp với database
                matched_person = None
                best_match_distance = 1.0
                
                if self.known_face_encodings:
                    face_distances = face_recognition.face_distance(self.known_face_encodings, new_face_encoding)
                    best_match_index = np.argmin(face_distances)
                    best_match_distance = face_distances[best_match_index]
                    
                    # Ngưỡng nhận diện
                    if best_match_distance < 0.6:
                        matched_person = self.known_face_names[best_match_index]
                
                # Nếu tìm thấy trùng khớp
                if matched_person:
                    # Tạo dialog với 3 options
                    dialog = tk.Toplevel(self.root)
                    dialog.title("⚠️ Phát hiện trùng lặp")
                    dialog.geometry("500x300")
                    dialog.transient(self.root)
                    dialog.grab_set()
                    
                    # Biến lưu lựa chọn
                    user_choice = tk.StringVar(value="")
                    
                    # Header
                    header = tk.Label(
                        dialog,
                        text="⚠️ PHÁT HIỆN TRÙNG LẶP",
                        font=("Arial", 14, "bold"),
                        bg="#e74c3c",
                        fg="white",
                        pady=15
                    )
                    header.pack(fill=tk.X)
                    
                    # Info frame
                    info_frame = tk.Frame(dialog, padx=30, pady=20)
                    info_frame.pack(fill=tk.BOTH, expand=True)
                    
                    info_text = (
                        f"Khuôn mặt này trùng với: {matched_person}\n\n"
                        f"Độ tương đồng: {(1 - best_match_distance) * 100:.1f}%\n\n"
                        f"Bạn muốn làm gì?"
                    )
                    tk.Label(
                        info_frame,
                        text=info_text,
                        font=("Arial", 11),
                        justify=tk.LEFT
                    ).pack(pady=10)
                    
                    # Button frame
                    btn_frame = tk.Frame(dialog)
                    btn_frame.pack(pady=20)
                    
                    # Button 1: Lưu ảnh
                    def save_image():
                        user_choice.set("save")
                        dialog.destroy()
                    
                    btn_save = tk.Button(
                        btn_frame,
                        text="💾 Lưu ảnh vào\nfolder này",
                        font=("Arial", 10, "bold"),
                        bg="#27ae60",
                        fg="white",
                        width=15,
                        height=3,
                        command=save_image
                    )
                    btn_save.pack(side=tk.LEFT, padx=10)
                    
                    # Button 2: Không lưu
                    def dont_save():
                        user_choice.set("skip")
                        dialog.destroy()
                    
                    btn_skip = tk.Button(
                        btn_frame,
                        text="🚫 Không lưu\n(Bỏ qua)",
                        font=("Arial", 10, "bold"),
                        bg="#95a5a6",
                        fg="white",
                        width=15,
                        height=3,
                        command=dont_save
                    )
                    btn_skip.pack(side=tk.LEFT, padx=10)
                    
                    # Button 3: Đăng ký mới
                    def register_new():
                        user_choice.set("new")
                        dialog.destroy()
                    
                    btn_new = tk.Button(
                        btn_frame,
                        text="➕ Đăng ký\nngười mới",
                        font=("Arial", 10, "bold"),
                        bg="#3498db",
                        fg="white",
                        width=15,
                        height=3,
                        command=register_new
                    )
                    btn_new.pack(side=tk.LEFT, padx=10)
                    
                    # Wait for user choice
                    dialog.wait_window()
                    
                    # Xử lý theo lựa chọn
                    choice = user_choice.get()
                    
                    if choice == "save":
                        # OPTION 1: Lưu ảnh vào folder người đã có
                        person_folder = os.path.join("faces", matched_person)
                        if not os.path.exists(person_folder):
                            os.makedirs(person_folder)
                        
                        # Đếm số ảnh hiện có
                        existing_count = len([f for f in os.listdir(person_folder) 
                                            if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
                        
                        ext = os.path.splitext(file_path)[1]
                        dest_path = os.path.join(person_folder, f"{matched_person}_{existing_count + 1}{ext}")
                        shutil.copy(file_path, dest_path)
                        
                        messagebox.showinfo("Thành công", 
                                          f"✅ Đã lưu ảnh vào folder của {matched_person}\n"
                                          f"Tổng số ảnh: {existing_count + 1}")
                        self.update_status(f"Đã thêm ảnh cho: {matched_person}")
                        self.load_known_faces()
                        return
                    
                    elif choice == "skip":
                        # OPTION 2: Không lưu, bỏ qua
                        messagebox.showinfo("Thông báo", "❎ Đã bỏ qua ảnh này (không lưu)")
                        self.update_status("Đã bỏ qua ảnh")
                        return
                    
                    elif choice == "new":
                        # OPTION 3: Đăng ký người mới (tiếp tục xuống dưới)
                        pass
                    else:
                        # User đóng dialog
                        self.update_status("Đã hủy")
                        return
                
                # Đăng ký người mới - Mở dialog nhập thông tin đầy đủ
                person_info = PersonInfoDialog(self.root).show()
                
                if person_info:
                    name = person_info["name"]
                    
                    # Đăng ký qua service V2 (không cần user_id)
                    result = self.enrollment_service.enroll_face(
                        image_path=file_path,
                        user_name=name,
                        gender=person_info["gender"],
                        birth_year=person_info["birth_year"],
                        hometown=person_info["hometown"],
                        residence=person_info["residence"],
                        check_duplicate=False  # Đã check trước đó
                    )
                    
                    if result["success"]:
                        info_text = f"✅ Đã đăng ký thành công: {name}\n"
                        if person_info["gender"]:
                            info_text += f"Giới tính: {person_info['gender']}\n"
                        if person_info["birth_year"]:
                            info_text += f"Năm sinh: {person_info['birth_year']}\n"
                        if person_info["hometown"]:
                            info_text += f"Quê quán: {person_info['hometown']}\n"
                        if person_info["residence"]:
                            info_text += f"Nơi sinh sống: {person_info['residence']}\n"
                        
                        messagebox.showinfo("Thành công", info_text)
                        self.update_status(f"Đã đăng ký người mới: {name}")
                    else:
                        messagebox.showerror("Lỗi", result["message"])
                    
                    # Reload data
                    self.identification_service.reload_database()
                    self.load_known_faces()
            else:
                messagebox.showwarning("Cảnh báo", "⚠️ Không phát hiện khuôn mặt trong ảnh!")
                
    def recognize_from_file(self):
        """Nhận diện khuôn mặt từ file"""
        file_paths = filedialog.askopenfilenames(
            title="Chọn ảnh/video để nhận diện",
            filetypes=[("Media files", "*.jpg *.jpeg *.png *.mp4 *.avi")]
        )
        
        if file_paths:
            self.update_status(f"Đang xử lý {len(file_paths)} file...")
            threading.Thread(target=self.process_recognition_files, args=(file_paths,), daemon=True).start()
            
    def process_recognition_files(self, file_paths):
        """Xử lý nhận diện từ các file"""
        total_faces = 0
        
        for file_path in file_paths:
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext in ['.jpg', '.jpeg', '.png']:
                # Process image
                image = cv2.imread(file_path)
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                
                face_locations = face_recognition.face_locations(rgb_image)
                face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
                
                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    # Compare with known faces
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                    folder_name = "Unknown"
                    display_info = []
                    
                    if True in matches:
                        face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            folder_name = self.known_face_names[best_match_index]
                            
                            # Lấy thông tin đầy đủ từ metadata
                            if folder_name in self.face_metadata:
                                metadata = self.face_metadata[folder_name]
                                
                                # Hiển thị TẤT CẢ thông tin, mỗi loại 1 dòng theo hàng dọc
                                # Dòng 1: Tên
                                if metadata.get('user_name'):
                                    display_info.append(f"👤 {metadata['ten']}")
                                
                                # Dòng 2: Giới tính
                                if metadata.get("gender"):
                                    display_info.append(f"⚧  {metadata['gioitinh']}")
                                
                                # Dòng 3: Năm sinh
                                if metadata.get("birth_year"):
                                    display_info.append(f"🎂 {metadata['namsinh']}")
                                
                                # Dòng 4: Quê quán
                                if metadata.get("hometown"):
                                    display_info.append(f"🏠 {metadata['quequan']}")
                                
                                # Dòng 5: Nơi sinh sống
                                if metadata.get("residence"):
                                    display_info.append(f"📍 {metadata['noisinh']}")
                                
                                # Nếu không có thông tin gì
                                if not display_info:
                                    display_info = [folder_name]
                            else:
                                display_info = [folder_name]
                    else:
                        display_info = ["❓ Unknown"]
                    
                    # Draw rectangle around face
                    cv2.rectangle(image, (left, top), (right, bottom), (0, 255, 0), 2)
                    
                    # Vẽ thông tin bằng PIL (hỗ trợ Unicode + emoji)
                    from PIL import Image as PILImage, ImageDraw, ImageFont
                    
                    # Convert sang PIL
                    pil_image = PILImage.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                    draw = ImageDraw.Draw(pil_image)
                    
                    # Sử dụng font hỗ trợ Unicode
                    try:
                        # Windows font hỗ trợ tiếng Việt và emoji
                        font_pil = ImageFont.truetype("arial.ttf", 14)
                    except:
                        font_pil = ImageFont.load_default()
                    
                    # Tính vị trí vẽ text
                    line_height = 20
                    y_offset = top - (len(display_info) * line_height) - 10
                    if y_offset < 0:
                        y_offset = bottom + 10
                    
                    # Vẽ từng dòng
                    for i, info_line in enumerate(display_info):
                        y_pos = y_offset + (i * line_height)
                        
                        # Đo kích thước text
                        bbox = draw.textbbox((0, 0), info_line, font=font_pil)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                        
                        # Vẽ background
                        draw.rectangle(
                            [(left, y_pos - 2), (left + text_width + 10, y_pos + text_height + 2)],
                            fill=(0, 255, 0)
                        )
                        
                        # Vẽ text
                        draw.text((left + 5, y_pos), info_line, font=font_pil, fill=(0, 0, 0))
                    
                    # Convert lại sang OpenCV
                    image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                    
                    total_faces += 1
                
                # Save result
                base_name = os.path.basename(file_path)
                output_path = f"recognized/recognized_{base_name}"
                cv2.imwrite(output_path, image)
        
        self.root.after(0, lambda: messagebox.showinfo("Hoàn thành", f"✅ Đã nhận diện {total_faces} khuôn mặt!\nKết quả lưu trong thư mục 'recognized'"))
        self.root.after(0, lambda: self.update_status(f"Hoàn thành! Nhận diện {total_faces} khuôn mặt"))
        
    def organize_photos(self):
        """Tổ chức ảnh theo người"""
        folder_path = filedialog.askdirectory(title="Chọn thư mục chứa ảnh cần tổ chức")
        
        if folder_path:
            self.update_status("Đang tổ chức ảnh...")
            threading.Thread(target=self.process_organize_photos, args=(folder_path,), daemon=True).start()
            
    def process_organize_photos(self, folder_path):
        """Xử lý tổ chức ảnh"""
        organized_count = 0
        unknown_count = 0
        
        # Create output directory
        output_dir = "organized_photos"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        for file in os.listdir(folder_path):
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                file_path = os.path.join(folder_path, file)
                
                try:
                    image = face_recognition.load_image_file(file_path)
                    face_locations = face_recognition.face_locations(image)
                    face_encodings = face_recognition.face_encodings(image, face_locations)
                    
                    for face_encoding in face_encodings:
                        matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                        name = "Unknown"
                        
                        if True in matches:
                            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                            best_match_index = np.argmin(face_distances)
                            if matches[best_match_index]:
                                name = self.known_face_names[best_match_index]
                        
                        # Create person folder
                        person_folder = os.path.join(output_dir, name)
                        if not os.path.exists(person_folder):
                            os.makedirs(person_folder)
                        
                        # Copy file
                        dest_path = os.path.join(person_folder, file)
                        shutil.copy(file_path, dest_path)
                        
                        if name == "Unknown":
                            unknown_count += 1
                        else:
                            organized_count += 1
                            
                except Exception as e:
                    print(f"Lỗi xử lý {file}: {e}")
        
        message = f"✅ Đã tổ chức:\n- {organized_count} ảnh có tên\n- {unknown_count} ảnh chưa xác định\n\nKết quả trong thư mục 'organized_photos'"
        self.root.after(0, lambda: messagebox.showinfo("Hoàn thành", message))
        self.root.after(0, lambda: self.update_status(f"Đã tổ chức {organized_count + unknown_count} ảnh"))
        
    def manage_faces(self):
        """Quản lý khuôn mặt đã đăng ký"""
        self.clear_right_panel()
        
        # Đánh dấu đang ở chế độ quản lý
        self.is_managing_faces = True
        
        title = tk.Label(
            self.right_panel,
            text="⚙️ Quản lý khuôn mặt",
            font=("Arial", 16, "bold"),
            bg="white"
        )
        title.pack(pady=20)
        
        # Info label - sẽ được cập nhật liên tục
        self.manage_info_label = tk.Label(
            self.right_panel,
            text=f"Tổng số: {len(self.person_encodings)} người | {len(self.known_face_encodings)} ảnh",
            font=("Arial", 10),
            bg="white",
            fg="#7f8c8d"
        )
        self.manage_info_label.pack()
        
        # Listbox với scrollbar
        list_frame = tk.Frame(self.right_panel, bg="white")
        list_frame.pack(pady=10, fill=tk.BOTH, expand=True, padx=20)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.face_listbox = tk.Listbox(
            list_frame,
            font=("Arial", 11),
            yscrollcommand=scrollbar.set,
            height=15
        )
        self.face_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.face_listbox.yview)
        
        # Load danh sách với số lượng ảnh
        self.refresh_face_list()
        
        # Buttons
        btn_frame = tk.Frame(self.right_panel, bg="white")
        btn_frame.pack(pady=10)
        
        btn_view = tk.Button(
            btn_frame,
            text="👁️ Xem ảnh",
            font=("Arial", 11),
            bg="#1abc9c",
            fg="white",
            width=12,
            command=self.view_person_images
        )
        btn_view.pack(side=tk.LEFT, padx=5)
        
        btn_add = tk.Button(
            btn_frame,
            text="➕ Thêm ảnh",
            font=("Arial", 11),
            bg="#3498db",
            fg="white",
            width=12,
            command=self.add_more_images
        )
        btn_add.pack(side=tk.LEFT, padx=5)
        
        btn_edit = tk.Button(
            btn_frame,
            text="📝 Sửa thông tin",
            font=("Arial", 11),
            bg="#9b59b6",
            fg="white",
            width=12,
            command=self.edit_person_info
        )
        btn_edit.pack(side=tk.LEFT, padx=5)
        
        btn_rename = tk.Button(
            btn_frame,
            text="✏️ Đổi tên",
            font=("Arial", 11),
            bg="#f39c12",
            fg="white",
            width=12,
            command=self.rename_face
        )
        btn_rename.pack(side=tk.LEFT, padx=5)
        
        btn_delete = tk.Button(
            btn_frame,
            text="🗑️ Xóa",
            font=("Arial", 11),
            bg="#e74c3c",
            fg="white",
            width=12,
            command=self.delete_face
        )
        btn_delete.pack(side=tk.LEFT, padx=5)
        
        # Bắt đầu auto-refresh
        self.auto_refresh_manage_faces()
    
    def refresh_face_list(self):
        """Refresh danh sách khuôn mặt"""
        if not hasattr(self, 'face_listbox'):
            return
        
        # Lưu lựa chọn hiện tại
        current_selection = None
        if self.face_listbox.curselection():
            current_selection = self.face_listbox.get(self.face_listbox.curselection()[0])
        
        # Xóa danh sách cũ
        self.face_listbox.delete(0, tk.END)
        
        # Load lại data
        self.load_known_faces()
        
        # Cập nhật info label
        if hasattr(self, 'manage_info_label'):
            self.manage_info_label.config(
                text=f"Tổng số: {len(self.person_encodings)} người"
            )
        
        # Thêm lại danh sách với CHỈ TÊN
        for person_name in sorted(self.person_encodings.keys()):
            self.face_listbox.insert(tk.END, person_name)
        
        # Khôi phục lựa chọn
        if current_selection:
            for i in range(self.face_listbox.size()):
                if self.face_listbox.get(i) == current_selection:
                    self.face_listbox.selection_set(i)
                    self.face_listbox.see(i)
                    break
    
    def auto_refresh_manage_faces(self):
        """Tự động refresh danh sách mỗi 2 giây"""
        if hasattr(self, 'is_managing_faces') and self.is_managing_faces:
            self.refresh_face_list()
            # Lặp lại sau 2 giây
            self.root.after(2000, self.auto_refresh_manage_faces)
    
    def view_person_images(self):
        """Mở folder chứa ảnh và video của người được chọn"""
        selection = self.face_listbox.curselection()
        if selection:
            person_name = self.face_listbox.get(selection[0])
            
            person_folder = os.path.join("faces", person_name)
            
            # Kiểm tra folder có tồn tại không
            if not os.path.exists(person_folder):
                messagebox.showwarning("Cảnh báo", f"Không tìm thấy folder của {person_name}!")
                return
            
            # Mở folder bằng File Explorer
            import subprocess
            try:
                # Windows
                subprocess.Popen(f'explorer "{os.path.abspath(person_folder)}"')
                self.update_status(f"Đã mở folder: {person_folder}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể mở folder:\n{str(e)}")
        else:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một người!")
    
    def add_more_images(self):
        """Thêm ảnh cho người đã có"""
        selection = self.face_listbox.curselection()
        if selection:
            display_text = self.face_listbox.get(selection[0])
            person_name = display_text.split(" (")[0]
            
            file_paths = filedialog.askopenfilenames(
                title=f"Chọn ảnh để thêm cho {person_name}",
                filetypes=[("Image files", "*.jpg *.jpeg *.png")]
            )
            
            if file_paths:
                person_folder = os.path.join("faces", person_name)
                if not os.path.exists(person_folder):
                    os.makedirs(person_folder)
                
                # Di chuyển ảnh cũ nếu có (cấu trúc cũ)
                old_files = [f for f in os.listdir("faces") 
                           if os.path.isfile(os.path.join("faces", f)) and 
                           os.path.splitext(f)[0] == person_name]
                for old_file in old_files:
                    shutil.move(os.path.join("faces", old_file), 
                              os.path.join(person_folder, old_file))
                
                # Đếm ảnh hiện có
                existing_count = len([f for f in os.listdir(person_folder) 
                                    if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
                
                added_count = 0
                for file_path in file_paths:
                    ext = os.path.splitext(file_path)[1]
                    dest_path = os.path.join(person_folder, 
                                           f"{person_name}_{existing_count + added_count + 1}{ext}")
                    shutil.copy(file_path, dest_path)
                    added_count += 1
                
                messagebox.showinfo("Thành công", 
                                  f"✅ Đã thêm {added_count} ảnh cho {person_name}\n"
                                  f"Tổng số ảnh: {existing_count + added_count}")
                self.load_known_faces()
                self.manage_faces()
        else:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một người!")
    
    def rename_face(self):
        """Đổi tên khuôn mặt"""
        selection = self.face_listbox.curselection()
        if selection:
            display_text = self.face_listbox.get(selection[0])
            old_name = display_text.split(" (")[0]
            new_name = simpledialog.askstring("Đổi tên", f"Nhập tên mới cho '{old_name}':")
            
            if new_name:
                old_folder = os.path.join("faces", old_name)
                new_folder = os.path.join("faces", new_name)
                
                # Kiểm tra folder tồn tại
                if os.path.exists(old_folder):
                    os.rename(old_folder, new_folder)
                    messagebox.showinfo("Thành công", f"✅ Đã đổi tên: {old_name} → {new_name}")
                else:
                    # Cấu trúc cũ - tìm file
                    renamed = False
                    for file in os.listdir("faces"):
                        if os.path.splitext(file)[0] == old_name:
                            old_path = os.path.join("faces", file)
                            if os.path.isfile(old_path):
                                # Tạo folder mới và di chuyển
                                if not os.path.exists(new_folder):
                                    os.makedirs(new_folder)
                                ext = os.path.splitext(file)[1]
                                new_path = os.path.join(new_folder, f"{new_name}_1{ext}")
                                shutil.move(old_path, new_path)
                                renamed = True
                                break
                    
                    if renamed:
                        messagebox.showinfo("Thành công", f"✅ Đã đổi tên: {old_name} → {new_name}")
                    else:
                        messagebox.showerror("Lỗi", "Không tìm thấy dữ liệu!")
                        return
                
                self.load_known_faces()
                self.manage_faces()
        else:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một người!")
            
    def delete_face(self):
        """Xóa khuôn mặt"""
        selection = self.face_listbox.curselection()
        if selection:
            display_text = self.face_listbox.get(selection[0])
            name = display_text.split(" (")[0]
            
            confirm = messagebox.askyesno("Xác nhận", 
                                         f"Bạn có chắc muốn xóa '{name}' và tất cả ảnh của người này?")
            
            if confirm:
                deleted = False
                
                # Xóa folder
                person_folder = os.path.join("faces", name)
                if os.path.exists(person_folder):
                    shutil.rmtree(person_folder)
                    deleted = True
                else:
                    # Xóa file cũ (cấu trúc cũ)
                    for file in os.listdir("faces"):
                        file_path = os.path.join("faces", file)
                        if os.path.isfile(file_path) and os.path.splitext(file)[0] == name:
                            os.remove(file_path)
                            deleted = True
                            break
                
                if deleted:
                    messagebox.showinfo("Thành công", f"✅ Đã xóa: {name}")
                    self.load_known_faces()
                    self.manage_faces()
                else:
                    messagebox.showerror("Lỗi", "Không tìm thấy dữ liệu!")
        else:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một người!")
    
    def edit_person_info(self):
        """Sửa thông tin cá nhân trong database"""
        selection = self.face_listbox.curselection()
        if not selection:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một người!")
            return
        
        display_text = self.face_listbox.get(selection[0])
        folder_name = display_text.split(" (")[0]
        
        # Lấy thông tin hiện tại từ database
        current_info = self.db.get_person_info(folder_name)
        
        if not current_info:
            messagebox.showerror("Lỗi", f"Không tìm thấy thông tin của '{folder_name}' trong database!")
            return
        
        # Tạo dialog chỉnh sửa
        dialog = tk.Toplevel(self.root)
        dialog.title(f"📝 Chỉnh sửa thông tin - {folder_name}")
        dialog.geometry("500x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Title
        title = tk.Label(
            dialog,
            text=f"📝 CHỈNH SỬA THÔNG TIN\n{folder_name}",
            font=("Arial", 14, "bold"),
            bg="#9b59b6",
            fg="white",
            pady=15
        )
        title.pack(fill=tk.X)
        
        # Form frame
        form_frame = tk.Frame(dialog, padx=30, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Folder name (read-only)
        tk.Label(form_frame, text="📁 Folder Name:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=5)
        folder_label = tk.Label(form_frame, text=folder_name, font=("Arial", 11), fg="blue")
        folder_label.grid(row=0, column=1, sticky="w", pady=5, padx=10)
        
        # Họ tên
        tk.Label(form_frame, text="👤 Họ và tên: *", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w", pady=5)
        name_entry = tk.Entry(form_frame, font=("Arial", 11), width=30)
        name_entry.insert(0, current_info.get("user_name", ""))
        name_entry.grid(row=1, column=1, pady=5, padx=10)
        
        # Giới tính
        tk.Label(form_frame, text="⚧ Giới tính:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="w", pady=5)
        gender_var = tk.StringVar(value=current_info.get("gender", ""))
        gender_frame = tk.Frame(form_frame)
        gender_frame.grid(row=2, column=1, sticky="w", pady=5, padx=10)
        
        tk.Radiobutton(gender_frame, text="Nam", variable=gender_var, value="Nam", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(gender_frame, text="Nữ", variable=gender_var, value="Nữ", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(gender_frame, text="Khác", variable=gender_var, value="Khác", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        
        # Năm sinh
        tk.Label(form_frame, text="🎂 Năm sinh:", font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=5)
        birth_entry = tk.Entry(form_frame, font=("Arial", 11), width=30)
        birth_entry.insert(0, current_info.get("birth_year", ""))
        birth_entry.grid(row=3, column=1, pady=5, padx=10)
        
        # Quê quán
        tk.Label(form_frame, text="🏠 Quê quán:", font=("Arial", 10, "bold")).grid(row=4, column=0, sticky="w", pady=5)
        hometown_entry = tk.Entry(form_frame, font=("Arial", 11), width=30)
        hometown_entry.insert(0, current_info.get("hometown", ""))
        hometown_entry.grid(row=4, column=1, pady=5, padx=10)
        
        # Nơi sinh sống
        tk.Label(form_frame, text="📍 Nơi sinh sống:", font=("Arial", 10, "bold")).grid(row=5, column=0, sticky="w", pady=5)
        residence_entry = tk.Entry(form_frame, font=("Arial", 11), width=30)
        residence_entry.insert(0, current_info.get("residence", ""))
        residence_entry.grid(row=5, column=1, pady=5, padx=10)
        
        # Thông tin metadata
        tk.Label(form_frame, text="", font=("Arial", 1)).grid(row=6, column=0, pady=10)
        
        meta_frame = tk.LabelFrame(form_frame, text="ℹ️ Thông tin khác", font=("Arial", 10, "bold"), padx=10, pady=10)
        meta_frame.grid(row=7, column=0, columnspan=2, sticky="ew", pady=10)
        
        tk.Label(meta_frame, text=f"📊 Số embeddings: {current_info.get('embedding_count', 0)}", font=("Arial", 9)).pack(anchor="w", pady=2)
        tk.Label(meta_frame, text=f"📅 Tạo lúc: {current_info.get('created_at', 'N/A')}", font=("Arial", 9)).pack(anchor="w", pady=2)
        tk.Label(meta_frame, text=f"🔄 Cập nhật: {current_info.get('updated_at', 'N/A')}", font=("Arial", 9)).pack(anchor="w", pady=2)
        
        # Buttons
        def save_changes():
            new_name = name_entry.get().strip()
            
            if not new_name:
                messagebox.showerror("Lỗi", "Họ tên không được để trống!", parent=dialog)
                return
            
            # Cập nhật thông tin - Sử dụng keyword arguments
            result = self.db.update_person_info(
                folder_name,
                user_name=new_name,
                gender=gender_var.get(),
                birth_year=birth_entry.get().strip(),
                hometown=hometown_entry.get().strip(),
                residence=residence_entry.get().strip()
            )
            
            if result["success"]:
                messagebox.showinfo("Thành công", f"✅ Đã cập nhật thông tin cho '{folder_name}'!", parent=dialog)
                dialog.destroy()
                self.load_known_faces()
                self.manage_faces()
            else:
                messagebox.showerror("Lỗi", f"❌ {result.get('message', 'Lỗi không xác định')}", parent=dialog)
        
        btn_frame = tk.Frame(dialog, pady=20)
        btn_frame.pack()
        
        btn_save = tk.Button(
            btn_frame,
            text="💾 Lưu thay đổi",
            font=("Arial", 11, "bold"),
            bg="#27ae60",
            fg="white",
            width=15,
            command=save_changes
        )
        btn_save.pack(side=tk.LEFT, padx=10)
        
        btn_cancel = tk.Button(
            btn_frame,
            text="❌ Hủy",
            font=("Arial", 11),
            bg="#95a5a6",
            fg="white",
            width=15,
            command=dialog.destroy
        )
        btn_cancel.pack(side=tk.LEFT, padx=10)
            
    def recognize_from_webcam(self):
        """Nhận diện real-time từ webcam"""
        self.clear_right_panel()
        
        title = tk.Label(
            self.right_panel,
            text="📹 Nhận diện từ Webcam",
            font=("Arial", 14, "bold"),
            bg="white"
        )
        title.pack(pady=10)
        
        # Video frame
        self.video_label = tk.Label(self.right_panel, bg="black")
        self.video_label.pack(pady=10)
        
        # Button frame
        btn_frame = tk.Frame(self.right_panel)
        btn_frame.pack(pady=10)
        
        # Record button
        self.is_recording = False
        self.video_writer = None
        self.record_btn = tk.Button(
            btn_frame,
            text="⏺️ Ghi video",
            font=("Arial", 11),
            bg="#27ae60",
            fg="white",
            width=15,
            command=self.toggle_recording
        )
        self.record_btn.pack(side=tk.LEFT, padx=5)
        
        # Stop button
        btn_stop = tk.Button(
            btn_frame,
            text="❌ Dừng",
            font=("Arial", 11),
            bg="#e74c3c",
            fg="white",
            width=15,
            command=self.stop_webcam_recognition
        )
        btn_stop.pack(side=tk.LEFT, padx=5)
        
        # Start webcam
        self.is_capturing = True
        self.video_capture = cv2.VideoCapture(0)
        self.process_current_frame = True
        self.update_webcam_recognition()
        
    def update_webcam_recognition(self):
        """Cập nhật video feed với nhận diện"""
        if self.is_capturing and self.video_capture.isOpened():
            ret, frame = self.video_capture.read()
            if ret:
                # Process every other frame
                if self.process_current_frame:
                    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                    
                    face_locations = face_recognition.face_locations(rgb_small_frame)
                    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                    
                    self.face_names = []
                    self.face_infos = []  # Lưu thông tin đầy đủ
                    for face_encoding in face_encodings:
                        matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                        folder_name = "Unknown"
                        info_lines = []
                        
                        if self.known_face_encodings:
                            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                            best_match_index = np.argmin(face_distances)
                            if matches[best_match_index]:
                                folder_name = self.known_face_names[best_match_index]
                                
                                # Lấy thông tin đầy đủ từ database
                                if folder_name in self.face_metadata:
                                    metadata = self.face_metadata[folder_name]
                                    
                                    # Hiển thị TẤT CẢ thông tin, mỗi loại 1 dòng theo hàng dọc
                                    # Dòng 1: Tên
                                    if metadata.get('user_name'):
                                        info_lines.append(str(metadata['user_name']))
                                    
                                    # Dòng 2: Giới tính
                                    if metadata.get("gender"):
                                        info_lines.append(f"GT: {metadata['gender']}")
                                    
                                    # Dòng 3: Năm sinh
                                    if metadata.get("birth_year"):
                                        info_lines.append(f"NS: {metadata['birth_year']}")
                                    
                                    # Dòng 4: Quê quán
                                    if metadata.get("hometown"):
                                        info_lines.append(f"QQ: {metadata['hometown']}")
                                    
                                    # Dòng 5: Nơi sinh sống
                                    if metadata.get("residence"):
                                        info_lines.append(f"O: {metadata['residence']}")
                                    
                                    # Nếu không có thông tin gì, hiện tên folder
                                    if not info_lines:
                                        info_lines = [str(folder_name)]
                                else:
                                    info_lines = [str(folder_name)]
                        
                        if not info_lines:
                            info_lines = ["Unknown"]
                        
                        self.face_names.append(folder_name)
                        self.face_infos.append(info_lines)
                    
                    self.face_locations = face_locations
                
                self.process_current_frame = not self.process_current_frame
                
                # Draw results with full info
                if hasattr(self, 'face_infos') and hasattr(self, 'face_locations'):
                    # Convert frame sang PIL để vẽ Unicode text
                    from PIL import Image as PILImage, ImageDraw, ImageFont
                    pil_frame = PILImage.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    draw = ImageDraw.Draw(pil_frame)
                    
                    try:
                        font_pil = ImageFont.truetype("arial.ttf", 15)
                    except:
                        font_pil = ImageFont.load_default()
                    
                    for (top, right, bottom, left), info_lines in zip(self.face_locations, self.face_infos):
                        # Scale coordinates
                        top *= 4
                        right *= 4
                        bottom *= 4
                        left *= 4
                        
                        # Draw rectangle around face
                        draw.rectangle([(left, top), (right, bottom)], outline=(0, 255, 0), width=2)
                        
                        # Draw info box với PIL
                        line_height = 22
                        y_offset = top - (len(info_lines) * line_height) - 10
                        
                        if y_offset < 0:
                            y_offset = bottom + 10
                        
                        # Draw each info line
                        for i, info_line in enumerate(info_lines):
                            # Đảm bảo info_line là string
                            info_text = str(info_line) if info_line is not None else ""
                            
                            if not info_text.strip():
                                continue
                            
                            y_pos = y_offset + (i * line_height)
                            
                            # Đo kích thước text
                            try:
                                bbox = draw.textbbox((0, 0), info_text, font=font_pil)
                                text_width = bbox[2] - bbox[0]
                                text_height = bbox[3] - bbox[1]
                            except:
                                text_width = len(info_text) * 8
                                text_height = 15
                            
                            # Background
                            draw.rectangle(
                                [(left, y_pos - 2), (left + text_width + 10, y_pos + text_height + 2)],
                                fill=(0, 255, 0)
                            )
                            
                            # Text
                            draw.text((left + 5, y_pos), info_text, font=font_pil, fill=(0, 0, 0))
                    
                    # Convert PIL frame back to OpenCV
                    frame = cv2.cvtColor(np.array(pil_frame), cv2.COLOR_RGB2BGR)
                
                # Lưu frame hiện tại để có thể save sau này
                self.current_recognition_frame = frame.copy()
                
                # Nếu đang recording, thu thập frames vào list
                if hasattr(self, 'is_recording') and self.is_recording:
                    if not hasattr(self, 'recognition_video_frames'):
                        self.recognition_video_frames = []
                    self.recognition_video_frames.append(frame.copy())
                
                # Display
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img = img.resize((640, 480), Image.Resampling.LANCZOS)
                imgtk = ImageTk.PhotoImage(image=img)
                
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
                
            self.root.after(10, self.update_webcam_recognition)
    
    def toggle_recording(self):
        """Bật/tắt ghi video"""
        if not self.is_recording:
            # Bắt đầu ghi
            self.start_recording()
        else:
            # Dừng ghi
            self.stop_recording()
    
    def start_recording(self):
        """Bắt đầu ghi video - thu thập frames"""
        if not hasattr(self, 'current_recognition_frame') or self.current_recognition_frame is None:
            messagebox.showwarning("Cảnh báo", "⚠️ Chưa có frame từ webcam!")
            return
        
        # Khởi tạo list để thu thập frames
        self.recognition_video_frames = []
        
        self.is_recording = True
        self.record_btn.config(text="⏹️ Dừng ghi", bg="#e74c3c")
        self.update_status("🔴 Đang ghi video nhận diện...")
    
    def stop_recording(self):
        """Dừng ghi video và lưu toàn bộ frames sang recognized/"""
        self.is_recording = False
        self.record_btn.config(text="⏺️ Ghi video", bg="#27ae60")
        
        # Kiểm tra có frames không
        if not hasattr(self, 'recognition_video_frames') or len(self.recognition_video_frames) == 0:
            messagebox.showwarning("Cảnh báo", "⚠️ Không có frame nào được ghi!")
            self.update_status("Sẵn sàng")
            return
        
        from datetime import datetime
        import shutil
        
        # Tạo folder temp
        self.create_temp_folder()
        
        # Tạo tên file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_video_path = f"temp/temp_webcam_{timestamp}.mp4"
        final_path = f"recognized/webcam_recognized_{timestamp}.mp4"
        
        try:
            # Lấy kích thước frame
            frame_height, frame_width = self.recognition_video_frames[0].shape[:2]
            
            # Tạo VideoWriter
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(temp_video_path, fourcc, 20.0, (frame_width, frame_height))
            
            # Ghi TẤT CẢ frames vào video
            for frame in self.recognition_video_frames:
                video_writer.write(frame)
            
            video_writer.release()
            
            # Di chuyển từ temp sang recognized
            shutil.move(temp_video_path, final_path)
            
            file_size = os.path.getsize(final_path) / (1024 * 1024)  # MB
            duration = len(self.recognition_video_frames) / 20.0  # Thời lượng (giây)
            
            messagebox.showinfo(
                "Thành công",
                f"✅ Đã lưu video nhận diện!\n\n"
                f"📁 Vị trí: {final_path}\n"
                f"📦 Kích thước: {file_size:.2f} MB\n"
                f"🎬 Frames: {len(self.recognition_video_frames)}\n"
                f"⏱️ Thời lượng: {duration:.1f}s"
            )
            self.update_status(f"✅ Đã lưu video: {final_path}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"❌ Lỗi khi lưu video:\n{str(e)}")
        finally:
            # Xóa folder temp và frames
            self.remove_temp_folder()
            self.recognition_video_frames = []


            
    def stop_webcam_recognition(self):
        """Dừng nhận diện webcam"""
        # Nếu đang recording, dừng recording trước
        if hasattr(self, 'is_recording') and self.is_recording:
            self.stop_recording()
        
        self.is_capturing = False
        if self.video_capture:
            self.video_capture.release()
        self.show_welcome_screen()
        
    def reload_data(self):
        """Tải lại dữ liệu khuôn mặt"""
        self.load_known_faces()
        self.update_status(f"Đã tải lại {len(self.known_face_encodings)} khuôn mặt")
        messagebox.showinfo("Thành công", f"✅ Đã tải lại {len(self.known_face_encodings)} khuôn mặt")


def main():
    root = tk.Tk()
    app = FaceRecognitionGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
