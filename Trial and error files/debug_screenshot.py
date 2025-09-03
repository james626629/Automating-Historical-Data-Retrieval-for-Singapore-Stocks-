#!/usr/bin/env python3
"""
Take screenshot after clicking date selector to see what's visible
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By

# Build driver in visible mode
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--window-size=1400,1000')
driver = webdriver.Chrome(options=chrome_options)

try:
    # Navigate to Yahoo Finance
    print("Navigating to Yahoo Finance...")
    driver.get("https://sg.finance.yahoo.com/quote/D05.SI/history/")
    time.sleep(5)
    
    # Click date selector to open modal
    print("\nClicking date selector to open modal...")
    date_selector = driver.find_element(By.CSS_SELECTOR, "button[data-ylk*='date-select']")
    print(f"Date selector text: {date_selector.text}")
    date_selector.click()
    
    # Wait for modal
    print("Waiting for modal to appear...")
    time.sleep(10)
    
    # Take screenshot
    driver.save_screenshot("after_date_click.png")
    print("Screenshot saved as 'after_date_click.png'")
    
    # Check what buttons are visible
    print("\nChecking for visible buttons...")
    all_buttons = driver.find_elements(By.TAG_NAME, "button")
    print(f"Total buttons: {len(all_buttons)}")
    
    visible_buttons = [btn for btn in all_buttons if btn.is_displayed()]
    print(f"Visible buttons: {len(visible_buttons)}")
    
    for btn in visible_buttons:
        text = btn.text.strip()
        if text and len(text) < 20:  # Only short button texts
            print(f"  - '{text}'")
    
    # Check for any element with "5Y" text
    print("\nSearching for any element with '5Y' text...")
    elements_with_5y = driver.find_elements(By.XPATH, "//*[contains(text(), '5Y')]")
    print(f"Found {len(elements_with_5y)} elements with '5Y' text")
    for elem in elements_with_5y:
        print(f"  - Tag: {elem.tag_name}, Text: '{elem.text}', Displayed: {elem.is_displayed()}")
    
    input("Press Enter to close browser...")
    
finally:
    driver.quit()
