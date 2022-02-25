#!/usr/bin/python3.9

from __future__ import print_function

from pyalgotrade import strategy
from pyalgotrade.barfeed import yahoofeed

from pyalgotrade.technical import ma
from pyalgotrade.technical import cross

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

strategy_name = "Moving Averages Crossover Backtest"

class MovingAverages(strategy.BacktestingStrategy):

    def __init__(self, feed, instrument, shares, capital, smaPeriod, dataFile):

        super(MovingAverages, self).__init__(feed, capital)

        self.__position = None
        self.__instrument = instrument
        self.__prices = feed[instrument].getPriceDataSeries()

        # We'll use adjusted close values instead of regular close values.
        self.setUseAdjustedValues(True)

        self.__sma = ma.SMA(self.__prices, smaPeriod)
        
        self.setDebugMode(False)

    def getSMA(self):
        return self.__sma
        
    def onEnterOk(self, position):

        execInfo = position.getEntryOrder().getExecutionInfo()
        quantity = str(execInfo.getQuantity())

    def onEnterCanceled(self, position):
        self.__position = None

    def onExitOk(self, position):

        execInfo = position.getExitOrder().getExecutionInfo()
        quantity = str(execInfo.getQuantity())

        self.__position = None

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        self.__position.exitMarket()

    def onBars(self, bars):
        
        ###############################################################
        # START - THIS IS BASICALLY THE CRUX OF THE BACKTEST'S LOGIC
        
        # IF WE ARE NOT IN A POSITION
        # AND THE SHARE PRICE GOES ABOVE THE SMA(smaPeriod) - BUY.
        # IF WE ARE ALREADY IN A POSITION,
        # AND THE SHARE PRICE GOES BELOW THE SMA(smaPeriod) - SELL.
        
        # If a position was not opened, check if we should enter a long position.
        if self.__position is None:

            if cross.cross_above(self.__prices, self.__sma) > 0:

                # Enter a buy market order for n shares. The order is good till canceled.
                self.__position = self.enterLong(self.__instrument, shares, True)

        # Check if we have to exit the position.
        elif cross.cross_below(self.__prices, self.__sma) > 0 and not self.__position.exitActive():
            
            self.__position.exitMarket()
            
        # END - THIS IS BASICALLY THE CRUX OF THE BACKTEST'S LOGIC
        ###############################################################
        
def run_strategy(ticker, shares, capital, smaPeriod, dataFile):

    # Load the bar feed from the CSV file
    feed = yahoofeed.Feed()
    feed.addBarsFromCSV(ticker, dataFile)

    # Evaluate the strategy with the feed.
    strat = MovingAverages(feed, ticker, shares, capital, smaPeriod, dataFile)
    
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
    plot = plotter.StrategyPlotter(strat)

    plt = plotter.StrategyPlotter(strat, True, True, True)
    plt.getInstrumentSubplot(ticker).addDataSeries("sma", strat.getSMA())
    plt.getOrCreateSubplot("returns").addDataSeries("Simple returns", retAnalyzer.getReturns())
    
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
    parser.add_argument("-p", "--period", help="The sma period that we will use as the basis for the cross over threshold.")
    parser.add_argument("-n", "--data_format", help="The provider of the historical data.")
    
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

    if not args.period:
        print("UNKNOWN - No period specified")
        sys.exit(UNKNOWN)

    if not args.data_format:
        print("UNKNOWN - No data_format specified")
        sys.exit(UNKNOWN)       
        
    ticker = args.ticker 
    shares = int(args.shares)
    capital = int(args.capital)
    period = args.period
    data_format = args.data_format
    
    dataFile = ""
    if data_format == "yahoo_finance_data":
        dataFile = "/shark/historical/yahoo_finance_data/" + ticker + ".csv"
        
    run_strategy(ticker, int(shares), int(capital), int(period), dataFile)
