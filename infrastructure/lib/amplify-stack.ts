import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as amplify from 'aws-cdk-lib/aws-amplify';
import * as codebuild from 'aws-cdk-lib/aws-codebuild';

export class AmplifyStack extends cdk.Stack {
    public readonly appId: string;

    constructor(scope: Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props);

        // Create Amplify App (Manual Deployment)
        const amplifyApp = new amplify.CfnApp(this, 'FaceRecognitionWebApp', {
            name: 'FaceRecognitionWeb',
            platform: 'WEB',
            environmentVariables: [
                { name: 'AMPLIFY_MONOREPO_APP_ROOT', value: 'frontend/web' }
            ]
        });

        // Create a branch (e.g., 'prod')
        const branch = new amplify.CfnBranch(this, 'ProdBranch', {
            appId: amplifyApp.attrAppId,
            branchName: 'prod',
            stage: 'PRODUCTION'
        });

        this.appId = amplifyApp.attrAppId;

        // Outputs
        new cdk.CfnOutput(this, 'AmplifyAppId', {
            value: amplifyApp.attrAppId,
            description: 'Amplify App ID'
        });

        new cdk.CfnOutput(this, 'AmplifyAppUrl', {
            value: `https://${branch.branchName}.${amplifyApp.attrDefaultDomain}`,
            description: 'Amplify App URL'
        });
    }
}
