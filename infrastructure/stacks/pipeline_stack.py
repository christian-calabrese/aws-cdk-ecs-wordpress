import json
from aws_cdk import (
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_codestarconnections as codestar,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    core
)


class PipelineStack(core.NestedStack):
    def __init__(self, scope: core.Construct, id: str, params,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.ecr_repository = ecr.Repository(
            self,
            "Wordpress-ECR-Repository",
            repository_name=params.fargate.container_image_name
        )

        github_secret = secretsmanager.CfnSecret(
            self,
            "Wordpress-Secretsmanager-GitHub-Secret",
            name=params.github_token_secret_name,
            secret_string=json.dumps({"github_token": params.github_token})
        )

        self.codestar_connection = codestar.CfnConnection(
            self,
            "Wordpress-Codestar-GitHub-Connection",
            connection_name="Wordpress-Codestar-Connection",
            provider_type="GitHub"
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
        secondary_db_uri = 'wordpress.route53.rds.replica' if params.aurora.get(
                                                                    "has_replica", None) else ""
        self.deploy_project = codebuild.PipelineProject(self,
                                                        "Wordpress-CodeBuild-Project",
                                                        environment=codebuild.BuildEnvironment(
                                                            privileged=True,
                                                            build_image=codebuild.LinuxBuildImage.STANDARD_5_0
                                                        ),
                                                        environment_variables={
                                                            "ENVIRONMENT": codebuild.BuildEnvironmentVariable(
                                                                value=params.name),
                                                            "IMAGE_REPO_NAME": codebuild.BuildEnvironmentVariable(
                                                                value=self.ecr_repository.repository_name),
                                                            "PRIMARY_DB_URI": codebuild.BuildEnvironmentVariable(
                                                                value='wordpress.route53.rds'),
                                                            "SECONDARY_DB_URI": codebuild.BuildEnvironmentVariable(
                                                                value=secondary_db_uri),
                                                            "WORDPRESS_TABLE_PREFIX": codebuild.BuildEnvironmentVariable(
                                                                value='wp_')
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
                                                                            "cd images/wordpress",
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
                                                              owner=params.github_repository_owner,
                                                              branch=params.branch,
                                                              trigger=codepipeline_actions.GitHubTrigger.POLL,
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
                    self.codestar_connection.attr_connection_arn
                ],
                effect=iam.Effect.ALLOW
            )
        )
