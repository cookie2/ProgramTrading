import requests
import json
import pandas as pd
from pandas_datareader import data
import yfinance as yf
from talib import RSI
from talib import SMA
from talib import MA
from talib import MACD
import matplotlib.pyplot as plt
import numpy as np
from io import StringIO
import time
import datetime
from dateutil.relativedelta import relativedelta
import stock as st
import csv
import sys
import tushare as twsecheck
import twstock
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import os
#import fix_yahoo_finance as yf

#偽造User-Agent
ua = UserAgent()
headers = {
    'User-Agent': ua.random
}

# 登入Cmoney
vs = st.VirtualStockAccount('0970401357', 'GwR6fgCLFx5i3ws', 1)

#日期處理
tdt = datetime.datetime.now()
today = tdt.strftime("%Y-%m-%d")
todayurl = tdt.strftime("%Y%m%d")
yesterday = (tdt + datetime.timedelta(days=-1)).strftime("%Y-%m-%d")
TF = (tdt + datetime.timedelta(days=-400)).strftime("%Y-%m-%d")
TenToNow = (tdt - relativedelta(years=1)).strftime('%Y-%m-%d')
RepDate = today.replace(str(tdt.year), str(tdt.year - 1911))

#星期幾
weekday = datetime.date.today().weekday()

#紀錄資料夾
recoardfile = 'G:/我的雲端硬碟/Stock Recoard/'

#下載股市資料
r = ""
df = ""
IfOpen = False
twseresp = json.loads(requests.post('https://www.twse.com.tw/exchangeReport/MI_INDEX?response=json&date=' + todayurl + '&type=ALL', headers = headers).text)
time.sleep(5)
yf.pdr_override()
#停資停券
exchangerep = json.loads(requests.post('https://www.twse.com.tw/exchangeReport/BFI84U?response=json', headers = headers).text)["data"]

#是否開市
if twseresp["stat"] == "OK":
    # 下載股價
    r = requests.post('https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date=' + todayurl + '&type=ALL', headers = headers)
    # 整理資料，變成表格
    df = pd.read_csv(StringIO(r.text.replace("=", "")),header=["證券代號" in l for l in r.text.split("\n")].index(True)-1)
    IfOpen = True

#開啟文件
position = open(recoardfile + '/Position/' + today + '.csv', 'w', encoding="utf-8", newline='')#建立部位
writer1 = csv.writer(position)
writer1.writerow(['股票代號', '倉別', '收盤價', '200日均線', '60日均線', 'RSI(2)', '100日平均成交股數'])

liquidation = open(recoardfile + '/Liquidation/' + today + '.csv', 'w', encoding="utf-8", newline='')#平倉
writer2 = csv.writer(liquidation)
writer2.writerow(['股票代號', '目標價', 'RSI(2)', '張數', '平倉種類', '觸發條件'])

hold = open(recoardfile + '/Hold/' + today + '.csv', 'w', encoding="utf-8", newline='')#持有部位
writer3 = csv.writer(hold)
writer3.writerow(['股票代碼', '股票名稱', '倉別', '現價', '買賣均價', '張數', '試算損益', '報酬率', '平均成本', '預估賣出收入', '今日可平倉數', '股票交易單位', '認股權證'])

errorlog = open(recoardfile + '/ErrorLog/' + today + '.csv', 'w', encoding="utf-8", newline='')#持有部位
writer4 = csv.writer(errorlog)
writer4.writerow(['股票代碼'])

#建立部位
def CodeBuy(code, index):
    aim = code+".TW"
    aimTW = code
    target = ''
    try:
        target = data.get_data_yahoo(aim, start=TF, end=today)
    except:
        time.sleep(5)
        try:
            target = data.get_data_yahoo(aim, start=TF, end=today)
        except:
            target = data.get_data_yahoo(aim+"O", start=TF, end=today)
    if target['Volume'][-1] == 0 or twseresp["data9"][index][8] == '--':
        return False

    #股價收盤
    price = float((twseresp["data9"][index][8]).replace(',', ''))

    #100日平均成交股數
    Volume = target['Volume'][(len(target['Volume'])-101):]
    AV = 0
    for DV in Volume:
        AV += (DV / 100)
    AV = round(AV, 2)

    #股價200日均線
    SMA_200 = float(SMA(round(target.Close, 2), timeperiod = 200)[-1])
    SMA_200 = round(SMA_200, 2)
    SMA_60 = float(SMA(round(target.Close, 2), timeperiod = 60)[-1])
    SMA_60 = round(SMA_60, 2)

    #取rsi(2)
    rsi2 = float(RSI(round(target.Close, 2), 2)[-1])
    rsi2 = round(rsi2, 2)
    
    #目標價格
    aimprice = price

    #股價高於200日均線和60日均線, RSI2小於10, 成交股數高於500k, 買入
    if price > SMA_200 and price > SMA_60 and rsi2 < 10 and AV > 500000:
        vs.buy(aimTW, 1, aimprice)
        writer1.writerow([aim, '買入', aimprice, SMA_200, SMA_60, rsi2, AV])
        return True
    #股價低於200日均線和60日均線, RSI2大於90, 成交股數高於500k, 放空
    elif price < SMA_200 and price < SMA_60 and rsi2 > 90 and AV > 500000:
        vs.Margin_Sell(aimTW, 1, aimprice)
        writer1.writerow([aim, '放空', aimprice, SMA_200, SMA_60, rsi2, AV])
        return True
    else:
        return False

#賣出
def CodeSell(code, Status, index):
    aim = code+".TW"
    aimTW = code
    target = ''
    try:
        target = data.get_data_yahoo(aim, start=TF, end=today)
    except:
        time.sleep(5)
        try:
            target = data.get_data_yahoo(aim, start=TF, end=today)
        except:
            target = data.get_data_yahoo(aim+"O", start=TF, end=today)
    target.dropna(axis=0, how='any')
    if target['Volume'][-1] == 0 or twseresp["data9"][index][8] == '--':
        return False
    
    #股價現在賣價
    np = float((vs.get_price(aimTW))['SalePrice'])
    
    #取rsi(2)
    rsi2 = float(RSI(round(target.Close, 2), 2)[-1])
    rsi2 = round(rsi2, 2)
    
    #股票平均購買價
    pp = Status['DeAvgPr']
    pp = float(pp)

    if Status['TkT'] == '現股':
        #手續費
        np_f = 0.0000000
        np_f = (np * 0.001425)+( np * 0.003)
        #計算損益
        pr = 0.0000000
        pr = (np - np_f) / (pp + (pp * 0.001425))
    
        #目標價格
        aimprice = np
    
        #股價跌幅達20%止損賣出
        if float(pr) < 0.8:
            vs.sell(aimTW, int(Status['IQty']), round(aimprice * 0.96, 2))
            writer2.writerow([code, aimprice, rsi2, int(Status['IQty']), '現股賣出', '止損'])
            return True
        #股價漲幅達40%賣出
        elif float(pr) > 1.4:
            vs.sell(aimTW, int(Status['IQty']), aimprice)
            writer2.writerow([code, aimprice, rsi2, int(Status['IQty']), '現股賣出', '停利'])
            return True
        #RSI2>80賣出
        elif float(rsi2) > 80 and float(pr) > 1:
            vs.sell(aimTW, int(Status['IQty']), aimprice)
            writer2.writerow([code, aimprice, rsi2, int(Status['IQty']), '現股賣出', '抵目標RSI'])
            return True
        else:
            return False
    elif Status['TkT'] == '融券':
        #手續費
        np_f = 0.0000000
        np_f = (np * 0.001425)+( np * 0.003)
        #計算漲跌幅
        pr = 0.0000000
        pr = (pp - np_f - np) / pp
    
        #目標價格
        aimprice = np
    
        #股價漲幅達20%止損賣出
        if float(pr) < -0.2:
            vs.Margin_Buy(aimTW, int(Status['IQty']), round(aimprice * 1.04, 2))
            writer2.writerow([code, aimprice, rsi2, int(Status['IQty']), '融券補回', '止損'])
            return True
        #股價跌幅達40%賣出
        elif float(pr) > 0.4:
            vs.Margin_Buy(aimTW, int(Status['IQty']), aimprice)
            writer2.writerow([code, aimprice, rsi2, int(Status['IQty']), '融券補回', '停利'])
            return True
        #RSI2<20賣出
        elif float(rsi2) < 20  and float(pr) > 0:
            vs.Margin_Buy(aimTW, int(Status['IQty']), aimprice)
            writer2.writerow([code, aimprice, rsi2, int(Status['IQty']), '融券補回', '抵目標RSI'])
            return True
        else:
            return False


#停資停券代碼
def CheckExchangeReport():
    stoplist = []
    for args in exchangerep:
        stoplist.append(args[0])
    return stoplist

def strategy1():
    #買入或放空
    a = df[(df['證券代號']=='1101')].index.tolist()
    args = df['證券代號'][a[0]:]
    forbiddenlist = CheckExchangeReport()
    for arg in args:
        try:
            if arg not in forbiddenlist:
                i = df[(df['證券代號']==arg)].index.tolist()[0]
                g = CodeBuy(arg, i)
        except:
            writer4.writerow([arg])
    #售出或補回
    rows = vs.status()
    for get in rows:
        i = df[(df['證券代號']==arg)].index.tolist()[0]
        CodeSell(get['Id'], get, i)
        stockrow = []
        #取得並記錄帳戶狀態
        for text in get:
            stockrow.append(get[text])
        writer3.writerow(stockrow)

if __name__ == "__main__":
    if IfOpen:
        strategy1()
    position.close()
    liquidation.close()
    hold.close()
    errorlog.close()
    os._exit(0)
        
