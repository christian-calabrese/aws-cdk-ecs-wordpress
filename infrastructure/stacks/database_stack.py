from aws_cdk import (
    aws_ec2 as ec2,
    aws_kms as kms,
    aws_rds as rds,
    core
)

from infrastructure.stacks.vpc_stack import VpcStack


class DatabaseStack(core.NestedStack):

    def __init__(self, scope: core.Construct, id: str, params, vpc_stack: VpcStack,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        if params.aurora.custom_kms_encrypted:
            self.kms_key = kms.Key(self, "Wordpress-KMS-RDS-Key")
        else:
            self.kms_key = None

        if params.aurora.serverless:
            self.database = rds.ServerlessCluster(
                self, "Wordpress-RDS-Aurora-Serverless",
                engine=rds.DatabaseClusterEngine.AURORA_MYSQL,
                default_database_name="wp-database",
                vpc=vpc_stack.vpc,
                scaling=rds.ServerlessScalingOptions(
                    auto_pause=core.Duration.seconds(params.aurora.get("auto_pause_sec", 0))
                ),
                deletion_protection=False,
                backup_retention=core.Duration.days(params.aurora.get("backup_retention_days", 1)),
                removal_policy=core.RemovalPolicy.SNAPSHOT,
                vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType('PRIVATE')).subnets,
                storage_encryption_key=self.kms_key
            )
        else:
            # TODO: Implement serverful database cluster with or without read replica
            self.database = None
