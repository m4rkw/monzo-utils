# OAuth token response

In order for the oauth flow to work you need a public webserver that can receive
the oauth token.

This CGI script [monzo.py](https://github.com/m4rkw/monzo-utils/blob/master/oauth_webserver/monzo.py) - needs to be reachable via a public URL and needs to
receive the token and place it in a local file where it can be picked up by the
sync process.

This only happens during the initial authentication flow when you first run a
sync, after that you'll have an access token that can be perpetually refreshed.
You'll only need the webserver again if the token expires and you haven't
refreshed it (the sync code automatically refreshes it).
