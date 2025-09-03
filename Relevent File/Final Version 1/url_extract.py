#!/usr/bin/env python3
"""
Scrape Yahoo Finance historical data for SG tickers/URLs using Selenium + BeautifulSoup.
- Can be run with ticker symbols (e.g., D05.SI) or full Yahoo Finance URLs.
- If a ticker is provided, it navigates to the URL for the last 5 years of data.
- If a URL is provided, it navigates directly to that URL.
- Scrolls to load all rows and parses the historical table.
- Outputs one Excel workbook with one sheet per item.

Usage:
  # By Ticker
  py scrape_yahoo_5y.py D05.SI O39.SI

  # By URL (use quotes)
  py scrape_yahoo_5y.py "https://sg.finance.yahoo.com/quote/D05.SI/history/?period1=1599127119&period2=1756881590"

Notes:
- Runs in headless mode by default. Set HEADLESS=0 env var to show browser.
"""

import os
import sys
import time
import math
import logging
from typing import List, Optional, Tuple
from urllib.parse import urlparse
from datetime import datetime, date, timedelta

import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# This new URL format allows us to specify the date range directly for the ticker-based approach.
BASE_URL_TEMPLATE = "https://sg.finance.yahoo.com/quote/{ticker}/history?period1={start_timestamp}&period2={end_timestamp}&interval=1d&frequency=1d&includeAdjustedClose=true"


def get_inputs_from_args_or_config() -> List[str]:
    if len(sys.argv) > 1:
        return sys.argv[1:]
    # fallback to config.json
    import json
    try:
        with open('config.json', 'r') as f:
            cfg = json.load(f)
            # "tickers" key can now contain tickers or URLs
            return cfg.get('tickers', ["D05.SI", "O39.SI", "U11.SI"])
    except Exception:
        return ["D05.SI", "O39.SI", "U11.SI"]


def build_driver() -> webdriver.Remote:
    headless = os.getenv('HEADLESS', '1') != '0'

    # Try Chrome first
    try:
        chrome_options = ChromeOptions()
        if headless:
            chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--window-size=1400,1000')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--lang=en-US')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_prefs = {"profile.default_content_setting_values.cookies": 2}
        chrome_options.add_experimental_option('prefs', chrome_prefs)
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
        # Stealth tweak
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        driver.set_page_load_timeout(60)
        return driver
    except Exception as e:
        logger.warning(f"Chrome not available ({e}). Falling back to Edge...")

    # Fallback to Edge (Chromium)
    edge_options = EdgeOptions()
    if headless:
        edge_options.add_argument('headless')
    edge_options.add_argument('window-size=1400,1000')
    edge_options.add_argument('--disable-gpu')
    edge_options.add_argument('--disable-blink-features=AutomationControlled')
    driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()), options=edge_options)
    driver.set_page_load_timeout(60)
    return driver


def accept_cookies_if_present(driver: webdriver.Remote):
    try:
        # This selector is generic for common cookie consent buttons.
        cookie_button_xpath = "//button[.//span[contains(., 'Accept all')]] | //button[contains(., 'Agree')]"
        
        cookie_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, cookie_button_xpath))
        )
        cookie_button.click()
        logger.info("Accepted cookies/consent banner.")
        time.sleep(1) # Give page a moment to settle after closing banner
    except Exception:
        logger.info("No cookie banner found or could not click it.")
        pass


def count_data_rows(driver: webdriver.Remote) -> int:
    try:
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        # Filter out non-price rows by checking number of <td>
        valid = 0
        for r in rows:
            tds = r.find_elements(By.TAG_NAME, 'td')
            if len(tds) >= 6:  # date + OHLC + adj close + volume
                valid += 1
        return valid
    except Exception:
        return 0


def scroll_to_load_all_rows(driver: webdriver.Remote, max_loops: int = 50, patience: int = 3):
    logger.info("Scrolling to load all rows...")
    last_count = -1
    stable_rounds = 0
    for i in range(max_loops):
        current = count_data_rows(driver)
        logger.debug(f"Scroll {i+1}: {current} rows")
        if current == last_count:
            stable_rounds += 1
        else:
            stable_rounds = 0
        if stable_rounds >= patience:
            logger.info(f"Rows stabilized at {current}. Stopping scroll.")
            break
        last_count = current
        # Scroll to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)  # Give more time for lazy loading
    else:
        logger.info(f"Reached max scroll loops with {last_count} rows")


def parse_table_html(html: str) -> pd.DataFrame:
    soup = BeautifulSoup(html, 'lxml')
    # First try the data-test attribute, then fall back to finding any table with historical data
    table = soup.find('table', {'data-test': 'historical-prices'})
    if table is None:
        # Try to find the main historical table by looking for the header row
        for tbl in soup.find_all('table'):
            thead = tbl.find('thead')
            if thead:
                header_text = ' '.join(thead.get_text(separator=' ').strip().lower().split())
                if all(k in header_text for k in ['date', 'open', 'high', 'low', 'close', 'volume']):
                    table = tbl
                    break
    if table is None:
        raise ValueError('Historical data table not found')

    rows = []
    for tr in table.select('tbody tr'):
        td_cells = tr.find_all('td')
        if len(td_cells) < 7: # Date, O, H, L, C, Adj C, Vol
            continue
            
        cells = [c.get_text(strip=True) for c in td_cells]
        
        # Skip Dividend / Stock Split events
        if 'Dividend' in cells[1] or 'Stock Split' in cells[1]:
            continue
        rows.append(cells)

    df = pd.DataFrame(rows, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])
    if df.empty:
        return df

    # Convert types
    def to_float(x: str) -> Optional[float]:
        try:
            x = x.replace(',', '')
            if x in ('', '-', 'N/A'): return None
            return float(x)
        except Exception:
            return None

    def to_int(x: str) -> Optional[int]:
        try:
            x = x.replace(',', '')
            if x in ('', '-', 'N/A'): return None
            return int(float(x))
        except Exception:
            return None

    for col in ['Open', 'High', 'Low', 'Close', 'Adj Close']:
        df[col] = df[col].apply(to_float)
    df['Volume'] = df['Volume'].apply(to_int)

    # Convert date
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    # Convert datetime to date only (removes timestamp)
    df['Date'] = df['Date'].dt.date
    df = df.sort_values('Date').reset_index(drop=True)

    # Daily Return = Close - Open
    df['Daily Return'] = (df['Close'] - df['Open']).round(4)

    return df


def scrape_input(driver: webdriver.Remote, user_input: str) -> Tuple[str, pd.DataFrame]:
    ticker = ""
    url = ""

    # Check if the input is a URL or a ticker symbol
    if user_input.startswith('http'):
        url = user_input
        try:
            # Extract ticker from URL path for sheet naming
            path = urlparse(url).path
            ticker = path.split('/quote/')[1].split('/')[0]
        except IndexError:
            logger.warning(f"Could not parse ticker from URL. Using a generic name.")
            ticker = f"custom_url_{int(time.time())}"
    else:
        ticker = user_input
        # --- URL Construction for Ticker ---
        end_date = datetime.now()
        start_date = end_date - timedelta(days=5 * 365)
        start_timestamp = int(time.mktime(start_date.timetuple()))
        end_timestamp = int(time.mktime(end_date.timetuple()))
        url = BASE_URL_TEMPLATE.format(
            ticker=ticker,
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp
        )
    
    logger.info(f"Processing ticker: '{ticker}' from input: '{user_input}'")
    logger.info(f"Navigating to: {url}")
    driver.get(url)
    
    accept_cookies_if_present(driver)

    # Wait for the table to be present on the page.
    try:
        # Try to wait for any table element first
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'table'))
        )
        # Give page a moment to fully render
        time.sleep(2)
    except Exception:
        logger.error(f"Could not find any table for {ticker}. The page might be empty or changed.")
        return ticker, pd.DataFrame() # Return empty dataframe on failure
    
    scroll_to_load_all_rows(driver)

    html = driver.page_source
    df = parse_table_html(html)
    logger.info(f"Parsed {len(df)} rows for {ticker}")
    return ticker, df


def main():
    user_inputs = get_inputs_from_args_or_config()
    logger.info(f"Inputs to scrape: {user_inputs}")

    driver = build_driver()
    all_data = {}
    failed = []

    try:
        for user_input in user_inputs:
            try:
                # Scrape function now returns the ticker and the dataframe
                ticker, df = scrape_input(driver, user_input)
                if df is None or df.empty:
                    raise ValueError('No data extracted')
                # Use the extracted/identified ticker as the key
                all_data[ticker] = df
                time.sleep(2) # Be polite between requests
            except Exception as e:
                logger.error(f"Failed to scrape '{user_input}': {e}")
                failed.append(user_input)
    finally:
        driver.quit()

    if not all_data:
        logger.error("No data scraped for any input. Exiting.")
        sys.exit(1)

    # Export to Excel
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_file = f'sgx_stocks_5Y_history_{timestamp}.xlsx'
    with pd.ExcelWriter(out_file, engine='openpyxl') as writer:
        for ticker, df in all_data.items():
            sheet_name = f"{ticker}_history"[:31]
            df.to_excel(writer, index=False, sheet_name=sheet_name)
    logger.info(f"Saved Excel workbook: {out_file}")

    if failed:
        logger.warning(f"Inputs that failed: {failed}")


if __name__ == '__main__':
    main()

