import json
from aws_cdk import (
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    core
)


class PipelineStack(core.NestedStack):
    def __init__(self, scope: core.Construct, id: str, params,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        github_secret = secretsmanager.CfnSecret(
            self,
            "Wordpress-Secretsmanager-GitHub-Secret",
            name=params.github_token_secret_name,
            secret_string=json.dumps({"github_token": params.github_token})
        )
        self.codebuild_policies = [
            iam.PolicyStatement(
                actions=[
                    'cloudformation:*',
                ],
                resources=['*'],
                effect=iam.Effect.ALLOW
            ),
            iam.PolicyStatement(
                conditions={
                    'ForAnyValue:StringEquals': {
                        'aws:CalledVia': [
                            'cloudformation.amazonaws.com'
                        ]
                    }
                },
                actions=['*'],
                resources=['*'],
                effect=iam.Effect.ALLOW
            ),
            iam.PolicyStatement(
                actions=[
                    's3:*',
                ],
                resources=['arn:aws:s3:::cdk*'],
                effect=iam.Effect.ALLOW
            ),
            iam.PolicyStatement(
                actions=[
                    'ec2:Describe*',
                    'ec2:Get*'
                ],
                resources=['*'],
                effect=iam.Effect.ALLOW
            ),
            iam.PolicyStatement(
                actions=[
                    'ecr:*'
                ],
                resources=['*'],
                effect=iam.Effect.ALLOW
            )
        ]

        self.deploy_project = codebuild.PipelineProject(self,
                                                        "Wordpress-CodeBuild-Project",
                                                        environment=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                                                        environment_variables={
                                                            "ENVIRONMENT": codebuild.BuildEnvironmentVariable(
                                                                value=params.name),
                                                            "IMAGE_REPO_NAME": codebuild.BuildEnvironmentVariable(
                                                                value=params.fargate.container_image_name)
                                                        },
                                                        build_spec=codebuild.BuildSpec.from_object(
                                                            {
                                                                "version": '0.2',
                                                                "env": {},
                                                                "phases": {
                                                                    "pre_build": {
                                                                        "commands": [
                                                                            "echo Logging in to Amazon ECR...",
                                                                            "aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com"
                                                                        ]
                                                                    },
                                                                    "install": {
                                                                        "runtime-versions": {
                                                                            "nodejs": 12,
                                                                            "python": "3.8"
                                                                        },
                                                                        "commands": [
                                                                            "echo Build started on `date`",
                                                                            "echo Building the Docker image...",
                                                                            "docker build -t $IMAGE_REPO_NAME:latest .",
                                                                            "docker tag $IMAGE_REPO_NAME:latest  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:latest",
                                                                            "docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$IMAGE_REPO_NAME:latest",
                                                                            "pip3 install -r requirements.txt",
                                                                            "npm install aws-cdk",
                                                                        ]
                                                                    },
                                                                    "build": {
                                                                        "commands": [
                                                                            "cdk deploy"
                                                                        ]
                                                                    }
                                                                }
                                                            }
                                                        )
                                                        )

        for policy in self.codebuild_policies:
            self.deploy_project.add_to_role_policy(policy)

        self.source_output = codepipeline.Artifact()

        self.pipeline = codepipeline.Pipeline(self,
                                              "Wordpress-CodePipeline-Pipeline",
                                              pipeline_name="Wordpress-CodePipeline-Pipeline",
                                              stages=[
                                                  codepipeline.StageProps(
                                                      stage_name="Source",
                                                      actions=[
                                                          codepipeline_actions.GitHubSourceAction(
                                                              action_name="GitHubSource",
                                                              output=self.source_output,
                                                              owner="AWS",
                                                              repo=params.git_repository_name,
                                                              oauth_token=core.SecretValue.secrets_manager(
                                                                  secret_id=github_secret.name,
                                                                  json_field="github_token"),
                                                          )
                                                      ]
                                                  ),
                                                  codepipeline.StageProps(
                                                      stage_name="BuildAndDeploy",
                                                      actions=[
                                                          codepipeline_actions.CodeBuildAction(
                                                              action_name="BuildAndDeploy",
                                                              project=self.deploy_project,
                                                              input=self.source_output
                                                          )
                                                      ]
                                                  )
                                              ]
                                              )

        self.pipeline.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'codestar-connections:UseConnection'
                ],
                resources=[
                    f"arn:aws:codestar-connections:{self.region}:{self.account}:connection/{params.codestar_connection_id}"
                ],
                effect=iam.Effect.ALLOW
            )
        )
