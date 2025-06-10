#!/usr/bin/env python3
"""
Manual Captcha Solver for TIKTOD V3
This script opens a visible browser window for manual captcha solving
"""
import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def manual_captcha_solve():
    print("TIKTOD V3 - Manual Captcha Solver")
    print("=" * 40)
    print("This will open a visible Chrome browser for you to manually solve the captcha.")
    print("After solving the captcha, the script will check if modes are available.")
    print()
    
    # Install ChromeDriver
    chromedriver_autoinstaller.install()
    
    # Setup visible Chrome browser
    chrome_options = Options()
    # Don't use headless mode - we want to see the browser
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        chrome_options.add_extension("ublock.crx")
        print("✓ UBlock extension loaded")
    except:
        print("⚠ UBlock extension not found, continuing without it")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print("Opening zefoy.com in visible browser...")
        driver.get("http://zefoy.com")
        
        # Wait for page to load
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        
        print("\n" + "=" * 40)
        print("INSTRUCTIONS:")
        print("1. The browser window should now be open")
        print("2. Manually solve the captcha on the zefoy.com page")
        print("3. Wait for the page to load the engagement buttons")
        print("4. Then press ENTER in this terminal to check available modes")
        print("=" * 40)
        
        input("\nPress ENTER after you've solved the captcha manually...")
        
        # Check for available modes
        print("\nChecking for available engagement modes...")
        
        button_selectors = {
            "Followers": [
                '//button[@class="btn btn-primary rounded-0 t-followers-button"]',
                '//button[contains(@class, "t-followers-button")]',
                '//button[contains(text(), "Followers")]'
            ],
            "Hearts": [
                '//button[@class="btn btn-primary rounded-0 t-hearts-button"]',
                '//button[contains(@class, "t-hearts-button")]',
                '//button[contains(text(), "Hearts")]'
            ],
            "Views": [
                '//button[@class="btn btn-primary rounded-0 t-views-button"]',
                '//button[contains(@class, "t-views-button")]',
                '//button[contains(text(), "Views")]'
            ],
            "Shares": [
                '//button[@class="btn btn-primary rounded-0 t-shares-button"]',
                '//button[contains(@class, "t-shares-button")]',
                '//button[contains(text(), "Shares")]'
            ],
            "Favorites": [
                '//button[@class="btn btn-primary rounded-0 t-favorites-button"]',
                '//button[contains(@class, "t-favorites-button")]',
                '//button[contains(text(), "Favorites")]'
            ],
            "Live Stream": [
                '//button[@class="btn btn-primary rounded-0 t-livestream-button"]',
                '//button[contains(@class, "t-livestream-button")]',
                '//button[contains(text(), "Live Stream")]'
            ]
        }
        
        available_modes = []
        
        for mode_name, selectors in button_selectors.items():
            found = False
            for selector in selectors:
                try:
                    button = driver.find_element(By.XPATH, selector)
                    if not button.get_attribute("disabled"):
                        available_modes.append(mode_name)
                        print(f"✓ Found: {mode_name}")
                        found = True
                        break
                except:
                    continue
            
            if not found:
                print(f"✗ Not found: {mode_name}")
        
        print(f"\nResult: {len(available_modes)} modes available out of {len(button_selectors)}")
        
        if available_modes:
            print("✓ Captcha solved successfully! Available modes:")
            for mode in available_modes:
                print(f"  - {mode}")
            print("\nYou can now run the main bot application (python app.py)")
        else:
            print("✗ No modes found. Captcha may not be solved correctly.")
            print("Try refreshing the page and solving the captcha again.")
        
        print("\nKeeping browser open for 30 seconds for you to inspect...")
        time.sleep(30)
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Closing browser...")
        driver.quit()

if __name__ == "__main__":
    manual_captcha_solve()
