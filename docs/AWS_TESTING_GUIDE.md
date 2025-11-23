# AWS Testing & Verification Guide

Hướng dẫn test và verify toàn bộ hệ thống sau khi deploy.

---

## Testing Checklist

- [ ] Infrastructure deployed successfully
- [ ] Lambda functions working
- [ ] API Gateway configured
- [ ] Frontend deployed to Amplify
- [ ] End-to-end authentication flow
- [ ] Face enrollment works
- [ ] Face identification works
- [ ] RBAC permissions work

---

## Step 1: Verify Infrastructure

### CloudFormation Stack

```bash
aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].StackStatus'
```

**Expected**: `CREATE_COMPLETE` or `UPDATE_COMPLETE`

### Cognito User Pool

```bash
USER_POOL_ID=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
  --output text)

aws cognito-idp describe-user-pool --user-pool-id $USER_POOL_ID
```

**Expected**: User Pool với Admin, Staff, Guest groups

### S3 Bucket

```bash
S3_BUCKET=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' \
  --output text)

# Check encryption
aws s3api get-bucket-encryption --bucket $S3_BUCKET
```

**Expected**: AES256 encryption enabled

### DynamoDB Table

```bash
TABLE_NAME=$(aws cloudformation describe-stacks \
  --stack-name FaceRecognitionStack-prod \
  --query 'Stacks[0].Outputs[?OutputKey==`DynamoDBTableName`].OutputValue' \
  --output text)

aws dynamodb describe-table --table-name $TABLE_NAME
```

**Expected**: Table status ACTIVE

---

## Step 2: Test Lambda Functions

### Test Auth Handler

```bash
# Test health endpoint
aws lambda invoke \
  --function-name auth-handler \
  --payload '{"resource":"/auth/health","httpMethod":"GET"}' \
  response.json

cat response.json
```

**Expected**: `{"status": "healthy"}`

### Test Enroll Handler

```bash
# Create base64 image (placeholder)
echo "Test payload" | base64 > test-image.txt

aws lambda invoke \
  --function-name enroll-handler \
  --payload '{"email":"test@example.com","image":"'$(cat test-image.txt)'"}' \
  response.json

cat response.json
```

### Test Identify Handler

```bash
aws lambda invoke \
  --function-name identify-handler \
  --payload '{"image":"'$(cat test-image.txt)'"}' \
  response.json

cat response.json
```

### Test People Handler

```bash
aws lambda invoke \
  --function-name people-handler \
 --payload '{"httpMethod":"GET","resource":"/people"}' \
  response.json

cat response.json
```

---

## Step 3: Test API Gateway

### Get API URL

```bash
API_ID=$(aws apigateway get-rest-apis \
  --query 'items[?name==`face-recognition-api`].id' \
  --output text)

API_URL="https://$API_ID.execute-api.us-east-1.amazonaws.com/prod"
echo "API URL: $API_URL"
```

### Test Registration

```bash
curl -X POST $API_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "Test123!",
    "full_name": "Test User"
  }'
```

**Expected**: `{"message": "User registered. Check email for verification code."}`

### Test Login (after verification)

```bash
curl -X POST $API_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "Test123!"
  }'
```

**Expected**: JWT token in response

---

## Step 4: Test Frontend (Amplify)

### Access Application

Open Amplify URL in browser:
```
https://master.APP_ID.amplifyapp.com
```

### Test User Registration

1. Click "Register" or "Sign Up"
2. Fill in:
   - Email: `user@example.com`
   - Password: `Test123!`
   - Full Name: `John Doe`
3. Submit form

**Expected**: "Check your email for verification code"

### Verify Email

1. Check email inbox
2. Copy verification code
3. Enter code in verification form
4. Submit

**Expected**: "Email verified successfully"

### Test Login

1. Go to login page
2. Enter:
   - Email: `user@example.com`
   - Password: `Test123!`
3. Submit

**Expected**: Redirect to dashboard

### Test Face Enrollment

1. After login, go to "Enroll" page
2. Click "Choose File" or use webcam
3. Upload a face image
4. Submit

**Expected**: 
- "Face enrolled successfully"
- Image appears in user profile
- User added to DynamoDB

**Verify in Backend**:
```bash
# Check S3
aws s3 ls s3://$S3_BUCKET/ --recursive

# Check DynamoDB
aws dynamodb scan --table-name $TABLE_NAME
```

### Test Face Identification

1. Go to "Identify" page
2. Upload same face image
3. Submit

**Expected**:
- "Face recognized: John Doe"
- Confidence score > 90%
- Bounding box drawn around face

### Test People Management

1. Go to "People" page
2. View list of enrolled users

**Expected**: List shows John Doe with image

---

## Step 5: Test RBAC (Role-Based Access)

### Create Admin User

```bash
# Create admin
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username admin@example.com \
  --user-attributes Name=email,Value=admin@example.com \
  --temporary-password Admin123!

# Add to Admin group
aws cognito-idp admin-add-user-to-group \
  --user-pool-id $USER_POOL_ID \
  --username admin@example.com \
  --group-name Admin

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username admin@example.com \
  --password Admin123! \
  --permanent
```

### Test Admin Permissions

Login as admin and verify:
- ✅ Can view all users
- ✅ Can delete users
- ✅ Can enroll faces
- ✅ Can identify faces

### Create Staff User

```bash
aws cognito-idp admin-create-user \
  --user-pool-id $USER_POOL_ID \
  --username staff@example.com \
  --user-attributes Name=email,Value=staff@example.com \
  --temporary-password Staff123!

aws cognito-idp admin-add-user-to-group \
  --user-pool-id $USER_POOL_ID \
  --username staff@example.com \
  --group-name Staff

aws cognito-idp admin-set-user-password \
  --user-pool-id $USER_POOL_ID \
  --username staff@example.com \
  --password Staff123! \
  --permanent
```

### Test Staff Permissions

Login as staff and verify:
- ✅ Can enroll faces
- ✅ Can identify faces
- ❌ Cannot delete users (should show error)

---

## Step 6: Performance Testing

### Lambda Cold Start

```bash
# Invoke after 5 minutes of inactivity
time aws lambda invoke \
  --function-name auth-handler \
  --payload '{"action":"health"}' \
  response.json
```

**Expected**: < 3 seconds

### Lambda Warm Start

```bash
# Invoke immediately after
time aws lambda invoke \
  --function-name auth-handler \
  --payload '{"action":"health"}' \
  response.json
```

**Expected**: < 500ms

### Concurrent Requests

```bash
# Send 10 concurrent requests
for i in {1..10}; do
  curl -X POST $API_URL/auth/health &
done
wait
```

**Expected**: All requests succeed

---

## Step 7: Check CloudWatch Logs

### View Lambda Logs

```bash
# Tail auth handler logs
aws logs tail /aws/lambda/auth-handler --follow

# Get last 100 lines
aws logs tail /aws/lambda/auth-handler --since 10m
```

### View API Gateway Logs

```bash
# Enable logging first if not enabled
aws apigateway update-stage \
  --rest-api-id $API_ID \
  --stage-name prod \
  --patch-operations op=replace,path=/accessLogSettings/destinationArn,value=arn:aws:logs:us-east-1:ACCOUNT:log-group:api-gateway-logs

# View logs
aws logs tail /aws/apigateway/$API_ID/prod --follow
```

---

## Step 8: Security Testing

### Test CORS

```bash
# Test OPTIONS request
curl -X OPTIONS $API_URL/auth/register \
  -H "Origin: https://example.com" \
  -H "Access-Control-Request-Method: POST"
```

**Expected**: CORS headers present

### Test Authentication

```bash
# Try to access protected endpoint without token
curl -X GET $API_URL/people

# Expected: 401 Unauthorized
```

### Test Invalid Inputs

```bash
# Test with invalid email
curl -X POST $API_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "not-an-email",
    "password": "Test123!"
  }'
```

**Expected**: Validation error

---

## Step 9: Load Testing (Optional)

### Using Apache Bench

```bash
# Install ab
# Windows: Download from Apache
# Linux: apt-get install apache2-utils

# Test 100 requests, 10 concurrent
ab -n 100 -c 10 -T "application/json" \
  -p test-payload.json \
  $API_URL/auth/health
```

### Using Artillery

```bash
npm install -g artillery

# Create artillery config
cat > load-test.yml <<EOF
config:
  target: "$API_URL"
  phases:
    - duration: 60
      arrivalRate: 10
scenarios:
  - flow:
      - post:
          url: "/auth/health"
EOF

# Run test
artillery run load-test.yml
```

---

## Verification Checklist

After all tests:

- [ ] Infrastructure: All resources created and configured
- [ ] Lambda: All 4 functions deployed and responsive
- [ ] API Gateway: All endpoints accessible
- [ ] Frontend: Deployed to Amplify and accessible
- [ ] Authentication: Register, verify, login working
- [ ] Enrollment: Face upload and indexing working
- [ ] Identification: Face recognition working with >90% confidence
- [ ] RBAC: Admin/Staff/Guest permissions working correctly
- [ ] Logs: CloudWatch logs capturing all operations
- [ ] Performance: Cold start <3s, warm start <500ms
- [ ] Security: CORS, authentication, input validation working

---

## Success Criteria

✅ All Lambda functions return 200 status
✅ API Gateway routes to correct Lambdas
✅ Frontend loads and displays correctly
✅ User can register, verify, and login
✅ Face enrollment stores image in S3
✅ Face identification returns correct user ID
✅ RBAC permissions enforced
✅ No errors in CloudWatch logs
✅ Performance within acceptable limits
