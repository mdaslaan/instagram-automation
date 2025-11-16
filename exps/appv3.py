import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import io
import threading
from datetime import datetime
import csv
import re
import base64

# Handle optional imports with error messages
try:
    import pandas as pd
except ImportError:
    messagebox.showerror("Missing Dependency", "Please install pandas: pip install pandas")
    exit(1)

try:
    import requests
except ImportError:
    messagebox.showerror("Missing Dependency", "Please install requests: pip install requests")
    exit(1)

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont
except ImportError:
    messagebox.showerror("Missing Dependency", "Please install Pillow: pip install Pillow")
    exit(1)

try:
    import google.generativeai as genai
except ImportError:
    messagebox.showerror("Missing Dependency", "Please install google-generativeai: pip install google-generativeai")
    exit(1)

class SocialMediaGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Social Media Content Generator")
        self.root.geometry("1400x800")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize variables
        self.data = None
        self.cards = []
        self.gemini_api_key = ""
        self.generated_data = []  # Store all generated content for export
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container with scrollbar
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # API Key Section
        api_frame = ttk.LabelFrame(main_frame, text="API Configuration", padding=10)
        api_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(api_frame, text="Gemini API Key:").pack(side=tk.LEFT)
        self.api_key_entry = ttk.Entry(api_frame, show="*", width=50)
        self.api_key_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Button(api_frame, text="Set API Key", command=self.set_api_key).pack(side=tk.LEFT)
        
        # File Upload Section
        upload_frame = ttk.LabelFrame(main_frame, text="File Upload", padding=10)
        upload_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(upload_frame, text="Upload Excel File", command=self.upload_file).pack(side=tk.LEFT)
        self.file_label = ttk.Label(upload_frame, text="No file selected")
        self.file_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Generation Controls
        control_frame = ttk.LabelFrame(main_frame, text="Generation Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(control_frame, text="Generate All Content", 
                  command=self.generate_all_content, 
                  style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(control_frame, text="Export All Data", 
                  command=self.export_data, 
                  style="Success.TButton").pack(side=tk.LEFT, padx=(0, 10))
        
        # Progress bar
        self.progress = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(control_frame, text="Ready")
        self.status_label.pack(side=tk.RIGHT)
        
        # Scrollable Cards Area
        self.create_scrollable_area(main_frame)
        
    def create_scrollable_area(self, parent):
        # Create canvas and scrollbar for cards
        canvas_frame = ttk.Frame(parent)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg='#f8f9fa')
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bind mouse wheel to canvas
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def set_api_key(self):
        self.gemini_api_key = self.api_key_entry.get().strip()
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                messagebox.showinfo("Success", "API Key set successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to configure API: {str(e)}")
        else:
            messagebox.showwarning("Warning", "Please enter a valid API key")
    
    def upload_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        
        if file_path:
            try:
                self.data = pd.read_excel(file_path)
                self.file_label.config(text=f"Loaded: {os.path.basename(file_path)} ({len(self.data)} rows)")
                self.create_cards()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")
    
    def create_cards(self):
        # Clear existing cards
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.cards.clear()
        
        # Create cards for each row
        if self.data is not None:
            for index, row in self.data.iterrows():
                card = self.create_card(self.scrollable_frame, row, index)
                self.cards.append(card)
                card.pack(fill=tk.X, padx=5, pady=5)
    
    def create_card(self, parent, data, index):
        # Main card frame
        card = ttk.LabelFrame(parent, text=f"Post #{index + 1}", padding=15)
        
        # Create two columns
        left_frame = ttk.Frame(card)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        right_frame = ttk.Frame(card)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(15, 0))
        
        # Left column - Data display
        info_frame = ttk.LabelFrame(left_frame, text="Post Information", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        # Display key information
        info_text = f"""Brand: {data.get('brand_name', 'N/A')}
Platform: {data.get('platform_type', 'N/A')}
Font Style: {data.get('font_style', 'N/A')}
Content: {data.get('content', 'N/A')[:100]}{'...' if len(str(data.get('content', ''))) > 100 else ''}
Phone: {data.get('phone_number', 'N/A')}
Email: {data.get('email_id', 'N/A')}

Prompt: {data.get('prompt', 'N/A')[:200]}{'...' if len(str(data.get('prompt', ''))) > 200 else ''}"""
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT, wraplength=400).pack(anchor=tk.W)
        
        # Image preview (if available)
        self.display_image_preview(info_frame, data)
        
        # Right column - Generated content and controls
        content_frame = ttk.LabelFrame(right_frame, text="Generated Content", padding=10)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Generated caption area
        caption_label = ttk.Label(content_frame, text="Generated Caption:")
        caption_label.pack(anchor=tk.W)
        
        caption_text = scrolledtext.ScrolledText(content_frame, height=6, width=50, wrap=tk.WORD)
        caption_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Store reference to caption widget
        setattr(card, 'caption_widget', caption_text)
        
        # Generated image preview
        image_label = ttk.Label(content_frame, text="Generated Image:")
        image_label.pack(anchor=tk.W, pady=(10, 5))
        
        image_preview = ttk.Label(content_frame, text="No image generated", relief=tk.SUNKEN, width=30)
        image_preview.pack(pady=(0, 10))
        
        # Store reference to image preview widget
        setattr(card, 'image_preview', image_preview)
        
        # Control buttons
        button_frame = ttk.Frame(right_frame)
        button_frame.pack(fill=tk.X)
        
        generate_btn = ttk.Button(
            button_frame, 
            text=f"Generate Row {index + 1}", 
            command=lambda idx=index: self.generate_single_content(idx)
        )
        generate_btn.pack(fill=tk.X, pady=(0, 5))
        
        # Store data reference
        setattr(card, 'data', data)
        setattr(card, 'index', index)
        
        return card
    
    def display_image_preview(self, parent, data):
        # Try to load and display the original image
        try:
            # Extract image URL from prompt - IMPROVED URL REGEX
            prompt = str(data.get('prompt', ''))
            # Fix: Use a better regex pattern to properly capture full image URLs
            urls = re.findall(r'(https?://[^\s]+\.(jpg|jpeg|png|gif|bmp|webp))', prompt, re.IGNORECASE)
            image_url = None
            
            if urls:
                # Use the first complete URL found
                image_url = urls[0][0]
            else:
                # Try to find any https URL that might be an image
                all_urls = re.findall(r'https?://[^\s]+', prompt)
                if all_urls:
                    image_url = all_urls[0]
                else:
                    return
            
            # Download and display image preview
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(image_url, headers=headers, timeout=15, stream=True)
            if response.status_code == 200:
                # Check if content is actually an image
                content_type = response.headers.get('content-type', '')
                if 'image' in content_type.lower():
                    image_data = io.BytesIO()
                    for chunk in response.iter_content(chunk_size=8192):
                        image_data.write(chunk)
                    image_data.seek(0)
                    
                    image = Image.open(image_data)
                    # Create thumbnail for preview
                    image.thumbnail((200, 150), Image.Resampling.LANCZOS)
                    
                    photo = ImageTk.PhotoImage(image)
                    image_label = ttk.Label(parent, image=photo)
                    # Store reference to prevent garbage collection
                    image_label._image_ref = photo
                    image_label.pack(pady=(10, 0))
                    
                    ttk.Label(parent, text="Original Image Preview", 
                             font=('Arial', 9, 'italic')).pack()
                    
                    print(f"Successfully loaded image from: {image_url}")
                else:
                    print(f"URL does not point to an image: {content_type}")
            else:
                print(f"Failed to download image, status code: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"Network error loading image: {e}")
        except Exception as e:
            print(f"Error loading image preview: {e}")
            # Create a placeholder for failed image loads
            placeholder = ttk.Label(parent, text="Image Preview\n(Load Failed)", 
                                  relief=tk.SUNKEN, width=25, 
                                  font=('Arial', 9, 'italic'))
            placeholder.pack(pady=(10, 0))
    
    def generate_all_content(self):
        if not self.gemini_api_key:
            messagebox.showwarning("Warning", "Please set your Gemini API key first")
            return
            
        if self.data is None:
            messagebox.showwarning("Warning", "Please upload an Excel file first")
            return
        
        # Start generation in separate thread
        self.progress.start()
        self.status_label.config(text="Generating content for all posts...")
        
        thread = threading.Thread(target=self._generate_all_content_worker)
        thread.daemon = True
        thread.start()
    
    def _generate_all_content_worker(self):
        try:
            for i, card in enumerate(self.cards):
                self.root.after(0, lambda idx=i: self.status_label.config(text=f"Generating content for post {idx + 1}..."))
                self._generate_content_for_card(card)
                
            self.root.after(0, self._generation_complete)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Generation failed: {str(e)}"))
            self.root.after(0, self._generation_complete)
    
    def generate_single_content(self, index):
        if not self.gemini_api_key:
            messagebox.showwarning("Warning", "Please set your Gemini API key first")
            return
            
        card = self.cards[index]
        
        self.progress.start()
        self.status_label.config(text=f"Generating content for post {index + 1}...")
        
        thread = threading.Thread(target=lambda: self._generate_single_content_worker(card))
        thread.daemon = True
        thread.start()
    
    def _generate_single_content_worker(self, card):
        try:
            self._generate_content_for_card(card)
            self.root.after(0, self._generation_complete)
        except Exception as error:
            self.root.after(0, lambda err=str(error): messagebox.showerror("Error", f"Generation failed: {err}"))
            self.root.after(0, self._generation_complete)
    
    def _download_and_save_image(self, url, filename_prefix):
        """Download an image from a URL and save it locally"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15, stream=True)
            if response.status_code == 200:
                # Check if content is actually an image
                content_type = response.headers.get('content-type', '')
                if 'image' not in content_type.lower():
                    print(f"URL does not point to an image: {content_type}")
                    return None
                
                # Create temp directory if it doesn't exist
                os.makedirs("temp_images", exist_ok=True)
                
                # Save image with timestamp to avoid filename conflicts
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_extension = url.split('.')[-1]
                if len(file_extension) > 5:  # Not a valid extension
                    file_extension = "jpg"  # Default extension
                
                file_path = os.path.join("temp_images", f"{filename_prefix}_{timestamp}.{file_extension}")
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                return file_path
            else:
                print(f"Failed to download image, status code: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Failed to download image: {e}")
            return None
    
    def _update_caption(self, card, caption_text):
        """Update the caption text in a card's caption widget"""
        try:
            if hasattr(card, 'caption_widget'):
                caption_widget = card.caption_widget
                caption_widget.delete('1.0', tk.END)
                caption_widget.insert(tk.END, caption_text)
        except Exception as e:
            print(f"Failed to update caption: {e}")
    
    def _update_image_preview(self, card, image, label_text="Generated Image"):
        """Update the image preview in a card"""
        try:
            image_preview = card.image_preview
            
            # Clear previous image if it exists
            if hasattr(image_preview, '_image_ref'):
                delattr(image_preview, '_image_ref')
            
            if image:
                # Create a thumbnail copy
                img_copy = image.copy()
                img_copy.thumbnail((300, 200), Image.Resampling.LANCZOS)
                
                # Convert to PhotoImage
                photo = ImageTk.PhotoImage(img_copy)
                
                # Update label
                image_preview.configure(image=photo, text='')
                image_preview._image_ref = photo  # Keep a reference
            else:
                image_preview.configure(image='', text=label_text)
                
        except Exception as e:
            print(f"Failed to update image preview: {e}")
            if hasattr(card, 'image_preview'):
                card.image_preview.configure(text=f"Image preview failed: {str(e)}")
    
    def _create_enhanced_placeholder_image(self, data):
        """Create a branded placeholder image with data from the row"""
        try:
            width, height = 800, 800
            bg_color = (240, 240, 240)
            text_color = (20, 20, 20)
            
            # Create blank image
            image = Image.new('RGB', (width, height), bg_color)
            draw = ImageDraw.Draw(image)
            
            # Try to load a font, use default if not available
            try:
                font_large = ImageFont.truetype("arial.ttf", 40)
                font_medium = ImageFont.truetype("arial.ttf", 30)
                font_small = ImageFont.truetype("arial.ttf", 24)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Draw border
            border_width = 10
            draw.rectangle([(border_width, border_width), 
                           (width - border_width, height - border_width)], 
                          outline=(180, 180, 180), width=border_width)
            
            # Add brand name
            brand_name = str(data.get('brand_name', 'Brand'))
            draw.text((width//2, height//4), brand_name, fill=text_color, 
                     font=font_large, anchor='mm')
            
            # Add content text
            content = str(data.get('content', 'Content'))
            draw.text((width//2, height//2), content, fill=text_color, 
                     font=font_medium, anchor='mm')
            
            # Add contact info
            phone = str(data.get('phone_number', ''))
            email = str(data.get('email_id', ''))
            contact_text = f"{phone}\n{email}"
            draw.text((width//2, 3*height//4), contact_text, fill=text_color,
                     font=font_small, anchor='mm')
            
            # Add platform info
            platform = str(data.get('platform_type', 'Social Media'))
            draw.text((width//2, height - 50), f"For {platform}", fill=text_color,
                     font=font_small, anchor='mm')
            
            return image
            
        except Exception as e:
            print(f"Failed to create placeholder image: {e}")
            # Return a very basic fallback image
            img = Image.new('RGB', (400, 300), (200, 200, 200))
            d = ImageDraw.Draw(img)
            d.text((200, 150), "Image Placeholder", fill=(0, 0, 0))
            return img
    
    def _save_image(self, image, filename_prefix):
        """Save a PIL image to disk"""
        try:
            # Create temp directory if it doesn't exist
            os.makedirs("temp_images", exist_ok=True)
            
            # Save image with timestamp to avoid filename conflicts
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join("temp_images", f"{filename_prefix}_{timestamp}.png")
            
            image.save(file_path, format="PNG")
            return file_path
            
        except Exception as e:
            print(f"Failed to save image: {e}")
            return None
    
    def _generation_complete(self):
        """Handle completion of generation process"""
        self.progress.stop()
        self.status_label.config(text="Generation complete")
        messagebox.showinfo("Complete", "Content generation complete!")
    
    def _create_image_generation_prompt(self, data, reference_url=None):
        """Create a detailed prompt for image generation with Gemini"""
        platform = data.get('platform_type', 'Instagram')
        
        prompt = f"""Generate a professional social media image for {platform} with these specifications:

        BRAND: {data.get('brand_name', 'Unknown Brand')}
        MAIN TEXT: "{data.get('content', 'Use the best.')}
        STYLE: Professional, high-quality, visually appealing
        FONT: {data.get('font_style', 'Lexend')}
        
        Include these contact details elegantly:
        Phone: {data.get('phone_number', '')}
        Email: {data.get('email_id', '')}
        
        Additional context from brand: {data.get('prompt', '')}
        
        Generate ONLY the image, optimized for {platform}.
        """
        
        if reference_url:
            prompt += f"\n\nReference this image for inspiration: {reference_url}"
        
        return prompt
    
    def _generate_content_for_card(self, card):
        data = card.data
        index = card.index
        
        try:
            # Initialize Gemini models
            caption_model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            # Extract image URL from prompt for reference
            prompt = str(data.get('prompt', ''))
            # Use improved regex to get complete URLs
            urls = re.findall(r'(https?://[^\s]+\.(jpg|jpeg|png|gif|bmp|webp))', prompt, re.IGNORECASE)
            image_url = None
            
            if urls:
                image_url = urls[0][0]
            else:
                # Try to find any https URL that might be an image
                all_urls = re.findall(r'https?://[^\s]+', prompt)
                if all_urls:
                    image_url = all_urls[0]
            
            # Generate one perfect caption using gemini-2.0-flash-exp
            caption_prompt = f"""
            You are an expert social media copywriter. Create ONE perfect, engaging caption for {data.get('platform_type', 'Instagram')} with these specifications:

            Brand: {data.get('brand_name', 'Unknown Brand')}
            Platform: {data.get('platform_type', 'Instagram')}
            Content Theme: {data.get('content', 'Use the best.')}
            Brand Context: {data.get('prompt', '')}
            Contact: {data.get('phone_number', '')} | {data.get('email_id', '')}

            Requirements:
            ✅ Write a compelling hook in the first line
            ✅ Include the theme "{data.get('content', 'Use the best.')}" naturally
            ✅ Add 5-8 relevant hashtags at the end
            ✅ Include a call-to-action
            ✅ Keep it under 150 words for {data.get('platform_type', 'Instagram')}
            ✅ Match premium brand voice for {data.get('brand_name', 'this brand')}
            ✅ Be engaging and conversion-focused

            Write ONLY the final caption, no explanations or alternatives.
            """
            
            caption_response = caption_model.generate_content(caption_prompt)
            generated_caption = caption_response.text.strip() if caption_response else "Failed to generate caption"
            
            # Update caption in UI
            self.root.after(0, lambda: self._update_caption(card, generated_caption))
            
            # Download and save original image if available
            original_image_path = None
            generated_image_path = None
            
            if image_url:
                try:
                    original_image_path = self._download_and_save_image(image_url, f"original_image_{index + 1}")
                except Exception as e:
                    print(f"Failed to download original image: {e}")
            
            # For now, create placeholder image since image generation API has issues
            try:
                placeholder_image = self._create_enhanced_placeholder_image(data)
                generated_image_path = self._save_image(placeholder_image, f"generated_image_{index + 1}")
                self.root.after(0, lambda img=placeholder_image: self._update_image_preview(card, img, "Generated Image"))
            except Exception as e:
                print(f"Failed to create placeholder image: {e}")
                self.root.after(0, lambda err=str(e): self._update_image_preview(card, None, f"Image generation failed: {err[:50]}..."))
            
            # Store generated data for export
            generated_entry = {
                **data.to_dict(),
                'generated_caption': generated_caption,
                'original_image_path': original_image_path,
                'generated_image_path': generated_image_path,
                'generation_timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Update or add to generated_data
            if len(self.generated_data) <= index:
                self.generated_data.extend([None] * (index + 1 - len(self.generated_data)))
            self.generated_data[index] = generated_entry
                
        except Exception as e:
            print(f"Content generation failed: {e}")
            error_caption = f"Generation failed: {str(e)}"
            self.root.after(0, lambda err=error_caption: self._update_caption(card, err))
            
            # Store error data for export
            error_entry = {
                **data.to_dict(),
                'generated_caption': error_caption,
                'original_image_path': None,
                'generated_image_path': None,
                'generation_timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if len(self.generated_data) <= index:
                self.generated_data.extend([None] * (index + 1 - len(self.generated_data)))
            self.generated_data[index] = error_entry
            
    def export_data(self):
        """Export all generated data to CSV and save images"""
        if not self.generated_data or not any(self.generated_data):
            messagebox.showwarning("Warning", "No generated data to export. Please generate content first.")
            return
        
        try:
            # Ask user where to save the export
            export_dir = filedialog.askdirectory(title="Select Export Directory")
            if not export_dir:
                return
            
            # Prepare data for CSV
            csv_data = []
            for entry in self.generated_data:
                if entry:  # Skip None entries
                    csv_data.append(entry)
            
            if not csv_data:
                messagebox.showwarning("Warning", "No valid generated data to export.")
                return
            
            # Create CSV file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"social_media_content_{timestamp}.csv"
            csv_path = os.path.join(export_dir, csv_filename)
            
            # Write CSV
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                if csv_data:
                    fieldnames = csv_data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(csv_data)
            
            # Copy images to export directory
            images_export_dir = os.path.join(export_dir, "images")
            os.makedirs(images_export_dir, exist_ok=True)
            
            copied_images = 0
            for entry in csv_data:
                # Copy original images
                if entry.get('original_image_path') and os.path.exists(entry['original_image_path']):
                    src = entry['original_image_path']
                    dst = os.path.join(images_export_dir, os.path.basename(src))
                    try:
                        import shutil
                        shutil.copy2(src, dst)
                        copied_images += 1
                    except Exception as e:
                        print(f"Failed to copy original image: {e}")
                
                # Copy generated images
                if entry.get('generated_image_path') and os.path.exists(entry['generated_image_path']):
                    src = entry['generated_image_path']
                    dst = os.path.join(images_export_dir, os.path.basename(src))
                    try:
                        import shutil
                        shutil.copy2(src, dst)
                        copied_images += 1
                    except Exception as e:
                        print(f"Failed to copy generated image: {e}")
            
            # Show success message
            messagebox.showinfo(
                "Export Successful", 
                f"Data exported successfully!\n\n"
                f"📁 CSV File: {csv_filename}\n"
                f"🖼️ Images copied: {copied_images}\n"
                f"📍 Location: {export_dir}"
            )
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export data: {str(e)}")

def main():
    root = tk.Tk()
    SocialMediaGenerator(root)
    
    # Configure style
    style = ttk.Style()
    style.configure('Accent.TButton', font=('Arial', 10, 'bold'))
    style.configure('Success.TButton', font=('Arial', 10, 'bold'))
    
    root.mainloop()

if __name__ == "__main__":
    main()