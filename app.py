#!/usr/bin/env python3
import json
import os
from types import SimpleNamespace

from aws_cdk import core
from infrastructure.infrastructure_stack import InfrastructureStack
from infrastructure.utils.environment import Environment

app = core.App()
env_name = os.environ.get("ENVIRONMENT", "dev")
with open(f"infrastructure/parameters/{env_name}.json", "r") as f:
    params = json.loads(f.read(), object_hook=lambda d: Environment(**d))

InfrastructureStack(app, "WordpressMainStack",
                env=core.Environment(region="eu-west-1"), params=params)
app.synth()

