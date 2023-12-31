# Changelog

## 0.0.52 - 05/01/2024

- Minor bugfixes

## 0.0.51 - 22/12/2023

- Fixed column alignment bug

## 0.0.50 - 14/12/2023

- Fixed incorrect calculation of monthly flex payment

## 0.0.49 - 14/12/2023

- Added support for monthly transfers to pots when salary is paid

## 0.0.48 - 13/12/2023

- Indicate when we can't connect to the database

## 0.0.47 - 09/12/2023

- When finding an older payment for display purposes this cannot be before the start date

## 0.0.46 - 09/12/2023

- Add support for renewals where the price is changing

## 0.0.45 - 25/11/2023

- Display next month's Flex payment in the monzo-payments summary

## 0.0.44 - 21/11/2023

- Fixed crash during sync when a new account is returned

## 0.0.43 - 18/11/2023

- Changes to support json output for a webservice

## 0.0.42 - 18/11/2023

- Fixed incorrect finance payment calculation

## 0.0.41 - 16/11/2023

- Don't auto withdraw/deposit if we have a tty
- Fixed flex output

## 0.0.40 - 16/11/2023

- Fixed flex payment calculation

## 0.0.39 - 16/11/2023

- Fixed invalid references

## 0.0.38 - 15/11/2023

- Fixed display issue with pending incoming transactions

## 0.0.37 - 15/11/2023

- Fixed sync on withdraw/deposit
- Notify if deposit/withdraw fails

## 0.0.36 - 15/11/2023

- Typo

## 0.0.35 - 15/11/2023

- Bugfix

## 0.0.34 - 15/11/2023

- Bugfixes

## 0.0.33 - 15/11/2023

- Bugfix

## 0.0.32 - 14/11/2023

- Bugfix

## 0.0.31 - 14/11/2023

- Bugfixes

## 0.0.30 - 14/11/2023

- Bugfix

## 0.0.29 - 14/11/2023

- Show next month total after credit balance adjustment

## 0.0.28 - 12/11/2023

- Added support for SQLite3

## 0.0.27 - 12/11/2023

- Bugfixes

## 0.0.26 - 12/11/2023

- Bugfixes

## 0.0.25 - 12/11/2023

- Decoupled the MySQL code from the DB layer

## 0.0.24 - 12/11/2023

- Add support for excluding accounts from search by config

## 0.0.23 - 12/11/2023

- Refactoring

## 0.0.22 - 12/11/2023

- Refactored monzo-payments
- Refactored monzo-sync, split API stuff out into a separate file

## 0.0.21 - 12/11/2023

- Bugfix in sync code

## 0.0.20 - 12/11/2023

- Refactoring

## 0.0.19 - 12/11/2023

- Added logging

## 0.0.18 - 11/11/2023

- Bugfixes

## 0.0.17 - 11/11/2023

- Show due date when start\_date is defined in payment config

## 0.0.16 - 11/11/2023

- Added flex payment summary back in after refactoring work

## 0.0.15 - 11/11/2023

- Refactored monzo-payments and fixed some bugs

## 0.0.14 - 11/11/2023

- Bugfixes in monzo-payments

## 0.0.12 - 11/11/2023

- Bugfix: num payments calculation for finance wasn't using a LIKE query

## 0.0.11 - 11/11/2023

- Use ORM query interface for monzo-search

## 0.0.10 - 11/11/2023

- Added support for pending refunds in monzo-payments

## 0.0.9 - 11/11/2023

- Fixed sync issues introduced accidentally in 0.0.7

## 0.0.8 - 11/11/2023

- Ensure column names are always escaped in sql queries

## 0.0.7 - 10/11/2023

- Push credit limit into the account table for credit cards
- Created models for the database records as a first step towards
  an abstraction layer for the database backend

## 0.0.6 - 08/11/2023

- Fixed ordering of records in monzo-payments, could have caused issues if historical
  data was ever backfilled

## 0.0.5 - 07/11/2023

- Support date searching in monzo-search

## 0.0.4 - 06/11/2023

- Fixed confusing error message in monzo-payments
- Fixed error in exception handling
- Fixed some code paths that resulted in an undefined variable
- Forked python-pushover as python-pushover2 and added support for Python3
  to make life easier, original project looks dead

## 0.0.3 - 06/11/2023

- Timeouts are common with the Monzo API so catch these and handle without
  writing to stderr

## 0.0.2 - 05/11/2023

- Tweaked output in the setup wizard slightly

## 0.0.1 - 05/11/2023

- Initial public release
