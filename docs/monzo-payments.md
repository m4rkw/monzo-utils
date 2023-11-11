# Monzo Payments

## Overview

monzo-payments is a program intended for people who like to keep track of their
regular outgoings and/or pay their regular bills from a Monzo pot.

It can track direct debits, standing orders, regular card payments, payments to
a Flex card and finance payments (however they are paid).

These regular payments are configured in YAML and then when monzo-payments is
run it will print a summary of all of the payments indicating which ones are due
and when.

If you specify a pot name then the script assumes that the pot needs to have
enough funds to cover all regular expenses that are due. If you don't specify a
pot then it assumes that the account itself needs to have sufficient funds to
cover the expenses.

## Features

 - Supports tracking regular card payments, direct debits, standing orders,
   Amazon Payments payments, Flex payments and generic finance payments
 - Tracks salary payments to determine which regular payments are due within
   the current salary period
 - Indicates when a payment was last paid and when it's next due
 - Fairly customisable configuration in simple YAML, see [example](https://github.com/m4rkw/monzo-utils/blob/master/docs/payments_config_example.yaml)
 - For finance, Amazon Payments and Flex it tracks the number of payments made vs
   total number of payments and the total balance remaining
 - Can notify when the bills pot or account is in credit or shortfall
 - If using a bills pot it can automatically top it up or withdraw credit
 - Indicates the total outgoings for this month and next month, handy for people
   who like to schedule a regular payment into a bills pot
 - Can track payments in a separate account to the account that the salary gets
   paid into, eg if a joint account is used to pay bills
 - Can track payments monthly, yearly or when a payment is due at a fixed
   arbitrary date in the future
 - Supports skipping payments on specific months for bills that are only charged
   during certain months of the year

## Example

````
$ monzo-payments Current
    DUE: Card payment    Something I pay for            £20.83            2022-11-16   2023-11-11
   PAID: Card payment    Something I pay for            £11.63            2023-10-21   2023-11-21
   PAID: Card payment    Something I pay for            £37.40            2023-10-19   2024-10-19
SKIPPED: Card payment    Something I pay for            £24.26            2023-07-19   2024-07-18
SKIPPED: Card payment    Something I pay for            £11.40            2023-05-10   2024-05-10
SKIPPED: Amazon Payments Something I pay for       0/5  £25.85   £129.24               2023-12-01
    DUE: Direct Debit    Something I pay for            £35.34            2023-10-05   2023-11-05
SKIPPED: Direct Debit    Something I pay for            £9.80                          2023-11-16
   PAID: Standing Order  Something I pay for            £49.30            2023-10-15   2023-11-15
   PAID: Standing Order  Something I pay for            £37.12            2023-10-20   2023-11-20
    DUE: Finance         Something I pay for       9/24 £33.71   £684.90  2023-10-13   2023-11-13
SKIPPED: Finance         Something I pay for       0/6  £16.78   £129.24               2023-12-01
SKIPPED: Flex            Flex payment                   £84.12   £211.16               2023-11-16
SKIPPED: Flex            - Something I Flex'd      0/3  £8.62    £113.00               2023-11-16
SKIPPED: Flex            - Something I Flex'd      0/3  £75.50   £98.16                2023-11-16

                          TOTAL THIS MONTH:             £225.33
                          TOTAL NEXT MONTH:             £277.80
    due: £89.88
balance: £129.13
 credit: £39.25

withdraw credit? [y/N]
````

In one handy summary we can see all of our monthly outgoings, statuses are as
follows:

- DUE - payment is due before the next salary date
- PAID - payment was due this month but has been paid
- SKIPPED - payment is not due before the next salary date

We can see when a payment was last made and when it's next due, and for finance
payments like Amazon payments, Flex or generic finance we can see how many
payments we've made and how much of the balance is left to pay.

At the end we can see the total for this month and next month - allowing you to
easily set a regular payment into a Bills pot to cover next month's expenses.

Based on the remaining payments that are due this month it checks the balance in
the Bills pot and indicates whether it's in credit or has a shortfall.

Additionally the script provides some other helpful functions:

- If running interactively and the pot balance has a shortfall it prompts the
  user to deposit from their configured current account
- If running non-interactively it can either send a push notification to the
  user indicating that their pot has a shortfall, or it can be set to
  automatically transfer funds from the current account to the pot to cover the
  shortfall
- Similarly if the pot has more than it needs this can be notified or
  automatically withdrawn to the nominated current account

## Configuration

In order to use monzo-payments you need to create a config file for each account
that you wish to use it with, these need to be in:

````
~/.monzo/<account name>.yaml
````

See: [payments\_config\_example.yaml](https://github.com/m4rkw/monzo-utils/blob/master/docs/payments_config_example.yaml) for configuration details.
