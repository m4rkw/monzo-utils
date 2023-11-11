from monzo_utils.lib.singleton import Singleton

class Transactions(metaclass=Singleton):
    seen = {}
