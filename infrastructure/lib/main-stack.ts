import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as rekognition from 'aws-cdk-lib/aws-rekognition';
import * as kms from 'aws-cdk-lib/aws-kms';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as path from 'path';

export class MainStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // --- KMS Keys ---
    const s3Key = new kms.Key(this, 'S3EncryptionKey', {
      enableKeyRotation: true,
      description: 'KMS key for S3 bucket encryption',
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const dynamoKey = new kms.Key(this, 'DynamoEncryptionKey', {
      enableKeyRotation: true,
      description: 'KMS key for DynamoDB encryption',
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // --- S3 Buckets with KMS Encryption ---
    const rawBucket = new s3.Bucket(this, 'RawBucket', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      encryption: s3.BucketEncryption.KMS,
      encryptionKey: s3Key,
      lifecycleRules: [
        {
          transitions: [
            {
              storageClass: s3.StorageClass.GLACIER,
              transitionAfter: cdk.Duration.days(30),
            }
          ],
          expiration: cdk.Duration.days(90),
        }
      ],
    });

    const processedBucket = new s3.Bucket(this, 'ProcessedBucket', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
      encryption: s3.BucketEncryption.KMS,
      encryptionKey: s3Key,
      lifecycleRules: [
        {
          transitions: [
            {
              storageClass: s3.StorageClass.GLACIER,
              transitionAfter: cdk.Duration.days(30),
            }
          ],
          expiration: cdk.Duration.days(90),
        }
      ],
    });

    // --- DynamoDB Tables with KMS Encryption ---
    const usersTable = new dynamodb.Table(this, 'UsersTable', {
      partitionKey: { name: 'UserId', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
      encryptionKey: dynamoKey,
    });

    usersTable.addGlobalSecondaryIndex({
      indexName: 'FaceIdIndex',
      partitionKey: { name: 'FaceId', type: dynamodb.AttributeType.STRING },
    });

    const accessLogsTable = new dynamodb.Table(this, 'AccessLogsTable', {
      partitionKey: { name: 'LogId', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      timeToLiveAttribute: 'TTL',
      encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
      encryptionKey: dynamoKey,
    });

    // UserProfiles Table for extended user data
    const userProfilesTable = new dynamodb.Table(this, 'UserProfilesTable', {
      partitionKey: { name: 'UserId', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
      encryptionKey: dynamoKey,
    });

    // OTPVerification Table for email OTP codes
    const otpTable = new dynamodb.Table(this, 'OTPVerificationTable', {
      partitionKey: { name: 'email', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      timeToLiveAttribute: 'ttl',
      encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
      encryptionKey: dynamoKey,
    });

    // --- Rekognition Collection ---
    const collectionId = 'FaceCollection';
    new rekognition.CfnCollection(this, 'FaceCollection', {
      collectionId: collectionId,
    });

    // --- Cognito with Groups (RBAC) ---
    const userPool = new cognito.UserPool(this, 'UserPool', {
      selfSignUpEnabled: true,
      signInAliases: { username: true, email: true },
      autoVerify: { email: true },
      standardAttributes: {
        email: { required: true, mutable: true },
        fullname: { required: false, mutable: true },
      },
      passwordPolicy: {
        minLength: 8,
        requireLowercase: true,
        requireUppercase: true,
        requireDigits: true,
        requireSymbols: true,
      },
      email: cognito.UserPoolEmail.withCognito(),
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const userPoolClient = new cognito.UserPoolClient(this, 'UserPoolClient', {
      userPool,
      authFlows: {
        userPassword: true,
        adminUserPassword: true,
      },
      generateSecret: false,
    });

    // Create Cognito Groups for RBAC
    new cognito.CfnUserPoolGroup(this, 'AdminGroup', {
      groupName: 'Admin',
      userPoolId: userPool.userPoolId,
      description: 'Administrators with full access',
    });

    new cognito.CfnUserPoolGroup(this, 'StaffGroup', {
      groupName: 'Staff',
      userPoolId: userPool.userPoolId,
      description: 'Staff with limited access',
    });

    new cognito.CfnUserPoolGroup(this, 'GuestGroup', {
      groupName: 'Guest',
      userPoolId: userPool.userPoolId,
      description: 'Guests with read-only access',
    });

    // --- Lambda Layer ---
    const commonLayer = new lambda.LayerVersion(this, 'CommonLayer', {
      code: lambda.Code.fromAsset(path.join(process.cwd(), '../backend/layer_v2')),
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_11],
      description: 'Common dependencies layer',
    });

    const commonEnv = {
      AWS_REGION: this.region,
      USER_POOL_ID: userPool.userPoolId,
      CLIENT_ID: userPoolClient.userPoolClientId,
      USERS_TABLE: usersTable.tableName,
      ACCESS_LOGS_TABLE: accessLogsTable.tableName,
      USER_PROFILES_TABLE: userProfilesTable.tableName,
      RAW_BUCKET: rawBucket.bucketName,
      PROCESSED_BUCKET: processedBucket.bucketName,
      COLLECTION_ID: collectionId,
      SMTP_USERNAME: process.env.SMTP_USERNAME || '',
      SMTP_PASSWORD: process.env.SMTP_PASSWORD || '',
      BREVO_API_KEY: process.env.BREVO_API_KEY || '',
    };

    const authFn = new lambda.Function(this, 'AuthHandler', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'auth.main.handler',
      code: lambda.Code.fromAsset(path.join(process.cwd(), '../backend/src')),
      layers: [commonLayer],
      environment: commonEnv,
      timeout: cdk.Duration.seconds(10),
      memorySize: 256,
    });

    authFn.addToRolePolicy(new iam.PolicyStatement({
      actions: [
        'cognito-idp:InitiateAuth',
        'cognito-idp:GetUser',
        'cognito-idp:AdminGetUser',
        'cognito-idp:AdminCreateUser',
        'cognito-idp:AdminSetUserPassword',
        'cognito-idp:AdminDeleteUser',
        'cognito-idp:AdminEnableUser',
        'cognito-idp:AdminDisableUser',
        'cognito-idp:AdminUpdateUserAttributes',
        'cognito-idp:AdminListGroupsForUser',
        'cognito-idp:AdminAddUserToGroup',
        'cognito-idp:AdminRemoveUserFromGroup',
        'cognito-idp:ListUsers',
        'cognito-idp:SignUp',
        'cognito-idp:ConfirmSignUp',
        'cognito-idp:ForgotPassword',
        'cognito-idp:ConfirmForgotPassword',
        'ses:SendEmail',
        'ses:SendRawEmail'
      ],
      resources: ['*'],
    }));

    // Grant access to UserProfiles table
    userProfilesTable.grantReadWriteData(authFn);
    userProfilesTable.grantReadWriteData(authFn);
    dynamoKey.grantEncryptDecrypt(authFn);

    const enrollFn = new lambda.Function(this, 'EnrollHandler', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'enroll.main.handler',
      code: lambda.Code.fromAsset(path.join(process.cwd(), '../backend/src')),
      layers: [commonLayer],
      environment: commonEnv,
      timeout: cdk.Duration.seconds(30),
      memorySize: 1024,
    });

    rawBucket.grantWrite(enrollFn);
    processedBucket.grantWrite(enrollFn);
    usersTable.grantWriteData(enrollFn);
    s3Key.grantEncryptDecrypt(enrollFn);
    dynamoKey.grantEncryptDecrypt(enrollFn);
    enrollFn.addToRolePolicy(new iam.PolicyStatement({
      actions: ['rekognition:IndexFaces', 'rekognition:DetectFaces'],
      resources: ['*'],
    }));

    const identifyFn = new lambda.Function(this, 'IdentifyHandler', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'identify.main.handler',
      code: lambda.Code.fromAsset(path.join(process.cwd(), '../backend/src')),
      layers: [commonLayer],
      environment: commonEnv,
      timeout: cdk.Duration.seconds(30),
      memorySize: 1024,
    });

    usersTable.grantReadData(identifyFn);
    accessLogsTable.grantWriteData(identifyFn);
    dynamoKey.grantEncryptDecrypt(identifyFn);
    identifyFn.addToRolePolicy(new iam.PolicyStatement({
      actions: ['rekognition:SearchFacesByImage'],
      resources: [`arn:aws:rekognition:${this.region}:${this.account}:collection/${collectionId}`],
    }));

    const peopleFn = new lambda.Function(this, 'PeopleHandler', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'people.main.handler',
      code: lambda.Code.fromAsset(path.join(process.cwd(), '../backend/src')),
      layers: [commonLayer],
      environment: commonEnv,
      timeout: cdk.Duration.seconds(10),
      memorySize: 512,
    });

    usersTable.grantReadWriteData(peopleFn);
    processedBucket.grantDelete(peopleFn);
    s3Key.grantEncryptDecrypt(peopleFn);
    dynamoKey.grantEncryptDecrypt(peopleFn);
    peopleFn.addToRolePolicy(new iam.PolicyStatement({
      actions: ['rekognition:DeleteFaces'],
      resources: [`arn:aws:rekognition:${this.region}:${this.account}:collection/${collectionId}`],
    }));

    const loggingFn = new lambda.Function(this, 'LoggingHandler', {
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'logging.main.handler',
      code: lambda.Code.fromAsset(path.join(process.cwd(), '../backend/src')),
      layers: [commonLayer],
      environment: commonEnv,
      timeout: cdk.Duration.seconds(10),
      memorySize: 512,
    });

    accessLogsTable.grantReadData(loggingFn);
    dynamoKey.grantEncryptDecrypt(loggingFn);

    // --- API Gateway with JWT Authorizer ---
    const api = new apigateway.RestApi(this, 'FaceRecogApi', {
      restApiName: 'Face Recognition Service',
      deployOptions: {
        throttlingRateLimit: 100,
        throttlingBurstLimit: 200,
      },
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: ['Content-Type', 'Authorization'],
      },
    });

    // Add CORS headers to all responses
    api.addGatewayResponse('Default4XX', {
      type: apigateway.ResponseType.DEFAULT_4XX,
      responseHeaders: {
        'Access-Control-Allow-Origin': "'*'",
        'Access-Control-Allow-Headers': "'Content-Type,Authorization'",
        'Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'",
      },
    });

    api.addGatewayResponse('Default5XX', {
      type: apigateway.ResponseType.DEFAULT_5XX,
      responseHeaders: {
        'Access-Control-Allow-Origin': "'*'",
        'Access-Control-Allow-Headers': "'Content-Type,Authorization'",
        'Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'",
      },
    });

    const authorizer = new apigateway.CognitoUserPoolsAuthorizer(this, 'CognitoAuthorizer', {
      cognitoUserPools: [userPool],
    });

    const requestValidator = new apigateway.RequestValidator(this, 'RequestValidator', {
      restApi: api,
      validateRequestBody: true,
      validateRequestParameters: true,
    });

    // Auth endpoint (public)
    const authResource = api.root.addResource('auth');

    const tokenResource = authResource.addResource('token');
    tokenResource.addMethod('POST', new apigateway.LambdaIntegration(authFn, {
      proxy: true,
    }));

    // Register endpoint (public)
    const registerResource = authResource.addResource('register');
    registerResource.addMethod('POST', new apigateway.LambdaIntegration(authFn, {
      proxy: true,
    }));

    // Confirm Registration endpoint (public)
    const confirmRegistrationResource = authResource.addResource('confirm-registration');
    confirmRegistrationResource.addMethod('POST', new apigateway.LambdaIntegration(authFn, {
      proxy: true,
    }));

    // Forgot Password endpoints (public)
    const forgotPasswordResource = authResource.addResource('forgot-password');
    forgotPasswordResource.addMethod('POST', new apigateway.LambdaIntegration(authFn, {
      proxy: true,
    }));

    const confirmForgotPasswordResource = forgotPasswordResource.addResource('confirm');
    confirmForgotPasswordResource.addMethod('POST', new apigateway.LambdaIntegration(authFn, {
      proxy: true,
    }));

    // Profile endpoints (protected by Lambda logic)
    const profileResource = authResource.addResource('profile');
    profileResource.addMethod('GET', new apigateway.LambdaIntegration(authFn, {
      proxy: true,
    }));

    profileResource.addMethod('PUT', new apigateway.LambdaIntegration(authFn, {
      proxy: true,
    }));

    // Admin endpoints (protected by Lambda logic)
    const adminResource = authResource.addResource('admin');
    const adminUsersResource = adminResource.addResource('users');

    adminUsersResource.addMethod('GET', new apigateway.LambdaIntegration(authFn, {
      proxy: true,
    }));

    const adminUserResource = adminUsersResource.addResource('{username}');
    adminUserResource.addMethod('PUT', new apigateway.LambdaIntegration(authFn, {
      proxy: true,
    }), {
      authorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });

    adminUserResource.addMethod('DELETE', new apigateway.LambdaIntegration(authFn, {
      proxy: true,
    }), {
      authorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });

    // Protected endpoints
    const enrollResource = api.root.addResource('enroll');
    enrollResource.addMethod('POST', new apigateway.LambdaIntegration(enrollFn, {
      proxy: true,
    }), {
      authorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });

    const identifyResource = api.root.addResource('identify');
    identifyResource.addMethod('POST', new apigateway.LambdaIntegration(identifyFn, {
      proxy: true,
    }), {
      authorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });

    const peopleResource = api.root.addResource('people');
    peopleResource.addMethod('GET', new apigateway.LambdaIntegration(peopleFn, {
      proxy: true,
    }), {
      authorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });

    const personResource = peopleResource.addResource('{user_id}');
    personResource.addMethod('DELETE', new apigateway.LambdaIntegration(peopleFn, {
      proxy: true,
    }), {
      authorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });

    personResource.addMethod('PUT', new apigateway.LambdaIntegration(peopleFn, {
      proxy: true,
    }), {
      authorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });

    const logsResource = api.root.addResource('logs');
    logsResource.addMethod('GET', new apigateway.LambdaIntegration(loggingFn, {
      proxy: true,
    }), {
      authorizer,
      authorizationType: apigateway.AuthorizationType.COGNITO,
    });

    // Outputs
    new cdk.CfnOutput(this, 'ApiUrl', { value: api.url });
    new cdk.CfnOutput(this, 'UserPoolId', { value: userPool.userPoolId });
    new cdk.CfnOutput(this, 'UserPoolClientId', { value: userPoolClient.userPoolClientId });
  }
}
