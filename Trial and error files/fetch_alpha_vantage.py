#!/usr/bin/env python3
"""
Singapore Stocks Historical Data Retrieval using Alpha Vantage API
Uses Alpha Vantage instead of Yahoo Finance to avoid rate limiting issues
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import logging
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('alpha_vantage_retrieval.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Your Alpha Vantage API Key
API_KEY = "14DK6NQ0JQ3ER2EN"
BASE_URL = "https://www.alphavantage.co/query"

class AlphaVantageStockFetcher:
    """Fetcher for Singapore stocks using Alpha Vantage API"""
    
    def __init__(self, api_key=API_KEY):
        self.api_key = api_key
        self.tickers = self.load_config()
        self.data = {}
        
    def load_config(self):
        """Load stock tickers from config"""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            return config['tickers']
        except:
            # Default tickers if config not found
            return [
                "D05.SI",  # DBS
                "O39.SI",  # OCBC
                "U11.SI",  # UOB
                "C38U.SI", # CapitaLand
                "Z74.SI"   # Singtel
            ]
    
    def fetch_daily_data(self, ticker, outputsize='full'):
        """Fetch daily data for a single stock from Alpha Vantage"""
        
        logger.info(f"Fetching {ticker} from Alpha Vantage...")
        
        # For Singapore stocks, we need to specify the exchange
        # Alpha Vantage format for Singapore Exchange is ticker.SGX or ticker.SI
        symbol = ticker
        
        # API parameters
        params = {
            'function': 'TIME_SERIES_DAILY_ADJUSTED',
            'symbol': symbol,
            'apikey': self.api_key,
            'outputsize': outputsize,  # 'full' for 20+ years, 'compact' for 100 days
            'datatype': 'json'
        }
        
        try:
            # Make API request
            response = requests.get(BASE_URL, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for error messages
                if 'Error Message' in data:
                    logger.error(f"API Error for {ticker}: {data['Error Message']}")
                    return None
                
                if 'Note' in data:
                    logger.warning(f"API Note: {data['Note']}")
                    logger.info("Reached API call limit (5 calls/min for free tier). Waiting...")
                    return None
                
                # Extract time series data
                if 'Time Series (Daily)' in data:
                    time_series = data['Time Series (Daily)']
                    
                    # Convert to DataFrame
                    df = pd.DataFrame.from_dict(time_series, orient='index')
                    df.index = pd.to_datetime(df.index)
                    df = df.sort_index()
                    
                    # Rename columns
                    df.columns = ['Open', 'High', 'Low', 'Close', 'Adjusted Close', 
                                  'Volume', 'Dividend', 'Split Coefficient']
                    
                    # Convert to numeric
                    for col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    # Add calculated fields
                    df['Daily Return (%)'] = df['Adjusted Close'].pct_change() * 100
                    df['MA_20'] = df['Adjusted Close'].rolling(window=20).mean()
                    df['MA_50'] = df['Adjusted Close'].rolling(window=50).mean()
                    df['MA_200'] = df['Adjusted Close'].rolling(window=200).mean()
                    df['Volatility (20D)'] = df['Daily Return (%)'].rolling(window=20).std()
                    
                    # Filter to last 5 years
                    five_years_ago = datetime.now() - timedelta(days=365*5)
                    df = df[df.index >= five_years_ago]
                    
                    logger.info(f"Successfully fetched {len(df)} records for {ticker}")
                    return df
                else:
                    logger.warning(f"No time series data found for {ticker}")
                    logger.debug(f"Response: {data}")
                    return None
            else:
                logger.error(f"HTTP Error {response.status_code} for {ticker}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching {ticker}: {str(e)}")
            return None
    
    def fetch_all_stocks(self):
        """Fetch all stocks with rate limit handling"""
        
        logger.info("=" * 60)
        logger.info("Starting Alpha Vantage data retrieval")
        logger.info(f"API Key: {self.api_key[:4]}...{self.api_key[-4:]}")
        logger.info(f"Fetching {len(self.tickers)} stocks")
        logger.info("Note: Free tier allows 5 API calls per minute")
        logger.info("=" * 60)
        
        successful = []
        failed = []
        
        for i, ticker in enumerate(self.tickers):
            logger.info(f"\nProcessing {i+1}/{len(self.tickers)}: {ticker}")
            
            # Alpha Vantage free tier: 5 calls per minute
            # So we need to wait 12 seconds between calls
            if i > 0:
                wait_time = 13  # 13 seconds to be safe
                logger.info(f"Waiting {wait_time} seconds (API rate limit)...")
                time.sleep(wait_time)
            
            # Fetch the data
            df = self.fetch_daily_data(ticker, outputsize='compact')  # Start with compact (100 days)
            
            if df is not None and not df.empty:
                self.data[ticker] = df
                successful.append(ticker)
                logger.info(f"✓ Successfully retrieved {ticker}")
            else:
                # Try alternative ticker format
                alt_ticker = ticker.replace('.SI', '.SGX')
                logger.info(f"Trying alternative format: {alt_ticker}")
                
                if i > 0:
                    time.sleep(13)
                
                df = self.fetch_daily_data(alt_ticker, outputsize='compact')
                
                if df is not None and not df.empty:
                    self.data[ticker] = df
                    successful.append(ticker)
                    logger.info(f"✓ Successfully retrieved {ticker} (as {alt_ticker})")
                else:
                    failed.append(ticker)
                    logger.warning(f"✗ Failed to retrieve {ticker}")
        
        # Summary
        logger.info("=" * 60)
        logger.info(f"Retrieval complete: {len(successful)}/{len(self.tickers)} successful")
        if successful:
            logger.info(f"Successful: {', '.join(successful)}")
        if failed:
            logger.info(f"Failed: {', '.join(failed)}")
            logger.info("\nNote: Some Singapore stocks may not be available on Alpha Vantage")
            logger.info("Consider using US-listed Singapore ETFs as alternatives (e.g., EWS)")
        
        return self.data
    
    def export_to_excel(self, filename='singapore_stocks_alpha_vantage.xlsx'):
        """Export fetched data to Excel"""
        
        if not self.data:
            logger.error("No data to export")
            return False
        
        try:
            from excel_exporter import ExcelExporter
            
            # Convert DataFrames to the format expected by ExcelExporter
            formatted_data = {}
            for ticker, df in self.data.items():
                if not df.empty:
                    # Reset index to have Date as a column
                    df_copy = df.copy()
                    df_copy.reset_index(inplace=True)
                    df_copy.rename(columns={'index': 'Date'}, inplace=True)
                    formatted_data[ticker] = df_copy
            
            if formatted_data:
                exporter = ExcelExporter(formatted_data, filename)
                exporter.export()
                logger.info(f"Data exported to: {filename}")
                return True
        except Exception as e:
            logger.error(f"Error exporting to Excel: {str(e)}")
            
            # Fallback: Simple Excel export
            logger.info("Using simple Excel export...")
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                for ticker, df in self.data.items():
                    if not df.empty:
                        sheet_name = ticker.replace('.', '_')
                        df.to_excel(writer, sheet_name=sheet_name)
                        logger.info(f"Saved {ticker} to Excel")
            
            logger.info(f"Data exported to: {filename}")
            return True
        
        return False


def main():
    """Main execution function"""
    
    try:
        # Initialize fetcher
        fetcher = AlphaVantageStockFetcher(api_key=API_KEY)
        
        # Check if we should fetch specific ticker
        if len(sys.argv) > 1:
            ticker = sys.argv[1]
            logger.info(f"Fetching single stock: {ticker}")
            df = fetcher.fetch_daily_data(ticker)
            if df is not None:
                fetcher.data[ticker] = df
        else:
            # Fetch all stocks
            fetcher.fetch_all_stocks()
        
        # Export to Excel
        if fetcher.data:
            success = fetcher.export_to_excel()
            
            if success:
                print("\n" + "=" * 60)
                print("SUCCESS!")
                print("=" * 60)
                print(f"Data saved to: singapore_stocks_alpha_vantage.xlsx")
                print(f"Stocks retrieved: {len(fetcher.data)}")
                print("\nNote: Alpha Vantage may have limited data for Singapore stocks.")
                print("If some stocks failed, they may not be available on this API.")
                return True
        else:
            print("\nNo data retrieved. Please check:")
            print("1. Your API key is valid")
            print("2. You haven't exceeded the daily limit (500 requests)")
            print("3. The ticker symbols are supported by Alpha Vantage")
            return False
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
