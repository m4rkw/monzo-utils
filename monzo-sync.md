# Monzo Sync

Synchronises transactions into a local MySQL database.

## Setup

See: [INSTALL.md](https://github.com/m4rkw/monzo-utils/blob/master/INSTALL.md) for installation instructions.

Once installed you can initiate the setup process with:

````
$ monzo-sync setup
````

Once setup it is simply invoked with no arguments in order to initiate the sync:

````
$ monzo-sync
````

It will synchronise accounts, transactions and related metadata into the local
database. OAuth tokens are automatically refreshed so as long as it's running
regularly you shouldn't need to do the oauth dance again.

## Finding new accounts

During the installation process monzo-sync will scan your Monzo accounts and
prompt you to add them for syncing.

If you get new accounts at any point you can scan again with:

````
$ monzo-sync scan-accounts
````
