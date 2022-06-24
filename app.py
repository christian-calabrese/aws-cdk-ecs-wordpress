#!/usr/bin/env python3
import json
import os

from aws_cdk import core
from aws_cdk.core import Tags

from infrastructure.infrastructure_stack import InfrastructureStack
from infrastructure.utils.environment import Environment

app = core.App()
env_name = os.environ.get("ENVIRONMENT", "dev")

params = Environment.from_file(env_path=f"infrastructure/parameters/{env_name}.json", uncommitted_env_path="infrastructure/parameters/uncommitted/.env.json")
print(f"PARAMS ONE: {params.vpc.az_number}")
main_stack = InfrastructureStack(app, "WordpressMainStack",
                                 env=core.Environment(region="eu-west-1"), params=params)
Tags.of(main_stack).add("stack_name", "ChristianCalabreseStack")
app.synth()
