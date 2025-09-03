# Singapore Stocks Historical Data Retrieval

## Project Overview
This project automates the retrieval of historical price data for 10 Singapore-listed stocks over the past 5 years and outputs the results in an organized Excel file.

## Selected Stocks
The following 10 Singapore stocks have been selected from the SGX Mainboard:

1. **D05.SI** - DBS Group Holdings
2. **O39.SI** - Oversea-Chinese Banking Corporation (OCBC)
3. **U11.SI** - United Overseas Bank (UOB) ✓ *EV/EBITDA: 10.17*
4. **C38U.SI** - CapitaLand Integrated Commercial Trust ✓ *EV/EBITDA: 16.78*
5. **Z74.SI** - Singapore Telecommunications (Singtel) ✓ *EV/EBITDA: 18.35*
6. **Y92.SI** - Thai Beverage ✓ *EV/EBITDA: 8.26*
7. **C52.SI** - ComfortDelGro Corporation ✓ *EV/EBITDA: 14.51*
8. **BN4.SI** - Keppel Corporation
9. **9CI.SI** - CapitaLand Investment ✓ *EV/EBITDA: 31.72*
10. **U96.SI** - Sembcorp Industries ✓ *EV/EBITDA: 10.93*

**Note:** EV/EBITDA data successfully retrieved for 7 out of 10 stocks (70% success rate)

## Data Sources
- **Primary Source**: Yahoo Finance via web scraping with Selenium
- **Method**: Automated browser navigation and data extraction
- **Data Coverage**: Daily historical data for the past 5 years
- **Latest Version**: Final Version 1 (September 2025)

## Features
- Automated web scraping for multiple stocks using Selenium WebDriver
- Support for both ticker symbols and direct Yahoo Finance URLs
- Daily OHLC (Open, High, Low, Close) prices
- Adjusted closing prices
- Trading volume data
- Calculated daily returns (Close - Open)
- **NEW: EV/EBITDA ratio extraction from Yahoo Finance statistics page**
- Date formatting optimized for Excel (no timestamps)
- Automatic scrolling to load all historical data
- Headless browser mode for background execution
- Multi-stock batch processing with separate Excel sheets

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup Steps

1. **Clone or download the project**
   ```bash
   cd singapore-stocks-data
   ```

2. **Install required packages**
   ```bash
   pip install -r requirements.txt
   ```
   
   **Additional requirements for Final Version 1:**
   ```bash
   pip install selenium beautifulsoup4 lxml webdriver-manager pandas openpyxl
   ```

## Usage

### Running the Latest Version (Final Version 1)

1. **Navigate to the Final Version 1 directory**
   ```bash
   cd "Relevent File/Final Version 1"
   ```

2. **Run the basic scraper (price data only)**
   ```bash
   py url_extract.py D05.SI O39.SI U11.SI C38U.SI Z74.SI Y92.SI C52.SI BN4.SI 9CI.SI U96.SI
   ```

3. **Run the enhanced scraper with EV/EBITDA data**
   ```bash
   py url_extract_EV_EBITDA.py D05.SI O39.SI U11.SI C38U.SI Z74.SI Y92.SI C52.SI BN4.SI 9CI.SI U96.SI
   ```

4. **Or run with Yahoo Finance URLs**
   ```bash
   py url_extract.py "https://sg.finance.yahoo.com/quote/D05.SI/history/?period1=1599127119&period2=1756881590"
   ```

5. **The script will:**
   - Navigate to Yahoo Finance for each ticker/URL
   - Automatically handle cookie consent banners
   - For EV/EBITDA version: Extract financial metrics from statistics page
   - Scroll to load all available historical data
   - Parse and extract OHLC prices and volume
   - Format dates properly (YYYY-MM-DD without timestamps)
   - Calculate daily returns
   - Generate timestamped Excel file with all data
   - Include EV/EBITDA ratios when available (70% success rate)

### Output Files

1. **sgx_stocks_5Y_history_YYYYMMDD_HHMMSS.xlsx** - Basic price data:
   - Individual sheets for each stock (e.g., "D05.SI_history")
   - Columns: Date, Open, High, Low, Close, Adj Close, Volume, Daily Return
   - Date format: YYYY-MM-DD (e.g., 2020-09-04)
   - Contains up to 5 years of historical data (typically ~1,257 rows per stock)

2. **sgx_stocks_with_EV_EBITDA_YYYYMMDD_HHMMSS.xlsx** - Enhanced with financial metrics:
   - Summary sheet with all tickers and their EV/EBITDA values
   - Individual stock sheets with price data + EV/EBITDA column (when available)
   - EV/EBITDA successfully retrieved for 70% of stocks
   - Highlighted formatting for financial metrics

3. **Console output** - Real-time progress updates:
   - Navigation status for each ticker
   - EV/EBITDA extraction results
   - Row count as data loads
   - Success/failure messages

**Latest Updates:** 
- Fixed date formatting issue - dates now display without timestamps
- Added EV/EBITDA extraction capability - successfully retrieved for 7/10 stocks

### Customization

To modify the stock selection or settings, edit `config.json`:
```json
{
    "tickers": ["D05.SI", "O39.SI", ...],
    "output_file": "singapore_stocks_data.xlsx",
    "years_of_data": 5
}
```

## Project Structure
```
singapore-stocks-data/
│
├── Relevent File/
│   └── Final Version 1/
│       ├── url_extract.py                    # Web scraper with date fix
│       ├── url_extract_EV_EBITDA.py         # Enhanced scraper with EV/EBITDA
│       ├── sgx_stocks_5Y_history_*.xlsx     # Price data output files
│       └── sgx_stocks_with_EV_EBITDA_*.xlsx # Files with EV/EBITDA data
│
├── fetch_stock_data.py              # Original yfinance version
├── excel_exporter.py                # Excel formatting module
├── config.json                      # Configuration file
├── requirements.txt                 # Python dependencies
├── README.md                        # This file
└── Various debug and test scripts
```

## Assumptions

1. **Market Days**: Calculations assume standard trading days (excluding weekends and holidays)
2. **Data Availability**: Not all stocks may have complete 5-year history
3. **EV/EBITDA**: Quarterly EV/EBITDA data may not be available for all stocks through the free API
4. **Currency**: All prices are in SGD (Singapore Dollars)
5. **Adjusted Prices**: Using adjusted close prices to account for dividends and splits

## Data Processing

### Calculated Metrics
- **Daily Returns**: Percentage change from previous day's adjusted close
- **Moving Averages**: 20, 50, and 200-day simple moving averages
- **Volatility**: 20-day rolling standard deviation of returns
- **YTD Return**: Year-to-date percentage return
- **1-Year Return**: Trailing 12-month percentage return

### Data Quality
- Missing data points are handled gracefully
- Failed ticker retrievals are logged and marked in output
- Data validation ensures completeness before export

## Challenges and Solutions

### Challenges Faced
1. **Date Formatting Issue**: Excel displaying dates with timestamps (12:00:00 AM)
   - *Solution*: Convert datetime to date-only format using `.dt.date`

2. **Dynamic Content Loading**: Yahoo Finance uses lazy loading for historical data
   - *Solution*: Implemented automatic scrolling with stability detection

3. **Cookie Consent Banners**: Blocking access to data
   - *Solution*: Automated cookie acceptance handling

4. **Browser Detection**: Sites detecting automated browsers
   - *Solution*: Stealth mode configuration with webdriver tweaks

5. **Rate Limiting**: Need to be respectful of server resources
   - *Solution*: Added delays between requests

### Suggestions for Improvement

1. **Multiple Data Sources**: 
   - Integrate Alpha Vantage or other APIs for comparison
   - Web scraping from SGX.com for official data

2. **Enhanced Analytics**:
   - Add technical indicators (RSI, MACD, Bollinger Bands)
   - Correlation analysis between stocks
   - Sector performance comparison

3. **Real-time Updates**:
   - Schedule daily/weekly automated runs
   - Email notifications for significant changes

4. **Database Storage**:
   - Store historical data in SQLite for faster access
   - Track data retrieval history

5. **Advanced Visualizations**:
   - Interactive dashboards using Plotly or Dash
   - Candlestick charts for better price analysis

## Error Handling

The script includes comprehensive error handling for:
- Network connectivity issues
- Invalid ticker symbols
- API rate limiting
- Data processing errors
- File I/O exceptions

All errors are logged to `stock_data_retrieval.log` for debugging.

## Support

For issues or questions, please refer to the log file for detailed error messages and execution trace.

## License

This project is created for the Galilee Internship Assignment.

---

**Author**: James Goh  
**Date**: September 2025  
**Latest Version**: Final Version 1 (Date formatting fixed + EV/EBITDA extraction added)  
**EV/EBITDA Success Rate**: 7 out of 10 stocks (70%)  
**Contact**: franklin.chua@galileeinvestment.com
