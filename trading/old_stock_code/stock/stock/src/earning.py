#!/usr/bin/env python
#https://pypi.python.org/pypi/yahoo-finance/1.1.4
#from above link, you can get all api and construct your own system


#for Windows, install anaconda first, then goto anaconda console, type "easy_install yahoo_finance" 
import os
import sys
import inspect
import traceback
from  yahoo_finance import Share
import yahoo_finance as f
import json
import requests
import threading

url = 'https://biz.yahoo.com/research/earncal/20160614.html'
url = 'https://biz.yahoo.com/research/earncal/20160614.html'

try:
    r=requests.get(url)
    print("rrrr", dir(r))
    print("rrrr json", r.iter_lines())
    for x in r.iter_lines():
        print('line', x)
except Exception as e:
    print("Exception:"+str(e))
