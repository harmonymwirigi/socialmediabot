# app/ui/tabs.py
import tkinter as tk
from tkinter import ttk, messagebox
from ..services.instagram.browser import InstagramBrowser
import time

class AccountsTab(ttk.Frame):
    def __init__(self, parent, account_service):
        super().__init__(parent)
        self.account_service = account_service
        self.browser = InstagramBrowser()
        
        self.setup_add_account_frame()
        self.setup_accounts_list()
        self.load_accounts()
    
    def setup_add_account_frame(self):
        add_frame = ttk.LabelFrame(self, text="Add Instagram Account")
        add_frame.pack(fill='x', padx=5, pady=5)
        
        # Username field
        username_frame = ttk.Frame(add_frame)
        username_frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(username_frame, text="Username:").pack(side='left')
        self.username_var = tk.StringVar()
        ttk.Entry(username_frame, textvariable=self.username_var).pack(side='left', padx=5, fill='x', expand=True)
        
        # Password field
        password_frame = ttk.Frame(add_frame)
        password_frame.pack(fill='x', padx=5, pady=5)
        ttk.Label(password_frame, text="Password:").pack(side='left')
        self.password_var = tk.StringVar()
        ttk.Entry(password_frame, textvariable=self.password_var, show="*").pack(side='left', padx=5, fill='x', expand=True)
        
        # Buttons frame
        button_frame = ttk.Frame(add_frame)
        button_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(button_frame, text="Add Account", command=self.add_account).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_fields).pack(side='left')

    def add_account(self):
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        if not username or not password:
            messagebox.showerror("Error", "Please fill in both username and password")
            return
        
        try:
            self.account_service.add_account(username, password)
            messagebox.showinfo("Success", f"Account {username} added successfully")
            self.clear_fields()
            self.load_accounts()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add account: {str(e)}")
    
    def clear_fields(self):
        self.username_var.set("")
        self.password_var.set("")

    def setup_accounts_list(self):
        list_frame = ttk.LabelFrame(self, text="Accounts List")
        list_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Create Treeview
        columns = ('Username', 'Status', 'Last Used', 'Login Status', 'Actions')
        self.accounts_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # Configure columns
        for col in columns:
            self.accounts_tree.heading(col, text=col)
            self.accounts_tree.column(col, width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.accounts_tree.yview)
        self.accounts_tree.configure(yscrollcommand=scrollbar.set)
        
        # Bind click event for the login button
        self.accounts_tree.bind('<ButtonRelease-1>', self.handle_button_click)
        
        # Pack widgets
        self.accounts_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def load_accounts(self):
        for item in self.accounts_tree.get_children():
            self.accounts_tree.delete(item)
        
        accounts = self.account_service.get_accounts()
        for account in accounts:
            username = account[0]
            status = "Active" if account[1] else "Inactive"
            last_used = account[2]
            has_cookies = self.browser._check_cookies_exist(username)
            login_status = "Logged In" if has_cookies else "Not Logged In"
            action_text = "" if has_cookies else "Login"
            
            self.accounts_tree.insert('', 'end', values=(
                username, status, last_used, login_status, action_text
            ))
    
    def handle_button_click(self, event):
        item = self.accounts_tree.identify_row(event.y)
        if not item:
            return
            
        col = self.accounts_tree.identify_column(event.x)
        if str(col) != "#5":  # Actions column
            return
            
        values = self.accounts_tree.item(item)['values']
        username = values[0]
        login_status = values[3]
        
        if login_status != "Logged In":
            self.initiate_manual_login(username)
    
    def initiate_manual_login(self, username):
        try:
            success = self.browser.initiate_manual_login(username)
            if success:
                messagebox.showinfo("Success", "Login successful! Cookies saved.")
                self.load_accounts()
            else:
                messagebox.showerror("Error", "Login failed or browser was closed before completion")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start login process: {str(e)}")
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
class CommentsTab(ttk.Frame):
    def __init__(self, parent, interaction_service):
        super().__init__(parent)
        self.interaction_service = interaction_service
        self.logger = logging.getLogger(__name__)
        
        self.setup_url_frame()
        self.setup_comments_frame()
        self.setup_control_frame()
        
        # Set progress callback
        self.interaction_service.set_progress_callback(self.update_progress)
    
    def setup_url_frame(self):
        url_frame = ttk.LabelFrame(self, text="Target Post")
        url_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(url_frame, text="Post URL:").pack(side='left', padx=5)
        self.url_var = tk.StringVar()
        ttk.Entry(url_frame, textvariable=self.url_var, width=50).pack(
            side='left', padx=5, pady=5, fill='x', expand=True
        )
    
    def setup_comments_frame(self):
        comments_frame = ttk.LabelFrame(self, text="Comments (One per line)")
        comments_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.comments_text = tk.Text(comments_frame, height=10)
        scrollbar = ttk.Scrollbar(comments_frame, orient='vertical', command=self.comments_text.yview)
        self.comments_text.configure(yscrollcommand=scrollbar.set)
        
        self.comments_text.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y')
    
    def setup_control_frame(self):
        control_frame = ttk.Frame(self)
        control_frame.pack(fill='x', padx=5, pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            control_frame, 
            variable=self.progress_var,
            maximum=100
        )
        self.progress.pack(fill='x', pady=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(control_frame, textvariable=self.status_var)
        status_label.pack(fill='x', pady=2)
        
        # Control buttons
        self.start_button = ttk.Button(
            control_frame,
            text="Start Commenting",
            command=self.start_commenting
        )
        self.start_button.pack(pady=5)
    
    def update_progress(self, value):
        """Update progress bar and status"""
        self.progress_var.set(value)
        self.status_var.set(f"Progress: {value:.1f}%")
        self.update_idletasks()
    
    def show_error(self, error_message):
        """Show error message in UI thread"""
        messagebox.showerror("Error", str(error_message))
    
    def show_success(self, success_message):
        """Show success message in UI thread"""
        messagebox.showinfo("Complete", success_message)
    
    def start_commenting(self):
        """Start the commenting process in a separate thread"""
        url = self.url_var.get().strip()
        comments = [c.strip() for c in self.comments_text.get("1.0", tk.END).strip().split('\n') if c.strip()]
        
        if not url or not comments:
            messagebox.showerror("Error", "Please provide both URL and comments")
            return
        
        # Disable controls
        self.start_button.configure(state='disabled')
        self.progress_var.set(0)
        self.status_var.set("Starting...")
        
        def comment_thread():
            try:
                self.logger.info("Starting comment process")
                results = self.interaction_service.comment_on_post(url, comments)
                
                # Calculate results
                total = len(comments)
                successes = sum(1 for r in results if r['success'])
                
                # Format success message
                success_message = f"Commenting complete: {successes}/{total} successful\n\n"
                for result in results:
                    status = "✓" if result['success'] else "✗"
                    error = f" - {result['error']}" if result['error'] else ""
                    success_message += f"{status} {result['username']}: {result['comment']}{error}\n"
                
                # Show results in UI thread
                self.after(0, lambda: self.show_success(success_message))
                
            except Exception as error:
                self.logger.error(f"Comment process failed: {str(error)}")
                # Show error in UI thread
                self.after(0, lambda: self.show_error(f"Failed to complete commenting: {str(error)}"))
                
            finally:
                # Re-enable controls in UI thread
                self.after(0, lambda: self.start_button.configure(state='normal'))
                self.after(0, lambda: self.status_var.set("Ready"))
        
        # Start comment thread
        threading.Thread(target=comment_thread, daemon=True).start()