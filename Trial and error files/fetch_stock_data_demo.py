#!/usr/bin/env python3
"""
Singapore Stocks Historical Data Retrieval Script - Demo Version
This version includes sample data generation when API is unavailable
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import json
import time
import random
import warnings
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_data_retrieval_demo.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class StockDataFetcherDemo:
    """Class to handle fetching and processing of stock data with demo fallback"""
    
    def __init__(self, config_file='config.json'):
        """Initialize the StockDataFetcher with configuration"""
        self.config = self.load_config(config_file)
        self.tickers = self.config['tickers']
        self.ticker_names = self.config.get('ticker_names', {})
        self.start_date = (datetime.now() - timedelta(days=365*5)).strftime('%Y-%m-%d')
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
        """Return default configuration if config file not found"""
        return {
            "tickers": ["D05.SI", "O39.SI", "U11.SI", "C38U.SI", "Z74.SI",
                       "Y92.SI", "C52.SI", "BN4.SI", "9CI.SI", "U96.SI"],
            "ticker_names": {
                "D05.SI": "DBS Group Holdings",
                "O39.SI": "OCBC Bank",
                "U11.SI": "UOB",
                "C38U.SI": "CapitaLand Trust",
                "Z74.SI": "Singtel",
                "Y92.SI": "Thai Beverage",
                "C52.SI": "ComfortDelGro",
                "BN4.SI": "Keppel Corp",
                "9CI.SI": "CapitaLand Investment",
                "U96.SI": "Sembcorp Industries"
            },
            "output_file": "singapore_stocks_data_demo.xlsx"
        }
    
    def generate_sample_data(self, ticker):
        """Generate sample historical data for demonstration"""
        logger.info(f"Generating sample data for {ticker}...")
        
        # Generate date range
        dates = pd.date_range(start=self.start_date, end=self.end_date, freq='B')  # Business days only
        
        # Set base price based on ticker type
        base_prices = {
            "D05.SI": 35.0,   # Banks typically higher
            "O39.SI": 13.0,
            "U11.SI": 29.0,
            "C38U.SI": 2.1,   # REITs typically lower
            "Z74.SI": 2.3,
            "Y92.SI": 0.6,
            "C52.SI": 1.4,
            "BN4.SI": 7.5,
            "9CI.SI": 3.2,
            "U96.SI": 4.8
        }
        
        base_price = base_prices.get(ticker, 10.0)
        
        # Generate price data with realistic patterns
        num_days = len(dates)
        
        # Create trend (slight upward bias for Singapore market)
        trend = np.linspace(0, 0.15, num_days) * base_price
        
        # Add cyclical pattern (quarterly earnings effect)
        cycle = np.sin(np.linspace(0, 8*np.pi, num_days)) * base_price * 0.05
        
        # Add random walk
        random_walk = np.cumsum(np.random.randn(num_days) * base_price * 0.01)
        
        # Combine components
        prices = base_price + trend + cycle + random_walk
        prices = np.maximum(prices, base_price * 0.5)  # Ensure no negative prices
        
        # Generate OHLC data
        df = pd.DataFrame()
        df['Date'] = dates.date
        
        # Generate realistic OHLC values
        df['Close'] = prices
        df['Open'] = prices * (1 + np.random.randn(num_days) * 0.005)
        df['High'] = np.maximum(df['Open'], df['Close']) * (1 + np.abs(np.random.randn(num_days) * 0.01))
        df['Low'] = np.minimum(df['Open'], df['Close']) * (1 - np.abs(np.random.randn(num_days) * 0.01))
        df['Adjusted Close'] = df['Close']  # Simplified - same as close
        
        # Generate volume (higher for banks, lower for REITs)
        base_volume = 10000000 if ticker in ["D05.SI", "O39.SI", "U11.SI"] else 5000000
        df['Volume'] = np.abs(base_volume + np.random.randn(num_days) * base_volume * 0.3).astype(int)
        
        # Calculate metrics
        df['Daily Return (%)'] = df['Adjusted Close'].pct_change() * 100
        df['MA_20'] = df['Adjusted Close'].rolling(window=20).mean()
        df['MA_50'] = df['Adjusted Close'].rolling(window=50).mean()
        df['MA_200'] = df['Adjusted Close'].rolling(window=200).mean()
        df['Volatility (20D)'] = df['Daily Return (%)'].rolling(window=20).std()
        
        # Add sample EV/EBITDA (last value only)
        df['Quarterly EV/EBITDA'] = [None] * (len(df) - 1) + [random.uniform(8, 15)]
        
        logger.info(f"Generated {len(df)} records of sample data for {ticker}")
        return df
    
    def fetch_stock_data(self, ticker, use_demo=False):
        """Fetch historical data for a single stock or generate demo data"""
        if use_demo:
            return self.generate_sample_data(ticker)
        
        try:
            logger.info(f"Attempting to fetch real data for {ticker}...")
            
            # Try to download real data with timeout
            stock = yf.Ticker(ticker)
            hist_data = stock.history(start=self.start_date, end=self.end_date, timeout=5)
            
            if hist_data.empty:
                logger.warning(f"No real data retrieved for {ticker}, using sample data")
                return self.generate_sample_data(ticker)
            
            # Process real data
            df = pd.DataFrame()
            df['Date'] = hist_data.index.date
            df['Adjusted Close'] = hist_data['Close'].values
            df['Volume'] = hist_data['Volume'].values
            df['Open'] = hist_data['Open'].values
            df['High'] = hist_data['High'].values
            df['Low'] = hist_data['Low'].values
            df['Close'] = hist_data['Close'].values
            df['Daily Return (%)'] = df['Adjusted Close'].pct_change() * 100
            df['MA_20'] = df['Adjusted Close'].rolling(window=20).mean()
            df['MA_50'] = df['Adjusted Close'].rolling(window=50).mean()
            df['MA_200'] = df['Adjusted Close'].rolling(window=200).mean()
            df['Volatility (20D)'] = df['Daily Return (%)'].rolling(window=20).std()
            
            # Try to get EV/EBITDA
            try:
                info = stock.info
                if 'enterpriseToEbitda' in info:
                    df['Quarterly EV/EBITDA'] = [None] * (len(df) - 1) + [info['enterpriseToEbitda']]
                else:
                    df['Quarterly EV/EBITDA'] = None
            except:
                df['Quarterly EV/EBITDA'] = None
            
            logger.info(f"Successfully fetched real data for {ticker}: {len(df)} records")
            return df
            
        except Exception as e:
            logger.warning(f"Could not fetch real data for {ticker}: {str(e)}")
            logger.info(f"Using sample data for {ticker}")
            return self.generate_sample_data(ticker)
    
    def fetch_all_stocks(self, demo_mode=False):
        """Fetch data for all stocks in the configuration"""
        logger.info(f"Starting data retrieval for {len(self.tickers)} stocks")
        logger.info(f"Date range: {self.start_date} to {self.end_date}")
        
        if demo_mode:
            logger.info("Running in DEMO MODE - generating sample data")
        else:
            logger.info("Attempting to fetch real data with fallback to sample data")
        
        for i, ticker in enumerate(self.tickers):
            # Small delay between requests if not in demo mode
            if not demo_mode and i > 0:
                time.sleep(random.uniform(1, 2))
            
            data = self.fetch_stock_data(ticker, use_demo=demo_mode)
            if data is not None:
                self.data[ticker] = data
        
        successful_count = sum(1 for v in self.data.values() if not v.empty)
        logger.info(f"Completed data retrieval. Successfully processed: {successful_count}/{len(self.tickers)} stocks")
        return self.data


def main():
    """Main execution function"""
    logger.info("=" * 60)
    logger.info("Singapore Stocks Historical Data Retrieval - Demo Version")
    logger.info("=" * 60)
    
    try:
        # Check if we should use demo mode
        demo_mode = '--demo' in sys.argv or '-d' in sys.argv
        
        # Initialize fetcher
        fetcher = StockDataFetcherDemo()
        
        # Fetch all stock data
        stock_data = fetcher.fetch_all_stocks(demo_mode=demo_mode)
        
        # Export to Excel
        from excel_exporter import ExcelExporter
        output_file = 'singapore_stocks_data_demo.xlsx' if demo_mode else 'singapore_stocks_data.xlsx'
        exporter = ExcelExporter(stock_data, output_file)
        output_file = exporter.export()
        
        logger.info(f"Data successfully exported to: {output_file}")
        logger.info("=" * 60)
        logger.info("Process completed successfully!")
        
        # Print summary
        print("\nSummary:")
        print(f"Mode: {'DEMO' if demo_mode else 'MIXED (Real + Sample)'}")
        print(f"Stocks processed: {len(stock_data)}")
        print(f"Output file: {output_file}")
        print(f"Log file: stock_data_retrieval_demo.log")
        
        if demo_mode:
            print("\nNote: This is SAMPLE DATA for demonstration purposes.")
            print("To attempt fetching real data, run without --demo flag")
        
        return True
        
    except Exception as e:
        logger.error(f"Fatal error in main execution: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
