from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import os

class EnhancedInstagramAutomator:
    def __init__(self, wait=5):
        self.wait = wait
        self.driver = None
        self.logged_in = False
        self.setup_driver()
    
    def setup_driver(self):
        """Initialize Chrome driver with options"""
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        self.driver = webdriver.Chrome(options=chrome_options)
    
    def login(self, username, password):
        """Login to Instagram"""
        if self.logged_in:
            return True
            
        print("Navigating to Instagram...")
        self.driver.get("https://www.instagram.com/")
        time.sleep(self.wait)
        
        print("Entering credentials...")
        self.driver.find_element("name", "username").send_keys(username)
        self.driver.find_element("name", "password").send_keys(password)
        time.sleep(self.wait)
        
        print("Clicking login button...")
        button = self.driver.find_element("xpath", "//button[@type='submit']")
        button.click()
        time.sleep(self.wait)
        
        self.logged_in = True
        print("Login successful!")
        return True
    
    def create_post(self, image_path, caption):
        """Create a new post with image and caption"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        self.driver.refresh()
        print("Creating new post...")
        time.sleep(self.wait)
        
        # Click new post button
        self.driver.find_element("xpath", "//*[@aria-label='New post']").click()
        time.sleep(self.wait)
        
        # Upload image
        print(f"Uploading image: {image_path}")
        self.driver.find_element("xpath", "//input[@type='file']").send_keys(os.path.abspath(image_path))
        time.sleep(self.wait)
        
        # Navigate through the post creation steps
        print("Navigating through post creation...")
        buttons = self.driver.find_elements("xpath", "//*[@role='button']")
        for step in range(5):  # Multiple steps in post creation
            for btn in buttons:
                try:
                    if btn.text.strip().lower() == "next":
                        btn.click()
                        break
                except:
                    continue
            time.sleep(self.wait)
            # Refresh button list for next iteration
            buttons = self.driver.find_elements("xpath", "//*[@role='button']")
        
        # Add caption
        print("Adding caption...")
        self.driver.find_element("xpath", "//*[@data-lexical-editor='true']").send_keys(str(caption))
        time.sleep(self.wait)
        
        # Share the post
        print("Sharing post...")
        buttons = self.driver.find_elements("xpath", "//*[@role='button']")
        for btn in buttons:
            try:
                if btn.text.strip().lower() == "share":
                    btn.click()
                    break
            except:
                pass
        
        time.sleep(self.wait)
        print("Post shared successfully!")
        return True
    
    def automate_post(self, username, password, image_path, caption):
        """Complete automation workflow for a single post"""
        try:
            if not self.logged_in:
                self.login(username, password)
            
            self.create_post(image_path, caption)
            return True
        except Exception as e:
            print(f"Error during post automation: {e}")
            raise e
    
    def close(self):
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
                print("Browser closed successfully")
            except:
                print("Error closing browser")
            finally:
                self.driver = None
                self.logged_in = False

# Compatibility class that matches the original interface
class InstagramAutomator(EnhancedInstagramAutomator):
    """Compatibility wrapper for the original InstagramAutomator interface"""
    pass

def main():
    """Main execution function for testing"""
    # Configuration
    USERNAME = "yahya.saad.magic"
    PASSWORD = "#Y1a2h3y4a5"
    IMAGE_PATH = "C:/Users/yahya/OneDrive/Pictures/logo.png"
    CAPTION = """Excited to launch my YouTube news channel, Dokit!
Stay tuned for the latest updates and stories. Let's start this journey together!
#FirstPost #DokitNews"""
    
    # Run automation
    automator = InstagramAutomator()
    try:
        automator.automate_post(USERNAME, PASSWORD, IMAGE_PATH, CAPTION)
        input("Press Enter to close the browser...")
    finally:
        automator.close()

if __name__ == "__main__":
    main()
