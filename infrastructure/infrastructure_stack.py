from aws_cdk import (
    core as cdk
)

from infrastructure.stacks.fargate_stack import FargateStack


class InfrastructureStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        vpc_stack = VpcStack(scope=scope, id="WordpressVpcStack")
        database_stack = cdk.Stack(scope=scope, id="WordpressDatabaseStack", vpc_stack=vpc_stack)
        fargate_stack = FargateStack(scope=scope, id="WordpressFargateStack", vpc_stack=vpc_stack, database_stack=database_stack)
