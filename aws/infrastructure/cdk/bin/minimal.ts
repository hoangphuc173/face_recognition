#!/usr/bin/env node
/**
 * Minimal Deployment Entry Point
 * Deploy only infrastructure without Lambda functions
 */

import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { MinimalStack } from '../lib/minimal-stack';

const app = new cdk.App();

new MinimalStack(app, 'FaceRecognitionMinimal', {
  projectName: 'face-recognition',
  environment: 'prod',
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT || '758934444761',
    region: process.env.CDK_DEFAULT_REGION || 'ap-southeast-1',
  },
  description: 'Face Recognition Infrastructure (DynamoDB, Cognito, Parameters)',
  tags: {
    Project: 'FaceRecognition',
    Environment: 'Production',
    ManagedBy: 'CDK',
    DeploymentType: 'Minimal',
  },
});

app.synth();
