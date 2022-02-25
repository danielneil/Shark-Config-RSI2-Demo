#!/usr/bin/python3.9

from pyalgotrade import strategy
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.stratanalyzer import drawdown
from pyalgotrade.stratanalyzer import trades
from pyalgotrade import plotter
from pyalgotrade import plotter

import argparse
import sys
import os
import time

import pandas as pd
import json

def GenerateJSONReport(strat, retAnalyzer, sharpeRatioAnalyzer, drawDownAnalyzer, tradesAnalyzer, plot, ticker, capital, dataFile):

    plotFileName = "/shark/reports/" + ticker + ".png"
    plot.savePlot(plotFileName)
    
    jsonBacktestSummary = "/shark/reports/" + ticker + ".backtest.summary.json"          
    with open(jsonBacktestSummary, 'w', encoding='utf-8') as f:

        sharpeRatio = sharpeRatioAnalyzer.getSharpeRatio(0.05)

        json_obj = {}
        json_obj['backtest_summary'] = []

        json_obj['backtest_summary'].append({
            'ticker': ticker,
            'starting_capital': capital,
            'final_portfolio_value': "{:.2f}".format(strat.getResult()),
            'cumulative_returns': "{:.2f}".format((retAnalyzer.getCumulativeReturns()[-1] * 100)),
            'sharpe_ratio': "{:.2f}".format(sharpeRatio),
            'max_drawdown': "{:.2f}".format((drawDownAnalyzer.getMaxDrawDown() * 100)),
            'longest_drawdown_duration': str(drawDownAnalyzer.getLongestDrawDownDuration()),
            'total_trades': str(tradesAnalyzer.getCount()), 
            'wins': str(tradesAnalyzer.getProfitableCount()),
            'losses': str(tradesAnalyzer.getUnprofitableCount())
            })

        json.dump(json_obj, f)

    jsonBacktestTotalTrades = "/shark/reports/" + ticker + ".backtest.totaltrades.json"
    with open(jsonBacktestTotalTrades, 'w', encoding='utf-8') as f:

        if tradesAnalyzer.getCount() > 0:

            profits = tradesAnalyzer.getAll()          
            returns = tradesAnalyzer.getAllReturns()

            json_obj = {}
            json_obj['total_trades'] = []

            json_obj['total_trades'].append({
                'avg_profit': "{:.2f}".format(profits.mean()),
                'profits_std_dev': "{:.2f}".format(profits.std()),
                'max_profit': "{:.2f}".format(profits.max()),
                'min_profit': "{:.2f}".format(profits.min()),
                'avg_return': "{:.2f}".format((returns.mean() * 100)),
                'returns_std_dev': "{:.2f}".format((returns.std() * 100)),
                'max_return': "{:.2f}".format((returns.max() * 100)),
                'min_return': "{:.2f}".format((returns.min() * 100))
                })

            json.dump(json_obj, f)

    jsonBacktestProfitableTrades = "/shark/reports/" + ticker + ".backtest.profitabletrades.json"
    with open(jsonBacktestProfitableTrades, 'w', encoding='utf-8') as f:

        if tradesAnalyzer.getProfitableCount() > 0:

            profits = tradesAnalyzer.getProfits()
            returns = tradesAnalyzer.getPositiveReturns()

            json_obj = {}
            json_obj['profitable_trades'] = []

            json_obj['profitable_trades'].append({
                'avg_profit':  "{:.2f}".format(profits.mean()),
                'profits_std_dev': "{:.2f}".format(profits.std()), 
                'max_profit': "{:.2f}".format(profits.max()),
                'min_profit': "{:.2f}".format(profits.min()),
                'avg_return': "{:.2f}".format((returns.mean() * 100)),
                'returns_std_dev': "{:.2f}".format((returns.std() * 100)),
                'max_return': "{:.2f}".format((returns.max() * 100)),
                'min_return': "{:.2f}".format((returns.min() * 100))
                })

            json.dump(json_obj, f)

    jsonBacktestUnprofitableTrades = "/shark/reports/" + ticker + ".backtest.unprofitabletrades.json"
    with open(jsonBacktestUnprofitableTrades, 'w', encoding='utf-8') as f:

        if tradesAnalyzer.getUnprofitableCount() > 0:
            
            losses = tradesAnalyzer.getLosses()
            returns = tradesAnalyzer.getNegativeReturns()

            json_obj = {}
            json_obj['unprofitable_trades'] = []

            json_obj['unprofitable_trades'].append({
                'avg_loss': "{:.2f}".format(losses.mean()),
                'losses_std_dev': "{:.2f}".format(losses.std()),
                'max_loss': "{:.2f}".format(losses.min()),
                'min_loss': "{:.2f}".format(losses.max()),
                'avg_return': "{:.2f}".format((returns.mean() * 100)),
                'returns_std_dev': "{:.2f}".format((returns.std() * 100)),
                'max_return': "{:.2f}".format((returns.max() * 100)),
                'min_return': "{:.2f}".format((returns.min() * 100))
                })

            json.dump(json_obj, f)
            
    dataFrameInfo = "/shark/reports/" + ticker + ".backtest.dataFrameInfo.json"
    with open(dataFrameInfo, 'w', encoding='utf-8') as f:
            
        df = pd.read_csv(dataFile)

        json_obj = {}
        json_obj['dataframe_info'] = []
        
        json_obj['dataframe_info'].append({
                'rows': df.shape[0],
                'frequency': "Daily",
                'start_date': df['Date'].iloc[0],
                'end_date': df['Date'].iloc[-1],
                'adjusted_close': "true",
                'provider': "yahoo_finance"
                })
        
        json.dump(json_obj, f)        
