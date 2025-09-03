#!/usr/bin/env python3
"""
Scrape Yahoo Finance 5Y historical data for SG tickers using Selenium + BeautifulSoup.
- Navigates to https://sg.finance.yahoo.com/quote/{TICKER}/history/
- Clicks 5Y range
- Scrolls to load all rows
- Parses the historical table
- Outputs one Excel workbook with one sheet per ticker named {TICKER}_5Y_history

Usage:
  py scrape_yahoo_5y.py D05.SI O39.SI Z74.SI
  # or read tickers from config.json if no args provided

Notes:
- Runs in headless mode by default. Set HEADLESS=0 env var to show browser.
- Handles cookie consent if present.
- Skips Dividend/Stock Split rows.
- Daily Return = Close - Open (absolute).
"""

import os
import sys
import time
import math
import logging
from typing import List, Optional

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

BASE_URL = "https://sg.finance.yahoo.com/quote/{ticker}/history/"


def get_tickers_from_args_or_config() -> List[str]:
    if len(sys.argv) > 1:
        return sys.argv[1:]
    # fallback to config.json
    import json
    try:
        with open('config.json', 'r') as f:
            cfg = json.load(f)
            return cfg.get('tickers', ["D05.SI", "O39.SI", "U11.SI"])  # default few
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
        # Common consent buttons
        selectors = [
            "button:has(span:contains('Accept'))",
            "button:has(span:contains('I agree'))",
            "button:has(span:contains('Agree'))",
            "button[title='Agree']",
            "button[aria-label*='Accept']",
        ]
        # Selenium doesn't support :has or :contains in CSS; use XPaths
        xpaths = [
            "//button[.//span[contains(translate(., 'ACEIPT', 'aceipt'), 'accept')]]",
            "//button[.//span[contains(., 'I agree')]]",
            "//button[contains(., 'Agree') or .//span[contains(., 'Agree')]]",
            "//button[@title='Agree']",
            "//button[contains(@aria-label, 'Accept') or contains(., 'Accept')]",
        ]
        for xp in xpaths:
            elems = driver.find_elements(By.XPATH, xp)
            if elems:
                try:
                    WebDriverWait(driver, 5).until(EC.element_to_be_clickable(elems[0]))
                    elems[0].click()
                    time.sleep(1)
                    logger.info("Accepted cookies/consent banner")
                    break
                except Exception:
                    continue
    except Exception:
        pass


def click_5y_and_wait(driver: webdriver.Remote):
    # Count initial rows
    initial_count = count_data_rows(driver)

    try:
        # Step 1: Find and click the date range selector button to open the dropdown.
        logger.info("Looking for date range selector button...")
        
        # We can use a more stable selector that looks for the button meant to open a dialog.
        date_selector_xpath = "//button[contains(@class, 'yf-') or contains(@data-ylk, 'date-select-start')]"
        
        date_selector = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, date_selector_xpath))
        )
        
        logger.info("Found date selector. Clicking to open dropdown...")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", date_selector)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", date_selector)
        logger.info("Clicked date selector.")

        # Step 2: Explicitly wait for the "5Y" button to be clickable inside the dropdown.
        # This is the key fix: replaces the unreliable time.sleep().
        logger.info("Waiting for 5Y button to be clickable...")
        five_y_button_xpath = "//button[@data-value='5_Y' or text()='5Y']" # A simpler, more robust XPath
        
        five_y_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, five_y_button_xpath))
        )
        
        # Step 3: Click the 5Y button.
        logger.info("Found 5Y button. Clicking...")
        driver.execute_script("arguments[0].click();", five_y_button)
        logger.info("Successfully clicked 5Y button.")
        
        # Step 4: Wait for table to reload with 5Y data
        logger.info("Waiting for table to refresh to 5Y range...")
        
        # Wait for row count to increase significantly (5Y should have ~1250 rows)
        WebDriverWait(driver, 30).until(
            lambda d: count_data_rows(d) > initial_count + 100 or count_data_rows(d) > 1000
        )
        new_count = count_data_rows(driver)
        logger.info(f"Table updated after 5Y click. Row count: {initial_count} -> {new_count}")

    except Exception as e:
        logger.warning(f"Error in click_5y_and_wait: {e}")
        logger.warning("Could not set 5Y range, proceeding with default data.")


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
    logger.info("Scrolling to load all rows (expecting ~1250 rows for 5 years)...")
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
    # Try to find the main historical table by looking for the header row
    table = None
    for tbl in soup.find_all('table'):
        thead = tbl.find('thead')
        if not thead:
            continue
        header_text = ' '.join(thead.get_text(separator=' ').strip().lower().split())
        if all(k in header_text for k in ['date', 'open', 'high', 'low', 'close', 'volume']):
            table = tbl
            break
    if table is None:
        # fallback to the strict selector provided
        table = soup.select_one('#main-content-wrapper table')
    if table is None:
        raise ValueError('Historical data table not found')

    rows = []
    for tr in table.select('tbody tr'):
        # Get all td cells
        td_cells = tr.find_all('td')
        if len(td_cells) < 6:
            continue
            
        # Clean date extraction - get only the text content, not pseudo-elements
        date_cell = td_cells[0]
        # Remove any ::before or ::after content by getting only direct text
        date_text = date_cell.find(text=True, recursive=False)
        if not date_text:
            # If no direct text, get all text and clean it
            date_text = date_cell.get_text(strip=True)
        
        cells = [date_text] + [c.get_text(strip=True) for c in td_cells[1:]]
        
        # Skip Dividend / Stock Split events
        if len(cells) > 1 and ('Dividend' in cells[1] or 'Stock Split' in cells[1]):
            continue
        # Expected Yahoo columns: Date, Open, High, Low, Close*, Adj Close**, Volume
        try:
            date = cells[0]
            open_, high, low, close = cells[1], cells[2], cells[3], cells[4]
            adj_close = cells[5] if len(cells) > 5 else close
            volume = cells[6] if len(cells) > 6 else ''
            rows.append([date, open_, high, low, close, adj_close, volume])
        except Exception:
            continue

    df = pd.DataFrame(rows, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'])
    if df.empty:
        return df

    # Convert types
    def to_float(x: str) -> Optional[float]:
        try:
            x = x.replace(',', '')
            if x in ('', '-', 'N/A'):
                return None
            return float(x)
        except Exception:
            return None

    def to_int(x: str) -> Optional[int]:
        try:
            x = x.replace(',', '')
            if x in ('', '-', 'N/A'):
                return None
            return int(float(x))
        except Exception:
            return None

    df['Open'] = df['Open'].apply(to_float)
    df['High'] = df['High'].apply(to_float)
    df['Low'] = df['Low'].apply(to_float)
    df['Close'] = df['Close'].apply(to_float)
    df['Adj Close'] = df['Adj Close'].apply(to_float)
    df['Volume'] = df['Volume'].apply(lambda v: to_int(v) if isinstance(v, str) else v)

    # Convert date
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df.dropna(subset=['Date'])
    df = df.sort_values('Date').reset_index(drop=True)

    # Daily Return = Close - Open
    df['Daily Return'] = (df['Close'] - df['Open']).round(4)

    return df


def scrape_ticker(driver: webdriver.Remote, ticker: str) -> pd.DataFrame:
    url = BASE_URL.format(ticker=ticker)
    logger.info(f"Navigating to {url}")
    driver.get(url)
    accept_cookies_if_present(driver)

    # Wait for any table presence
    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'table')))
    except Exception:
        logger.warning("Table not present after load; continuing")
    
    # Give page time to fully load all elements
    time.sleep(2)
    
    # Click 5Y and wait
    click_5y_and_wait(driver)

    # Scroll to load all rows
    scroll_to_load_all_rows(driver)

    # Parse table
    html = driver.page_source
    df = parse_table_html(html)
    logger.info(f"Parsed {len(df)} rows for {ticker}")
    return df


def main():
    tickers = get_tickers_from_args_or_config()
    logger.info(f"Tickers to scrape: {tickers}")

    driver = build_driver()
    all_data = {}
    failed = []

    try:
        for i, ticker in enumerate(tickers):
            try:
                df = scrape_ticker(driver, ticker)
                if df is None or df.empty:
                    raise ValueError('No data extracted')
                all_data[ticker] = df
                # Be polite between tickers
                time.sleep(2)
            except Exception as e:
                logger.error(f"Failed to scrape {ticker}: {e}")
                failed.append(ticker)
    finally:
        driver.quit()

    if not all_data:
        logger.error("No data scraped for any ticker. Exiting.")
        sys.exit(1)

    # Export to Excel with timestamp to avoid file lock issues
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_file = f'sgx_stocks_5Y_history_{timestamp}.xlsx'
    with pd.ExcelWriter(out_file, engine='openpyxl') as writer:
        for ticker, df in all_data.items():
            sheet_name = f"{ticker}_5Y_history"
            # Limit sheet name to 31 chars
            sheet_name = sheet_name[:31]
            df.to_excel(writer, index=False, sheet_name=sheet_name)
    logger.info(f"Saved Excel workbook: {out_file}")

    if failed:
        logger.warning(f"Tickers failed: {failed}")


if __name__ == '__main__':
    main()

