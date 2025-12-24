"""
Configuration settings for Proxy Manager
"""
import json
from pathlib import Path


class ConfigManager:
    """Manages application configuration and credentials"""
    
    def __init__(self):
        self.config_file = Path.home() / ".proxy_manager_config.json"
        self.credentials_file = Path.home() / ".proxy_manager_credentials.json"
        
        # Default proxy configuration
        self.default_config = {
            "http_proxy": "http://usuario:contraseña@192.168.91.20:3128",
            "https_proxy": "http://usuario:contraseña@192.168.91.20:3128",
            "ftp_proxy": "http://usuario:contraseña@192.168.91.20:3128",
            "no_proxy": "localhost,127.0.0.1,localaddress,.localdomain.com,*.cu",
            "apt_proxy": "http://usuario:contraseña@192.168.91.20:3128"
        }
        
        self.default_credentials = {
            "username": "",
            "password": ""
        }
        
        # Load existing configuration or create defaults
        self.proxy_settings = self.load_config()
        self.credentials = self.load_credentials()
    
    def load_config(self):
        """Load proxy configuration from file or return defaults"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading configuration: {e}")
                return self.default_config
        else:
            self.save_config(self.default_config)
            return self.default_config
    
    def save_config(self, config):
        """Save proxy configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def load_credentials(self):
        """Load user credentials from file or return defaults"""
        if self.credentials_file.exists():
            try:
                with open(self.credentials_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading credentials: {e}")
                return self.default_credentials
        else:
            self.save_credentials(self.default_credentials)
            return self.default_credentials
    
    def save_credentials(self):
        """Save user credentials to file"""
        try:
            with open(self.credentials_file, 'w') as f:
                json.dump(self.credentials, f, indent=2)
        except Exception as e:
            print(f"Error saving credentials: {e}")