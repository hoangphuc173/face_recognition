#!/bin/bash
# Build Lambda Layer with Python dependencies

echo "📦 Building Lambda Layer..."

cd services/lambda-serverless/layers/python-deps

# Remove old build
rm -rf python/
mkdir -p python/

# Install dependencies
pip install -r requirements.txt -t python/

# Create deployment package
zip -r python-deps-layer.zip python/

echo "✅ Lambda layer built: python-deps-layer.zip"
