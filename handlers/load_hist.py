#!/usr/bin/env python
# coding: utf-8

# In[70]:


from binance.client import Client
import openpyxl
import numpy as np
import pandas as pd
import os
from datetime import timedelta, datetime
import plotly.graph_objects as go
import time
import requests
import json
import math


# In[71]:


class LoadHistoryData:
    # ТИП: Спот или Фьючерсы
    MARKET = {
        "SPOT": "https://api.binance.com/api/v3",
        "FUTURE": "https://fapi.binance.com/fapi/v1"
    }

    # ТАЙМФРЕЙМ
    TF = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "4h": 240,
        "1d": 1440
    }

    # Переменные для работы
    _limit = None
    _limit_max = None
    _request_count = None
    _market = None
    _t_d, _f_d = None, None
    _t, _f, _tf, _sym = None, None, None, None

    def __init__(self, market, sym, tf, f, t):
        self._sym = sym
        self._tf = tf
        self._market = market

        # Максимальное кол-во баров у спота и фьюча разное
        self._limit_max = 1000 if market == 'SPOT' else 1500

        # Обрабатываем и конвертируем дату начала
        self._t = datetime.strptime(t, '%Y-%m-%d %H:%M:%S')
        self._t_d = str(datetime.strftime(self._t, '_%Y%m%d_%H%M_'))
        self._t = int(datetime.timestamp(self._t))

        # Обрабатываем и конвертируем дату окончания
        self._f = datetime.strptime(f, '%Y-%m-%d %H:%M:%S')
        self._f_d = str(datetime.strftime(self._f, '_%Y%m%d_%H%M'))
        self._f = int(datetime.timestamp(self._f))

        # Рассчитываем кол-во баров необходимых для закрытия переданных дат
        self._limit = int((self._t - self._f) / (self.TF[self._tf] * 60))

        # Рассчитывем кол-во запросов исходя из максимального кол-ва баров
        self._request_count = math.ceil(self._limit / self._limit_max)

    # Функция загрузки данных
    def load(self):
        payload = {}
        headers = {'Content-Type': 'application/json'}
        data = list()
        cur_limit = self._limit_max if self._request_count > 1 else self._limit
        cur_f = self._f
        cur_t = self._f + cur_limit * (self.TF[self._tf] * 60)
        for r in range(0, self._request_count):
            url = "{}/klines?symbol={}&interval={}&limit={}&startTime={}&endTime={}".format(
                self.MARKET[self._market],
                self._sym,
                self._tf,
                cur_limit,
                "{}000".format(cur_f),
                "{}000".format(cur_t)
            )
            self._limit -= self._limit_max
            cur_limit = cur_limit if self._limit >= self._limit_max else self._limit
            cur_f = cur_t
            cur_t = cur_t + cur_limit * (self.TF[self._tf] * 60)
            response = requests.request("GET", url, headers=headers, data=payload)
            if response.status_code == 200:
                d = json.loads(response.text)
                data.extend(d)
            # Сделаем паузу, чтобы не грузить биржу

        # Произведем постобработку списка
        for item in data:
            item[0] = int(str(item[0])[:-3])
            item.pop(11)
            item.pop(6)

        # Создадим датафрейм и присвоим имена колонок
        df = pd.DataFrame(data, columns=[
            'Date',
            'Open',
            'High',
            'Low',
            'Close',
            'Volume',
            'Quote asset volume',
            'Number of trades',
            'Taker buy base asset volume',
            'Taker buy quote asset volume'
        ])
        df['Open'] = df['Open'].astype(float)
        df['High'] = df['High'].astype(float)
        df['Low'] = df['Low'].astype(float)
        df['Close'] = df['Close'].astype(float)
        df['Quote asset volume'] = round(df['Quote asset volume'].astype(float), 0) / 1000000
        # Сформируем имя для csv файла и сохраним его
        return df


# In[108]:


def getPrices(BuyDateList, sl):
    z = (sl - BuyDateList) * 100 / (BuyDateList)
    percents = z
    return percents


# In[179]:


def delta_gmt_time(firstdate, delta_time):
    if delta_time.find('+') == -1:
        dts = datetime.strptime(firstdate, '%Y-%m-%d %H:%M:%S')
        dts = dts - timedelta(hours=int(delta_time.replace('-', '')))
        newdate = dts.strftime('%Y-%m-%d %H:%M:%S')
    else:
        dts = datetime.strptime(firstdate, '%Y-%m-%d %H:%M:%S')
        dts = dts + timedelta(hours=int(delta_time.replace('+', '')))
        newdate = dts.strftime('%Y-%m-%d %H:%M:%S')
    return newdate


# In[180]:


def delta_time(firstdate, delta_time):
    dts = datetime.strptime(firstdate, '%Y-%m-%d %H:%M:%S')
    dts = dts + timedelta(minutes=int(delta_time))
    newdate = dts.strftime('%Y-%m-%d %H:%M:%S')
    return newdate


# In[181]:


def minus_delta_time(firstdate):
    dts = datetime.strptime(firstdate, '%Y-%m-%d %H:%M:%S')
    dts = dts - timedelta(minutes=1)
    newdate = dts.strftime('%Y-%m-%d %H:%M:%S')
    return newdate


# In[182]:


def get_maximum(frame, buyprice):
    global maximum, time_of_maximum
    for i in range(3, len(frame) - 4):
        if (frame['High'][i] > frame['High'][i - 1]) and (frame['High'][i] > frame['High'][i - 2]) and (
                frame['High'][i] > frame['High'][i - 3]):
            if (frame['High'][i] > frame['High'][i + 1]) and (frame['High'][i] > frame['High'][i + 2]) and (
                    frame['High'][i] > frame['High'][i + 3]):
                maximum = frame['High'][i]
                time_of_maximum = i
        else:
            maximum = 0
            time_of_maximum = -1
            for n in range(0, len(frame)):
                if frame['High'][n] > maximum:
                    maximum = frame['High'][n]
                    time_of_maximum = n
    frame = [maximum, time_of_maximum, float(getPrices(buyprice, maximum))]
    return frame


# In[183]:


def get_minimum(frame, buyprice):
    global minimum, time_of_minimum
    for i in range(3, len(frame) - 4):
        if (frame['Low'][i] < frame['Low'][i - 1]) and (frame['Low'][i] < frame['Low'][i - 2]) and (
                frame['Low'][i] < frame['Low'][i - 3]):
            if (frame['Low'][i] < frame['Low'][i + 1]) and (frame['Low'][i] < frame['Low'][i + 2]) and (
                    frame['Low'][i] < frame['High'][i + 3]):
                minimum = frame['High'][i]
                time_of_minimum = i
        else:
            minimum = 10000000000
            time_of_minimum = 100000
            for n in range(0, len(frame)):
                if frame['Low'][n] < minimum:
                    minimum = frame['Low'][n]
                    time_of_minimum = n
    frame = [minimum, time_of_minimum, float(getPrices(buyprice, minimum))]
    return frame


# In[184]:

def start_hist_load(timeframe, delta, unx, market, xlsx_path):
    timeframe = float(timeframe)
    delta = float(delta)
    unx = unx
    market = market
    # market = 'SPOT' #Если пользователь нажимает кнопку "Спот"

    book = openpyxl.open(xlsx_path, read_only=True)
    sheet = book.active
    max_row = sheet.max_row

    # Парсинг отчета для получения нужных данных
    data_frame = []
    for row in range(2, max_row + 1):
        coin = sheet[row][0].value.replace(' ', '')
        buydate = sheet[row][1].value[:19]
        buydate = minus_delta_time(delta_gmt_time(buydate, unx))
        closedate = delta_time(buydate, delta)
        buyprice = float(sheet[row][4].value)
        deal = [coin, buydate, closedate, buyprice]
        #print(deal)
        if len(deal) > 0:
            data_frame += [deal]

    # In[190]:

    print(data_frame)
    extremums = []
    for i in range(0, len(data_frame)):
        print(data_frame[i])
        history_data = LoadHistoryData(market, data_frame[i][0] + 'USDT', timeframe, data_frame[i][1], data_frame[i][2])
        history_frame = history_data.load()
        max_cound = get_maximum(history_frame, data_frame[i][3])
        min_cound = get_minimum(history_frame, data_frame[i][3])
        extr_cound = [data_frame[i][0], max_cound[0], max_cound[1], max_cound[2], min_cound[0], min_cound[1], min_cound[2]]
        if len(extr_cound) > 0:
            extremums += [extr_cound]

    print(extremums)

    # In[191]:


    data = np.array(extremums)

    # convert NumPy array to pandas DataFrame

    df = pd.DataFrame(data=data, columns=['Монета', 'Максимум', 'Свеча максимума', 'Дельта максимума от ТВХ в %', 'Минимум',
                                          'Свеча минимума', 'Дельта минимума от ТВХ %'])
    return df


    # In[ ]:




