# Hướng Dẫn Triển Khai Thủ Công Trên AWS Console

Hướng dẫn này dành cho việc triển khai hệ thống hoàn toàn bằng giao diện web AWS Console, hạn chế tối đa việc dùng dòng lệnh (CLI).

> **Lưu ý**: Triển khai thủ công dễ xảy ra sai sót và tốn nhiều thời gian hơn so với dùng script/CDK. Hãy làm cẩn thận từng bước.

---

## Bước 1: Chuẩn Bị File Code

Trước khi lên Console, bạn cần chuẩn bị các file zip code trên máy tính:

1. **Lambda Layer (Thư viện)**:
   - Tải file `layer.zip` (nếu bạn đã build) hoặc build thủ công:
     - Tạo thư mục `python`
     - Cài thư viện vào đó: `pip install -r backend/requirements.txt -t python/`
     - Nén thư mục `python` thành `layer.zip`

2. **Lambda Functions (Code xử lý)**:
   - Nén nội dung bên trong `backend/src/auth/` thành `auth.zip`
   - Nén nội dung bên trong `backend/src/enroll/` thành `enroll.zip`
   - Nén nội dung bên trong `backend/src/identify/` thành `identify.zip`
   - Nén nội dung bên trong `backend/src/people/` thành `people.zip`

---

## Bước 2: Tạo S3 Bucket (Lưu Trữ Ảnh)

1. Truy cập **S3 Console**: https://s3.console.aws.amazon.com/
2. Nhấn **Create bucket**.
3. **Bucket name**: Đặt tên duy nhất (ví dụ: `face-recog-images-2024`)
4. **Region**: Chọn `US East (N. Virginia) us-east-1` (hoặc region bạn muốn).
5. Các cài đặt khác để mặc định.
6. Nhấn **Create bucket**.
7. **Lưu lại tên bucket** để dùng sau này.

---

## Bước 3: Tạo DynamoDB Table (Cơ Sở Dữ Liệu)

1. Truy cập **DynamoDB Console**: https://dynamodb.console.aws.amazon.com/
2. Nhấn **Create table**.
3. **Table name**: `FaceRecognitionUsers` (hoặc tên bạn muốn).
4. **Partition key**: `user_id` (kiểu String).
5. Các cài đặt khác để mặc định (On-demand capacity mode được khuyến nghị).
6. Nhấn **Create table**.
7. **Lưu lại tên table**.

---

## Bước 4: Tạo Cognito User Pool (Xác Thực)

1. Truy cập **Cognito Console**: https://console.aws.amazon.com/cognito/
2. Nhấn **Create user pool**.
3. **Step 1: Sign-in options**:
   - Chọn **Email**.
   - Nhấn Next.
4. **Step 2: Password policy**:
   - Để mặc định (MFA: No MFA).
   - Nhấn Next.
5. **Step 3: Sign-up experience**:
   - Bỏ chọn "Enable self-registration" nếu chỉ muốn Admin tạo user (hoặc giữ nguyên).
   - Nhấn Next.
6. **Step 4: Email delivery**:
   - Chọn **Send email with Cognito**.
   - Nhấn Next.
7. **Step 5: App integration**:
   - **User pool name**: `FaceRecogPool`.
   - Tích chọn **Use the Cognito Hosted UI** (nếu cần, hoặc bỏ qua).
   - Tại mục **App client**, đặt tên: `FaceRecogClient`.
   - Bỏ chọn "Generate client secret" (quan trọng cho web app).
   - Nhấn Next.
8. **Step 6: Review**: Nhấn **Create user pool**.
9. **Lưu lại**: `User Pool ID` và `App Client ID`.

---

## Bước 5: Tạo Rekognition Collection (AI)

Phần này không có giao diện tạo trực tiếp trên Console, bạn cần dùng **CloudShell** (giao diện dòng lệnh trên web) một lần duy nhất:

1. Nhấn vào biểu tượng **CloudShell** (hình dấu nhắc lệnh `>_`) trên thanh menu trên cùng bên phải AWS Console.
2. Chờ terminal khởi động.
3. Gõ lệnh sau và nhấn Enter:
   ```bash
   aws rekognition create-collection --collection-id face-recognition-collection
   ```
4. Nếu thành công, bạn sẽ thấy kết quả JSON trả về `StatusCode: 200`.
5. **Lưu lại Collection ID**: `face-recognition-collection`.

---

## Bước 6: Tạo IAM Role (Quyền Truy Cập)

Lambda cần quyền để truy cập S3, DynamoDB, Rekognition.

1. Truy cập **IAM Console**: https://console.aws.amazon.com/iam/
2. Vào mục **Roles** -> **Create role**.
3. **Trusted entity type**: Chọn **AWS service**.
4. **Service or use case**: Chọn **Lambda**.
5. Nhấn **Next**.
6. **Add permissions**: Tìm và tích chọn các quyền sau (để đơn giản cho demo, thực tế nên giới hạn kỹ hơn):
   - `AmazonS3FullAccess`
   - `AmazonDynamoDBFullAccess`
   - `AmazonRekognitionFullAccess`
   - `AmazonCognitoPowerUser`
   - `CloudWatchLogsFullAccess`
7. Nhấn **Next**.
8. **Role name**: `FaceRecogLambdaRole`.
9. Nhấn **Create role**.

---

## Bước 7: Tạo Lambda Functions

Lặp lại bước này cho 4 functions: `auth`, `enroll`, `identify`, `people`.

1. Truy cập **Lambda Console**: https://console.aws.amazon.com/lambda/
2. Nhấn **Create function**.
3. Chọn **Author from scratch**.
4. **Function name**: `auth-handler` (tương tự cho các cái khác).
5. **Runtime**: `Python 3.11`.
6. **Architecture**: `x86_64`.
7. **Permissions**:
   - Mở rộng "Change default execution role".
   - Chọn **Use an existing role**.
   - Chọn `FaceRecogLambdaRole` vừa tạo ở Bước 6.
8. Nhấn **Create function**.

**Cấu hình Code & Layer**:
1. Trong tab **Code**, nhấn **Upload from** -> **.zip file**.
2. Chọn file zip tương ứng (`auth.zip` cho `auth-handler`, v.v.).
3. Kéo xuống dưới cùng, phần **Layers**, nhấn **Add a layer**.
   - Chọn **Create a new layer** (nếu chưa tạo).
   - Upload `layer.zip`.
   - Quay lại function, chọn layer vừa tạo.

**Cấu hình Biến Môi Trường (Configuration -> Environment variables)**:
Thêm các biến sau (tùy function mà cần biến nào, nhưng thêm hết cũng được cho tiện):
- `S3_BUCKET`: (Tên bucket ở Bước 2)
- `DYNAMODB_TABLE`: (Tên table ở Bước 3)
- `REKOGNITION_COLLECTION`: `face-recognition-collection`
- `COGNITO_USER_POOL_ID`: (ID ở Bước 4)
- `COGNITO_CLIENT_ID`: (Client ID ở Bước 4)
- `REGION`: `us-east-1`

**Cấu hình Timeout**:
- Vào **Configuration** -> **General configuration** -> **Edit**.
- Tăng **Timeout** lên `1 min 0 sec`.
- Nhấn **Save**.

---

## Bước 8: Tạo API Gateway

1. Truy cập **API Gateway Console**: https://console.aws.amazon.com/apigateway/
2. Chọn **REST API** -> **Build**.
3. **API name**: `FaceRecogAPI`.
4. Nhấn **Create API**.

**Tạo Resource & Method**:
1. Nhấn **Create resource**.
   - Resource path: `/auth` (ví dụ).
   - Nhấn **Create resource**.
2. Chọn resource `/auth`, nhấn **Create method**.
   - Method type: `POST`.
   - Integration type: **Lambda Function**.
   - Lambda function: Chọn `auth-handler`.
   - Nhấn **Create method**.

Làm tương tự cho các đường dẫn khác:
- `/enroll` (POST) -> `enroll-handler`
- `/identify` (POST) -> `identify-handler`
- `/people` (GET) -> `people-handler`

**Bật CORS**:
1. Chọn resource (ví dụ `/auth`), nhấn **Enable CORS**.
2. Tích chọn các method (POST).
3. Nhấn **Save**.

**Deploy API**:
1. Nhấn **Deploy API**.
2. **Stage**: Chọn *New stage*, đặt tên `prod`.
3. Nhấn **Deploy**.
4. **Lưu lại Invoke URL** (ví dụ: `https://xyz.execute-api.us-east-1.amazonaws.com/prod`).

---

## Bước 9: Kết Nối Frontend

1. Mở file code frontend `frontend/web/.env.local` (trên máy tính).
2. Sửa `NEXT_PUBLIC_API_URL` thành Invoke URL vừa lấy ở Bước 8.
3. Deploy frontend lên **AWS Amplify** (xem hướng dẫn Amplify Deployment, phần này làm trên web console rất dễ).

---

## Tổng Kết

Bạn đã hoàn thành việc tạo hệ thống thủ công!
- **Ưu điểm**: Hiểu rõ từng dịch vụ, không cần cài đặt CLI phức tạp.
- **Nhược điểm**: Nhiều bước, dễ quên cấu hình, khó quản lý khi hệ thống lớn.
