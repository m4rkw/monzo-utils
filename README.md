# Monzo Utils

## Overview

A collection of utility python scripts for managing Monzo and Monzo Flex
accounts. PRs very welcome!

Monzo Utils comprises of:

 - [monzo-sync](https://github.com/m4rkw/monzo-utils/blob/master/docs/monzo-sync.md) - polls the Monzo API and syncs account, transaction and pot
   information into a local MySQL database
 - [monzo-status](https://github.com/m4rkw/monzo-utils/blob/master/docs/monzo-status.md) - shows a summary of all accounts and pots and their balances
 - [monzo-search](https://github.com/m4rkw/monzo-utils/blob/master/docs/monzo-search.md) - provides a simple commandline search interface for
   transactions in the SQL database, allowing search by string or transaction
   value
 - [monzo-payments](https://github.com/m4rkw/monzo-utils/blob/master/docs/monzo-payments.md) - tracks regular payments like direct debits, standing
   orders, regular card payments, flex payments and finance payments being paid
   from a bills pot and provides a summary show which payments are due and when

## Requirements

- A public webserver to receive the oauth token response
- Python 3 + pip
- MySQL or MariaDB
- A [pushover.net](https://pushover.net) account if notifications are required when using monzo-payments (free)

From pip:

- [monzo-api](https://github.com/petermcd/monzo-api) (thanks to Peter McDonald for writing this)
- mysqlclient
- PyYAML
- requests
- python-pushover

Should work on any posix-compliant system but has only been tested on Linux and
macOS.

## Installation

See: [INSTALL.md](https://github.com/m4rkw/monzo-utils/blob/master/docs/INSTALL.md)

## Disclaimer

Use at your own risk, I am not responsible for any issues that may arise from
the use of this software. You are solely responsible for maintaining the
security of your bank and credit accounts.

**This code is not affiliated with or endorsed by Monzo Bank in any way.**

## Notes and background

The code is a bit rough and there are probably uncaught edge-cases, bugs and
other potential issues due to my having very limited time to work on it.
It pretty much assumes you're in the UK and using GBP as your main currency,
there's no support for other currencies yet. There is some support for
specifying transactions in dollar amounts (precede with a $) but this hasn't
been well tested.

I switched to Monzo a few weeks before releasing this project on github after
around 20 years of using various different scraping technologies to scrape my
bank and credit accounts. I always wanted to release the code for those but
because scraping isn't officially supported by the banks it seemed unwise as it
could potentially be misused for nefarious purposes.

As Monzo has a public API this is no longer a concern, and the Monzo API is
relatively safe. It's not possible to transfer money other than between an
account and a pot so theft of funds via the API is not possible. It's not even
possible to transfer money between a sole current account and a joint account.

I hope that by releasing this others will find it useful and contribute to
making it better and more polished over time.

If you're wondering what the point of the "provider" table is, which only has
one record which for this project is always Monzo, this is so that it's possible
to have other data collection mechanisms populating the same database without
interfering with the Monzo data. I personally have a long history of data from
other sources so this is a useful way to differentiate it.
