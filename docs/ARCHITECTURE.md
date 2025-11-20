# System Architecture

This document provides a detailed overview of the Face Recognition System's architecture. The system is designed to be modular, scalable, and flexible, supporting both cloud-native and hybrid deployment models.

## Core Principles

- **Decoupling:** Components are loosely coupled and communicate through well-defined APIs and message queues.
- **Scalability:** The architecture is designed to scale horizontally to handle varying loads.
- **Flexibility:** It supports different operational modes, including real-time identification, batch enrollment, and database management.

## High-Level Architecture

The system is composed of several key components:

1.  **API Gateway:** The single entry point for all client requests. It handles routing, authentication, and rate limiting.
2.  **Backend Services:** A set of microservices responsible for the core business logic.
3.  **Real-time Processing Pipeline:** A data-driven pipeline for processing real-time video streams.
4.  **Data Stores:** Databases and storage solutions for storing user data, face embeddings, and metadata.
5.  **Client Applications:** User-facing applications, including a desktop GUI and web clients.

## Component Breakdown

### 1. Backend API (`/aws/backend`)

A FastAPI-based application that exposes RESTful endpoints for managing the system.

-   **Main Application (`/api/app.py`):** Defines all API endpoints directly:
    -   `/health` and `/ready`: Health check endpoints
    -   `/api/v1/enroll`: Face enrollment endpoint
    -   `/api/v1/identify`: Face identification endpoint
    -   `/api/v1/people`: People management endpoints (GET, GET by ID, DELETE)
    -   `/api/v1/telemetry`: System telemetry endpoints
-   **Route Modules (`/api/routes/`):** Separate route files exist but are not currently integrated into the main app. These include:
    -   `auth.py`: Authentication routes (not currently used)
    -   `enroll.py`: Enrollment routes (alternative implementation)
    -   `identify.py`: Identification routes (alternative implementation)
    -   `people.py`: People management routes (alternative implementation)

### 2. AWS Integration (`/aws/backend/aws`)

This module contains clients for interacting with AWS services:

-   **DynamoDB (`dynamodb_client.py`):** Manages interaction with three DynamoDB tables:
    -   `People` table: Stores person metadata (person_id, user_name, gender, etc.)
    -   `Embeddings` table: Stores face embedding records (embedding_id, person_id, face_id, image_url, etc.)
    -   `Matches` table: Stores identification history (match_id, person_id, confidence, timestamp, etc.)
-   **S3 (`s3_client.py`):** Handles storage and retrieval of images.
-   **Rekognition (`rekognition_client.py`):** Interfaces with Amazon Rekognition for face detection and comparison.
-   **Secrets Manager (`secrets_manager_client.py`):** Manages retrieval of secrets.

### 3. Core Logic (`/aws/backend/core`)

Contains the main business logic of the application:

-   **`database_manager.py`:** A high-level abstraction for database operations, supporting multiple database types.
-   **`enrollment_service.py`:** Orchestrates the steps involved in enrolling a new face.
-   **`identification_service.py`:** Orchestrates the face identification workflow.

### 4. Infrastructure as Code (IaC)

The infrastructure is defined and managed using both AWS CDK and Terraform.

-   **CDK (`/aws/infrastructure/cdk`):** Defines the core cloud infrastructure, including Lambda functions, API Gateway, S3 buckets, and DynamoDB tables.
-   **Terraform (`/aws/infrastructure/terraform`):** Provides an alternative way to manage cloud resources.

## Data Flow

### Enrollment Flow

1.  Client sends an image and metadata to the `/api/v1/enroll` endpoint (multipart/form-data).
2.  The API validates the request and processes the image using `EnrollmentService`.
3.  The service uploads the image to S3 and calls Amazon Rekognition `IndexFaces` to add the face to the collection.
4.  Metadata is stored in DynamoDB (`People` and `Embeddings` tables).
5.  Response is returned synchronously with enrollment results.

### Real-time Identification Flow

1.  A camera or client captures an image and sends it to the `/api/v1/identify` endpoint (multipart/form-data).
2.  The backend receives the image and processes it using `IdentificationService`.
3.  The service calls Amazon Rekognition `SearchFacesByImage` to search the face collection.
4.  Matches are retrieved from DynamoDB and returned in the response.
5.  Results are returned synchronously with identification data.

This document serves as a high-level guide. For more detailed information, please refer to the source code and specific component documentation.
