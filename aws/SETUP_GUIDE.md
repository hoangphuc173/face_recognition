# Hướng dẫn Setup và Chạy Face Recognition System

## 1. CÀI ĐẶT AWS

### Bước 1.1: Cấu hình AWS Credentials
```powershell
# Kiểm tra AWS CLI đã cài chưa
aws --version

# Cấu hình credentials (nếu chưa có)
aws configure
# Nhập:
# - AWS Access Key ID
# - AWS Secret Access Key  
# - Default region: ap-southeast-1
# - Default output format: json
```

### Bước 1.2: Tạo S3 Bucket
```powershell
# Tạo bucket với tên unique
$bucketName = "face-recognition-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
aws s3 mb s3://$bucketName --region ap-southeast-1
Write-Host "Created bucket: $bucketName"

# Lưu tên bucket này để dùng sau
```

### Bước 1.3: Tạo Rekognition Collection
```powershell
# Tạo collection
aws rekognition create-collection --collection-id face-recognition-collection-dev --region ap-southeast-1
```

### Bước 1.4: Tạo DynamoDB Tables
```powershell
cd C:\Users\ADMIN\Downloads\facerecog\aws
python create_database.py
```

## 2. CẤU HÌNH FILE .ENV

Sửa file `aws/.env` với thông tin AWS của bạn:

```env
# AWS Region
AWS_REGION=ap-southeast-1

# S3 Bucket (thay bằng bucket name từ bước 1.2)
AWS_S3_BUCKET=face-recognition-20251119-215108-32ce1e86

# Rekognition Collection
AWS_REKOGNITION_COLLECTION=face-recognition-collection-dev

# DynamoDB Tables (giữ nguyên)
AWS_DYNAMODB_PEOPLE_TABLE=face-recognition-people-dev
AWS_DYNAMODB_EMBEDDINGS_TABLE=face-recognition-embeddings-dev
AWS_DYNAMODB_MATCHES_TABLE=face-recognition-matches-dev

# App Settings
DEBUG=true
LOG_LEVEL=INFO
```

## 3. CHẠY HỆ THỐNG

### Terminal 1: Khởi động API Server
```powershell
cd C:\Users\ADMIN\Downloads\facerecog\aws
python -m uvicorn backend.api.app:app --reload --host 127.0.0.1 --port 8888
```

### Terminal 2: Khởi động GUI Application
```powershell
cd C:\Users\ADMIN\Downloads\facerecog
python app/gui_app.py
```

## 4. KIỂM TRA HỆ THỐNG

### Kiểm tra API
```powershell
# Health check
curl http://127.0.0.1:8888/health

# Xem API docs
Start-Process "http://127.0.0.1:8888/docs"
```

### Kiểm tra Database
```powershell
# Liệt kê people
aws dynamodb scan --table-name face-recognition-people-dev --region ap-southeast-1

# Kiểm tra S3
aws s3 ls s3://YOUR_BUCKET_NAME/enrollments/

# Kiểm tra Rekognition collection
aws rekognition list-faces --collection-id face-recognition-collection-dev --region ap-southeast-1
```

## 5. RESET DATABASE (NẾU CẦN)

```powershell
cd C:\Users\ADMIN\Downloads\facerecog\aws
python reset_database.py
```

Chương trình sẽ hỏi xác nhận trước khi xóa:
- Tất cả records trong DynamoDB tables
- Tất cả faces trong Rekognition collection
- Tất cả files trong S3 bucket

## 6. XỬ LÝ LỖI THƯỜNG GẶP

### Lỗi: "AWS services not configured"
**Nguyên nhân**: File .env chưa được load đúng

**Giải pháp**:
```powershell
# Kiểm tra file .env có đúng vị trí không
Test-Path C:\Users\ADMIN\Downloads\facerecog\aws\.env

# Restart lại server để load .env mới
# Ctrl+C để dừng server, sau đó chạy lại lệnh uvicorn
```

### Lỗi: "Bucket does not exist"
**Nguyên nhân**: S3 bucket chưa được tạo hoặc tên bucket sai

**Giải pháp**:
```powershell
# Kiểm tra bucket có tồn tại không
aws s3 ls s3://YOUR_BUCKET_NAME

# Nếu không có, tạo lại bucket
aws s3 mb s3://YOUR_BUCKET_NAME --region ap-southeast-1
```

### Lỗi: "Collection does not exist"
**Nguyên nhân**: Rekognition collection chưa được tạo

**Giải pháp**:
```powershell
# Tạo collection
aws rekognition create-collection --collection-id face-recognition-collection-dev --region ap-southeast-1
```

### Lỗi: "Table does not exist"
**Nguyên nhân**: DynamoDB tables chưa được tạo

**Giải pháp**:
```powershell
cd C:\Users\ADMIN\Downloads\facerecog\aws
python create_database.py
```

### Lỗi: "Port 8888 already in use"
**Nguyên nhân**: Có process khác đang dùng port 8888

**Giải pháp**:
```powershell
# Kill process đang dùng port 8888
$proc = Get-NetTCPConnection -LocalPort 8888 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($proc) { Stop-Process -Id $proc -Force }

# Hoặc dùng port khác
python -m uvicorn backend.api.app:app --reload --host 127.0.0.1 --port 8889
```

## 7. TÍNH NĂNG CHÍNH

### Enrollment (Đăng ký)
1. Mở GUI application
2. Click "Start Camera"
3. Nhập thông tin: Full Name, Gender, Birth Year, Hometown, Residence
4. Click "Capture Face from Camera" để chụp ảnh
5. Click "Register from Captured Photo" để đăng ký

### Identification (Nhận diện)
1. Click "Start Camera"
2. Click "Identify Now" để nhận diện người trong camera
3. Kết quả sẽ hiển thị: Tên, độ tin cậy, thông tin chi tiết

### Quản lý Database
- Tab "People": Xem danh sách người đã đăng ký
- Tab "Stats": Xem thống kê hệ thống
- Tab "Advanced": Xóa người dùng, xem chi tiết

## 8. API ENDPOINTS

### Enrollment
```bash
POST http://127.0.0.1:8888/api/v1/enroll
Content-Type: multipart/form-data

# Form data:
- image: file
- user_name: string
- gender: string (optional)
- birth_year: string (optional)
- hometown: string (optional)
- residence: string (optional)
```

### Identification
```bash
POST http://127.0.0.1:8888/api/v1/identify
Content-Type: multipart/form-data

# Form data:
- image: file
```

### List People
```bash
GET http://127.0.0.1:8888/api/v1/people
```

### Get Person
```bash
GET http://127.0.0.1:8888/api/v1/people/{person_id}
```

### Delete Person
```bash
DELETE http://127.0.0.1:8888/api/v1/people/{person_id}
```

### Health Check
```bash
GET http://127.0.0.1:8888/health
```

## 9. LOGS VÀ DEBUG

### Xem logs của API server
Logs sẽ hiển thị trực tiếp trong terminal chạy uvicorn

### Xem logs của AWS services
```powershell
# CloudWatch logs (nếu có)
aws logs tail /aws/lambda/face-recognition --follow

# DynamoDB logs
aws dynamodb describe-table --table-name face-recognition-people-dev
```

### Enable debug mode
Trong file `.env`:
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

## 10. BACKUP VÀ RESTORE

### Backup DynamoDB
```powershell
# Export people table
aws dynamodb scan --table-name face-recognition-people-dev > backup_people.json

# Export embeddings table
aws dynamodb scan --table-name face-recognition-embeddings-dev > backup_embeddings.json
```

### Backup S3
```powershell
# Sync S3 bucket to local
aws s3 sync s3://YOUR_BUCKET_NAME ./s3_backup/
```

### Restore (nếu cần)
```powershell
# Import to DynamoDB (cần xử lý format JSON trước)
# Restore S3
aws s3 sync ./s3_backup/ s3://YOUR_BUCKET_NAME/
```

## 11. MONITORING

### Kiểm tra resource usage
```powershell
# DynamoDB metrics
aws cloudwatch get-metric-statistics --namespace AWS/DynamoDB --metric-name ConsumedReadCapacityUnits --dimensions Name=TableName,Value=face-recognition-people-dev --start-time 2025-11-19T00:00:00Z --end-time 2025-11-19T23:59:59Z --period 3600 --statistics Sum

# Rekognition usage
aws ce get-cost-and-usage --time-period Start=2025-11-01,End=2025-11-30 --granularity MONTHLY --metrics UsageQuantity --filter file://filter.json
```

### Chi phí AWS
```powershell
# Xem billing dashboard
Start-Process "https://console.aws.amazon.com/billing/home"
```

## 12. PRODUCTION DEPLOYMENT

Khi deploy production, cần:

1. Tắt DEBUG mode
2. Sử dụng Cognito authentication
3. Enable API key
4. Sử dụng HTTPS
5. Deploy với Docker hoặc AWS Lambda
6. Setup CloudWatch monitoring
7. Enable backup cho DynamoDB
8. Sử dụng CloudFront cho S3

Xem thêm trong file `docs/DEPLOYMENT.md`
