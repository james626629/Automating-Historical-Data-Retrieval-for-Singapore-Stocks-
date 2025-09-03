#!/usr/bin/env python3
"""
Singapore Stocks Historical Data Retrieval Script
Author: Galilee Internship Assignment
Date: September 2025
Description: Automates the retrieval of historical price data for Singapore-listed stocks
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import logging
import sys
from pathlib import Path
import json
import warnings
import time
import random
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_data_retrieval.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class StockDataFetcher:
    """Class to handle fetching and processing of stock data"""
    
    def __init__(self, config_file='config.json'):
        """Initialize the StockDataFetcher with configuration"""
        self.config = self.load_config(config_file)
        self.tickers = self.config['tickers']
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
            # Use default configuration
            return self.get_default_config()
    
    def get_default_config(self):
        """Return default configuration if config file not found"""
        return {
            "tickers": [
                "D05.SI",  # DBS Group
                "O39.SI",  # OCBC Bank
                "U11.SI",  # UOB
                "C38U.SI", # CapitaLand Integrated Commercial Trust
                "Z74.SI",  # Singtel
                "Y92.SI",  # Thai Beverage
                "C52.SI",  # ComfortDelGro
                "BN4.SI",  # Keppel Corp
                "9CI.SI",  # CapitaLand Investment
                "U96.SI"   # Sembcorp Industries
            ],
            "output_file": "singapore_stocks_data.xlsx"
        }
    
    def fetch_stock_data(self, ticker, retry_count=3):
        """Fetch historical data for a single stock with retry logic"""
        for attempt in range(retry_count):
            try:
                logger.info(f"Fetching data for {ticker}... (Attempt {attempt + 1}/{retry_count})")
                
                # Add delay to avoid rate limiting
                if attempt > 0:
                    delay = random.uniform(5, 10) * attempt  # Exponential backoff
                    logger.info(f"Waiting {delay:.1f} seconds before retry...")
                    time.sleep(delay)
                
                # Download stock data
                stock = yf.Ticker(ticker)
                hist_data = stock.history(start=self.start_date, end=self.end_date)
                
                if hist_data.empty:
                    logger.warning(f"No data retrieved for {ticker}")
                    return None
                
                # Process the data
                processed_data = self.process_stock_data(hist_data, stock)
                
                logger.info(f"Successfully fetched data for {ticker}: {len(processed_data)} records")
                return processed_data
                
            except Exception as e:
                error_msg = str(e)
                if "Rate limited" in error_msg or "Too Many Requests" in error_msg:
                    logger.warning(f"Rate limited for {ticker}. Attempt {attempt + 1}/{retry_count}")
                    if attempt < retry_count - 1:
                        continue
                logger.error(f"Error fetching data for {ticker}: {error_msg}")
                
        return None
    
    def process_stock_data(self, hist_data, stock):
        """Process raw stock data and calculate additional metrics"""
        # Create DataFrame with required columns
        df = pd.DataFrame()
        
        # Basic price and volume data
        df['Date'] = hist_data.index
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        df['Adjusted Close'] = hist_data['Close'].values
        df['Volume'] = hist_data['Volume'].values
        df['Open'] = hist_data['Open'].values
        df['High'] = hist_data['High'].values
        df['Low'] = hist_data['Low'].values
        df['Close'] = hist_data['Close'].values
        
        # Calculate daily returns
        df['Daily Return (%)'] = df['Adjusted Close'].pct_change() * 100
        
        # Calculate moving averages
        df['MA_20'] = df['Adjusted Close'].rolling(window=20).mean()
        df['MA_50'] = df['Adjusted Close'].rolling(window=50).mean()
        df['MA_200'] = df['Adjusted Close'].rolling(window=200).mean()
        
        # Calculate volatility (20-day rolling)
        df['Volatility (20D)'] = df['Daily Return (%)'].rolling(window=20).std()
        
        # Attempt to fetch quarterly EV/EBITDA
        df['Quarterly EV/EBITDA'] = self.fetch_ev_ebitda(stock, df)
        
        return df
    
    def fetch_ev_ebitda(self, stock, df):
        """Attempt to fetch EV/EBITDA data"""
        try:
            # Try to get info from yfinance
            info = stock.info
            
            # Check if EV/EBITDA is available
            if 'enterpriseToEbitda' in info:
                ev_ebitda = info['enterpriseToEbitda']
                # Create a column with the latest value (as quarterly data might not be available)
                return [ev_ebitda if i == len(df)-1 else None for i in range(len(df))]
            else:
                logger.info("EV/EBITDA data not available for this stock")
                return [None] * len(df)
        except Exception as e:
            logger.warning(f"Could not fetch EV/EBITDA: {str(e)}")
            return [None] * len(df)
    
    def fetch_all_stocks(self):
        """Fetch data for all stocks in the configuration"""
        logger.info(f"Starting data retrieval for {len(self.tickers)} stocks")
        logger.info(f"Date range: {self.start_date} to {self.end_date}")
        logger.info("Note: Adding delays between requests to avoid rate limiting...")
        
        for i, ticker in enumerate(self.tickers):
            # Add delay between requests to avoid rate limiting
            if i > 0:
                delay = random.uniform(2, 5)  # Random delay between 2-5 seconds
                logger.info(f"Waiting {delay:.1f} seconds before next request...")
                time.sleep(delay)
            
            data = self.fetch_stock_data(ticker)
            if data is not None:
                self.data[ticker] = data
            else:
                # Create empty DataFrame with message for failed tickers
                self.data[ticker] = pd.DataFrame({
                    'Status': ['Data retrieval failed - Please check ticker symbol or try alternative data source']
                })
        
        successful_count = sum(1 for v in self.data.values() if not v.empty and 'Status' not in v.columns)
        logger.info(f"Completed data retrieval. Successfully fetched: {successful_count}/{len(self.tickers)} stocks")
        return self.data
    
    def validate_data(self):
        """Validate the fetched data for completeness and quality"""
        validation_report = {}
        
        for ticker, data in self.data.items():
            report = {
                'records': len(data) if not data.empty else 0,
                'has_data': not data.empty and 'Adjusted Close' in data.columns,
                'missing_values': data.isnull().sum().to_dict() if not data.empty else {},
                'date_range': f"{data['Date'].min()} to {data['Date'].max()}" if not data.empty and 'Date' in data.columns else "N/A"
            }
            validation_report[ticker] = report
            
            if report['has_data']:
                logger.info(f"{ticker}: {report['records']} records, {report['date_range']}")
            else:
                logger.warning(f"{ticker}: No valid data")
        
        return validation_report


def main():
    """Main execution function"""
    logger.info("=" * 60)
    logger.info("Singapore Stocks Historical Data Retrieval")
    logger.info("=" * 60)
    
    try:
        # Initialize fetcher
        fetcher = StockDataFetcher()
        
        # Fetch all stock data
        stock_data = fetcher.fetch_all_stocks()
        
        # Validate data
        validation_report = fetcher.validate_data()
        
        # Export to Excel
        from excel_exporter import ExcelExporter
        exporter = ExcelExporter(stock_data, fetcher.config.get('output_file', 'singapore_stocks_data.xlsx'))
        output_file = exporter.export()
        
        logger.info(f"Data successfully exported to: {output_file}")
        logger.info("=" * 60)
        logger.info("Process completed successfully!")
        
        # Print summary
        print("\nSummary:")
        print(f"Stocks processed: {len(stock_data)}")
        print(f"Output file: {output_file}")
        print(f"Log file: stock_data_retrieval.log")
        
        return True
        
    except Exception as e:
        logger.error(f"Fatal error in main execution: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
