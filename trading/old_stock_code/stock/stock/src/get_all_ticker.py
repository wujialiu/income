#! /usr/bin/env python
import os
import sys
import json
import finsymbols as data

if __name__ == '__main__':
    #a =data.get_sp500_symbols()
    a = data.get_amex_symbols()
    b = data.get_nyse_symbols()
    c = data.get_nasdaq_symbols()
    a +=b+c
    print(type(a), len(a))
    with open('ticker.json', 'w+') as outfile:
        json.dump(a, outfile)
    with open('ticker.txt', 'w+') as f:
        for line in a:
            f.write(str(line)+'\n')
