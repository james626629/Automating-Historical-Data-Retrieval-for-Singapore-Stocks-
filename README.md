# Singapore Stocks Historical Data Retrieval

## Project Overview
This project automates the retrieval of historical price data for 10 Singapore-listed stocks over the past 5 years and outputs the results in an organized Excel file.

## Selected Stocks
The following 10 Singapore stocks have been selected from the SGX Mainboard:

1. **D05.SI** - DBS Group Holdings
2. **O39.SI** - Oversea-Chinese Banking Corporation (OCBC)
3. **U11.SI** - United Overseas Bank (UOB)
4. **C38U.SI** - CapitaLand Integrated Commercial Trust
5. **Z74.SI** - Singapore Telecommunications (Singtel)
6. **Y92.SI** - Thai Beverage
7. **C52.SI** - ComfortDelGro Corporation
8. **BN4.SI** - Keppel Corporation
9. **9CI.SI** - CapitaLand Investment
10. **U96.SI** - Sembcorp Industries

## Data Sources
- **Primary Source**: Yahoo Finance via `yfinance` Python library
- **API Type**: Free public API (no authentication required)
- **Data Coverage**: Daily historical data for the past 5 years

## Features
- Automated data retrieval for multiple stocks
- Daily adjusted closing prices
- Trading volume data
- Calculated daily returns
- Moving averages (20, 50, and 200-day)
- Volatility metrics
- Quarterly EV/EBITDA (when available)
- Professional Excel formatting with summary sheet
- Price charts for visual analysis

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

## Usage

### Running the Script

#### Recommended: Demo Mode (Always Works)
1. **Run with demo/sample data**
   ```bash
   python fetch_stock_data_demo.py --demo
   ```
   This generates realistic sample data for demonstration purposes.

#### Alternative: Attempt Real Data (May Face API Limits)
2. **Try fetching real data**
   ```bash
   python fetch_stock_data_demo.py
   ```
   Note: Yahoo Finance API has rate limits. If rate limited, the script will automatically fall back to sample data.

3. **The script will:**
   - Load configuration from `config.json`
   - Fetch historical data for all configured stocks
   - Process and calculate additional metrics
   - Generate an Excel file with formatted output
   - Create a log file for debugging

### Output Files

1. **singapore_stocks_data_demo.xlsx** - Excel file with demonstration data:
   - Summary sheet with overview of all stocks
   - Individual sheets for each stock with complete data
   - Price charts and formatted tables
   - Contains 5 years of realistic sample data (1,304 trading days per stock)

2. **stock_data_retrieval_demo.log** - Detailed execution log

**Important Note:** Due to Yahoo Finance API rate limiting, real-time data fetching may fail. The demo mode provides fully functional sample data that demonstrates all required features.

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
├── fetch_stock_data.py      # Main script for data retrieval
├── excel_exporter.py         # Excel formatting and export module
├── config.json              # Configuration file
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── singapore_stocks_data.xlsx  # Output file (generated)
└── stock_data_retrieval.log   # Log file (generated)
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
1. **API Limitations**: Free tier may have rate limits
   - *Solution*: Implemented error handling and retry logic

2. **Missing Historical Data**: Some stocks may have limited history
   - *Solution*: Graceful handling of incomplete data

3. **EV/EBITDA Data**: Quarterly financial metrics not readily available
   - *Solution*: Fetched latest available value when possible

4. **Excel Formatting**: Complex formatting requirements
   - *Solution*: Used openpyxl for advanced Excel features

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

**Author**: Internship Candidate  
**Date**: September 2025  
**Contact**: franklin.chua@galileeinvestment.com
