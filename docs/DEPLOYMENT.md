# Deployment Guide

This guide provides instructions for deploying the Face Recognition System. It covers both local setup for development and production deployment on AWS.

## Prerequisites

-   Python 3.11+
-   Node.js 18+
-   Go 1.21+ (for Lambda functions)
-   Rust (for Lambda functions, optional)
-   AWS CLI v2, configured with appropriate credentials
-   AWS CDK 2.x
-   Terraform (optional, for alternative IaC)

## 1. Local Development Setup

### Backend

1.  **Navigate to the backend directory:**

    ```bash
    cd aws/backend
    ```

2.  **Create a virtual environment and install dependencies:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Set up environment variables:**

    Create a `.env` file in the `aws/backend` directory and populate it with the necessary configuration (e.g., database credentials, AWS region).

4.  **Run the FastAPI server:**

    ```bash
    uvicorn api.app:app --reload
    ```

The API will be available at `http://127.0.0.1:8000`.

### Frontend (Desktop App)

1.  **Navigate to the app directory:**

    ```bash
    cd app
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application:**

    ```bash
    python gui_app.py
    ```

## 2. Production Deployment on AWS

The infrastructure is managed using AWS CDK. This is the recommended way to deploy the system to production.

### Building Lambda Functions

The project includes Lambda functions written in different languages (Python, Go, Rust). The CDK deployment process handles the building and packaging of these functions automatically. Ensure you have the necessary toolchains installed on your deployment machine:

-   **Go:** Install Go 1.21+ for the `image-processor-go` function.
-   **Rust:** Install Rust for the `image-processor-rs` function.

### Deploying with CDK

1.  **Navigate to the CDK directory:**

    ```bash
    cd aws/infrastructure/cdk
    ```

2.  **Install Node.js dependencies:**

    ```bash
    npm install
    ```

3.  **Bootstrap CDK (if you haven't already):**

    ```bash
    cdk bootstrap
    ```

4.  **Deploy the stack:**

    ```bash
    cdk deploy
    ```

This command will provision all the necessary AWS resources, including:

-   API Gateway (REST API)
-   Lambda functions for backend logic (Python, Go, and Rust)
-   DynamoDB tables:
    -   `face-recognition-people-{env}`: People metadata
    -   `face-recognition-embeddings-{env}`: Face embeddings
    -   `face-recognition-matches-{env}`: Identification history
-   S3 buckets for image storage
-   Amazon Rekognition Face Collection
-   IAM roles and policies
-   CloudWatch Logs and Metrics
-   ElastiCache Redis (optional, for caching)

After deployment, the CDK output will provide the URL for the deployed API Gateway endpoint. The FastAPI application can also be run directly on EC2/ECS or as a containerized service.
