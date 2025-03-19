# app/ui/creation_tab.py

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import logging
import os
import random
import string
import time
from datetime import datetime
import calendar
from PIL import Image, ImageTk

class CreationTab(ttk.Frame):
    """Tab for creating new Instagram accounts"""
    
    def __init__(self, parent, account_creator):
        super().__init__(parent)
        self.account_creator = account_creator
        self.logger = logging.getLogger(__name__)
        
        # Create scrollable frame first
        self.canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        # Initialize all variables first
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar()
        self.username_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.temp_email_var = tk.BooleanVar(value=False)
        self.fullname_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.show_password_var = tk.BooleanVar(value=False)
        self.phone_var = tk.StringVar()
        self.month_var = tk.StringVar()
        self.day_var = tk.StringVar()
        self.year_var = tk.StringVar()
        self.gender_var = tk.StringVar(value="Female")
        self.profile_pic_var = tk.StringVar()
        self.bio_char_count_var = tk.StringVar(value="0/150")
        self.use_proxy_var = tk.BooleanVar(value=False)
        self.proxy_type_var = tk.StringVar(value="http")
        self.proxy_ip_var = tk.StringVar()
        self.proxy_port_var = tk.StringVar()
        self.proxy_username_var = tk.StringVar()
        self.proxy_password_var = tk.StringVar()
        # Set callbacks
        self.account_creator.set_callbacks(
            progress_callback=self.update_progress,
            status_callback=self.update_status
        )
        
        # Initialize variables
        self.running = False
        self.current_thread = None
        
        # Load default profile picture if available
        self.default_profile_pic = os.path.join(os.path.dirname(__file__), "..", "resources", "default_profile.jpg")
        if not os.path.exists(self.default_profile_pic):
            self.default_profile_pic = None
        
        # Setup sections
        self.setup_account_details_frame()
        self.setup_profile_settings_frame()
        self.setup_proxy_frame()
        self.setup_log_area()
        self.setup_control_frame()
    
    def setup_account_details_frame(self):
        """Setup the account details input section"""
        details_frame = ttk.LabelFrame(self.scrollable_frame, text="Account Details")
        details_frame.pack(fill='x', padx=5, pady=5)
        
        # Username section
        username_frame = ttk.Frame(details_frame)
        username_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(username_frame, text="Username:").pack(side='left')
        self.username_var = tk.StringVar()
        ttk.Entry(username_frame, textvariable=self.username_var, width=20).pack(side='left', padx=5)
        
        ttk.Button(username_frame, text="Check Availability", 
                   command=self.check_username).pack(side='left', padx=5)
        
        ttk.Button(username_frame, text="Generate", 
                   command=self.generate_username).pack(side='left')
        
        # Email field
        email_frame = ttk.Frame(details_frame)
        email_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(email_frame, text="Email:").pack(side='left')
        self.email_var = tk.StringVar()
        ttk.Entry(email_frame, textvariable=self.email_var, width=30).pack(side='left', padx=5, fill='x', expand=True)
        
        self.temp_email_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(email_frame, text="Use Temp Email", variable=self.temp_email_var,
                        command=self.toggle_temp_email).pack(side='left')
        
        # Full name field
        fullname_frame = ttk.Frame(details_frame)
        fullname_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(fullname_frame, text="Full Name:").pack(side='left')
        self.fullname_var = tk.StringVar()
        ttk.Entry(fullname_frame, textvariable=self.fullname_var).pack(side='left', padx=5, fill='x', expand=True)
        
        # Password field
        password_frame = ttk.Frame(details_frame)
        password_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(password_frame, text="Password:").pack(side='left')
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(password_frame, textvariable=self.password_var, show="*")
        self.password_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        ttk.Button(password_frame, text="Generate", 
                   command=self.generate_password).pack(side='left')
        
        self.show_password_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(password_frame, text="Show", variable=self.show_password_var,
                       command=self.toggle_password_visibility).pack(side='left')
        
        # Phone field
        phone_frame = ttk.Frame(details_frame)
        phone_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(phone_frame, text="Phone (optional):").pack(side='left')
        self.phone_var = tk.StringVar()
        ttk.Entry(phone_frame, textvariable=self.phone_var).pack(side='left', padx=5, fill='x', expand=True)
        
        # Date of birth section
        dob_frame = ttk.Frame(details_frame)
        dob_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(dob_frame, text="Date of Birth:").pack(side='left')
        
        # Month dropdown
        self.month_var = tk.StringVar()
        months = [(str(i), calendar.month_name[i]) for i in range(1, 13)]
        month_menu = ttk.Combobox(dob_frame, textvariable=self.month_var, values=[m[1] for m in months], width=10)
        month_menu.pack(side='left', padx=2)
        month_menu.current(random.randint(0, 11))  # Random month
        
        # Day dropdown
        self.day_var = tk.StringVar()
        day_menu = ttk.Combobox(dob_frame, textvariable=self.day_var, values=list(range(1, 32)), width=5)
        day_menu.pack(side='left', padx=2)
        day_menu.current(random.randint(0, 27))  # Random day (avoiding month length issues)
        
        # Year dropdown
        self.year_var = tk.StringVar()
        current_year = datetime.now().year
        # Ages between 18 and 40
        years = list(range(current_year - 40, current_year - 18))
        year_menu = ttk.Combobox(dob_frame, textvariable=self.year_var, values=years, width=7)
        year_menu.pack(side='left', padx=2)
        year_menu.current(random.randint(0, len(years) - 1))  # Random adult age
        
        # Gender selection
        gender_frame = ttk.Frame(details_frame)
        gender_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(gender_frame, text="Gender:").pack(side='left')
        
        self.gender_var = tk.StringVar(value="Female")
        ttk.Radiobutton(gender_frame, text="Female", variable=self.gender_var, value="Female").pack(side='left', padx=5)
        ttk.Radiobutton(gender_frame, text="Male", variable=self.gender_var, value="Male").pack(side='left', padx=5)
        ttk.Radiobutton(gender_frame, text="Custom", variable=self.gender_var, value="Custom").pack(side='left', padx=5)
    
    def setup_profile_settings_frame(self):
        """Setup profile settings section"""
        profile_frame = ttk.LabelFrame(self.scrollable_frame, text="Profile Settings")
        profile_frame.pack(fill='x', padx=5, pady=5)
        
        # Profile picture
        pic_frame = ttk.Frame(profile_frame)
        pic_frame.pack(fill='x', padx=5, pady=5)
        
        # Preview frame
        preview_frame = ttk.Frame(pic_frame)
        preview_frame.pack(side='left', padx=5)
        
        # Placeholder for image preview
        self.preview_canvas = tk.Canvas(preview_frame, width=80, height=80, bg='lightgray')
        self.preview_canvas.pack(side='top')
        
        # Profile picture selection
        pic_select_frame = ttk.Frame(pic_frame)
        pic_select_frame.pack(side='left', fill='x', expand=True, padx=5)
        
        ttk.Label(pic_select_frame, text="Profile Picture:").pack(side='top', anchor='w')
        
        pic_path_frame = ttk.Frame(pic_select_frame)
        pic_path_frame.pack(side='top', fill='x', expand=True, pady=2)
        
        self.profile_pic_var = tk.StringVar()
        ttk.Entry(pic_path_frame, textvariable=self.profile_pic_var).pack(side='left', fill='x', expand=True)
        
        ttk.Button(pic_path_frame, text="Browse", 
                  command=self.browse_profile_pic).pack(side='left', padx=5)
        
        ttk.Button(pic_path_frame, text="Default", 
                  command=self.use_default_pic).pack(side='left')
        
        ttk.Button(pic_path_frame, text="Random", 
                  command=self.generate_random_pic).pack(side='left', padx=5)
        
        # Bio section
        bio_frame = ttk.Frame(profile_frame)
        bio_frame.pack(fill='x', padx=5, pady=5)
        
        bio_label_frame = ttk.Frame(bio_frame)
        bio_label_frame.pack(side='top', fill='x')
        
        ttk.Label(bio_label_frame, text="Bio:").pack(side='left')
        
        ttk.Label(bio_label_frame, text="Max 150 characters", 
                 font=("", 8)).pack(side='right')
        
        self.bio_text = tk.Text(bio_frame, height=3, width=40)
        self.bio_text.pack(side='top', fill='x', expand=True, pady=2)
        
        bio_buttons_frame = ttk.Frame(bio_frame)
        bio_buttons_frame.pack(side='top', fill='x')
        
        ttk.Button(bio_buttons_frame, text="Generate Bio", 
                  command=self.generate_bio).pack(side='left')
        
        ttk.Button(bio_buttons_frame, text="Clear", 
                  command=lambda: self.bio_text.delete('1.0', tk.END)).pack(side='left', padx=5)
        
        self.bio_char_count_var = tk.StringVar(value="0/150")
        ttk.Label(bio_buttons_frame, textvariable=self.bio_char_count_var).pack(side='right')
        
        # Bind text change to update character count
        self.bio_text.bind("<KeyRelease>", self.update_char_count)
    
    def setup_proxy_frame(self):
        """Setup proxy settings section"""
        proxy_frame = ttk.LabelFrame(self.scrollable_frame, text="Proxy Settings")
        proxy_frame.pack(fill='x', padx=5, pady=5)
        
        # Use proxy checkbox
        proxy_check_frame = ttk.Frame(proxy_frame)
        proxy_check_frame.pack(fill='x', padx=5, pady=5)
        
        self.use_proxy_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(proxy_check_frame, text="Use Proxy", 
                        variable=self.use_proxy_var,
                        command=self.toggle_proxy_fields).pack(side='left')
        
        proxy_help_text = "Using proxies helps avoid IP blocks and increases success rates"
        ttk.Label(proxy_check_frame, text=proxy_help_text, 
                 font=("", 8), foreground="gray").pack(side='left', padx=10)
        
        # Proxy type
        proxy_type_frame = ttk.Frame(proxy_frame)
        proxy_type_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(proxy_type_frame, text="Type:").pack(side='left')
        
        self.proxy_type_var = tk.StringVar(value="http")
        proxy_type_menu = ttk.Combobox(proxy_type_frame, textvariable=self.proxy_type_var, 
                                      values=["http", "https", "socks4", "socks5"], 
                                      state='disabled', width=8)
        proxy_type_menu.pack(side='left', padx=5)
        self.proxy_type_menu = proxy_type_menu
        
        # IP and Port
        proxy_address_frame = ttk.Frame(proxy_frame)
        proxy_address_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(proxy_address_frame, text="IP:").pack(side='left')
        self.proxy_ip_var = tk.StringVar()
        self.proxy_ip_entry = ttk.Entry(proxy_address_frame, textvariable=self.proxy_ip_var, state='disabled')
        self.proxy_ip_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        ttk.Label(proxy_address_frame, text="Port:").pack(side='left')
        self.proxy_port_var = tk.StringVar()
        self.proxy_port_entry = ttk.Entry(proxy_address_frame, textvariable=self.proxy_port_var, 
                                         width=6, state='disabled')
        self.proxy_port_entry.pack(side='left', padx=5)
        
        # Username and Password
        proxy_auth_frame = ttk.Frame(proxy_frame)
        proxy_auth_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(proxy_auth_frame, text="Username:").pack(side='left')
        self.proxy_username_var = tk.StringVar()
        self.proxy_username_entry = ttk.Entry(proxy_auth_frame, textvariable=self.proxy_username_var, state='disabled')
        self.proxy_username_entry.pack(side='left', padx=5, fill='x', expand=True)
        
        ttk.Label(proxy_auth_frame, text="Password:").pack(side='left')
        self.proxy_password_var = tk.StringVar()
        self.proxy_password_entry = ttk.Entry(proxy_auth_frame, textvariable=self.proxy_password_var, 
                                            show="*", state='disabled')
        self.proxy_password_entry.pack(side='left', padx=5, fill='x', expand=True)
    
    def setup_log_area(self):
        """Setup log and status area"""
        log_frame = ttk.LabelFrame(self.scrollable_frame, text="Status")
        log_frame.pack(fill='x', padx=5, pady=5)  # Change to fill='x' instead of 'both'
        
        # Add a toggle button
        self.log_expanded = tk.BooleanVar(value=False)
        ttk.Checkbutton(log_frame, text="Show Log", variable=self.log_expanded, 
                    command=self.toggle_log_visibility).pack(anchor='w')
        
        # Status label and progress bar as before
        # ...
        
        # Log text in a separate frame that can be hidden
        self.log_container = ttk.Frame(log_frame)
        self.log_container.pack(fill='both', expand=True, padx=5, pady=5)
        self.log_container.pack_forget()  # Initially hidden
        
        self.log_text = scrolledtext.ScrolledText(self.log_container, height=8)
        self.log_text.pack(fill='both', expand=True)
        self.log_text.config(state='disabled')

    def toggle_log_visibility(self):
        """Toggle log area visibility"""
        if self.log_expanded.get():
            self.log_container.pack(fill='both', expand=True, padx=5, pady=5)
        else:
            self.log_container.pack_forget()
        
    def setup_control_frame(self):
        """Setup control buttons"""
        control_frame = ttk.Frame(self.scrollable_frame)
        control_frame.pack(fill='x', padx=5, pady=10)
        
        # Start button
        self.start_button = ttk.Button(
            control_frame,
            text="Create Account",
            command=self.start_creation
        )
        self.start_button.pack(side='left', padx=5)
        
        # Reset button
        ttk.Button(
            control_frame,
            text="Reset Form",
            command=self.reset_form
        ).pack(side='left', padx=5)
        
        # Stats button
        ttk.Button(
            control_frame,
            text="View Stats",
            command=self.show_stats
        ).pack(side='left', padx=5)
        
        # Verification button for handling manual verification
        self.verification_button = ttk.Button(
            control_frame,
            text="Manual Verification",
            command=self.show_verification_dialog,
            state='disabled'
        )
        self.verification_button.pack(side='right', padx=5)
        
        # Batch creation button
        self.batch_button = ttk.Button(
            control_frame,
            text="Batch Creation",
            command=self.show_batch_dialog
        )
        self.batch_button.pack(side='right', padx=5)
    
    def log_message(self, message):
        """Add message to log area"""
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
    
    def update_status(self, message):
        """Update status label and log"""
        self.status_var.set(message)
        self.log_message(message)
    
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_var.set(value)
        self.update_idletasks()
    
    def toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")
    
    def toggle_proxy_fields(self):
        """Enable/disable proxy fields based on checkbox"""
        state = 'normal' if self.use_proxy_var.get() else 'disabled'
        
        self.proxy_type_menu.config(state=state)
        self.proxy_ip_entry.config(state=state)
        self.proxy_port_entry.config(state=state)
        self.proxy_username_entry.config(state=state)
        self.proxy_password_entry.config(state=state)
    
    def toggle_temp_email(self):
        """Handle temp email checkbox change"""
        if self.temp_email_var.get():
            # Remember old email if user entered one
            self.old_email = self.email_var.get()
            
            # Set a placeholder
            self.email_var.set("[Will generate temp email]")
            self.update_status("Will use temporary email for registration")
        else:
            # Restore old email if there was one
            if hasattr(self, 'old_email'):
                self.email_var.set(self.old_email)
            else:
                self.email_var.set("")
    
    def update_char_count(self, event=None):
        """Update bio character count"""
        text = self.bio_text.get("1.0", tk.END)
        count = len(text.strip())
        self.bio_char_count_var.set(f"{count}/150")
        
        # Highlight in red if over limit
        if count > 150:
            self.bio_char_count_var.set(f"{count}/150 (Too long!)")
    
    def browse_profile_pic(self):
        """Open file browser to select profile picture"""
        file_path = filedialog.askopenfilename(
            title="Select Profile Picture",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png")]
        )
        
        if file_path:
            self.profile_pic_var.set(file_path)
            self.update_status(f"Selected profile picture: {os.path.basename(file_path)}")
            self.show_image_preview(file_path)
    
    def use_default_pic(self):
        """Use default profile picture"""
        if self.default_profile_pic and os.path.exists(self.default_profile_pic):
            self.profile_pic_var.set(self.default_profile_pic)
            self.update_status(f"Using default profile picture")
            self.show_image_preview(self.default_profile_pic)
        else:
            messagebox.showinfo("Info", "No default profile picture available")
    
    def generate_random_pic(self):
        """Generate a random profile picture (placeholder)"""
        # This would typically connect to an API to generate an avatar
        # For now, we'll just use the default
        self.use_default_pic()
        self.update_status("Random profile picture generation not implemented yet")
    
    def show_image_preview(self, image_path):
        """Show image preview in canvas"""
        try:
            # Open image file
            img = Image.open(image_path)
            
            # Resize to fit canvas
            img = img.resize((80, 80), Image.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # Save reference (to prevent garbage collection)
            self.photo_image = photo
            
            # Clear canvas and display image
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(40, 40, image=photo)
            
        except Exception as e:
            self.logger.error(f"Error displaying image preview: {str(e)}")
            # Clear canvas and show error
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(40, 40, text="Error", fill="red")
    
    def generate_username(self):
        """Generate a username based on fullname or random if not available"""
        fullname = self.fullname_var.get().strip()
        
        if not fullname:
            # Generate a completely random username
            random_username = ''.join(random.choices(string.ascii_lowercase, k=5)) + \
                             ''.join(random.choices(string.digits, k=3))
            self.username_var.set(random_username)
            self.update_status(f"Generated random username: {random_username}")
            return
        
        # Generate username from fullname
        suggestions = self.account_creator.generate_username(
            fullname,
            prefix=random.choice(['', 'the', 'real', 'its']),
            suffix=random.choice(['', str(random.randint(1, 999)), 
                                 random.choice(['photo', 'pics', 'gram', 'official'])])
        )
        
        # Set the first suggestion
        if suggestions:
            self.username_var.set(suggestions[0])
            self.update_status(f"Generated username from name: {suggestions[0]}")
            
            # Show other suggestions
            if len(suggestions) > 1:
                suggestions_str = "\n".join(suggestions[1:5])
                self.log_message(f"Other username suggestions:\n{suggestions_str}")
    
    def generate_password(self):
        """Generate a strong random password"""
        length = 12
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(random.choice(chars) for _ in range(length))
        
        self.password_var.set(password)
        self.update_status(f"Generated strong password")
    
    def generate_bio(self):
        """Generate a random bio based on interests"""
        # Generate a simple bio
        fullname = self.fullname_var.get().strip()
        
        # List of templates
        templates = [
            "Hi, I'm {name}! {interest} enthusiast | {hobby} lover",
            "{name} | {interest} | {hobby} | {location}",
            "{interest} & {hobby} | {emoji} {name} {emoji}",
            "Just a {adjective} person who loves {interest} and {hobby}",
            "{emoji} {interest} | {hobby} | {name}"
        ]
        
        # Random data
        interests = ["photography", "art", "travel", "music", "fashion", "food", "fitness", "nature", "tech", "books"]
        hobbies = ["hiking", "cooking", "reading", "dancing", "yoga", "running", "gaming", "painting", "writing", "surfing"]
        locations = ["NYC", "LA", "London", "Tokyo", "Paris", "Sydney", "Berlin", "Toronto", "Miami", "Barcelona"]
        adjectives = ["creative", "adventurous", "passionate", "curious", "happy", "inspired", "motivated", "positive", "friendly", "chill"]
        emojis = ["✨", "🌟", "🌈", "🌺", "🌹", "🌻", "🌞", "🌊", "🔥", "🦋", "🎵", "📷", "🎨", "✈️", "💫"]
        
        # Choose a template and fill it
        template = random.choice(templates)
        
        # Use name if provided, otherwise "me"
        name = fullname.split()[0] if fullname else "me"
        
        # Fill in the template
        bio = template.format(
            name=name,
            interest=random.choice(interests),
            hobby=random.choice(hobbies),
            location=random.choice(locations),
            adjective=random.choice(adjectives),
            emoji=random.choice(emojis)
        )
        
        # Set the bio
        self.bio_text.delete("1.0", tk.END)
        self.bio_text.insert("1.0", bio)
        self.update_char_count()
        
        self.update_status(f"Generated random bio")
    
    def check_username(self):
        """Check if username is available on Instagram"""
        username = self.username_var.get().strip()
        
        if not username:
            messagebox.showerror("Error", "Please enter a username to check")
            return
        
        self.update_status(f"Checking availability for username: {username}")
        self.start_button.config(state='disabled')
        
        def check_thread():
            try:
                is_available = self.account_creator.check_username_available(username)
                
                # Update UI in main thread
                self.after(0, lambda: self._handle_username_check_result(username, is_available))
                
            except Exception as e:
                self.logger.error(f"Error checking username: {str(e)}")
                
                # Update UI in main thread
                self.after(0, lambda: self.update_status(f"Error checking username: {str(e)}"))
                self.after(0, lambda: self.start_button.config(state='normal'))
        
        # Start in separate thread
        threading.Thread(target=check_thread, daemon=True).start()
    
    def _handle_username_check_result(self, username, is_available):
        """Handle username availability check result"""
        if is_available:
            messagebox.showinfo("Username Check", f"Username '{username}' is available!")
            self.update_status(f"Username '{username}' is available")
        else:
            messagebox.showwarning("Username Check", f"Username '{username}' is not available. Please choose another.")
            self.update_status(f"Username '{username}' is not available")
        
        self.start_button.config(state='normal')
    
    def validate_form(self):
        """Validate form inputs before starting creation"""
        required_fields = {
            'Username': self.username_var.get().strip(),
            'Email': self.email_var.get().strip(),
            'Full Name': self.fullname_var.get().strip(),
            'Password': self.password_var.get().strip()
        }
        
        # Check required fields
        for field, value in required_fields.items():
            if not value or value == "[Will generate temp email]":
                messagebox.showerror("Error", f"{field} is required")
                return False
        
        # Validate email format if not using temp email
        if not self.temp_email_var.get():
            import re
            email_pattern = re.compile(r'[^@]+@[^@]+\.[^@]+')
            if not email_pattern.match(self.email_var.get()):
                messagebox.showerror("Error", "Invalid email format")
                return False
        
        # Validate password strength
        password = self.password_var.get()
        if len(password) < 8:
            messagebox.showerror("Error", "Password must be at least 8 characters long")
            return False
        
        # Validate proxy settings if enabled
        if self.use_proxy_var.get():
            if not self.proxy_ip_var.get() or not self.proxy_port_var.get():
                messagebox.showerror("Error", "Proxy IP and Port are required when using proxy")
                return False
            
            try:
                port = int(self.proxy_port_var.get())
                if port < 1 or port > 65535:
                    raise ValueError("Invalid port number")
            except ValueError:
                messagebox.showerror("Error", "Proxy port must be a valid number between 1-65535")
                return False
        
        # Check if bio is too long
        bio = self.bio_text.get("1.0", tk.END).strip()
        if len(bio) > 150:
            messagebox.showerror("Error", "Bio is too long (maximum 150 characters)")
            return False
        
        return True
    
    def start_creation(self):
        """Start account creation process"""
        if not self.validate_form():
            return
        
        if self.running:
            messagebox.showinfo("In Progress", "Account creation is already in progress")
            return
        
        # Disable controls
        self.start_button.config(state='disabled')
        self.running = True
        
        # Reset progress
        self.progress_var.set(0)
        self.update_status("Starting account creation...")
        
        # Gather form data
        account_data = {
            'username': self.username_var.get().strip(),
            'email': self.email_var.get().strip(),
            'fullname': self.fullname_var.get().strip(),
            'password': self.password_var.get().strip(),
            'phone': self.phone_var.get().strip() or None,
            'date_of_birth': (
                self.get_month_number(),
                int(self.day_var.get()),
                int(self.year_var.get())
            ),
            'gender': self.gender_var.get(),
            'profile_pic': self.profile_pic_var.get() or None,
            'bio': self.bio_text.get("1.0", tk.END).strip() or None
        }
        
        # Handle temp email
        if self.temp_email_var.get():
            # Generate temp email will be handled in the creation thread
            account_data['email'] = None
            account_data['use_temp_email'] = True
        
        # Configure proxy if enabled
        proxy = None
        if self.use_proxy_var.get():
            proxy = {
                'ip': self.proxy_ip_var.get(),
                'port': self.proxy_port_var.get(),
                'protocol': self.proxy_type_var.get(),
                'username': self.proxy_username_var.get() or None,
                'password': self.proxy_password_var.get() or None
            }
        
        def creation_thread():
            try:
                # Generate temp email if needed
                if account_data.get('use_temp_email'):
                    self.update_status("Generating temporary email...")
                    temp_email = self.account_creator.email_verifier.generate_temp_email()
                    
                    if not temp_email:
                        self.after(0, lambda: messagebox.showerror(
                            "Error", "Failed to generate temporary email. Please try again or use your own email."
                        ))
                        self.after(0, lambda: self.update_status("Failed to generate temporary email"))
                        self.after(0, lambda: self._reset_creation_state())
                        return
                    
                    account_data['email'] = temp_email
                    self.after(0, lambda: self.update_status(f"Using temporary email: {temp_email}"))
                
                # Add proxy to proxy pool if specified
                if proxy:
                    self.update_status(f"Using proxy: {proxy['ip']}:{proxy['port']}")
                    self.account_creator.proxy_manager.add_proxies([proxy])
                
                # Start account creation
                result = self.account_creator.create_account(**account_data)
                
                # Update UI in main thread
                self.after(0, lambda: self._handle_creation_result(result, account_data))
                
            except Exception as e:
                self.logger.error(f"Error during account creation: {str(e)}")
                
                # Update UI in main thread
                self.after(0, lambda: self.update_status(f"Error: {str(e)}"))
                self.after(0, lambda: messagebox.showerror("Error", f"Account creation failed: {str(e)}"))
                self.after(0, lambda: self._reset_creation_state())
        
        # Start in separate thread
        self.current_thread = threading.Thread(target=creation_thread, daemon=True)
        self.current_thread.start()
    
    def _handle_creation_result(self, result, account_data):
        """Handle account creation result"""
        if result['success']:
            messagebox.showinfo(
                "Success", 
                f"Account '{result['username']}' created successfully!"
            )
            self.update_status(f"Account '{result['username']}' created successfully!")
            
            # Log credentials
            self.log_message(f"Account created successfully:")
            self.log_message(f"Username: {result['username']}")
            self.log_message(f"Password: {account_data['password']}")
            self.log_message(f"Email: {account_data['email']}")
            
            # Reset form on success
            self.reset_form()
        else:
            error_msg = result.get('error', 'Unknown error occurred')
            verification_info = ""
            
            if result.get('verification_required'):
                verification_type = result.get('verification_type', 'unknown')
                verification_info = f"\n\nVerification required: {verification_type}."
                
                # Enable verification button
                self.verification_button.config(state='normal')
                
                # Store verification details for later
                self.verification_data = {
                    'username': result['username'],
                    'type': verification_type,
                    'email': account_data['email']
                }
            
            messagebox.showerror("Creation Failed", f"Failed to create account: {error_msg}{verification_info}")
            self.update_status(f"Account creation failed: {error_msg}")
        
        self._reset_creation_state()
    
    def _reset_creation_state(self):
        """Reset UI state after creation attempt"""
        self.running = False
        self.start_button.config(state='normal')
        self.current_thread = None
    
    def reset_form(self):
        """Clear all form fields"""
        self.username_var.set("")
        self.email_var.set("")
        self.fullname_var.set("")
        self.password_var.set("")
        self.phone_var.set("")
        self.profile_pic_var.set("")
        self.bio_text.delete("1.0", tk.END)
        
        # Reset checkboxes
        self.temp_email_var.set(False)
        self.show_password_var.set(False)
        self.use_proxy_var.set(False)
        self.toggle_proxy_fields()
        self.toggle_password_visibility()
        
        # Reset proxy fields
        self.proxy_ip_var.set("")
        self.proxy_port_var.set("")
        self.proxy_username_var.set("")
        self.proxy_password_var.set("")
        
        # Reset progress
        self.progress_var.set(0)
        self.status_var.set("Ready")
        
        # Set random date of birth
        current_year = datetime.now().year
        self.month_var.set(calendar.month_name[random.randint(1, 12)])
        self.day_var.set(str(random.randint(1, 28)))
        self.year_var.set(str(random.randint(current_year - 40, current_year - 18)))
        
        # Clear log
        self.log_text.config(state='normal')
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state='disabled')
        
        # Reset image preview
        self.preview_canvas.delete("all")
        
        # Disable verification button
        self.verification_button.config(state='disabled')
    
    def get_month_number(self):
        """Convert month name to number"""
        month_name = self.month_var.get()
        try:
            # Try to directly convert if it's already a number
            return int(month_name)
        except ValueError:
            # Convert from name to number
            for i, name in enumerate(calendar.month_name):
                if name == month_name:
                    return i
            # Default to January if not found
            return 1
    
    def show_stats(self):
        """Show account creation statistics"""
        stats = self.account_creator.get_stats()
        
        stats_text = f"""Account Creation Statistics:
        
Total Attempts: {stats['attempts']}
Successful: {stats['successes']} ({stats['successes']/max(1, stats['attempts'])*100:.1f}%)
Failed: {stats['failures']} ({stats['failures']/max(1, stats['attempts'])*100:.1f}%)
Verifications Required: {stats['verifications_required']}
CAPTCHAs Encountered: {stats['captchas_encountered']}
"""
        
        messagebox.showinfo("Creation Statistics", stats_text)
    
    def show_verification_dialog(self):
        """Show dialog for manual verification"""
        if not hasattr(self, 'verification_data'):
            messagebox.showinfo("Verification", "No pending verification")
            return
        
        verification_window = tk.Toplevel(self)
        verification_window.title("Manual Verification")
        verification_window.geometry("400x300")
        verification_window.resizable(False, False)
        
        # Verification details
        ttk.Label(verification_window, text="Account Verification", font=("", 12, "bold")).pack(pady=10)
        
        details_frame = ttk.Frame(verification_window)
        details_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(details_frame, text=f"Username: {self.verification_data['username']}").pack(anchor='w')
        ttk.Label(details_frame, text=f"Verification Type: {self.verification_data['type']}").pack(anchor='w')
        ttk.Label(details_frame, text=f"Email: {self.verification_data['email']}").pack(anchor='w')
        
        # Code entry
        code_frame = ttk.Frame(verification_window)
        code_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(code_frame, text="Verification Code:").pack(anchor='w')
        
        code_var = tk.StringVar()
        code_entry = ttk.Entry(code_frame, textvariable=code_var, width=20)
        code_entry.pack(fill='x', pady=5)
        code_entry.focus()
        
        # Buttons
        button_frame = ttk.Frame(verification_window)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(button_frame, text="Submit", 
                  command=lambda: self.submit_verification_code(code_var.get(), verification_window)).pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="Cancel", 
                  command=verification_window.destroy).pack(side='right', padx=5)
    
    def submit_verification_code(self, code, window):
        """Handle verification code submission"""
        if not code:
            messagebox.showerror("Error", "Please enter a verification code")
            return
        
        # Here you would implement the code to submit the verification code
        # For now, we just show a message
        self.update_status(f"Verification code submitted: {code}")
        messagebox.showinfo("Verification", "Code submitted. This feature will be fully implemented in the future.")
        
        # Close the window
        window.destroy()
        
        # Disable verification button
        self.verification_button.config(state='disabled')
    
    def show_batch_dialog(self):
        """Show dialog for batch account creation"""
        batch_window = tk.Toplevel(self)
        batch_window.title("Batch Account Creation")
        batch_window.geometry("500x400")
        
        ttk.Label(batch_window, text="Batch Account Creation", font=("", 12, "bold")).pack(pady=10)
        
        # Number of accounts
        count_frame = ttk.Frame(batch_window)
        count_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(count_frame, text="Number of Accounts:").pack(side='left')
        count_var = tk.IntVar(value=5)
        ttk.Spinbox(count_frame, from_=1, to=20, textvariable=count_var, width=5).pack(side='left', padx=5)
        
        # Username pattern
        username_frame = ttk.Frame(batch_window)
        username_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(username_frame, text="Username Pattern:").pack(side='left')
        username_pattern_var = tk.StringVar(value="user_{random}")
        ttk.Entry(username_frame, textvariable=username_pattern_var).pack(side='left', padx=5, fill='x', expand=True)
        
        ttk.Label(username_frame, text="Use {random} for random string").pack(side='right')
        
        # Name pattern
        name_frame = ttk.Frame(batch_window)
        name_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(name_frame, text="Name Pattern:").pack(side='left')
        name_pattern_var = tk.StringVar(value="User {num}")
        ttk.Entry(name_frame, textvariable=name_pattern_var).pack(side='left', padx=5, fill='x', expand=True)
        
        ttk.Label(name_frame, text="Use {num} for sequence number").pack(side='right')
        
        # Use proxy
        proxy_frame = ttk.Frame(batch_window)
        proxy_frame.pack(fill='x', padx=10, pady=5)
        
        use_proxy_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(proxy_frame, text="Use Proxies", variable=use_proxy_var).pack(side='left')
        
        ttk.Label(proxy_frame, text="From proxy settings tab").pack(side='left', padx=5)
        
        # Settings
        settings_frame = ttk.LabelFrame(batch_window, text="Settings")
        settings_frame.pack(fill='x', padx=10, pady=5)
        
        auto_verify_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Auto-verify accounts if possible", 
                       variable=auto_verify_var).pack(anchor='w', padx=5, pady=2)
        
        random_bio_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Generate random bio for each account", 
                       variable=random_bio_var).pack(anchor='w', padx=5, pady=2)
        
        profile_pic_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(settings_frame, text="Add profile picture to accounts", 
                       variable=profile_pic_var).pack(anchor='w', padx=5, pady=2)
        
        # Log frame
        log_frame = ttk.LabelFrame(batch_window, text="Status")
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        batch_log = tk.Text(log_frame, height=5, width=50, state='disabled')
        batch_log.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Button frame
        button_frame = ttk.Frame(batch_window)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(button_frame, text="Start Batch Creation", 
                  command=lambda: self.start_batch_creation(
                      count_var.get(), 
                      username_pattern_var.get(),
                      name_pattern_var.get(),
                      use_proxy_var.get(),
                      auto_verify_var.get(),
                      random_bio_var.get(),
                      profile_pic_var.get(),
                      batch_log,
                      batch_window
                  )).pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="Close", 
                  command=batch_window.destroy).pack(side='right', padx=5)
    
    def start_batch_creation(self, count, username_pattern, name_pattern, 
                           use_proxy, auto_verify, random_bio, profile_pic,
                           log_text, window):
        """Start batch account creation process"""
        # This would typically implement batch creation
        # For now, just show a message
        
        log_text.config(state='normal')
        log_text.insert(tk.END, f"Starting batch creation of {count} accounts...\n")
        log_text.config(state='disabled')
        
        messagebox.showinfo("Batch Creation", 
                           "Batch creation will be implemented in a future update. This dialog is a preview.")
        
        window.destroy()