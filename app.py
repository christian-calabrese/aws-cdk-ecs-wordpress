#!/usr/bin/env python3
import os

from aws_cdk import core as cdk

from aws_cdk import core
from infrastructure.stacks.database_stack import DatabaseStack

from infrastructure.infrastructure_stack import InfrastructureStack

app = core.App()
InfrastructureStack(app, "MyWestCdkStack",
                env=core.Environment(region="us-west-1"))
app.synth()

