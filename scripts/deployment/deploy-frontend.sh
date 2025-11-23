#!/bin/bash
# Deploy Web Frontend to S3 + CloudFront

set -e

echo "============================================"
echo "   Deploying Web Frontend to AWS"
echo "============================================"
echo ""

# Step 1: Build Next.js app
echo "Step 1/4: Building Next.js app..."
cd frontend/web
npm install
npm run export
echo "✅ Build complete. Output in: out/"
echo ""

# Step 2: Deploy CDK Frontend Stack
echo "Step 2/4: Deploying CDK Frontend Stack..."
cd ../../infrastructure
npm install
npx cdk deploy FaceRecogFrontendStack --require-approval never
echo "✅ CDK stack deployed"
echo ""

# Step 3: Get S3 bucket name and CloudFront ID
echo "Step 3/4: Getting deployment info..."
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name FaceRecogFrontendStack \
  --query "Stacks[0].Outputs[?OutputKey=='WebBucketName'].OutputValue" \
  --output text)

DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
  --stack-name FaceRecogFrontendStack \
  --query "Stacks[0].Outputs[?OutputKey=='DistributionId'].OutputValue" \
  --output text)

CLOUDFRONT_URL=$(aws cloudformation describe-stacks \
  --stack-name FaceRecogFrontendStack \
  --query "Stacks[0].Outputs[?OutputKey=='WebFrontendUrl'].OutputValue" \
  --output text)

echo "Bucket: $BUCKET_NAME"
echo "Distribution: $DISTRIBUTION_ID"
echo ""

# Step 4: Sync files to S3
echo "Step 4/4: Uploading to S3..."
cd ../frontend/web
aws s3 sync out/ s3://$BUCKET_NAME/ --delete
echo "✅ Files uploaded"
echo ""

# Step 5: Invalidate CloudFront cache
echo "Invalidating CloudFront cache..."
aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"
echo "✅ Cache invalidated"
echo ""

echo "============================================"
echo "   DEPLOYMENT COMPLETE!"
echo "============================================"
echo ""
echo "Web App URL: $CLOUDFRONT_URL"
echo ""
echo "Next steps:"
echo "1. Open the URL in your browser"
echo "2. Test the app functionality"
echo "3. Update DNS if using custom domain"
echo ""
