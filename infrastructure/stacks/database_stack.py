from aws_cdk import (
    aws_ec2 as ec2,
    aws_rds as rds,
    core
)


class DatabaseStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
