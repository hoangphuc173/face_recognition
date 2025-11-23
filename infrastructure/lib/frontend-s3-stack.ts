import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';

export class FrontendS3Stack extends cdk.Stack {
    constructor(scope: Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props);

        // --- S3 Bucket for Web Frontend with Website Hosting ---
        const websiteBucket = new s3.Bucket(this, 'WebFrontendBucket', {
            websiteIndexDocument: 'index.html',
            websiteErrorDocument: 'index.html', // SPA routing
            publicReadAccess: true,
            blockPublicAccess: new s3.BlockPublicAccess({
                blockPublicAcls: false,
                blockPublicPolicy: false,
                ignorePublicAcls: false,
                restrictPublicBuckets: false,
            }),
            removalPolicy: cdk.RemovalPolicy.DESTROY,
            autoDeleteObjects: true,
            cors: [
                {
                    allowedMethods: [
                        s3.HttpMethods.GET,
                        s3.HttpMethods.HEAD,
                    ],
                    allowedOrigins: ['*'],
                    allowedHeaders: ['*'],
                },
            ],
        });

        // --- S3 Bucket for Desktop App Releases ---
        const desktopReleasesBucket = new s3.Bucket(this, 'DesktopReleasesBucket', {
            publicReadAccess: true,
            blockPublicAccess: new s3.BlockPublicAccess({
                blockPublicAcls: false,
                blockPublicPolicy: false,
                ignorePublicAcls: false,
                restrictPublicBuckets: false,
            }),
            removalPolicy: cdk.RemovalPolicy.RETAIN, // Keep releases
            versioned: true,
            cors: [
                {
                    allowedMethods: [s3.HttpMethods.GET],
                    allowedOrigins: ['*'],
                    allowedHeaders: ['*'],
                },
            ],
        });

        // --- Outputs ---
        new cdk.CfnOutput(this, 'WebFrontendUrl', {
            value: websiteBucket.bucketWebsiteUrl,
            description: 'Web Frontend S3 Website URL',
        });

        new cdk.CfnOutput(this, 'WebBucketName', {
            value: websiteBucket.bucketName,
            description: 'S3 Bucket for Web Frontend',
        });

        new cdk.CfnOutput(this, 'DesktopReleasesUrl', {
            value: `https://${desktopReleasesBucket.bucketRegionalDomainName}`,
            description: 'Desktop App Download URL',
        });

        new cdk.CfnOutput(this, 'DesktopReleasesBucketName', {
            value: desktopReleasesBucket.bucketName,
            description: 'S3 Bucket for Desktop App Releases',
        });
    }
}
