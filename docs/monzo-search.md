# Monzo Search

A handy search interface for synced transactions.

### Usage

````
usage:

monzo-search [-p] [-d] [search string]

-p                 # include pot transactions
-d                 # show declined transactions

search string examples:

monzo-search amazon                                # case-insensitive string search
monzo-search TfL Travel Charge                     # case-insensitive string search
monzo-search on 2023-11-05                         # transactions for date
monzo-search on 2023-11                            # transactions for month
monzo-search on 2023                               # transactions for year
monzo-search on 2023-11-05 amazon                  # transactions on date matching string
monzo-search from 2023-11-05                       # transactions from date onwards
monzo-search from 2023-11-05 amazon                # transactions from date onwards matching string
monzo-search to 2023-11-05                         # transactions up to date
monzo-search to 2023-11-05 amazon                  # transactions up to date matching string
monzo-search from 2023-11-01 to 2023-11-05         # transactions for date range
monzo-search from 2023-11-01 to 2023-11-05 amazon  # transactions for date range matching string
monzo-search from 2022 to 2023                     # year range
monzo-search from 2022-04 to 2022-09               # month range
monzo-search 10.99                                 # query for monetary value
monzo-search 11                                    # query for monetary value 11.00 - 11.99

dates can be in any parseable format
````

### By default - show the last years worth of transactions

````
$ monzo-search
````

### Find transactions by string (case-insensitive)

````
$ monzo-search amazon
account  pot    date         money_in  money_out  description
----------------------------------------------------------------------------------------------------------------------------
Current         11/10 19:08            0.82 R     AWS EMEA aws.amazon.co LUX
Current         13/10 19:40            0.82 R     AWS EMEA aws.amazon.co LUX
Current  Bills        23:10            0.82 R     AWS EMEA aws.amazon.co LUX
Current         17/10 20:22            3.06       AMZNMKTPLACE AMAZON.CO LONDON GBR
Current         19/10 02:05  0.82                 AWS EMEA aws.amazon.co LUX
Current         21/10 01:05  0.82                 AWS EMEA aws.amazon.co LUX
Current  Bills        01:14  0.82                 AWS EMEA aws.amazon.co LUX
Current         24/10 19:09            31.94      AMAZON* 204-8922853-10 3528008547917 LUX
Current         26/10 09:32            12.92      AMZNMktplace amazon.co.uk GBR
Current               11:58  12.92                AMAZON MARKETPLACE AMAZON.CO.UK GBR
Current  Bills        11:59            *19.73*    CHATGPT SUBSCRIPTION +14158799686 USA
````

The R suffix indicates that a transaction was refunded by a later transaction.

Where a value is shown wrapped in * * this means the transaction is still pending.

### Find transactions by monetary value

````
$ monzo-search 8.99
account  pot    date         money_in  money_out  description
------------------------------------------------------------------------------------
Current  Bills  21/10 13:02            8.99       APPLE.COM/BILL APPLE.COM/BIL IRL
````
