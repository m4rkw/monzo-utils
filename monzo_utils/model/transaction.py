from monzo_utils.model.base import BaseModel

class Transaction(BaseModel):

    DISPLAY_KEYS = ['date','type','money_in','money_out','pending','description']
