# Installation

1. A database is required, this can currently be either MySQL or
SQLite3. If using MySQL you'll need to install that first.

2. If using MySQL create the database and import the schema:

````
$ mysql
mysql> create database monzo;
mysql> grant all privileges on monzo.* to monzo@localhost identified by 'databasepassword';
mysql> flush privileges;
````

````
$ cat schema_mysql.sql | mysql -umonzo -p -D monzo

````

3. If using SQLite you can create the database with:

````
$ mkdir ~/.monzo
$ cat schema_sqlite3.sql | sqlite3 ~/.monzo/data.db
````

4. Install the pip package:

````
$ pip3 install monzo-utils
````

5. You'll need a webserver on the machine where the sync is going to run in
order to receive the oauth tokens, example nginx config and a python CGI script
can be found in [oauth\_webserver/](https://github.com/m4rkw/monzo-utils/tree/master/oauth_webserver)

Your redirect URL for the Monzo OAuth Client you'll create in the next step must
point at this CGI script, eg:

https://hostname/monzo.py

(TLS is strongly recommended as the tokens can be used to access your Monzo
account)

Note: by default the CGI script drops the oauth token file in
/var/www/monzo/token, change this if desired in the [CGI script](https://github.com/m4rkw/monzo-utils/blob/master/oauth_webserver/monzo.py).

## Create the OAuth app on the Monzo website

1. Go to: https://developers.monzo.com and log in, it will send you a login url
via email.

2. Click grant and then approve the access request in the Monzo app, this is
granting the website temporary access to your Monzo account in order to
configure your OAuth clients.

3. Click New OAuth Client and fill out the details, ensure that the redirect URL
points at the monzo.py CGI script and that Confidentiality is set to
Confidential.

4. Click on the new OAuth client to view its Client ID and Client Secret.

## Setup Monzo Sync

Run the setup wizard to configure the sync script:

````
$ monzo-sync setup

========================
Monzo Utils Setup Wizard
========================

Requirements:

1) You must have created an OAuth client here: https://developers.monzo.com/apps/new
   Note: confidentiality must be set to Confidential

2) The MySQL database must be ready (see README.md)

3) The machine we are running on must be reachable on a known port from the internet.
   This is only required during setup for the initial oauth authentication flow.
   Once this is complete and the tokens are stored this can be removed.

Continue? [y/N] y

Enter MySQL host [127.0.0.1]:
Enter MySQL port [3306]:
Enter MySQL database [monzo]:
Enter MySQL username [monzo]:
Enter MySQL password [monzo]:

Enter Monzo Client ID: oauth2client_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Enter Monzo Client Secret: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Enter Monzo Client redirect URL: https://hostname/monzo.py
Enter the path where the CGI script will store the token file:
Enter Token path [/var/www/monzo/token]:

If the auth token expires or stops working the sync script can send
an email to notify you. Enter this email below or leave blank if not required.
Enter Email: emailaddress

Authentication required, check email or visit:

https://auth.monzo.com?client_id=oauth2client_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
````

Click the link, enter your Monzo email address and click Grant Access.

Wait for the email to arrive and click the link to log into Monzo.

You'll now get an approval request in the Monzo app, click Approve. At the
same time the webserver should receive a request that contains the oauth
tokens which the CGI script should store on disk for you.

If all has worked you will now be prompted for which accounts you want to sync
and give them names etc.

Once that's set up it will perform an initial sync and then you can sync any
time by running monzo-sync:

````
$ monzo-sync
````

It will synchronise accounts, transactions and related metadata into the local
database. OAuth tokens are automatically refreshed so as long as it's running
regularly you shouldn't need to do the oauth dance again.

## Monitoring

If you want to monitor the sync process you can add this to ~/.monzo/config.yaml:

````
touch_file: /path/to/file
````

Then whenever monzo-sync syncs successfully it will touch this file and you can
track its mtime to confirm that the sync is working.
