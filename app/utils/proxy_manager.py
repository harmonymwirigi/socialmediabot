# app/utils/proxy_manager.py

import random
import time
import logging
import threading
import requests
from datetime import datetime, timedelta

class ProxyManager:
    """
    Manages a pool of proxies for rotating IPs to prevent blocking
    """
    
    def __init__(self, proxy_list=None, proxy_api_url=None, api_key=None, max_uses=5, cooldown_minutes=10):
        self.logger = logging.getLogger(__name__)
        self.proxies = []
        self.lock = threading.Lock()
        self.max_uses = max_uses
        self.cooldown_minutes = cooldown_minutes
        self.proxy_api_url = proxy_api_url
        self.api_key = api_key
        
        # Initialize proxies
        if proxy_list:
            self.add_proxies(proxy_list)
        elif proxy_api_url and api_key:
            self.fetch_proxies_from_api()
    
    def add_proxies(self, proxy_list):
        """
        Add proxies to the pool
        
        Args:
            proxy_list (list): List of proxy dictionaries with format:
                {
                    'ip': '123.456.789.012',
                    'port': '8080',
                    'username': 'user', # Optional
                    'password': 'pass'  # Optional
                }
        """
        with self.lock:
            for proxy in proxy_list:
                proxy_entry = {
                    'id': len(self.proxies),
                    'ip': proxy.get('ip'),
                    'port': proxy.get('port'),
                    'username': proxy.get('username'),
                    'password': proxy.get('password'),
                    'protocol': proxy.get('protocol', 'http'),
                    'uses': 0,
                    'last_used': None,
                    'in_use': False,
                    'failed': False
                }
                self.proxies.append(proxy_entry)
            
            self.logger.info(f"Added {len(proxy_list)} proxies to pool. Total proxies: {len(self.proxies)}")
    
    def fetch_proxies_from_api(self):
        """Fetch proxies from the configured API service"""
        if not self.proxy_api_url or not self.api_key:
            self.logger.error("Cannot fetch proxies: API URL or key not provided")
            return
        
        try:
            self.logger.info(f"Fetching proxies from API: {self.proxy_api_url}")
            
            # Make API request
            params = {
                'api_key': self.api_key,
                'protocol': 'http,https',
                'country': 'US,CA,UK,AU',  # Example countries
                'anonymity': 'high',
                'limit': 20
            }
            
            response = requests.get(self.proxy_api_url, params=params)
            
            if response.status_code == 200:
                proxy_data = response.json()
                
                # Format depends on the API provider
                # This is an example assuming a common format
                proxy_list = []
                
                for item in proxy_data.get('data', []):
                    proxy = {
                        'ip': item.get('ip'),
                        'port': item.get('port'),
                        'username': item.get('username'),
                        'password': item.get('password'),
                        'protocol': item.get('protocol', 'http')
                    }
                    proxy_list.append(proxy)
                
                self.add_proxies(proxy_list)
                self.logger.info(f"Successfully fetched {len(proxy_list)} proxies")
            else:
                self.logger.error(f"Failed to fetch proxies: {response.status_code} - {response.text}")
        
        except Exception as e:
            self.logger.error(f"Error fetching proxies from API: {str(e)}")
    
    def get_proxy(self):
        """
        Get an available proxy from the pool
        
        Returns:
            dict: Proxy information or None if no proxy available
        """
        with self.lock:
            # Check if we have any proxies
            if not self.proxies:
                self.logger.warning("No proxies available in pool")
                return None
            
            available_proxies = []
            
            # Find available proxies
            for proxy in self.proxies:
                # Skip proxies that are in use or have failed
                if proxy['in_use'] or proxy['failed']:
                    continue
                
                # Skip proxies that have reached max uses
                if proxy['uses'] >= self.max_uses:
                    continue
                
                # Skip proxies that are in cooldown
                if proxy['last_used'] and (datetime.now() - proxy['last_used']).total_seconds() < (self.cooldown_minutes * 60):
                    continue
                
                available_proxies.append(proxy)
            
            if not available_proxies:
                self.logger.warning("No available proxies that meet criteria")
                
                # If all proxies have reached max uses, reset the use counter
                all_max_uses = all(p['uses'] >= self.max_uses for p in self.proxies if not p['failed'])
                if all_max_uses:
                    self.logger.info("Resetting use counter for all proxies")
                    for proxy in self.proxies:
                        proxy['uses'] = 0
                    
                    # Try again
                    return self.get_proxy()
                
                return None
            
            # Select a random proxy
            proxy = random.choice(available_proxies)
            
            # Mark proxy as in use
            proxy['in_use'] = True
            proxy['uses'] += 1
            proxy['last_used'] = datetime.now()
            
            self.logger.info(f"Selected proxy: {proxy['ip']}:{proxy['port']} (Uses: {proxy['uses']})")
            
            return proxy.copy()
    
    def release_proxy(self, proxy_id, failed=False):
        """
        Release a proxy back to the pool
        
        Args:
            proxy_id: ID of the proxy to release
            failed (bool): Whether the proxy failed
        """
        with self.lock:
            for proxy in self.proxies:
                if proxy['id'] == proxy_id:
                    proxy['in_use'] = False
                    if failed:
                        proxy['failed'] = True
                        self.logger.warning(f"Marking proxy as failed: {proxy['ip']}:{proxy['port']}")
                    break
    
    def test_proxy(self, proxy):
        """
        Test if a proxy is working
        
        Args:
            proxy (dict): Proxy to test
            
        Returns:
            bool: Whether the proxy is working
        """
        try:
            test_url = 'https://www.instagram.com'
            
            # Build proxy URL
            auth = ''
            if proxy.get('username') and proxy.get('password'):
                auth = f"{proxy['username']}:{proxy['password']}@"
            
            proxy_url = f"{proxy['protocol']}://{auth}{proxy['ip']}:{proxy['port']}"
            
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            response = requests.get(test_url, proxies=proxies, timeout=10)
            
            if response.status_code == 200:
                self.logger.info(f"Proxy test successful: {proxy['ip']}:{proxy['port']}")
                return True
            else:
                self.logger.warning(f"Proxy test failed with status {response.status_code}: {proxy['ip']}:{proxy['port']}")
                return False
                
        except Exception as e:
            self.logger.warning(f"Proxy test failed with error: {str(e)}")
            return False
    
    def test_all_proxies(self):
        """
        Test all proxies in the pool and remove failed ones
        
        Returns:
            int: Number of working proxies
        """
        working_count = 0
        
        with self.lock:
            for proxy in self.proxies:
                if not proxy['failed'] and not proxy['in_use']:
                    if self.test_proxy(proxy):
                        working_count += 1
                    else:
                        proxy['failed'] = True
        
        self.logger.info(f"Proxy test completed: {working_count}/{len(self.proxies)} working")
        return working_count