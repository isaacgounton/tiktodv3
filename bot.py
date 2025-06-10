import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import pytesseract
import time
import random
import customtkinter as ctk
import tkinter as tk
import re
from utils import log_message, resource_path

class Bot:
    def __init__(self, app, log_callback):
        self.app = app
        self.log_callback = log_callback
        self.driver = None
        self.running = False

    def setup_bot(self, manual_captcha=False):
        log_message(self.app, "Setting up the bot...")
        # Automatically install the correct version of ChromeDriver
        chromedriver_autoinstaller.install()
        
        chrome_options = Options()
        
        # Only enable headless mode if not solving captcha manually
        if not manual_captcha:
            chrome_options.add_argument("--headless")  # Enable headless mode (invisible browser)
            log_message(self.app, "Running in headless mode (invisible browser)")
        else:
            log_message(self.app, "Running in visible mode for manual captcha solving")
            
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-webgl")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--log-level=3")  # Suppress most logs
        chrome_options.add_argument("--disable-logging")  # Disable logging
        
        # Only add ublock extension if it exists
        try:
            chrome_options.add_extension("ublock.crx")  # Ublock Extension
        except Exception as e:
            log_message(self.app, f"Could not load ublock extension: {e}")

        self.driver = webdriver.Chrome(options=chrome_options)

        # Block requests to fundingchoicesmessages.google.com
        self.driver.execute_cdp_cmd(
            "Network.setBlockedURLs",
            {"urls": ["https://fundingchoicesmessages.google.com/*"]}
        )
        self.driver.execute_cdp_cmd("Network.enable", {})  # Enable network interception

        self.get_captcha()

        # Create a frame for the mode selection
        self.app.mode_frame = ctk.CTkFrame(self.app.sidebar_frame, corner_radius=0)
        self.app.mode_frame.grid(row=5, column=0, padx=20, pady=10, sticky="nsew")

        self.app.mode_label = ctk.CTkLabel(self.app.mode_frame, text="Select Mode:")
        self.app.mode_label.grid(row=0, column=0, padx=20, pady=10)
        self.app.mode_var = tk.StringVar(value="----------")

        available_modes = []
        
        # Define multiple XPath patterns for each button type (primary and fallback selectors)
        button_selectors = {
            "Followers": [
                '//button[@class="btn btn-primary rounded-0 t-followers-button"]',
                '//button[contains(@class, "t-followers-button")]',
                '//button[contains(text(), "Followers")]',
                '//button[contains(@onclick, "followers")]'
            ],
            "Hearts": [
                '//button[@class="btn btn-primary rounded-0 t-hearts-button"]',
                '//button[contains(@class, "t-hearts-button")]',
                '//button[contains(text(), "Hearts")]',
                '//button[contains(@onclick, "hearts")]'
            ],
            "Views": [
                '//button[@class="btn btn-primary rounded-0 t-views-button"]',
                '//button[contains(@class, "t-views-button")]',
                '//button[contains(text(), "Views")]',
                '//button[contains(@onclick, "views")]'
            ],
            "Shares": [
                '//button[@class="btn btn-primary rounded-0 t-shares-button"]',
                '//button[contains(@class, "t-shares-button")]',
                '//button[contains(text(), "Shares")]',
                '//button[contains(@onclick, "shares")]'
            ],
            "Favorites": [
                '//button[@class="btn btn-primary rounded-0 t-favorites-button"]',
                '//button[contains(@class, "t-favorites-button")]',
                '//button[contains(text(), "Favorites")]',
                '//button[contains(@onclick, "favorites")]'
            ],
            "Live Stream": [
                '//button[@class="btn btn-primary rounded-0 t-livestream-button"]',
                '//button[contains(@class, "t-livestream-button")]',
                '//button[contains(text(), "Live Stream")]',
                '//button[contains(@onclick, "livestream")]'
            ]
        }

        # Check for available modes using multiple selectors
        for mode_name, selectors in button_selectors.items():
            button_found = False
            working_selector = None
            
            for selector in selectors:
                try:
                    button = self.driver.find_element(By.XPATH, selector)
                    if not button.get_attribute("disabled"):
                        available_modes.append(mode_name)
                        working_selector = selector
                        button_found = True
                        log_message(self.app, f"Found available mode: {mode_name} using selector: {selector}")
                        break
                except:
                    continue
            
            if not button_found:
                log_message(self.app, f"Mode {mode_name} not available - no working selectors found")

        self.app.mode_menu = ctk.CTkOptionMenu(self.app.mode_frame, variable=self.app.mode_var, values=available_modes)
        self.app.mode_menu.grid(row=1, column=0, padx=20, pady=10)

        self.app.start_button.configure(text="Start", command=self.app.start_bot)

    def get_captcha(self):
        url = "http://zefoy.com"

        try:
            log_message(self.app, "Loading zefoy.com...")
            self.driver.get(url)
            
            # Wait for the page to load
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            log_message(self.app, "Page loaded successfully")

            # Check if we're already past the captcha
            if self.check_if_captcha_solved():
                log_message(self.app, "Already past captcha screen!")
                return

            for attempt in range(5):  # Increased attempts
                try:
                    log_message(self.app, f"Captcha attempt {attempt + 1}/5")
                    
                    # Try multiple selectors for captcha image
                    captcha_selectors = [
                        '//img[@class="img-thumbnail card-img-top border-0"]',
                        '//img[contains(@class, "captcha")]',
                        '//img[contains(@src, "captcha")]',
                        '//img[@alt="captcha"]'
                    ]
                    
                    captcha_img_tag = None
                    for selector in captcha_selectors:
                        try:
                            captcha_img_tag = WebDriverWait(self.driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, selector))
                            )
                            if captcha_img_tag:
                                log_message(self.app, f"Captcha found using selector: {selector}")
                                break
                        except:
                            continue

                    if not captcha_img_tag:
                        log_message(self.app, "No captcha image found. Checking if already solved...")
                        if self.check_if_captcha_solved():
                            log_message(self.app, "Captcha already solved!")
                            return
                        else:
                            log_message(self.app, "Refreshing page...")
                            self.driver.refresh()
                            time.sleep(3)
                            continue

                    # Take screenshot and process captcha
                    captcha_img_tag.screenshot('captcha.png')
                    log_message(self.app, "Captcha image saved")
                    
                    image = Image.open('captcha.png')
                    captcha_text = self.read_captcha(image)
                    
                    # Clean up captcha text
                    captcha_text = ''.join(c for c in captcha_text if c.isalnum()).strip()
                    log_message(self.app, f"Detected captcha: '{captcha_text}'")

                    if len(captcha_text) < 3:
                        log_message(self.app, "Captcha text too short, retrying...")
                        self.driver.refresh()
                        time.sleep(2)
                        continue

                    # Find input field with multiple selectors
                    input_selectors = [
                        '//input[@class="form-control form-control-lg text-center rounded-0 remove-spaces"]',
                        '//input[contains(@class, "form-control")]',
                        '//input[@type="text"]'
                    ]
                    
                    input_field = None
                    for selector in input_selectors:
                        try:
                            input_field = self.driver.find_element(By.XPATH, selector)
                            if input_field:
                                break
                        except:
                            continue

                    if not input_field:
                        log_message(self.app, "Could not find captcha input field")
                        continue

                    # Clear and enter captcha
                    input_field.clear()
                    input_field.send_keys(captcha_text)
                    log_message(self.app, "Captcha entered, submitting...")
                    
                    # Submit by pressing Enter or finding submit button
                    try:
                        input_field.send_keys("\n")
                    except:
                        # Try to find and click submit button
                        try:
                            submit_btn = self.driver.find_element(By.XPATH, '//button[@type="submit"]')
                            submit_btn.click()
                        except:
                            pass

                    time.sleep(4)  # Wait for response

                    # Check if captcha was solved
                    if self.check_if_captcha_solved():
                        log_message(self.app, "Captcha solved successfully!")
                        return
                    else:
                        log_message(self.app, "Captcha incorrect, retrying...")
                        time.sleep(2)

                except Exception as e:
                    log_message(self.app, f"Attempt {attempt + 1} error: {str(e)[:100]}")
                    if attempt < 4:
                        time.sleep(3)
                        self.driver.refresh()
                        time.sleep(2)

            # If all attempts failed, provide manual option
            log_message(self.app, "Automatic captcha solving failed.")
            log_message(self.app, "MANUAL SOLUTION REQUIRED:")
            log_message(self.app, "1. A browser window should open (disable headless mode)")
            log_message(self.app, "2. Manually solve the captcha on zefoy.com")
            log_message(self.app, "3. Then restart the bot")
            
        except Exception as e:
            log_message(self.app, f"Critical error in captcha handling: {e}")

    def check_if_captcha_solved(self):
        """Check if we've successfully passed the captcha screen"""
        try:
            # Look for elements that appear after successful captcha
            success_indicators = [
                '/html/body/div[6]/div/div[2]/div/div/div[1]',
                '//button[contains(@class, "t-followers-button")]',
                '//button[contains(@class, "t-hearts-button")]',
                '//button[contains(@class, "t-views-button")]',
                '//div[contains(@class, "container")]//button'
            ]
            
            for selector in success_indicators:
                try:
                    if self.driver.find_elements(By.XPATH, selector):
                        return True
                except:
                    continue
            return False
        except:
            return False

    def read_captcha(self, image):
        config = r'--oem 3 --psm 6'
        return pytesseract.image_to_string(image, config=config)

    def parse_wait_time(self, text):
        match = re.search(r'(\d+) minute\(s\) (\d{1,2}) second\(s\)', text)
        if not match:
            match = re.search(r'(\d+) minute\(s\) (\d{1,2}) seconds', text)
        if match:
            minutes = int(match.group(1))
            seconds = int(match.group(2))
            return minutes * 60 + seconds + 2
        else:
            log_message(self.app, f"Failed to parse wait time from text: {text}")
        return 0

    def increment_mode_count(self, mode):
        if mode == "Views":
            self.app.views += 1000
            log_message(self.app, f"Views incremented by 1000")
        elif mode == "Hearts":
            increment = random.randint(11, 15)
            self.app.hearts += increment
            log_message(self.app, f"Hearts incremented by {increment}")
        elif mode == "Shares":
            increment = random.randint(70, 80)
            self.app.shares += increment
            log_message(self.app, f"Shares incremented by {increment}")
        elif mode == "Favorites":
            increment = random.randint(3, 6)
            self.app.favorites += increment
            log_message(self.app, f"Favorites incremented by {increment}")

    def find_element_with_fallbacks(self, selectors, element_type="button"):
        """Try multiple selectors until one works"""
        for selector in selectors:
            try:
                element = self.driver.find_element(By.XPATH, selector)
                if element:
                    return element
            except:
                continue
        raise Exception(f"Could not find {element_type} using any of the provided selectors")

    def loop(self, vidUrl, mode, amount):
        # Define selectors with fallbacks for each mode
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

        # Define fallback selectors for form elements based on common patterns
        data = {
            "Followers": {
                "Input": ['/html/body/div[9]/div/form/div/input', '//input[contains(@placeholder, "Enter")]', '//input[@type="text"]'],
                "Send": ['/html/body/div[9]/div/div/div[1]/div/form/button', '//button[contains(text(), "Send")]', '//button[@type="submit"]'],
                "Search": ['/html/body/div[9]/div/form/div/div/button', '//button[contains(text(), "Search")]'],
                "TextBeforeSend": ['/html/body/div[9]/div/div/span', '//span[contains(text(), "minute")]'],
                "TextAfterSend": ['/html/body/div[9]/div/div/span[1]', '//span[contains(text(), "minute")]']
            },
            "Hearts": {
                "Input": ['/html/body/div[8]/div/form/div/input', '//input[contains(@placeholder, "Enter")]', '//input[@type="text"]'],
                "Send": ['/html/body/div[8]/div/div/div[1]/div/form/button', '//button[contains(text(), "Send")]', '//button[@type="submit"]'],
                "Search": ['/html/body/div[8]/div/form/div/div/button', '//button[contains(text(), "Search")]'],
                "TextBeforeSend": ['/html/body/div[8]/div/div/span', '//span[contains(text(), "minute")]'],
                "TextAfterSend": ['/html/body/div[8]/div/div/span[1]', '//span[contains(text(), "minute")]']
            },
            "Views": {
                "Input": ['/html/body/div[10]/div/form/div/input', '//input[contains(@placeholder, "Enter")]', '//input[@type="text"]'],
                "Send": ['/html/body/div[10]/div/div/div[1]/div/form/button', '//button[contains(text(), "Send")]', '//button[@type="submit"]'],
                "Search": ['/html/body/div[10]/div/form/div/div/button', '//button[contains(text(), "Search")]'],
                "TextBeforeSend": ['/html/body/div[10]/div/div/span', '//span[contains(text(), "minute")]'],
                "TextAfterSend": ['/html/body/div[10]/div/div/span[1]', '//span[contains(text(), "minute")]']
            },
            "Shares": {
                "Input": ['/html/body/div[11]/div/form/div/input', '//input[contains(@placeholder, "Enter")]', '//input[@type="text"]'],
                "Send": ['/html/body/div[11]/div/div/div[1]/div/form/button', '//button[contains(text(), "Send")]', '//button[@type="submit"]'],
                "Search": ['/html/body/div[11]/div/form/div/div/button', '//button[contains(text(), "Search")]'],
                "TextBeforeSend": ['/html/body/div[11]/div/div/span', '//span[contains(text(), "minute")]'],
                "TextAfterSend": ['/html/body/div[11]/div/div/span[1]', '//span[contains(text(), "minute")]']
            },
            "Favorites": {
                "Input": ['/html/body/div[12]/div/form/div/input', '//input[contains(@placeholder, "Enter")]', '//input[@type="text"]'],
                "Send": ['/html/body/div[12]/div/div/div[1]/div/form/button', '//button[contains(text(), "Send")]', '//button[@type="submit"]'],
                "Search": ['/html/body/div[12]/div/form/div/div/button', '//button[contains(text(), "Search")]'],
                "TextBeforeSend": ['/html/body/div[12]/div/div/span', '//span[contains(text(), "minute")]'],
                "TextAfterSend": ['/html/body/div[12]/div/div/span[1]', '//span[contains(text(), "minute")]']
            },
        }

        while self.running:  # Check the flag in the loop condition
            try:
                self.driver.refresh()
                time.sleep(2)
                
                # Use fallback system to find and click the main button
                main_button = self.find_element_with_fallbacks(button_selectors[mode], f"{mode} main button")
                main_button.click()
                time.sleep(2)
                
                # Find and fill the input field
                input_field = self.find_element_with_fallbacks(data[mode]["Input"], f"{mode} input field")
                input_field.clear()  # Clear any existing text first
                input_field.send_keys(vidUrl)
                time.sleep(2)
                
                # Find and click the search button
                search_button = self.find_element_with_fallbacks(data[mode]["Search"], f"{mode} search button")
                search_button.click()
                time.sleep(6)

                # Check for delay after Search
                try:
                    wait_element = self.find_element_with_fallbacks(data[mode]["TextBeforeSend"], f"{mode} wait text before send")
                    wait_text = wait_element.text
                    if wait_text:
                        wait_seconds = self.parse_wait_time(wait_text)
                        if wait_seconds > 0:
                            current_time = time.time() - self.app.start_time
                            future_time = time.strftime('%H:%M:%S', time.gmtime(current_time + wait_seconds))
                            log_message(self.app, f"Wait {wait_seconds} seconds for your next submit (at {future_time} Elapsed Time)")
                            time.sleep(wait_seconds)
                            self.driver.refresh()
                            continue  # Skip the rest of the loop and start over
                except Exception as e:
                    log_message(self.app, f"Could not find wait text before send, continuing: {e}")

                # Find and click the send button
                send_button = self.find_element_with_fallbacks(data[mode]["Send"], f"{mode} send button")
                send_button.click()
                time.sleep(7)
                
                # Extract wait time after Send
                try:
                    wait_element = self.find_element_with_fallbacks(data[mode]["TextAfterSend"], f"{mode} wait text after send")
                    wait_text = wait_element.text
                    time.sleep(1)
                    wait_seconds = self.parse_wait_time(wait_text)
                    current_time = time.time() - self.app.start_time
                    future_time = time.strftime('%H:%M:%S', time.gmtime(current_time + wait_seconds))
                    log_message(self.app, f"Wait {wait_seconds} seconds for your next submit (at {future_time} Elapsed Time)")
                except Exception as e:
                    log_message(self.app, f"Could not parse wait time after send: {e}")
                    wait_seconds = 60  # Default wait time

                # Increment counts based on mode
                self.increment_mode_count(mode)

                # Check if the amount limit is reached
                if (mode == "Views" and self.app.views >= amount) or \
                   (mode == "Hearts" and self.app.hearts >= amount) or \
                   (mode == "Followers" and self.app.followers >= amount) or \
                   (mode == "Shares" and self.app.shares >= amount) or \
                   (mode == "Favorites" and self.app.favorites >= amount):
                    log_message(self.app, f"{mode} limit reached: {amount}")
                    self.app.stop_bot()
                    break

                time.sleep(wait_seconds)
            except Exception as e:
                log_message(self.app, f"Error in {mode} loop: {e}")
                self.driver.refresh()
                time.sleep(5)
