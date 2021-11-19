from aws_cdk import (
    core as cdk
)

from infrastructure.stacks.database_stack import DatabaseStack
from infrastructure.stacks.fargate_stack import FargateStack
from infrastructure.stacks.pipeline_stack import PipelineStack
from infrastructure.stacks.vpc_stack import VpcStack


class InfrastructureStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str, params, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.vpc_stack = VpcStack(scope=self, id="WordpressVpcStack", params=params)
        self.database_stack = DatabaseStack(scope=self, id="WordpressDatabaseStack", params=params,
                                            vpc_stack=self.vpc_stack)
        self.pipeline_stack = PipelineStack(scope=self, id="WordpressPipelineStack", params=params)
        self.fargate_stack = FargateStack(scope=self, id="WordpressFargateStack", params=params,
                                          vpc_stack=self.vpc_stack,
                                          database_stack=self.database_stack,
                                          pipeline_stack=self.pipeline_stack)
