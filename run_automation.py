from instagram_automation import InstagramAutomator

def run_instagram_automation():
    """Run the Instagram automation with custom parameters"""
    
    # You can modify these values as needed
    username = "yahya.saad.magic"
    password = "#Y1a2h3y4a5"
    image_path = "C:/Users/yahya/OneDrive/Pictures/logo.png"
    caption = """Excited to launch my YouTube news channel, Dokit!
Stay tuned for the latest updates and stories. Let's start this journey together!
#FirstPost #DokitNews"""
    
    automator = InstagramAutomator()
    automator.automate_post(username, password, image_path, caption)

if __name__ == "__main__":
    run_instagram_automation()
