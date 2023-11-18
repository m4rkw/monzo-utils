import os
import pwd
import yaml
import sys
from monzo_utils.lib.singleton import Singleton

class Config(metaclass=Singleton):

    def __init__(self, config=None, config_path=None):
        if config_path is None:
            homedir = pwd.getpwuid(os.getuid()).pw_dir
            config_path = f"{homedir}/.monzo"

        if not os.path.exists(config_path):
            os.mkdir(config_path, 0o755)

        self.config_file = f"{config_path}/config.yaml"

        if config:
            self.config = config
        else:
            if not os.path.exists(self.config_file):
                sys.stderr.write(f"config file not found: {self.config_file}, run setup first.\n")
                sys.exit(1)

            self.config = yaml.safe_load(open(self.config_file).read())


    def __getattr__(self, name):
        if name in self.config:
            return self.config[name]

        return object.__getattribute__(self, name)


    def set(self, key, value):
        self.config[key] = value


    @property
    def keys(self):
        return self.config.keys()


    def save(self):
        with open(self.config_file, 'w') as f:
            f.write(yaml.dump(self.config))
