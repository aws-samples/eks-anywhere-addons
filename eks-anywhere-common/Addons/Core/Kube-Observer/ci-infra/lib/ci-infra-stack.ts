import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as codebuild from 'aws-cdk-lib/aws-codebuild';
import {Construct} from 'constructs';

export class CiInfraStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Least Privilege Policy Document for Pushing images from codebuild to ecr
    const ecrPushPolicy = new iam.PolicyDocument({
      statements: [
        new iam.PolicyStatement({
          actions: [
            "ecr:CompleteLayerUpload",
            "ecr:GetAuthorizationToken",
            "ecr:UploadLayerPart",
            "ecr:InitiateLayerUpload",
            "ecr:BatchCheckLayerAvailability",
            "ecr:PutImage"
          ],
          resources: ['*']
        })
      ]
    });

    // Role using the least privilege policy for codebuild to push images to ecr
    const ecrPushRole = new iam.Role(this, 'ecr-push-role', {
      assumedBy:  new iam.ServicePrincipal('codebuild.amazonaws.com'),
      inlinePolicies: {
        'ecrPushPolicy': ecrPushPolicy
      },
    });

    const codeBuildSourceCredentials = new codebuild.GitHubSourceCredentials(this,  'observer-source-credentials', {
      accessToken: cdk.SecretValue.secretsManager('github-token')
    });

    /*
     * CodeBuild project that constructs a python container using docker
     * and then pushes the output to a public ECR at public.ecr.aws/n5p5f4n3/conformitron-observer-bot
     */
    const observerBuilder = new codebuild.Project(this, 'observer-builder', {
      buildSpec: codebuild.BuildSpec.fromObject({
        version: '0.2',
        phases: {
          pre_build: {
            commands: [
              'echo Logging in to Amazon ECR...',
              'aws ecr-public get-login-password --region us-east-2 | docker login --username AWS --password-stdin ${ECR_REPO_NAME}'
            ],
          },
          build: {
            commands: [
              'echo Build started on `date`',
              'echo Building the Docker image...',
              'cd ./eks-anywhere-common/Addons/Core/Kube-Observer/ObserverBot/',
              'docker build -t ${ECR_REPO_NAME}:latest .',
            ],
          },
          post_build: {
            commands: [
              'echo Build completed on `date`',
              'docker push ${ECR_REPO_NAME}:latest',
            ],
          },
        },
      }),
      environment: {
        buildImage: codebuild.LinuxBuildImage.STANDARD_7_0,
        privileged: true,
        computeType: codebuild.ComputeType.LARGE,
      },
      environmentVariables: {
        ECR_REPO_NAME: {
          value: ''
        }
      },
      source: codebuild.Source.gitHub({
        owner: 'aws-samples',
        repo: 'eks-anywhere-addons',
        webhookFilters: [
          codebuild.FilterGroup.inEventOf(codebuild.EventAction.PUSH).andBranchIs('feature/e2e-feedback-testing'),
        ],
      }),
      role: ecrPushRole,
    });

    /*
     * TODO: Figure out multi-arch builds on codebuild
     */
    /*const eksBuilder = new codebuild.Project(this, 'eks-anywhere-builder', {
      buildSpec: codebuild.BuildSpec.fromObject({
        version: '0.2',
        phases: {
          pre_build: {
            commands: [
              'echo Logging in to Amazon ECR...',
              'aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin ${ECR_REPO_NAME}',
              ]
            },
          build: {
            commands: [
              'echo Build started on `date`',
              'echo Building the Docker image...',
              'cd ./eks-anywhere-common/Addons/Core/Kube-Observer/ObserverBot',
              'docker buildx create --use --name observer-builder',
              'docker buildx build --platform linux/arm64,linux/amd64 -t ${ECR_REPO_NAME}:latest .',
            ]
          },
          post_build: {
            commands: [
              'echo Build completed on `date`',
              'echo Setting up multi-arch manifests',
              'docker push ${ECR_REPO}:latest',
              'docker manifest push ${ECR_REPO_NAME}:latest',
            ]
          },
        }
      }),
      environment: {
        buildImage: codebuild.LinuxArmBuildImage.AMAZON_LINUX_2_STANDARD_3_0,
        privileged: true,
        computeType: codebuild.ComputeType.LARGE,
      },
      environmentVariables: {
        ECR_REPO_NAME: {
          value: '771830474512.dkr.ecr.us-east-2.amazonaws.com/eks-anywhere'
        }
      },
      source: codebuild.Source.gitHub({
        owner: '5herlocked',
        repo: 'eks-anywhere-addons',
        webhookFilters: [
          codebuild.FilterGroup.inEventOf(codebuild.EventAction.PUSH).andBranchIs('main'),
        ],
      }),
      role: ecrPushRole,
    });*/
  }
}
