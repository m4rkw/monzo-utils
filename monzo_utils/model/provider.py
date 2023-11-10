from monzo_utils.model.base import BaseModel

class Provider(BaseModel):

    def accounts(self, orderby='name', orderdir='asc', limit=None, order=None):
        accounts = super().related('Account', 'provider_id', self.id, orderby, orderdir, limit)

        # return accounts in a specific order
        if order:
            sorted_accounts = []

            for account_name in order:
                for account in accounts:
                    if account.name == account_name:
                        sorted_accounts.append(account)
                        break

            return sorted_accounts

        return accounts
