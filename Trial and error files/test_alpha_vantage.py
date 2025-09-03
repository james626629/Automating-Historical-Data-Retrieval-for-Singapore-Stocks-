#!/usr/bin/env python3
"""
Test Alpha Vantage API with US stocks and Singapore ETFs
Since Singapore stocks aren't available, we'll use alternatives
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import time
import sys

API_KEY = "14DK6NQ0JQ3ER2EN"
BASE_URL = "https://www.alphavantage.co/query"

def test_api_with_us_stock():
    """Test if API works with a US stock"""
    print("Testing Alpha Vantage API with Apple (AAPL)...")
    
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': 'AAPL',
        'apikey': API_KEY,
        'outputsize': 'compact'
    }
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        if 'Time Series (Daily)' in data:
            print("✓ API is working! Successfully fetched AAPL data")
            return True
        elif 'Error Message' in data:
            print(f"✗ API Error: {data['Error Message']}")
            return False
        elif 'Note' in data:
            print(f"API Note: {data['Note']}")
            print("You've reached the rate limit. Wait a minute and try again.")
            return False
        else:
            print("Unexpected response:", data)
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def fetch_singapore_alternatives():
    """Fetch alternatives that track Singapore market"""
    
    print("\n" + "=" * 60)
    print("Fetching Singapore Market Alternatives")
    print("=" * 60)
    
    # These are US-listed ETFs and ADRs that track Singapore companies
    alternatives = {
        'EWS': 'iShares MSCI Singapore ETF',
        'FLSG': 'Franklin FTSE Singapore ETF',
        'SE': 'Sea Limited (Singapore tech company)',
        'GRAB': 'Grab Holdings (Singapore company)',
        # Some Asian banks with Singapore exposure
        'DBS': 'DBS Group (if ADR available)',
    }
    
    successful_data = {}
    
    for symbol, name in alternatives.items():
        print(f"\nFetching {symbol} - {name}...")
        
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'apikey': API_KEY,
            'outputsize': 'compact'
        }
        
        try:
            response = requests.get(BASE_URL, params=params, timeout=10)
            data = response.json()
            
            if 'Time Series (Daily)' in data:
                time_series = data['Time Series (Daily)']
                df = pd.DataFrame.from_dict(time_series, orient='index')
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                
                # Rename columns
                df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                
                # Convert to numeric
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                successful_data[symbol] = df
                print(f"✓ Success! Got {len(df)} days of data")
            else:
                print(f"✗ No data available for {symbol}")
            
            # Wait to avoid rate limit (5 calls per minute for free tier)
            time.sleep(13)
            
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
    
    return successful_data

def save_to_excel(data_dict, filename='singapore_alternatives.xlsx'):
    """Save data to Excel"""
    if not data_dict:
        print("No data to save")
        return
    
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        for symbol, df in data_dict.items():
            df.to_excel(writer, sheet_name=symbol)
            print(f"Saved {symbol} to Excel")
    
    print(f"\nData saved to: {filename}")

def main():
    print("=" * 60)
    print("Alpha Vantage API Test & Singapore Alternatives")
    print("=" * 60)
    
    # First test if API works
    if test_api_with_us_stock():
        print("\n✓ Your API key is valid and working!")
        print("\nUnfortunately, Alpha Vantage doesn't support Singapore Exchange (SGX) stocks.")
        print("However, we can fetch US-listed ETFs that track the Singapore market.\n")
        
        response = input("Would you like to fetch Singapore ETF data instead? (y/n): ")
        
        if response.lower() == 'y':
            data = fetch_singapore_alternatives()
            if data:
                save_to_excel(data)
                print("\n" + "=" * 60)
                print("SUCCESS!")
                print("=" * 60)
                print("Downloaded US-listed Singapore ETFs and companies")
                print("\nNote: For actual Singapore stocks (D05.SI, O39.SI, etc.),")
                print("you'll need to use Yahoo Finance during off-peak hours or")
                print("consider a paid data provider like Bloomberg or Refinitiv.")
        else:
            print("\nFor Singapore stocks, you have these options:")
            print("1. Wait for Yahoo Finance rate limits to reset (few hours)")
            print("2. Use a VPN to change your IP address")
            print("3. Try early morning or late night when traffic is lower")
            print("4. Use the demo data generator for testing purposes")
            print("5. Consider paid APIs like Bloomberg, Refinitiv, or EOD Historical Data")
    else:
        print("\n✗ API key might be invalid or you've hit the daily limit (500 requests)")

if __name__ == "__main__":
    main()
