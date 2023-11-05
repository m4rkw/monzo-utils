# Monzo Status

Prints a summary of accounts and pots and their balances.

````
$ monzo-status
Account  Sort code  Account no  Balance   Available Bills    Savings   Petrol  Eating out  Travel
----------------------------------------------------------------------------------------------------------------
Current  11-11-11   12345678    £100.00   £100.00   £811.82  £3250.00  £0.00   £0.00       £84.74
Joint    11-11-12   98765432    £100.00   £100.00
Flex                            £200.00   £3800.00
````

If you want your accounts to appear in a specific order you can configure this
in ~/.monzo/config.yaml:

````
account_order:
  - Current
  - Joint
  - Flex
````
