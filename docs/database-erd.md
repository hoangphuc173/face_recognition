# Face Recognition System - Entity Relationship Diagram (ERD)

## 📊 Database Schema

```mermaid
erDiagram
    USERS ||--o{ EMBEDDINGS : "has"
    USERS ||--o{ ACCESS_LOGS : "generates"
    EMBEDDINGS }o--|| REKOGNITION_COLLECTION : "indexed in"
    
    USERS {
        string person_id PK "UUID"
        string user_name "GSI"
        string full_name
        string email
        string phone_number
        json metadata "Custom attributes"
        string s3_image_url
        datetime created_at
        datetime updated_at
        string enrollment_status "active/inactive"
        int face_count "Number of faces enrolled"
    }
    
    EMBEDDINGS {
        string person_id PK "Partition Key"
        string face_id SK "Sort Key (from Rekognition)"
        string rekognition_face_id "Unique face ID"
        list embedding_vector "512-dimensional"
        json bounding_box "Face location"
        float confidence "0-100"
        datetime indexed_at
        string image_quality "HIGH/MEDIUM/LOW"
        json face_attributes "Age, emotions, etc"
        string status "active/deleted"
    }
    
    ACCESS_LOGS {
        string log_id PK "UUID"
        string person_id "FK to Users"
        datetime timestamp SK "ISO 8601"
        string action "identify/verify"
        string use_case "attendance/access_control/financial"
        float confidence_score "0-100"
        boolean match_result "true/false"
        string ip_address
        json request_metadata
        string session_id
    }
    
    REKOGNITION_COLLECTION {
        string collection_id PK "face-recognition-collection"
        string collection_arn
        datetime created_at
        int face_count
        string status
    }
```

---

## 🗄️ DynamoDB Tables Detail

### 1. **Users Table**

```yaml
Table Name: face-recognition-users-prod-773600
Partition Key: person_id (String)
Billing Mode: ON_DEMAND
Indexes:
  - GSI: user_name-index
    - Partition Key: user_name (String)
    - Projection: ALL
```

**Attributes:**
| Attribute | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| person_id | String | ✅ | UUID primary key | "550e8400-e29b-41d4-a716-446655440000" |
| user_name | String | ✅ | Unique username (GSI) | "john.doe" |
| full_name | String | ✅ | Display name | "John Doe" |
| email | String | ❌ | Email address | "john@example.com" |
| phone_number | String | ❌ | Phone with country code | "+84123456789" |
| metadata | Map | ❌ | Custom attributes | {"department": "IT", "employee_id": "E001"} |
| s3_image_url | String | ✅ | S3 path to image | "s3://bucket/enrollments/550e8400.jpg" |
| created_at | String | ✅ | ISO 8601 timestamp | "2025-11-20T10:30:00Z" |
| updated_at | String | ✅ | ISO 8601 timestamp | "2025-11-20T10:30:00Z" |
| enrollment_status | String | ✅ | Status enum | "active" / "inactive" / "pending" |
| face_count | Number | ✅ | Total faces enrolled | 1 |

**Access Patterns:**
1. Get user by person_id: `GetItem(person_id)`
2. Find user by username: `Query(user_name-index, user_name=?)`
3. List all users: `Scan()`
4. List active users: `Scan(FilterExpression: enrollment_status = 'active')`

---

### 2. **Embeddings Table**

```yaml
Table Name: face-recognition-embeddings-prod-773600
Partition Key: person_id (String)
Sort Key: face_id (String)
Billing Mode: ON_DEMAND
```

**Attributes:**
| Attribute | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| person_id | String | ✅ | Foreign key to Users | "550e8400-e29b-41d4-a716-446655440000" |
| face_id | String | ✅ | Composite sort key | "face_20251120_103000" |
| rekognition_face_id | String | ✅ | AWS Rekognition face ID | "2a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p" |
| embedding_vector | List | ✅ | 512-dim float array | [0.123, -0.456, 0.789, ...] |
| bounding_box | Map | ✅ | Face coordinates | {"Width": 0.5, "Height": 0.6, "Left": 0.2, "Top": 0.1} |
| confidence | Number | ✅ | Detection confidence | 99.87 |
| indexed_at | String | ✅ | ISO 8601 timestamp | "2025-11-20T10:30:00Z" |
| image_quality | String | ✅ | Quality assessment | "HIGH" / "MEDIUM" / "LOW" |
| face_attributes | Map | ❌ | Age, gender, emotions | {"AgeRange": {"Low": 25, "High": 35}} |
| status | String | ✅ | Face status | "active" / "deleted" |

**Access Patterns:**
1. Get all faces for person: `Query(person_id)`
2. Get specific face: `GetItem(person_id, face_id)`
3. Count faces for person: `Query(person_id, Select='COUNT')`
4. Delete face: `DeleteItem(person_id, face_id)`

---

### 3. **Access Logs Table**

```yaml
Table Name: face-recognition-access-logs-prod-773600
Partition Key: log_id (String)
Sort Key: timestamp (String)
Billing Mode: ON_DEMAND
Indexes:
  - GSI: person_id-timestamp-index
    - Partition Key: person_id (String)
    - Sort Key: timestamp (String)
    - Projection: ALL
TTL: Enabled on ttl attribute (30 days)
```

**Attributes:**
| Attribute | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| log_id | String | ✅ | UUID primary key | "7d8e9f0a-1b2c-3d4e-5f6g-7h8i9j0k1l2m" |
| person_id | String | ✅ | Foreign key to Users | "550e8400-e29b-41d4-a716-446655440000" |
| timestamp | String | ✅ | ISO 8601 timestamp (SK) | "2025-11-20T10:30:00Z" |
| action | String | ✅ | Action type | "identify" / "verify" / "enroll" |
| use_case | String | ✅ | Use case scenario | "attendance" / "access_control" / "financial" |
| confidence_score | Number | ✅ | Match confidence | 98.5 |
| match_result | Boolean | ✅ | Success/failure | true / false |
| ip_address | String | ❌ | Client IP | "203.0.113.45" |
| request_metadata | Map | ❌ | Additional info | {"device": "mobile", "location": "Office A"} |
| session_id | String | ❌ | Session identifier | "sess_abc123" |
| ttl | Number | ✅ | Unix timestamp for auto-delete | 1732464000 |

**Access Patterns:**
1. Get log by ID: `GetItem(log_id, timestamp)`
2. Get logs for person: `Query(person_id-timestamp-index, person_id=?)`
3. Get logs in time range: `Query(person_id-timestamp-index, person_id=?, timestamp BETWEEN ? AND ?)`
4. Recent logs: `Query(person_id-timestamp-index, person_id=?, ScanIndexForward=false, Limit=10)`

---

## 🔗 Relationships

### Users ↔ Embeddings (1:N)
- One user can have multiple face embeddings
- Each embedding belongs to exactly one user
- Cascade delete: When user is deleted, all embeddings should be removed

### Users ↔ Access Logs (1:N)
- One user generates multiple access logs
- Each log is associated with one user
- Logs are auto-deleted after 30 days (TTL)

### Embeddings ↔ Rekognition Collection (N:1)
- Multiple embeddings indexed in one Rekognition collection
- Collection ID: `face-recognition-collection`
- Sync required: DynamoDB embeddings must match Rekognition faces

---

## 📐 Data Model Diagram (Alternative View)

```
┌─────────────────────────────────────────────┐
│            USERS TABLE                      │
│  PK: person_id                              │
│  GSI: user_name                             │
├─────────────────────────────────────────────┤
│  • user_name (unique)                       │
│  • full_name                                │
│  • email, phone                             │
│  • s3_image_url                             │
│  • metadata (JSON)                          │
│  • enrollment_status                        │
│  • timestamps                               │
└────┬────────────────────────────────────────┘
     │
     │ 1:N
     │
┌────▼────────────────────────────────────────┐
│         EMBEDDINGS TABLE                    │
│  PK: person_id | SK: face_id                │
├─────────────────────────────────────────────┤
│  • rekognition_face_id                      │
│  • embedding_vector[512]                    │
│  • bounding_box (JSON)                      │
│  • confidence                               │
│  • image_quality                            │
│  • face_attributes (JSON)                   │
│  • indexed_at                               │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│        ACCESS LOGS TABLE                    │
│  PK: log_id | SK: timestamp                 │
│  GSI: person_id-timestamp-index             │
├─────────────────────────────────────────────┤
│  • person_id (FK)                           │
│  • action, use_case                         │
│  • confidence_score                         │
│  • match_result                             │
│  • ip_address, metadata                     │
│  • ttl (30 days auto-delete)                │
└─────────────────────────────────────────────┘
```

---

## 💾 Storage Estimates

### Users Table
- Average item size: ~2 KB
- 1,000 users = 2 MB
- 10,000 users = 20 MB
- 100,000 users = 200 MB

### Embeddings Table
- Average item size: ~8 KB (512-dim vector + metadata)
- 1,000 embeddings = 8 MB
- 10,000 embeddings = 80 MB
- 100,000 embeddings = 800 MB

### Access Logs Table (with 30-day TTL)
- Average item size: ~1 KB
- 1,000 logs/day = 30 MB/month
- 10,000 logs/day = 300 MB/month
- 100,000 logs/day = 3 GB/month

**Total for 10K users with 30-day logs:**
- Users: 20 MB
- Embeddings: 80 MB
- Logs (10K/day): 300 MB
- **Total: ~400 MB** (Well within DynamoDB Free Tier: 25 GB)

---

## 🔐 Security Considerations

1. **Encryption at Rest**: All DynamoDB tables encrypted with AWS KMS
2. **Encryption in Transit**: TLS 1.2+ for all connections
3. **IAM Policies**: Least privilege access for Lambda functions
4. **TTL**: Automatic deletion of logs after 30 days (GDPR compliance)
5. **Backup**: Point-in-time recovery enabled
6. **Audit**: CloudWatch Logs for all DynamoDB operations
