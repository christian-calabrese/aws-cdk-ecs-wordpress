#!/usr/bin/env python3
import json
import os

from aws_cdk import core
from aws_cdk.core import Tags

from infrastructure.infrastructure_stack import InfrastructureStack
from infrastructure.utils.environment import Environment

app = core.App()
env_name = os.environ.get("ENVIRONMENT", "dev")
with open(f"infrastructure/parameters/{env_name}.json", "r") as f:
    params = json.loads(f.read(), object_hook=lambda d: Environment(**d))

with open(f"infrastructure/parameters/uncommitted/.env.json", "r") as f:
    uncommitted_env = json.loads(f.read())

params.__dict__.update(uncommitted_env)

main_stack = InfrastructureStack(app, "WordpressMainStack",
                    env=core.Environment(region="eu-west-1"), params=params)
Tags.of(main_stack).add("stack_name", "ChristianCalabreseStack")
app.synth()
