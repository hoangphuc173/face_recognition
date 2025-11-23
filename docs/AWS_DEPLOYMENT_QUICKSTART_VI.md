# Hướng Dẫn Triển Khai AWS - Tổng Quan Tiếng Việt

## 📚 Tài Liệu Đầy Đủ

Để xem hướng dẫn chi tiết đầy đủ bằng tiếng Anh, xem:
- `AWS_INFRASTRUCTURE_DEPLOYMENT.md` - Deployment CDK đầy đủ
- `AWS_LAMBDA_DEPLOYMENT.md` - Deployment Lambda chi tiết  
- `AWS_TESTING_GUIDE.md` - Testing toàn diện
- `AWS_TROUBLESHOOTING.md` - Xử lý sự cố

## 🚀 Quick Start - Triển Khai Nhanh

### 1️⃣ Deploy Infrastructure (CDK)

```bash
cd infrastructure

# Cài dependencies
npm install

# Cấu hình environment
echo "AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)" > .env
echo "AWS_REGION=us-east-1" >> .env

# Bootstrap CDK (lần đầu)
cdk bootstrap

# Deploy
cdk deploy --all
```

**Kết quả**: Cognito, S3, DynamoDB, Rekognition Collection được tạo (~5-10 phút)

---

### 2️⃣ Deploy Lambda Functions

```bash
# Build Lambda Layer
scripts\utilities\build-layer.ps1

# Deploy nhanh tất cả 4 functions
scripts\cloud\deploy-lambda-quick.ps1
```

**Kết quả**: 4 Lambda functions (auth, enroll, identify, people) được deploy

---

### 3️⃣ Deploy Frontend (Amplify)

1. Mở **AWS Amplify Console**
2. **New app** → **Host web app** → **GitHub**
3. Chọn repo: `hoangphuc173/face_recognition`
4. Chọn branch: `master`
5. App root: `frontend/web`
6. **Environment variables**:
   ```
   NEXT_PUBLIC_API_URL = https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod
   ```
7. **Save and deploy**

**Kết quả**: Frontend deployed tại `https://master.APP_ID.amplifyapp.com`

---

## ✅ Testing - Kiểm Tra

### Test Lambda Functions

```bash
# Test auth
aws lambda invoke --function-name auth-handler --payload '{"action":"health"}' response.json
cat response.json

# Test người people
aws lambda invoke --function-name people-handler --payload '{"httpMethod":"GET"}' response.json
```

### Test Frontend

1. Mở Amplify URL
2. **Register** → Nhập email/password
3. **Verify** → Nhập OTP code từ email
4. **Login** → Đăng nhập
5. **Enroll** → Upload ảnh khuôn mặt
6. **Identify** → Test nhận diện

---

## 🔧 Xử Lý Lỗi Thường Gặp

### Lambda Timeout

```bash
# Tăng timeout lên 60 giây
aws lambda update-function-configuration \
  --function-name enroll-handler \
  --timeout 60
```

### Lambda Out of Memory

```bash
# Tăng memory lên 1024MB
aws lambda update-function-configuration \
  --function-name enroll-handler \
  --memory-size 1024
```

### CORS Error

Thêm headers vào Lambda response:
```python
return {
    "statusCode": 200,
    "headers": {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS"
    },
    "body": json.dumps(data)
}
```

### API Gateway 502

- Kiểm tra Lambda logs: `aws logs tail /aws/lambda/auth-handler --follow`
- Verify Lambda response format (phải là proxy format)
- Tăng Lambda timeout nếu cần

---

## 💰 Chi Phí Ước Tính

**Infrastructure** (~$5-10/tháng):
- Cognito: $0 (50K MAU miễn phí)
- S3: ~$1
- DynamoDB: ~$2.50
- KMS: $1/key/tháng
- CloudWatch: ~$0.50

**Với traffic** (1000 requests/ngày, ~$25-30/tháng):
- Lambda: ~$10
- API Gateway: ~$3.50
- Rekognition: ~$1
- Data transfer: ~$5

---

## 📋 Danh Sách Kiểm Tra Deployment

- [ ] CDK infrastructure deployed
- [ ] 4 Lambda functions deployed
- [ ] API Gateway configured
- [ ] Amplify frontend deployed
- [ ] Cognito User Pool có Admin/Staff/Guest groups
- [ ] Test registration/login works
- [ ] Test face enrollment works
- [ ] Test face identification works
- [ ] CloudWatch logs hoạt động

---

## 🆘 Cần Trợ Giúp?

1. **Kiểm tra CloudWatch Logs** (thông tin chi tiết nhất):
   ```bash
   aws logs tail /aws/lambda/FUNCTION_NAME --follow
   ```

2. **Xem tài liệu đầy đủ** (tiếng Anh):
   - Infrastructure: `docs/AWS_INFRASTRUCTURE_DEPLOYMENT.md`
   - Lambda: `docs/AWS_LAMBDA_DEPLOYMENT.md`
   - Testing: `docs/AWS_TESTING_GUIDE.md`
   - Troubleshooting: `docs/AWS_TROUBLESHOOTING.md`

3. **AWS Service Health**: https://status.aws.amazon.com

---

## 🔄 Cập Nhật Deployment

### Update Lambda Code

```bash
# Rebuild và update
cd backend/src/auth
zip -r auth-handler.zip .
aws lambda update-function-code \
  --function-name auth-handler \
  --zip-file fileb://auth-handler.zip
```

### Update Infrastructure

```bash
cd infrastructure
npm run build
cdk deploy --all
```

### Update Frontend

Push to GitHub master branch → Amplify auto-deploys

---

## 🗑️ Xóa Tất Cả

```bash
cd infrastructure
cdk destroy --all
```

Xem `docs/AWS_CLEANUP_GUIDE_VI.md` để biết chi tiết xóa resources.
