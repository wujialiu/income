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
import datetime

"""
YearLow
OneyrTargetPrice
DividendShare
ChangeFromFiftydayMovingAverage
FiftydayMovingAverage
SharesOwned
PercentChangeFromTwoHundreddayMovingAverage
PricePaid
DaysLow
DividendYield
Commission
EPSEstimateNextQuarter
ChangeFromYearLow
ChangeFromYearHigh
EarningsShare
AverageDailyVolume
LastTradePriceOnly
YearHigh
EBITDA
Change_PercentChange
AnnualizedGain
ShortRatio
LastTradeDate
PriceSales
EPSEstimateCurrentYear
BookValue
LastTradeDateTimeUTC
Bid
AskRealtime
PreviousClose
DaysRangeRealtime
EPSEstimateNextYear
Volume
HoldingsGainPercent
PercentChange
TickerTrend
Ask
ChangeRealtime
PriceEPSEstimateNextYear
HoldingsGain
Change
MarketCapitalization
Name
HoldingsValue
DaysRange
AfterHoursChangeRealtime
symbol
ChangePercentRealtime
DaysValueChange
LastTradeTime
StockExchange
DividendPayDate
LastTradeRealtimeWithTime
Notes
MarketCapRealtime
ExDividendDate
PERatio
DaysValueChangeRealtime
ErrorIndicationreturnedforsymbolchangedinvalid
ChangeinPercent
HoldingsValueRealtime
PercentChangeFromFiftydayMovingAverage
PriceBook
ChangeFromTwoHundreddayMovingAverage
DaysHigh
PercentChangeFromYearLow
TradeDate
LastTradeWithTime
BidRealtime
YearRange
HighLimit
OrderBookRealtime
HoldingsGainRealtime
PEGRatio
Currency
LowLimit
HoldingsGainPercentRealtime
TwoHundreddayMovingAverage
PERatioRealtime
PercebtChangeFromYearHigh
Open
PriceEPSEstimateCurrentYear
MoreInfo
Symbol
(u'FAX', {u'YearLow': u'4.22', u'OneyrTargetPrice': None, u'DividendShare': u'0.42', u'ChangeFromFiftydayMovingAverage': u'0.10', u'FiftydayMovingAverage': u'4.95', u'SharesOwned': None, u'PercentChangeFromTwoHundreddayMovingAverage': u'+6.84%', u'PricePaid': None, u'DaysLow': u'5.02', u'DividendYield': u'8.35', u'Commission': None, u'EPSEstimateNextQuarter': u'0.00', u'ChangeFromYearLow': u'0.83', u'ChangeFromYearHigh': u'-0.04', u'EarningsShare': u'-0.61', u'AverageDailyVolume': u'744766', u'LastTradePriceOnly': u'5.05', u'YearHigh': u'5.09', u'EBITDA': u'0.00', u'Change_PercentChange': u'+0.02 - +0.40%', u'AnnualizedGain': None, u'ShortRatio': u'0.27', u'LastTradeDate': u'6/10/2016', u'PriceSales': u'12.22', u'EPSEstimateCurrentYear': u'nan', u'BookValue': u'5.57', u'LastTradeDateTimeUTC': '2016-06-10 20:02:00 UTC+0000', u'Bid': u'4.95', u'AskRealtime': None, u'PreviousClose': u'5.03', u'DaysRangeRealtime': None, u'EPSEstimateNextYear': None, u'Volume': u'280738', u'HoldingsGainPercent': None, u'PercentChange': u'+0.40%', u'TickerTrend': None, u'Ask': u'5.10', u'ChangeRealtime': None, u'PriceEPSEstimateNextYear': None, u'HoldingsGain': None, u'Change': u'+0.02', u'MarketCapitalization': u'1.29B', u'Name': u'Aberdeen Asia-Pacific Income Fu', u'HoldingsValue': None, u'DaysRange': u'5.02 - 5.05', u'AfterHoursChangeRealtime': None, u'symbol': u'FAX', u'ChangePercentRealtime': None, u'DaysValueChange': None, u'LastTradeTime': u'4:02pm', u'StockExchange': u'ASE', u'DividendPayDate': u'3/28/2016', u'LastTradeRealtimeWithTime': None, u'Notes': None, u'MarketCapRealtime': None, u'ExDividendDate': u'5/17/2016', u'PERatio': None, u'DaysValueChangeRealtime': None, u'ErrorIndicationreturnedforsymbolchangedinvalid': None, u'ChangeinPercent': u'+0.40%', u'HoldingsValueRealtime': None, u'PercentChangeFromFiftydayMovingAverage': u'+1.99%', u'PriceBook': u'0.90', u'ChangeFromTwoHundreddayMovingAverage': u'0.32', u'DaysHigh': u'5.05', u'PercentChangeFromYearLow': u'+19.67%', u'TradeDate': None, u'LastTradeWithTime': u'4:02pm - <b>5.05</b>', u'BidRealtime': None, u'YearRange': u'4.22 - 5.09', u'HighLimit': None, u'OrderBookRealtime': None, u'HoldingsGainRealtime': None, u'PEGRatio': u'0.00', u'Currency': u'USD', u'LowLimit': None, u'HoldingsGainPercentRealtime': None, u'TwoHundreddayMovingAverage': u'4.73', u'PERatioRealtime': None, u'PercebtChangeFromYearHigh': u'-0.79%', u'Open': u'5.02', u'PriceEPSEstimateCurrentYear': None, u'MoreInfo': None, u'Symbol': u'FAX'})
"""

def is_good(mydata):
    try:
        #print('gggggg', mydata['ChangeFromTwoHundreddayMovingAverage'], "bbbb", mydata)
        if float(mydata['ChangeFromFiftydayMovingAverage']) < 0:
            return False
        fifty = None    
        two_hundred = None
        fifty = mydata['PercentChangeFromFiftydayMovingAverage'][:-2]
        if float(fifty) < 5.0:
            return False

        if float(mydata['ChangeFromTwoHundreddayMovingAverage']) < 0:
            return False
        two_hundred = mydata['PercentChangeFromTwoHundreddayMovingAverage'][:-2]
        if float(two_hundred) < 5.0:
            return False

        if fifty < two_hundred: 
            return False

        year_low = float(mydata['YearLow'])
        year_high = float(mydata['YearHigh'])

        if year_high < 10.00:
            return False

        if ((year_high - year_low)/year_low) < 1.40:
            return False

        retrace = float(mydata['PercebtChangeFromYearHigh'][:-2])
        if retrace < -20.0:
            return False

        return True    
    except Exception as e:
        print("Exception in is_good:" +str(e) +'***'+ fifty + '***' + two_hundred)
        return False
        #pass
        

def get_one_stock(thread_id, tickers, good):
    #print(thread_id, len(tickers))
    for ticker in tickers:
        try:
            stock = Share(ticker)
            stock.refresh()
            my_data = stock.data_set
            #for x in my_data.keys():
            #    print(x)
            #print(ticker, my_data)
            tmp = {}
            tmp[ticker]=my_data
            if is_good(my_data):
                #print('!!!!!!', thread_id, tmp)
                good.append(tmp)

        except Exception as e:
            #pass
            print("Exception in get_one_stock:" +str(e))

with open('good.json', 'r') as f:
     data = json.load(f)
print(len(data))     
size = 50
tickers = []
good =[]
i = 0
while i < (len(data)/size):
   my_tickers = data[i*(size):(i+1)*size]
   tickers.append(my_tickers)
   good.append([])
   i+=1

if (i*size) < len(data):
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
    
print('total of 1B companies with data_set:', len(final))

now = datetime.datetime.now()
my_json = now.strftime("%Y_%m_%d")+'.json'
my_text = now.strftime("%Y_%m_%d")+'.txt'

with open(my_json, 'w+') as outfile:
        json.dump(final, outfile)

with open(my_text, 'w+') as outfile:
    for x in final:
        outfile.write(str(x)+'\n')
sys.exit()    


