#!/usr/bin/python3.9

from __future__ import print_function

from pyalgotrade import strategy
from pyalgotrade.barfeed import yahoofeed

from pyalgotrade.technical import cross
from pyalgotrade.technical import ma
from pyalgotrade.technical import rsi

from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.stratanalyzer import drawdown
from pyalgotrade.stratanalyzer import trades
from pyalgotrade import plotter
import pyalgotrade

from _functions import GenerateJSONReport 

import argparse
import sys
import os

import time

import pandas as pd

# Nagios constants. 

OK           = 0
WARNING      = 1
CRITICAL     = 2
UNKNOWN      = 3

strategy_name = "RSI2"

class RSI2(strategy.BacktestingStrategy):

    def __init__(self, feed, instrument, shares, capital, dataFile, entrySMA, exitSMA, rsiPeriod, overSoldThreshold, overBoughtThreshold):

        super(RSI2, self).__init__(feed, capital)

        self.__position = None
        self.__instrument = instrument
        self.__prices = feed[instrument].getPriceDataSeries()

        # We'll use adjusted close values instead of regular close values.
        self.setUseAdjustedValues(True)

        self.__priceDS = feed[instrument].getPriceDataSeries()
        self.__entrySMA = ma.SMA(self.__priceDS, entrySMA)
        self.__exitSMA = ma.SMA(self.__priceDS, exitSMA)
        self.__rsi = rsi.RSI(self.__priceDS, rsiPeriod)
        self.__overBoughtThreshold = overBoughtThreshold
        self.__overSoldThreshold = overSoldThreshold
        self.__longPos = None
        self.__shortPos = None

        self.setDebugMode(False)


    def getEntrySMA(self):
        return self.__entrySMA

    def getExitSMA(self):
        return self.__exitSMA

    def getRSI(self):
        return self.__rsi

    def onEnterCanceled(self, position):
        if self.__longPos == position:
            self.__longPos = None
        elif self.__shortPos == position:
            self.__shortPos = None
        else:
            assert(False)

    def onExitOk(self, position):
        if self.__longPos == position:
            self.__longPos = None
        elif self.__shortPos == position:
            self.__shortPos = None
        else:
            assert(False)

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        position.exitMarket()

    def onBars(self, bars):
        # Wait for enough bars to be available to calculate SMA and RSI.
        if self.__exitSMA[-1] is None or self.__entrySMA[-1] is None or self.__rsi[-1] is None:
            return

        bar = bars[self.__instrument]
        if self.__longPos is not None:
            if self.exitLongSignal():
                self.__longPos.exitMarket()
        elif self.__shortPos is not None:
            if self.exitShortSignal():
                self.__shortPos.exitMarket()
        else:
            if self.enterLongSignal(bar):
                shares = int(self.getBroker().getCash() * 0.9 / bars[self.__instrument].getPrice())
                self.__longPos = self.enterLong(self.__instrument, shares, True)
            elif self.enterShortSignal(bar):
                shares = int(self.getBroker().getCash() * 0.9 / bars[self.__instrument].getPrice())
                self.__shortPos = self.enterShort(self.__instrument, shares, True)

    def enterLongSignal(self, bar):
        return bar.getPrice() > self.__entrySMA[-1] and self.__rsi[-1] <= self.__overSoldThreshold

    def exitLongSignal(self):
        return cross.cross_above(self.__priceDS, self.__exitSMA)

    def enterShortSignal(self, bar):
        return bar.getPrice() < self.__entrySMA[-1] and self.__rsi[-1] >= self.__overBoughtThreshold

    def exitShortSignal(self):
        return cross.cross_below(self.__priceDS, self.__exitSMA)

def run_strategy(ticker, shares, capital, dataFile, entrySMA, exitSMA, rsiPeriod, overSoldThreshold, overBoughtThreshold):

    # Load the bar feed from the CSV file
    feed = yahoofeed.Feed()
    feed.addBarsFromCSV(ticker, dataFile)

    # Evaluate the strategy with the feed.
    strat = RSI2(feed, ticker, shares, capital, dataFile, entrySMA, exitSMA, rsiPeriod, overSoldThreshold, overBoughtThreshold)
    
    # Attach  analyzers to the strategy before executing it.
    retAnalyzer = pyalgotrade.stratanalyzer.returns.Returns()
    strat.attachAnalyzer(retAnalyzer)

    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    strat.attachAnalyzer(sharpeRatioAnalyzer)
   
    drawDownAnalyzer = drawdown.DrawDown()
    strat.attachAnalyzer(drawDownAnalyzer)
    
    tradesAnalyzer = trades.Trades()
    strat.attachAnalyzer(tradesAnalyzer)

    # Attach the plotter
    plt = plotter.StrategyPlotter(strat, True, False, True)
    plt.getInstrumentSubplot(ticker).addDataSeries("Entry SMA", strat.getEntrySMA())
    plt.getInstrumentSubplot(ticker).addDataSeries("Exit SMA", strat.getExitSMA())
    plt.getOrCreateSubplot("rsi").addDataSeries("RSI", strat.getRSI())
    plt.getOrCreateSubplot("rsi").addLine("Overbought", overBoughtThreshold)
    plt.getOrCreateSubplot("rsi").addLine("Oversold", overSoldThreshold)

    # Run the strategy.
    strat.run()
    
    # Print out our findings.
    print("Sharpe Ratio: %.2f" % sharpeRatioAnalyzer.getSharpeRatio(0.05))

    # Generate the JSON report
    GenerateJSONReport(strat, retAnalyzer, sharpeRatioAnalyzer, drawDownAnalyzer, tradesAnalyzer, plt, ticker, capital, dataFile)
    
    if sharpeRatioAnalyzer.getSharpeRatio(0.05) > 0: 
       sys.exit(OK)
    else:
       sys.exit(CRITICAL)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    
    parser.add_argument("-t", "--ticker", help="Ticker of the stock to run the backtest against.")
    parser.add_argument("-s", "--shares", help="The number of imaginary shares to purchase.")
    parser.add_argument("-c", "--capital", help="The imaginary amount of capital available (in dollars).")
    parser.add_argument("-n", "--data_format", help="The provider of the historical data.")
    parser.add_argument("-e", "--entrySMA", help="The sma period that we will use as the basis for entry into a trade")
    parser.add_argument("-x", "--exitSMA", help="The sma period that we will use as the basis for exit from a trade")
    parser.add_argument("-r", "--rsiPeriod", help="The rsi period that we will use as the basis for the trade")
    parser.add_argument("-os", "--overSoldThreshold", help="The RSI indication that will be considered over sold.")
    parser.add_argument("-ob", "--overBoughtThreshold", help="The RSI indication that will be considered over bought.")

    args = parser.parse_args()

    if not args.ticker:
        print ("UNKNOWN - No ticker specified")
        sys.exit(UNKNOWN)

    if not args.shares:
        print("UNKNOWN - No shares specified")
        sys.exit(UNKNOWN)

    if not args.capital:
        print("UNKNOWN - No capital amount specified")
        sys.exit(UNKNOWN)

    if not args.data_format:
        print("UNKNOWN - No data_format specified")
        sys.exit(UNKNOWN)       

    if not args.entrySMA:
        print("UNKNOWN - No entrySMA specified")
        sys.exit(UNKNOWN)

    if not args.exitSMA:
        print("UNKNOWN - No exitSMA specified")
        sys.exit(UNKNOWN)

    if not args.rsiPeriod:
        print("UNKNOWN - No rsiPeriod specified")
        sys.exit(UNKNOWN)

    if not args.overSoldThreshold:
        print("UNKNOWN - No overSoldThreshold specified")
        sys.exit(UNKNOWN)

    if not args.overBoughtThreshold:
        print("UNKNOWN - No overBoughtThreshold specified")
        sys.exit(UNKNOWN)

        
    ticker = args.ticker 
    shares = int(args.shares)
    capital = int(args.capital)
    data_format = args.data_format

    # RSI 2 Specific args.
    entrySMA = int(args.entrySMA)
    exitSMA = int(args.exitSMA)
    rsiPeriod = int(args.rsiPeriod)
    overSoldThreshold = int(args.overSoldThreshold)
    overBoughtThreshold = int(args.overBoughtThreshold)
    
    dataFile = ""
    if data_format == "yahoo_finance_data":

        dataFile = "/shark/historical/yahoo_finance_data/" + ticker + ".csv"
        
    run_strategy(ticker, shares, capital, dataFile, entrySMA, exitSMA, rsiPeriod, overSoldThreshold, overBoughtThreshold)
