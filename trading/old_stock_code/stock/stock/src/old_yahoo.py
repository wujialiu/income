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

def get_one_stock(thread_id, tickers, good):
    for ticker in tickers:
        try:
            stock = Share(ticker['symbol'])
            a = stock.get_open()
            #print(thread_id, ":", ticker['symbol'], a, dir(stock))
            cap = stock.get_market_cap()
            if 'B' in cap:
                print(ticker['symbol'], cap)
                good.append(ticker['symbol'])

        except Exception as e:
            pass
            #print("EEEEEEEEE:" +str(e))

with open('ticker.txt', 'r') as f:
     data = json.load(f)
size = 100
tickers = []
good =[]
i = 0
while i < (len(data)/size):
   my_tickers = data[i*(size):(i+1)*size]
   tickers.append(my_tickers)
   good.append([])
   i+=1

my_ticker = data[i*size:]
tickers.append(my_ticker)
good.append([])

threads = []
for i in range(len(tickers)):
    t = threading.Thread(target=get_one_stock, args=(i, tickers[i], good[i]))
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
with open('good.txt', 'w+') as outfile:
        json.dump(final, outfile)
sys.exit()    



#get all args
my_args = []
if len(sys.argv) >= 2:
    my_args = sys.argv[1:]

stocks = []
for arg in my_args:
    #for every *.txt, we collect ticker here:
    if ".txt" in arg:
        with open(arg, "r") as f:
            stocks = f.readlines()
        my_args.remove(arg)    
#we display general market first        
#basic_list =['spy','dia', 'qqq', 'iwm','ewh', 'nky', 'ashr', 'gld', 'slv', 'oil']         
basic_list =['googl', 'spy','gld', 'fb']         

#then ticker in the command, then ticker in *.txt
#in any *.txt, one line one ticker
stocks =basic_list         

#print(stocks)
row_title = "\nticker price    price%  volume     volume% open      day_low   day_high  year_low  year_high market_cap P/E     avg_50" +\
    "    avg_200"

i=0
for ticker in stocks:

    sys.exit()
    try:
        if (i%10) == 0:
            print(row_title)
        ticker = ticker.rstrip()
        if len(ticker) == 0:
            continue
        stock = Share(ticker)
        stock.refresh()
        change = (float(stock.get_price()) - float(stock.get_prev_close()))/float(stock.get_prev_close()) 
        change = round(change *100.0, 2)
        if change > 0.0:
            change= '+' + str(change)
        else:    
            change =str(change)
          
        line = ticker.ljust(7) 
        line += stock.get_price().ljust(9)+ change.ljust(8)+ stock.get_volume().ljust(11) + \
            str(round(float(stock.get_volume())/float(stock.get_avg_daily_volume())*100.0)).ljust(8) +\
            stock.get_open().ljust(10)+ \
            stock.get_days_low().ljust(10)+ \
            stock.get_days_high().ljust(10)+ \
            stock.get_year_low().ljust(10)+ \
            stock.get_year_high().ljust(10)
        line = line + str(stock.get_market_cap()).ljust(11) + \
            str(stock.get_price_earnings_ratio()).ljust(8)+\
            stock.get_50day_moving_avg().ljust(10) +\
            stock.get_200day_moving_avg().ljust(10) 
        print(line)    
    except Exception as e:
        print("Exception error:", str(e))
        traceback.print_exc()
    i+=1

#you get get a spy.txt and then filter everything by yourself
