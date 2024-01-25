from monzo_utils.lib.singleton import Singleton

class TransactionsSeen(metaclass=Singleton):
    seen = {}
