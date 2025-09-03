#!/usr/bin/env python3
"""
Singapore Stocks Historical Data Retrieval - Real Data Version
Enhanced with better rate limit handling and alternative approaches
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import json
import time
import warnings
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('real_data_retrieval.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class RealStockDataFetcher:
    """Fetcher optimized for real data with better rate limit handling"""
    
    def __init__(self, config_file='config.json'):
        """Initialize the fetcher"""
        self.config = self.load_config(config_file)
        self.tickers = self.config['tickers']
        self.ticker_names = self.config.get('ticker_names', {})
        # Reduce the time range to minimize data and avoid rate limits
        self.start_date = (datetime.now() - timedelta(days=365*2)).strftime('%Y-%m-%d')  # 2 years instead of 5
        self.end_date = datetime.now().strftime('%Y-%m-%d')
        self.data = {}
        
    def load_config(self, config_file):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_file}")
            return config
        except FileNotFoundError:
            logger.error(f"Configuration file {config_file} not found")
            return self.get_default_config()
    
    def get_default_config(self):
        """Return default configuration"""
        return {
            "tickers": ["D05.SI", "O39.SI", "U11.SI"],  # Start with just 3 stocks
            "ticker_names": {
                "D05.SI": "DBS Group Holdings",
                "O39.SI": "OCBC Bank",
                "U11.SI": "UOB"
            },
            "output_file": "singapore_stocks_real_data.xlsx"
        }
    
    def fetch_single_stock(self, ticker, retry_count=3):
        """Fetch data for a single stock with enhanced retry logic"""
        
        for attempt in range(retry_count):
            try:
                logger.info(f"Fetching {ticker} (Attempt {attempt + 1}/{retry_count})...")
                
                # Longer delay between retries
                if attempt > 0:
                    wait_time = 30 * (2 ** attempt)  # Exponential backoff: 30s, 60s, 120s
                    logger.info(f"Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                
                # Method 1: Try using download function with different parameters
                logger.info(f"Trying bulk download method for {ticker}...")
                data = yf.download(
                    ticker, 
                    start=self.start_date, 
                    end=self.end_date,
                    progress=False,
                    show_errors=False,
                    threads=False,  # Single thread to avoid rate limits
                    timeout=30
                )
                
                if not data.empty:
                    logger.info(f"Successfully downloaded {len(data)} records for {ticker}")
                    return self.process_downloaded_data(data, ticker)
                
                # Method 2: Try Ticker object with smaller chunks
                logger.info(f"Trying Ticker object method for {ticker}...")
                time.sleep(5)  # Small delay before trying alternative method
                
                stock = yf.Ticker(ticker)
                data = stock.history(
                    start=self.start_date,
                    end=self.end_date,
                    interval="1d",
                    prepost=False,
                    actions=False,
                    auto_adjust=True,
                    back_adjust=False
                )
                
                if not data.empty:
                    logger.info(f"Successfully fetched {len(data)} records for {ticker}")
                    return self.process_ticker_data(data, ticker)
                
                logger.warning(f"No data retrieved for {ticker} on attempt {attempt + 1}")
                
            except Exception as e:
                error_msg = str(e)
                if "rate limit" in error_msg.lower() or "429" in error_msg:
                    logger.warning(f"Rate limited for {ticker}. Attempt {attempt + 1}/{retry_count}")
                else:
                    logger.error(f"Error fetching {ticker}: {error_msg}")
        
        logger.error(f"Failed to fetch data for {ticker} after {retry_count} attempts")
        return None
    
    def process_downloaded_data(self, data, ticker):
        """Process data from yf.download()"""
        df = pd.DataFrame()
        
        # Handle multi-level columns from download
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
        
        df['Date'] = data.index.date
        df['Open'] = data['Open'].values if 'Open' in data else None
        df['High'] = data['High'].values if 'High' in data else None
        df['Low'] = data['Low'].values if 'Low' in data else None
        df['Close'] = data['Close'].values if 'Close' in data else None
        df['Adjusted Close'] = data['Adj Close'].values if 'Adj Close' in data else data['Close'].values
        df['Volume'] = data['Volume'].values if 'Volume' in data else None
        
        # Calculate additional metrics
        df['Daily Return (%)'] = df['Adjusted Close'].pct_change() * 100
        df['MA_20'] = df['Adjusted Close'].rolling(window=20).mean()
        df['MA_50'] = df['Adjusted Close'].rolling(window=50).mean()
        df['MA_200'] = df['Adjusted Close'].rolling(window=200).mean()
        df['Volatility (20D)'] = df['Daily Return (%)'].rolling(window=20).std()
        
        return df
    
    def process_ticker_data(self, data, ticker):
        """Process data from Ticker.history()"""
        df = pd.DataFrame()
        
        df['Date'] = data.index.date
        df['Open'] = data['Open'].values
        df['High'] = data['High'].values
        df['Low'] = data['Low'].values
        df['Close'] = data['Close'].values
        df['Adjusted Close'] = data['Close'].values  # history() returns adjusted by default
        df['Volume'] = data['Volume'].values
        
        # Calculate additional metrics
        df['Daily Return (%)'] = df['Adjusted Close'].pct_change() * 100
        df['MA_20'] = df['Adjusted Close'].rolling(window=20).mean()
        df['MA_50'] = df['Adjusted Close'].rolling(window=50).mean()
        df['MA_200'] = df['Adjusted Close'].rolling(window=200).mean()
        df['Volatility (20D)'] = df['Daily Return (%)'].rolling(window=20).std()
        
        return df
    
    def fetch_all_stocks_sequential(self):
        """Fetch stocks one by one with long delays"""
        logger.info("=" * 60)
        logger.info(f"Starting REAL data retrieval for {len(self.tickers)} stocks")
        logger.info(f"Date range: {self.start_date} to {self.end_date}")
        logger.info("Using conservative approach with long delays...")
        logger.info("=" * 60)
        
        successful = []
        failed = []
        
        for i, ticker in enumerate(self.tickers):
            logger.info(f"\nProcessing stock {i+1}/{len(self.tickers)}: {ticker}")
            
            # Long delay between different stocks (except for first one)
            if i > 0:
                wait_time = 60  # 1 minute between stocks
                logger.info(f"Waiting {wait_time} seconds before next stock...")
                time.sleep(wait_time)
            
            # Fetch the stock data
            data = self.fetch_single_stock(ticker)
            
            if data is not None and not data.empty:
                self.data[ticker] = data
                successful.append(ticker)
                logger.info(f"✓ Successfully retrieved {ticker}")
            else:
                failed.append(ticker)
                logger.error(f"✗ Failed to retrieve {ticker}")
                # Create placeholder
                self.data[ticker] = pd.DataFrame({
                    'Status': ['Data retrieval failed - API rate limit reached']
                })
        
        # Summary
        logger.info("=" * 60)
        logger.info(f"Retrieval complete: {len(successful)}/{len(self.tickers)} successful")
        if successful:
            logger.info(f"Successful: {', '.join(successful)}")
        if failed:
            logger.info(f"Failed: {', '.join(failed)}")
        
        return self.data
    
    def fetch_batch_download(self):
        """Alternative: Try downloading all stocks at once"""
        logger.info("Attempting batch download of all stocks...")
        
        try:
            # Download all tickers at once
            data = yf.download(
                tickers=' '.join(self.tickers),
                start=self.start_date,
                end=self.end_date,
                group_by='ticker',
                threads=False,
                progress=False
            )
            
            if not data.empty:
                logger.info(f"Batch download successful! Processing data...")
                
                # Process each ticker's data
                for ticker in self.tickers:
                    try:
                        if len(self.tickers) == 1:
                            ticker_data = data
                        else:
                            ticker_data = data[ticker] if ticker in data.columns.levels[0] else None
                        
                        if ticker_data is not None and not ticker_data.empty:
                            self.data[ticker] = self.process_downloaded_data(ticker_data, ticker)
                            logger.info(f"Processed {ticker}: {len(self.data[ticker])} records")
                    except Exception as e:
                        logger.error(f"Error processing {ticker}: {str(e)}")
                        self.data[ticker] = pd.DataFrame({'Status': ['Processing error']})
                
                return self.data
            
        except Exception as e:
            logger.error(f"Batch download failed: {str(e)}")
            return None


def main():
    """Main execution function"""
    logger.info("Singapore Stocks REAL Data Retrieval")
    logger.info("=" * 60)
    
    try:
        # Parse command line arguments
        use_batch = '--batch' in sys.argv
        
        # Initialize fetcher
        fetcher = RealStockDataFetcher()
        
        # Choose method
        if use_batch:
            logger.info("Using BATCH download method...")
            stock_data = fetcher.fetch_batch_download()
            if not stock_data:
                logger.info("Batch failed, trying sequential...")
                stock_data = fetcher.fetch_all_stocks_sequential()
        else:
            logger.info("Using SEQUENTIAL download method (recommended)...")
            stock_data = fetcher.fetch_all_stocks_sequential()
        
        # Export to Excel
        if stock_data and any(not df.empty for df in stock_data.values()):
            from excel_exporter import ExcelExporter
            output_file = 'singapore_stocks_real_data.xlsx'
            exporter = ExcelExporter(stock_data, output_file)
            output_file = exporter.export()
            
            logger.info(f"Data exported to: {output_file}")
            logger.info("Process completed!")
            
            # Print summary
            print("\n" + "=" * 60)
            print("SUMMARY")
            print("=" * 60)
            print(f"Output file: {output_file}")
            print(f"Stocks processed: {len(stock_data)}")
            
            successful = sum(1 for df in stock_data.values() if not df.empty and 'Status' not in df.columns)
            print(f"Successful downloads: {successful}/{len(stock_data)}")
            
            print("\nTips for better results:")
            print("1. Run during off-peak hours (early morning or late night)")
            print("2. Use a VPN to change IP if rate limited")
            print("3. Try the --batch flag for batch download")
            print("4. Reduce the number of stocks in config.json")
            print("5. Wait a few hours between attempts")
        else:
            logger.error("No data retrieved. Please try again later.")
            
        return True
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
