# Environment Variables for AWS Amplify

## Required Variables

Add these environment variables in the Amplify Console during deployment:

### Production Environment

```bash
# API Gateway URL (REQUIRED)
NEXT_PUBLIC_API_URL=https://YOUR-API-ID.execute-api.us-east-1.amazonaws.com/prod
```

## How to Get Your API Gateway URL

1. Open AWS Console
2. Navigate to **API Gateway**
3. Click on your API (likely named something like "face-recognition-api")
4. Click **Stages** in the left sidebar
5. Click **prod**
6. Copy the **Invoke URL** at the top
7. Example: `https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod`

## How to Add to Amplify

1. In Amplify Console > Your App > **Environment variables**
2. Click **Add environment variable**
3. Key: `NEXT_PUBLIC_API_URL`
4. Value: Your API Gateway URL (paste from above)
5. Click **Save**

## Verification

After deployment, you can verify the variable is set by:
- Checking browser console for API calls
- They should point to your production API Gateway URL
- NOT to `http://localhost:5555`

---

**Important Notes:**
- ✅ Variables starting with `NEXT_PUBLIC_` are exposed to the browser
- ✅ They must be set BEFORE the first deployment
- ⚠️ Changes to env vars require a new deployment (auto-triggered)
