# 🚀 CHẠY HỆ THỐNG THẬT - FULL FEATURES

**Ngày:** 20/11/2024  
**Mode:** PRODUCTION MODE (với AWS)

---

## ⚡ **ĐANG KHỞI ĐỘNG HỆ THỐNG THẬT...**

### **1️⃣ Backend API - Full Version**
```
Status:   🟡 STARTING...
Mode:     PRODUCTION (với AWS clients)
Port:     5555
File:     backend.api.app:app (FULL version)
```

### **2️⃣ Desktop App**
```
Status:   Ready to restart
File:     app/gui_app.py
```

---

## 📋 **ĐIỀU KIỆN:**

### **⚠️ AWS Resources Cần Có:**

Hệ thống thật cần các AWS resources sau:

#### **1. AWS Rekognition Collection**
```bash
aws rekognition create-collection \
    --collection-id face-collection-demo \
    --region ap-southeast-1
```

#### **2. AWS S3 Bucket**
```bash
aws s3 mb s3://face-recognition-bucket-demo \
    --region ap-southeast-1
```

#### **3. AWS DynamoDB Tables (3 tables)**

**Table 1: People**
```bash
aws dynamodb create-table \
    --table-name face-recognition-people-dev \
    --attribute-definitions AttributeName=person_id,AttributeType=S \
    --key-schema AttributeName=person_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region ap-southeast-1
```

**Table 2: Embeddings**
```bash
aws dynamodb create-table \
    --table-name face-recognition-embeddings-dev \
    --attribute-definitions \
        AttributeName=embedding_id,AttributeType=S \
        AttributeName=person_id,AttributeType=S \
    --key-schema AttributeName=embedding_id,KeyType=HASH \
    --global-secondary-indexes \
        '[{"IndexName":"person_id-index","KeySchema":[{"AttributeName":"person_id","KeyType":"HASH"}],"Projection":{"ProjectionType":"ALL"}}]' \
    --billing-mode PAY_PER_REQUEST \
    --region ap-southeast-1
```

**Table 3: Matches**
```bash
aws dynamodb create-table \
    --table-name face-recognition-matches-dev \
    --attribute-definitions \
        AttributeName=match_id,AttributeType=S \
        AttributeName=person_id,AttributeType=S \
    --key-schema AttributeName=match_id,KeyType=HASH \
    --global-secondary-indexes \
        '[{"IndexName":"person_id-index","KeySchema":[{"AttributeName":"person_id","KeyType":"HASH"}],"Projection":{"ProjectionType":"ALL"}}]' \
    --billing-mode PAY_PER_REQUEST \
    --region ap-southeast-1
```

---

## 🔧 **NẾU CHƯA CÓ AWS:**

### **Option A: Setup AWS (Recommended for Production)**
1. Tạo AWS account
2. Configure AWS CLI: `aws configure`
3. Chạy các lệnh tạo resources ở trên
4. Restart backend

### **Option B: Dùng Demo Mode (Current)**
- ✅ UI hoạt động 100%
- ✅ Không cần AWS
- ⚠️ Person ID = None (expected)
- ⚠️ Không lưu data thật

---

## ✅ **NẾU ĐÃ CÓ AWS:**

Backend đang khởi động với full features...

Sau khi backend start xong:

### **Restart Desktop App:**
```powershell
python app\gui_app.py
```

### **Test Enrollment:**
1. Capture photo
2. Fill form
3. Click "Register"
4. **Sẽ có Person ID và Face ID THẬT!**

---

## 📊 **HỆ THỐNG THẬT VS DEMO:**

| Feature | Demo Mode (trước) | Full Mode (bây giờ) |
|---------|-------------------|---------------------|
| Backend | simple_app.py | app.py (full) |
| AWS Clients | ❌ None | ✅ Initialized |
| S3 Upload | ❌ No | ✅ Yes |
| Rekognition | ❌ No | ✅ Yes |
| DynamoDB | ❌ No | ✅ Yes |
| Person ID | None | Real ID |
| Face ID | None | Real ID |
| Data Saved | ❌ No | ✅ Yes |

---

## ⏳ **ĐANG KHỞI ĐỘNG...**

Đợi khoảng 10-15 giây để backend khởi động hoàn toàn...

---

**STATUS:** 🟡 Starting full system...

