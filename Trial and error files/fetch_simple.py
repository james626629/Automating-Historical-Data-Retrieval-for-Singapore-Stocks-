#!/usr/bin/env python3
"""
Simple script to fetch Singapore stock data - one at a time
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import sys

def fetch_stock(ticker, start_date, end_date):
    """Simple fetch for a single stock"""
    print(f"\nFetching {ticker}...")
    try:
        # Simple download - no extra parameters
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        
        if not data.empty:
            print(f"Success! Got {len(data)} records for {ticker}")
            return data
        else:
            print(f"No data for {ticker}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    # Configuration
    tickers = [
        "D05.SI",  # DBS
        "O39.SI",  # OCBC
        "U11.SI",  # UOB
        "C38U.SI", # CapitaLand
        "Z74.SI"   # Singtel
    ]
    
    # Date range - just 1 year to reduce load
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    print("=" * 60)
    print("Singapore Stocks Data Fetcher - Simple Version")
    print("=" * 60)
    print(f"Fetching {len(tickers)} stocks")
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print("=" * 60)
    
    all_data = {}
    
    # Fetch one stock at a time with delay
    for i, ticker in enumerate(tickers):
        if i > 0:
            wait = 30  # 30 second delay between stocks
            print(f"\nWaiting {wait} seconds before next stock...")
            time.sleep(wait)
        
        data = fetch_stock(ticker, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        if data is not None:
            all_data[ticker] = data
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Retrieved {len(all_data)} out of {len(tickers)} stocks")
    
    if all_data:
        # Save to Excel
        with pd.ExcelWriter('singapore_stocks_simple.xlsx', engine='openpyxl') as writer:
            for ticker, data in all_data.items():
                # Clean ticker name for sheet name
                sheet_name = ticker.replace('.', '_')
                data.to_excel(writer, sheet_name=sheet_name)
                print(f"Saved {ticker} to Excel")
        
        print(f"\nData saved to: singapore_stocks_simple.xlsx")
    else:
        print("No data retrieved.")
    
    return len(all_data) > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
