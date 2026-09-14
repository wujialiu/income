import csv
data=[]
with open('eggs.csv', newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=' ', quotechar='|')
    for row in reader:
        #print(', '.join(row))
        fs=row[0].split(',')
        #print("1111", fields)
        if len(fs)<=5:
            continue
        ex=["SHE","SHG","NMFQS","exchange","","OTCGREY","OTCBB",'PINK',"OTCMKTS","OTCQB","OTCQX","LSE","BATS"]
        if fs[1] in ex:
            continue
        if fs[3]!="USD":
            continue    
        if fs[2]!="Stock" and fs[2]!="ETF":
            continue    
        #print(row[0])
        if fs[4]=="":
            continue
        if fs[5]=="":
            continue
        mydata=[fs[0],fs[1],fs[2],fs[3],fs[4],fs[5]]
        data.append(mydata)
     
with open('ticker.txt', 'w+') as f:
    for x in data:
        print(x)    
        f.write(x[0]+"*"+x[1]+"*"+x[2] + '*'+  x[4]+"*"+x[5]+'\n')
