from aws_cdk import (
    aws_ec2 as ec2,
    aws_kms as kms,
    aws_rds as rds,
    aws_logs as logs,
    core
)

from infrastructure.stacks.vpc_stack import VpcStack
from infrastructure.utils.utils import rds_capacity_units


class DatabaseStack(core.NestedStack):

    def __init__(self, scope: core.Construct, id: str, params, vpc_stack: VpcStack,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        if params.aurora.custom_kms_encrypted:
            self.kms_key = kms.Key(self, "Wordpress-KMS-RDS-Key")
        else:
            self.kms_key = None

        if params.aurora.serverless:
            try:
                self.min_capacity = rds_capacity_units[params.aurora.capacity.min]
            except KeyError:
                raise (Exception(f"Minimum capacity must be in {rds_capacity_units.keys()}"))
            try:
                self.max_capacity = rds_capacity_units[params.aurora.capacity.max]
            except KeyError:
                raise (Exception(f"Maximum capacity must be in {list(rds_capacity_units.keys())}"))
            self.database = rds.ServerlessCluster(
                self, "Wordpress-RDS-Aurora-Serverless",
                engine=rds.DatabaseClusterEngine.AURORA_MYSQL,
                default_database_name="wp-database",
                vpc=vpc_stack.vpc,
                scaling=rds.ServerlessScalingOptions(
                    auto_pause=core.Duration.seconds(params.aurora.get("auto_pause_sec", 0)),
                    min_capacity=rds_capacity_units[params.aurora.capacity.min],
                    max_capacity=rds_capacity_units[params.aurora.capacity.max]
                ),
                deletion_protection=False,
                backup_retention=core.Duration.days(params.aurora.get("backup_retention_days", 1)),
                removal_policy=core.RemovalPolicy.SNAPSHOT,
                vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType('PRIVATE')).subnets,
                storage_encryption_key=self.kms_key
            )
        else:
            self.database = rds.DatabaseCluster(
                self, "Wordpress-RDS-Aurora",
                engine=rds.DatabaseClusterEngine.AURORA_MYSQL,
                cluster_identifier="Wordpress-RDS",
                instances=params.aurora.get("az_number", 2),
                default_database_name="wp-database",
                instance_props=rds.InstanceProps(
                    vpc=vpc_stack.vpc,
                    vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType('PRIVATE')).subnets,
                    allow_major_version_upgrade=False,
                    auto_minor_version_upgrade=True,
                    instance_type=ec2.InstanceType(instance_type_identifier=params.aurora.instance_type)
                ),
                cloudwatch_logs_exports=["error", "slowquery"],
                cloudwatch_logs_retention=logs.RetentionDays.ONE_MONTH,
                backup=rds.BackupProps(
                    retention=core.Duration.days(params.aurora.get("backup_retention_days", 7)),
                    preferred_window="01:00-03:00"
                ),
                preferred_maintenance_window="sun03:00-sun05:00",
                instance_identifier_base="FLWP-",
                deletion_protection=True if params.name == "prod" else False,
                removal_policy=core.RemovalPolicy.SNAPSHOT,
                storage_encryption_key=self.kms_key
            )
