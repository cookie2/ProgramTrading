import stock as st
import time
import datetime
import csv
import sys
import os

vs = st.VirtualStockAccount('0970401357', 'GwR6fgCLFx5i3ws', 1)

#日期處理
tdt = datetime.datetime.now()
today = tdt.strftime("%Y-%m-%d")
#紀錄資料夾
recoardfile = 'G:/我的雲端硬碟/Stock Recoard/'

#取得並記錄帳戶狀態
def GetStatu():
    rows = vs.status()
    for row in rows:
        get = []
        for text in row:
            get.append(row[text])
        writer3.writerow(get)

hold = open(recoardfile + '/Hold/' + today + '.csv', 'w', encoding="utf-8", newline='')#持有部位
writer3 = csv.writer(hold)
writer3.writerow(['股票代碼', '股票名稱', '倉別', '現價', '買賣均價', '張數', '試算損益', '報酬率', '平均成本', '預估賣出收入', '今日可平倉數', '股票交易單位', '認股權證'])

GetStatu()
hold.close()
