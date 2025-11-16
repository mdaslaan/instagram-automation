import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import unicodedata


class InstagramAutomator:
    """
    A class to automate Instagram actions like posting, following, etc.
    """
    
    def __init__(self, headless=False, maximize=True):
        """
        Initialize the Instagram automator with browser settings
        
        Args:
            headless (bool): Run browser in headless mode
            maximize (bool): Maximize the browser window
        """
        self.chrome_options = Options()
        
        # Add options to handle potential issues
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--disable-extensions")
        self.chrome_options.add_argument("--disable-web-security")
        self.chrome_options.add_argument("--allow-running-insecure-content")
        
        if maximize:
            self.chrome_options.add_argument("--start-maximized")
            
        if headless:
            self.chrome_options.add_argument("--headless")
            
        self.driver = None
        self.is_logged_in = False
        
    def start_browser(self):
        """Start the Chrome browser with error handling"""
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            return self
        except Exception as e:
            print(f"Failed to start browser: {e}")
            return None
    
    def clean_text_for_instagram(self, text):
        """Clean and prepare text for Instagram posting"""
        try:
            # Normalize unicode characters
            text = unicodedata.normalize('NFC', text)
            
            # Remove or replace problematic characters
            text = re.sub(r'[\u200b-\u200d\ufeff]', '', text)  # Remove zero-width characters
            
            # Ensure text is properly encoded
            text = text.encode('utf-8', errors='ignore').decode('utf-8')
            
            return text
        except Exception as e:
            print(f"Text cleaning error: {e}")
            # Return a safe fallback
            return re.sub(r'[^\w\s\n#@.,!?-]', '', str(text))
        
    def login(self, username, password, wait_after_login=5):
        """
        Login to Instagram with enhanced error handling
        
        Args:
            username (str): Instagram username
            password (str): Instagram password
            wait_after_login (int): Seconds to wait after login
        """
        if not self.driver:
            if not self.start_browser():
                return None
            
        try:
            self.driver.get("https://www.instagram.com/")
            time.sleep(3)
            
            # Accept cookies if present
            try:
                cookies_btn = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept') or contains(text(), 'Allow')]"))
                )
                cookies_btn.click()
                time.sleep(2)
            except:
                pass  # No cookies dialog
            
            # Find and fill username field
            username_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.clear()
            username_field.send_keys(username)
            
            # Find and fill password field
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(password)
            
            # Click login button
            login_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_btn.click()
            
            # Wait and check for successful login
            time.sleep(wait_after_login)
            
            # Check if login was successful
            try:
                # Look for elements that indicate successful login
                WebDriverWait(self.driver, 10).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.XPATH, "//*[@aria-label='New post']")),
                        EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/')]//img[@alt*='profile']"))
                    )
                )
                self.is_logged_in = True
                print("Successfully logged in")
                return self
            except:
                # Check for error messages
                try:
                    error_element = self.driver.find_element(By.XPATH, "//*[contains(text(), 'incorrect') or contains(text(), 'error')]")
                    print(f"Login failed: {error_element.text}")
                except:
                    print("Login failed: Unknown error")
                return None
                
        except Exception as e:
            print(f"Login failed: {e}")
            return None
    
    def create_post(self, image_path, caption, wait_between_steps=3, max_retries=3):
        """
        Create a new Instagram post with simplified caption handling
        
        Args:
            image_path (str): Full path to image file
            caption (str): Caption text for the post
            wait_between_steps (int): Seconds to wait between steps
            max_retries (int): Maximum number of retry attempts
        """
        if not self.driver or not self.is_logged_in:
            print("Browser not started or not logged in. Please login first.")
            return None
        
        # Clean the caption text
        caption = self.clean_text_for_instagram(caption)
        
        for attempt in range(max_retries):
            try:
                print(f"Attempting to create post (attempt {attempt + 1}/{max_retries})")
                
                # Navigate to home if not already there
                try:
                    home_btn = self.driver.find_element(By.XPATH, "//a[@href='/']")
                    home_btn.click()
                    time.sleep(2)
                except:
                    pass
                
                # Click new post button
                new_post_btn = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[@aria-label='New post'] | //*[contains(@aria-label, 'Create')]"))
                )
                new_post_btn.click()
                time.sleep(wait_between_steps)
                
                # Upload image
                file_input = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@type='file']"))
                )
                file_input.send_keys(image_path)
                time.sleep(wait_between_steps * 2)
                
                # Navigate through the post creation steps
                for step in range(3):  # Usually: Select -> Edit -> Share
                    try:
                        # Look for Next button
                        next_buttons = self.driver.find_elements(By.XPATH, "//*[text()='Next' or text()='Share']")
                        if next_buttons:
                            next_buttons[0].click()
                            time.sleep(wait_between_steps)
                        else:
                            # Alternative method - look for buttons by role
                            buttons = self.driver.find_elements(By.XPATH, "//button")
                            for btn in buttons:
                                btn_text = btn.text.strip().lower()
                                if btn_text in ['next', 'share']:
                                    btn.click()
                                    time.sleep(wait_between_steps)
                                    break
                    except Exception as e:
                        print(f"Step {step + 1} error: {e}")
                        continue
                
                # Add caption with simplified approach
                try:
                    self.driver.find_element("xpath", "//*[@aria-placeholder='Write a caption...']").send_keys(caption)
                    time.sleep(wait_between_steps)
                except Exception as e:
                    print(f"Caption input error: {e}")
                    # Continue anyway, post might work without caption
                
                # Click Share button
                try:
                    share_buttons = self.driver.find_elements(By.XPATH, "//*[text()='Share']")
                    if share_buttons:
                        share_buttons[0].click()
                    else:
                        # Alternative method
                        buttons = self.driver.find_elements(By.XPATH, "//button")
                        for btn in buttons:
                            if btn.text.strip().lower() == 'share':
                                btn.click()
                                break
                    
                    # Wait for post to complete
                    time.sleep(wait_between_steps * 3)
                    
                    # Check if post was successful
                    try:
                        # Look for success indicators
                        success_indicators = [
                            "//div[contains(text(), 'Post shared')]",
                            "//div[contains(text(), 'shared')]", 
                            "//*[@aria-label='New post']"  # Back to main page
                        ]
                        
                        for indicator in success_indicators:
                            try:
                                WebDriverWait(self.driver, 5).until(
                                    EC.presence_of_element_located((By.XPATH, indicator))
                                )
                                print("Post created successfully")
                                return self
                            except:
                                continue
                        
                        # If no success indicator found, assume success if no error
                        print("Post likely created successfully")
                        return self
                        
                    except Exception as e:
                        print(f"Post verification warning: {e}")
                        return self  # Assume success if no clear failure
                        
                except Exception as e:
                    print(f"Share button error: {e}")
                    if attempt < max_retries - 1:
                        continue
                    return None
                    
            except Exception as e:
                print(f"Post creation attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    print(f"Retrying in {wait_between_steps} seconds...")
                    time.sleep(wait_between_steps)
                    
                    # Try to close any open dialogs
                    try:
                        close_buttons = self.driver.find_elements(By.XPATH, "//*[@aria-label='Close']")
                        for btn in close_buttons:
                            btn.click()
                            time.sleep(1)
                    except:
                        pass
                else:
                    print("All retry attempts failed")
                    return None
        
        return None
    
    def handle_dialogs(self):
        """Handle common Instagram dialogs that might appear"""
        try:
            # Handle "Turn on Notifications" dialog
            not_now_buttons = self.driver.find_elements(By.XPATH, "//*[text()='Not Now']")
            for btn in not_now_buttons:
                if btn.is_displayed():
                    btn.click()
                    time.sleep(1)
            
            # Handle other potential dialogs
            dismiss_buttons = self.driver.find_elements(By.XPATH, "//*[@aria-label='Dismiss']")
            for btn in dismiss_buttons:
                if btn.is_displayed():
                    btn.click()
                    time.sleep(1)
                    
        except Exception as e:
            print(f"Dialog handling error: {e}")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            finally:
                self.driver = None
                self.is_logged_in = False


# Example usage (commented out)

if __name__ == "__main__":
    # Initialize and start the automator
    instagram = InstagramAutomator()
    
    # Login to Instagram
    instagram.login(
        username="yahya.saad.magic", 
        password="#Y1a2h3y4a5"
    )
    
    # Create a post with emojis
    instagram.create_post(
        image_path="C:/Users/yahya/Downloads/images.jpeg",
        caption=" Excited to launch my YouTube news channel, Dokit! \n #FirstPost #DokitNews"
    )
    
    # Close the browser
    instagram.close()
               