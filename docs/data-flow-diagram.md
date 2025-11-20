# Face Recognition System - Data Flow Diagram

## 🔄 Overall System Data Flow

```mermaid
graph TB
    subgraph "Client Layer"
        WebApp[Web Application]
        MobileApp[Mobile App]
        DesktopApp[Desktop App]
    end
    
    subgraph "Input Processing"
        Camera[Camera/Upload]
        ImageCapture[Image Capture]
        Base64Encode[Base64 Encoding]
    end
    
    subgraph "AWS Cloud"
        subgraph "API Layer"
            APIGateway[API Gateway<br/>HTTPS Endpoint]
            CORS[CORS Handler]
            Auth[Authorization<br/>Future: Cognito]
        end
        
        subgraph "Lambda Processing"
            EnrollLambda[Enroll Function<br/>Face Registration]
            IdentifyLambda[Identify Function<br/>Face Recognition]
            UtilityLambda[Utility Functions<br/>Health, Stats, People]
        end
        
        subgraph "AI/ML Processing"
            RekDetect[Rekognition<br/>Face Detection]
            RekIndex[Rekognition<br/>Index Faces]
            RekSearch[Rekognition<br/>Search Faces]
            FaceVector[512-Dim<br/>Embedding Vector]
        end
        
        subgraph "Storage Layer"
            S3Images[S3 Bucket<br/>Image Storage]
            DDBUsers[DynamoDB<br/>Users Table]
            DDBEmbeddings[DynamoDB<br/>Embeddings Table]
            DDBLogs[DynamoDB<br/>Access Logs]
        end
        
        subgraph "Configuration"
            SSMParams[Systems Manager<br/>Parameter Store<br/>Thresholds]
        end
        
        subgraph "Monitoring"
            CloudWatchLogs[CloudWatch Logs]
            CloudWatchMetrics[CloudWatch Metrics]
        end
    end
    
    subgraph "Response Processing"
        JSONResponse[JSON Response]
        ResultFormat[Format Result]
    end
    
    %% Input Flow
    WebApp --> Camera
    MobileApp --> Camera
    DesktopApp --> Camera
    Camera --> ImageCapture
    ImageCapture --> Base64Encode
    Base64Encode --> APIGateway
    
    %% API Gateway Flow
    APIGateway --> CORS
    CORS --> Auth
    Auth -.-> EnrollLambda
    Auth -.-> IdentifyLambda
    Auth -.-> UtilityLambda
    
    %% Enrollment Flow
    EnrollLambda --> |1. Upload Image| S3Images
    EnrollLambda --> |2. Detect Face| RekDetect
    RekDetect --> |Face Found| RekIndex
    RekIndex --> |Generate| FaceVector
    FaceVector --> |3. Store Embedding| DDBEmbeddings
    EnrollLambda --> |4. Store User| DDBUsers
    EnrollLambda --> |Get Threshold| SSMParams
    
    %% Identification Flow
    IdentifyLambda --> |1. Search Face| RekSearch
    RekSearch --> |Match Faces| FaceVector
    IdentifyLambda --> |2. Query User| DDBUsers
    IdentifyLambda --> |3. Query Embedding| DDBEmbeddings
    IdentifyLambda --> |4. Log Access| DDBLogs
    IdentifyLambda --> |Get Threshold| SSMParams
    
    %% Utility Flow
    UtilityLambda --> DDBUsers
    UtilityLambda --> DDBEmbeddings
    UtilityLambda --> DDBLogs
    UtilityLambda --> SSMParams
    
    %% Monitoring Flow
    EnrollLambda -.-> CloudWatchLogs
    IdentifyLambda -.-> CloudWatchLogs
    UtilityLambda -.-> CloudWatchLogs
    EnrollLambda -.-> CloudWatchMetrics
    IdentifyLambda -.-> CloudWatchMetrics
    
    %% Response Flow
    EnrollLambda --> ResultFormat
    IdentifyLambda --> ResultFormat
    UtilityLambda --> ResultFormat
    ResultFormat --> JSONResponse
    JSONResponse --> APIGateway
    APIGateway --> WebApp
    APIGateway --> MobileApp
    APIGateway --> DesktopApp
    
    %% Styling
    classDef inputClass fill:#E1D5E7,stroke:#9673A6,stroke-width:2px
    classDef apiClass fill:#FFF2CC,stroke:#D6B656,stroke-width:2px
    classDef lambdaClass fill:#FFE6CC,stroke:#D79B00,stroke-width:2px
    classDef aiClass fill:#E8F5E9,stroke:#116D5B,stroke-width:2px
    classDef storageClass fill:#E3F2FD,stroke:#3334B9,stroke-width:2px
    classDef monitorClass fill:#FCE4EC,stroke:#C7131F,stroke-width:2px
    classDef outputClass fill:#D5E8D4,stroke:#82B366,stroke-width:2px
    
    class WebApp,MobileApp,DesktopApp,Camera,ImageCapture,Base64Encode inputClass
    class APIGateway,CORS,Auth apiClass
    class EnrollLambda,IdentifyLambda,UtilityLambda lambdaClass
    class RekDetect,RekIndex,RekSearch,FaceVector aiClass
    class S3Images,DDBUsers,DDBEmbeddings,DDBLogs,SSMParams storageClass
    class CloudWatchLogs,CloudWatchMetrics monitorClass
    class JSONResponse,ResultFormat outputClass
```

---

## 📊 Enrollment Data Flow (Detailed)

```mermaid
flowchart TD
    Start([User Captures Photo]) --> Input{Input Validation}
    
    Input -->|Valid| B64[Base64 Encode Image]
    Input -->|Invalid| Error1[Error: Invalid Input]
    
    B64 --> API[POST /enroll<br/>to API Gateway]
    
    API --> Lambda[EnrollFunction<br/>Triggered]
    
    Lambda --> Decode[Decode Base64<br/>to Binary Image]
    Decode --> GenID[Generate UUID<br/>person_id]
    
    GenID --> S3Upload[Upload to S3<br/>enrollments/person_id.jpg]
    S3Upload -->|Success| S3Store[(S3 Storage<br/>Image Stored)]
    S3Upload -->|Fail| Error2[Error: S3 Upload Failed]
    
    S3Store --> RekIndex[Rekognition<br/>IndexFaces API]
    
    RekIndex --> FaceDetect{Face Detected?}
    FaceDetect -->|No| Error3[Error: No Face Found]
    FaceDetect -->|Multiple| Error4[Error: Multiple Faces]
    FaceDetect -->|Yes| ExtractFeatures[Extract Face Features<br/>512-dim Vector]
    
    ExtractFeatures --> Quality{Image Quality<br/>Check}
    Quality -->|Low| Error5[Error: Poor Image Quality]
    Quality -->|Good| StoreFace[Store face_id<br/>in Rekognition Collection]
    
    StoreFace --> SaveEmbed[Save to DynamoDB<br/>Embeddings Table]
    SaveEmbed --> SaveUser[Save to DynamoDB<br/>Users Table]
    
    SaveUser --> GetThreshold[Get Threshold<br/>from SSM]
    GetThreshold --> LogEnroll[Log to CloudWatch]
    
    LogEnroll --> Response{Build Response}
    Response --> Success[Success Response<br/>person_id, face_id, confidence]
    
    Error1 --> ErrorResponse[Error Response<br/>400/500]
    Error2 --> ErrorResponse
    Error3 --> ErrorResponse
    Error4 --> ErrorResponse
    Error5 --> ErrorResponse
    
    Success --> End([Return to Client])
    ErrorResponse --> End
    
    style Start fill:#E1D5E7
    style End fill:#D5E8D4
    style Success fill:#D5E8D4
    style Error1 fill:#F8CECC
    style Error2 fill:#F8CECC
    style Error3 fill:#F8CECC
    style Error4 fill:#F8CECC
    style Error5 fill:#F8CECC
    style ErrorResponse fill:#F8CECC
```

---

## 🔍 Identification Data Flow (Detailed)

```mermaid
flowchart TD
    Start([User Captures Photo<br/>for Identification]) --> Input{Input Validation}
    
    Input -->|Valid| B64[Base64 Encode Image]
    Input -->|Invalid| Error1[Error: Invalid Input]
    
    B64 --> API[POST /identify<br/>to API Gateway]
    API --> Lambda[IdentifyFunction<br/>Triggered]
    
    Lambda --> GetThreshold[Get Threshold<br/>from SSM Parameter Store]
    GetThreshold --> Decode[Decode Base64<br/>to Binary Image]
    
    Decode --> RekSearch[Rekognition<br/>SearchFacesByImage API]
    
    RekSearch --> FaceDetect{Face Detected?}
    FaceDetect -->|No| Error2[Error: No Face Found]
    FaceDetect -->|Yes| SearchCollection[Search in<br/>Rekognition Collection]
    
    SearchCollection --> MatchFound{Match Found?}
    MatchFound -->|No| NoMatch[Return: No Match<br/>Unknown Person]
    
    MatchFound -->|Yes| GetSimilarity[Get Similarity Score<br/>0-100%]
    GetSimilarity --> CompareThreshold{Similarity >=<br/>Threshold?}
    
    CompareThreshold -->|No| LowConfidence[Return: Low Confidence<br/>Below Threshold]
    CompareThreshold -->|Yes| QueryUser[Query Users Table<br/>by person_id]
    
    QueryUser --> QueryEmbed[Query Embeddings Table<br/>for face details]
    QueryEmbed --> LogAccess[Log to Access Logs Table<br/>timestamp, confidence, result]
    
    LogAccess --> LogCW[Log to CloudWatch]
    LogCW --> BuildResponse[Build Success Response<br/>person_id, name, confidence]
    
    BuildResponse --> Success[Success Response<br/>Match Found]
    NoMatch --> Success2[Success Response<br/>No Match]
    LowConfidence --> Success3[Success Response<br/>Low Confidence]
    
    Error1 --> ErrorResponse[Error Response<br/>400]
    Error2 --> ErrorResponse
    
    Success --> End([Return to Client])
    Success2 --> End
    Success3 --> End
    ErrorResponse --> End
    
    style Start fill:#E1D5E7
    style End fill:#D5E8D4
    style Success fill:#D5E8D4
    style Success2 fill:#FFF9E6
    style Success3 fill:#FFF9E6
    style Error1 fill:#F8CECC
    style Error2 fill:#F8CECC
    style ErrorResponse fill:#F8CECC
```

---

## 📦 Data Types & Transformations

### Input Data Format

```json
// Enrollment Request
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "name": "John Doe",
  "user_name": "john.doe",
  "metadata": {
    "department": "IT",
    "employee_id": "E001",
    "role": "Developer"
  }
}

// Identification Request
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "use_case": "attendance"
}
```

### Processing Transformations

```
1. Base64 String (from client)
   ↓
2. Binary Image Data (Lambda decode)
   ↓
3. Image Validation (size, format, dimensions)
   ↓
4. Face Detection (Rekognition)
   ↓
5. 512-Dimensional Vector (embedding)
   ↓
6. Normalized Vector (0-1 range)
   ↓
7. Storage in DynamoDB (JSON format)
```

### Output Data Format

```json
// Enrollment Response
{
  "success": true,
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "face_id": "face_20251120_103000",
  "rekognition_face_id": "2a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p",
  "confidence": 99.87,
  "s3_url": "s3://bucket/enrollments/550e8400.jpg",
  "bounding_box": {
    "Width": 0.5,
    "Height": 0.6,
    "Left": 0.2,
    "Top": 0.1
  },
  "timestamp": "2025-11-20T10:30:00Z"
}

// Identification Response (Match Found)
{
  "success": true,
  "match": true,
  "person_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "John Doe",
  "user_name": "john.doe",
  "confidence": 98.5,
  "threshold": 90.0,
  "metadata": {
    "department": "IT",
    "employee_id": "E001"
  },
  "timestamp": "2025-11-20T10:35:00Z"
}

// Identification Response (No Match)
{
  "success": true,
  "match": false,
  "reason": "No matching face found",
  "timestamp": "2025-11-20T10:35:00Z"
}
```

---

## 📊 Data Size Estimates

### Image Data
- **Input**: 1-5 MB (JPEG/PNG from client)
- **Base64 Encoded**: +33% size increase (1.3-6.5 MB)
- **S3 Storage**: Original size (1-5 MB per image)
- **Lambda Memory**: 10 MB buffer for processing

### Embedding Vector
- **Dimensions**: 512 floats
- **Size**: 512 × 4 bytes = 2,048 bytes (2 KB)
- **DynamoDB Storage**: ~8 KB (with metadata)

### Response Payload
- **Enrollment**: ~500 bytes (JSON)
- **Identification**: ~800 bytes (JSON)
- **List People**: ~5-50 KB (depending on page size)

---

## 🔄 Data Flow States

### Enrollment States
```
IDLE → CAPTURING → ENCODING → UPLOADING → DETECTING → 
INDEXING → STORING → LOGGING → SUCCESS
                ↓ (at any point)
              ERROR
```

### Identification States
```
IDLE → CAPTURING → ENCODING → SEARCHING → MATCHING → 
QUERYING → LOGGING → SUCCESS
                ↓ (at any point)
              NO_MATCH / LOW_CONFIDENCE / ERROR
```

---

## ⚡ Performance Metrics

| Stage | Average Time | Max Time | Data Transfer |
|-------|--------------|----------|---------------|
| Image Capture | 100-500ms | 2s | Client-side |
| Base64 Encode | 50-200ms | 500ms | Client-side |
| API Gateway | 10-50ms | 200ms | HTTP headers |
| Lambda Cold Start | 1-3s | 5s | N/A |
| Lambda Warm | 100-500ms | 1s | N/A |
| S3 Upload | 200-800ms | 2s | 1-5 MB |
| Rekognition Index | 500-1500ms | 3s | 1-5 MB |
| Rekognition Search | 300-1000ms | 2s | 1-5 MB |
| DynamoDB Write | 10-50ms | 200ms | <1 KB |
| DynamoDB Query | 10-30ms | 100ms | <10 KB |
| **Total Enrollment** | **2-3s** | **8s** | 1-5 MB |
| **Total Identification** | **1-2s** | **5s** | 1-5 MB |

---

## 🔐 Data Security Flow

```mermaid
graph LR
    A[Client] -->|TLS 1.2+| B[API Gateway]
    B -->|IAM Auth| C[Lambda]
    C -->|KMS Encrypted| D[S3]
    C -->|KMS Encrypted| E[DynamoDB]
    C -->|IAM Role| F[Rekognition]
    
    style A fill:#E1D5E7
    style B fill:#FFF2CC
    style C fill:#FFE6CC
    style D fill:#D5E8D4
    style E fill:#E3F2FD
    style F fill:#E8F5E9
```

**Security Measures:**
- ✅ TLS 1.2+ for all client connections
- ✅ IAM roles for Lambda execution
- ✅ KMS encryption at rest (S3, DynamoDB)
- ✅ VPC endpoints for private connectivity
- ✅ CloudWatch audit logs
- ✅ Parameter Store for sensitive configs
