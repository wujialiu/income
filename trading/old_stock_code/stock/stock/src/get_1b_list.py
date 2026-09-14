#!/usr/bin/env python
#https://pypi.python.org/pypi/yahoo-finance/1.1.4
#from above link, you can get all api and construct your own system

import os
import sys
import inspect
import traceback
from  yahoo_finance import Share
import yahoo_finance as f
import json
import requests
import threading

def get_one_stock(thread_id, tickers, good, big, small):
    for ticker in tickers:
        try:
            stock = Share(ticker['symbol'])
            print(thread_id, ":", ticker['symbol'])
            cap = stock.get_market_cap()
            if 'B' in cap:
                position = cap.find('B')
                big.append(float(cap[:position]) *1000000000.0)
                print(ticker['symbol'], cap)
                good.append(ticker['symbol'])
            if 'M' in cap:
                position = cap.find('M')
                small.append(float(cap[:position]) *1000000.0)
                print(ticker['symbol'], cap)

        except Exception as e:
            pass
            #print("EEEEEEEEE:" +str(e))

with open('ticker.json', 'r') as f:
     data = json.load(f)
size = 100
tickers = []
good =[]
big = []
small = []
i = 0
while i < (len(data)/size):
   my_tickers = data[i*(size):(i+1)*size]
   tickers.append(my_tickers)
   good.append([])
   big.append([])
   small.append([])
   i+=1
if (i*size) < len(data):
    my_ticker = data[i*size:]
    tickers.append(my_ticker)
    good.append([])
    big.append([])
    small.append([])

threads = []
for i in range(len(tickers)):
    t = threading.Thread(target=get_one_stock, args=(i, tickers[i], good[i], big[i], small[i]))
    threads.append(t)
    t.start()
for j in range(len(threads)):
    threads[j].join()

total = 0
final = []
for x in good:
    for y in x:
        final.append(y)    
    total += len(x)
    
print('total of 1B companies:', len(final))
sum_big = 0.0
for x in big:
   sum_big += sum(x)
print("sum of big", sum_big/1000000000.0)   
sum_small = 0.0
for x in small:
   sum_small += sum(x)
print("sum of small", sum_small/1000000000.0)   

with open('good.json', 'w+') as outfile:
    json.dump(final, outfile)
with open('good.txt', 'w+') as f:
    for line in final:
        f.write(str(line) + '\n')
sys.exit()    


