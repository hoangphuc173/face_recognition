# Image Processor (Go)

This AWS Lambda function is responsible for processing images uploaded to the S3 `raw-images` bucket. It is written in Go for performance and efficiency.

## Functionality

1.  **Triggered by S3:** The function is automatically invoked when a new object is created in the `raw/` prefix of the S3 bucket.
2.  **Image Processing:** It performs face detection and indexing using Amazon Rekognition.
3.  **Stores Metadata:** The extracted facial embeddings and other metadata are stored in a DynamoDB table.
4.  **Saves Processed Image:** The processed image (e.g., with bounding boxes) is saved to the `processed-images` S3 bucket.

## Build & Deployment

This function is built and deployed automatically as part of the AWS CDK deployment process (`cdk deploy`).

The `build.sh` script in this directory handles the compilation of the Go binary and the creation of the `deployment.zip` package required for Lambda.

### Manual Build

To build the function manually, run the build script from within this directory:

```bash
./build.sh
```

This will produce a `deployment.zip` file in the `dist/` directory.

## Dependencies

-   [AWS Lambda Go](https://github.com/aws/aws-lambda-go)
-   [AWS SDK for Go V2](https://github.com/aws/aws-sdk-go-v2)

The dependencies are managed in the `go.mod` file.

