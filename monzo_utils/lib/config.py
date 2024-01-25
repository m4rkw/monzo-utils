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

            self.config = yaml.safe_load(self.get_file_contents(self.config_file))


    def get_file_contents(self, path):
        return open(path).read()


    def __getattr__(self, name):
        try:
            return self.config[name]
        except:
            pass

        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


    def set(self, key, value):
        self.config[key] = value


    @property
    def keys(self):
        return self.config.keys()


    def save(self):
        self.set_file_contents(self.config_file, yaml.dump(self.config))


    def set_file_contents(self, path, content):
        with open(path, 'w') as f:
            f.write(content)
