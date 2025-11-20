#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { FaceRecognitionStack } from '../lib/face-recognition-stack';
import * as dotenv from 'dotenv';

// Load environment variables
dotenv.config();

const app = new cdk.App();

// Get configuration from environment or context
const account = process.env.AWS_ACCOUNT_ID || process.env.CDK_DEFAULT_ACCOUNT;
const region = process.env.AWS_REGION || process.env.CDK_DEFAULT_REGION || 'ap-southeast-1';
const environment = process.env.ENVIRONMENT || 'dev';
const projectName = process.env.PROJECT_NAME || 'face-recognition';

// Define environment configurations
const envConfig = {
    dev: {
        sagemakerMemory: 4096,
        sagemakerMaxConcurrency: 20,
        cacheNodeType: 'cache.t3.micro',
        enableXRay: true,
        enableBackup: false,
    },
    staging: {
        sagemakerMemory: 6144,
        sagemakerMaxConcurrency: 50,
        cacheNodeType: 'cache.t3.small',
        enableXRay: true,
        enableBackup: true,
    },
    prod: {
        sagemakerMemory: 6144,
        sagemakerMaxConcurrency: 100,
        cacheNodeType: 'cache.r6g.large',
        enableXRay: true,
        enableBackup: true,
    },
};

// Create stack
new FaceRecognitionStack(app, `${projectName}-Stack-${environment}`, {
    env: {
        account: account,
        region: region,
    },
    stackName: `${projectName}-${environment}`,
    description: `Serverless Face Recognition System with AI/ML - ${environment.toUpperCase()}`,
    tags: {
        Project: projectName,
        Environment: environment,
        ManagedBy: 'CDK',
        Owner: 'hoangphuc173',
        CostCenter: 'AI-ML',
    },
    // Pass environment-specific configuration
    environmentName: environment,
    projectName: projectName,
    config: envConfig[environment as keyof typeof envConfig] || envConfig.dev,
});

// Add stack tags
cdk.Tags.of(app).add('Application', 'FaceRecognition');
cdk.Tags.of(app).add('Terraform', 'false');
cdk.Tags.of(app).add('CDK', 'true');

app.synth();
