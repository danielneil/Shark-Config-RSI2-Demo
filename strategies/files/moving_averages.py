#!/usr/bin/python

import argparse
import Shark
import sys

cmd_arg_help = "Strategy: Moving Average Cross Over. Alert when the share price goes above/below the specified simple moving average period."

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description=cmd_arg_help)
    parser.add_argument("-t", "--ticker", help="Ticker of the stock to run the strategy against.")
    parser.add_argument("-s", "--sma", help="Simple Moving Averages Period.")
    args = parser.parse_args()

    if not args.ticker:
        print ("UNKNOWN - No ticker specified")
        sys.exit(UNKNOWN)

    if not args.sma:
        print ("UNKNOWN - No sma specified")
        sys.exit(UNKNOWN)    
        
    ticker = args.ticker 
    sma_period = args.sma

    sma = Shark.Plugins.GetSMA(ticker, sma_period)
    price = Shark.Plugins.GetPrice(ticker)
    
    if price > sma:

       alert_str = "BUY - Price $" + str(price) + " is above SMA(" + str(sma) + ")"
       print(alert_str)
       sys.exit(CRITICAL)
   
    else:
       
       alert_str = "SELL - Price $" + str(price) + " is below SMA(" + str(sma) + ")"
       print(alert_str)
       sys.exit(CRITICAL)
