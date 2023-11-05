#!/usr/bin/env python3

import os
import sys
import json

token = os.environ['QUERY_STRING'].split('=')[1].split('&')[0]
state = os.environ['QUERY_STRING'].split('=')[2]

with open('/var/www/monzo/token.new','w') as f:
  f.write(json.dumps({'token':token,'state':state}))

os.rename('/var/www/monzo/token.new','/var/www/monzo/token')

print("location:monzo://accounts\n")
