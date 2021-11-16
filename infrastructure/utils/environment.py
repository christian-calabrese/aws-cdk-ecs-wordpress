from types import SimpleNamespace


class Environment(SimpleNamespace):
    def get(self, key, default):
        return self.__dict__.get(key, default)
