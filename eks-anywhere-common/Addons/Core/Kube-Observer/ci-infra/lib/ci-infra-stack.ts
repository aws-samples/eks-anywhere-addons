import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as codebuild from 'aws-cdk-lib/aws-codebuild';
import * as codepipeline from 'aws-cdk-lib/aws-codepipeline';
import * as codepipeline_actions from 'aws-cdk-lib/aws-codepipeline-actions';
import {Construct} from 'constructs';

export class CiInfraStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Least Privilege Policy Document for Pushing images from codebuild to ecr
    const ecrPushPolicy = new iam.PolicyDocument({
      statements: [
        new iam.PolicyStatement({
          actions: [
            'ecr:BatchCheckLayerAvailability',
            'ecr:GetDownloadUrlForLayer',
            'ecr:BatchGetImage',
            'ecr:PutImage'
          ],
          resources: ['arn:aws:ecr-public::867286930927:repository/conformitron-observer-bot']
        })
      ]
    });

    // Role using the least privilege policy for codebuild to push images to ecr
    const ecrPushRole = new iam.Role(this, 'ecr-push-role', {
      assumedBy: new iam.ServicePrincipal('codebuild.amazonaws.com'),
      inlinePolicies: {
        'ecrPushPolicy': ecrPushPolicy
      }
    });

    /*
     * CodeBuild project that constructs a python container using docker
     * and then pushes the output to a public ECR at public.ecr.aws/n5p5f4n3/conformitron-observer-bot
     */
    const observerBuilder = new codebuild.PipelineProject(this, 'observer-arm-builder', {
      buildSpec: codebuild.BuildSpec.fromObject({
        version: '0.2',
        phases: {
          pre_build: {
            commands: [
              'echo Logging in to Amazon ECR...',
              '$(aws ecr-public get-login --no-include-email --region us-east-1)',
            ],
          },
          build: {
            commands: [
              'echo Build started on `date`',
              'echo Building the Docker image...',
              'cd ./eks-anywhere-common/Addons/Core/Kube-Observer/',
              'docker build -t ${ECR_REPO_NAME}:amd64 . --platform=amd64',
              'docker build -t ${ECR_REPO_NAME}:arm64 . --platform=arm64',
            ],
          },
          post_build: {
            commands: [
              'echo Build completed on `date`',
              'echo Setting up multi-arch manifests',
              'docker manifest create ${ECR_REPO_NAME}:latest ${ECR_REPO_NAME}:arm64 ${ECR_REPO}:amd64',
              'docker manifest annotate ${ECR_REPO_NAME}:latest ${ECR_REPO_NAME}:arm64 --os linux --arch arm',
              'docker push ${ECR_REPO}:latest',
              'docker manifest push ${ECR_REPO_NAME}:latest',
            ],
          },
        },
      }),
      environment: {
        buildImage: codebuild.LinuxArmBuildImage.AMAZON_LINUX_2_STANDARD_3_0,
        privileged: true,
        computeType: codebuild.ComputeType.LARGE,
      },
      environmentVariables: {
        ECR_REPO_NAME: {
          value: 'public.ecr.aws/n5p5f4n3/conformitron-observer-bot'
        }
      }
    });

    const sourceOutput = new codepipeline.Artifact();
    const buildOutput = new codepipeline.Artifact();
    const githubToken = cdk.SecretValue.secretsManager('github-token');

    const observerPipeline = new codepipeline.Pipeline(this, 'observer-pipeline', {
      stages: [
        {
          stageName: 'Source',
          actions: [
            new codepipeline_actions.GitHubSourceAction({
              actionName: 'GitHub_Source',
              output: sourceOutput,
              owner: 'aws-samples',
              repo: 'eks-anywhere-addons',
              oauthToken: githubToken,
              branch: 'feature/e2e-feedback-testing',
            }),
          ],
        },
        {
          stageName: 'Build and Push',
          actions: [
            new codepipeline_actions.CodeBuildAction({
              actionName: 'Docker_Build_and_Push',
              project: observerBuilder,
              input: sourceOutput,
              role: ecrPushRole
            }),
          ],
        },
      ],
    });
  }
}
