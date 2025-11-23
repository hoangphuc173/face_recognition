#!/bin/bash
set -e

# Get the directory of the script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define the output directory
OUTPUT_DIR="$SCRIPT_DIR/dist"

# Clean up previous builds
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# Build the Go binary for Lambda
cd "$SCRIPT_DIR"
GOOS=linux GOARCH=amd64 go build -o "$OUTPUT_DIR/main" main.go

# Create the deployment package
cd "$OUTPUT_DIR"
zip deployment.zip main

# Clean up the binary
rm main

echo "Build successful! Deployment package is at $OUTPUT_DIR/deployment.zip"

