# Social Media Content Generator & Instagram Uploader

A comprehensive GUI application for generating social media content using AI and automating Instagram posts. This tool streamlines the process of creating engaging captions and images, then uploading them directly to Instagram.

## Features

- **AI-Powered Content Generation**: Uses Google's Gemini AI to create engaging social media captions based on your brand data
- **Excel Data Import**: Load brand information, content themes, and contact details from Excel files
- **Automated Image Creation**: Generates placeholder images with brand names and content themes
- **Instagram Automation**: Automated login and post uploading using Selenium WebDriver
- **Batch Processing**: Generate and upload multiple posts in sequence
- **Real-time Logging**: Monitor all activities with timestamped logs and status updates
- **User-Friendly GUI**: Intuitive Tkinter interface with progress tracking and error handling
- **Threading Support**: Non-blocking operations for smooth user experience

## Requirements

- Python 3.8+
- Google Chrome browser (for Instagram automation)
- ChromeDriver (automatically managed by webdriver-manager)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/social-media-automator.git
cd social-media-automator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your Gemini API key:
   - Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - The application will prompt you to enter it in the GUI

## Usage

1. Run the application:
```bash
python main/main.py
```

2. Configure your settings:
   - Enter your Gemini API key
   - Provide Instagram credentials
   - Upload an Excel file with your content data

3. Excel File Format:
   Your Excel file should contain columns like:
   - `brand_name`: Name of the brand
   - `platform_type`: Target platform (e.g., Instagram)
   - `content`: Content theme or description
   - `phone_number`: Contact phone number
   - `email_id`: Contact email
   - `prompt`: Additional context for AI generation

4. Generate Content:
   - Click "Generate All Content" to create captions and images for all rows
   - Or use "Generate" on individual posts

5. Upload to Instagram:
   - Login to Instagram using the provided credentials
   - Click "Upload All Posts" for batch upload or "Upload This" for individual posts

## Project Structure

```
automator/
├── main.py              # Main GUI application
├── exps/
├──── appv1.py                 # Version 1 implementation
├──── appv2.py                 # Version 2 implementation
├──── appv3.py                 # Version 3 implementation
├──── appv4.py                 # Version 4 implementation
├── Auto.py                  # Automation utilities
├── Automator.py             # Core automation class
├── enhanced_instagram_automation.py  # Enhanced Instagram features
├── instagram_automation.py  # Basic Instagram automation
├── main.ipynb               # Jupyter notebook version
├── requirements.txt         # Python dependencies
├── run_automation.py        # Command-line runner
├── __pycache__/             # Python cache files
├── exported_images/         # Generated images output
└── temp_images/             # Temporary image storage
```

## Key Components

### InstagramUploader Class
Handles browser automation for Instagram:
- Automated login
- Post creation and uploading
- Error handling and retries

### SocialMediaGeneratorV4 Class
Main GUI application featuring:
- Excel file processing
- AI content generation
- Image creation
- Batch upload management
- Real-time status monitoring

## Safety & Ethics

- Use this tool responsibly and in accordance with Instagram's terms of service
- Respect rate limits and avoid spamming
- Ensure all content complies with platform guidelines
- The tool includes delays between uploads to prevent being flagged as spam

## Troubleshooting

### Common Issues:

1. **ChromeDriver Issues**: The application uses webdriver-manager to automatically handle ChromeDriver. If issues persist, ensure Chrome is up to date.

2. **Instagram Login Failures**: 
   - Verify credentials
   - Check if Instagram requires additional verification
   - Ensure stable internet connection

3. **AI Generation Errors**:
   - Verify Gemini API key is valid
   - Check internet connection for API calls

4. **Image Generation Issues**:
   - Ensure Pillow is installed correctly
   - Check file permissions for temp_images directory

### Logs
All activities are logged in the application's log panel. Check the logs for detailed error messages and debugging information.

## Development

The project has evolved through multiple versions:
- **v1**: Basic functionality
- **v2**: Enhanced features
- **v3**: Improved UI
- **v4**: Current version with advanced automation and error handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer


This tool is for educational and legitimate business purposes only. Users are responsible for complying with all applicable laws and platform terms of service. The developers are not responsible for any misuse or violations.
