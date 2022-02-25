#!/usr/bin/python3.9

# Based on https://www.investopedia.com/articles/trading/07/bollinger.asp

from __future__ import print_function

from pyalgotrade import strategy
from pyalgotrade.barfeed import yahoofeed

from pyalgotrade.technical import bollinger

from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.stratanalyzer import drawdown
from pyalgotrade.stratanalyzer import trades
from pyalgotrade import plotter
import pyalgotrade

from pyalgotrade import broker as basebroker

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

strategy_name = "from pyalgotrade.technical import bollinger"

class BBands(strategy.BacktestingStrategy):

    def __init__(self, feed, instrument, shares, capital, dataFile, bandsPeriod):
        super(BBands, self).__init__(feed)
        self.__instrument = instrument
        self.__bbands = bollinger.BollingerBands(feed[instrument].getCloseDataSeries(), bandsPeriod, 2)
        self.setDebugMode(False)


    def getBollingerBands(self):
        return self.__bbands

    def onOrderUpdated(self, order):
        if order.isBuy():
            orderType = "Buy"
        else:
            orderType = "Sell"

    def onBars(self, bars):
        lower = self.__bbands.getLowerBand()[-1]
        upper = self.__bbands.getUpperBand()[-1]
        if lower is None:
            return

        shares = self.getBroker().getShares(self.__instrument)
        bar = bars[self.__instrument]
        if shares == 0 and bar.getClose() < lower:
            sharesToBuy = int(self.getBroker().getCash(False) / bar.getClose())
            self.marketOrder(self.__instrument, sharesToBuy)
        elif shares > 0 and bar.getClose() > upper:
            self.marketOrder(self.__instrument, -1*shares)


def run_strategy(ticker, shares, capital, dataFile, bandsPeriod):

    # Load the bar feed from the CSV file
    feed = yahoofeed.Feed()
    feed.addBarsFromCSV(ticker, dataFile)

    # Evaluate the strategy with the feed.
    strat = BBands(feed, ticker, shares, capital, dataFile, bandsPeriod)
    
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
    plt = plotter.StrategyPlotter(strat, True, True, True)
    plt.getInstrumentSubplot(ticker).addDataSeries("upper", strat.getBollingerBands().getUpperBand())
    plt.getInstrumentSubplot(ticker).addDataSeries("middle", strat.getBollingerBands().getMiddleBand())
    plt.getInstrumentSubplot(ticker).addDataSeries("lower", strat.getBollingerBands().getLowerBand())

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
    parser.add_argument("-b", "--bandsPeriod", help="The sma period that we will use as the basis for entry into a trade")

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

    if not args.bandsPeriod:
        print("UNKNOWN - No bandsPeriod specified")
        sys.exit(UNKNOWN)

        
    ticker = args.ticker 
    shares = int(args.shares)
    capital = int(args.capital)
    data_format = args.data_format

    # BBands Specific args.
    bandsPeriod = int(args.bandsPeriod)
    
    dataFile = ""
    if data_format == "yahoo_finance_data":

        dataFile = "/shark/historical/yahoo_finance_data/" + ticker + ".csv"
        
    run_strategy(ticker, shares, capital, dataFile, bandsPeriod)
