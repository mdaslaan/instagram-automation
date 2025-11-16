import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
from PIL import Image, ImageTk
import requests
from io import BytesIO
import os
import google.generativeai as genai
import re
import threading
import time

class ModernExcelCardViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Social Media Post Card Viewer")
        self.root.geometry("1400x900")  # Increased width for side panel
        self.root.configure(bg='#1a1a2e')
        
        # Variables
        self.df = None
        self.current_row = 0
        self.logo_image = None
        self.content_text_widget = None
        self.generated_content_widget = None
        self.is_generating_all = False
        
        # Configure Gemini API
        self.setup_gemini_api()
        
        # Color scheme
        self.colors = {
            'primary': '#16213e',
            'secondary': '#0f3460',
            'accent': '#e94560',
            'text_primary': '#ffffff',
            'text_secondary': '#b8b8b8',
            'card_bg': '#2a2a3e',
            'success': '#4CAF50',
            'warning': '#FF9800'
        }
        
        # Configure styles
        self.configure_styles()
        
        # Create main frame
        self.main_frame = tk.Frame(root, bg=self.colors['primary'])
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.create_widgets()
        
    def setup_gemini_api(self):
        """Setup Gemini API with better error handling"""
        try:
            api_key = "AIzaSyC4u6hIHHJFyUgD_ux_yUeFdPScvFeRKIY"
            if not api_key or api_key == "YOUR_GEMINI_API_KEY":
                self.gemini_available = False
                print("Please set your Gemini API key")
                return
                
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-pro')  # Using gemini-pro instead of 2.5-pro
            self.gemini_available = True
            print("Gemini API configured successfully")
        except Exception as e:
            print(f"Gemini API setup failed: {e}")
            self.gemini_available = False

    def configure_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure button style
        style.configure('Modern.TButton',
                       background=self.colors['accent'],
                       foreground='white',
                       borderwidth=0,
                       relief='flat',
                       padding=(15, 8))
        
        style.map('Modern.TButton',
                 background=[('active', '#d63447')])
        
        # Configure frame style
        style.configure('Card.TFrame',
                       background=self.colors['card_bg'],
                       relief='flat',
                       borderwidth=1)
        
    def create_widgets(self):
        # Header
        header_frame = tk.Frame(self.main_frame, bg=self.colors['primary'], height=80)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, 
                              text="📱 Social Media Post Manager", 
                              font=("Segoe UI", 24, "bold"),
                              bg=self.colors['primary'],
                              fg=self.colors['text_primary'])
        title_label.pack(pady=20)
        
        # Control panel
        control_frame = tk.Frame(self.main_frame, bg=self.colors['secondary'], height=80)
        control_frame.pack(fill=tk.X, pady=(0, 20))
        control_frame.pack_propagate(False)
        
        # Upload section
        upload_frame = tk.Frame(control_frame, bg=self.colors['secondary'])
        upload_frame.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=15)
        
        self.upload_btn = tk.Button(upload_frame, 
                                   text="📁 Upload Excel File",
                                   command=self.upload_file,
                                   bg=self.colors['accent'],
                                   fg='white',
                                   font=("Segoe UI", 11, "bold"),
                                   relief='flat',
                                   padx=20, pady=8,
                                   cursor='hand2')
        self.upload_btn.pack(side=tk.LEFT, padx=(0, 15))
        
        self.file_label = tk.Label(upload_frame, 
                                  text="No file selected", 
                                  font=("Segoe UI", 10),
                                  bg=self.colors['secondary'],
                                  fg=self.colors['text_secondary'])
        self.file_label.pack(side=tk.LEFT, pady=8)
        
        # Navigation section
        nav_frame = tk.Frame(control_frame, bg=self.colors['secondary'])
        nav_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=20, pady=15)
        
        self.prev_btn = tk.Button(nav_frame, text="⬅ Previous", 
                                 command=self.prev_row,
                                 bg=self.colors['primary'],
                                 fg='white',
                                 font=("Segoe UI", 10, "bold"),
                                 relief='flat',
                                 padx=15, pady=8,
                                 state=tk.DISABLED,
                                 cursor='hand2')
        self.prev_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.row_label = tk.Label(nav_frame, 
                                 text="No data loaded", 
                                 font=("Segoe UI", 11, "bold"),
                                 bg=self.colors['secondary'],
                                 fg=self.colors['text_primary'])
        self.row_label.pack(side=tk.LEFT, padx=10, pady=8)
        
        self.next_btn = tk.Button(nav_frame, text="Next ➡", 
                                 command=self.next_row,
                                 bg=self.colors['primary'],
                                 fg='white',
                                 font=("Segoe UI", 10, "bold"),
                                 relief='flat',
                                 padx=15, pady=8,
                                 state=tk.DISABLED,
                                 cursor='hand2')
        self.next_btn.pack(side=tk.LEFT, padx=(10, 15))
        
        # Generate content button
        self.generate_btn = tk.Button(nav_frame, text="✨ Generate Content", 
                                     command=self.generate_content,
                                     bg='#9C27B0',
                                     fg='white',
                                     font=("Segoe UI", 10, "bold"),
                                     relief='flat',
                                     padx=15, pady=8,
                                     state=tk.DISABLED,
                                     cursor='hand2')
        self.generate_btn.pack(side=tk.LEFT, padx=(15, 5))
        
        # Generate All button
        self.generate_all_btn = tk.Button(nav_frame, text="🚀 Generate All", 
                                         command=self.generate_all_content,
                                         bg='#FF5722',
                                         fg='white',
                                         font=("Segoe UI", 10, "bold"),
                                         relief='flat',
                                         padx=15, pady=8,
                                         state=tk.DISABLED,
                                         cursor='hand2')
        self.generate_all_btn.pack(side=tk.LEFT, padx=(5, 10))
        
        # Jump to row
        jump_frame = tk.Frame(nav_frame, bg=self.colors['secondary'])
        jump_frame.pack(side=tk.LEFT)
        
        tk.Label(jump_frame, text="Row:", 
                font=("Segoe UI", 10),
                bg=self.colors['secondary'],
                fg=self.colors['text_secondary']).pack(side=tk.LEFT, padx=(0, 5))
        
        self.row_entry = tk.Entry(jump_frame, width=6, 
                                 font=("Segoe UI", 10),
                                 relief='flat',
                                 bg='white',
                                 fg='black')
        self.row_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.row_entry.bind('<Return>', self.jump_to_row)
        
        self.jump_btn = tk.Button(jump_frame, text="Go", 
                                 command=self.jump_to_row,
                                 bg=self.colors['warning'],
                                 fg='white',
                                 font=("Segoe UI", 9, "bold"),
                                 relief='flat',
                                 padx=10, pady=6,
                                 state=tk.DISABLED,
                                 cursor='hand2')
        self.jump_btn.pack(side=tk.LEFT)
        
        # Main content area - modify to create split view
        content_frame = tk.Frame(self.main_frame, bg=self.colors['primary'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create split panes
        main_paned = tk.PanedWindow(content_frame, orient=tk.HORIZONTAL, 
                                   bg=self.colors['primary'], 
                                   sashwidth=5,
                                   sashrelief=tk.RAISED)
        main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Left pane for original content
        left_frame = tk.Frame(main_paned, bg=self.colors['primary'])
        main_paned.add(left_frame, width=800)
        
        # Create scrollable frame for left pane
        self.canvas = tk.Canvas(left_frame, bg=self.colors['primary'], highlightthickness=0)
        left_scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.colors['primary'])
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=left_scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        left_scrollbar.pack(side="right", fill="y")
        
        # Right pane for generated content
        right_frame = tk.Frame(main_paned, bg=self.colors['secondary'])
        main_paned.add(right_frame, width=500)
        
        # Generated content header
        gen_header = tk.Frame(right_frame, bg=self.colors['secondary'], height=60)
        gen_header.pack(fill=tk.X, pady=(10, 0))
        gen_header.pack_propagate(False)
        
        tk.Label(gen_header, 
                text="🤖 AI Generated Content", 
                font=("Segoe UI", 16, "bold"),
                bg=self.colors['secondary'],
                fg=self.colors['text_primary']).pack(pady=15)
        
        # Generated content area
        gen_content_frame = tk.Frame(right_frame, bg=self.colors['secondary'])
        gen_content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Generated content text widget
        self.generated_content_widget = tk.Text(gen_content_frame,
                                               wrap=tk.WORD,
                                               font=("Segoe UI", 11),
                                               bg='#f8f9fa',
                                               fg='#2c3e50',
                                               relief='flat',
                                               padx=15, pady=15,
                                               state=tk.DISABLED)
        
        gen_scrollbar = tk.Scrollbar(gen_content_frame, orient="vertical", 
                                    command=self.generated_content_widget.yview)
        self.generated_content_widget.configure(yscrollcommand=gen_scrollbar.set)
        
        self.generated_content_widget.pack(side="left", fill="both", expand=True)
        gen_scrollbar.pack(side="right", fill="y")
        
        # Action buttons for generated content
        gen_actions_frame = tk.Frame(right_frame, bg=self.colors['secondary'])
        gen_actions_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        self.apply_btn = tk.Button(gen_actions_frame, 
                                  text="✅ Apply to Current Post",
                                  command=self.apply_generated_content,
                                  bg=self.colors['success'],
                                  fg='white',
                                  font=("Segoe UI", 10, "bold"),
                                  relief='flat',
                                  padx=20, pady=8,
                                  state=tk.DISABLED,
                                  cursor='hand2')
        self.apply_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_gen_btn = tk.Button(gen_actions_frame, 
                                      text="🗑️ Clear",
                                      command=self.clear_generated_content,
                                      bg=self.colors['warning'],
                                      fg='white',
                                      font=("Segoe UI", 10, "bold"),
                                      relief='flat',
                                      padx=15, pady=8,
                                      cursor='hand2')
        self.clear_gen_btn.pack(side=tk.LEFT)
        
        # Bind mousewheel
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        if self.canvas.winfo_exists():
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
    def upload_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            try:
                self.df = pd.read_excel(file_path)
                
                if self.df.empty:
                    messagebox.showwarning("Warning", "The selected file is empty.")
                    return
                
                filename = os.path.basename(file_path)
                self.file_label.config(text=f"✅ {filename} ({len(self.df)} posts loaded)")
                
                self.current_row = 0
                self.update_card()
                self.update_navigation()
                
                messagebox.showinfo("Success", f"🎉 File loaded successfully!\n{len(self.df)} posts found.")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file:\n{str(e)}")
    
    def load_image_from_url(self, url, size=(100, 100)):
        try:
            if not url or pd.isna(url):
                return None
            
            response = requests.get(url, timeout=10)
            image = Image.open(BytesIO(response.content))
            image = image.resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(image)
        except Exception:
            return None
    
    def create_field_widget(self, parent, icon, title, value, row, is_large=False):
        # Field container
        field_frame = tk.Frame(parent, bg=self.colors['card_bg'])
        field_frame.grid(row=row, column=0, sticky="ew", padx=15, pady=8)
        parent.grid_columnconfigure(0, weight=1)
        
        # Icon and title
        header_frame = tk.Frame(field_frame, bg=self.colors['card_bg'])
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        icon_label = tk.Label(header_frame, 
                             text=icon, 
                             font=("Segoe UI", 14),
                             bg=self.colors['card_bg'],
                             fg=self.colors['accent'])
        icon_label.pack(side=tk.LEFT, padx=(0, 8))
        
        title_label = tk.Label(header_frame, 
                              text=title.upper(), 
                              font=("Segoe UI", 10, "bold"),
                              bg=self.colors['card_bg'],
                              fg=self.colors['text_secondary'])
        title_label.pack(side=tk.LEFT)
        
        # Value
        if pd.isna(value):
            value = "N/A"
        
        value_font = ("Segoe UI", 12 if is_large else 11)
        if is_large:
            value_font = ("Segoe UI", 12, "bold")
        
        value_label = tk.Label(field_frame, 
                              text=str(value), 
                              font=value_font,
                              bg=self.colors['card_bg'],
                              fg=self.colors['text_primary'],
                              wraplength=400,
                              justify=tk.LEFT)
        value_label.pack(fill=tk.X, padx=20)
        
        return field_frame
    
    def remove_emojis(self, text):
        """Remove emojis from text"""
        emoji_pattern = re.compile("["
                                   u"\U0001F600-\U0001F64F"  # emoticons
                                   u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                   u"\U0001F680-\U0001F6FF"  # transport & map
                                   u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                   u"\U00002702-\U000027B0"
                                   u"\U000024C2-\U0001F251"
                                   "]+", flags=re.UNICODE)
        return emoji_pattern.sub(r'', text)

    def generate_content(self):
        """Generate social media content using Gemini API with better error handling"""
        if not self.gemini_available:
            messagebox.showerror("Error", "Gemini API is not configured. Please check your API key.")
            return
            
        if self.df is None or self.df.empty:
            messagebox.showwarning("Warning", "No data loaded. Please upload an Excel file first.")
            return
            
        try:
            # Show loading message
            self.generate_btn.config(text="Generating...", state=tk.DISABLED)
            self.root.update()
            
            # Get current row data safely
            row_data = self.df.iloc[self.current_row]
            
            # Prepare context for Gemini with safe access
            brand_name = str(row_data.get('brand_name', 'Unknown Brand'))
            platform = str(row_data.get('platform_type', 'social media'))
            post_type = str(row_data.get('type_of_post', 'post'))
            existing_content = str(row_data.get('content', ''))
            prompt_context = str(row_data.get('prompt', ''))
            
            # Create generation prompt
            generation_prompt = f"""
            Create engaging social media content for the following:
            
            Brand: {brand_name}
            Platform: {platform}
            Post Type: {post_type}
            {f"Additional Context: {prompt_context}" if prompt_context and prompt_context != 'nan' else ""}
            
            Requirements:
            1. Generate a compelling caption without any emojis
            2. Create relevant hashtags (emojis allowed in hashtags only)
            3. Keep the caption professional and engaging
            4. Make it suitable for {platform}
            5. Reflect the brand voice of {brand_name}
            6. Maximum caption length: 150 words
            
            Format the response exactly as:
            CAPTION:
            [Your caption here without emojis]
            
            HASHTAGS:
            [Your hashtags here with emojis allowed]
            """
            
            # Generate content using Gemini with timeout
            response = self.model.generate_content(generation_prompt)
            
            if not response or not response.text:
                raise Exception("Empty response from Gemini API")
                
            generated_text = response.text
            
            # Display in right panel
            self.display_generated_content(generated_text)
            
            # Show success message
            self.show_status_message("Content generated successfully!", "success")
            
        except Exception as e:
            error_msg = f"Failed to generate content: {str(e)}"
            messagebox.showerror("Generation Error", error_msg)
            self.show_status_message("Generation failed", "error")
        finally:
            # Reset button
            self.generate_btn.config(text="✨ Generate Content", state=tk.NORMAL)

    def generate_all_content(self):
        """Generate content for all rows in background thread"""
        if not self.gemini_available:
            messagebox.showerror("Error", "Gemini API is not configured.")
            return
            
        if self.df is None or self.df.empty:
            messagebox.showwarning("Warning", "No data loaded.")
            return
            
        # Confirm action
        result = messagebox.askyesno("Generate All Content", 
                                   f"This will generate content for all {len(self.df)} posts. "
                                   f"This may take several minutes. Continue?")
        if not result:
            return
            
        # Start generation in background thread
        self.is_generating_all = True
        self.generate_all_btn.config(text="Generating All...", state=tk.DISABLED)
        self.generate_btn.config(state=tk.DISABLED)
        
        # Start background thread
        thread = threading.Thread(target=self._generate_all_worker, daemon=True)
        thread.start()

    def _generate_all_worker(self):
        """Worker function for generating all content"""
        try:
            total_rows = len(self.df)
            success_count = 0
            
            for i in range(total_rows):
                if not self.is_generating_all:  # Check if cancelled
                    break
                    
                try:
                    # Update progress on main thread
                    self.root.after(0, self._update_progress, i + 1, total_rows)
                    
                    row_data = self.df.iloc[i]
                    
                    # Skip if content already exists
                    if pd.notna(row_data.get('content', '')) and str(row_data.get('content', '')).strip():
                        continue
                    
                    # Generate content for this row
                    content = self._generate_content_for_row(row_data)
                    
                    if content:
                        self.df.at[i, 'content'] = content
                        success_count += 1
                    
                    # Add delay to avoid API rate limits
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Error generating content for row {i + 1}: {e}")
                    continue
            
            # Update UI on completion
            self.root.after(0, self._generation_complete, success_count, total_rows)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Bulk generation failed: {e}"))
        finally:
            self.is_generating_all = False

    def _generate_content_for_row(self, row_data):
        """Generate content for a single row"""
        try:
            brand_name = str(row_data.get('brand_name', 'Unknown Brand'))
            platform = str(row_data.get('platform_type', 'social media'))
            post_type = str(row_data.get('type_of_post', 'post'))
            prompt_context = str(row_data.get('prompt', ''))
            
            generation_prompt = f"""
            Create social media content for:
            Brand: {brand_name}
            Platform: {platform}
            Type: {post_type}
            {f"Context: {prompt_context}" if prompt_context and prompt_context != 'nan' else ""}
            
            Requirements:
            - Caption without emojis (max 100 words)
            - Relevant hashtags (emojis allowed)
            - Professional and engaging
            
            Format:
            CAPTION:
            [caption]
            
            HASHTAGS:
            [hashtags]
            """
            
            response = self.model.generate_content(generation_prompt)
            
            if response and response.text:
                return self._parse_generated_content(response.text)
            
        except Exception as e:
            print(f"Error generating content: {e}")
            
        return None

    def _parse_generated_content(self, generated_text):
        """Parse and format generated content"""
        try:
            caption_match = re.search(r'CAPTION:\s*(.*?)\s*HASHTAGS:', generated_text, re.DOTALL)
            hashtags_match = re.search(r'HASHTAGS:\s*(.*?)$', generated_text, re.DOTALL)
            
            if caption_match and hashtags_match:
                caption = caption_match.group(1).strip()
                hashtags = hashtags_match.group(1).strip()
                
                # Remove emojis from caption
                caption = self.remove_emojis(caption)
                
                return f"{caption}\n\n{hashtags}"
            else:
                return self.remove_emojis(generated_text)
                
        except Exception:
            return self.remove_emojis(generated_text)

    def _update_progress(self, current, total):
        """Update progress display"""
        self.generate_all_btn.config(text=f"Generating... {current}/{total}")

    def _generation_complete(self, success_count, total_rows):
        """Handle completion of bulk generation"""
        self.generate_all_btn.config(text="🚀 Generate All", state=tk.NORMAL)
        self.generate_btn.config(state=tk.NORMAL)
        self.is_generating_all = False
        
        # Update current card display
        self.update_card()
        
        messagebox.showinfo("Generation Complete", 
                          f"Successfully generated content for {success_count} out of {total_rows} posts.")

    def display_generated_content(self, content):
        """Display generated content in right panel"""
        if self.generated_content_widget:
            self.generated_content_widget.config(state=tk.NORMAL)
            self.generated_content_widget.delete(1.0, tk.END)
            self.generated_content_widget.insert(1.0, content)
            self.generated_content_widget.config(state=tk.DISABLED)
            self.apply_btn.config(state=tk.NORMAL)

    def apply_generated_content(self):
        """Apply generated content to current post"""
        if self.generated_content_widget and self.df is not None:
            try:
                content = self.generated_content_widget.get(1.0, tk.END).strip()
                if content:
                    self.df.at[self.current_row, 'content'] = content
                    self.update_card()
                    self.show_status_message("Content applied successfully!", "success")
                    self.apply_btn.config(state=tk.DISABLED)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to apply content: {e}")

    def clear_generated_content(self):
        """Clear generated content panel"""
        if self.generated_content_widget:
            self.generated_content_widget.config(state=tk.NORMAL)
            self.generated_content_widget.delete(1.0, tk.END)
            self.generated_content_widget.config(state=tk.DISABLED)
            self.apply_btn.config(state=tk.DISABLED)

    def show_status_message(self, message, msg_type="info"):
        """Show status message in title bar temporarily"""
        original_title = self.root.title()
        if msg_type == "success":
            self.root.title(f"✅ {message}")
        elif msg_type == "error":
            self.root.title(f"❌ {message}")
        else:
            self.root.title(f"ℹ️ {message}")
        
        # Reset title after 3 seconds
        self.root.after(3000, lambda: self.root.title(original_title))

    def update_card(self):
        if self.df is None or self.df.empty:
            return
        
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Get current row data
        row_data = self.df.iloc[self.current_row]
        
        # Main card container
        card_container = tk.Frame(self.scrollable_frame, bg=self.colors['primary'])
        card_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Card frame with shadow effect
        shadow_frame = tk.Frame(card_container, bg='#0a0a1a', height=2)
        shadow_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        
        main_card = tk.Frame(card_container, bg=self.colors['card_bg'], relief='flat', bd=0)
        main_card.pack(fill=tk.BOTH, expand=True)
        
        # Card header
        header_frame = tk.Frame(main_card, bg=self.colors['secondary'], height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Logo section
        logo_frame = tk.Frame(header_frame, bg=self.colors['secondary'])
        logo_frame.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=10)
        
        # Load logo image
        logo_url = row_data.get('logo_of_brand', '')
        logo_image = self.load_image_from_url(logo_url, (40, 40))
        
        if logo_image:
            logo_label = tk.Label(logo_frame, image=logo_image, bg=self.colors['secondary'])
            logo_label.image = logo_image  # Keep reference
            logo_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Brand info
        brand_info_frame = tk.Frame(logo_frame, bg=self.colors['secondary'])
        brand_info_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        brand_name = row_data.get('brand_name', 'Unknown Brand')
        platform = row_data.get('platform_type', 'Unknown Platform')
        
        brand_label = tk.Label(brand_info_frame, 
                              text=str(brand_name), 
                              font=("Segoe UI", 16, "bold"),
                              bg=self.colors['secondary'],
                              fg=self.colors['text_primary'])
        brand_label.pack(anchor=tk.W)
        
        platform_label = tk.Label(brand_info_frame, 
                                 text=f"📱 {platform}", 
                                 font=("Segoe UI", 10),
                                 bg=self.colors['secondary'],
                                 fg=self.colors['text_secondary'])
        platform_label.pack(anchor=tk.W)
        
        # Post type badge
        post_type = row_data.get('type_of_post', 'post')
        type_badge = tk.Label(header_frame, 
                             text=f"🏷️ {post_type.upper()}", 
                             font=("Segoe UI", 10, "bold"),
                             bg=self.colors['accent'],
                             fg='white',
                             padx=10, pady=5)
        type_badge.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # Card body
        body_frame = tk.Frame(main_card, bg=self.colors['card_bg'])
        body_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=20)
        
        # Content section (prominent) - modify to store reference to text widget
        content_value = row_data.get('content', '')
        if content_value and not pd.isna(content_value):
            content_container = tk.Frame(body_frame, bg=self.colors['primary'])
            content_container.grid(row=0, column=0, sticky="ew", padx=15, pady=10)
            body_frame.grid_columnconfigure(0, weight=1)
            
            # Content header with edit capability
            content_header_frame = tk.Frame(content_container, bg=self.colors['primary'])
            content_header_frame.pack(fill=tk.X, padx=15, pady=(10, 5))
            
            tk.Label(content_header_frame, 
                    text="💭 CONTENT", 
                    font=("Segoe UI", 10, "bold"),
                    bg=self.colors['primary'],
                    fg=self.colors['accent']).pack(side=tk.LEFT)
            
            # Edit button for content
            edit_btn = tk.Button(content_header_frame, 
                               text="📝 Edit",
                               command=self.toggle_content_edit,
                               bg=self.colors['warning'],
                               fg='white',
                               font=("Segoe UI", 8, "bold"),
                               relief='flat',
                               padx=8, pady=2,
                               cursor='hand2')
            edit_btn.pack(side=tk.RIGHT)
            
            self.content_text_widget = tk.Text(content_container, 
                                              height=6, 
                                              wrap=tk.WORD,
                                              font=("Segoe UI", 12),
                                              bg='#ffffff',
                                              fg='#333333',
                                              relief='flat',
                                              padx=15, pady=10)
            self.content_text_widget.pack(fill=tk.X, padx=15, pady=(0, 15))
            self.content_text_widget.insert(1.0, str(content_value))
            self.content_text_widget.config(state=tk.DISABLED)
        
        # Other fields
        row_counter = 1
        field_configs = [
            ('🎨', 'Font Style', row_data.get('font_style', '')),
            ('📝', 'Prompt', row_data.get('prompt', '')),
            ('📞', 'Phone Number', row_data.get('phone_number', '')),
            ('📧', 'Email ID', row_data.get('email_id', '')),
        ]
        
        for icon, title, value in field_configs:
            if value and not pd.isna(value):
                self.create_field_widget(body_frame, icon, title, value, row_counter)
                row_counter += 1
        
        # Logo URL (if different from displayed logo)
        logo_url = row_data.get('logo_of_brand', '')
        if logo_url and not pd.isna(logo_url):
            self.create_field_widget(body_frame, '🔗', 'Logo URL', logo_url, row_counter)
            row_counter += 1
        
        # Update canvas scroll region
        self.canvas.update_idletasks()
    
    def toggle_content_edit(self):
        """Toggle content text widget between edit and read-only mode"""
        if self.content_text_widget:
            current_state = self.content_text_widget.cget('state')
            if current_state == tk.DISABLED:
                self.content_text_widget.config(state=tk.NORMAL, bg='#f0f0f0')
            else:
                # Save the content back to DataFrame
                new_content = self.content_text_widget.get(1.0, tk.END).strip()
                self.df.at[self.current_row, 'content'] = new_content
                self.content_text_widget.config(state=tk.DISABLED, bg='#ffffff')

    def update_navigation(self):
        if self.df is None or self.df.empty:
            self.prev_btn.config(state=tk.DISABLED)
            self.next_btn.config(state=tk.DISABLED)
            self.jump_btn.config(state=tk.DISABLED)
            self.generate_btn.config(state=tk.DISABLED)
            self.generate_all_btn.config(state=tk.DISABLED)
            self.row_label.config(text="No data loaded")
            return
        
        total_rows = len(self.df)
        self.row_label.config(text=f"Post {self.current_row + 1} of {total_rows}")
        
        # Update button states
        if self.current_row > 0:
            self.prev_btn.config(state=tk.NORMAL, bg=self.colors['success'])
        else:
            self.prev_btn.config(state=tk.DISABLED, bg=self.colors['primary'])
            
        if self.current_row < total_rows - 1:
            self.next_btn.config(state=tk.NORMAL, bg=self.colors['success'])
        else:
            self.next_btn.config(state=tk.DISABLED, bg=self.colors['primary'])
            
        self.jump_btn.config(state=tk.NORMAL)
        
        # Enable generation buttons only if API is available and not currently generating
        if self.gemini_available and not self.is_generating_all:
            self.generate_btn.config(state=tk.NORMAL)
            self.generate_all_btn.config(state=tk.NORMAL)
        else:
            self.generate_btn.config(state=tk.DISABLED)
            self.generate_all_btn.config(state=tk.DISABLED)

    def prev_row(self):
        if self.df is not None and self.current_row > 0:
            self.current_row -= 1
            self.update_card()
            self.update_navigation()
            self.canvas.yview_moveto(0)  # Scroll to top
            
    def next_row(self):
        if self.df is not None and self.current_row < len(self.df) - 1:
            self.current_row += 1
            self.update_card()
            self.update_navigation()
            self.canvas.yview_moveto(0)  # Scroll to top
            
    def jump_to_row(self, event=None):
        if self.df is None:
            return
        
        try:
            row_num = int(self.row_entry.get()) - 1
            
            if 0 <= row_num < len(self.df):
                self.current_row = row_num
                self.update_card()
                self.update_navigation()
                self.row_entry.delete(0, tk.END)
                self.canvas.yview_moveto(0)  # Scroll to top
            else:
                messagebox.showwarning("Invalid Row", 
                                     f"Please enter a row number between 1 and {len(self.df)}")
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid row number")

def main():
    root = tk.Tk()
    
    # Install required packages message
    try:
        import PIL
        import requests
        import google.generativeai
    except ImportError:
        messagebox.showwarning("Missing Dependencies", 
                             "Please install required packages:\npip install pillow requests pandas openpyxl google-generativeai")
        return
    
    app = ModernExcelCardViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main()