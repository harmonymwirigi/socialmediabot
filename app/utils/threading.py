# Add to app/utils/threading.py
import threading
import logging
import traceback

def run_in_background(func):
    """Decorator to run a function in a background thread"""
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper