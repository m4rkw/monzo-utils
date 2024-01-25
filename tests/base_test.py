import os
import sys
sys.path.append(os.path.realpath(os.path.dirname(__file__) + "/../"))
import unittest

class BaseTest(unittest.TestCase):

    def setUp(self):
        pass
