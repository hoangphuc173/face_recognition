# API Endpoints

This document details the RESTful API endpoints provided by the backend service. The base URL for all endpoints is `/api/v1`.

## Health Checks

### 1. Health Check

-   **Endpoint:** `/health`
-   **Method:** `GET`
-   **Description:** Basic health check endpoint.
-   **Response:**

    ```json
    {
        "status": "healthy",
        "timestamp": "2025-01-20T10:00:00Z",
        "version": "2.0.0"
    }
    ```

### 2. Readiness Check

-   **Endpoint:** `/ready`
-   **Method:** `GET`
-   **Description:** Verifies all services are ready (database connectivity check).
-   **Response:**

    ```json
    {
        "status": "ready",
        "database": {"status": "ok"},
        "timestamp": "2025-01-20T10:00:00Z"
    }
    ```

## Enrollment

### 1. Enroll New Face

-   **Endpoint:** `/api/v1/enroll`
-   **Method:** `POST`
-   **Description:** Enrolls a new person by uploading an image and providing metadata.
-   **Request Body:** `multipart/form-data`
    -   `image`: Face image file (JPG, PNG) - **required**
    -   `user_name`: Full name of the person - **required**
    -   `gender`: Gender (optional)
    -   `birth_year`: Birth year (optional)
    -   `hometown`: Hometown (optional)
    -   `residence`: Current residence (optional)
-   **Response:**

    ```json
    {
        "success": true,
        "user_name": "John Doe",
        "person_id": "person_abc123",
        "face_id": "face_xyz789",
        "message": "✅ Created profile: John Doe (ID: person_abc123)",
        "duplicate_found": false,
        "duplicate_info": null,
        "image_url": "s3://bucket/enrollments/person_abc123/image.jpg",
        "quality_score": 0.95,
        "processing_time_ms": 1250.5
    }
    ```

## Identification

### 1. Identify Face

-   **Endpoint:** `/api/v1/identify`
-   **Method:** `POST`
-   **Description:** Identifies faces in an image using AWS Rekognition.
-   **Request Body:** `multipart/form-data`
    -   `image`: Image file containing face(s) - **required**
    -   `threshold`: Recognition threshold (0.0-1.0, default: 0.6, lower = more strict) - **optional**
-   **Response:**

    ```json
    {
        "success": true,
        "faces_detected": 1,
        "processing_time_ms": 850.2,
        "faces": [
            {
                "person_id": "person_abc123",
                "user_name": "John Doe",
                "gender": "Male",
                "birth_year": "1990",
                "hometown": "New York, USA",
                "residence": "London, UK",
                "confidence": 0.995,
                "similarity": 99.5,
                "face_id": "face_xyz789",
                "match_time": "2025-01-20T10:00:00Z"
            }
        ]
    }
    ```

## People Management

### 1. Get All People

-   **Endpoint:** `/api/v1/people`
-   **Method:** `GET`
-   **Description:** Retrieves a list of all enrolled people in the database.
-   **Response:**

    ```json
    [
        {
            "folder_name": "person_abc123",
            "person_id": "person_abc123",
            "user_name": "John Doe",
            "gender": "Male",
            "birth_year": "1990",
            "hometown": "New York, USA",
            "residence": "London, UK",
            "embedding_count": 3,
            "created_at": "2025-01-15T10:00:00Z",
            "updated_at": "2025-01-20T10:00:00Z"
        }
    ]
    ```

### 2. Get Person by ID

-   **Endpoint:** `/api/v1/people/{folder_name}`
-   **Method:** `GET`
-   **Description:** Retrieves detailed information about a specific person.
-   **Path Parameters:**
    -   `folder_name`: Person's unique ID (person_id)
-   **Response:**

    ```json
    {
        "folder_name": "person_abc123",
        "person_id": "person_abc123",
        "user_name": "John Doe",
        "gender": "Male",
        "birth_year": "1990",
        "hometown": "New York, USA",
        "residence": "London, UK",
        "embedding_count": 3,
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-20T10:00:00Z"
    }
    ```

### 3. Delete Person

-   **Endpoint:** `/api/v1/people/{folder_name}`
-   **Method:** `DELETE`
-   **Description:** Deletes a person and all their associated data from the system.
-   **Path Parameters:**
    -   `folder_name`: Person's unique ID (person_id)
-   **Response:**

    ```json
    {
        "success": true,
        "message": "Successfully deleted person 'person_abc123'"
    }
    ```

## Telemetry

### 1. Get System Telemetry

-   **Endpoint:** `/api/v1/telemetry`
-   **Method:** `GET`
-   **Description:** Get real-time system performance metrics.
-   **Response:**

    ```json
    {
        "cpu_usage": 15.5,
        "memory_usage": 45.8,
        "disk_usage": 75.2
    }
    ```

### 2. Ingest Telemetry Event

-   **Endpoint:** `/api/v1/telemetry`
-   **Method:** `POST`
-   **Description:** Receive telemetry events (for local testing/monitoring).
-   **Request Body:**

    ```json
    {
        "client_id": "client_123",
        "transport": "rest",
        "latency_ms": 150.5,
        "status": "success",
        "faces_detected": 1,
        "timestamp": "2025-01-20T10:00:00Z",
        "api_endpoint": "/api/v1/identify"
    }
    ```

## Notes

- All endpoints are currently **unauthenticated** for local development. In production, authentication should be enabled via AWS Cognito or JWT tokens.
- The API uses AWS Rekognition for face detection and recognition.
- Images are stored in AWS S3, metadata is stored in AWS DynamoDB.
- Response times vary based on AWS service latency and network conditions.

