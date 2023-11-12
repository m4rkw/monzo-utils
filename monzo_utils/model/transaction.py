from monzo_utils.model.base import BaseModel

class Transaction(BaseModel):

    DISPLAY_KEYS = ['date','type','money_in','money_out','pending','description']
    RELATIONSHIPS = {
        'account': ['`transaction`.account_id', 'account.id'],
        'transaction_metadata': ['`transaction`.id', 'transaction_metadata.transaction_id'],
        'pot': ['`transaction`.pot_id', 'pot.id']
    }
