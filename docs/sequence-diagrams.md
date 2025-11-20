# Face Recognition System - Sequence Diagrams

## 🔄 Enrollment Flow (POST /enroll)

```mermaid
sequenceDiagram
    participant Client
    participant API as API Gateway
    participant Lambda as EnrollFunction
    participant S3 as S3 Bucket
    participant Rek as Rekognition
    participant DDB as DynamoDB
    participant SSM as Systems Manager
    participant CW as CloudWatch

    Client->>API: POST /enroll<br/>{image: base64, name, metadata}
    API->>Lambda: Invoke EnrollFunction
    
    Lambda->>CW: Log: Start enrollment
    Lambda->>SSM: Get threshold config
    SSM-->>Lambda: Return: attendance=90%
    
    Lambda->>Lambda: Decode base64 image
    Lambda->>Lambda: Generate person_id (UUID)
    
    Lambda->>S3: Upload image<br/>s3://bucket/enrollments/{person_id}.jpg
    S3-->>Lambda: Success: S3 URL
    
    Lambda->>Rek: IndexFaces(image, collection_id)
    Rek->>Rek: Detect face features
    Rek->>Rek: Extract 512-dim embedding
    Rek-->>Lambda: Return: face_id, confidence, bounding_box
    
    alt No face detected
        Lambda->>CW: Log: No face detected
        Lambda-->>API: Error 400: No face in image
        API-->>Client: Error response
    end
    
    Lambda->>DDB: PutItem to Users table<br/>{person_id, name, metadata, s3_url}
    DDB-->>Lambda: Success
    
    Lambda->>DDB: PutItem to Embeddings table<br/>{person_id, face_id, embedding, timestamp}
    DDB-->>Lambda: Success
    
    Lambda->>CW: Log: Enrollment success
    Lambda-->>API: Success 200<br/>{person_id, face_id, confidence}
    API-->>Client: Success response
```

---

## 🔍 Identification Flow (POST /identify)

```mermaid
sequenceDiagram
    participant Client
    participant API as API Gateway
    participant Lambda as IdentifyFunction
    participant Rek as Rekognition
    participant SSM as Systems Manager
    participant DDB as DynamoDB
    participant CW as CloudWatch

    Client->>API: POST /identify<br/>{image: base64, use_case}
    API->>Lambda: Invoke IdentifyFunction
    
    Lambda->>CW: Log: Start identification
    Lambda->>SSM: Get threshold for use_case
    SSM-->>Lambda: Return: threshold (90/95/98%)
    
    Lambda->>Lambda: Decode base64 image
    
    Lambda->>Rek: SearchFacesByImage(image, collection_id)
    Rek->>Rek: Detect face features
    Rek->>Rek: Extract embedding
    Rek->>Rek: Search in collection
    Rek-->>Lambda: Return: matches[] with face_id, similarity
    
    alt No face detected
        Lambda->>CW: Log: No face detected
        Lambda-->>API: Error 400: No face in image
        API-->>Client: Error response
    end
    
    alt No match found
        Lambda->>CW: Log: No match found
        Lambda-->>API: Success 200<br/>{match: false, message: "Unknown person"}
        API-->>Client: No match response
    end
    
    Lambda->>Lambda: Filter by threshold<br/>(similarity >= threshold)
    
    alt Similarity below threshold
        Lambda->>CW: Log: Low confidence match
        Lambda-->>API: Success 200<br/>{match: false, reason: "Low confidence"}
        API-->>Client: Low confidence response
    end
    
    Lambda->>DDB: Query Users table<br/>by person_id (from face_id)
    DDB-->>Lambda: Return: {name, metadata}
    
    Lambda->>DDB: Query Embeddings table<br/>for face details
    DDB-->>Lambda: Return: {face_id, enrollment_date}
    
    Lambda->>DDB: PutItem to AccessLogs table<br/>{log_id, person_id, timestamp, confidence}
    DDB-->>Lambda: Success
    
    Lambda->>CW: Log: Identification success
    Lambda-->>API: Success 200<br/>{match: true, person_id, name, confidence}
    API-->>Client: Match found response
```

---

## 📊 Health Check Flow (GET /health)

```mermaid
sequenceDiagram
    participant Client
    participant API as API Gateway
    participant Lambda as HealthFunction
    participant DDB as DynamoDB
    participant CW as CloudWatch

    Client->>API: GET /health
    API->>Lambda: Invoke HealthFunction
    
    Lambda->>DDB: DescribeTable(Users)
    DDB-->>Lambda: Table status: ACTIVE
    
    Lambda->>DDB: Query: COUNT(*)
    DDB-->>Lambda: Return: user_count
    
    Lambda->>CW: Log: Health check
    Lambda-->>API: Success 200<br/>{status: "healthy", users: count}
    API-->>Client: Health status
```

---

## 👥 List People Flow (GET /people)

```mermaid
sequenceDiagram
    participant Client
    participant API as API Gateway
    participant Lambda as ListPeopleFunction
    participant DDB as DynamoDB
    participant CW as CloudWatch

    Client->>API: GET /people?limit=20
    API->>Lambda: Invoke ListPeopleFunction
    
    Lambda->>DDB: Scan Users table<br/>(limit=20, filter)
    DDB-->>Lambda: Return: items[], LastEvaluatedKey
    
    Lambda->>Lambda: Format response
    Lambda->>CW: Log: Listed {count} people
    Lambda-->>API: Success 200<br/>{people: [], count, next_token}
    API-->>Client: People list
```

---

## 📈 Stats Flow (GET /stats)

```mermaid
sequenceDiagram
    participant Client
    participant API as API Gateway
    participant Lambda as DbStatsFunction
    participant DDB as DynamoDB
    participant CW as CloudWatch

    Client->>API: GET /stats
    API->>Lambda: Invoke DbStatsFunction
    
    par Parallel Queries
        Lambda->>DDB: DescribeTable(Users)
        DDB-->>Lambda: {ItemCount, TableSize}
        
        Lambda->>DDB: DescribeTable(Embeddings)
        DDB-->>Lambda: {ItemCount, TableSize}
        
        Lambda->>DDB: DescribeTable(AccessLogs)
        DDB-->>Lambda: {ItemCount, TableSize}
    end
    
    Lambda->>Lambda: Calculate totals
    Lambda->>CW: Log: Stats retrieved
    Lambda-->>API: Success 200<br/>{users, embeddings, logs, total_size}
    API-->>Client: Statistics
```

---

## ⚙️ Get Thresholds Flow (GET /thresholds)

```mermaid
sequenceDiagram
    participant Client
    participant API as API Gateway
    participant Lambda as GetThresholdsFunction
    participant SSM as Systems Manager
    participant CW as CloudWatch

    Client->>API: GET /thresholds
    API->>Lambda: Invoke GetThresholdsFunction
    
    par Get All Thresholds
        Lambda->>SSM: GetParameter(/threshold/attendance)
        SSM-->>Lambda: Return: 90
        
        Lambda->>SSM: GetParameter(/threshold/access_control)
        SSM-->>Lambda: Return: 95
        
        Lambda->>SSM: GetParameter(/threshold/financial)
        SSM-->>Lambda: Return: 98
    end
    
    Lambda->>Lambda: Format response
    Lambda->>CW: Log: Thresholds retrieved
    Lambda-->>API: Success 200<br/>{attendance: 90, access_control: 95, financial: 98}
    API-->>Client: Thresholds config
```

---

## 🔴 Error Handling Flows

### Rekognition Error

```mermaid
sequenceDiagram
    participant Lambda
    participant Rek as Rekognition
    participant CW as CloudWatch
    participant Client

    Lambda->>Rek: IndexFaces(image)
    Rek-->>Lambda: Error: InvalidImageFormatException
    
    Lambda->>CW: Log: Invalid image format
    Lambda->>Lambda: Format error response
    Lambda-->>Client: Error 400<br/>{error: "Invalid image format"}
```

### DynamoDB Error

```mermaid
sequenceDiagram
    participant Lambda
    participant DDB as DynamoDB
    participant CW as CloudWatch
    participant Client

    Lambda->>DDB: PutItem(person)
    DDB-->>Lambda: Error: ConditionalCheckFailedException
    
    Lambda->>CW: Log: Person already exists
    Lambda->>Lambda: Format error response
    Lambda-->>Client: Error 409<br/>{error: "Person already enrolled"}
```

---

## 📊 Flow Summary

| Flow | Method | Lambda | Services Used | Response Time |
|------|--------|--------|---------------|---------------|
| Enrollment | POST /enroll | EnrollFunction | S3, Rekognition, DynamoDB, SSM | ~2-3s |
| Identification | POST /identify | IdentifyFunction | Rekognition, DynamoDB, SSM | ~1-2s |
| Health Check | GET /health | HealthFunction | DynamoDB | ~100-200ms |
| List People | GET /people | ListPeopleFunction | DynamoDB | ~200-500ms |
| Stats | GET /stats | DbStatsFunction | DynamoDB | ~300-600ms |
| Thresholds | GET /thresholds | GetThresholdsFunction | SSM | ~100-200ms |

---

## 🔑 Key Points

### Enrollment Process:
1. Validate & decode image
2. Upload to S3
3. Index face with Rekognition
4. Store user + embedding in DynamoDB
5. Return person_id

### Identification Process:
1. Validate & decode image
2. Search face in Rekognition collection
3. Check confidence threshold
4. Query user details from DynamoDB
5. Log access
6. Return match result

### Error Scenarios:
- **No face detected**: 400 Bad Request
- **Multiple faces**: 400 Bad Request (current implementation)
- **Low confidence**: 200 OK with match=false
- **No match**: 200 OK with match=false
- **Service errors**: 500 Internal Server Error
