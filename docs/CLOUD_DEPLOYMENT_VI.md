# Hướng Dẫn Triển Khai Cloud

Tổng quan về quy trình triển khai hệ thống lên AWS Cloud.

> **Lưu ý**: Để có hướng dẫn chi tiết từng bước, vui lòng xem các tài liệu chuyên sâu:
> - `AWS_INFRASTRUCTURE_DEPLOYMENT_VI.md` (Cơ sở hạ tầng)
> - `AWS_LAMBDA_DEPLOYMENT_VI.md` (Backend)
> - `AMPLIFY_DEPLOYMENT_VI.md` (Frontend)

---

## Tổng Quan Kiến Trúc

Hệ thống được triển khai theo mô hình Serverless trên AWS:

1. **Frontend**: Next.js app được host trên **AWS Amplify**.
2. **API**: **Amazon API Gateway** quản lý các RESTful endpoints.
3. **Backend**: **AWS Lambda** xử lý logic nghiệp vụ (Python).
4. **Database**: **Amazon DynamoDB** lưu trữ thông tin người dùng.
5. **Storage**: **Amazon S3** lưu trữ ảnh khuôn mặt.
6. **AI/ML**: **Amazon Rekognition** xử lý nhận diện khuôn mặt.
7. **Auth**: **Amazon Cognito** quản lý định danh và phân quyền.

---

## Quy Trình Triển Khai

### Giai Đoạn 1: Cơ Sở Hạ Tầng (Infrastructure)

Sử dụng **AWS CDK** để tạo toàn bộ tài nguyên AWS cần thiết.

- **Công cụ**: AWS CDK (TypeScript)
- **Thư mục**: `infrastructure/`
- **Lệnh chính**: `cdk deploy --all`

### Giai Đoạn 2: Backend (Lambda)

Đóng gói và triển khai mã nguồn Python lên Lambda functions.

- **Công cụ**: AWS CLI, Zip
- **Thư mục**: `backend/`
- **Lệnh chính**: `scripts/cloud/deploy-lambda-quick.ps1`

### Giai Đoạn 3: Frontend (Web)

Kết nối GitHub repository với AWS Amplify để triển khai CI/CD.

- **Công cụ**: AWS Amplify Console
- **Thư mục**: `frontend/web/`
- **Cấu hình**: `amplify.yml`

---

## Môi Trường

Chúng ta sử dụng mô hình đa môi trường (Multi-environment):

### 1. Development (Local)
- Chạy trên máy cá nhân
- Kết nối tới AWS resources thực (DynamoDB, S3, Rekognition) hoặc giả lập
- Dùng cho phát triển tính năng mới

### 2. Production (Cloud)
- Môi trường chính thức phục vụ người dùng
- Tự động scale theo tải
- Bảo mật cao, logging đầy đủ

---

## Chi Phí Ước Tính

Mô hình Serverless giúp tối ưu chi phí (Pay-as-you-go):

- **Cố định**: ~$5-10/tháng (KMS, lưu trữ cơ bản)
- **Biến đổi**: Dựa trên usage (Lambda invocations, API calls, Storage)
  - Với 1000 users/ngày: ~$25-30/tháng

---

## Bảo Mật

- **IAM Roles**: Nguyên tắc đặc quyền tối thiểu (Least Privilege)
- **Cognito**: Xác thực JWT chuẩn công nghiệp
- **KMS**: Mã hóa dữ liệu nghỉ (At-rest encryption) cho S3 và DynamoDB
- **HTTPS**: Mã hóa dữ liệu truyền tải (In-transit encryption)

---

## Giám Sát & Vận Hành

- **CloudWatch Logs**: Log chi tiết từ Lambda và API Gateway
- **CloudWatch Metrics**: Theo dõi độ trễ, lỗi, số lượng request
- **X-Ray**: Trace request qua các dịch vụ (tùy chọn)

---

## Khôi Phục Thảm Họa (Disaster Recovery)

- **S3 Versioning**: Khôi phục file bị xóa/ghi đè
- **DynamoDB PITR**: Point-in-time recovery (khôi phục theo thời điểm)
- **Infrastructure as Code**: Có thể tái triển khai toàn bộ hệ thống sang Region khác trong < 30 phút.
