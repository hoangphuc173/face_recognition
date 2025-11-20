#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { BusinessStack } from '../lib/business-stack';

const app = new cdk.App();

// Get API Gateway ID from Extended stack output
const EXISTING_API_ID = 'r7hwlthie5'; // From Extended stack output
const EXISTING_API_ROOT_RESOURCE_ID = 'h84wlp3ho5'; // Retrieved from API Gateway

new BusinessStack(app, 'FaceRecognitionBusiness', {
  env: {
    account: '758934444761',
    region: 'ap-southeast-1',
  },
  
  // Reference resources from deployed stacks
  usersTableName: 'face-recognition-users-prod-773600',
  embeddingsTableName: 'face-recognition-embeddings-prod-773600',
  accessLogsTableName: 'face-recognition-access-logs-prod-773600',
  userPoolId: 'ap-southeast-1_qQKOiB3OZ',
  s3BucketName: 'face-recognition-images-829717935400',
  existingApiId: EXISTING_API_ID,
  existingApiRootResourceId: EXISTING_API_ROOT_RESOURCE_ID,
});
