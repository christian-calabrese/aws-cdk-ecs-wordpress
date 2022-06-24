from __future__ import annotations

import json

from types import SimpleNamespace
from typing import Optional


class Environment(SimpleNamespace):
    def get(self, key, default):
        return self.__dict__.get(key, default)

    @classmethod
    def from_file(cls, env_path: str, uncommitted_env_path: Optional[str]) -> Environment:
        instance = cls()
        with open(f"{env_path}", "r") as f:
            instance = json.loads(f.read(), object_hook=lambda d: cls(**d))

        if uncommitted_env_path:
            with open(f"{uncommitted_env_path}", "r") as f:
                uncommitted_env = json.loads(f.read())
            instance.__dict__.update(uncommitted_env)

        return instance
