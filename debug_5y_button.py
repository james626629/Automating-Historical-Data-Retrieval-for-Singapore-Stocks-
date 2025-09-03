#!/usr/bin/env python3
"""
Debug script to find and click the 5Y button on Yahoo Finance
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
    
    # Try to find all buttons with value attribute
    print("\n=== Looking for buttons with value attribute ===")
    buttons_with_value = driver.find_elements(By.CSS_SELECTOR, "button[value]")
    for btn in buttons_with_value:
        value = btn.get_attribute('value')
        text = btn.text
        print(f"Found button: value='{value}', text='{text}'")
    
    # Try to find 5Y button specifically
    print("\n=== Looking for 5Y button ===")
    selectors_to_try = [
        ("CSS", "button[value='5_Y']"),
        ("XPATH", "//button[@value='5_Y']"),
        ("XPATH", "//button[contains(text(), '5Y')]"),
        ("XPATH", "//button[normalize-space()='5Y']"),
    ]
    
    for selector_type, selector in selectors_to_try:
        try:
            if selector_type == "CSS":
                elem = driver.find_element(By.CSS_SELECTOR, selector)
            else:
                elem = driver.find_element(By.XPATH, selector)
            print(f"✓ Found with {selector_type}: {selector}")
            print(f"  Text: '{elem.text}'")
            print(f"  Displayed: {elem.is_displayed()}")
            print(f"  Enabled: {elem.is_enabled()}")
            
            # Try to click it
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
            time.sleep(1)
            elem.click()
            print("  ✓ Clicked successfully!")
            time.sleep(3)
            
            # Check row count after click
            rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
            print(f"  Table now has {len(rows)} rows")
            break
            
        except Exception as e:
            print(f"✗ Not found with {selector_type}: {selector}")
    
    print("\n=== Page structure debug ===")
    # Check if there's a dropdown or modal that needs to be opened first
    date_buttons = driver.find_elements(By.CSS_SELECTOR, "button[data-ylk*='date']")
    print(f"Found {len(date_buttons)} date-related buttons")
    for btn in date_buttons:
        print(f"  - {btn.text}: data-ylk='{btn.get_attribute('data-ylk')}'")
    
    input("Press Enter to close browser...")
    
finally:
    driver.quit()
