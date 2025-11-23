# Hướng Dẫn Kiểm Thử & Xác Minh AWS

Hướng dẫn kiểm thử và xác minh toàn bộ hệ thống sau khi triển khai.

---

## Danh Sách Kiểm Tra

- [ ] Cơ sở hạ tầng đã triển khai thành công
- [ ] Các Lambda functions hoạt động
- [ ] API Gateway đã được cấu hình
- [ ] Frontend đã triển khai lên Amplify
- [ ] Luồng xác thực đầu cuối hoạt động
- [ ] Đăng ký khuôn mặt hoạt động
- [ ] Nhận diện khuôn mặt hoạt động
- [ ] Phân quyền RBAC hoạt động

---

## Bước 1: Xác Minh Cơ Sở Hạ Tầng

### CloudFormation Stack

```bash
aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].StackStatus'
```

**Mong đợi**: `CREATE_COMPLETE` hoặc `UPDATE_COMPLETE`

### Cognito User Pool

```bash
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

aws cognito-idp describe-user-pool --user-pool-id $USER_POOL_ID
```

**Mong đợi**: User Pool với các nhóm Admin, Staff, Guest

### S3 Bucket

```bash
S3_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' \
  --output text)

# Kiểm tra mã hóa
aws s3api get-bucket-encryption --bucket $S3_BUCKET
```

**Mong đợi**: Mã hóa AES256 được bật

### DynamoDB Table

```bash
TABLE_NAME=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`DynamoDBTableName`].OutputValue' \
  --output text)

aws dynamodb describe-table --table-name $TABLE_NAME
```

**Mong đợi**: Trạng thái Table là ACTIVE

---

## Bước 2: Kiểm Tra Lambda Functions

### Test Auth Handler

```bash
# Test endpoint health
aws lambda invoke \
  --function-name auth-handler \
  --payload '{"resource":"/auth/health","httpMethod":"GET"}' \
  response.json

cat response.json
```

**Mong đợi**: `{"status": "healthy"}`

### Test Enroll Handler

```bash
# Tạo ảnh base64 (giả lập)
echo "Test payload" | base64 > test-image.txt

aws lambda invoke \
  --function-name enroll-handler \
  --payload '{"email":"test@example.com","image":"'$(cat test-image.txt)'"}' \
  response.json

cat response.json
```

### Test Identify Handler

```bash
aws lambda invoke \
  --function-name identify-handler \
  --payload '{"image":"'$(cat test-image.txt)'"}' \
  response.json

cat response.json
```

### Test People Handler

```bash
aws lambda invoke \
  --function-name people-handler \
 --payload '{"httpMethod":"GET","resource":"/people"}' \
  response.json

cat response.json
```

---

## Bước 3: Kiểm Tra API Gateway

### Lấy API URL

```bash
API_ID=$(aws apigateway get-rest-apis \
  --query 'items[?name==`face-recognition-api`].id' \
  --output text)

API_URL="https://$API_ID.execute-api.us-east-1.amazonaws.com/prod"
echo "API URL: $API_URL"
```

### Test Đăng Ký

```bash
curl -X POST $API_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "Test123!",
    "full_name": "Test User"
  }'
```

**Mong đợi**: `{"message": "User registered. Check email for verification code."}`

### Test Đăng Nhập (sau khi xác thực)

```bash
curl -X POST $API_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "Test123!"
  }'
```

**Mong đợi**: JWT token trong phản hồi

---

## Bước 4: Kiểm Tra Frontend (Amplify)

### Truy Cập Ứng Dụng

Mở Amplify URL trong trình duyệt:
```
https://master.APP_ID.amplifyapp.com
```

### Test Đăng Ký Người Dùng

1. Nhấn "Register" hoặc "Sign Up"
2. Điền thông tin:
   - Email: `user@example.com`
   - Password: `Test123!`
   - Full Name: `John Doe`
3. Gửi form

**Mong đợi**: "Check your email for verification code"

### Xác Thực Email

1. Kiểm tra hộp thư email
2. Sao chép mã xác thực
3. Nhập mã vào form xác thực
4. Gửi

**Mong đợi**: "Email verified successfully"

### Test Đăng Nhập

1. Vào trang đăng nhập
2. Nhập:
   - Email: `user@example.com`
   - Password: `Test123!`
3. Gửi

**Mong đợi**: Chuyển hướng đến dashboard

### Test Đăng Ký Khuôn Mặt

1. Sau khi đăng nhập, vào trang "Enroll"
2. Nhấn "Choose File" hoặc dùng webcam
3. Tải lên ảnh khuôn mặt
4. Gửi

**Mong đợi**: 
- "Face enrolled successfully"
- Ảnh xuất hiện trong hồ sơ người dùng
- Người dùng được thêm vào DynamoDB

**Xác minh trong Backend**:
```bash
# Kiểm tra S3
aws s3 ls s3://$S3_BUCKET/ --recursive

# Kiểm tra DynamoDB
aws dynamodb scan --table-name $TABLE_NAME
```

### Test Nhận Diện Khuôn Mặt

1. Vào trang "Identify"
2. Tải lên cùng ảnh khuôn mặt đó
3. Gửi

**Mong đợi**:
- "Face recognized: John Doe"
- Độ tin cậy > 90%
- Khung bao quanh khuôn mặt được vẽ

### Test Quản Lý Người Dùng

1. Vào trang "People"
2. Xem danh sách người dùng đã đăng ký

**Mong đợi**: Danh sách hiển thị John Doe với ảnh

---

## Bước 5: Kiểm Tra RBAC (Phân Quyền Dựa Trên Vai Trò)

### Tạo Admin User

```bash
# Tạo admin
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username admin@example.com \
  --user-attributes Name=email,Value=admin@example.com \
  --temporary-password Admin123!

# Thêm vào nhóm Admin
aws cognito-idp admin-add-user-to-group \
  --user-pool-id $USER_POOL_ID \
  --username admin@example.com \
  --group-name Admin

# Đặt mật khẩu vĩnh viễn
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username admin@example.com \
  --password Admin123! \
  --permanent
```

### Test Quyền Admin

Đăng nhập với tư cách admin và xác minh:
- ✅ Có thể xem tất cả người dùng
- ✅ Có thể xóa người dùng
- ✅ Có thể đăng ký khuôn mặt
- ✅ Có thể nhận diện khuôn mặt

### Tạo Staff User

```bash
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username staff@example.com \
  --user-attributes Name=email,Value=staff@example.com \
  --temporary-password Staff123!

aws cognito-idp admin-add-user-to-group \
  --user-pool-id $USER_POOL_ID \
  --username staff@example.com \
  --group-name Staff

aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username staff@example.com \
  --password Staff123! \
  --permanent
```

### Test Quyền Staff

Đăng nhập với tư cách staff và xác minh:
- ✅ Có thể đăng ký khuôn mặt
- ✅ Có thể nhận diện khuôn mặt
- ❌ Không thể xóa người dùng (sẽ hiện lỗi)

---

## Bước 6: Kiểm Tra Hiệu Năng

### Lambda Cold Start

```bash
# Gọi sau 5 phút không hoạt động
time aws lambda invoke \
  --function-name auth-handler \
  --payload '{"action":"health"}' \
  response.json
```

**Mong đợi**: < 3 giây

### Lambda Warm Start

```bash
# Gọi ngay sau đó
time aws lambda invoke \
  --function-name auth-handler \
  --payload '{"action":"health"}' \
  response.json
```

**Mong đợi**: < 500ms

### Concurrent Requests (Yêu Cầu Đồng Thời)

```bash
# Gửi 10 yêu cầu đồng thời
for i in {1..10}; do
  curl -X POST $API_URL/auth/health &
done
wait
```

**Mong đợi**: Tất cả yêu cầu thành công

---

## Bước 7: Kiểm Tra CloudWatch Logs

### Xem Lambda Logs

```bash
# Theo dõi logs auth handler
aws logs tail /aws/lambda/auth-handler --follow

# Lấy 100 dòng cuối
aws logs tail /aws/lambda/auth-handler --since 10m
```

### Xem API Gateway Logs

```bash
# Bật logging trước nếu chưa bật
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name prod \
  --patch-operations op=replace,path=/accessLogSettings/destinationArn,value=arn:aws:logs:us-east-1:ACCOUNT:log-group:api-gateway-logs

# Xem logs
aws logs tail /aws/apigateway/$API_ID/prod --follow
```

---

## Bước 8: Kiểm Tra Bảo Mật

### Test CORS

```bash
# Test OPTIONS request
curl -X OPTIONS $API_URL/auth/register \
  -H "Origin: https://example.com" \
  -H "Access-Control-Request-Method: POST"
```

**Mong đợi**: Có các headers CORS

### Test Xác Thực

```bash
# Thử truy cập endpoint được bảo vệ mà không có token
curl -X GET $API_URL/people

# Mong đợi: 401 Unauthorized
```

### Test Dữ Liệu Không Hợp Lệ

```bash
# Test với email không hợp lệ
curl -X POST $API_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "not-an-email",
    "password": "Test123!"
  }'
```

**Mong đợi**: Lỗi xác thực (Validation error)

---

## Bước 9: Load Testing (Tùy Chọn)

### Sử Dụng Apache Bench

```bash
# Cài đặt ab
# Windows: Tải từ Apache
# Linux: apt-get install apache2-utils

# Test 100 requests, 10 concurrent
ab -n 100 -c 10 -T "application/json" \
  -p test-payload.json \
  $API_URL/auth/health
```

### Sử Dụng Artillery

```bash
npm install -g artillery

# Tạo config artillery
cat > load-test.yml <<EOF
config:
  target: "$API_URL"
  phases:
    - duration: 60
      arrivalRate: 10
scenarios:
  - flow:
      - post:
          url: "/auth/health"
EOF

# Chạy test
artillery run load-test.yml
```

---

## Danh Sách Kiểm Tra Xác Minh

Sau tất cả các bài test:

- [ ] Cơ sở hạ tầng: Tất cả resources được tạo và cấu hình
- [ ] Lambda: Tất cả 4 functions đã triển khai và phản hồi
- [ ] API Gateway: Tất cả endpoints truy cập được
- [ ] Frontend: Đã triển khai lên Amplify và truy cập được
- [ ] Xác thực: Đăng ký, xác minh, đăng nhập hoạt động
- [ ] Đăng ký: Tải lên ảnh và đánh chỉ mục hoạt động
- [ ] Nhận diện: Nhận diện khuôn mặt hoạt động với độ tin cậy >90%
- [ ] RBAC: Quyền Admin/Staff/Guest được thực thi đúng
- [ ] Logs: CloudWatch logs ghi lại tất cả hoạt động
- [ ] Hiệu năng: Cold start <3s, warm start <500ms
- [ ] Bảo mật: CORS, xác thực, kiểm tra dữ liệu đầu vào hoạt động

---

## Tiêu Chí Thành Công

✅ Tất cả Lambda functions trả về trạng thái 200
✅ API Gateway định tuyến đúng tới Lambdas
✅ Frontend tải và hiển thị đúng
✅ Người dùng có thể đăng ký, xác minh và đăng nhập
✅ Đăng ký khuôn mặt lưu ảnh vào S3
✅ Nhận diện khuôn mặt trả về đúng User ID
✅ Quyền RBAC được thực thi
✅ Không có lỗi trong CloudWatch logs
✅ Hiệu năng nằm trong giới hạn chấp nhận được
