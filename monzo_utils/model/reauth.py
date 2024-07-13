import sys
from monzo_utils.model.base import BaseModel
from monzo_utils.lib.db import DB

class Reauth(BaseModel):

    primary_key = 'key'
