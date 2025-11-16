from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

class InstagramAutomator:
    def __init__(self):
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Initialize Chrome driver with options"""
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome(options=chrome_options)
    
    def login(self, username, password):
        """Login to Instagram"""
        print("Navigating to Instagram...")
        self.driver.get("https://www.instagram.com/")
        time.sleep(3)
        
        print("Entering credentials...")
        self.driver.find_element(By.NAME, "username").send_keys(username)
        self.driver.find_element(By.NAME, "password").send_keys(password)
        
        print("Clicking login button...")
        button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        button.click()
        time.sleep(5)
    
    def create_new_post(self):
        """Click on new post button"""
        print("Clicking new post button...")
        self.driver.find_element(By.XPATH, "//*[@aria-label='New post']").click()
        time.sleep(3)
    
    def upload_image(self, image_path):
        """Upload image file"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        print(f"Uploading image: {image_path}")
        self.driver.find_element(By.XPATH, "//input[@type='file']").send_keys(image_path)
        time.sleep(3)
    
    def navigate_next_steps(self):
        """Click Next buttons twice to proceed"""
        print("Navigating through post creation steps...")
        buttons = self.driver.find_elements(By.XPATH, "//*[@role='button']")
        for i in range(2):
            for btn in buttons:
                try:
                    if btn.text.strip().lower() == "next":
                        btn.click()
                        break
                except:
                    pass
            time.sleep(2)
            # Refresh button list for next iteration
            buttons = self.driver.find_elements(By.XPATH, "//*[@role='button']")
    
    def add_caption(self, caption):
        """Add caption to the post"""
        print("Adding caption...")
        caption_field = self.driver.find_element(By.XPATH, "//*[@data-lexical-editor='true']")
        caption_field.clear()
        caption_field.send_keys(caption)
        time.sleep(2)
    
    def share_post(self):
        """Share the post"""
        print("Sharing post...")
        buttons = self.driver.find_elements(By.XPATH, "//*[@role='button']")
        for btn in buttons:
            if btn.text.strip().lower() == "share":
                btn.click()
                break
        time.sleep(3)
        print("Post shared successfully!")
    
    def automate_post(self, username, password, image_path, caption):
        """Complete automation workflow"""
        try:
            self.login(username, password)
            self.create_new_post()
            self.upload_image(image_path)
            self.navigate_next_steps()
            self.add_caption(caption)
            self.share_post()
            print("Automation completed successfully!")
            time.sleep(5)
            self.driver.refresh()
            time.sleep(5)
        except Exception as e:
            print(f"Error during automation: {e}")
        finally:
            input("Press Enter to close the browser...")
            self.close()
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

def main():
    """Main execution function"""
    # Configuration
    USERNAME = "yahya.saad.magic"
    PASSWORD = "#Y1a2h3y4a5"
    IMAGE_PATH = "C:/Users/yahya/OneDrive/Pictures/logo.png"
    CAPTION = """Excited to launch my YouTube news channel, Dokit!
Stay tuned for the latest updates and stories. Let's start this journey together!
#FirstPost #DokitNews"""
    
    # Run automation
    automator = InstagramAutomator()
    automator.automate_post(USERNAME, PASSWORD, IMAGE_PATH, CAPTION)

if __name__ == "__main__":
    main()
