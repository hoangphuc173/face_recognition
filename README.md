# Face Recognition System - AWS Serverless

A production-ready face recognition system using AWS Serverless architecture with dual frontends (Desktop/Tauri and Web/Next.js).

## Architecture

- **Backend**: FastAPI on AWS Lambda
- **Authentication**: AWS Cognito with JWT and RBAC (Admin/Staff/Guest)
- **Storage**: S3 (KMS encrypted, Glacier lifecycle)
- **Database**: DynamoDB (KMS encrypted, TTL for logs)
- **AI/ML**: AWS Rekognition (Face Collection, IndexFaces, SearchFaces)
- **Infrastructure**: AWS CDK (TypeScript)
- **API**: API Gateway with JWT Authorizer, throttling (100/200 req/s)

## Project Structure

```
├── backend/           # Backend Lambda functions & API
│   ├── src/          # Source code (auth, enroll, identify, people)
│   └── tests/        # Backend tests
├── frontend/         # Frontend applications
│   ├── web/         # Next.js web app (AWS Amplify)
│   └── desktop/     # Tauri desktop app
├── infrastructure/   # AWS CDK infrastructure as code
├── scripts/         # Organized scripts
│   ├── local/      # Local development scripts
│   ├── cloud/      # Cloud/AWS operations
│   ├── deployment/ # Full deployment
│   ├── utilities/  # Helper tools
│   └── testing/    # Test scripts
├── environments/    # Environment configurations
│   ├── local/      # Local dev configs
│   └── cloud/      # Cloud/production configs
└── docs/           # Documentation
    ├── FOLDER_STRUCTURE.md      # Detailed folder structure
    ├── LOCAL_DEVELOPMENT.md     # Local development guide
    ├── CLOUD_DEPLOYMENT.md      # Cloud deployment guide
    └── AMPLIFY_DEPLOYMENT.md    # Amplify-specific guide
```

See [`docs/FOLDER_STRUCTURE.md`](docs/FOLDER_STRUCTURE.md) for complete folder structure details.

## Features

### Backend
- ✅ **Auth**: Cognito integration, JWT tokens, RBAC (Admin/Staff/Guest)
- ✅ **Enroll**: Image validation, preprocessing, S3 upload, Rekognition indexing, DynamoDB storage
- ✅ **Identify**: Frame processing, face search (90-95% threshold), confidence + bbox + user_id
- ✅ **People API**: Full CRUD (Create via Enroll, Read, Update, Delete)
- ✅ **Preprocessing**: 
  - Resize to 640×480
  - Brightness check (50-205)
  - Contrast check (>20)
  - Blur detection
  - **Face size validation (>=100x100 pixels)**
  - **Head pose validation (<30° Pitch/Roll/Yaw)**
- ✅ **Anti-spoofing**: Rule-based quality checks using Rekognition DetectFaces

### Infrastructure
- ✅ **KMS Encryption**: All S3 and DynamoDB tables encrypted with customer-managed keys
- ✅ **JWT Authorizer**: Cognito User Pool authorizer on all protected endpoints
- ✅ **Throttling**: 100 req/s rate limit, 200 burst limit
- ✅ **Validation**: Request body and parameter validation
- ✅ **Lifecycle**: S3 → Glacier after 30 days, deletion after 90 days
- ✅ **IAM**: Least privilege policies per Lambda function
- ✅ **TTL**: AccessLogs auto-deletion via DynamoDB TTL

### Frontends
- ✅ **Desktop (Tauri)**: Real-time camera, enrollment, people management
- ✅ **Web (Next.js)**: Login, identify, people, enroll, access logs pages

---

## Quick Start

### Local Development

**Backend Only**:
```bash
scripts\local\backend\start-backend-only.bat
# Access API at http://localhost:5555
```

**Web Frontend** (requires backend running):
```bash
scripts\local\frontend\start-frontend.bat
# Access at http://localhost:3000
```

**Desktop App** (requires backend running):
```bash
scripts\local\frontend\start-desktop-app.bat
```

**Full Local System** (backend + web):
```bash
scripts\local\start-full-local-system.bat
```

See [`docs/LOCAL_DEVELOPMENT.md`](docs/LOCAL_DEVELOPMENT.md) for detailed local setup guide.

### Cloud Deployment

**Deploy Infrastructure**:
```bash
scripts\cloud\setup-aws.ps1
```

**Deploy Lambda Functions**:
```bash
scripts\cloud\deploy-lambda-quick.ps1
```

**Deploy Frontend to Amplify**: See [`docs/AMPLIFY_DEPLOYMENT.md`](docs/AMPLIFY_DEPLOYMENT.md)

**Deploy Everything**:
```bash
scripts\deployment\deploy-all.ps1
```

See [`docs/CLOUD_DEPLOYMENT.md`](docs/CLOUD_DEPLOYMENT.md) for complete deployment guide.

---

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/token` | POST | ❌ | Login, returns JWT + Role + Groups |
| `/enroll` | POST | ✅ | Upload face image for enrollment |
| `/identify` | POST | ✅ | Identify face from image |
| `/people` | GET | ✅ | List all users |
| `/people/{user_id}` | PUT | ✅ | Update user details |
| `/people/{user_id}` | DELETE | ✅ | Delete user |
| `/logs` | GET | ✅ | Retrieve access logs |

## Security

- **Encryption at Rest**: KMS for S3 and DynamoDB
- **Encryption in Transit**: HTTPS/TLS via API Gateway
- **Authentication**: JWT tokens from Cognito
# Face Recognition System - AWS Serverless

A production-ready face recognition system using AWS Serverless architecture with dual frontends (Desktop/Tauri and Web/Next.js).

## Architecture

- **Backend**: FastAPI on AWS Lambda
- **Authentication**: AWS Cognito with JWT and RBAC (Admin/Staff/Guest)
- **Storage**: S3 (KMS encrypted, Glacier lifecycle)
- **Database**: DynamoDB (KMS encrypted, TTL for logs)
- **AI/ML**: AWS Rekognition (Face Collection, IndexFaces, SearchFaces)
- **Infrastructure**: AWS CDK (TypeScript)
- **API**: API Gateway with JWT Authorizer, throttling (100/200 req/s)

## Project Structure

```
├── backend/           # Backend Lambda functions & API
│   ├── src/          # Source code (auth, enroll, identify, people)
│   └── tests/        # Backend tests
├── frontend/         # Frontend applications
│   ├── web/         # Next.js web app (AWS Amplify)
│   └── desktop/     # Tauri desktop app
├── infrastructure/   # AWS CDK infrastructure as code
├── scripts/         # Organized scripts
│   ├── local/      # Local development scripts
│   ├── cloud/      # Cloud/AWS operations
│   ├── deployment/ # Full deployment
│   ├── utilities/  # Helper tools
│   └── testing/    # Test scripts
├── environments/    # Environment configurations
│   ├── local/      # Local dev configs
│   └── cloud/      # Cloud/production configs
└── docs/           # Documentation
    ├── FOLDER_STRUCTURE.md      # Detailed folder structure
    ├── LOCAL_DEVELOPMENT.md     # Local development guide
    ├── CLOUD_DEPLOYMENT.md      # Cloud deployment guide
    └── AMPLIFY_DEPLOYMENT.md    # Amplify-specific guide
```

See [`docs/FOLDER_STRUCTURE.md`](docs/FOLDER_STRUCTURE.md) for complete folder structure details.

## Features

### Backend
- ✅ **Auth**: Cognito integration, JWT tokens, RBAC (Admin/Staff/Guest)
- ✅ **Enroll**: Image validation, preprocessing, S3 upload, Rekognition indexing, DynamoDB storage
- ✅ **Identify**: Frame processing, face search (90-95% threshold), confidence + bbox + user_id
- ✅ **People API**: Full CRUD (Create via Enroll, Read, Update, Delete)
- ✅ **Preprocessing**: 
  - Resize to 640×480
  - Brightness check (50-205)
  - Contrast check (>20)
  - Blur detection
  - **Face size validation (>=100x100 pixels)**
  - **Head pose validation (<30° Pitch/Roll/Yaw)**
- ✅ **Anti-spoofing**: Rule-based quality checks using Rekognition DetectFaces

### Infrastructure
- ✅ **KMS Encryption**: All S3 and DynamoDB tables encrypted with customer-managed keys
- ✅ **JWT Authorizer**: Cognito User Pool authorizer on all protected endpoints
- ✅ **Throttling**: 100 req/s rate limit, 200 burst limit
- ✅ **Validation**: Request body and parameter validation
- ✅ **Lifecycle**: S3 → Glacier after 30 days, deletion after 90 days
- ✅ **IAM**: Least privilege policies per Lambda function
- ✅ **TTL**: AccessLogs auto-deletion via DynamoDB TTL

### Frontends
- ✅ **Desktop (Tauri)**: Real-time camera, enrollment, people management
- ✅ **Web (Next.js)**: Login, identify, people, enroll, access logs pages

---

## Quick Start

### Local Development

**Backend Only**:
```bash
scripts\local\backend\start-backend-only.bat
# Access API at http://localhost:5555
```

**Web Frontend** (requires backend running):
```bash
scripts\local\frontend\start-frontend.bat
# Access at http://localhost:3000
```

**Desktop App** (requires backend running):
```bash
scripts\local\frontend\start-desktop-app.bat
```

**Full Local System** (backend + web):
```bash
scripts\local\start-full-local-system.bat
```

See [`docs/LOCAL_DEVELOPMENT.md`](docs/LOCAL_DEVELOPMENT.md) for detailed local setup guide.

### Cloud Deployment

**Deploy Infrastructure**:
```bash
scripts\cloud\setup-aws.ps1
```

**Deploy Lambda Functions**:
```bash
scripts\cloud\deploy-lambda-quick.ps1
```

**Deploy Frontend to Amplify**: See [`docs/AMPLIFY_DEPLOYMENT.md`](docs/AMPLIFY_DEPLOYMENT.md)

**Deploy Everything**:
```bash
scripts\deployment\deploy-all.ps1
```

See [`docs/CLOUD_DEPLOYMENT.md`](docs/CLOUD_DEPLOYMENT.md) for complete deployment guide.

---

## API Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/token` | POST | ❌ | Login, returns JWT + Role + Groups |
| `/enroll` | POST | ✅ | Upload face image for enrollment |
| `/identify` | POST | ✅ | Identify face from image |
| `/people` | GET | ✅ | List all users |
| `/people/{user_id}` | PUT | ✅ | Update user details |
| `/people/{user_id}` | DELETE | ✅ | Delete user |
| `/logs` | GET | ✅ | Retrieve access logs |

## Security

- **Encryption at Rest**: KMS for S3 and DynamoDB
- **Encryption in Transit**: HTTPS/TLS via API Gateway
- **Authentication**: JWT tokens from Cognito
- **Authorization**: Role-based access control (Admin/Staff/Guest)
- **Least Privilege**: IAM policies scoped per Lambda function
- **Anti-spoofing**: Face quality checks (brightness, contrast, size, pose, sharpness)

---

## 📚 Documentation (Tài Liệu)

### 🇻🇳 Tiếng Việt (Vietnamese)

- **[Triển Khai Nhanh (Quick Start)](docs/AWS_DEPLOYMENT_QUICKSTART_VI.md)** - 🚀 Bắt đầu tại đây!
- **[Triển Khai Thủ Công (Console)](docs/AWS_MANUAL_DEPLOYMENT_CONSOLE_VI.md)** - 🖱️ Làm bằng giao diện web (Không code)
- **[Hướng Dẫn Xóa AWS (Cleanup)](docs/AWS_CLEANUP_GUIDE_VI.md)** - 🧹 Xóa tài nguyên cũ
- **[Triển Khai Hạ Tầng (Infrastructure)](docs/AWS_INFRASTRUCTURE_DEPLOYMENT_VI.md)** - Chi tiết CDK
- **[Triển Khai Backend (Lambda)](docs/AWS_LAMBDA_DEPLOYMENT_VI.md)** - Chi tiết Lambda
- **[Triển Khai Frontend (Amplify)](docs/AMPLIFY_DEPLOYMENT_VI.md)** - Chi tiết Web App
- **[Kiểm Thử & Xác Minh (Testing)](docs/AWS_TESTING_GUIDE_VI.md)** - Hướng dẫn test
- **[Xử Lý Sự Cố (Troubleshooting)](docs/AWS_TROUBLESHOOTING_VI.md)** - Sửa lỗi thường gặp
- **[Phát Triển Local](docs/LOCAL_DEVELOPMENT_VI.md)** - Chạy trên máy cá nhân
- **[Cấu Trúc Thư Mục](docs/FOLDER_STRUCTURE_VI.md)** - Giải thích source code

### 🇺🇸 English

- **[Folder Structure](docs/FOLDER_STRUCTURE.md)**
- **[Local Development](docs/LOCAL_DEVELOPMENT.md)**
- **[Cloud Deployment](docs/CLOUD_DEPLOYMENT.md)**
- **[Amplify Deployment](docs/AMPLIFY_DEPLOYMENT.md)**
- **[AWS Cleanup Guide](docs/AWS_CLEANUP_GUIDE.md)**
- **[AWS Infrastructure Deployment](docs/AWS_INFRASTRUCTURE_DEPLOYMENT.md)**
- **[AWS Lambda Deployment](docs/AWS_LAMBDA_DEPLOYMENT.md)**
- **[AWS Testing Guide](docs/AWS_TESTING_GUIDE.md)**
- **[AWS Troubleshooting](docs/AWS_TROUBLESHOOTING.md)**

## License
Proprietary
