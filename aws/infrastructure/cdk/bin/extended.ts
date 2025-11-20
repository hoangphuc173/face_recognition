#!/usr/bin/env node
/**
 * Extended Deployment Entry Point
 * Deploy API Gateway + Lambda functions (no numpy dependencies)
 */

import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { ExtendedStack } from '../lib/extended-stack';

const app = new cdk.App();

new ExtendedStack(app, 'FaceRecognitionExtended', {
  projectName: 'face-recognition',
  environment: 'prod',
  
  // Values from previous deployment
  usersTableName: 'face-recognition-users-prod-773600',
  embeddingsTableName: 'face-recognition-embeddings-prod-773600',
  accessLogsTableName: 'face-recognition-access-logs-prod-773600',
  userPoolId: 'ap-southeast-1_qQKOiB3OZ',
  rekognitionCollection: 'face-recognition-collection-dev',
  s3Bucket: 'face-recognition-20251119-215108-32ce1e86',
  
  env: {
    account: '758934444761',
    region: 'ap-southeast-1',
  },
  description: 'Face Recognition Extended - API Gateway + Lambda Functions',
  tags: {
    Project: 'FaceRecognition',
    Environment: 'Production',
    ManagedBy: 'CDK',
    DeploymentType: 'Extended',
  },
});

app.synth();
