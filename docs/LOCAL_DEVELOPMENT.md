# Local Development Guide

Hướng dẫn setup và chạy hệ thống face recognition trên local machine.

---

## Prerequisites

### Required Software

- **Python 3.11+**
- **Node.js 18+** and npm
- **Rust** (for desktop app)
- **Git**

### AWS Account (Optional for Local)

Bạn có thể test local mà không cần AWS, nhưng một số tính năng cần AWS services:
- Face recognition: AWS Rekognition
- User data: DynamoDB
- Image storage: S3

---

## Environment Setup

### 1. Backend Environment

Copy environment template:
```bash
# See environments/local/README.md for full guide
```

Create `.env.local` in root:
```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret

COGNITO_USER_POOL_ID=us-east-1_XXXXX
COGNITO_CLIENT_ID=XXXXXXXXX

S3_BUCKET_NAME=your-bucket
DYNAMODB_TABLE_NAME=face-recognition-users

LOCAL_MODE=true
DEBUG=true
```

### 2. Frontend Environment

For web (`frontend/web/.env.local`):
```bash
NEXT_PUBLIC_API_URL=http://localhost:5555
```

Desktop app reads from app settings.

---

## Running the System

### Option 1: Backend Only (API Development)

```bash
scripts\local\backend\start-backend-only.bat
```

- Starts FastAPI backend on `http://localhost:5555`
- Good for API development and testing
- Hot reload enabled

### Option 2: Web Frontend Development

Terminal 1 - Backend:
```bash
scripts\local\backend\start-backend-only.bat
```

Terminal 2 - Frontend:
```bash
scripts\local\frontend\start-frontend.bat
```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:5555`

### Option 3: Desktop App Development

Terminal 1 - Backend:
```bash
scripts\local\backend\start-backend-only.bat
```

Terminal 2 - Desktop:
```bash
scripts\local\frontend\start-desktop-app.bat
```

### Option 4: Full Local System (All in One)

```bash
scripts\local\start-full-local-system.bat
```

Starts both backend and web frontend automatically.

---

## Development Workflows

### Backend Development

1. Make changes to `backend/src/`
2. Backend auto-reloads (FastAPI hot reload)
3. Test via `http://localhost:5555/docs` (Swagger UI)

### Web Frontend Development

1. Make changes to `frontend/web/`
2. Next.js auto-reloads
3. View at `http://localhost:3000`

### Desktop App Development

1. Make changes to `frontend/desktop/src/`
2. Tauri auto-reloads (dev mode)
3. App window opens automatically

---

## Testing

### Test API Endpoints

Use Swagger UI:
```
http://localhost:5555/docs
```

Or use the test script:
```bash
scripts\testing\test-all.ps1
```

### Manual Testing

1. **Register**: Create new user with email
2. **Verify**: Use OTP code (check console logs for local)
3. **Login**: Get access token
4. **Enroll**: Upload face image
5. **Identify**: Test face recognition

---

## Debugging

### Backend Debugging

Enable debug mode in `.env.local`:
```bash
DEBUG=true
```

Run with debugger:
```bash
scripts\local\backend\debug-backend.bat
```

### Check Logs

Backend logs print to console with DEBUG=true.

### Common Issues

**Port already in use**:
```bash
# Backend (5555)
netstat -ano | findstr :5555
taskkill /PID <pid> /F

# Frontend (3000)
netstat -ano | findstr :3000
taskkill /PID <pid> /F
```

**AWS Credentials**:
- Verify `.env.local` has correct AWS credentials
- Test: `aws sts get-caller-identity`

**Dependencies**:
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend Web
cd frontend/web
npm install

# Frontend Desktop
cd frontend/desktop
npm install
```

---

## Hot Reload

- **Backend**: FastAPI auto-reloads on `.py` file changes
- **Web**: Next.js auto-reloads on file changes
- **Desktop**: Tauri auto-rebuilds on file changes (slower than web)

---

## Next Steps

- See `CLOUD_DEPLOYMENT.md` for deploying to AWS
- See `FOLDER_STRUCTURE.md` for project organization
- See `AMPLIFY_DEPLOYMENT.md` for Amplify deployment
