#!/usr/bin/env python3
"""
Debug script to investigate why the 5Y button isn't being found
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

# Setup Chrome (visible mode to see what's happening)
options = Options()
options.add_argument('--window-size=1400,1000')
options.add_argument('--disable-blink-features=AutomationControlled')

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
    
    # Wait a moment
    time.sleep(2)
    
    # Check what elements are now visible
    print("\n=== Step 2: Check for modal/dialog elements ===")
    
    # Check for various modal indicators
    modal_selectors = [
        "div[role='dialog']",
        "div[class*='modal']",
        "div[class*='dialog']",
        "div.quickpicks",
    ]
    
    for selector in modal_selectors:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            if elements:
                print(f"✓ Found {len(elements)} element(s) with selector: {selector}")
                for elem in elements:
                    print(f"  - Displayed: {elem.is_displayed()}, Size: {elem.size}")
        except:
            print(f"✗ No elements with: {selector}")
    
    print("\n=== Step 3: Search for ANY button with value='5_Y' ===")
    # Look for the 5Y button anywhere in the DOM
    all_5y_buttons = driver.find_elements(By.CSS_SELECTOR, "button[value='5_Y']")
    print(f"Found {len(all_5y_buttons)} button(s) with value='5_Y'")
    
    for i, btn in enumerate(all_5y_buttons):
        print(f"\nButton {i+1}:")
        print(f"  Text: '{btn.text}'")
        print(f"  Displayed: {btn.is_displayed()}")
        print(f"  Enabled: {btn.is_enabled()}")
        print(f"  Location: {btn.location}")
        print(f"  Size: {btn.size}")
        print(f"  Classes: {btn.get_attribute('class')}")
        
        if btn.is_displayed() and btn.is_enabled():
            print("  Trying to click this button...")
            try:
                # Try scrolling to it first
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                time.sleep(0.5)
                btn.click()
                print("  ✓ Clicked successfully!")
                
                # Wait and check table rows
                time.sleep(3)
                rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                print(f"  Table now has {len(rows)} rows")
                break
            except Exception as e:
                print(f"  ✗ Click failed: {e}")
    
    # Alternative: Try using XPath
    print("\n=== Step 4: Try XPath search ===")
    xpath_buttons = driver.find_elements(By.XPATH, "//button[@value='5_Y']")
    print(f"Found {len(xpath_buttons)} button(s) via XPath")
    
    # Check if the quickpicks div exists but is hidden
    print("\n=== Step 5: Check quickpicks div visibility ===")
    quickpicks = driver.find_elements(By.CSS_SELECTOR, "div.quickpicks, div[class*='quickpicks']")
    for qp in quickpicks:
        print(f"Quickpicks div found:")
        print(f"  Displayed: {qp.is_displayed()}")
        print(f"  HTML: {qp.get_attribute('outerHTML')[:200]}...")
    
    print("\n=== Manual Check ===")
    print("Please check the browser window.")
    print("Is there a modal/dropdown visible?")
    print("Can you see the 5Y button?")
    print("Try manually clicking it to see if it works.")
    
    input("\nPress Enter to close browser...")
    
finally:
    driver.quit()
