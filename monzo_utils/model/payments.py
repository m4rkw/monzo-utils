import sys
from monzo_utils.model.base import BaseModel
from monzo_utils.lib.db import DB

class Payments(BaseModel):

    primary_key = 'key'
