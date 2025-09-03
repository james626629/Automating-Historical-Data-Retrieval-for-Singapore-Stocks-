#!/usr/bin/env python3
"""
Batch download approach - sometimes works when individual downloads fail
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import sys

def main():
    # All tickers in one string
    tickers = "D05.SI O39.SI U11.SI C38U.SI Z74.SI Y92.SI C52.SI BN4.SI 9CI.SI U96.SI"
    
    # Date range - 1 year
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    print("=" * 60)
    print("Singapore Stocks - Batch Download")
    print("=" * 60)
    print(f"Tickers: {tickers}")
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print("=" * 60)
    
    print("\nAttempting batch download of all stocks at once...")
    print("This sometimes works even when individual downloads fail.\n")
    
    try:
        # Download all at once
        data = yf.download(
            tickers=tickers,
            start=start_date,
            end=end_date,
            group_by='ticker',
            progress=True  # Show progress bar
        )
        
        if not data.empty:
            print(f"\nSuccess! Downloaded data with shape: {data.shape}")
            
            # Save to Excel
            filename = 'singapore_stocks_batch.xlsx'
            
            # Check if it's multi-level columns (multiple tickers)
            if isinstance(data.columns, pd.MultiIndex):
                # Multiple tickers - save each to separate sheet
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    ticker_list = tickers.split()
                    for ticker in ticker_list:
                        try:
                            if ticker in data.columns.levels[0]:
                                ticker_data = data[ticker]
                                sheet_name = ticker.replace('.', '_')
                                ticker_data.to_excel(writer, sheet_name=sheet_name)
                                print(f"Saved {ticker}")
                        except:
                            print(f"Could not save {ticker}")
            else:
                # Single ticker or combined data
                data.to_excel(filename, sheet_name='All_Stocks')
                print("Saved combined data")
            
            print(f"\nData saved to: {filename}")
            print("\nNote: Check the Excel file to see which stocks were successfully downloaded.")
            return True
        else:
            print("No data retrieved.")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        
        # Try alternative: download one by one in a batch call
        print("\nTrying alternative batch method...")
        ticker_list = tickers.split()
        
        successful = []
        for ticker in ticker_list:
            try:
                print(f"Trying {ticker}...", end=" ")
                data = yf.Ticker(ticker).history(period="1y")
                if not data.empty:
                    print(f"Success! {len(data)} records")
                    successful.append((ticker, data))
                else:
                    print("No data")
            except Exception as e:
                print(f"Failed: {e}")
        
        if successful:
            # Save what we got
            filename = 'singapore_stocks_partial.xlsx'
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                for ticker, data in successful:
                    sheet_name = ticker.replace('.', '_')
                    data.to_excel(writer, sheet_name=sheet_name)
            
            print(f"\nPartial data saved to: {filename}")
            print(f"Successfully retrieved: {len(successful)}/{len(ticker_list)} stocks")
            return True
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
