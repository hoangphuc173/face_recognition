# Hướng Dẫn Triển Khai Amplify

Hướng dẫn triển khai ứng dụng frontend Next.js lên AWS Amplify Hosting.

---

## Điều Kiện Tiên Quyết

- ✅ Mã nguồn đã được đẩy lên GitHub
- ✅ API Gateway URL đã sẵn sàng (từ bước triển khai Lambda)
- Tài khoản AWS có quyền truy cập Amplify

---

## Bước 1: Tạo Ứng Dụng Amplify

1. Đăng nhập vào **AWS Amplify Console**
2. Nhấn **"New app"** -> Chọn **"Host web app"**
3. Chọn **GitHub** làm nguồn mã nguồn
4. Ủy quyền truy cập GitHub (nếu chưa làm)
5. Chọn repository: `hoangphuc173/face_recognition`
6. Chọn branch: `master`
7. Nhấn **Next**

---

## Bước 2: Cấu Hình Build

Amplify sẽ tự động phát hiện file `amplify.yml` trong thư mục `frontend/web`.

Đảm bảo cấu hình build như sau (Amplify sẽ tự điền, nhưng hãy kiểm tra lại):

```yaml
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - cd frontend/web
        - npm ci
    build:
      commands:
        - npm run build
  artifacts:
    baseDirectory: frontend/web/.next
    files:
      - '**/*'
  cache:
    paths:
      - frontend/web/node_modules/**/*
```

Nếu Amplify không tự phát hiện đúng, hãy nhấn **Edit** và dán cấu hình trên vào.

---

## Bước 3: Thiết Lập Biến Môi Trường

Đây là bước quan trọng nhất để frontend kết nối được với backend.

1. Trong phần **Advanced settings**, mở rộng mục **Environment variables**
2. Thêm biến môi trường sau:

   - **Key**: `NEXT_PUBLIC_API_URL`
   - **Value**: `https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod`

   *(Thay thế `YOUR-API-ID` bằng ID thực tế của API Gateway bạn đã triển khai)*

3. Nhấn **Next**

---

## Bước 4: Xem Lại và Triển Khai

1. Xem lại tất cả thông tin
2. Nhấn **Save and deploy**

Amplify sẽ bắt đầu quy trình CI/CD:
- **Provision**: Tạo môi trường build
- **Build**: Cài đặt dependencies và build ứng dụng Next.js
- **Deploy**: Triển khai lên CDN
- **Verify**: Kiểm tra cơ bản

Quá trình này mất khoảng 5-10 phút.

---

## Bước 5: Xác Minh Triển Khai

Sau khi triển khai thành công (4 dấu tích xanh):

1. Nhấn vào URL ứng dụng (ví dụ: `https://master.APP_ID.amplifyapp.com`)
2. Kiểm tra trang đăng nhập có hiện ra không
3. Mở Developer Tools (F12) -> Console
4. Gõ `process.env.NEXT_PUBLIC_API_URL` (hoặc kiểm tra network request) để đảm bảo nó trỏ đúng tới API Gateway

---

## Cập Nhật Ứng Dụng

Mỗi khi bạn `git push` lên branch `master`, Amplify sẽ tự động:
1. Phát hiện thay đổi
2. Kéo mã nguồn mới về
3. Build lại ứng dụng
4. Triển khai phiên bản mới

Bạn không cần làm gì thêm thủ công.

---

## Tên Miền Tùy Chỉnh (Tùy Chọn)

Nếu bạn muốn dùng tên miền riêng (ví dụ: `app.yourdomain.com`):

1. Vào **Domain management** trong menu bên trái
2. Nhấn **Add domain**
3. Nhập tên miền của bạn
4. Làm theo hướng dẫn để cấu hình DNS (CNAME record)
5. Amplify sẽ tự động cấp chứng chỉ SSL miễn phí
