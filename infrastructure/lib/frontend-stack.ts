import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import * as path from 'path';

export class FrontendStack extends cdk.Stack {
    constructor(scope: Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props);

        // --- S3 Bucket for Web Frontend ---
        const websiteBucket = new s3.Bucket(this, 'WebFrontendBucket', {
            websiteIndexDocument: 'index.html',
            websiteErrorDocument: '404.html',
            publicReadAccess: true,
            blockPublicAccess: s3.BlockPublicAccess.BLOCK_ACLS,
            removalPolicy: cdk.RemovalPolicy.DESTROY,
            autoDeleteObjects: true,
            cors: [
                {
                    allowedMethods: [s3.HttpMethods.GET, s3.HttpMethods.HEAD],
                    allowedOrigins: ['*'],
                    allowedHeaders: ['*'],
                },
            ],
        });

        // --- CloudFront Distribution ---
        const distribution = new cloudfront.Distribution(this, 'WebDistribution', {
            defaultBehavior: {
                origin: new origins.S3Origin(websiteBucket),
                viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
                allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                cachedMethods: cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
            },
            defaultRootObject: 'index.html',
            errorResponses: [
                {
                    httpStatus: 403,
                    responseHttpStatus: 200,
                    responsePagePath: '/index.html',
                    ttl: cdk.Duration.minutes(5),
                },
                {
                    httpStatus: 404,
                    responseHttpStatus: 200,
                    responsePagePath: '/index.html',
                    ttl: cdk.Duration.minutes(5),
                },
            ],
            priceClass: cloudfront.PriceClass.PRICE_CLASS_100, // US, Europe only
            enabled: true,
        });

        // --- Deploy Web Frontend to S3 ---
        // Uncomment when ready to deploy
        /*
        new s3deploy.BucketDeployment(this, 'DeployWebsite', {
          sources: [s3deploy.Source.asset(path.join(process.cwd(), '../frontend/web/out'))],
          destinationBucket: websiteBucket,
          distribution: distribution,
          distributionPaths: ['/*'], // Invalidate CloudFront cache
        });
        */

        // --- S3 Bucket for Desktop App Releases ---
        const desktopReleasesBucket = new s3.Bucket(this, 'DesktopReleasesBucket', {
            publicReadAccess: true,
            blockPublicAccess: s3.BlockPublicAccess.BLOCK_ACLS,
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

        // --- CloudFront for Desktop Releases ---
        const releaseDistribution = new cloudfront.Distribution(this, 'ReleaseDistribution', {
            defaultBehavior: {
                origin: new origins.S3Origin(desktopReleasesBucket),
                viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
            },
            priceClass: cloudfront.PriceClass.PRICE_CLASS_ALL,
        });

        // --- Outputs ---
        new cdk.CfnOutput(this, 'WebFrontendUrl', {
            value: `https://${distribution.distributionDomainName}`,
            description: 'Web Frontend CloudFront URL',
        });

        new cdk.CfnOutput(this, 'WebBucketName', {
            value: websiteBucket.bucketName,
            description: 'S3 Bucket for Web Frontend',
        });

        new cdk.CfnOutput(this, 'DistributionId', {
            value: distribution.distributionId,
            description: 'CloudFront Distribution ID for cache invalidation',
        });

        new cdk.CfnOutput(this, 'DesktopReleasesUrl', {
            value: `https://${releaseDistribution.distributionDomainName}`,
            description: 'Desktop App Download URL',
        });

        new cdk.CfnOutput(this, 'DesktopReleasesBucketName', {
            value: desktopReleasesBucket.bucketName,
            description: 'S3 Bucket for Desktop App Releases',
        });
    }
}
