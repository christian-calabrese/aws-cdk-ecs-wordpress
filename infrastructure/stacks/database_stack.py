from aws_cdk import (
    aws_ec2 as ec2,
    aws_rds as rds,
    core
)

from infrastructure.stacks.vpc_stack import VpcStack


class DatabaseStack(core.NestedStack):

    def __init__(self, scope: core.Construct, id: str, params, vpc_stack: VpcStack,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
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
                backup_retention=core.Duration.days(7),
                removal_policy=core.RemovalPolicy.SNAPSHOT,
                subnet_group=ec2.SubnetSelection(subnet_type=ec2.SubnetType('PRIVATE')).subnets
            )
        else:
            self.database = None
