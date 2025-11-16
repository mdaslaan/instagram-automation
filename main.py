import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import io
import threading
from datetime import datetime
import csv
import re
import time

# Optional imports with graceful handling
try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import requests
except ImportError:
    requests = None

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont
except ImportError:
    Image = ImageTk = ImageDraw = ImageFont = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Selenium for uploading
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
except ImportError:
    webdriver = None

class InstagramUploader:
    """Handles Instagram browser automation (single and batch uploads)."""
    def __init__(self, status_callback=lambda m: None):
        self.driver = None
        self.stop_event = threading.Event()
        self.status_callback = status_callback
        self.lock = threading.Lock()
        self._init_driver()

    def _init_driver(self):
        if webdriver is None:
            self.status_callback("Selenium not installed. Upload disabled.")
            return
        try:
            chrome_options = Options()
            chrome_options.add_argument("--start-maximized")
            self.driver = webdriver.Chrome(options=chrome_options)
            self.status_callback("Chrome launched")
        except Exception as e:
            self.status_callback(f"Failed to start Chrome: {e}")
            self.driver = None

    def login(self, username, password):
        if not self.driver:
            self.status_callback("Driver not available")
            return False
        try:
            self.status_callback("Opening Instagram login page...")
            self.driver.get("https://www.instagram.com/")
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.NAME, "username")))
            u = self.driver.find_element(By.NAME, "username")
            p = self.driver.find_element(By.NAME, "password")
            u.clear(); u.send_keys(username)
            p.clear(); p.send_keys(password)
            self.status_callback("Submitting credentials...")
            self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
            WebDriverWait(self.driver, 30).until(lambda d: "accounts/login" not in d.current_url)
            self.status_callback("Login successful")
            return True
        except TimeoutException:
            self.status_callback("Login timeout / maybe wrong credentials")
        except Exception as e:
            self.status_callback(f"Login failed: {e}")
        return False

    def _click_new_post(self):
        WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[@aria-label='New post']"))).click()
        time.sleep(2)

    def _upload_image(self, image_path):
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found: {image_path}")
        inp = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.XPATH, "//input[@type='file']")))
        inp.send_keys(os.path.abspath(image_path))
        time.sleep(2)

    def _next_steps(self, count=2):
        for _ in range(count):
            buttons = self.driver.find_elements(By.XPATH, "//*[@role='button']")
            clicked = False
            for b in buttons:
                try:
                    if b.text.strip().lower() == "next":
                        b.click(); clicked = True; break
                except Exception:
                    pass
            if not clicked:
                time.sleep(1)
            time.sleep(1.5)

    def _add_caption(self, caption):
        field = WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.XPATH, "//*[@data-lexical-editor='true']")))
        field.click()
        try:
            field.clear()
        except Exception:
            pass
        field.send_keys(caption[:2200])
        time.sleep(1)

    def _share(self):
        buttons = self.driver.find_elements(By.XPATH, "//*[@role='button']")
        for b in buttons:
            try:
                if b.text.strip().lower() == "share":
                    b.click(); return True
            except Exception:
                pass
        return False

    def upload_post(self, image_path, caption):
        with self.lock:
            if self.stop_event.is_set():
                return False, "Stopped"
            try:
                self.status_callback("Starting new post upload...")
                self._click_new_post()
                self._upload_image(image_path)
                self._next_steps()
                self._add_caption(caption or "")
                if not self._share():
                    raise RuntimeError("Share button not found")
                self.status_callback("Post shared; waiting for completion")
                time.sleep(5)
                return True, "Uploaded"
            except Exception as e:
                self.status_callback(f"Upload failed: {e}")
                return False, str(e)

    def stop(self):
        self.stop_event.set()
        self.status_callback("Stop requested")

    def reset_stop(self):
        if self.stop_event.is_set():
            self.stop_event.clear()
            self.status_callback("Stop flag cleared")

    def close(self):
        try:
            if self.driver:
                self.driver.quit()
        except Exception:
            pass
        self.driver = None

class SocialMediaGeneratorV4:
    def __init__(self, root):
        self.root = root
        self.root.title("Social Media Content Generator & Instagram Uploader (v4)")
        self.root.geometry("1600x900")
        self.root.configure(bg='#f5f5f5')

        self.gemini_api_key = ""
        self.data = None
        self.cards = []
        self.generated_data = []
        self.uploader = InstagramUploader(status_callback=self._log_and_status)
        self.upload_thread = None

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Add initial log entry
        self._add_log("Application started - Chrome browser launched", "INFO")

    # UI BUILD
    def _build_ui(self):
        # Configure style
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        
        # Configure custom styles
        style.configure('Title.TLabel', font=('Segoe UI', 12, 'bold'), foreground='#2c3e50')
        style.configure('Header.TButton', font=('Segoe UI', 9, 'bold'), padding=(10, 5))
        style.configure('Action.TButton', font=('Segoe UI', 9), padding=(8, 4))
        
        # Main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        
        # Left side - Controls and Cards
        left_frame = ttk.Frame(main_container)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Right side - Logs
        right_frame = ttk.LabelFrame(main_container, text="Activity Logs", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # Build left side components
        self._build_controls(left_frame)
        self._build_cards_area(left_frame)
        
        # Build right side logs
        self._build_logs_panel(right_frame)

    def _build_controls(self, parent):
        # Control panel
        control_frame = ttk.LabelFrame(parent, text="Controls", padding=10)
        control_frame.pack(fill=tk.X, pady=(0, 8))
        
        # Row 0: API Key
        api_frame = ttk.Frame(control_frame)
        api_frame.grid(row=0, column=0, columnspan=5, sticky='ew', pady=(0, 5))
        api_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Label(api_frame, text="Gemini API Key:", style='Title.TLabel').grid(row=0, column=0, sticky='w')
        self.api_entry = ttk.Entry(api_frame, show='*', font=('Consolas', 9))
        self.api_entry.grid(row=0, column=1, sticky='ew', padx=(10, 5))
        ttk.Button(api_frame, text="Set API Key", command=self._set_api_key, style='Header.TButton').grid(row=0, column=2)

        # Row 1: Instagram Credentials
        cred_frame = ttk.Frame(control_frame)
        cred_frame.grid(row=1, column=0, columnspan=5, sticky='ew', pady=5)
        cred_frame.grid_columnconfigure(1, weight=1)
        cred_frame.grid_columnconfigure(3, weight=1)
        
        ttk.Label(cred_frame, text="Instagram Username:", style='Title.TLabel').grid(row=0, column=0, sticky='w')
        self.user_entry = ttk.Entry(cred_frame, font=('Segoe UI', 9))
        self.user_entry.grid(row=0, column=1, sticky='ew', padx=(10, 15))
        
        ttk.Label(cred_frame, text="Password:", style='Title.TLabel').grid(row=0, column=2, sticky='w')
        self.pass_entry = ttk.Entry(cred_frame, show='*', font=('Segoe UI', 9))
        self.pass_entry.grid(row=0, column=3, sticky='ew', padx=(10, 15))
        
        ttk.Button(cred_frame, text="🔐 Login to Instagram", command=self._login_instagram, style='Header.TButton').grid(row=0, column=4)

        # Row 2: File operations
        file_frame = ttk.Frame(control_frame)
        file_frame.grid(row=2, column=0, columnspan=5, sticky='ew', pady=5)
        file_frame.grid_columnconfigure(1, weight=1)
        
        ttk.Button(file_frame, text="📁 Upload Excel File", command=self._upload_file, style='Header.TButton').grid(row=0, column=0)
        self.file_label = ttk.Label(file_frame, text="No file loaded", foreground='#7f8c8d', font=('Segoe UI', 9, 'italic'))
        self.file_label.grid(row=0, column=1, sticky='w', padx=(15, 0))

        # Row 3: Generation and Upload controls
        action_frame = ttk.Frame(control_frame)
        action_frame.grid(row=3, column=0, columnspan=5, sticky='ew', pady=(10, 5))
        
        ttk.Button(action_frame, text="⚡ Generate All Content", command=self._generate_all, style='Header.TButton').grid(row=0, column=0, padx=(0, 10))
        ttk.Button(action_frame, text="🚀 Upload All Posts", command=self._upload_all_generated, style='Header.TButton').grid(row=0, column=1, padx=(0, 10))
        ttk.Button(action_frame, text="⏹️ Stop Upload", command=self._stop_uploading, style='Action.TButton').grid(row=0, column=2, padx=(0, 20))
        
        # Progress and status
        self.progress = ttk.Progressbar(action_frame, mode='indeterminate', length=200)
        self.progress.grid(row=0, column=3, padx=(0, 10))
        
        self.status_label = ttk.Label(action_frame, text="Ready", foreground='#27ae60', font=('Segoe UI', 9, 'bold'))
        self.status_label.grid(row=0, column=4)

    def _build_cards_area(self, parent):
        # Cards area with improved styling
        cards_frame = ttk.LabelFrame(parent, text="Generated Content Posts", padding=5)
        cards_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas for scrolling
        self.canvas = tk.Canvas(cards_frame, bg='#ffffff', highlightthickness=0)
        vsb = ttk.Scrollbar(cards_frame, orient='vertical', command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)
        
        self.inner.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.create_window((0,0), window=self.inner, anchor='nw')
        self.canvas.configure(yscrollcommand=vsb.set)
        
        self.canvas.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        self.canvas.bind_all('<MouseWheel>', lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), 'units'))

    def _build_logs_panel(self, parent):
        # Configure logs panel width
        parent.configure(width=350)
        parent.pack_propagate(False)
        
        # Logs header with controls
        logs_header = ttk.Frame(parent)
        logs_header.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(logs_header, text="📋 Real-time Activity", font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT)
        ttk.Button(logs_header, text="Clear", command=self._clear_logs, style='Action.TButton').pack(side=tk.RIGHT)
        
        # Logs text area
        self.logs_text = scrolledtext.ScrolledText(
            parent, 
            height=40, 
            width=45, 
            wrap=tk.WORD,
            font=('Consolas', 8),
            bg='#2c3e50',
            fg='#ecf0f1',
            insertbackground='#ecf0f1'
        )
        self.logs_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for different log levels
        self.logs_text.tag_configure('INFO', foreground='#3498db')
        self.logs_text.tag_configure('SUCCESS', foreground='#2ecc71')
        self.logs_text.tag_configure('WARNING', foreground='#f39c12')
        self.logs_text.tag_configure('ERROR', foreground='#e74c3c')
        self.logs_text.tag_configure('TIMESTAMP', foreground='#95a5a6', font=('Consolas', 7))

    def _add_log(self, message, level="INFO"):
        """Add a log entry with timestamp and color coding"""
        if not hasattr(self, 'logs_text'):
            return
            
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Insert timestamp
        self.logs_text.insert(tk.END, f"[{timestamp}] ", 'TIMESTAMP')
        
        # Insert level indicator
        level_indicators = {
            'INFO': 'ℹ️',
            'SUCCESS': '✅',
            'WARNING': '⚠️',
            'ERROR': '❌'
        }
        
        indicator = level_indicators.get(level, 'ℹ️')
        self.logs_text.insert(tk.END, f"{indicator} ", level)
        
        # Insert message
        self.logs_text.insert(tk.END, f"{message}\n", level)
        
        # Auto-scroll to bottom
        self.logs_text.see(tk.END)
        
        # Limit log entries to prevent memory issues
        lines = self.logs_text.get('1.0', tk.END).split('\n')
        if len(lines) > 500:
            # Remove oldest entries
            self.logs_text.delete('1.0', f'{len(lines)-400}.0')

    def _clear_logs(self):
        """Clear all log entries"""
        if hasattr(self, 'logs_text'):
            self.logs_text.delete('1.0', tk.END)
            self._add_log("Logs cleared", "INFO")

    def _log_and_status(self, message):
        """Update both status label and add to logs"""
        self._set_status(message)
        
        # Determine log level based on message content
        level = "INFO"
        if any(word in message.lower() for word in ['error', 'failed', 'exception']):
            level = "ERROR"
        elif any(word in message.lower() for word in ['warning', 'timeout', 'skip']):
            level = "WARNING"
        elif any(word in message.lower() for word in ['success', 'complete', 'uploaded', 'shared']):
            level = "SUCCESS"
            
        self._add_log(message, level)

    # STATUS
    def _set_status(self, msg):
        self.root.after(0, lambda m=msg: self.status_label.config(text=m))

    # API
    def _set_api_key(self):
        key = self.api_entry.get().strip()
        if not key:
            messagebox.showwarning("API", "Enter API key")
            self._add_log("API key setup failed - No key entered", "WARNING")
            return
        if genai is None:
            messagebox.showerror("Dependency", "google-generativeai not installed")
            self._add_log("API key setup failed - google-generativeai not installed", "ERROR")
            return
        try:
            genai.configure(api_key=key)
            self.gemini_api_key = key
            messagebox.showinfo("API", "API key set")
            self._add_log("Gemini API key configured successfully", "SUCCESS")
        except Exception as e:
            messagebox.showerror("API", f"Failed: {e}")
            self._add_log(f"API key setup failed: {e}", "ERROR")

    # FILE
    def _upload_file(self):
        if pd is None:
            messagebox.showerror("Dependency", "pandas not installed")
            self._add_log("File upload failed - pandas not installed", "ERROR")
            return
        path = filedialog.askopenfilename(title="Select Excel", filetypes=[("Excel","*.xlsx *.xls")])
        if not path: 
            self._add_log("File upload cancelled by user", "INFO")
            return
        try:
            self._add_log(f"Loading Excel file: {os.path.basename(path)}", "INFO")
            self.data = pd.read_excel(path)
            self.file_label.config(text=f"Loaded {os.path.basename(path)} ({len(self.data)} rows)")
            self._add_log(f"Excel file loaded successfully - {len(self.data)} rows found", "SUCCESS")
            self._build_cards()
            self._add_log(f"Created {len(self.cards)} content cards", "INFO")
        except Exception as e:
            messagebox.showerror("File", f"Failed to read: {e}")
            self._add_log(f"File loading failed: {e}", "ERROR")

    # CARDS
    def _build_cards(self):
        for w in self.inner.winfo_children(): w.destroy()
        self.cards.clear()
        if self.data is None: return
        for idx, row in self.data.iterrows():
            card = ttk.LabelFrame(self.inner, text=f"Post #{idx+1}", padding=10)
            card.grid(row=idx, column=0, sticky='we', padx=5, pady=5)
            card.grid_columnconfigure(0, weight=1)
            # Info
            info = (
                f"Brand: {row.get('brand_name','')}\n"
                f"Platform: {row.get('platform_type','')}\n"
                f"Font: {row.get('font_style','')}\n"
                f"Content: {str(row.get('content',''))[:100]}...\n"
                f"Phone: {row.get('phone_number','')}  Email: {row.get('email_id','')}\n"
            )
            ttk.Label(card, text=info, justify='left').pack(anchor='w')

            # Caption box
            cap_label = ttk.Label(card, text="Generated Caption:")
            cap_label.pack(anchor='w', pady=(5,0))
            cap_box = scrolledtext.ScrolledText(card, height=5, width=80, wrap=tk.WORD)
            cap_box.pack(fill='x', pady=2)

            # Image preview
            img_label = ttk.Label(card, text="(No image)", relief=tk.SUNKEN, width=40)
            img_label.pack(pady=4)

            # Buttons row
            btn_frame = ttk.Frame(card)
            btn_frame.pack(fill='x', pady=2)
            ttk.Button(btn_frame, text="Generate", command=lambda i=idx: self._generate_single(i)).pack(side='left', padx=2)
            ttk.Button(btn_frame, text="Upload This", command=lambda i=idx: self._upload_single(i)).pack(side='left', padx=2)

            # Store refs
            card.data = row
            card.index = idx
            card.caption_widget = cap_box
            card.image_widget = img_label
            card.generated_image_path = None
            self.cards.append(card)

    # GENERATION
    def _generate_all(self):
        if not self.gemini_api_key:
            messagebox.showwarning("Generate", "Set API key first")
            self._add_log("Generation failed - API key not set", "WARNING")
            return
        if not self.cards:
            messagebox.showwarning("Generate", "Load data first")
            self._add_log("Generation failed - No data loaded", "WARNING")
            return
        self._add_log(f"Starting generation for {len(self.cards)} posts", "INFO")
        self.progress.start()
        threading.Thread(target=self._generate_all_worker, daemon=True).start()

    def _generate_all_worker(self):
        for i, card in enumerate(self.cards):
            self._add_log(f"Generating content for post {i+1}/{len(self.cards)}", "INFO")
            self._generate_for_card(card)
        self.root.after(0, self.progress.stop)
        self._set_status("Generation complete")
        self._add_log("All content generation completed successfully", "SUCCESS")
        messagebox.showinfo("Generate", "All captions generated")

    def _generate_single(self, idx):
        if idx >= len(self.cards): return
        if not self.gemini_api_key:
            messagebox.showwarning("Generate", "Set API key first")
            self._add_log(f"Generation failed for post {idx+1} - API key not set", "WARNING")
            return
        self._add_log(f"Starting generation for post {idx+1}", "INFO")
        self.progress.start()
        threading.Thread(target=lambda: self._generate_single_worker(idx), daemon=True).start()

    def _generate_single_worker(self, idx):
        self._generate_for_card(self.cards[idx])
        self.root.after(0, self.progress.stop)
        self._set_status(f"Post {idx+1} generated")
        self._add_log(f"Content generation completed for post {idx+1}", "SUCCESS")

    def _generate_for_card(self, card):
        data = card.data
        idx = card.index
        try:
            model = genai.GenerativeModel('gemini-2.0-flash-exp') if genai else None
            if not model:
                raise RuntimeError("Gemini SDK missing")
            prompt = f"""You are a social media copywriter. Create ONE engaging caption.\nBrand: {data.get('brand_name','')}\nPlatform: {data.get('platform_type','Instagram')}\nTheme: {data.get('content','')}\nContext: {data.get('prompt','')}\nPhone: {data.get('phone_number','')} Email: {data.get('email_id','')}\nRules: Hook first line, <=150 words, 5-8 relevant hashtags end, CTA, premium tone.\nReturn only caption."""
            resp = model.generate_content(prompt)
            caption = (resp.text or '').strip() if resp else 'Generation failed'
            self._add_log(f"Caption generated for post {idx+1} (Brand: {data.get('brand_name', 'Unknown')})", "SUCCESS")
        except Exception as e:
            caption = f"Generation failed: {e}"[:500]
            self._add_log(f"Caption generation failed for post {idx+1}: {e}", "ERROR")
        self.root.after(0, lambda c=caption: self._set_caption(card, c))
        # Placeholder image creation
        try:
            img = self._create_placeholder_image(data)
            path = self._save_temp_image(img, f"generated_{idx+1}")
            card.generated_image_path = path
            self.root.after(0, lambda im=img, cd=card: self._update_image(cd, im))
            self._add_log(f"Placeholder image created for post {idx+1}", "INFO")
        except Exception as e:
            self._add_log(f"Image creation failed for post {idx+1}: {e}", "WARNING")
        # Store export record
        entry = { **data.to_dict(), 'generated_caption': caption, 'generated_image_path': getattr(card, 'generated_image_path', None), 'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S') }
        if len(self.generated_data) <= idx:
            self.generated_data.extend([None] * (idx + 1 - len(self.generated_data)))
        self.generated_data[idx] = entry

    def _set_caption(self, card, caption):
        if hasattr(card, 'caption_widget'):
            card.caption_widget.delete('1.0', tk.END)
            card.caption_widget.insert(tk.END, caption)

    def _create_placeholder_image(self, data):
        if Image is None:
            return None
        W,H = 800,800
        img = Image.new('RGB',(W,H),(245,245,245))
        d = ImageDraw.Draw(img)
        try:
            f_big = ImageFont.truetype('arial.ttf', 42)
            f_med = ImageFont.truetype('arial.ttf', 28)
        except Exception:
            f_big = f_med = ImageFont.load_default()
        brand = str(data.get('brand_name','Brand'))[:30]
        content = str(data.get('content','Content'))[:80]
        d.text((W//2, H//3), brand, fill=(20,20,20), font=f_big, anchor='mm')
        d.text((W//2, H//2), content, fill=(40,40,40), font=f_med, anchor='mm', spacing=4)
        return img

    def _save_temp_image(self, image, prefix):
        if image is None: return None
        os.makedirs('temp_images', exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        path = os.path.join('temp_images', f"{prefix}_{ts}.png")
        image.save(path, 'PNG')
        return path

    def _update_image(self, card, image):
        if image is None or ImageTk is None: return
        copy = image.copy(); copy.thumbnail((300,200))
        ph = ImageTk.PhotoImage(copy)
        card.image_widget.configure(image=ph, text='')
        card.image_widget._image_ref = ph

    # INSTAGRAM LOGIN
    def _login_instagram(self):
        if not self.uploader or not self.uploader.driver:
            messagebox.showerror("Upload", "Browser not available")
            self._add_log("Instagram login failed - Browser not available", "ERROR")
            return
        user = self.user_entry.get().strip()
        pwd = self.pass_entry.get().strip()
        if not user or not pwd:
            messagebox.showwarning("Login", "Enter username and password")
            self._add_log("Instagram login failed - Missing credentials", "WARNING")
            return
        self._add_log(f"Attempting Instagram login for user: {user}", "INFO")
        threading.Thread(target=lambda: self._do_login(user, pwd), daemon=True).start()

    def _do_login(self, u, p):
        ok = self.uploader.login(u, p)
        if ok:
            self._set_status("Logged in")
            self._add_log(f"Successfully logged into Instagram as {u}", "SUCCESS")
        else:
            self._set_status("Login failed")
            self._add_log(f"Instagram login failed for user {u}", "ERROR")

    # UPLOAD SINGLE
    def _upload_single(self, idx):
        if idx >= len(self.cards): return
        if not self.uploader or not self.uploader.driver:
            messagebox.showerror("Upload", "Browser not ready / login first")
            self._add_log(f"Upload failed for post {idx+1} - Browser not ready", "ERROR")
            return
        card = self.cards[idx]
        caption = card.caption_widget.get('1.0', tk.END).strip()
        if not caption:
            messagebox.showwarning("Upload", "Generate caption first")
            self._add_log(f"Upload skipped for post {idx+1} - No caption", "WARNING")
            return
        image_path = card.generated_image_path or ''
        if not image_path or not os.path.exists(image_path):
            messagebox.showwarning("Upload", "Generated image missing")
            self._add_log(f"Upload skipped for post {idx+1} - Missing image", "WARNING")
            return
        self._add_log(f"Starting upload for post {idx+1}", "INFO")
        self.progress.start()
        threading.Thread(target=lambda: self._upload_single_worker(card, image_path, caption), daemon=True).start()

    def _upload_single_worker(self, card, image_path, caption):
        self.uploader.reset_stop()
        success, msg = self.uploader.upload_post(image_path, caption)
        self.root.after(0, self.progress.stop)
        self._set_status(f"Post {card.index+1}: {msg}")
        if success:
            self._add_log(f"Post {card.index+1} uploaded successfully", "SUCCESS")
            messagebox.showinfo("Upload", f"Post {card.index+1} uploaded")
        else:
            self._add_log(f"Post {card.index+1} upload failed: {msg}", "ERROR")
            messagebox.showerror("Upload", f"Post {card.index+1} failed: {msg}")

    # UPLOAD ALL
    def _upload_all_generated(self):
        if not self.cards:
            messagebox.showwarning("Upload", "No posts")
            self._add_log("Batch upload failed - No posts available", "WARNING")
            return
        if not self.uploader or not self.uploader.driver:
            messagebox.showerror("Upload", "Browser not ready / login first")
            self._add_log("Batch upload failed - Browser not ready", "ERROR")
            return
        self.uploader.reset_stop()
        if self.upload_thread and self.upload_thread.is_alive():
            messagebox.showinfo("Upload", "Upload already running")
            self._add_log("Batch upload skipped - Already in progress", "INFO")
            return
        self._add_log(f"Starting batch upload for {len(self.cards)} posts", "INFO")
        self.progress.start()
        self.upload_thread = threading.Thread(target=self._upload_all_worker, daemon=True)
        self.upload_thread.start()

    def _upload_all_worker(self):
        uploaded_count = 0
        skipped_count = 0
        
        for card in self.cards:
            if self.uploader.stop_event.is_set():
                self._add_log("Batch upload stopped by user", "WARNING")
                break
                
            caption = card.caption_widget.get('1.0', tk.END).strip()
            if not caption:
                self._add_log(f"Skipping post {card.index+1} - No caption", "WARNING")
                skipped_count += 1
                continue
                
            img_path = card.generated_image_path
            if not img_path or not os.path.exists(img_path):
                self._add_log(f"Skipping post {card.index+1} - No image", "WARNING")
                skipped_count += 1
                continue
                
            success, msg = self.uploader.upload_post(img_path, caption)
            if success:
                uploaded_count += 1
                self._add_log(f"Post {card.index+1} uploaded successfully", "SUCCESS")
            else:
                self._add_log(f"Post {card.index+1} failed: {msg}", "ERROR")
            
            # Brief delay between posts
            for _ in range(5):
                if self.uploader.stop_event.is_set():
                    break
                time.sleep(1)
            if self.uploader.stop_event.is_set():
                break
                
        self.root.after(0, self.progress.stop)
        
        if self.uploader.stop_event.is_set():
            self._add_log(f"Batch upload stopped - {uploaded_count} uploaded, {skipped_count} skipped", "WARNING")
        else:
            self._add_log(f"Batch upload complete - {uploaded_count} uploaded, {skipped_count} skipped", "SUCCESS")
            messagebox.showinfo("Upload", f"Batch upload complete!\nUploaded: {uploaded_count}\nSkipped: {skipped_count}")

    def _stop_uploading(self):
        if self.uploader:
            self.uploader.stop()
            self._add_log("Upload stop requested", "INFO")

    # CLEANUP
    def _on_close(self):
        try:
            if self.uploader:
                self.uploader.close()
        except Exception:
            pass
        self.root.destroy()

# ENTRY POINT

def main():
    root = tk.Tk()
    # Basic styling
    style = ttk.Style()
    try:
        style.theme_use('clam')
    except Exception:
        pass
    style.configure('TButton', padding=4)
    app = SocialMediaGeneratorV4(root)
    root.mainloop()

if __name__ == '__main__':
    main()
