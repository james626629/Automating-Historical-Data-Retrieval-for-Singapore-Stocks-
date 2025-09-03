#!/usr/bin/env python3
"""
Debug script to find the 5Y button inside the dropdown
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Setup Chrome (visible mode)
options = Options()
options.add_argument('--window-size=1400,1000')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

try:
    # Navigate to page
    url = "https://sg.finance.yahoo.com/quote/D05.SI/history/"
    print(f"Navigating to {url}")
    driver.get(url)
    
    # Wait for page to load
    time.sleep(5)
    
    # Find and click date selector
    print("\n=== Step 1: Find and click date selector ===")
    date_button = driver.find_element(By.CSS_SELECTOR, "button[data-ylk*='date-select']")
    print(f"Found date button: {date_button.text}")
    date_button.click()
    print("Clicked date selector")
    
    # Wait for dropdown to appear
    time.sleep(2)
    
    print("\n=== Step 2: Find all elements in the dropdown ===")
    
    # Try to find the dropdown container
    dropdowns = [
        "div[role='menu']",
        "ul[role='menu']",
        "div.yf-3zn7qw",
        "div[data-test='date-picker-menu']",
    ]
    
    for selector in dropdowns:
        try:
            dropdown = driver.find_element(By.CSS_SELECTOR, selector)
            print(f"✓ Found dropdown with selector: {selector}")
            
            # Find all buttons in dropdown
            buttons = dropdown.find_elements(By.TAG_NAME, "button")
            print(f"  Found {len(buttons)} buttons in dropdown:")
            for btn in buttons:
                text = btn.text.strip()
                value = btn.get_attribute('value')
                classes = btn.get_attribute('class')
                visible = btn.is_displayed()
                print(f"    - Text: '{text}', Value: '{value}', Visible: {visible}")
                if '5Y' in text or '5_Y' in value if value else False:
                    print(f"      ^^^ THIS IS THE 5Y BUTTON! ^^^")
            break
        except:
            print(f"✗ No dropdown found with: {selector}")
    
    print("\n=== Step 3: Try to find 5Y button directly ===")
    # Try various selectors after dropdown is open
    selectors = [
        "button:contains('5Y')",
        "li button",
        "button.tertiary-btn",
        "//button[contains(text(), '5Y')]",
        "//li//button[contains(., '5Y')]",
    ]
    
    for selector in selectors:
        try:
            if selector.startswith("//"):
                elements = driver.find_elements(By.XPATH, selector)
            else:
                # CSS selector doesn't support :contains, so use XPath instead
                if ":contains" in selector:
                    continue
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
            
            if elements:
                print(f"✓ Found {len(elements)} elements with: {selector}")
                for elem in elements:
                    if '5Y' in elem.text:
                        print(f"  Found 5Y button! Text: '{elem.text}'")
                        elem.click()
                        print("  Clicked 5Y button!")
                        time.sleep(3)
                        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                        print(f"  Table now has {len(rows)} rows")
                        break
        except Exception as e:
            pass
    
    print("\n=== Manual inspection ===")
    print("Please manually check the browser window.")
    print("The dropdown should be open. Look for the 5Y button.")
    print("You can manually click it to see if it works.")
    
    input("\nPress Enter to close browser...")
    
finally:
    driver.quit()
