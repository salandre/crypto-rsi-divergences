import talib, numpy
import datetime, time
from binance.client import Client
from binance.enums import *
import config

TIME_DELTA = 50 # Nombre de prériodes (= nombre de chandeliers)
DIV_DELTA = 20 # Nombre de chandeliers à prendre en compte pour le calcul de divergence
RSI_MIN = 30 # RSI minimum
RSI_MAX = 70 # RSI maximum
RSI_WARM_PERIOD = 15 # période mini pour le RSI 14 périodes

print("Démarrage du scanner")

client = Client(config.API_KEY, config.API_SECRET)

tickers = []
message = ""

binance_tickers = client.get_all_tickers()

print("récupération des paires")

for ticker in binance_tickers: 
    if(ticker['symbol'].find('BTC') != -1 and ticker['symbol'][:3] != 'BTC'):
        tickers.append(ticker['symbol'])

print("{} paires récupérées".format(len(tickers)))

while True:

    minute = datetime.datetime.now().strftime("%M")
    if minute == "01":

        print("début : {}".format(datetime.datetime.now().strftime("%H:%M:%S")))

        fin = datetime.datetime.today().strftime("%d %b, %Y")
        heure = (datetime.datetime.now() - datetime.timedelta(seconds=(3600))).strftime("%H")
        fin = fin + ", " + heure + ":00:00"

        debut = (datetime.datetime.now() - datetime.timedelta(seconds=(TIME_DELTA*3600))).strftime("%d %b, %Y, %H:%M:%S")

        for i in range(0, len(tickers)):

            candlesticks = client.get_historical_klines(tickers[i], Client.KLINE_INTERVAL_1HOUR, debut, fin)

            closes = []
            new_closes = []
            rsi_array = []
            times = []
            rsi = 0
            laDate = ""

            counter = 0
            for candlestick in candlesticks:
                counter += 1
                closes.append(float(candlestick[4]))
                times.append(candlestick[0] / 1000)

            if counter > RSI_WARM_PERIOD:
                for j in range(0, len(closes)-1):
                    new_closes.append(closes[j])

                    prix_btc = closes[j]
                    laDate = datetime.datetime.fromtimestamp(times[j])

                    if(j > RSI_WARM_PERIOD):
                        np_closes = numpy.array(new_closes)
                        rsi_tab = talib.RSI(np_closes, timeperiod=14)
                        rsi = rsi_tab[-1]
                        rsi_array.append(rsi)
                        np_rsi = numpy.array(rsi_array)
        
                if rsi < RSI_MIN:
                    rsi_mini = numpy.array(np_rsi[-DIV_DELTA:]).min()
                    if rsi > rsi_mini:
                        prix_mini = numpy.array(np_closes[-DIV_DELTA:-1]).min()
                        if prix_btc < prix_mini:
                            message += "- ticker : " + tickers[i] + " - " 
                            print("DIV HAUSSIERE SUR {} - PRIX = {} - PRIX mini = {} - RSI = {} - Min = {} - date : {}".format(tickers[i], prix_btc, prix_mini, rsi, rsi_mini, laDate)) 

                if rsi > RSI_MAX:
                    rsi_maxi = numpy.array(np_rsi[-DIV_DELTA:]).max()
                    if rsi < rsi_maxi:
                        prix_maxi = numpy.array(np_closes[-DIV_DELTA:-1]).max()
                        if prix_btc > prix_maxi:
                            print("DIV BAISSIERE SUR {} - PRIX = {} - PRIX maxi = {} - RSI = {} - Max = {} - date : {}".format(tickers[i], prix_btc, prix_maxi, rsi, rsi_maxi, laDate))  

        print("fin : {}".format(datetime.datetime.now().strftime("%H:%M:%S")) )
        if message != "":
            message = ""

    time.sleep(30)