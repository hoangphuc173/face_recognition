#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { MainStack } from '../lib/main-stack';
import { AmplifyStack } from '../lib/amplify-stack';

const app = new cdk.App();

// Backend Stack
const backendStack = new MainStack(app, 'FaceRecogBackendStack', {
    env: {
        account: process.env.CDK_DEFAULT_ACCOUNT,
        region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
    },
    description: 'Face Recognition Backend - Lambda + API Gateway + Cognito',
});

// Frontend Stack (Amplify)
const frontendStack = new AmplifyStack(app, 'FaceRecogAmplifyStack', {
    env: {
        account: process.env.CDK_DEFAULT_ACCOUNT,
        region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
    },
    description: 'Face Recognition Frontend - AWS Amplify',
});

// Tags
cdk.Tags.of(backendStack).add('Project', 'FaceRecognition');
cdk.Tags.of(backendStack).add('Environment', 'Production');
cdk.Tags.of(frontendStack).add('Project', 'FaceRecognition');
cdk.Tags.of(frontendStack).add('Environment', 'Production');
