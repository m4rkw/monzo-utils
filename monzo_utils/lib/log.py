import os
import sys
import datetime
import inspect
import pwd
from monzo_utils.lib.singleton import Singleton

MAX_SIZE_MB = 10
MAX_FILES = 5

class Log(metaclass=Singleton):

    def __init__(self):
        homedir = pwd.getpwuid(os.getuid()).pw_dir
        self.logfile = f"{homedir}/.monzo/logfile"


    def info(self, message):
        self.log(inspect.currentframe().f_code.co_name, message)


    def warning(self, message):
        self.log(inspect.currentframe().f_code.co_name, message)


    def error(self, message):
        self.log(inspect.currentframe().f_code.co_name, message)


    def fatal(self, message):
        self.log(inspect.currentframe().f_code.co_name, message)


    def log(self, level, message):
        log_line = "%s: %s - %s\n" % (
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            level.upper(),
            message
        )

        with open(self.logfile, 'a+') as f:
            f.write(log_line)

        if sys.stdin.isatty():
            if level == 'info':
                sys.stdout.write(log_line)
                sys.stdout.flush()
            else:
                sys.stderr.write(log_line)
                sys.stderr.flush()

        self.rotate()


    def rotate(self):
        if os.stat(self.logfile).st_size >= MAX_SIZE_MB * 1024 * 1024:
            for i in reversed(list(range(1, MAX_FILES))):
                filename = '%s.%d' % (self.logfile, i)
                next_filename = '%s.%d' % (self.logfile, i+1)

                if i+1 == MAX_FILES:
                    if os.path.exists(filename):
                        os.remove(filename)
                else:
                    if os.path.exists(filename):
                        os.rename(filename, next_filename)

            if os.path.exists(self.logfile):
                os.rename(self.logfile, '%s.1' % (self.logfile))
