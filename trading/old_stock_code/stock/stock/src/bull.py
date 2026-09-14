#! /usr/bin/env python
import os
import sys
import pandas 
#import pandas.io.data as web   # Package and modules for importing data; this code may change depending on pandas version
import pandas_datareader.data as web   #for aconda
import datetime
import json

def average(result, n):
    return sum([x[2] for x in result][-n:])/n

def up_from_bottom(result):
    my_list = [x[2] for x in result]
    bottom = min(my_list)
    if (my_list[-1]/bottom) > 2.5:
        return True
    return False    

bull = []
try:
    with open('good.json', 'r') as f:
        data = json.load(f)

    end = datetime.date.today()
    my_day = end.day
    if end.day == 29:
        my_day =28
    start = datetime.datetime(end.year - 1, end.month, my_day)

    print('range:', start, end)
    # First argument is the series we want, second is the source ("yahoo" for Yahoo! Finance), third is the start date, fourth is the end date
    for x in data:
        try:
            apple = web.DataReader(x, "yahoo", start, end)
            #print(apple.head())
            #print('type', type(apple))
            rows = apple.iterrows()
            result =[]
            for r in rows:
                y=r
                #print('second', x[1].__str__)
                item =  y[1].__str__()
                items=item.split()
                result.append((items[14], float(items[9]), float(items[12])))
            #print(result)    
            if len(result) < 100:
                continue

            if result[-1][2] > average(result, 20):
                if average(result,20) > average(result, 50):
                    if average(result, 10) > average(result, 100):
                        if up_from_bottom(result):
                            print('bull:', x)
                            bull.append(x)
        except Exception as e:
            print('Exception for foo loop', x, str(e))
           
    with open('bull.txt', 'w+') as outfile:
        for z in bull:
            outfile.write(str(z)+'\n')

except Exception as e:
    print("EEEException: ", str(e))
f.close()
