# app/services/utils/proxy_manager.py
import random
import logging
import time
import requests
from datetime import datetime, timedelta

class ProxyManager:
    """
    Manages proxies for Instagram automation
    """
    
    def __init__(self):
        self.proxies = []
        self.logger = logging.getLogger(__name__)
        
        # Time to wait before reusing a failed proxy (in seconds)
        self.cooldown_period = 3600  # 1 hour
    
    def add_proxies(self, proxy_list):
        """
        Add a list of proxies to the manager
        
        Args:
            proxy_list (list): List of proxy dictionaries with keys:
                              ip, port, protocol, username, password
        """
        for proxy in proxy_list:
            # Add additional fields for tracking
            proxy['last_used'] = None
            proxy['failure_count'] = 0
            proxy['last_failure'] = None
            proxy['working'] = True
            
            # Add to the list if not already present
            if not any(p['ip'] == proxy['ip'] and p['port'] == proxy['port'] for p in self.proxies):
                self.proxies.append(proxy)
                self.logger.info(f"Added proxy: {proxy['ip']}:{proxy['port']}")
    
    def get_proxy(self, exclude_ips=None):
        """
        Get a random working proxy
        
        Args:
            exclude_ips (list): Optional list of IP addresses to exclude
            
        Returns:
            dict: A proxy dictionary or None if no working proxies
        """
        if not self.proxies:
            self.logger.warning("No proxies available")
            return None
        
        # Filter out excluded IPs
        available_proxies = self.proxies
        if exclude_ips:
            available_proxies = [p for p in self.proxies if p['ip'] not in exclude_ips]
        
        # Filter out proxies in cooldown
        now = datetime.now()
        available_proxies = [
            p for p in available_proxies 
            if p['working'] and (
                p['last_failure'] is None or 
                (now - p['last_failure']).total_seconds() > self.cooldown_period
            )
        ]
        
        if not available_proxies:
            self.logger.warning("No working proxies available")
            return None
        
        # Get the least recently used proxy
        proxy = min(available_proxies, key=lambda p: p['last_used'] or datetime.min)
        
        # Update last used time
        proxy['last_used'] = datetime.now()
        
        self.logger.info(f"Using proxy: {proxy['ip']}:{proxy['port']}")
        return proxy
    
    def mark_proxy_failure(self, proxy_id):
        """
        Mark a proxy as failed
        
        Args:
            proxy_id (str): The ID of the proxy to mark as failed
        """
        for proxy in self.proxies:
            if proxy.get('id') == proxy_id:
                proxy['failure_count'] += 1
                proxy['last_failure'] = datetime.now()
                
                # Disable proxy after too many failures
                if proxy['failure_count'] >= 5:
                    proxy['working'] = False
                    self.logger.warning(f"Proxy {proxy['ip']}:{proxy['port']} marked as non-working after {proxy['failure_count']} failures")
                else:
                    self.logger.info(f"Proxy {proxy['ip']}:{proxy['port']} failure count: {proxy['failure_count']}")
                break
    
    def release_proxy(self, proxy_id):
        """
        Release a proxy after use (nothing to do in this implementation)
        
        Args:
            proxy_id (str): The ID of the proxy to release
        """
        pass
    
    def test_proxies(self):
        """
        Test all proxies and update their status
        
        Returns:
            tuple: (working_count, total_count)
        """
        working_count = 0
        
        for proxy in self.proxies:
            try:
                self.logger.info(f"Testing proxy: {proxy['ip']}:{proxy['port']}")
                
                proxies = {
                    "http": f"{proxy['protocol']}://{proxy.get('username', '')}:{proxy.get('password', '')}@{proxy['ip']}:{proxy['port']}",
                    "https": f"{proxy['protocol']}://{proxy.get('username', '')}:{proxy.get('password', '')}@{proxy['ip']}:{proxy['port']}"
                }
                
                # Test with a request to Instagram
                response = requests.get("https://www.instagram.com/", 
                                        proxies=proxies, 
                                        timeout=10)
                
                if response.status_code == 200:
                    proxy['working'] = True
                    proxy['failure_count'] = 0
                    proxy['last_failure'] = None
                    working_count += 1
                    self.logger.info(f"Proxy {proxy['ip']}:{proxy['port']} is working")
                else:
                    proxy['working'] = False
                    proxy['failure_count'] += 1
                    proxy['last_failure'] = datetime.now()
                    self.logger.warning(f"Proxy {proxy['ip']}:{proxy['port']} returned status code {response.status_code}")
            
            except Exception as e:
                proxy['working'] = False
                proxy['failure_count'] += 1
                proxy['last_failure'] = datetime.now()
                self.logger.error(f"Error testing proxy {proxy['ip']}:{proxy['port']}: {str(e)}")
        
        return working_count, len(self.proxies)