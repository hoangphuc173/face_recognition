@echo off
REM Deploy Web Frontend to S3 + CloudFront (Windows) - Non-Interactive

echo ============================================
echo    Deploying Web Frontend to AWS
echo ============================================
echo.

REM Step 1: Build Next.js app
echo Step 1/4: Building Next.js app...
cd frontend\web
call npm install
call npm run export
echo ✅ Build complete. Output in: out\
echo.

REM Step 2: Deploy CDK Frontend Stack
echo Step 2/4: Deploying CDK Frontend Stack...
cd ..\..\infrastructure
call npm install
call npx cdk deploy FaceRecogFrontendStack --require-approval never
echo ✅ CDK stack deployed
echo.

REM Step 3: Get outputs
echo Step 3/4: Getting deployment info...
for /f "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name FaceRecogFrontendStack --query "Stacks[0].Outputs[?OutputKey=='WebBucketName'].OutputValue" --output text') do set BUCKET_NAME=%%i
for /f "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name FaceRecogFrontendStack --query "Stacks[0].Outputs[?OutputKey=='DistributionId'].OutputValue" --output text') do set DISTRIBUTION_ID=%%i
for /f "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name FaceRecogFrontendStack --query "Stacks[0].Outputs[?OutputKey=='WebFrontendUrl'].OutputValue" --output text') do set CLOUDFRONT_URL=%%i

echo Bucket: %BUCKET_NAME%
echo Distribution: %DISTRIBUTION_ID%
echo.

REM Step 4: Upload to S3
echo Step 4/4: Uploading to S3...
cd ..\frontend\web
aws s3 sync out\ s3://%BUCKET_NAME%/ --delete
echo ✅ Files uploaded
echo.

REM Step 5: Invalidate cache
echo Invalidating CloudFront cache...
aws cloudfront create-invalidation --distribution-id %DISTRIBUTION_ID% --paths "/*"
echo ✅ Cache invalidated
echo.

echo ============================================
echo    DEPLOYMENT COMPLETE!
echo ============================================
echo.
echo Web App URL: %CLOUDFRONT_URL%
echo.
