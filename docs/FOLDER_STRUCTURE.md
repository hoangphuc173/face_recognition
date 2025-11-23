# Project Folder Structure

## Root Directory Overview

```
face_recognition/
├── backend/              # Backend Lambda functions and API
├── frontend/             # Frontend applications (web + desktop)
├── infrastructure/       # AWS CDK infrastructure as code
├── scripts/              # All scripts organized by purpose
├── environments/         # Environment configurations
├── docs/                 # Documentation
├── legacy/               # Archived legacy code
├── .gitignore           # Git ignore rules
└── README.md            # Main project documentation
```

---

## Backend Structure

```
backend/
├── src/                  # Source code
│   ├── auth/            # Authentication Lambda handler
│   ├── enroll/          # Face enrollment Lambda handler
│   ├── identify/        # Face identification Lambda handler
│   ├── people/          # People management Lambda handler
│   ├── api/             # API routes for local development
│   ├── logging/         # Logging utilities
│   └── shared/          # Shared utilities and models
├── tests/               # Backend tests
└── requirements.txt     # Python dependencies
```

**Note**: `backend/layer/` and `backend/layer_v2/` are gitignored (large build artifacts).

---

## Frontend Structure

```
frontend/
├── web/                 # Next.js web application (for AWS Amplify)
│   ├── app/            # Next.js 14+ App Router
│   ├── components/     # React components
│   ├── lib/           # Utilities and API client
│   └── public/        # Static assets
│
└── desktop/            # Tauri desktop application
    ├── src/           # React frontend code
    └── src-tauri/     # Rust backend code
```

---

## Scripts Organization

```
scripts/
├── local/              # LOCAL DEVELOPMENT
│   ├── backend/       
│   │   ├── start-backend-only.bat           # Backend API only
│   │   ├── debug-backend.bat                # Debug mode
│   │   └── restart-backend.bat              # Restart backend
│   ├── frontend/
│   │   ├── start-frontend.bat               # Web frontend
│   │   ├── start-frontend.ps1               # Web frontend (PS)
│   │   └── start-desktop-app.bat            # Desktop app
│   ├── start-full-local-system.bat          # Full system local
│   └── start-full-system-legacy.bat         # Legacy full system
│
├── cloud/              # CLOUD/AWS OPERATIONS
│   ├── backend/
│   │   ├── start-backend-cloud.bat          # Backend with cloud services
│   │   └── start-backend-lambda.bat         # Test Lambda locally
│   ├── deploy-lambda.ps1                     # Full Lambda deployment
│   ├── deploy-lambda-quick.ps1               # Quick Lambda deployment
│   ├── deploy-lambda-simple.ps1              # Simple Lambda deployment
│   ├── setup-aws.ps1                         # Full AWS setup
│   ├── setup-aws-simple.ps1                  # Simple AWS setup
│   └── start-cloud-system.bat                # Full cloud system
│
├── deployment/         # FULL DEPLOYMENT
│   ├── deploy-frontend.bat                   # Deploy frontend
│   ├── deploy-frontend.sh                    # Deploy frontend (sh)
│   ├── deploy-all.ps1                        # Deploy everything
│   └── deploy-full-system.ps1                # Full system deployment
│
├── utilities/          # HELPER UTILITIES
│   ├── build-layer.ps1                       # Build Lambda layer
│   ├── setup-smtp.ps1                        # Setup SMTP
│   ├── setup-brevo.ps1                       # Setup Brevo email
│   ├── verify-rbac.py                        # Verify RBAC
│   ├── promote-admin.bat                     # Promote user to admin
│   └── add-cloudfront-permissions.bat        # CloudFront permissions
│
└── testing/            # TEST SCRIPTS
    └── test-all.ps1                          # Run all tests
```

---

## Infrastructure (AWS CDK)

```
infrastructure/
├── bin/                # CDK app entry point
├── lib/               # CDK stack definitions
└── README.md          # Infrastructure documentation
```

---

## Environments Configurations

```
environments/
├── local/             # Local development configs
│   └── README.md     # Local env setup guide
└── cloud/            # Cloud/production configs
    └── README.md     # Cloud env setup guide
```

---

## Documentation

```
docs/
├── FOLDER_STRUCTURE.md      # This file
├── LOCAL_DEVELOPMENT.md     # Local development guide
├── CLOUD_DEPLOYMENT.md      # Cloud deployment guide
└── AMPLIFY_DEPLOYMENT.md    # Amplify-specific guide
```

---

## Quick Reference

### Local Development
- **Start backend only**: `scripts\local\backend\start-backend-only.bat`
- **Start web frontend**: `scripts\local\frontend\start-frontend.bat`
- **Start desktop app**: `scripts\local\frontend\start-desktop-app.bat`
- **Full local system**: `scripts\local\start-full-local-system.bat`

### Cloud Operations
- **Deploy Lambda functions**: `scripts\cloud\deploy-lambda-quick.ps1`
- **Setup AWS resources**: `scripts\cloud\setup-aws.ps1`
- **Start with cloud services**: `scripts\cloud\backend\start-backend-cloud.bat`

### Deployment
- **Deploy frontend to Amplify**: `scripts\deployment\deploy-frontend.bat`
- **Deploy everything**: `scripts\deployment\deploy-all.ps1`

---

## Legacy Folder

The `legacy/` folder contains archived code from previous iterations. **Do not use for production**.
