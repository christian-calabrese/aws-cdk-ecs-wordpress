from aws_cdk import (
    aws_codebuild as codebuild,
    aws_codecommit as codecommit,
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
            )
        ]

        self.deploy_project = codebuild.PipelineProject(self,
                                                        "Wordpress-CodeBuild-Project",
                                                        environment=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
                                                        environment_variables={
                                                            "ENVIRONMENT": codebuild.BuildEnvironmentVariable(
                                                                params.name)
                                                        },
                                                        build_spec=codebuild.BuildSpec.from_object(
                                                            {
                                                                "version": '0.2',
                                                                "env": {},
                                                                "phases": {
                                                                    "install": {
                                                                        "runtime-versions": {
                                                                            "nodejs": 12
                                                                        },
                                                                        "commands": [
                                                                            'npm install aws-cdk',
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
                                                              oauth_token=secretsmanager.Secret.from_secret_attributes(
                                                                  self, "ImportedSecret",
                                                                  secret_complete_arn=f"arn:aws:secretsmanager:{self.region}:{self.account}:secret:{params.github_token_secret_name}"),
                                                          )
                                                      ]
                                                  ),
                                                  codepipeline.StageProps(self,
                                                                          stage_name="BuildAndDeploy",
                                                                          actions=[
                                                                              codepipeline_actions.CodeBuildAction(
                                                                                  action_name="BuildAndDeploy",
                                                                                  project=self.codebuild_project,
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
