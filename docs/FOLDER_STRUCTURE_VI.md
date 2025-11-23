# Cấu Trúc Thư Mục Dự Án

Tài liệu này mô tả chi tiết cấu trúc thư mục của dự án Face Recognition.

---

## Tổng Quan

```
face_recognition/
├── backend/           # Mã nguồn Backend (Lambda functions)
├── frontend/          # Mã nguồn Frontend (Web & Desktop)
├── infrastructure/    # Mã nguồn Infrastructure (AWS CDK)
├── scripts/           # Các script tiện ích và deployment
├── environments/      # Cấu hình môi trường (Local & Cloud)
├── docs/              # Tài liệu dự án
└── legacy/            # Mã nguồn cũ (đã lưu trữ)
```

---

## Chi Tiết Thư Mục

### 1. `backend/`

Chứa mã nguồn Python cho các AWS Lambda functions.

- **`src/`**: Mã nguồn chính
  - **`auth/`**: Xử lý xác thực (Đăng ký, Đăng nhập, Verify)
  - **`enroll/`**: Xử lý đăng ký khuôn mặt (Upload S3, Index Rekognition)
  - **`identify/`**: Xử lý nhận diện khuôn mặt
  - **`people/`**: Quản lý thông tin người dùng (CRUD)
  - **`shared/`**: Các module dùng chung (Database, S3, Utils)
- **`tests/`**: Unit tests và Integration tests cho backend
- **`requirements.txt`**: Các thư viện Python cần thiết

### 2. `frontend/`

Chứa mã nguồn cho giao diện người dùng.

- **`web/`**: Ứng dụng Web (Next.js)
  - **`src/`**: Components, Pages, Hooks
  - **`public/`**: Static assets
  - **`amplify.yml`**: Cấu hình build cho AWS Amplify
- **`desktop/`**: Ứng dụng Desktop (Tauri + React)
  - **`src-tauri/`**: Mã nguồn Rust cho backend của desktop app
  - **`src/`**: Mã nguồn React cho giao diện

### 3. `infrastructure/`

Chứa mã nguồn Infrastructure as Code (IaC) sử dụng AWS CDK.

- **`lib/`**: Định nghĩa các Stacks và Constructs
  - **`main-stack.ts`**: Stack chính định nghĩa toàn bộ hạ tầng
- **`bin/`**: Entry point của ứng dụng CDK
- **`cdk.json`**: Cấu hình CDK

### 4. `scripts/`

Chứa các script để chạy, kiểm thử và triển khai hệ thống.

- **`local/`**: Script chạy môi trường local
  - **`backend/`**: Chạy backend server local
  - **`frontend/`**: Chạy frontend server local
  - **`start-full-local-system.bat`**: Chạy toàn bộ hệ thống local
- **`cloud/`**: Script thao tác với AWS
  - **`deploy-lambda-quick.ps1`**: Deploy nhanh Lambda functions
  - **`setup-aws.ps1`**: Thiết lập môi trường AWS ban đầu
- **`deployment/`**: Script triển khai đầy đủ
  - **`deploy-all.ps1`**: Triển khai toàn bộ hệ thống (Infra + Lambda + Frontend)
- **`utilities/`**: Các công cụ hỗ trợ
  - **`build-layer.ps1`**: Build Lambda Layer
  - **`verify-rbac.py`**: Kiểm tra phân quyền
- **`testing/`**: Script kiểm thử
  - **`test-all.ps1`**: Chạy tất cả các test

### 5. `environments/`

Chứa các file cấu hình môi trường.

- **`local/`**: Cấu hình cho phát triển local
  - **`README.md`**: Hướng dẫn cấu hình local
- **`cloud/`**: Cấu hình cho môi trường cloud/production
  - **`README.md`**: Hướng dẫn cấu hình cloud

### 6. `docs/`

Chứa tài liệu hướng dẫn chi tiết.

- **`FOLDER_STRUCTURE.md`**: Tài liệu này
- **`LOCAL_DEVELOPMENT.md`**: Hướng dẫn phát triển local
- **`CLOUD_DEPLOYMENT.md`**: Hướng dẫn triển khai Cloud
- **`AMPLIFY_DEPLOYMENT.md`**: Hướng dẫn triển khai Amplify
- **`AWS_*.md`**: Các hướng dẫn chi tiết về AWS (Cleanup, Infra, Lambda, Testing, Troubleshooting)

---

## Các File Quan Trọng Khác

- **`README.md`**: Tài liệu giới thiệu dự án, hướng dẫn nhanh
- **`.gitignore`**: Cấu hình loại trừ file khỏi Git
- **`package.json`**: Quản lý dependencies cho Node.js (root)

---

## Quy Ước Đặt Tên

- **Thư mục**: `kebab-case` (ví dụ: `user-profiles`, `api-gateway`)
- **File Python**: `snake_case` (ví dụ: `lambda_handler.py`, `user_service.py`)
- **File TypeScript/JavaScript**: `camelCase` hoặc `PascalCase` cho class/component
- **Lambda Functions**: `kebab-case` (ví dụ: `auth-handler`, `enroll-handler`)
- **DynamoDB Tables**: `PascalCase` (ví dụ: `UserProfiles`, `AuditLogs`)
- **S3 Buckets**: `kebab-case` (ví dụ: `face-recognition-images-prod`)
